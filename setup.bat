@echo off
:: FuguMT翻訳サーバー Windowsセットアップスクリプト
:: 
:: このスクリプトはWindows環境でFuguMT翻訳サーバーのセットアップを自動化します。
::

title FuguMT翻訳サーバー セットアップ

echo.
echo ==========================================
echo 🚀 FuguMT翻訳サーバー セットアップ
echo ==========================================
echo.

:: Python確認
echo 🔍 Python環境を確認中...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Pythonが見つかりません。
    echo    Python 3.8以上をインストールしてください。
    echo    https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version

:: Pythonバージョンチェック（簡易版）
for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
echo Pythonバージョン: %PYTHON_VERSION%
echo.

:: 仮想環境の作成
echo 🔧 仮想環境を作成中...
if not exist "venv" (
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ❌ 仮想環境の作成に失敗しました
        pause
        exit /b 1
    )
    echo ✅ 仮想環境を作成しました
) else (
    echo ℹ️  仮想環境は既に存在します
)

:: 仮想環境のアクティベート
echo 🔧 仮想環境をアクティベート中...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ❌ 仮想環境のアクティベートに失敗しました
    pause
    exit /b 1
)
echo ✅ 仮想環境をアクティベートしました

:: pip確認・アップグレード
echo 📦 pipをアップグレード中...
python -m pip install --upgrade pip setuptools wheel
echo.

:: セットアップスクリプト実行
echo 🔧 セットアップスクリプトを実行中...
python setup.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ セットアップに失敗しました。
    echo    エラーログを確認してください。
    pause
    exit /b 1
)

echo.
echo ✅ セットアップが完了しました！
echo.
echo 次のステップ:
echo   1. run.bat を実行してサーバーを起動
echo   2. Webブラウザで ws://127.0.0.1:55002 に接続
echo   3. 設定変更は config/fugumt_translator.ini を編集
echo.
echo 開発用（オプション）:
echo   - 仮想環境を手動で使用: venv\Scripts\activate.bat
echo.

pause