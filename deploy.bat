@echo off
REM Render Deployment Script for Impossible Challenge

echo =========================================
echo DEPLOYING IMPOSSIBLE CHALLENGE TO RENDER
echo =========================================

REM Get the Render URL from user
set /p RENDER_URL="Enter your Render service URL (e.g., https://impossible-challenge.onrender.com): "

REM Remove trailing slash if present
if "%RENDER_URL:~-1%"=="/" set RENDER_URL=%RENDER_URL:~0,-1%

echo Using URL: %RENDER_URL%

REM Update extension files with new URL
echo.
echo Updating extension files...

REM Update background.js
powershell -Command "(Get-Content extension\background.js) -replace '{{RENDER_URL}}', '%RENDER_URL%' | Set-Content extension\background.js"

REM Update manifest.json
powershell -Command "(Get-Content extension\manifest.json) -replace '{{RENDER_URL}}', '%RENDER_URL%' | Set-Content extension\manifest.json"

REM Update popup.js
powershell -Command "(Get-Content extension\popup.js) -replace '{{RENDER_URL}}', '%RENDER_URL%' | Set-Content extension\popup.js"

REM Update content.js
powershell -Command "(Get-Content extension\content.js) -replace '{{RENDER_URL}}', '%RENDER_URL%' | Set-Content extension\content.js"

REM Re-package extension
echo.
echo Re-packaging extension...
if exist static\extension\impossible_ext.zip del static\extension\impossible_ext.zip
cd extension
powershell -Command "Compress-Archive -Path *.js,*.json,*.html,*.css -DestinationPath ..\static\extension\impossible_ext.zip"
cd ..

echo.
echo =========================================
echo DEPLOYMENT PREPARATION COMPLETE!
echo =========================================
echo.
echo Next steps:
echo 1. Push this code to your GitHub repository
echo 2. Go to https://dashboard.render.com
echo 3. Click 'New +' -^> 'Web Service'
echo 4. Connect your GitHub repository
echo 5. Configure:
echo    - Name: impossible-challenge
echo    - Runtime: Python
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: gunicorn --worker-class eventlet -w 1 server:app
echo 6. Add Environment Variable:
echo    - Key: BASE_URL
echo    - Value: %RENDER_URL%
echo 7. Click 'Create Web Service'
echo.
echo Flag: UITCTF{y0u_f0und_th3_h1dd3n_p13c3s_t0g3th3r_w3ll_d0n3!}
echo =========================================
pause
