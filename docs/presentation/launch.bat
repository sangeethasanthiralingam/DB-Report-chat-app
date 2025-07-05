@echo off
echo Starting DB Report Chat App Documentation Presentation...
echo.
echo Starting server from project root...
cd /d "%~dp0..\.."
echo Current directory: %CD%
echo.
echo Starting HTTP server on port 8000...
echo.
echo Opening presentation in your default browser...
start http://localhost:8000/docs/presentation/
echo.
echo Server is running at: http://localhost:8000
echo Presentation is at: http://localhost:8000/docs/presentation/
echo.
echo Press Ctrl+C to stop the server
echo.
python -m http.server 8000 