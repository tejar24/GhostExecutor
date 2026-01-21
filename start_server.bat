@echo off
echo Starting Ghost-QC Server...
echo.
echo Frontend will be available at: http://localhost:8000
echo API docs available at: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
python -m uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
pause
