# FuguMT翻訳サーバー 🌸

リアルタイム翻訳専用AI WebSocketサーバー

## 概要

FuguMTモデルを使用したオフライン翻訳サービスを提供するローカルWebSocketサーバーです。Unity アプリケーションやその他のクライアントアプリケーション向けに、高品質なリアルタイム翻訳サービスを提供します。

**主な特徴:**

* FuguMT (staka/fugumt-en-ja) モデルを使用したオフライン翻訳
* WebSocket通信によるリアルタイム処理
* 英日・日英翻訳対応
* GPU/MPS/CPU 自動選択対応
* 優先度別リクエスト処理
* 自動設定ファイル生成
* 詳細なログ機能
* 統計情報取得API

## FuguMTについて

FuguMTは[s-takaさん](https://staka.jp/wordpress/?p=413)が開発したオープンソースの英日・日英翻訳モデルです：

- MarianNMTベースで構築
- BLEU score 31.65（GPT-3.5の27.04、GPT-4の29.66より高性能）
- CC BY-SA 4.0ライセンス
- Hugging Face: [staka/fugumt-en-ja](https://huggingface.co/staka/fugumt-en-ja)

## システム要件

* **Python**: 3.8 以上
* **メモリ**: 8GB以上推奨（GPU使用時）
* **GPU**: NVIDIA GPU (CUDA対応) またはApple Silicon推奨（CPUでも動作可能）
* **ストレージ**: 5GB以上の空き容量（モデルダウンロード用）
* **ネットワーク**: 初回実行時のモデルダウンロードに必要

## インストール

### 自動インストール（推奨）

#### Windows

```batch
# プロジェクトをダウンロード
git clone https://github.com/your-username/MenZ-FuguMT.git
cd MenZ-FuguMT

# 自動セットアップを実行
setup.bat

# サーバーを起動
run.bat
```

#### Linux/macOS

```bash
# プロジェクトをダウンロード
git clone https://github.com/your-username/MenZ-FuguMT.git
cd MenZ-FuguMT

# 自動セットアップを実行
chmod +x setup.sh
./setup.sh

# サーバーを起動
./run.sh
```

### 手動インストール

```bash
# 依存関係をインストール
pip install -r requirements.txt

# 必要なディレクトリを作成
mkdir -p config logs

# 設定ファイルを作成
python setup.py

# サーバーを起動
python main.py
```

## 設定

設定ファイル `config/fugumt_translator.ini` を編集して、サーバーの動作をカスタマイズできます。

### 主要設定

```ini
[SERVER]
host = 127.0.0.1
port = 55002
max_connections = 50

[TRANSLATION]
model_name_en_ja = staka/fugumt-en-ja
model_name_ja_en = staka/fugumt-ja-en
device = auto  # auto, cpu, cuda, mps
max_length = 512
num_beams = 4
temperature = 1.0

[LOGGING]
level = INFO
file = logs/fugumt_translator.log

[PERFORMANCE]
batch_size = 1
timeout_seconds = 30.0
worker_threads = 4
```

### デバイス設定

* `auto`: 自動選択（CUDA → MPS → CPU の順）
* `cuda`: NVIDIA GPU使用
* `mps`: Apple Silicon GPU使用
* `cpu`: CPU使用

## 使用方法

### サーバー起動

```bash
# デフォルト設定で起動
python main.py

# ポート指定
python main.py --port 8080

# ホスト指定（外部アクセス許可）
python main.py --host 0.0.0.0 --port 8080

# 設定ファイル指定
python main.py --config my_config.ini
```

### WebSocket接続

```javascript
const ws = new WebSocket('ws://127.0.0.1:55002');
```

### 翻訳リクエスト

```json
{
    "type": "translation",
    "request_id": "unique-request-id",
    "text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "ja",
    "priority": "high"
}
```

### レスポンス

```json
{
    "request_id": "unique-request-id",
    "translated": "こんにちは、元気ですか？",
    "source_text": "Hello, how are you?",
    "source_lang": "en",
    "target_lang": "ja",
    "processing_time_ms": 250.5,
    "status": "completed",
    "context_id": "speaker-1"
}
```

## API リファレンス

### リクエストタイプ

#### 翻訳リクエスト (`type: "translation"`)

| パラメータ | 型 | 必須 | 説明 |
|-----------|----|----|------|
| `text` | string | ✅ | 翻訳対象テキスト |
| `source_lang` | string | | 源言語（デフォルト: "en"） |
| `target_lang` | string | | 目標言語（デフォルト: "ja"） |
| `request_id` | string | | リクエストID（省略時自動生成） |
| `priority` | string | | 優先度（"high", "normal", "low"） |

#### Pingリクエスト (`type: "ping"`)

接続確認用のリクエスト。

#### 統計情報リクエスト (`type: "stats"`)

サーバーと翻訳エンジンの統計情報を取得。

#### ヘルスチェックリクエスト (`type: "health"`)

サーバーの健康状態を確認。

### 言語コード

| 言語 | コード |
|------|--------|
| 英語 | `en` |
| 日本語 | `ja` |

## Unity での使用例

```csharp
using System;
using System.Threading.Tasks;
using UnityEngine;
using WebSocketSharp;

public class FuguMTClient : MonoBehaviour
{
    private WebSocket ws;
    
    void Start()
    {
        ws = new WebSocket("ws://127.0.0.1:55002");
        ws.OnMessage += OnMessage;
        ws.Connect();
    }
    
    public void TranslateText(string text, string sourceLang = "en", string targetLang = "ja")
    {
        var request = new
        {
            type = "translation",
            request_id = Guid.NewGuid().ToString(),
            text = text,
            source_lang = sourceLang,
            target_lang = targetLang
        };
        
        ws.Send(JsonUtility.ToJson(request));
    }
    
    private void OnMessage(object sender, MessageEventArgs e)
    {
        var response = JsonUtility.FromJson<TranslationResponse>(e.Data);
        Debug.Log($"翻訳結果: {response.translated}");
    }
}

[Serializable]
public class TranslationResponse
{
    public string request_id;
    public string translated;
    public string status;
}
```

## Python クライアントの例

```python
import asyncio
import websockets
import json

async def translate_text(text, source_lang="en", target_lang="ja"):
    uri = "ws://127.0.0.1:55002"
    
    async with websockets.connect(uri) as websocket:
        request = {
            "type": "translation",
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        result = json.loads(response)
        
return result["translated"]

# 使用例
async def main():
    translation = await translate_text("Hello world!")
    print(f"翻訳結果: {translation}")

asyncio.run(main())
```

## トラブルシューティング

### GPU が認識されない

```bash
# GPU環境をチェック
python check_gpu.py

# NVIDIA GPU
nvidia-smi

# 依存関係を再インストール
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 翻訳が遅い

1. **設定ファイルを調整**:
   ```ini
   [TRANSLATION]
   device = cuda  # または mps
   num_beams = 2  # ビーム数を減らす
   max_length = 256  # 最大長を短縮
   
   [PERFORMANCE]
   batch_size = 4  # バッチサイズを増加
   ```

2. **メモリ不足の場合**:
   ```ini
   [TRANSLATION]
   num_beams = 1
   max_length = 128
   ```

### 接続エラー

1. **ファイアウォール設定を確認**
2. **ポートが使用されていないか確認**:
   ```bash
   # Windows
   netstat -an | findstr :55002
   
   # Linux/macOS
   lsof -i :55002
   ```

### モデルダウンロードエラー

1. **ネットワーク接続を確認**
2. **Hugging Face Hubの設定**:
   ```bash
   # キャッシュクリア
   rm -rf ~/.cache/huggingface/
   
   # 手動ダウンロード
   python -c "from transformers import MarianTokenizer, MarianMTModel; MarianTokenizer.from_pretrained('staka/fugumt-en-ja'); MarianMTModel.from_pretrained('staka/fugumt-en-ja')"
   ```

## 開発者向け情報

### プロジェクト構造

```
MenZ-FuguMT/
├── FuguMTTranslator/              # メインパッケージ
│   ├── __init__.py
│   ├── config.py                  # 設定管理
│   ├── translator.py              # 翻訳エンジン
│   └── websocket_server.py        # WebSocketサーバー
├── config/
│   └── fugumt_translator.ini      # 設定ファイル
├── logs/                          # ログファイル
├── main.py                        # エントリーポイント
├── setup.py                       # セットアップスクリプト
├── requirements.txt               # 依存関係
├── setup.bat / setup.sh           # 自動セットアップ
├── run.bat / run.sh               # 実行スクリプト
├── check_gpu.py                   # GPU環境チェック
└── README.md                      # このファイル
```

### ログファイル

ログは以下の場所に出力されます：

- **Windows**: `logs\\fugumt_translator.log`
- **Linux/macOS**: `logs/fugumt_translator.log`

### パフォーマンスチューニング

1. **GPU最適化**:
   ```ini
   [TRANSLATION]
   device = cuda
   use_cache = true
   
   [PERFORMANCE]
   worker_threads = 2
   batch_size = 8
   ```

2. **CPU最適化**:
   ```ini
   [TRANSLATION]
   device = cpu
   num_beams = 1
   max_length = 256
   
   [PERFORMANCE]
   worker_threads = 4
   batch_size = 1
   ```

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

ただし、使用するFuguMTモデルは**CC BY-SA 4.0ライセンス**の下で配布されており、研究用途での使用が前提となっています。商用利用の際は、モデルライセンスを十分にご確認ください。

## 謝辞

- **FuguMTモデル**: [s-takaさん](https://staka.jp/wordpress/?p=413)による優秀な翻訳モデルの提供に感謝いたします
- **参考プロジェクト**: [MenZ-translation](https://github.com/zagan-the-gun/MenZ-translation)のアーキテクチャを参考にさせていただきました
- **Marian NMT**: MarianNMTフレームワークの開発チームに感謝いたします

## 貢献

プルリクエストやイシューの報告を歓迎します。

## サポート

問題が発生した場合は、GitHub Issues でお知らせください。

---

**FuguMT翻訳サーバー** - 高品質なオフライン翻訳サービスをあなたのアプリケーションに 🌸