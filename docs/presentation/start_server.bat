@echo off
echo Starting DB Report Chat App Documentation Server...
echo.

cd /d "%~dp0..\.."
echo Current directory: %CD%
echo.

echo Starting Python HTTP server...
echo Documentation will be available at: http://localhost:8000/docs/presentation/
echo.
echo Press Ctrl+C to stop the server
echo.

python -m http.server 8000 