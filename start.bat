@echo off
chcp 65001 >nul
cd /d "%~dp0site"

where python >nul 2>nul
if errorlevel 1 (
  echo Python не найден. Установите его с https://www.python.org/downloads/ и запустите снова.
  pause
  exit /b 1
)

echo Проверяю зависимости...
python -m pip install -q -r requirements.txt

echo.
echo Сайт:          http://localhost:5000
echo Панель заявок: http://localhost:5000/admin
echo Чтобы остановить сайт, закройте это окно.
echo.

start "" cmd /c "timeout /t 3 >nul & start http://localhost:5000"
python app.py
pause
