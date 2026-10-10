import os
import re

import pytest
from playwright.sync_api import expect


# ==================================================
# Public/demo configuration
# ==================================================
#
# Real company page names, route patterns, task names and
# business-specific labels are configured through environment
# variables instead of being hard-coded in the public repository.
# ==================================================

TASK_NAME = os.getenv(
    "TEST_STATISTICS_TASK_NAME",
    "测试任务",
)

STATISTICS_MENU_TEXT = os.getenv(
    "TEST_STATISTICS_MENU_TEXT",
    "统计分析",
)

PHONE_STATISTICS_TEXT = os.getenv(
    "TEST_PHONE_STATISTICS_TEXT",
    "任务统计",
)

STATISTICS_URL_PATTERN = os.getenv(
    "TEST_STATISTICS_URL_PATTERN",
    r".*/statistics/.*",
)

TASK_TIME_TEXT = os.getenv(
    "TEST_TASK_TIME_TEXT",
    "任务时间",
)

DETAIL_BUTTON_TEXT = os.getenv(
    "TEST_DETAIL_BUTTON_TEXT",
    "详情",
)

DETAIL_TITLE_KEYWORDS = [
    item.strip()
    for item in os.getenv(
        "TEST_DETAIL_TITLE_KEYWORDS",
        "任务汇总详细|任务汇总详情",
    ).split("|")
    if item.strip()
]

NAME_PLACEHOLDER = os.getenv(
    "TEST_NAME_PLACEHOLDER",
    "请输入姓名",
)

PHONE_PLACEHOLDER = os.getenv(
    "TEST_PHONE_PLACEHOLDER",
    "请输入电话",
)

SEARCH_BUTTON_TEXT = os.getenv(
    "TEST_SEARCH_BUTTON_TEXT",
    "搜索",
)

EMPTY_DATA_TEXT = os.getenv(
    "TEST_EMPTY_DATA_TEXT",
    "暂无数据",
)

CORE_METRICS = [
    item.strip()
    for item in os.getenv(
        "TEST_CORE_METRICS",
        "呼叫人数|接通人数|接通率",
    ).split("|")
    if item.strip()
]

CHART_TITLES = [
    item.strip()
    for item in os.getenv(
        "TEST_CHART_TITLES",
        "接通结果分类|未接通结果分类",
    ).split("|")
    if item.strip()
]

BASIC_FIELDS = [
    item.strip()
    for item in os.getenv(
        "TEST_DETAIL_BASIC_FIELDS",
        "姓名：|电话：|通话时长：|接通结果分类|搜索",
    ).split("|")
    if item.strip()
]

REQUIRED_COLUMNS = [
    item.strip()
    for item in os.getenv(
        "TEST_DETAIL_REQUIRED_COLUMNS",
        "姓名|手机号码|通话时长|呼叫时间|拨打次数|呼叫状态|接通结果分类|短信提醒",
    ).split("|")
    if item.strip()
]


# ==================================================
# 通用定位辅助函数
# ==================================================

def get_first_visible(locator):
    try:
        count = locator.count()
    except Exception:
        return None

    for i in range(count):
        item = locator.nth(i)

        try:
            if item.is_visible():
                return item
        except Exception:
            pass

    return None


def find_visible_text_any_frame(
    page,
    text,
):
    for frame in page.frames:
        try:
            locator = frame.get_by_text(
                text,
                exact=True,
            )

            result = get_first_visible(
                locator
            )

            if result is not None:
                return result

        except Exception:
            pass

    return None


def get_leftmost_visible(locator):
    """
    Same task text can appear more than once.
    Prefer the left-most visible element in the task list.
    """

    result = None
    min_x = None

    try:
        count = locator.count()
    except Exception:
        return None

    for i in range(count):
        item = locator.nth(i)

        try:
            if not item.is_visible():
                continue

            box = item.bounding_box()

            if box is None:
                continue

            x = box["x"]

            if (
                min_x is None
                or x < min_x
            ):
                min_x = x
                result = item

        except Exception:
            pass

    return result


def get_topmost_visible(locator):
    """
    When multiple detail buttons exist, choose the top-most visible one.
    """

    result = None
    min_y = None

    try:
        count = locator.count()
    except Exception:
        return None

    for i in range(count):
        item = locator.nth(i)

        try:
            if not item.is_visible():
                continue

            box = item.bounding_box()

            if box is None:
                continue

            y = box["y"]

            if (
                min_y is None
                or y < min_y
            ):
                min_y = y
                result = item

        except Exception:
            pass

    return result


# ==================================================
# 手机号脱敏
# ==================================================

def mask_phone(text):
    return re.sub(
        r"(1[3-9]\d{2})\d{4}(\d{4})",
        r"\1****\2",
        text,
    )


# ==================================================
# 保持浏览器打开
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
        "查看完以后可以直接关闭浏览器。"
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
                    "浏览器已关闭，测试正常结束。"
                )
                return

            page.wait_for_timeout(
                1000
            )

        except Exception:
            print(
                "浏览器已关闭，测试正常结束。"
            )
            return


# ==================================================
# 统计菜单
# ==================================================

def find_statistics_menu(page):
    """
    Prefer the Element UI top-navigation structure,
    then fall back to exact text lookup in all frames.
    """

    candidates = page.locator(
        ".el-menu--horizontal "
        ".el-submenu__title"
    )

    for i in range(
        candidates.count()
    ):
        item = candidates.nth(i)

        try:
            if not item.is_visible():
                continue

            text = (
                item.inner_text()
                .strip()
            )

            if (
                STATISTICS_MENU_TEXT
                in text
            ):
                return item

        except Exception:
            pass

    return find_visible_text_any_frame(
        page,
        STATISTICS_MENU_TEXT,
    )


def wait_for_navigation(page):
    print(
        "第1步：正在等待目标系统顶部导航加载..."
    )

    for second in range(30):
        statistics_menu = (
            find_statistics_menu(
                page
            )
        )

        if statistics_menu is not None:
            print(
                "第1步：顶部导航已加载，"
                f"等待约 {second + 1} 秒"
            )
            return statistics_menu

        page.wait_for_timeout(
            1000
        )

    print(
        "第一次未发现顶部导航，自动刷新一次..."
    )

    page.reload(
        wait_until="domcontentloaded"
    )

    page.wait_for_timeout(
        5000
    )

    for _ in range(30):
        statistics_menu = (
            find_statistics_menu(
                page
            )
        )

        if statistics_menu is not None:
            print(
                "刷新后顶部导航加载成功"
            )
            return statistics_menu

        page.wait_for_timeout(
            1000
        )

    raise AssertionError(
        f"没有找到顶部【{STATISTICS_MENU_TEXT}】菜单"
    )


def enter_phone_statistics(page):
    statistics_menu = (
        wait_for_navigation(
            page
        )
    )

    expect(
        statistics_menu
    ).to_be_visible(
        timeout=10000
    )

    print(
        f"第1步：已找到顶部【{STATISTICS_MENU_TEXT}】"
    )

    statistics_menu.hover()

    page.wait_for_timeout(
        1000
    )

    print(
        f"第2步：已展开【{STATISTICS_MENU_TEXT}】菜单"
    )

    statistics_entry = None

    for _ in range(5):
        statistics_entry = (
            find_visible_text_any_frame(
                page,
                PHONE_STATISTICS_TEXT,
            )
        )

        if (
            statistics_entry
            is not None
        ):
            break

        page.wait_for_timeout(
            500
        )

    if statistics_entry is None:
        try:
            statistics_menu.click()
        except Exception:
            statistics_menu.click(
                force=True
            )

        page.wait_for_timeout(
            1000
        )

        for _ in range(5):
            statistics_entry = (
                find_visible_text_any_frame(
                    page,
                    PHONE_STATISTICS_TEXT,
                )
            )

            if (
                statistics_entry
                is not None
            ):
                break

            page.wait_for_timeout(
                500
            )

    assert (
        statistics_entry
        is not None
    ), (
        f"没有定位到【{PHONE_STATISTICS_TEXT}】"
    )

    try:
        statistics_entry.click()
    except Exception:
        statistics_entry.click(
            force=True
        )

    expect(
        page
    ).to_have_url(
        re.compile(
            STATISTICS_URL_PATTERN
        ),
        timeout=20000,
    )

    page.wait_for_timeout(
        2000
    )

    print(
        f"第3步：已成功进入【{PHONE_STATISTICS_TEXT}】"
    )


# ==================================================
# 详情页面辅助函数
# ==================================================

def wait_for_detail_page(page):
    print(
        "第9步：正在等待详情页面加载..."
    )

    for _ in range(30):
        try:
            body_text = (
                page.locator(
                    "body"
                )
                .inner_text()
            )

            if any(
                keyword in body_text
                for keyword
                in DETAIL_TITLE_KEYWORDS
            ):
                print(
                    "第9步：详情页面标题已加载"
                )
                return True

        except Exception:
            pass

        try:
            name_input = (
                page.locator(
                    f"input[placeholder='{NAME_PLACEHOLDER}']"
                )
            )

            phone_input = (
                page.locator(
                    f"input[placeholder='{PHONE_PLACEHOLDER}']"
                )
            )

            if (
                get_first_visible(
                    name_input
                )
                is not None
                and
                get_first_visible(
                    phone_input
                )
                is not None
            ):
                print(
                    "第9步：详情查询区域已加载"
                )
                return True

        except Exception:
            pass

        page.wait_for_timeout(
            500
        )

    return False


def read_total_detail_count(page):
    body_text = (
        page.locator(
            "body"
        )
        .inner_text()
    )

    matches = re.findall(
        r"共\s*(\d+)\s*条",
        body_text,
    )

    if not matches:
        return None

    try:
        return int(
            matches[-1]
        )
    except Exception:
        return None


def is_empty_detail(page):
    body_text = (
        page.locator(
            "body"
        )
        .inner_text()
    )

    total_count = (
        read_total_detail_count(
            page
        )
    )

    if total_count == 0:
        return True

    if (
        EMPTY_DATA_TEXT
        in body_text
    ):
        return True

    return False


def get_all_table_text(page):
    tables = page.locator(
        "table"
    )

    texts = []

    for i in range(
        tables.count()
    ):
        try:
            text = (
                tables.nth(i)
                .inner_text()
                .strip()
            )

            if text:
                texts.append(
                    text
                )

        except Exception:
            pass

    return "\n".join(
        texts
    )


def print_detail_summary(page):
    """
    Public version does not print raw business records.
    It only prints the current record count.
    """

    total_count = (
        read_total_detail_count(
            page
        )
    )

    print()
    print(
        "========== 详情数据摘要 =========="
    )

    if total_count is not None:
        print(
            f"系统分页显示：共 {total_count} 条"
        )
    else:
        print(
            "未读取到明确的记录总数"
        )

    print(
        "公开版本不输出居民姓名、电话或原始业务记录。"
    )
    print(
        "=================================="
    )

    return total_count


# ==================================================
# 电话任务统计自动化
#
# chronic_page comes from conftest.py.
# The fixture name is retained only for compatibility.
# ==================================================

@pytest.mark.ui
@pytest.mark.regression
def test_phone_statistics(
    chronic_page
):
    print()
    print(
        "======================================"
    )
    print(
        "开始执行任务统计自动化"
    )
    print(
        f"目标任务：{TASK_NAME}"
    )
    print(
        "======================================"
    )

    print(
        "公共Fixture：已完成登录并进入目标业务系统"
    )

    # ==================================================
    # Step 1-3: open statistics page
    # ==================================================

    enter_phone_statistics(
        chronic_page
    )

    # ==================================================
    # Step 4: validate statistics page
    # ==================================================

    task_time = (
        chronic_page.get_by_text(
            TASK_TIME_TEXT,
            exact=True,
        )
        .first
    )

    expect(
        task_time
    ).to_be_visible(
        timeout=15000
    )

    print(
        "第4步：统计页面加载完整"
    )

    # ==================================================
    # Step 5: choose target task
    # ==================================================

    task_candidates = (
        chronic_page.get_by_text(
            TASK_NAME,
            exact=True,
        )
    )

    latest_task = (
        get_leftmost_visible(
            task_candidates
        )
    )

    assert (
        latest_task
        is not None
    ), (
        f"没有找到目标任务【{TASK_NAME}】"
    )

    latest_task.scroll_into_view_if_needed()
    latest_task.click()

    chronic_page.wait_for_timeout(
        1500
    )

    print(
        f"第5步：已选择【{TASK_NAME}】任务"
    )

    # ==================================================
    # Step 6: validate core metrics
    # ==================================================

    for metric in CORE_METRICS:
        locator = (
            chronic_page.get_by_text(
                metric,
                exact=True,
            )
        )

        visible_metric = (
            get_first_visible(
                locator
            )
        )

        assert (
            visible_metric
            is not None
        ), (
            f"没有找到统计指标：{metric}"
        )

        print(
            f"核心指标校验成功：{metric}"
        )

    print(
        "第6步：核心统计指标显示正常"
    )

    # ==================================================
    # Step 7: validate charts
    # ==================================================

    for title in CHART_TITLES:
        locator = (
            chronic_page.get_by_text(
                title,
                exact=True,
            )
        )

        visible_title = (
            get_first_visible(
                locator
            )
        )

        assert (
            visible_title
            is not None
        ), (
            f"没有找到图表：{title}"
        )

        print(
            f"图表校验成功：{title}"
        )

    print(
        "第7步：统计图表显示正常"
    )

    # ==================================================
    # Step 8: open top-most detail
    # ==================================================

    detail_buttons = (
        chronic_page.get_by_role(
            "button",
            name=DETAIL_BUTTON_TEXT,
            exact=True,
        )
    )

    assert (
        detail_buttons.count()
        >= 1
    ), (
        "统计页面没有找到详情按钮"
    )

    connected_detail = (
        get_topmost_visible(
            detail_buttons
        )
    )

    assert (
        connected_detail
        is not None
    ), (
        "没有找到详情按钮"
    )

    connected_detail.scroll_into_view_if_needed()
    connected_detail.click()

    print(
        "第8步：已点击详情"
    )

    # ==================================================
    # Step 9: verify detail page
    # ==================================================

    detail_loaded = (
        wait_for_detail_page(
            chronic_page
        )
    )

    assert detail_loaded, (
        "点击详情后没有进入详情页面"
    )

    print(
        "第9步：已成功进入详情页面"
    )

    # ==================================================
    # Step 10: verify query area
    # ==================================================

    body_text = (
        chronic_page.locator(
            "body"
        )
        .inner_text()
    )

    for field in BASIC_FIELDS:
        assert (
            field in body_text
        ), (
            f"详情页面缺少基础查询项：{field}"
        )

        print(
            f"详情基础项校验成功：{field}"
        )

    print(
        "第10步：详情查询区域校验成功"
    )

    # ==================================================
    # Step 11: data / empty state
    # ==================================================

    total_count = (
        read_total_detail_count(
            chronic_page
        )
    )

    empty = (
        is_empty_detail(
            chronic_page
        )
    )

    print()
    print(
        "======================================"
    )

    if total_count is not None:
        print(
            f"详情当前记录数：{total_count}"
        )

    if empty:
        print(
            "当前详情页面为【空数据状态】"
        )

        assert (
            EMPTY_DATA_TEXT
            in body_text
            or total_count == 0
        ), (
            "详情显示0条，但没有发现空数据状态"
        )

        print(
            "第11步：空数据状态验证通过"
        )

    else:
        print(
            "当前详情页面存在数据"
        )

        table_text = (
            get_all_table_text(
                chronic_page
            )
        )

        for column in REQUIRED_COLUMNS:
            assert (
                column in table_text
                or column in body_text
            ), (
                f"详情页面缺少字段：{column}"
            )

            print(
                f"详情字段校验成功：{column}"
            )

        print(
            "第11步：详情数据表头校验成功"
        )

        print_detail_summary(
            chronic_page
        )

    print(
        "======================================"
    )

    # ==================================================
    # Step 12: optional resident search
    # ==================================================

    test_name = os.getenv(
        "TEST_DWELLER_NAME"
    )

    if (
        test_name
        and not empty
    ):
        name_input = (
            get_first_visible(
                chronic_page.locator(
                    f"input[placeholder='{NAME_PLACEHOLDER}']"
                )
            )
        )

        if name_input is not None:
            name_input.fill(
                test_name
            )

            chronic_page.wait_for_timeout(
                300
            )

            search_button = (
                get_first_visible(
                    chronic_page.get_by_role(
                        "button",
                        name=SEARCH_BUTTON_TEXT,
                        exact=True,
                    )
                )
            )

            assert (
                search_button
                is not None
            ), (
                "没有找到详情搜索按钮"
            )

            search_button.click()

            chronic_page.wait_for_timeout(
                1500
            )

            search_body = (
                chronic_page.locator(
                    "body"
                )
                .inner_text()
            )

            if test_name in search_body:
                print(
                    "第12步：已找到配置的测试居民"
                )
            else:
                print(
                    "当前详情没有找到配置的测试居民；"
                    "环境数据可能尚未同步，本项不判定整个测试失败。"
                )

    elif (
        test_name
        and empty
    ):
        print(
            "当前详情为0条数据，跳过测试居民搜索。"
        )

    # ==================================================
    # Complete
    # ==================================================

    print()
    print(
        "======================================"
    )
    print(
        "任务统计自动化执行成功"
    )
    print(
        "已完成：进入统计页、选择任务、"
        "验证指标与图表、进入详情、"
        "验证空数据/数据表结构。"
    )
    print(
        "======================================"
    )

    keep_browser_open(
        chronic_page
    )
