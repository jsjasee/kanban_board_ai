@echo off
set IMAGE_NAME=pm-mvp
set CONTAINER_NAME=pm-mvp-app

docker build -t %IMAGE_NAME% .
if errorlevel 1 exit /b 1

docker rm -f %CONTAINER_NAME% >nul 2>nul
docker run -d --name %CONTAINER_NAME% --env-file .env -p 8000:8000 %IMAGE_NAME%
