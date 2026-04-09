@echo off
setlocal EnableDelayedExpansion
chcp 65001 > nul

echo ====================================================
echo   🚀 정글부킹 AEO 랜딩페이지 자동 배포 스크립트 🚀
echo ====================================================
echo.

cd /d "%~dp0"

IF NOT EXIST ".git" (
    echo [초기화] Git 저장소를 생성합니다...
    git init
    git branch -M main
    echo.
    set /p REMOTE_URL="배포할 Github 저장소 URL을 입력하세요 (예: https://github.com/my-acc/repo.git): "
    git remote add origin !REMOTE_URL!
    echo.
)

echo [1/3] 변경 변경사항을 스캔합니다...
git add .

echo [2/3] 커밋을 생성합니다...
git commit -m "Auto Deploy: 정글부킹 AEO 랜딩페이지 업데이트 (%date%)"

echo [3/3] Github Pages 서버로 배포(Push)를 시작합니다...
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo ❌ 배포 중 오류가 발생했습니다. 저장소 권한이나 상태를 확인해주세요.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo   🎉 배포 완료!
echo   Github Pages 설정(Settings) -^> Pages 메뉴 배포 현황을 확인하세요!
echo ====================================================
pause
