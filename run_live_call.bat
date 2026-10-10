@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

echo.
echo ======================================
echo LIVE CALL AUTOMATION TEST
echo ======================================
echo.
echo WARNING:
echo This test may create a real authorized test task
echo and may trigger a phone call to the authorized test number.
echo.
echo Normal regression does NOT run this test.
echo.

REM ======================================
REM Manual confirmation
REM ======================================

set /p CONFIRM=Type CALL to continue:

if /I not "%CONFIRM%"=="CALL" (
    echo.
    echo Live call test cancelled.
    echo.
    pause
    endlocal
    exit /b 0
)

echo.
echo Confirmation accepted.
echo.

REM ======================================
REM Check virtual environment
REM ======================================

if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: .venv was not found.
    echo Please create the virtual environment
    echo and install project dependencies first.
    echo.
    pause
    endlocal
    exit /b 1
)

REM ======================================
REM Check target test file
REM ======================================

if not exist "tests\test_invite_flow.py" (
    echo ERROR: tests\test_invite_flow.py was not found.
    echo.
    pause
    endlocal
    exit /b 1
)

REM ======================================
REM Activate virtual environment
REM ======================================

call ".venv\Scripts\activate.bat"

REM ======================================
REM Live-call test environment
REM ======================================

REM Only this script enables authorized live-call execution.
set ALLOW_TEST_CALL=true

REM Keep headed browser open for up to 2 minutes.
set KEEP_BROWSER_SECONDS=120

REM Keep Python console output readable.
set PYTHONIOENCODING=utf-8

REM ======================================
REM Create report directory
REM ======================================

if not exist "reports" (
    mkdir reports
)

REM ======================================
REM Generate timestamp
REM ======================================

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TIMESTAMP=%%i

set REPORT_FILE=reports\live_call_%TIMESTAMP%.html

echo.
echo ======================================
echo Starting live call automation...
echo ======================================
echo.
echo Safety:
echo - Manual CALL confirmation: enabled
echo - ALLOW_TEST_CALL=true only in this script
echo - Only tests\test_invite_flow.py is targeted
echo - Only live_call marked tests are executed
echo.
echo Browser mode: HEADED
echo Browser keep time: 120 seconds
echo Report:
echo %REPORT_FILE%
echo.

REM ======================================
REM Run authorized live-call test
REM
REM Double isolation:
REM 1. Explicitly target test_invite_flow.py
REM 2. Execute only tests marked live_call
REM ======================================

python -m pytest ^
tests\test_invite_flow.py ^
-m live_call ^
--headed ^
-s ^
-v ^
--html="%REPORT_FILE%" ^
--self-contained-html

REM ======================================
REM Save pytest exit code
REM ======================================

set TEST_RESULT=%ERRORLEVEL%

echo.
echo ======================================

if "%TEST_RESULT%"=="0" (
    echo LIVE CALL TEST: PASS
) else (
    echo LIVE CALL TEST: FAIL
)

echo ======================================
echo.

REM ======================================
REM Open HTML report
REM ======================================

if exist "%REPORT_FILE%" (
    echo HTML report:
    echo %REPORT_FILE%
    echo.
    echo Opening HTML report...
    start "" "%REPORT_FILE%"
) else (
    echo WARNING: HTML report was not found.
)

echo.

REM ======================================
REM Final result
REM ======================================

if "%TEST_RESULT%"=="0" (
    echo Test completed successfully.
) else (
    echo Test failed.
    echo Please check the terminal output
    echo and HTML report for details.
)

echo.
pause

endlocal & exit /b %TEST_RESULT%
