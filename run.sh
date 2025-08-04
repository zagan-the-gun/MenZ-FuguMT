#!/bin/bash
# FuguMT翻訳サーバー Linux/macOS実行スクリプト
#
# このスクリプトはLinux/macOS環境でFuguMT翻訳サーバーを起動します。
#

set -e

echo
echo "=========================================="
echo "🌸 FuguMT翻訳サーバー 起動"
echo "=========================================="
echo

# 仮想環境の確認とアクティベート
if [ ! -d "venv" ]; then
    echo "❌ 仮想環境が見つかりません。"
    echo "   ./setup.sh を実行してセットアップを完了してください。"
    exit 1
fi

echo "🔧 仮想環境をアクティベート中..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "❌ 仮想環境のアクティベートに失敗しました。"
    echo "   ./setup.sh を実行してセットアップを完了してください。"
    exit 1
fi

PYTHON_CMD="python"

# 必要なディレクトリが存在するか確認
if [ ! -d "FuguMTTranslator" ]; then
    echo "❌ FuguMTTranslatorパッケージが見つかりません。"
    echo "   ./setup.sh を実行してセットアップを完了してください。"
    exit 1
fi

# main.pyが存在するか確認
if [ ! -f "main.py" ]; then
    echo "❌ main.pyが見つかりません。"
    echo "   ファイルが破損している可能性があります。"
    exit 1
fi

# GPU情報表示（参考用）
if command -v nvidia-smi &> /dev/null; then
    echo "🎮 利用可能GPU:"
    nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader
    echo
fi

echo "🚀 サーバーを起動しています..."
echo "🛑 サーバーを停止するには Ctrl+C を押してください"
echo

# サーバー起動
$PYTHON_CMD main.py "$@"

echo
echo "サーバーが停止されました。"