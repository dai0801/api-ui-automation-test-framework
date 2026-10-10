import os
import re

from playwright.sync_api import expect


# ==================================================
# Public/demo UI configuration
# ==================================================
#
# Public repositories should not hard-code:
# - real company domains
# - internal application names
# - internal URL paths
#
# These values are provided through environment variables.
# The safe defaults below are only placeholders.
# ==================================================

LOGIN_URL = os.getenv(
    "TEST_LOGIN_URL",
    "https://example.invalid/login",
)

PASSWORD_LOGIN_TEXT = os.getenv(
    "TEST_PASSWORD_LOGIN_TEXT",
    "密码登录",
)

LOGIN_BUTTON_TEXT = os.getenv(
    "TEST_LOGIN_BUTTON_TEXT",
    "立即登录",
)

LOGIN_SUCCESS_TEXT = os.getenv(
    "TEST_LOGIN_SUCCESS_TEXT",
    "用户中心",
)

LOGIN_SUCCESS_URL_PATTERN = os.getenv(
    "TEST_LOGIN_SUCCESS_URL_PATTERN",
    r".*/main.*",
)

TARGET_SYSTEM_NAME = os.getenv(
    "TEST_TARGET_SYSTEM_NAME",
    "业务管理系统",
)

TARGET_SYSTEM_URL_PATTERN = os.getenv(
    "TEST_TARGET_SYSTEM_URL_PATTERN",
    r".*/business-system.*",
)


# ==================================================
# 登录用户中心
# ==================================================

def login_user_center(page):
    """
    Login to the user center with credentials from environment variables.

    The real login URL and UI labels should be configured in .env locally.
    """

    # ==================================================
    # 读取账号密码
    # ==================================================

    account = os.getenv(
        "TEST_LOGIN_ACCOUNT"
    )

    password = os.getenv(
        "TEST_LOGIN_PASSWORD"
    )

    assert account, (
        "没有配置 TEST_LOGIN_ACCOUNT"
    )

    assert password, (
        "没有配置 TEST_LOGIN_PASSWORD"
    )

    # ==================================================
    # 打开登录页面
    # ==================================================

    page.goto(
        LOGIN_URL,
        wait_until="domcontentloaded",
    )

    # ==================================================
    # 选择密码登录
    # ==================================================

    password_login = (
        page.get_by_text(
            PASSWORD_LOGIN_TEXT,
            exact=True,
        )
    )

    expect(
        password_login
    ).to_be_visible(
        timeout=15000
    )

    password_login.click()

    # ==================================================
    # 获取账号密码输入框
    # ==================================================

    inputs = page.locator(
        "input:visible"
    )

    assert (
        inputs.count() >= 2
    ), (
        "没有找到账号密码输入框"
    )

    # ==================================================
    # 输入账号
    # ==================================================

    inputs.nth(0).fill(
        account
    )

    # ==================================================
    # 输入密码
    # ==================================================

    inputs.nth(1).fill(
        password
    )

    # ==================================================
    # 点击登录
    # ==================================================

    login_button = (
        page.get_by_role(
            "button",
            name=LOGIN_BUTTON_TEXT,
        )
    )

    expect(
        login_button
    ).to_be_visible(
        timeout=10000
    )

    login_button.click()

    # ==================================================
    # 验证登录成功
    # ==================================================

    expect(
        page.get_by_text(
            LOGIN_SUCCESS_TEXT,
            exact=True,
        ).first
    ).to_be_visible(
        timeout=20000
    )

    expect(
        page
    ).to_have_url(
        re.compile(
            LOGIN_SUCCESS_URL_PATTERN
        ),
        timeout=20000,
    )

    print(
        "公共登录模块：用户中心登录成功"
    )

    return page


# ==================================================
# 从用户中心进入目标业务系统
#
# 函数名保留 open_chronic_system，
# 以兼容现有测试代码和 Fixture。
# 公共仓库中不再暴露真实系统名称。
# ==================================================

def open_chronic_system(page):
    """
    Open the configured target business system from the user center.

    The application name and target URL pattern are configured through
    environment variables so the public repository does not expose
    internal system information.
    """

    target_entry = (
        page.get_by_text(
            TARGET_SYSTEM_NAME,
            exact=True,
        )
    )

    expect(
        target_entry
    ).to_be_visible(
        timeout=20000
    )

    # ==================================================
    # 记录当前标签页数量
    # ==================================================

    old_page_count = len(
        page.context.pages
    )

    # ==================================================
    # 点击目标系统入口
    # ==================================================

    target_entry.click()

    page.wait_for_timeout(
        5000
    )

    # ==================================================
    # 判断是否打开新标签页
    # ==================================================

    if (
        len(page.context.pages)
        > old_page_count
    ):

        target_page = (
            page.context.pages[-1]
        )

    else:

        target_page = page

    # ==================================================
    # 切换至目标业务系统
    # ==================================================

    target_page.bring_to_front()

    target_page.wait_for_load_state(
        "domcontentloaded"
    )

    # ==================================================
    # 验证目标业务系统地址
    # ==================================================

    expect(
        target_page
    ).to_have_url(
        re.compile(
            TARGET_SYSTEM_URL_PATTERN
        ),
        timeout=20000,
    )

    print(
        "公共登录模块：已进入目标业务系统"
    )

    return target_page
