# HumenUseBrowser

AI 驱动的浏览器自动化工具。一句话指令，AI 自动分析页面、定位元素、执行操作。

## 灵感来源

本项目受以下两个项目启发：

- **[CloakBrowser](https://github.com/nicobailey/cloakbrowser)** — 基于 Playwright 的隐身浏览器，内置反检测补丁，可绕过指纹识别、WebDriver 检测等反爬机制。本项目使用 CloakBrowser 作为底层浏览器引擎，确保自动化操作不被目标网站识别为机器人。

- **[Playwright](https://github.com/microsoft/playwright)** — 微软开源的浏览器自动化框架，支持 Chromium、Firefox、WebKit 三大引擎。本项目基于 Playwright 的页面操作能力（点击、输入、滚动、提取）和 v1.60.0 新增的 Tracing/HAR 录制功能构建。

## Playwright v1.60.0 新功能

本项目充分利用了 Playwright v1.60.0（2025 年 5 月 11 日发布）的关键新特性：

### HAR 录制与 Tracing 深度集成

`tracing.startHar()` / `tracing.stopHar()` 将 HAR 录制作为一等公民的 Tracing API，同时记录操作轨迹、截图、DOM 快照和网络请求：

```python
context.tracing.start(har_path="trace.har", screenshots=True, snapshots=True)
page.goto("https://example.com")
context.tracing.stop(path="trace.har")
# trace.har 包含 HAR + 操作轨迹 + 截图，可直接拖入 DevTools 回放
```

### Drop API

`locator.drop()` 模拟外部文件拖拽上传，适用于测试拖拽上传区域：

```python
await page.locator('#dropzone').drop({
    files: {'name': 'note.txt', 'mimeType': 'text/plain', 'buffer': Buffer.from('hello')}
})
```

### Aria Snapshots 增强

- `expect(page).toMatchAriaSnapshot()` 现可直接在 Page 上使用
- `locator.ariaSnapshot()` 新增 `boxes` 选项，输出每个元素的边界框坐标 `[box=x,y,width,height]`，专为 AI 消费设计

### 其他重要更新

- `test.abort()` — 从 fixture/hook 中中止测试
- `locator.highlight()` 新增 `style` 选项，可自定义高亮样式
- `browser.on('context')` 事件 — 监听新上下文创建
- HTML reporter 支持直接打开 `.zip` 文件

## 架构

```
用户自然语言输入 → 必应搜索 → AI 智能分析 → 结构化动作 → 浏览器执行 → 页面快照 → 循环
```

## 核心特性

- **一句话驱动** — 只需说"帮我登录超星学习通"，AI 自动完成全部操作
- **探索式搜索** — 从必应开始，AI 自动生成搜索词，逐步找到目标
- **视觉标注** — 操作时红色线框标注目标元素，实时可见
- **隐身浏览器** — CloakBrowser 反检测，绕过指纹识别
- **错误自愈** — 选择器失败时 AI 自动切换方案重试
- **HAR + Trace 录制** — 基于 Playwright 1.60.0 的 tracing.startHar()，一份文件包含操作轨迹、网络请求、截图和 DOM 快照

## 文件结构

```
├── config.py              # 配置中心（API Key、账号密码、参数）
├── browser_engine.py      # 浏览器引擎（CloakBrowser + Playwright Tracing 封装）
├── page_analyzer.py       # 页面快照提取（DOM → AI 可读文本）
├── action_executor.py     # 动作执行器（click/type/navigate/scroll + 视觉标注）
├── ai_agent.py            # 主入口（AI 对话 + 动作循环）
├── record_har.py          # HAR 网络录制工具（基于 tracing.startHar()）
└── requirements.txt       # 依赖清单
```

## 安装

```bash
pip install -r requirements.txt
```

依赖：
- `cloakbrowser>=0.3.30` — 隐身浏览器
- `playwright==1.60.0` — 浏览器自动化框架
- `openai>=1.0.0` — AI API 客户端

## 配置

编辑 `config.py`：

```python
DEEPSEEK_API_KEY = "your-api-key"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

DEFAULT_PHONE = "your-phone"
DEFAULT_PASSWORD = "your-password"
```

## 使用

### 命令行模式

```bash
python ai_agent.py "帮我登录超星学习通"
python ai_agent.py "帮我找GitHub今天最热门的项目"
python ai_agent.py "帮我查一下今天的天气"
```

### 交互模式

```bash
python ai_agent.py
>>> 帮我登录超星学习通
>>> 查看我的课程
>>> quit
```

### HAR 录制

```bash
python record_har.py
# 生成 trace.har，包含 HAR + 操作轨迹 + 截图
# 用 npx playwright show-trace trace.har 查看
```

## 支持的 AI 模型

兼容 OpenAI 接口协议的模型均可使用：

| 模型 | Base URL |
|------|----------|
| DeepSeek | `https://api.deepseek.com` |
| MiMo | `https://token-plan-sgp.xiaomimimo.com/v1` |
| OpenAI | `https://api.openai.com/v1` |

## 工作流程

1. **自动导航** — 浏览器自动打开必应（不经过 AI 决策）
2. **AI 分析** — 根据用户指令生成搜索关键词
3. **页面快照** — 提取所有可交互元素（按钮、输入框、链接）
4. **AI 决策** — 返回 JSON 动作数组（点击/输入/滚动/提取）
5. **执行动作** — 带视觉标注执行每个操作
6. **循环** — 重新快照 → AI 再决策 → 直到任务完成

## AI 动作类型

```json
{"action": "click", "selector": "#loginBtn"}
{"action": "type", "selector": "input[name=\"phone\"]", "value": "18878103869"}
{"action": "navigate", "url": "https://github.com/trending"}
{"action": "scroll", "direction": "down", "amount": "page"}
{"action": "extract", "selector": ".course-list", "description": "课程列表"}
{"action": "wait", "ms": 3000}
{"action": "done", "summary": "任务完成"}
```

## License

Apache License 2.0
