import os
import re
import time

import requests
from playwright.sync_api import sync_playwright

from config import BASE_URL, DWELLER_API, get_headers
from utils.auth import login_user_center


# ==================================================
# Public/demo configuration
# ==================================================
#
# The public repository must not hard-code real company:
# - domains
# - internal application paths
# - application names
# - API path fragments
# - business menu labels
#
# Configure real values locally through environment variables.
# Safe defaults below intentionally point to example/demo values.
# ==================================================

TARGET_APP_URL = os.getenv(
    "TEST_TARGET_APP_URL",
    "https://example.invalid/business-app",
)

TARGET_APP_URL_KEYWORD = os.getenv(
    "TEST_TARGET_APP_URL_KEYWORD",
    "business-app",
)

API_REQUEST_PATH_KEYWORD = os.getenv(
    "TEST_API_REQUEST_PATH_KEYWORD",
    "/api/",
)

TARGET_MENU_TEXT = os.getenv(
    "TEST_TARGET_MENU_TEXT",
    "居民管理",
)

TARGET_APP_KEYWORDS = [
    item.strip()
    for item in os.getenv(
        "TEST_TARGET_APP_KEYWORDS",
        "业务系统,测试系统",
    ).split(",")
    if item.strip()
]

PROBE_QUERY_SCENE = os.getenv(
    "TEST_API_QUERY_SCENE",
    "resident_list",
)

PROBE_GROUP_TYPE = os.getenv(
    "TEST_API_GROUP_TYPE",
    "1",
)

PROBE_RANK = os.getenv(
    "TEST_API_RANK",
    "0",
)


# ==================================================
# 只读接口探测
# ==================================================

def probe_api_auth(headers):
    """
    用只读列表接口探测当前 Authorization / X-AppCode 是否有效。

    公共版本中的业务参数均使用安全占位值，
    真实值应在本地环境变量中配置。
    """

    params = {
        "groupId": "",
        "name": "",
        "queryScene": PROBE_QUERY_SCENE,
        "groupType": int(PROBE_GROUP_TYPE),
        "rank": int(PROBE_RANK),
        "pageIndex": 1,
        "pageSize": 1,
    }

    return requests.get(
        BASE_URL + DWELLER_API,
        headers=headers,
        params=params,
        timeout=10,
    )


# ==================================================
# 判断是否已经捕获完整鉴权
# ==================================================

def has_credentials(captured):
    return bool(
        captured.get("token")
        and captured.get("app_code")
    )


# ==================================================
# 等待鉴权出现
# ==================================================

def wait_for_credentials(
    context,
    captured,
    timeout_seconds=12,
):
    deadline = (
        time.time()
        + timeout_seconds
    )

    while (
        time.time()
        < deadline
    ):

        if has_credentials(
            captured
        ):
            return True

        pages = [
            page
            for page in context.pages
            if not page.is_closed()
        ]

        if pages:
            try:
                pages[-1].wait_for_timeout(
                    500
                )
            except Exception:
                pass
        else:
            time.sleep(
                0.5
            )

    return has_credentials(
        captured
    )


# ==================================================
# 找目标业务系统页面
# ==================================================

def get_outbound_page(context):
    """
    从当前 Context 所有标签页中寻找目标业务系统页面。

    函数名保留 get_outbound_page，
    以兼容当前项目内部结构。
    """

    for page in reversed(
        context.pages
    ):

        try:

            if page.is_closed():
                continue

            if (
                TARGET_APP_URL_KEYWORD
                in page.url
            ):
                return page

        except Exception:
            pass

    return None


# ==================================================
# 从用户中心进入目标业务系统
# ==================================================

def open_outbound_from_user_center(
    page,
    context,
):
    """
    优先从用户中心正常点击进入目标业务系统。

    兼容：
    - href 入口
    - 普通 div / card
    - 文本入口
    - 新标签页
    """

    # 等待用户中心应用卡片加载
    page.wait_for_timeout(
        4000
    )

    # --------------------------------------------------
    # 方式1：href 中包含目标系统关键字
    # --------------------------------------------------

    selectors = [
        f"a[href*='{TARGET_APP_URL_KEYWORD}']",
        f"[href*='{TARGET_APP_URL_KEYWORD}']",
    ]

    for selector in selectors:

        try:

            candidates = page.locator(
                selector
            )

            for i in range(
                candidates.count()
            ):

                item = (
                    candidates.nth(i)
                )

                try:

                    if not item.is_visible():
                        continue

                    item.click()

                    page.wait_for_timeout(
                        3000
                    )

                    target_page = (
                        get_outbound_page(
                            context
                        )
                    )

                    if target_page:
                        return target_page

                except Exception:
                    pass

        except Exception:
            pass

    # --------------------------------------------------
    # 方式2：根据配置的应用名称关键字寻找
    # --------------------------------------------------

    for keyword in TARGET_APP_KEYWORDS:

        try:

            candidates = (
                page.get_by_text(
                    re.compile(
                        re.escape(
                            keyword
                        )
                    )
                )
            )

            for i in range(
                candidates.count()
            ):

                item = (
                    candidates.nth(i)
                )

                try:

                    if not item.is_visible():
                        continue

                    item.click()

                    page.wait_for_timeout(
                        3000
                    )

                    target_page = (
                        get_outbound_page(
                            context
                        )
                    )

                    if target_page:
                        return target_page

                except Exception:
                    pass

        except Exception:
            pass

    return None


# ==================================================
# 在目标页面触发只读列表请求
# ==================================================

def trigger_dweller_request(
    page,
    captured,
):
    """
    尝试进入配置的目标菜单，让页面发出 API 请求，
    再从真实请求头中抓取临时鉴权。

    公共版本不包含真实业务系统路径。
    """

    if page is None:
        return False

    try:

        page.bring_to_front()

        page.wait_for_load_state(
            "domcontentloaded"
        )

    except Exception:
        pass

    # 先等待首页自身可能已经发出的请求
    for _ in range(8):

        if has_credentials(
            captured
        ):
            return True

        try:
            page.wait_for_timeout(
                500
            )
        except Exception:
            pass

    # --------------------------------------------------
    # 尝试点击配置的目标菜单
    # --------------------------------------------------

    try:

        menu_candidates = (
            page.get_by_text(
                TARGET_MENU_TEXT,
                exact=True,
            )
        )

        for i in range(
            menu_candidates.count()
        ):

            item = (
                menu_candidates.nth(i)
            )

            try:

                if not item.is_visible():
                    continue

                item.click()

                print(
                    f"API鉴权刷新：已点击【{TARGET_MENU_TEXT}】"
                )

                break

            except Exception:
                pass

    except Exception:
        pass

    # --------------------------------------------------
    # 等待目标API请求出现
    # --------------------------------------------------

    for _ in range(20):

        if has_credentials(
            captured
        ):
            return True

        try:
            page.wait_for_timeout(
                500
            )
        except Exception:
            pass

    return has_credentials(
        captured
    )


# ==================================================
# 打印用户中心可疑入口
# 仅打印匹配配置关键字的文字，不打印敏感请求头
# ==================================================

def print_user_center_candidates(page):
    """
    当自动找不到目标应用时，
    输出用户中心中可能的应用入口文字，
    方便本地调试。
    """

    print()
    print(
        "========== 用户中心入口诊断 =========="
    )

    try:

        body_text = (
            page.locator(
                "body"
            )
            .inner_text()
        )

        lines = []

        for line in (
            body_text.splitlines()
        ):

            line = (
                line.strip()
            )

            if not line:
                continue

            if any(
                keyword in line
                for keyword
                in TARGET_APP_KEYWORDS
            ):

                if (
                    line
                    not in lines
                ):
                    lines.append(
                        line
                    )

        if lines:

            for line in lines[:30]:
                print(
                    line
                )

        else:

            print(
                "没有在用户中心正文中发现"
                "与 TEST_TARGET_APP_KEYWORDS 匹配的文字。"
            )

    except Exception as exc:

        print(
            "读取用户中心文字失败：",
            exc,
        )

    print(
        "======================================"
    )


# ==================================================
# 自动刷新鉴权
# ==================================================

def refresh_api_auth_via_ui():
    """
    自动登录用户中心 -> 进入目标业务系统 ->
    触发只读 API 请求 -> 捕获真实临时鉴权。

    只更新当前 pytest 进程里的环境变量。
    不写回 .env。
    """

    print()
    print(
        "======================================"
    )
    print(
        "当前API鉴权无效，开始自动刷新..."
    )
    print(
        "======================================"
    )

    captured = {}

    with sync_playwright() as playwright:

        # 调试阶段使用 headed，
        # 方便观察自动鉴权卡在哪一步。
        browser = (
            playwright.chromium.launch(
                headless=False
            )
        )

        context = (
            browser.new_context()
        )

        page = (
            context.new_page()
        )

        # --------------------------------------------------
        # 监听整个 Context 的请求
        # --------------------------------------------------

        def record_request(request):

            try:

                if (
                    API_REQUEST_PATH_KEYWORD
                    not in request.url
                ):
                    return

                try:

                    raw_headers = (
                        request.all_headers()
                    )

                except Exception:

                    raw_headers = (
                        request.headers
                    )

                headers = {
                    str(key).lower():
                    value
                    for key, value
                    in raw_headers.items()
                }

                token = (
                    headers.get(
                        "authorization"
                    )
                )

                app_code = (
                    headers.get(
                        "x-appcode"
                    )
                    or
                    headers.get(
                        "x-app-code"
                    )
                )

                if (
                    token
                    and
                    app_code
                ):

                    first_capture = not has_credentials(
                        captured
                    )

                    captured[
                        "token"
                    ] = token

                    captured[
                        "app_code"
                    ] = app_code

                    if first_capture:
                        print(
                            "API鉴权刷新："
                            "已捕获 Authorization + X-AppCode"
                        )

            except Exception:
                pass

        context.on(
            "request",
            record_request,
        )

        # --------------------------------------------------
        # 第1步：自动登录用户中心
        # --------------------------------------------------

        login_user_center(
            page
        )

        print(
            "API鉴权刷新：用户中心登录成功"
        )

        page.wait_for_timeout(
            3000
        )

        # --------------------------------------------------
        # 第2步：从用户中心进入目标业务系统
        # --------------------------------------------------

        target_page = (
            open_outbound_from_user_center(
                page,
                context,
            )
        )

        # --------------------------------------------------
        # 第3步：如果正常入口没找到，
        # 先打印诊断，再尝试直达配置URL
        # --------------------------------------------------

        if target_page is None:

            print(
                "API鉴权刷新："
                "未从用户中心自动找到目标业务系统入口"
            )

            print_user_center_candidates(
                page
            )

            try:

                # 新开标签页，不覆盖用户中心页面。
                target_page = (
                    context.new_page()
                )

                target_page.goto(
                    TARGET_APP_URL,
                    wait_until="domcontentloaded",
                )

                target_page.wait_for_timeout(
                    4000
                )

                # 如果直达地址被SSO或网关重定向，
                # 这里视为没有进入目标系统。
                if (
                    TARGET_APP_URL_KEYWORD
                    not in target_page.url
                ):

                    print(
                        "API鉴权刷新："
                        "直接访问目标系统被重定向，"
                        f"当前地址：{target_page.url}"
                    )

                    target_page = None

            except Exception as exc:

                print(
                    "API鉴权刷新："
                    f"直接访问目标系统失败：{exc}"
                )

                target_page = None

        # --------------------------------------------------
        # 第4步：有目标页面时触发只读请求
        # --------------------------------------------------

        if target_page is not None:

            print(
                "API鉴权刷新：已进入目标业务系统"
            )

            trigger_dweller_request(
                target_page,
                captured,
            )

        # --------------------------------------------------
        # 第5步：最终等待
        # --------------------------------------------------

        if not has_credentials(
            captured
        ):

            wait_for_credentials(
                context,
                captured,
                timeout_seconds=8,
            )

        current_urls = [
            current_page.url
            for current_page
            in context.pages
            if not current_page.is_closed()
        ]

        # 成功后关闭调试浏览器
        if has_credentials(
            captured
        ):
            browser.close()

        else:
            # 失败时保留10秒，方便观察当前页面。
            print()
            print(
                "自动鉴权暂未成功。"
            )
            print(
                "浏览器将保留10秒用于查看当前页面..."
            )

            try:
                page.wait_for_timeout(
                    10000
                )
            except Exception:
                pass

            browser.close()

    assert (
        captured.get("token")
        and captured.get("app_code")
    ), (
        "自动登录成功，但仍没有从目标业务系统请求中捕获到 "
        "Authorization / X-AppCode。\n"
        f"本次打开页面：{current_urls}\n"
        "请检查本地环境变量中的目标系统 URL、"
        "URL 关键字、API 请求关键字和菜单文本配置。"
    )

    os.environ[
        "TEST_AUTH_TOKEN"
    ] = captured["token"]

    os.environ[
        "TEST_APP_CODE"
    ] = captured["app_code"]

    print(
        "API鉴权刷新成功"
    )

    return get_headers()


# ==================================================
# 获取可用API鉴权
# ==================================================

def ensure_api_headers():
    """
    当前鉴权有效 -> 直接使用
    当前鉴权401/缺失 -> 自动登录刷新
    """

    current_headers = None

    try:

        current_headers = (
            get_headers()
        )

    except AssertionError:
        pass

    if current_headers:

        try:

            response = (
                probe_api_auth(
                    current_headers
                )
            )

            if (
                response.status_code
                == 200
            ):

                print(
                    "API鉴权检查：当前鉴权有效"
                )

                return current_headers

            if (
                response.status_code
                == 401
            ):

                print(
                    "API鉴权检查：当前Token已过期"
                )

            else:

                print(
                    "API鉴权检查："
                    "当前鉴权返回状态码",
                    response.status_code,
                )

        except requests.RequestException as exc:

            print(
                "API鉴权探测请求异常：",
                exc,
            )

    else:

        print(
            "API鉴权检查：当前未配置有效鉴权"
        )

    # 自动刷新
    new_headers = (
        refresh_api_auth_via_ui()
    )

    # 刷新后再验证一次
    response = (
        probe_api_auth(
            new_headers
        )
    )

    assert (
        response.status_code
        == 200
    ), (
        "自动刷新API鉴权后验证仍失败，"
        f"状态码：{response.status_code}，"
        f"响应内容：{response.text}"
    )

    print(
        "API鉴权检查：刷新后验证通过"
    )

    return new_headers
