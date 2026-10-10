from datetime import datetime
from pathlib import Path

import pytest
from dotenv import load_dotenv

from utils.api_auth import ensure_api_headers
from utils.auth import (
    login_user_center,
    open_chronic_system,
)


# ==================================================
# 项目根目录
# ==================================================

PROJECT_ROOT = Path(
    __file__
).parent


# ==================================================
# 自动加载 .env
# ==================================================

ENV_FILE = (
    PROJECT_ROOT
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_FILE,
    override=False,
)


# ==================================================
# 报告目录
# ==================================================

REPORT_DIR = (
    PROJECT_ROOT
    / "reports"
)

SCREENSHOT_DIR = (
    REPORT_DIR
    / "screenshots"
)


# ==================================================
# Pytest启动时创建报告目录
# ==================================================

def pytest_sessionstart(
    session
):
    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    SCREENSHOT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )


# ==================================================
# Fixture：API鉴权
#
# 一次pytest运行只检查/刷新一次。
# 5个接口测试共用。
# ==================================================

@pytest.fixture(
    scope="session"
)
def api_headers():

    print()
    print(
        "========== Fixture：API鉴权检查 =========="
    )

    headers = (
        ensure_api_headers()
    )

    print(
        "========== API鉴权准备完成 =========="
    )

    return headers


# ==================================================
# Fixture：已登录用户中心
# ==================================================

@pytest.fixture
def user_center_page(
    page
):

    print()
    print(
        "========== Fixture：登录用户中心 =========="
    )

    logged_page = (
        login_user_center(
            page
        )
    )

    yield logged_page


# ==================================================
# Fixture：已进入AI慢病系统
# ==================================================

@pytest.fixture
def chronic_page(
    user_center_page
):

    print()
    print(
        "========== Fixture：进入慢病系统 =========="
    )

    chronic = (
        open_chronic_system(
            user_center_page
        )
    )

    yield chronic


# ==================================================
# UI测试失败自动截图
# ==================================================

@pytest.hookimpl(
    hookwrapper=True
)
def pytest_runtest_makereport(
    item,
    call
):

    outcome = yield

    report = (
        outcome.get_result()
    )

    # ==================================================
    # 只处理测试执行阶段失败
    # ==================================================

    if report.when != "call":
        return

    if not report.failed:
        return

    # ==================================================
    # 获取当前测试页面
    # ==================================================

    page = item.funcargs.get(
        "page"
    )

    if page is None:

        page = item.funcargs.get(
            "user_center_page"
        )

    if page is None:

        page = item.funcargs.get(
            "chronic_page"
        )

    # API测试没有浏览器页面
    if page is None:
        return

    try:

        if page.is_closed():
            return

        # ==================================================
        # 时间戳
        # ==================================================

        timestamp = (
            datetime.now()
            .strftime(
                "%Y%m%d_%H%M%S"
            )
        )

        # ==================================================
        # 安全文件名
        # ==================================================

        safe_name = (
            item.name
            .replace("/", "_")
            .replace("\\", "_")
            .replace(":", "_")
            .replace("[", "_")
            .replace("]", "_")
        )

        screenshot_path = (
            SCREENSHOT_DIR
            / (
                f"{safe_name}_"
                f"{timestamp}.png"
            )
        )

        # ==================================================
        # 保存整页截图
        # ==================================================

        page.screenshot(
            path=str(
                screenshot_path
            ),
            full_page=True,
        )

        print()
        print(
            "======================================"
        )

        print(
            "测试失败，已自动保存页面截图："
        )

        print(
            screenshot_path
        )

        print(
            "======================================"
        )

    except Exception as error:

        print()
        print(
            f"失败截图保存异常：{error}"
        )