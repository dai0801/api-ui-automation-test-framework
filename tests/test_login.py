from pathlib import Path

import pytest
from playwright.sync_api import expect

from utils.auth import LOGIN_SUCCESS_TEXT


# ==================================================
# 项目根目录
# ==================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

AUTH_STATE_FILE = (
    PROJECT_ROOT
    / "auth_state.json"
)


# ==================================================
# 登录自动化测试
# ==================================================

@pytest.mark.ui
@pytest.mark.regression
def test_auto_login(
    user_center_page
):
    """
    验证公共登录 Fixture 的登录结果，
    并将浏览器登录状态保存到本地 auth_state.json。

    auth_state.json 已通过 .gitignore 排除，
    不应提交到公开仓库。
    """

    print()
    print(
        "======================================"
    )

    print(
        "开始验证登录结果"
    )

    print(
        "======================================"
    )

    # ==================================================
    # Fixture 已负责完成登录
    # 测试这里只验证登录后的关键页面文案
    # ==================================================

    expect(
        user_center_page.get_by_text(
            LOGIN_SUCCESS_TEXT,
            exact=True,
        ).first
    ).to_be_visible(
        timeout=10000
    )

    print(
        "登录结果校验成功"
    )

    # ==================================================
    # 保存浏览器登录状态
    #
    # 仅用于本地测试调试。
    # 公开仓库不得提交 auth_state.json。
    # ==================================================

    user_center_page.context.storage_state(
        path=str(
            AUTH_STATE_FILE
        )
    )

    print(
        "登录状态已保存到本地："
        f"{AUTH_STATE_FILE.name}"
    )
