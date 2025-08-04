"""
WebSocketサーバーモジュール

FuguMT翻訳サーバーのWebSocket通信を管理します。
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional, Set
import websockets
from websockets.server import WebSocketServerProtocol
import threading
from queue import Queue, Empty
from .translator import FuguMTTranslator


class WebSocketServer:
    """WebSocketサーバークラス"""
    
    def __init__(self, config, translator: FuguMTTranslator):
        """
        WebSocketサーバーの初期化
        
        Args:
            config: 設定オブジェクト
            translator: 翻訳エンジン
        """
        self.config = config
        self.translator = translator
        self.logger = logging.getLogger(__name__)
        
        # 接続管理
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.client_info: Dict[WebSocketServerProtocol, Dict] = {}
        
        # リクエスト処理キュー
        self.request_queue = Queue()
        self.response_queues: Dict[str, Queue] = {}
        
        # 統計情報
        self.server_stats = {
            'start_time': time.time(),
            'total_connections': 0,
            'active_connections': 0,
            'total_requests': 0,
            'total_errors': 0
        }
        
        # ワーカースレッド
        self.workers = []
        self.running = False
        self.server = None
        
    async def start_server(self, shutdown_event=None):
        """サーバー開始"""
        try:
            self.logger.info(f"FuguMT翻訳サーバーを開始します...")
            self.logger.info(f"ホスト: {self.config.server_host}")
            self.logger.info(f"ポート: {self.config.server_port}")
            
            # ワーカースレッド開始
            self.running = True
            for i in range(self.config.worker_threads):
                worker = threading.Thread(target=self._worker_thread, args=(i,))
                worker.daemon = False  # 確実に終了を待機するため
                worker.start()
                self.workers.append(worker)
                
            self.logger.info(f"{self.config.worker_threads}個のワーカースレッドを開始しました")
            
            # WebSocketサーバー開始
            async with websockets.serve(
                self.handle_client,
                self.config.server_host,
                self.config.server_port,
                max_size=None,
                ping_interval=20,
                ping_timeout=10
            ) as server:
                self.logger.info("サーバーが正常に開始されました")
                self.server = server
                
                # シャットダウンイベントを待機
                if shutdown_event:
                    await shutdown_event.wait()
                else:
                    await asyncio.Future()  # 永続化（後方互換性のため）
                
        except Exception as e:
            self.logger.error(f"サーバー開始エラー: {e}")
            raise
        finally:
            self.stop_server()
            
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        """クライアント接続処理"""
        client_id = str(uuid.uuid4())
        client_address = websocket.remote_address
        
        self.logger.info(f"新しいクライアント接続: {client_id} from {client_address}")
        
        # クライアント登録
        self.connected_clients.add(websocket)
        self.client_info[websocket] = {
            'id': client_id,
            'address': client_address,
            'connect_time': time.time(),
            'request_count': 0
        }
        
        self.server_stats['total_connections'] += 1
        self.server_stats['active_connections'] += 1
        
        try:
            await self._client_loop(websocket, client_id)
        except websockets.exceptions.ConnectionClosed:
            self.logger.info(f"クライアント接続終了: {client_id}")
        except Exception as e:
            self.logger.error(f"クライアント処理エラー {client_id}: {e}")
        finally:
            # クライアント登録解除
            self.connected_clients.discard(websocket)
            self.client_info.pop(websocket, None)
            self.server_stats['active_connections'] -= 1
            
    async def _client_loop(self, websocket: WebSocketServerProtocol, client_id: str):
        """クライアントメッセージ処理ループ"""
        async for message in websocket:
            try:
                await self._process_message(websocket, client_id, message)
            except Exception as e:
                self.logger.error(f"メッセージ処理エラー {client_id}: {e}")
                error_response = {
                    'error': str(e),
                    'status': 'error'
                }
                await websocket.send(json.dumps(error_response, ensure_ascii=False))
                
    async def _process_message(self, websocket: WebSocketServerProtocol, client_id: str, message: str):
        """メッセージ処理"""
        try:
            data = json.loads(message)
        except json.JSONDecodeError as e:
            raise ValueError(f"無効なJSONフォーマット: {e}")
            
        # リクエストタイプによる処理分岐
        request_type = data.get('type', 'translation')
        
        if request_type == 'translation':
            await self._handle_translation_request(websocket, client_id, data)
        elif request_type == 'ping':
            await self._handle_ping_request(websocket, client_id, data)
        elif request_type == 'stats':
            await self._handle_stats_request(websocket, client_id, data)
        elif request_type == 'health':
            await self._handle_health_request(websocket, client_id, data)
        else:
            raise ValueError(f"サポートされていないリクエストタイプ: {request_type}")
            
    async def _handle_translation_request(self, websocket: WebSocketServerProtocol, client_id: str, data: Dict):
        """翻訳リクエスト処理"""
        request_id = data.get('request_id', str(uuid.uuid4()))
        
        # 必須フィールドの確認
        required_fields = ['text']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"必須フィールドが不足: {field}")
                
        # デフォルト値設定
        text = data['text']
        source_lang = data.get('source_lang', 'en')
        target_lang = data.get('target_lang', 'ja')
        priority = data.get('priority', 'normal')
        
        # レスポンスキューの作成
        response_queue = Queue()
        self.response_queues[request_id] = response_queue
        
        # リクエストをワーカーキューに追加
        request = {
            'id': request_id,
            'client_id': client_id,
            'type': 'translation',
            'text': text,
            'source_lang': source_lang,
            'target_lang': target_lang,
            'priority': priority,
            'timestamp': time.time()
        }
        
        self.request_queue.put(request)
        self.server_stats['total_requests'] += 1
        self.client_info[websocket]['request_count'] += 1
        
        # レスポンス待機
        try:
            response = response_queue.get(timeout=self.config.timeout_seconds)
            response['request_id'] = request_id
            
            await websocket.send(json.dumps(response, ensure_ascii=False))
            
        except Empty:
            timeout_response = {
                'request_id': request_id,
                'error': f'リクエストタイムアウト ({self.config.timeout_seconds}秒)',
                'status': 'timeout'
            }
            await websocket.send(json.dumps(timeout_response, ensure_ascii=False))
            
        finally:
            # レスポンスキューのクリーンアップ
            self.response_queues.pop(request_id, None)
            
    async def _handle_ping_request(self, websocket: WebSocketServerProtocol, client_id: str, data: Dict):
        """Pingリクエスト処理"""
        pong_response = {
            'type': 'pong',
            'timestamp': time.time(),
            'server_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'ok'
        }
        await websocket.send(json.dumps(pong_response, ensure_ascii=False))
        
    async def _handle_stats_request(self, websocket: WebSocketServerProtocol, client_id: str, data: Dict):
        """統計情報リクエスト処理"""
        translator_stats = self.translator.get_stats()
        
        combined_stats = {
            'type': 'stats',
            'server_stats': self.server_stats.copy(),
            'translator_stats': translator_stats,
            'supported_languages': self.translator.get_supported_languages(),
            'timestamp': time.time(),
            'status': 'ok'
        }
        
        # アップタイム計算
        combined_stats['server_stats']['uptime_seconds'] = time.time() - self.server_stats['start_time']
        
        await websocket.send(json.dumps(combined_stats, ensure_ascii=False))
        
    async def _handle_health_request(self, websocket: WebSocketServerProtocol, client_id: str, data: Dict):
        """ヘルスチェックリクエスト処理"""
        health_info = self.translator.health_check()
        health_info['type'] = 'health'
        health_info['server_status'] = 'running'
        health_info['active_connections'] = self.server_stats['active_connections']
        
        await websocket.send(json.dumps(health_info, ensure_ascii=False))
        
    def _worker_thread(self, worker_id: int):
        """ワーカースレッド処理"""
        self.logger.info(f"ワーカースレッド {worker_id} を開始しました")
        
        while self.running:
            try:
                # リクエストを取得
                request = self.request_queue.get(timeout=1.0)
                
                # 翻訳処理実行
                if request['type'] == 'translation':
                    result = self.translator.translate(
                        request['text'],
                        request['source_lang'],
                        request['target_lang']
                    )
                    
                    # レスポンスをクライアントキューに送信
                    response_queue = self.response_queues.get(request['id'])
                    if response_queue:
                        response_queue.put(result)
                        
                # タスク完了マーク
                self.request_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"ワーカースレッド {worker_id} エラー: {e}")
                self.server_stats['total_errors'] += 1
                
                # エラーレスポンス
                if 'request' in locals():
                    response_queue = self.response_queues.get(request['id'])
                    if response_queue:
                        error_result = {
                            'error': str(e),
                            'status': 'error',
                            'processing_time_ms': 0
                        }
                        response_queue.put(error_result)
                        
        self.logger.info(f"ワーカースレッド {worker_id} を終了しました")
        
    def stop_server(self):
        """サーバー停止"""
        self.logger.info("サーバーを停止しています...")
        self.running = False
        
        # 全クライアント接続を閉じる
        try:
            for websocket in self.connected_clients.copy():
                try:
                    asyncio.create_task(websocket.close())
                except RuntimeError:
                    # イベントループが実行されていない場合はスキップ
                    pass
        except Exception as e:
            self.logger.warning(f"クライアント接続の終了中にエラー: {e}")
        
        # 全ワーカースレッドの終了を待機
        self.logger.info("ワーカースレッドの終了を待機中...")
        for i, worker in enumerate(self.workers):
            if worker.is_alive():
                worker.join(timeout=2.0)  # タイムアウト短縮
                if worker.is_alive():
                    self.logger.warning(f"ワーカースレッド {i} が終了しませんでした（タイムアウト）")
                else:
                    self.logger.debug(f"ワーカースレッド {i} が正常に終了しました")
        
        self.logger.info("サーバーが停止されました")