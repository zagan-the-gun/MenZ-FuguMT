#!/bin/bash
# FuguMT翻訳サーバー Linux/macOSセットアップスクリプト
#
# このスクリプトはLinux/macOS環境でFuguMT翻訳サーバーのセットアップを自動化します。
#

set -e

echo
echo "=========================================="
echo "🚀 FuguMT翻訳サーバー セットアップ"
echo "=========================================="
echo

## CPU前提でセットアップ（GPU選択は行わない）

# Python確認
echo "🔍 Python環境を確認中..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Pythonが見つかりません。"
        echo "   Python 3.8以上をインストールしてください。"
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD --version

# Pythonバージョンチェック
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ]; then
    echo "❌ Python 3.8以上が必要です"
    exit 1
fi

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]; then
    echo "❌ Python 3.8以上が必要です"
    exit 1
fi

echo

# 仮想環境の作成
echo "🔧 仮想環境を作成中..."
if [ ! -d "venv" ]; then
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ 仮想環境の作成に失敗しました"
        exit 1
    fi
    echo "✅ 仮想環境を作成しました"
else
    echo "ℹ️  仮想環境は既に存在します"
fi

# 仮想環境のアクティベート
echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 仮想環境のアクティベートに失敗しました"
    exit 1
fi
echo "✅ 仮想環境をアクティベートしました"

# pip確認・アップグレード
echo "📦 pipをアップグレード中..."
python -m pip install --upgrade pip setuptools wheel
echo

echo "🎛  GPUモード: cpu (固定)"

# OS判定とGPU環境確認
echo "🖥️  システム情報:"
uname -a
echo

if command -v nvidia-smi &> /dev/null; then
    echo "🎮 NVIDIA GPU情報:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    echo
fi

# Apple Silicon確認（macOS）
if [[ "$OSTYPE" == "darwin"* ]]; then
    if [[ $(uname -m) == "arm64" ]]; then
        echo "✅ Apple Silicon検出（MPS利用可能）"
    else
        echo "ℹ️  Intel Mac"
    fi
    echo
fi

# セットアップスクリプト実行
echo "🔧 セットアップスクリプトを実行中..."
python setup.py

if [ $? -ne 0 ]; then
    echo
    echo "❌ セットアップに失敗しました。"
    echo "   エラーログを確認してください。"
    exit 1
fi

echo
echo "✅ セットアップが完了しました！"
echo

## CUDA版のインストールは行いません（CPU前提）

echo "次のステップ:"
echo "  1. ./run.sh を実行してサーバーを起動"
echo "  2. Webブラウザで ws://127.0.0.1:55002 に接続"
echo "  3. 設定変更は config/fugumt_translator.ini を編集"
echo ""
echo "開発用（オプション）:"
echo "  - 仮想環境を手動で使用: source venv/bin/activate"
echo

# 実行権限付与
chmod +x run.sh
echo "🔧 run.sh に実行権限を付与しました"