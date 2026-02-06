@echo off
echo ========================================
echo Git Quick Setup Script
echo ========================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed!
    echo.
    echo Please download and install Git from:
    echo https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

echo [OK] Git is installed
echo.

REM Initialize repository if needed
if not exist .git (
    echo Initializing Git repository...
    git init
    echo [OK] Repository initialized
) else (
    echo [OK] Repository already initialized
)

echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Configure Git (first time only):
echo    git config --global user.name "Your Name"
echo    git config --global user.email "your.email@example.com"
echo.
echo 2. Create first commit:
echo    git add .
echo    git commit -m "Initial commit - iCapture System"
echo.
echo 3. Create GitHub repository at:
echo    https://github.com/new
echo.
echo 4. Link to GitHub (replace YOUR_USERNAME):
echo    git remote add origin https://github.com/YOUR_USERNAME/icapture-system.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo ========================================
echo Read GIT_SETUP_GUIDE.md for detailed instructions!
echo ========================================
pause
