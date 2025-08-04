#!/usr/bin/env python3
"""
FuguMT翻訳サーバー メインエントリーポイント

Usage:
    python main.py [--config CONFIG_FILE] [--host HOST] [--port PORT]
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
from pathlib import Path

# ログ設定（早期に設定）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

try:
    from FuguMTTranslator import Config, FuguMTTranslator, WebSocketServer
except ImportError as e:
    logging.error(f"FuguMTTranslatorパッケージのインポートに失敗: {e}")
    logging.error("setup.pyを実行してセットアップを完了してください: python setup.py")
    sys.exit(1)


class FuguMTServer:
    """FuguMT翻訳サーバーメインクラス"""
    
    def __init__(self, config_path=None, host=None, port=None):
        """
        サーバー初期化
        
        Args:
            config_path (str, optional): 設定ファイルパス
            host (str, optional): サーバーホスト（設定ファイルより優先）
            port (int, optional): サーバーポート（設定ファイルより優先）
        """
        # 設定読み込み
        self.config = Config(config_path)
        
        # コマンドライン引数で設定上書き
        if host:
            self.config.config['SERVER']['host'] = host
        if port:
            self.config.config['SERVER']['port'] = str(port)
        
        # ログ設定
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.translator = None
        self.websocket_server = None
        self.running = False
        self.shutdown_event = None
        self.signal_count = 0  # シグナル受信回数
        
    def _setup_logging(self):
        """ログ設定"""
        log_level = getattr(logging, self.config.log_level.upper())
        log_file = self.config.log_file
        
        # ログディレクトリ作成
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True)
        
        # ルートロガー設定
        logger = logging.getLogger()
        logger.setLevel(log_level)
        
        # ファイルハンドラー追加
        if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    async def start(self):
        """サーバー開始"""
        try:
            # 非同期イベント初期化
            self.shutdown_event = asyncio.Event()
            
            self.logger.info("="*50)
            self.logger.info("FuguMT翻訳サーバーを開始します")
            self.logger.info("="*50)
            
            # 翻訳エンジン初期化
            self.logger.info("翻訳エンジンを初期化中...")
            self.translator = FuguMTTranslator(self.config)
            
            # WebSocketサーバー初期化
            self.logger.info("WebSocketサーバーを初期化中...")
            self.websocket_server = WebSocketServer(self.config, self.translator)
            
            # ヘルスチェック
            health = self.translator.health_check()
            if health['status'] != 'healthy':
                self.logger.error(f"翻訳エンジンのヘルスチェックに失敗: {health}")
                return False
            
            self.logger.info("✅ 翻訳エンジン正常")
            self.logger.info(f"サポート言語ペア: {health['supported_pairs']}")
            self.logger.info(f"使用デバイス: {health['device']}")
            
            # シグナルハンドラー設定
            self._setup_signal_handlers()
            
            self.running = True
            
            # サーバー開始
            await self.websocket_server.start_server(self.shutdown_event)
            
        except KeyboardInterrupt:
            self.logger.info("キーボード割り込みを受信")
        except Exception as e:
            self.logger.error(f"サーバー開始エラー: {e}")
            return False
        finally:
            await self.stop()
            
        return True
    
    async def stop(self):
        """サーバー停止"""
        if not self.running:
            return
            
        self.logger.info("サーバーを停止中...")
        self.running = False
        
        # WebSocketサーバー停止
        if self.websocket_server:
            self.websocket_server.stop_server()
            
        # 翻訳エンジンのクリーンアップ
        if self.translator:
            self.translator.cleanup()
            
        # 追加のクリーンアップ
        try:
            import gc
            gc.collect()
            
            # CUDAリソースの強制クリーンアップ
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()
                
        except Exception as e:
            self.logger.warning(f"追加クリーンアップ中にエラー: {e}")
            
        self.logger.info("サーバーが停止されました")
        
    def _setup_signal_handlers(self):
        """シグナルハンドラー設定"""
        def signal_handler(signum, frame):
            self.signal_count += 1
            self.logger.info(f"シグナル {signum} を受信 ({self.signal_count}回目)")
            
            if self.signal_count == 1:
                # 1回目：通常の終了処理
                self.running = False
                if self.shutdown_event:
                    try:
                        # 現在のイベントループを取得してスレッドセーフに実行
                        loop = asyncio.get_running_loop()
                        loop.call_soon_threadsafe(self._shutdown)
                    except RuntimeError:
                        # イベントループが実行されていない場合は強制終了
                        self.logger.warning("イベントループが実行されていないため強制終了します")
                        import os
                        os._exit(1)
                        
            elif self.signal_count == 2:
                # 2回目：より強制的な終了
                self.logger.warning("2回目のシグナル受信 - 強制終了を開始します")
                try:
                    # 即座にリソースクリーンアップ
                    if self.translator:
                        self.translator.cleanup()
                    import gc
                    gc.collect()
                except Exception as e:
                    self.logger.error(f"強制クリーンアップエラー: {e}")
                finally:
                    import os
                    os._exit(0)
                    
            else:
                # 3回目以降：即座に強制終了
                self.logger.error("3回目のシグナル受信 - 即座に強制終了します")
                import os
                os._exit(1)
                
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def _shutdown(self):
        """シャットダウン処理（同期版）"""
        if self.shutdown_event:
            self.shutdown_event.set()
        
    def show_startup_info(self):
        """起動時情報表示"""
        print("\n" + "="*60)
        print("🌸 FuguMT翻訳サーバー")
        print("="*60)
        print(f"📡 サーバーアドレス: ws://{self.config.server_host}:{self.config.server_port}")
        print(f"🤖 翻訳モデル: {self.config.model_name_en_ja}")
        print(f"💾 デバイス: {self.config.device}")
        print(f"📝 ログファイル: {self.config.log_file}")
        print(f"⚙️  設定ファイル: {self.config.config_path}")
        print("="*60)
        print("💡 使用方法:")
        print("   WebSocketクライアントで接続してください")
        print("   例: ws://127.0.0.1:55002")
        print()
        print("📋 メッセージフォーマット:")
        print('   {"type": "translation", "text": "Hello", "source_lang": "en", "target_lang": "ja"}')
        print()
        print("🛑 サーバー停止: Ctrl+C")
        print("="*60)


def parse_arguments():
    """コマンドライン引数パース"""
    parser = argparse.ArgumentParser(
        description="FuguMT翻訳サーバー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py                           # デフォルト設定で起動
  python main.py --port 8080               # ポート指定
  python main.py --config my_config.ini    # 設定ファイル指定
  python main.py --host 0.0.0.0 --port 8080  # 外部アクセス許可
        """
    )
    
    parser.add_argument(
        "--config",
        help="設定ファイルパス（デフォルト: config/fugumt_translator.ini）"
    )
    
    parser.add_argument(
        "--host",
        help="サーバーホスト（デフォルト: 127.0.0.1）"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="サーバーポート（デフォルト: 55002）"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="FuguMT翻訳サーバー v1.0.0"
    )
    
    return parser.parse_args()


async def main():
    """メイン関数"""
    args = parse_arguments()
    
    # サーバー初期化
    server = FuguMTServer(
        config_path=args.config,
        host=args.host,
        port=args.port
    )
    
    # 起動情報表示
    server.show_startup_info()
    
    # サーバー開始
    success = await server.start()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nサーバーが停止されました")
    except Exception as e:
        logging.error(f"予期しないエラー: {e}")
        sys.exit(1)