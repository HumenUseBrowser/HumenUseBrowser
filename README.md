# HumenUseBrowser

AI 驱动的浏览器自动化工具。一句话指令，AI 自动分析页面、定位元素、执行操作。

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

## 文件结构

```
├── config.py              # 配置中心（API Key、账号密码、参数）
├── browser_engine.py      # 浏览器引擎（CloakBrowser 封装）
├── page_analyzer.py       # 页面快照提取（DOM → AI 可读文本）
├── action_executor.py     # 动作执行器（click/type/navigate/scroll）
├── ai_agent.py            # 主入口（AI 对话 + 动作循环）
└── record_har.py          # HAR 网络录制工具
```

## 安装

```bash
pip install cloakbrowser openai
```

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

## 支持的 AI 模型

兼容 OpenAI 接口协议的模型均可使用：

| 模型 | Base URL |
|------|----------|
| DeepSeek | `https://api.deepseek.com` |
| MiMo | `https://token-plan-sgp.xiaomimimo.com/v1` |
| OpenAI | `https://api.openai.com/v1` |

## 工作流程

1. **自动导航** — 浏览器自动打开必应
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
