#!/usr/bin/env python3
"""
FuguMT翻訳サーバー セットアップスクリプト

自動インストールと環境構築を行います。
"""

import sys
import subprocess
import os
import platform
import shutil
from pathlib import Path


def check_python_version():
    """Pythonバージョンチェック"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8以上が必要です")
        print(f"現在のバージョン: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def check_system_requirements():
    """システム要件チェック"""
    print("🔍 システム要件を確認中...")
    
    # OS情報
    os_name = platform.system()
    print(f"OS: {os_name} {platform.release()}")
    
    # メモリチェック（簡易）
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        print(f"メモリ: {memory_gb:.1f}GB")
        
        if memory_gb < 4:
            print("⚠️  メモリが4GB未満です。動作が遅くなる可能性があります。")
    except ImportError:
        print("メモリ情報の取得をスキップ（psutilが未インストール）")
    
    # GPU チェック
    check_gpu_availability()


def check_gpu_availability():
    """GPU利用可能性チェック"""
    print("🎮 GPU利用可能性を確認中...")
    
    # CUDA チェック
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ NVIDIA GPU検出")
            # GPU情報の簡易表示
            lines = result.stdout.split('\n')
            for line in lines:
                if 'GeForce' in line or 'RTX' in line or 'GTX' in line or 'Tesla' in line:
                    print(f"   {line.strip()}")
        else:
            print("ℹ️  NVIDIA GPUが検出されませんでした")
    except FileNotFoundError:
        print("ℹ️  nvidia-smiが見つかりません（NVIDIA GPUなし）")
    
    # Apple Silicon (MPS) チェック
    if platform.system() == "Darwin":
        try:
            # macOSでApple Siliconかチェック
            result = subprocess.run(['uname', '-m'], capture_output=True, text=True)
            if 'arm64' in result.stdout:
                print("✅ Apple Silicon検出（MPS利用可能）")
            else:
                print("ℹ️  Intel Mac（MPS利用不可）")
        except:
            pass


def install_dependencies():
    """依存関係のインストール"""
    print("📦 依存関係をインストール中...")
    
    try:
        # requirements.txtから依存関係をインストール
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ 依存関係のインストール完了")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 依存関係のインストールに失敗: {e}")
        print("手動でインストールしてください:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def create_directories():
    """必要なディレクトリの作成"""
    print("📁 ディレクトリを作成中...")
    
    directories = ["config", "logs", "models", "cache"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   {directory}/")
    
    print("✅ ディレクトリ作成完了")


def create_config():
    """設定ファイルの作成"""
    print("⚙️  設定ファイルを作成中...")
    
    try:
        from FuguMTTranslator import Config
        config = Config()
        print("✅ 設定ファイル作成完了")
        print(f"   設定ファイル: {config.config_path}")
        
    except Exception as e:
        print(f"❌ 設定ファイル作成に失敗: {e}")
        return False
        
    return True


def test_installation():
    """インストールテスト"""
    print("🧪 インストールテストを実行中...")
    
    try:
        # 基本的なインポートテスト
        import torch
        print(f"✅ PyTorch {torch.__version__}")
        
        import transformers
        print(f"✅ Transformers {transformers.__version__}")
        
        import websockets
        print(f"✅ WebSockets {websockets.__version__}")
        
        # GPU利用可能性テスト
        if torch.cuda.is_available():
            print(f"✅ CUDA利用可能 (デバイス数: {torch.cuda.device_count()})")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("✅ MPS（Apple Silicon）利用可能")
        else:
            print("ℹ️  CPU使用（GPU加速なし）")
        
        # FuguMTTranslatorのインポートテスト
        from FuguMTTranslator import Config, FuguMTTranslator
        print("✅ FuguMTTranslator パッケージ")
        
        print("✅ インストールテスト完了")
        return True
        
    except ImportError as e:
        print(f"❌ インストールテスト失敗: {e}")
        return False


def show_next_steps():
    """次のステップの表示"""
    print("\n" + "="*50)
    print("🎉 セットアップ完了！")
    print("="*50)
    print()
    print("次のステップ:")
    print("1. サーバーを起動: python main.py")
    print("2. 設定変更: config/fugumt_translator.ini を編集")
    print("3. ログ確認: logs/fugumt_translator.log を確認")
    print()
    print("デフォルト設定:")
    print("- サーバーアドレス: ws://127.0.0.1:55002")
    print("- 翻訳モデル: FuguMT (staka/fugumt-en-ja)")
    print("- ログレベル: INFO")
    print()
    print("Webブラウザでテスト:")
    print("http://localhost:55002 でテストページにアクセス可能")
    print()
    print("問題が発生した場合:")
    print("- ログファイルを確認してください")
    print("- GPU使用時は適切なCUDAドライバーが必要です")
    print("- メモリ不足の場合は設定ファイルでバッチサイズを調整してください")


def main():
    """メインセットアップ処理"""
    print("🚀 FuguMT翻訳サーバー セットアップ")
    print("="*40)
    
    # Python バージョンチェック
    check_python_version()
    
    # システム要件チェック
    check_system_requirements()
    
    # ディレクトリ作成
    create_directories()
    
    # 依存関係インストール
    if not install_dependencies():
        sys.exit(1)
    
    # 設定ファイル作成
    if not create_config():
        sys.exit(1)
    
    # インストールテスト
    if not test_installation():
        print("⚠️  インストールテストに失敗しましたが、継続します")
    
    # 次のステップ表示
    show_next_steps()


if __name__ == "__main__":
    main()