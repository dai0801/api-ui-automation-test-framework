@echo off
setlocal
chcp 65001 >nul

cd /d "%~dp0"

echo.
echo ======================================
echo 自动化测试 - 安全回归
echo ======================================
echo.

REM ======================================
REM 检查虚拟环境
REM ======================================

if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] 未找到虚拟环境 .venv
    echo 请先创建虚拟环境并安装项目依赖。
    echo.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

REM ======================================
REM 安全回归环境
REM ======================================

REM 普通回归执行结束后立即关闭浏览器
set KEEP_BROWSER_SECONDS=0

REM 普通回归禁止真实外呼
set ALLOW_TEST_CALL=false

REM 统一Python终端输出编码
set PYTHONIOENCODING=utf-8

REM ======================================
REM 创建报告目录
REM ======================================

if not exist "reports" (
    mkdir reports
)

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TIMESTAMP=%%i

set REPORT_FILE=reports\regression_%TIMESTAMP%.html

echo 本次执行：
echo.
echo [1] 居民接口自动化
echo [2] 登录 UI 自动化
echo [3] 电话任务统计 UI 自动化
echo.
echo 安全策略：
echo - 仅执行 regression 标记用例
echo - 不执行 live_call 真实外呼用例
echo - ALLOW_TEST_CALL=false
echo - UI 执行结束后自动关闭浏览器
echo.
echo ======================================
echo 开始执行
echo ======================================
echo.

REM ======================================
REM 执行安全回归
REM
REM 双重保护：
REM 1. 只指定安全测试文件
REM 2. 只执行 regression 标记用例
REM ======================================

python -m pytest ^
tests\test_dweller.py ^
tests\test_login.py ^
tests\test_statistics.py ^
-m regression ^
-s ^
--html="%REPORT_FILE%" ^
--self-contained-html

set TEST_RESULT=%ERRORLEVEL%

echo.
echo ======================================

if "%TEST_RESULT%"=="0" (
    echo 回归测试：全部通过
) else (
    echo 回归测试：存在失败用例
)

echo ======================================
echo.

REM ======================================
REM 打开HTML报告
REM ======================================

if exist "%REPORT_FILE%" (
    echo HTML测试报告：
    echo %REPORT_FILE%
    echo.
    echo 正在打开测试报告...
    start "" "%REPORT_FILE%"
) else (
    echo [WARNING] 没有找到HTML测试报告。
)

echo.

REM ======================================
REM 最终结果
REM ======================================

if "%TEST_RESULT%"=="0" (
    echo 测试结果：PASS
) else (
    echo 测试结果：FAIL
    echo 请查看终端失败信息或HTML报告。
)

echo.
pause

endlocal & exit /b %TEST_RESULT%
