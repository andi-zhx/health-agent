@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo 正在安装医疗系统所需依赖...
echo.
pip install -r requirements.txt
echo.
if errorlevel 1 (
    echo 安装失败，请检查是否已安装 Python 并已将 Python 加入 PATH。
    pause
    exit /b 1
)
echo 依赖安装完成。现在可双击「启动医疗系统.bat」或「启动医疗系统.pyw」启动程序。
echo.
pause
