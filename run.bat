@echo off
:: FuguMT翻訳サーバー Windows実行スクリプト
::
:: このスクリプトはWindows環境でFuguMT翻訳サーバーを起動します。
::

title FuguMT翻訳サーバー

echo.
echo ==========================================
echo 🌸 FuguMT翻訳サーバー 起動
echo ==========================================
echo.

:: 仮想環境の確認とアクティベート
if not exist "venv" (
    echo ❌ 仮想環境が見つかりません。
    echo    setup.bat を実行してセットアップを完了してください。
    pause
    exit /b 1
)

echo 🔧 仮想環境をアクティベート中...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ❌ 仮想環境のアクティベートに失敗しました。
    echo    setup.bat を実行してセットアップを完了してください。
    pause
    exit /b 1
)

:: 必要なディレクトリが存在するか確認
if not exist "FuguMTTranslator" (
    echo ❌ FuguMTTranslatorパッケージが見つかりません。
    echo    setup.bat を実行してセットアップを完了してください。
    pause
    exit /b 1
)

:: main.pyが存在するか確認
if not exist "main.py" (
    echo ❌ main.pyが見つかりません。
    echo    ファイルが破損している可能性があります。
    pause
    exit /b 1
)

echo 🚀 サーバーを起動しています...
echo 🛑 サーバーを停止するには Ctrl+C を押してください
echo.

:: サーバー起動
python main.py

echo.
echo サーバーが停止されました。
pause