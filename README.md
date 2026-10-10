# API + UI 自动化测试框架实践

这是一个基于 **Python + Pytest + Requests + Playwright** 搭建的接口与 Web UI 混合自动化测试项目。

公开版本已经对真实公司域名、内部系统名称、接口路径、业务模板、测试账号、Token、测试数据和报告内容做了脱敏处理。仓库默认使用 `example.invalid` 和通用占位配置，不会连接真实业务环境。

---

## 项目简介

项目围绕一个典型的业务管理系统自动化场景展开，覆盖：

- API 查询与分页校验
- Web 登录自动化
- 统计页面自动化
- 详情页数据 / 空数据兼容
- 授权测试任务流程
- 临时鉴权失效检测与自动刷新
- HTML 测试报告
- UI 失败自动截图
- 普通回归与高风险测试隔离

项目重点不是单个页面脚本，而是把测试前置、鉴权、报告、安全开关和执行入口整理成可复用的自动化测试结构。

---

## 技术栈

| 技术 | 用途 |
| --- | --- |
| Python | 自动化脚本开发 |
| Pytest | 测试组织、Fixture、参数化、Marker |
| Requests | HTTP API 自动化 |
| Playwright | Web UI 自动化 |
| pytest-playwright | Playwright 与 Pytest 集成 |
| pytest-html | HTML 测试报告 |
| python-dotenv | 环境变量与敏感配置管理 |
| Windows Batch | 一键回归和隔离执行 |

---

## 项目结构

```text
outbound_api_test_public/
│
├─ test_data/
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

## 核心能力

### 1. API 自动化

`tests/test_dweller.py` 当前包含：

- 已存在数据查询
- 不存在数据查询
- 分页大小 `5 / 10 / 20` 参数化校验

业务参数通过环境变量配置，不在公开代码中写死真实接口业务值。

---

### 2. UI 登录自动化

`utils/auth.py` 封装公共登录能力：

```text
打开登录页
→ 密码登录
→ 输入账号密码
→ 登录
→ 校验登录结果
→ 进入目标业务系统
```

登录 URL、按钮文案、成功页面标识和目标系统名称均通过环境变量配置。

---

### 3. Pytest Fixture

公共 Fixture 集中在 `conftest.py`。

主要包括：

```text
api_headers
user_center_page
chronic_page
```

其中：

- `api_headers`：Session 级别鉴权准备
- `user_center_page`：完成登录并提供已登录页面
- `chronic_page`：进入目标业务系统

通过 Fixture 抽取公共前置，减少测试文件中的重复代码。

---

### 4. 临时鉴权自动刷新

API 测试运行前会先检查当前鉴权是否有效。

```text
读取当前鉴权
→ 发起只读探测请求
→ 200：直接复用
→ 401 / 缺失：自动执行 UI 登录
→ 进入目标业务系统
→ 捕获最新 Authorization / X-AppCode
→ 再次验证
→ 继续执行 API 测试
```

新鉴权只写入当前 pytest 进程，不回写 `.env`。

这可以避免长期固定 Token 过期后导致整组接口用例批量失败。

---

### 5. 统计页面自动化

`tests/test_statistics.py` 覆盖通用统计页面流程：

```text
进入统计模块
→ 打开目标统计页
→ 选择任务
→ 校验核心指标
→ 校验图表
→ 进入详情
→ 校验查询区域
→ 兼容有数据 / 无数据状态
```

公开版不会输出原始居民姓名、电话或完整业务记录。

---

### 6. 授权测试流程

`tests/test_invite_flow.py` 作为高风险业务用例单独隔离。

流程包括：

```text
进入测试任务页面
→ 选择模板
→ 处理通知内容
→ 上传测试数据
→ 校验导入结果
→ 勾选授权测试对象
→ 执行任务
→ 校验页面成功提示
→ 捕获关键 POST Response
→ 校验关键接口 HTTP 状态
```

该测试默认不会执行真实任务。

---

## 安全隔离

项目把普通回归和高风险测试分成两个独立入口。

### 普通回归

```bat
run_regression.bat
```

安全策略：

```text
ALLOW_TEST_CALL=false
只运行安全测试文件
只执行 regression Marker
```

---

### 高风险测试

```bat
run_live_call.bat
```

安全策略：

```text
必须人工输入 CALL
ALLOW_TEST_CALL=true 只在该脚本中开启
只运行 test_invite_flow.py
只执行 live_call Marker
```

高风险测试只应在明确授权的测试环境、测试账号和测试号码上运行。

---

## HTML 报告与失败截图

项目使用 `pytest-html` 生成自包含 HTML 报告。

UI 测试失败时，`conftest.py` 会尝试自动保存页面截图到：

```text
reports/screenshots/
```

报告、截图、登录状态等本地运行产物已经加入 `.gitignore`，不应提交到公开仓库。

---

## 环境配置

安装依赖：

```bash
pip install -r requirements.txt
```

安装 Chromium：

```bash
playwright install chromium
```

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

然后在本地 `.env` 中填写自己的测试环境配置。

公开仓库中的默认 URL 使用：

```text
https://example.invalid
```

因此不会误访问真实业务系统。

---

## 常用命令

运行 API 测试：

```bash
pytest tests/test_dweller.py -s -v
```

查看测试收集：

```bash
pytest tests/test_dweller.py --collect-only -q
```

运行安全回归：

```bat
run_regression.bat
```

运行隔离的授权测试：

```bat
run_live_call.bat
```

---

## 本地验证结果

在脱敏前的授权测试环境中，安全回归基准曾完成：

```text
5 个 API 测试
+ 1 个登录 UI 测试
+ 1 个统计 UI 测试
= 7 Passed
```

并验证过以下工程能力：

```text
Token 失效检测
→ UI 自动登录
→ 自动捕获最新临时鉴权
→ API 自动恢复执行
→ UI 回归继续执行
→ HTML 报告输出
```

公开仓库默认配置为脱敏占位值，因此需要自行配置测试环境后才能运行。

---

## 工程实践亮点

- API + UI 混合自动化
- Session 级鉴权 Fixture
- 公共登录 / 系统初始化 Fixture
- 401 自动检测与临时鉴权刷新
- 参数化分页测试
- HTML 测试报告
- UI 失败自动截图
- `.env` 敏感配置隔离
- 普通回归 / 高风险测试分离
- 人工确认 + Marker + 环境变量多重保护

---

## 后续可继续优化

- 封装统一 API Client
- 引入 Page Object Model
- 增加统一日志模块
- 将失败截图嵌入 HTML 报告
- 加入 Mock / Demo 服务
- 接入 CI 执行安全回归
- 增加更多异常、边界、权限类用例
- 增加测试数据工厂
- 建立需求与自动化用例映射

---

## 脱敏说明

公开版本不包含：

```text
真实公司域名
真实内部系统地址
真实账号 / 密码
Authorization / Cookie / Token
真实 X-AppCode
真实居民姓名 / 电话
真实业务 Excel 模板
真实业务测试报告
真实内部接口路径
```

所有真实环境信息都应只存在于本地 `.env` 或受控测试环境中。

---

## 项目用途

该项目主要用于展示：

```text
自动化测试框架搭建能力
接口测试能力
Web UI 自动化能力
Pytest Fixture 设计能力
测试风险控制意识
测试结果追踪与故障定位能力
```

适合作为测试开发、软件测试、QA 自动化方向的学习与项目实践案例。
