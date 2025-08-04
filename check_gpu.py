#!/usr/bin/env python3
"""
GPU環境チェックスクリプト

FuguMT翻訳サーバーで利用可能なGPU環境を確認します。
"""

import sys
import platform


def check_python_environment():
    """Python環境チェック"""
    print("🐍 Python環境:")
    print(f"   バージョン: {sys.version}")
    print(f"   プラットフォーム: {platform.platform()}")
    print()


def check_pytorch():
    """PyTorch環境チェック"""
    print("🔥 PyTorch環境:")
    
    try:
        import torch
        print(f"   PyTorch: {torch.__version__}")
        print(f"   CUDA利用可能: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"   CUDAバージョン: {torch.version.cuda}")
            gpu_count = torch.cuda.device_count()
            print(f"   GPUデバイス数: {gpu_count}")
            print()
            print("   利用可能なGPU:")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_properties = torch.cuda.get_device_properties(i)
                gpu_memory = gpu_properties.total_memory / (1024**3)
                compute_capability = f"{gpu_properties.major}.{gpu_properties.minor}"
                
                # メモリ使用状況（可能であれば）
                try:
                    torch.cuda.empty_cache()
                    allocated = torch.cuda.memory_allocated(i) / (1024**3)
                    cached = torch.cuda.memory_reserved(i) / (1024**3)
                    free = gpu_memory - cached
                    print(f"   GPU {i}: {gpu_name}")
                    print(f"      メモリ: {gpu_memory:.1f}GB (使用中: {cached:.1f}GB, 空き: {free:.1f}GB)")
                    print(f"      Compute Capability: {compute_capability}")
                    print(f"      設定例: device = cuda, gpu_id = {i}")
                except Exception:
                    print(f"   GPU {i}: {gpu_name}")
                    print(f"      メモリ: {gpu_memory:.1f}GB")
                    print(f"      Compute Capability: {compute_capability}")
                    print(f"      設定例: device = cuda, gpu_id = {i}")
                print()
            
            if gpu_count > 1:
                print("   🔍 複数GPUが検出されました！")
                print("   設定ファイルでGPU IDを指定することで特定のGPUを使用できます:")
                print("   config/fugumt_translator.ini の [TRANSLATION] セクションで")
                print("   device = cuda")
                print("   gpu_id = 0  # 使用したいGPUのID（0から始まる）")
                print()
        
        # Apple Silicon (MPS) チェック
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            print("   MPS（Apple Silicon）: 利用可能")
        
        print()
        
    except ImportError:
        print("   ❌ PyTorchがインストールされていません")
        print("      pip install torch でインストールしてください")
        print()


def check_transformers():
    """Transformers環境チェック"""
    print("🤗 Transformers環境:")
    
    try:
        import transformers
        print(f"   Transformers: {transformers.__version__}")
        print()
    except ImportError:
        print("   ❌ Transformersがインストールされていません")
        print("      pip install transformers でインストールしてください")
        print()


def check_websockets():
    """WebSockets環境チェック"""
    print("🌐 WebSockets環境:")
    
    try:
        import websockets
        print(f"   WebSockets: {websockets.__version__}")
        print()
    except ImportError:
        print("   ❌ WebSocketsがインストールされていません")
        print("      pip install websockets でインストールしてください")
        print()


def check_fugumt_model():
    """FuguMTモデルアクセスチェック"""
    print("🐡 FuguMTモデルアクセステスト:")
    
    try:
        from transformers import MarianTokenizer, MarianMTModel
        
        model_name = "staka/fugumt-en-ja"
        print(f"   モデル: {model_name}")
        
        # トークナイザーテスト
        print("   トークナイザー読み込み中...")
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        print("   ✅ トークナイザー読み込み成功")
        
        # モデルテスト（メモリ使用量が多いため注意）
        print("   モデル読み込み中...")
        model = MarianMTModel.from_pretrained(model_name)
        print("   ✅ モデル読み込み成功")
        
        # 簡単な翻訳テスト
        print("   翻訳テスト中...")
        inputs = tokenizer("Hello world", return_tensors="pt")
        outputs = model.generate(**inputs, max_length=50, num_beams=4)
        translated = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"   テスト翻訳: 'Hello world' -> '{translated}'")
        print("   ✅ 翻訳テスト成功")
        print()
        
    except Exception as e:
        print(f"   ❌ エラー: {e}")
        print("   ネットワーク接続またはモデルダウンロードに問題があります")
        print()


def check_system_resources():
    """システムリソースチェック"""
    print("💻 システムリソース:")
    
    try:
        import psutil
        
        # CPU情報
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"   CPU: {cpu_count}コア (使用率: {cpu_percent}%)")
        
        # メモリ情報
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_percent = memory.percent
        print(f"   メモリ: {memory_gb:.1f}GB (使用率: {memory_percent}%)")
        
        if memory_gb < 4:
            print("   ⚠️  メモリが4GB未満です。動作が制限される可能性があります。")
        elif memory_gb < 8:
            print("   ⚠️  メモリが8GB未満です。大きなモデルで問題が生じる可能性があります。")
        
        # ディスク容量
        disk = psutil.disk_usage('.')
        disk_gb = disk.free / (1024**3)
        print(f"   利用可能ディスク容量: {disk_gb:.1f}GB")
        
        if disk_gb < 5:
            print("   ⚠️  ディスク容量が不足しています。モデルダウンロードに必要です。")
        
        print()
        
    except ImportError:
        print("   psutilがインストールされていません（オプション）")
        print("   pip install psutil でより詳細な情報を確認できます")
        print()


def run_comprehensive_test():
    """総合テスト"""
    print("🧪 総合動作テスト:")
    
    try:
        # FuguMTTranslatorのインポートテスト
        from FuguMTTranslator import Config, FuguMTTranslator
        
        print("   設定ファイル作成テスト...")
        config = Config()
        print("   ✅ 設定ファイル作成成功")
        
        print("   翻訳エンジン初期化テスト...")
        # 注意: これは時間がかかりメモリを大量に使用します
        print("   (この処理には時間がかかります...)")
        translator = FuguMTTranslator(config)
        print("   ✅ 翻訳エンジン初期化成功")
        
        print("   ヘルスチェックテスト...")
        health = translator.health_check()
        print(f"   ヘルス状態: {health['status']}")
        print(f"   使用デバイス: {health['device']}")
        
        # 使用中のGPU詳細情報を表示
        if health['device'].startswith('cuda'):
            import torch
            if ':' in health['device']:
                gpu_id = int(health['device'].split(':')[1])
            else:
                gpu_id = torch.cuda.current_device()
            
            gpu_name = torch.cuda.get_device_name(gpu_id)
            gpu_memory = torch.cuda.get_device_properties(gpu_id).total_memory / (1024**3)
            try:
                allocated = torch.cuda.memory_allocated(gpu_id) / (1024**3)
                print(f"   使用GPU詳細: {gpu_name} (ID: {gpu_id})")
                print(f"   GPU メモリ: {gpu_memory:.1f}GB (現在使用中: {allocated:.1f}GB)")
            except Exception:
                print(f"   使用GPU詳細: {gpu_name} (ID: {gpu_id}, メモリ: {gpu_memory:.1f}GB)")
        
        print("   ✅ 総合テスト成功")
        print()
        
    except Exception as e:
        print(f"   ❌ 総合テストエラー: {e}")
        print("   setup.py を実行してセットアップを完了してください")
        print()


def main():
    """メイン処理"""
    print("="*50)
    print("🔍 FuguMT翻訳サーバー 環境チェック")
    print("="*50)
    print()
    
    # 基本環境チェック
    check_python_environment()
    check_pytorch()
    check_transformers()
    check_websockets()
    
    # システムリソースチェック
    check_system_resources()
    
    # FuguMTモデルチェック
    check_fugumt_model()
    
    # 総合テスト
    run_comprehensive_test()
    
    print("="*50)
    print("✅ 環境チェック完了")
    print("="*50)
    print()
    print("推奨事項:")
    print("- GPU利用時は十分なメモリ（8GB以上）を確保してください")
    print("- 初回実行時はモデルダウンロードに時間がかかります")
    print("- 安定した動作にはネットワーク接続が必要です")


if __name__ == "__main__":
    main()