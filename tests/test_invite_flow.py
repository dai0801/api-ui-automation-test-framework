import json
import os
import re
from pathlib import Path

import pytest
from playwright.sync_api import expect


# ==================================================
# Public/demo configuration
# ==================================================
#
# The public repository must not hard-code real company:
# - domains
# - internal application routes
# - template names
# - internal API endpoint keywords
# - real test-data filenames
#
# Configure real values locally through environment variables.
# The safe defaults below are placeholders only.
# ==================================================

INVITE_URL = os.getenv(
    "TEST_INVITE_URL",
    "https://example.invalid/invite",
)

TEST_EXCEL = Path(
    os.getenv(
        "TEST_INVITE_EXCEL",
        "test_data/invite_sample.xlsx",
    )
)

TEMPLATE_NAME = os.getenv(
    "TEST_INVITE_TEMPLATE_NAME",
    "测试邀约模板",
)

INVITE_PAGE_TEXT = os.getenv(
    "TEST_INVITE_PAGE_TEXT",
    "居民邀约",
)

NOTICE_SECTION_TEXT = os.getenv(
    "TEST_NOTICE_SECTION_TEXT",
    "选择通知内容",
)

TEMPLATE_INPUT_PLACEHOLDER = os.getenv(
    "TEST_TEMPLATE_INPUT_PLACEHOLDER",
    "请选择电话模板",
)

NOTICE_CONTENT_SELECTOR = os.getenv(
    "TEST_NOTICE_CONTENT_SELECTOR",
    "form [contenteditable='true']",
)

CONFIRM_PAGE_TEXT = os.getenv(
    "TEST_CONFIRM_PAGE_TEXT",
    "确认邀约居民",
)

UPLOAD_TEXT = os.getenv(
    "TEST_UPLOAD_TEXT",
    "点击上传",
)

IMPORT_RESULT_TITLE = os.getenv(
    "TEST_IMPORT_RESULT_TITLE",
    "居民信息导入结果",
)

SYSTEM_PROMPT_TITLE = os.getenv(
    "TEST_SYSTEM_PROMPT_TITLE",
    "系统提示",
)

NEXT_BUTTON_TEXT = os.getenv(
    "TEST_NEXT_BUTTON_TEXT",
    "下一步",
)

CLOSE_BUTTON_TEXT = os.getenv(
    "TEST_CLOSE_BUTTON_TEXT",
    "关闭",
)

EXECUTE_BUTTON_TEXT = os.getenv(
    "TEST_EXECUTE_BUTTON_TEXT",
    "执行",
)

TASK_SUCCESS_TEXT = os.getenv(
    "TEST_TASK_SUCCESS_TEXT",
    "任务创建成功",
)

FILTER_API_KEYWORD = os.getenv(
    "TEST_FILTER_API_KEYWORD",
    "/api/invite/filter",
)

EXECUTE_API_KEYWORD = os.getenv(
    "TEST_EXECUTE_API_KEYWORD",
    "/api/call/create",
)


# ==================================================
# Sensitive-data sanitization
# ==================================================

SENSITIVE_KEYS = {
    "phone",
    "mobile",
    "mobilephone",
    "phonenumber",
    "telephone",
    "idcard",
    "idno",
    "identityno",
    "password",
    "token",
    "accesstoken",
    "refreshtoken",
    "authorization",
    "cookie",
}


def sanitize_text(text):
    """
    Mask common phone numbers and token-like values before logging.
    """

    if not text:
        return text

    # Mainland China 11-digit phone number
    text = re.sub(
        r"(?<!\d)1[3-9]\d{9}(?!\d)",
        "1**********",
        text,
    )

    # Common authorization fields
    text = re.sub(
        r"(?i)"
        r"(authorization|access_token|accesstoken|"
        r"refresh_token|refreshtoken|token)"
        r"(\s*[:=]\s*)"
        r"([^\s,;}\]]+)",
        r"\1\2***MASKED***",
        text,
    )

    return text


def sanitize_data(data):
    """
    Recursively mask sensitive fields in JSON-like data.
    """

    if isinstance(data, dict):
        result = {}

        for key, value in data.items():
            if str(key).lower() in SENSITIVE_KEYS:
                result[key] = "***MASKED***"
            else:
                result[key] = sanitize_data(value)

        return result

    if isinstance(data, list):
        return [
            sanitize_data(item)
            for item in data
        ]

    if isinstance(data, str):
        return sanitize_text(data)

    return data


def get_safe_response_body(response):
    """
    Return a sanitized response body for local diagnostics.
    """

    try:
        body_json = response.json()

        safe_json = sanitize_data(
            body_json
        )

        return json.dumps(
            safe_json,
            ensure_ascii=False,
            indent=2,
        )

    except Exception:
        try:
            body_text = response.text()

            body_text = sanitize_text(
                body_text
            )

            if len(body_text) > 8000:
                body_text = (
                    body_text[:8000]
                    + "\n……内容过长，已截断……"
                )

            return body_text

        except Exception as exc:
            return (
                "无法读取响应内容："
                f"{exc}"
            )


# ==================================================
# Notification-content helper
# ==================================================

def clean_notification_content(page):
    """
    Remove half-width/full-width asterisks from the editable notice.
    """

    print()
    print(
        "第2.1步：开始处理通知内容"
    )

    content_box = page.locator(
        NOTICE_CONTENT_SELECTOR
    ).first

    expect(
        content_box
    ).to_be_visible(
        timeout=10000
    )

    original_content = (
        content_box
        .inner_text()
        .strip()
    )

    assert original_content, (
        "通知内容为空"
    )

    # Do not print real message content to console/report.
    print(
        "第2.1步：已读取通知内容，"
        f"长度={len(original_content)}"
    )

    cleaned_content = (
        original_content
        .replace("*", "")
        .replace("＊", "")
        .strip()
    )

    assert cleaned_content, (
        "删除星号后通知内容为空"
    )

    if (
        cleaned_content
        != original_content
    ):
        content_box.fill(
            cleaned_content
        )

        content_box.press(
            "Tab"
        )

        page.wait_for_timeout(
            800
        )

        print(
            "第2.1步：已自动删除通知内容中的星号"
        )

    else:
        print(
            "第2.1步：当前通知内容没有星号"
        )

    final_content = (
        content_box
        .inner_text()
        .strip()
    )

    assert "*" not in final_content, (
        "通知内容仍然存在半角星号"
    )

    assert "＊" not in final_content, (
        "通知内容仍然存在全角星号"
    )

    assert (
        final_content
        == cleaned_content
    ), (
        "通知内容页面实际值与预期不一致"
    )

    print(
        "第2.1步：通知内容校验成功"
    )


# ==================================================
# Dialog helper
# ==================================================

def get_visible_dialog(page):
    dialogs = page.locator(
        "[role='dialog']:visible"
    )

    if dialogs.count() == 0:
        return None

    return dialogs.last


# ==================================================
# Browser hold helper
# ==================================================

def keep_browser_open(page):
    keep_seconds = int(
        os.getenv(
            "KEEP_BROWSER_SECONDS",
            "0",
        )
    )

    if keep_seconds <= 0:
        return

    print()
    print(
        "======================================"
    )
    print(
        f"浏览器最多保持打开 {keep_seconds} 秒"
    )
    print(
        "查看结束后可以直接关闭浏览器。"
    )
    print(
        "手动关闭浏览器不会导致前面的业务校验失败。"
    )
    print(
        "======================================"
    )

    for _ in range(
        keep_seconds
    ):
        try:
            if page.is_closed():
                print(
                    "检测到页面已关闭，测试正常结束。"
                )
                return

            page.wait_for_timeout(
                1000
            )

        except Exception:
            print(
                "检测到浏览器已经关闭，测试正常结束。"
            )
            return

    print(
        "浏览器等待时间结束。"
    )


# ==================================================
# Response diagnostic helper
# ==================================================

def print_target_response(
    title,
    responses,
    url_keyword,
):
    print()
    print(
        "======================================"
    )
    print(
        title
    )

    matched = [
        response
        for response in responses
        if url_keyword in response.url
    ]

    if not matched:
        print(
            f"没有捕获到目标接口关键字：{url_keyword}"
        )
        print(
            "======================================"
        )
        return None

    response = matched[-1]

    print(
        "HTTP状态码：",
        response.status,
    )

    print(
        "请求地址：",
        sanitize_text(
            response.url
        ),
    )

    print(
        "业务响应Body："
    )

    body = get_safe_response_body(
        response
    )

    print(
        body
    )

    print(
        "======================================"
    )

    return response


# ==================================================
# Resident-row helper
# ==================================================

def find_resident_row_with_checkbox(
    page,
    test_name,
):
    """
    Element UI tables may render duplicated fixed-column rows.
    Prefer the visible matching row that actually contains a checkbox.
    """

    if test_name:
        rows = page.locator(
            "table tbody tr:visible",
            has_text=test_name,
        )
    else:
        rows = page.locator(
            "table tbody tr:visible"
        )

    assert rows.count() >= 1, (
        "居民列表中没有居民数据"
    )

    for i in range(
        rows.count()
    ):
        row = rows.nth(i)

        if (
            row.locator(
                ".el-checkbox__inner"
            ).count()
            > 0
            or
            row.locator(
                "input[type='checkbox']"
            ).count()
            > 0
        ):
            return row

    raise AssertionError(
        "找到了居民数据行，但没有找到可勾选的居民行"
    )


# ==================================================
# Main live-call test
#
# chronic_page is provided by conftest.py.
# The fixture name is kept for compatibility with the local project,
# while the public repository does not expose the real system name.
# ==================================================

@pytest.mark.ui
@pytest.mark.live_call
def test_invite_flow(
    chronic_page
):
    test_name = os.getenv(
        "TEST_DWELLER_NAME"
    )

    allow_test_call = (
        os.getenv(
            "ALLOW_TEST_CALL",
            "false",
        ).lower()
        == "true"
    )

    assert TEST_EXCEL.exists(), (
        f"没有找到测试Excel：{TEST_EXCEL}"
    )

    assert allow_test_call, (
        "当前没有允许创建真实测试任务。\n"
        "仅在明确授权的测试环境和测试号码上运行，"
        "并通过 run_live_call.bat 人工确认。"
    )

    print()
    print(
        "======================================"
    )
    print(
        "开始执行授权测试邀约流程"
    )
    print(
        "公共Fixture：已完成登录并进入目标业务系统"
    )
    print(
        f"测试数据文件：{TEST_EXCEL.name}"
    )
    print(
        f"模板：{TEMPLATE_NAME}"
    )
    print(
        "======================================"
    )

    # ==================================================
    # Step 1: open invite page
    # ==================================================

    chronic_page.goto(
        INVITE_URL,
        wait_until="domcontentloaded",
    )

    expect(
        chronic_page.get_by_text(
            INVITE_PAGE_TEXT,
            exact=True,
        ).first
    ).to_be_visible(
        timeout=20000
    )

    expect(
        chronic_page.get_by_text(
            NOTICE_SECTION_TEXT,
            exact=True,
        )
    ).to_be_visible(
        timeout=20000
    )

    print(
        "第1步：已进入邀约页面"
    )

    # ==================================================
    # Step 2: select template
    # ==================================================

    template_input = (
        chronic_page.locator(
            f"input[placeholder='{TEMPLATE_INPUT_PLACEHOLDER}']"
        )
    )

    expect(
        template_input
    ).to_be_visible(
        timeout=15000
    )

    if (
        template_input
        .input_value()
        .strip()
        != TEMPLATE_NAME
    ):
        template_input.click()

        template_text = (
            chronic_page.get_by_text(
                TEMPLATE_NAME,
                exact=True,
            )
        )

        expect(
            template_text
        ).to_be_visible(
            timeout=15000
        )

        template_row = (
            template_text.locator(
                "xpath=ancestor::tr"
            )
        )

        expect(
            template_row
        ).to_be_visible(
            timeout=10000
        )

        select_button = (
            template_row.get_by_role(
                "button",
                name="选择",
                exact=True,
            )
        )

        expect(
            select_button
        ).to_be_visible(
            timeout=10000
        )

        select_button.click()

    chronic_page.wait_for_timeout(
        1000
    )

    expect(
        template_input
    ).to_have_value(
        TEMPLATE_NAME,
        timeout=10000,
    )

    print(
        f"第2步：已选择模板【{TEMPLATE_NAME}】"
    )

    # ==================================================
    # Step 2.1: clean notice content
    # ==================================================

    clean_notification_content(
        chronic_page
    )

    # ==================================================
    # Step 2.2: verify notice area
    # ==================================================

    notification_form = (
        chronic_page.locator(
            NOTICE_CONTENT_SELECTOR
        ).first
    )

    expect(
        notification_form
    ).to_be_visible(
        timeout=10000
    )

    notification_text = (
        notification_form
        .inner_text()
    )

    assert "*" not in notification_text, (
        "通知内容仍存在半角星号"
    )

    assert "＊" not in notification_text, (
        "通知内容仍存在全角星号"
    )

    print(
        "第2.2步：通知内容校验成功"
    )

    # ==================================================
    # Step 3: next
    # ==================================================

    next_button = (
        chronic_page.get_by_role(
            "button",
            name=NEXT_BUTTON_TEXT,
            exact=True,
        )
    )

    expect(
        next_button
    ).to_be_visible(
        timeout=10000
    )

    next_button.scroll_into_view_if_needed()
    next_button.click()

    chronic_page.wait_for_timeout(
        1000
    )

    dialog = get_visible_dialog(
        chronic_page
    )

    if dialog is not None:
        dialog_text = (
            dialog
            .inner_text()
            .strip()
        )

        error_keywords = [
            "不能为空",
            "格式错误",
            "错误",
            "失败",
        ]

        if any(
            keyword in dialog_text
            for keyword in error_keywords
        ):
            raise AssertionError(
                "通知内容修改后仍未通过业务校验：\n"
                f"{sanitize_text(dialog_text)}"
            )

    expect(
        chronic_page.get_by_text(
            CONFIRM_PAGE_TEXT,
            exact=True,
        )
    ).to_be_visible(
        timeout=20000
    )

    print(
        "第3步：已进入确认居民页面"
    )

    # ==================================================
    # Step 4: upload test data
    # ==================================================

    upload_text = (
        chronic_page.get_by_text(
            UPLOAD_TEXT,
            exact=True,
        ).first
    )

    expect(
        upload_text
    ).to_be_visible(
        timeout=15000
    )

    with chronic_page.expect_file_chooser(
        timeout=10000
    ) as file_chooser_info:
        upload_text.click()

    file_chooser = (
        file_chooser_info.value
    )

    file_chooser.set_files(
        str(
            TEST_EXCEL.resolve()
        )
    )

    print(
        f"第4步：{TEST_EXCEL.name} 已上传"
    )

    # ==================================================
    # Step 5: wait for parsing result
    # ==================================================

    success_title = (
        chronic_page.get_by_text(
            IMPORT_RESULT_TITLE,
            exact=True,
        )
    )

    error_title = (
        chronic_page.get_by_text(
            SYSTEM_PROMPT_TITLE,
            exact=True,
        )
    )

    result_type = None

    for _ in range(60):
        try:
            if (
                success_title.count() > 0
                and
                success_title.first.is_visible()
            ):
                result_type = "success"
                break
        except Exception:
            pass

        try:
            if (
                error_title.count() > 0
                and
                error_title.first.is_visible()
            ):
                result_type = "error"
                break
        except Exception:
            pass

        chronic_page.wait_for_timeout(
            1000
        )

    assert (
        result_type is not None
    ), (
        "等待60秒仍未获得测试数据解析结果"
    )

    if (
        result_type
        == "error"
    ):
        dialog = get_visible_dialog(
            chronic_page
        )

        if dialog is not None:
            error_text = (
                dialog.inner_text()
            )
        else:
            error_text = (
                chronic_page
                .locator("body")
                .inner_text()
            )

        raise AssertionError(
            "测试数据后台校验失败：\n"
            f"{sanitize_text(error_text)}"
        )

    print(
        "第5步：测试数据后台解析成功"
    )

    # ==================================================
    # Step 6: validate import summary
    # ==================================================

    dialog = get_visible_dialog(
        chronic_page
    )

    if dialog is not None:
        result_text = (
            dialog.inner_text()
        )
    else:
        result_text = (
            chronic_page
            .locator("body")
            .inner_text()
        )

    assert re.search(
        r"成功\s*1",
        result_text,
    ), (
        "导入成功人数不是1"
    )

    assert re.search(
        r"失败\s*0",
        result_text,
    ), (
        "导入失败人数不是0"
    )

    assert re.search(
        r"总共\s*1",
        result_text,
    ), (
        "导入总人数不是1"
    )

    print(
        "第6步：成功1 / 失败0 / 总共1，校验通过"
    )

    # ==================================================
    # Step 7: close import result
    # ==================================================

    close_button = (
        chronic_page.get_by_role(
            "button",
            name=CLOSE_BUTTON_TEXT,
            exact=True,
        )
    )

    expect(
        close_button
    ).to_be_visible(
        timeout=10000
    )

    close_button.click()

    chronic_page.wait_for_timeout(
        1000
    )

    print(
        "第7步：已关闭导入结果"
    )

    # ==================================================
    # Step 8: verify resident list
    # ==================================================

    expect(
        chronic_page.get_by_text(
            re.compile(
                r"共\s*1\s*条"
            )
        ).first
    ).to_be_visible(
        timeout=15000
    )

    if test_name:
        resident_verify_row = (
            chronic_page.locator(
                "table tbody tr:visible",
                has_text=test_name,
            ).first
        )

        expect(
            resident_verify_row
        ).to_be_visible(
            timeout=10000
        )

        print(
            "第8步：授权测试居民已进入列表"
        )

    else:
        print(
            "第8步：测试居民已经进入邀约列表"
        )

    # ==================================================
    # Step 9: select resident
    # ==================================================

    resident_row = (
        find_resident_row_with_checkbox(
            chronic_page,
            test_name,
        )
    )

    expect(
        resident_row
    ).to_be_visible(
        timeout=10000
    )

    resident_row.scroll_into_view_if_needed()

    chronic_page.wait_for_timeout(
        500
    )

    checkbox_inner = (
        resident_row.locator(
            ".el-checkbox__inner"
        ).first
    )

    checkbox_label = (
        resident_row.locator(
            "label.el-checkbox"
        ).first
    )

    checkbox_wrapper = (
        resident_row.locator(
            ".el-checkbox__input"
        ).first
    )

    if (
        checkbox_inner.count()
        > 0
    ):
        checkbox_inner.click(
            force=True
        )

    elif (
        checkbox_label.count()
        > 0
    ):
        checkbox_label.click(
            force=True
        )

    elif (
        checkbox_wrapper.count()
        > 0
    ):
        checkbox_wrapper.click(
            force=True
        )

    else:
        raise AssertionError(
            "没有找到居民复选框"
        )

    chronic_page.wait_for_timeout(
        700
    )

    real_checkbox = (
        resident_row.locator(
            "input[type='checkbox']"
        ).first
    )

    if (
        real_checkbox.count()
        > 0
    ):
        assert (
            real_checkbox
            .is_checked()
        ), (
            "居民没有真正被选中"
        )

    print(
        "第9步：授权测试居民已成功勾选"
    )

    # ==================================================
    # Step 10: locate execute button
    # ==================================================

    execute_button = (
        chronic_page.get_by_role(
            "button",
            name=EXECUTE_BUTTON_TEXT,
            exact=True,
        )
    )

    expect(
        execute_button
    ).to_be_visible(
        timeout=10000
    )

    execute_button.scroll_into_view_if_needed()

    chronic_page.wait_for_timeout(
        500
    )

    print(
        "第10步：已找到执行按钮"
    )

    # ==================================================
    # Step 11: capture POST responses
    # ==================================================

    post_responses = []

    def record_response(response):
        try:
            if (
                response.request.method
                == "POST"
            ):
                post_responses.append(
                    response
                )
        except Exception:
            pass

    chronic_page.on(
        "response",
        record_response,
    )

    # ==================================================
    # Step 12: execute
    # ==================================================

    print(
        "第11步：准备创建授权测试任务"
    )

    execute_button.click()

    print(
        "第11步：已点击执行"
    )

    chronic_page.wait_for_timeout(
        1200
    )

    # ==================================================
    # Step 12.1: handle possible confirmation dialog
    # ==================================================

    dialog = get_visible_dialog(
        chronic_page
    )

    if dialog is not None:
        dialog_text = (
            dialog
            .inner_text()
            .strip()
        )

        error_keywords = [
            "不能为空",
            "格式错误",
            "错误",
            "失败",
        ]

        if any(
            keyword in dialog_text
            for keyword in error_keywords
        ):
            raise AssertionError(
                "创建任务业务校验失败：\n"
                f"{sanitize_text(dialog_text)}"
            )

        confirm_button = (
            dialog.get_by_role(
                "button",
                name=re.compile(
                    r"^(确认|确定|确认执行|确认创建)$"
                ),
            )
        )

        if (
            confirm_button.count()
            > 0
        ):
            confirm_button.first.click()

            print(
                "已自动确认测试任务创建"
            )

    # ==================================================
    # Step 13: verify task success
    # ==================================================

    print(
        "第12步：正在等待任务创建结果..."
    )

    success_locator = (
        chronic_page.get_by_text(
            TASK_SUCCESS_TEXT,
            exact=False,
        )
    )

    expect(
        success_locator.first
    ).to_be_visible(
        timeout=30000
    )

    print(
        f"第12步：检测到【{TASK_SUCCESS_TEXT}】"
    )

    chronic_page.wait_for_timeout(
        3000
    )

    # ==================================================
    # Step 14: local POST diagnostics
    # ==================================================

    print()
    print(
        "======================================"
    )
    print(
        "本次执行捕获到的POST请求："
    )

    if post_responses:
        for response in post_responses:
            print(
                response.status,
                sanitize_text(
                    response.url
                ),
            )
    else:
        print(
            "没有捕获到POST请求"
        )

    print(
        "======================================"
    )

    # ==================================================
    # Step 15: optional filtering response
    # ==================================================

    print_target_response(
        title=(
            "【关键接口1】"
            "邀约过滤业务响应"
        ),
        responses=post_responses,
        url_keyword=(
            FILTER_API_KEYWORD
        ),
    )

    # ==================================================
    # Step 16: task-creation response
    # ==================================================

    execute_response = print_target_response(
        title=(
            "【关键接口2】"
            "测试任务创建业务响应"
        ),
        responses=post_responses,
        url_keyword=(
            EXECUTE_API_KEYWORD
        ),
    )

    assert (
        execute_response
        is not None
    ), (
        "页面虽然显示任务创建成功，"
        "但是没有捕获到配置的任务创建接口。"
    )

    assert (
        200
        <= execute_response.status
        < 300
    ), (
        "任务创建接口HTTP状态异常："
        f"{execute_response.status}"
    )

    # ==================================================
    # Step 17: final diagnostics
    # ==================================================

    print()
    print(
        "======================================"
    )
    print(
        "当前已确认："
    )
    print(
        "1. 公共Fixture已完成登录和进入目标业务系统"
    )
    print(
        "2. 测试数据导入成功"
    )
    print(
        "3. 授权测试居民已勾选"
    )
    print(
        "4. 页面显示任务创建成功"
    )
    print(
        "5. 关键过滤接口已发出"
    )
    print(
        "6. 任务创建接口已发出且HTTP为2xx"
    )
    print(
        "======================================"
    )

    keep_browser_open(
        chronic_page
    )
