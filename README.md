# API + UI Automation Test Framework

基于 **Python + Pytest + Requests + Playwright** 搭建的接口与 Web UI 混合自动化测试项目，包含公共 Fixture、临时鉴权自动刷新、HTML 报告、失败截图以及高风险测试隔离等工程化能力。

> Public demo repository. All company URLs, internal routes, test accounts, tokens, templates and personal data have been replaced with safe placeholders.

---

## 项目亮点

| 能力 | 实现 |
| --- | --- |
| API 自动化 | Requests + Pytest，覆盖查询、空结果、分页参数化 |
| UI 自动化 | Playwright，覆盖登录、统计页、详情页等核心流程 |
| 公共前置 | 使用 Pytest Fixture 抽取登录、系统初始化、API 鉴权 |
| 鉴权恢复 | 检测 401 后通过 UI 登录自动获取最新临时鉴权 |
| 数据驱动 | `pytest.mark.parametrize` 覆盖多组分页参数 |
| 测试报告 | `pytest-html` 生成自包含 HTML 报告 |
| 失败定位 | UI 测试失败时自动保存页面截图 |
| 风险隔离 | 普通回归与授权高风险流程分离，使用 Marker + 环境变量 + 人工确认 |
| 敏感信息保护 | `.env` 管理本地配置，公开仓库仅保留 `.env.example` |

### 已验证基准

在脱敏前的授权测试环境中完成过一次完整安全回归：

```text
5 个 API 测试
+ 1 个登录 UI 测试
+ 1 个统计 UI 测试
= 7 Passed
```

同时验证了下面这条完整链路：

```text
旧 Token 失效
→ API 返回 401
→ 自动执行 UI 登录
→ 自动进入目标系统
→ 捕获最新 Authorization / X-AppCode
→ 再次验证接口
→ API + UI 回归继续执行
→ 输出 HTML 测试报告
```

公开仓库默认使用 `example.invalid` 和通用占位配置，因此不会连接真实业务环境。

---

## 技术栈

```text
Python
Pytest
Requests
Playwright
pytest-playwright
pytest-html
python-dotenv
Windows Batch
```

---

## 项目结构

```text
api-ui-automation-test-framework/
│
├─ test_data/
│  └─ README.md
│
├─ tests/
│  ├─ test_dweller.py
│  ├─ test_invite_flow.py
│  ├─ test_login.py
│  └─ test_statistics.py
│
├─ utils/
│  ├─ __init__.py
│  ├─ api_auth.py
│  └─ auth.py
│
├─ .env.example
├─ .gitignore
├─ config.py
├─ conftest.py
├─ pytest.ini
├─ README.md
├─ requirements.txt
├─ run_live_call.bat
└─ run_regression.bat
```

---

## 核心设计

### 1. API 自动化

`tests/test_dweller.py` 当前包含 5 条 API 测试：

```text
查询已存在数据
查询不存在数据
pageSize = 5
pageSize = 10
pageSize = 20
```

主要验证：

- HTTP 状态码
- 分页参数
- 返回数据数量
- 查询结果
- 空数据场景

分页使用 `pytest.mark.parametrize` 实现参数化。

---

### 2. UI 登录自动化

公共登录能力封装在：

```text
utils/auth.py
```

流程：

```text
打开登录页
→ 密码登录
→ 输入账号密码
→ 登录
→ 校验登录结果
→ 进入目标业务系统
```

URL、系统名称和关键页面文案全部通过环境变量配置，不在公开代码中写死真实内部信息。

---

### 3. Pytest Fixture

公共 Fixture 集中在 `conftest.py`：

```text
api_headers
user_center_page
chronic_page
```

职责：

- `api_headers`：Session 级 API 鉴权准备
- `user_center_page`：完成登录并提供已登录页面
- `chronic_page`：进入目标业务系统

这样可以减少测试文件中的重复登录和初始化代码。

---

### 4. 401 自动鉴权恢复

`utils/api_auth.py` 实现：

```text
检查当前鉴权
→ 200：直接使用
→ 401 / 缺失：自动登录
→ 进入目标业务系统
→ 监听浏览器 API 请求
→ 获取最新临时 Authorization / X-AppCode
→ 再次探测接口
→ 恢复 API 测试
```

刷新后的鉴权只写入当前 pytest 进程，不回写 `.env`。

---

### 5. 统计页面 UI 自动化

`tests/test_statistics.py` 覆盖：

```text
进入统计模块
→ 选择目标统计页
→ 选择任务
→ 校验核心指标
→ 校验图表
→ 打开详情
→ 校验查询区域
→ 兼容有数据 / 无数据状态
```

公开版本不会输出原始姓名、电话号码或完整业务记录。

---

### 6. 授权高风险流程

`tests/test_invite_flow.py` 单独标记为：

```python
@pytest.mark.live_call
```

流程包括：

```text
进入任务页面
→ 选择模板
→ 处理通知内容
→ 上传授权测试数据
→ 校验导入结果
→ 勾选测试对象
→ 执行任务
→ 校验页面成功状态
→ 捕获关键 POST Response
→ 校验关键接口 HTTP 状态
```

该测试不会加入普通回归。

---

## 风险隔离

### 普通安全回归

运行：

```bat
run_regression.bat
```

保护策略：

```text
ALLOW_TEST_CALL=false
只指定安全测试文件
只执行 regression Marker
UI 结束后自动关闭浏览器
```

### 授权高风险测试

运行：

```bat
run_live_call.bat
```

保护策略：

```text
必须人工输入 CALL
ALLOW_TEST_CALL=true 只在该脚本中开启
只运行 test_invite_flow.py
只执行 live_call Marker
使用 headed 浏览器
```

高风险测试只应在明确授权的测试环境、测试账号和测试号码上执行。

---

## HTML 报告与失败截图

项目使用 `pytest-html` 生成自包含 HTML 报告。

UI 测试失败时会自动保存截图：

```text
reports/screenshots/
```

这些运行产物已经通过 `.gitignore` 排除，不会进入公开仓库。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Chromium

```bash
playwright install chromium
```

### 3. 创建本地环境配置

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中填写你自己的测试环境配置。

### 4. 运行 API 测试

```bash
pytest tests/test_dweller.py -s -v
```

### 5. 运行安全回归

```bat
run_regression.bat
```

---

## 配置说明

公开仓库只提供：

```text
.env.example
```

真实 `.env` 应保留在本地，并已加入 `.gitignore`。

公开版默认使用：

```text
https://example.invalid
```

不会误请求真实公司环境。

---

## 敏感信息保护

公开版本不包含：

```text
真实公司域名
真实内部系统地址
真实账号 / 密码
Authorization / Cookie / Token
真实 X-AppCode
真实姓名 / 电话
真实业务 Excel 模板
真实测试报告
真实内部接口路径
```

所有真实环境信息都只应存在于本地 `.env` 或受控测试环境中。

---

## 后续优化方向

- 统一封装 API Client
- 引入 Page Object Model
- 增加统一日志模块
- 将失败截图嵌入 HTML 报告
- 增加 Mock / Demo 服务
- 接入 CI 执行安全回归
- 增加异常、边界、权限类用例
- 建立需求与自动化用例映射

---

## 项目价值

这个项目主要展示：

```text
Python 自动化能力
API 测试能力
Playwright Web UI 自动化能力
Pytest Fixture 设计能力
临时鉴权处理能力
回归测试组织能力
风险控制意识
失败定位与测试报告能力
代码脱敏与公开仓库安全意识
```

适合作为 **软件测试 / QA / 自动化测试 / 测试开发实习** 的项目实践。
