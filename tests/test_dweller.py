import os

import pytest
import requests

from config import (
    BASE_URL,
    DWELLER_API,
)


# ==================================================
# Public/demo API configuration
# ==================================================

QUERY_SCENE = os.getenv(
    "TEST_API_QUERY_SCENE",
    "resident_list",
)

GROUP_TYPE = int(
    os.getenv(
        "TEST_API_GROUP_TYPE",
        "1",
    )
)

RANK = int(
    os.getenv(
        "TEST_API_RANK",
        "0",
    )
)

NONEXISTENT_NAME = os.getenv(
    "TEST_NONEXISTENT_DWELLER_NAME",
    "AUTO_TEST_NOT_EXIST_999999",
)


# ==================================================
# Request parameter helper
# ==================================================

def build_params(
    *,
    name,
    page_size,
):
    return {
        "groupId": "",
        "name": name,
        "queryScene": QUERY_SCENE,
        "groupType": GROUP_TYPE,
        "rank": RANK,
        "pageIndex": 1,
        "pageSize": page_size,
    }


# ==================================================
# API tests
# ==================================================

@pytest.mark.api
@pytest.mark.regression
def test_search_dweller(
    api_headers
):
    """
    场景：根据已存在的测试居民姓名查询
    预期：接口返回对应居民
    """

    test_name = os.getenv(
        "TEST_DWELLER_NAME"
    )

    assert test_name, (
        "没有配置 TEST_DWELLER_NAME"
    )

    response = requests.get(
        BASE_URL + DWELLER_API,
        headers=api_headers,
        params=build_params(
            name=test_name,
            page_size=20,
        ),
        timeout=10,
    )

    assert (
        response.status_code
        == 200
    ), (
        f"接口请求失败，状态码："
        f"{response.status_code}，"
        f"响应内容：{response.text}"
    )

    result = response.json()

    assert result["pageIndex"] == 1
    assert result["pageSize"] == 20
    assert result["totalCount"] >= 1
    assert len(result["data"]) >= 1

    names = [
        item.get("name")
        for item in result["data"]
    ]

    assert (
        test_name in names
    ), (
        f"搜索测试居民失败，"
        f"返回记录数：{len(names)}"
    )


@pytest.mark.api
@pytest.mark.regression
def test_search_nonexistent_dweller(
    api_headers
):
    """
    场景：查询不存在的居民
    预期：结果为空
    """

    response = requests.get(
        BASE_URL + DWELLER_API,
        headers=api_headers,
        params=build_params(
            name=NONEXISTENT_NAME,
            page_size=20,
        ),
        timeout=10,
    )

    assert (
        response.status_code
        == 200
    ), (
        f"接口请求失败，状态码："
        f"{response.status_code}，"
        f"响应内容：{response.text}"
    )

    result = response.json()

    assert (
        result["totalCount"]
        == 0
    ), (
        "totalCount 应为 0，"
        f"实际为：{result['totalCount']}"
    )

    assert (
        result["data"]
        == []
    ), (
        "data 应为空，"
        f"实际返回记录数：{len(result['data'])}"
    )


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize(
    "page_size",
    [5, 10, 20],
)
def test_dweller_page_size(
    api_headers,
    page_size,
):
    """
    场景：验证不同分页大小
    预期：接口返回的 pageSize 与请求参数一致
    """

    test_name = os.getenv(
        "TEST_DWELLER_NAME"
    )

    assert test_name, (
        "没有配置 TEST_DWELLER_NAME"
    )

    response = requests.get(
        BASE_URL + DWELLER_API,
        headers=api_headers,
        params=build_params(
            name=test_name,
            page_size=page_size,
        ),
        timeout=10,
    )

    assert (
        response.status_code
        == 200
    ), (
        f"接口请求失败，状态码："
        f"{response.status_code}，"
        f"响应内容：{response.text}"
    )

    result = response.json()

    assert (
        result["pageIndex"]
        == 1
    )

    assert (
        result["pageSize"]
        == page_size
    ), (
        f"请求 pageSize={page_size}，"
        f"实际返回 pageSize="
        f"{result['pageSize']}"
    )

    assert (
        len(result["data"])
        <= page_size
    ), (
        "返回数据数量超过分页大小："
        f"{len(result['data'])}"
        f" > {page_size}"
    )
