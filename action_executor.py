from config import ACTION_TIMEOUT_MS, PAGE_LOAD_WAIT_MS


HIGHLIGHT_JS = """
(args) => {
    const {selector, actionType, value} = args;
    let el = null;

    // 查找目标元素
    if (selector.startsWith('text=')) {
        const text = selector.slice(5).replace(/"/g, '');
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) {
            if (walker.currentNode.textContent.trim().includes(text)) {
                el = walker.currentNode.parentElement;
                break;
            }
        }
    } else if (selector.startsWith('role=')) {
        // role 选择器 fallback
        el = document.querySelector('[role]');
    } else {
        el = document.querySelector(selector);
    }

    if (!el) return false;

    // 滚动到元素可见
    el.scrollIntoView({behavior: 'smooth', block: 'center'});

    // 创建高亮框
    const rect = el.getBoundingClientRect();
    const box = document.createElement('div');
    box.id = '__ai_highlight__';
    box.style.cssText = `
        position: fixed;
        left: ${rect.left - 4}px;
        top: ${rect.top - 4}px;
        width: ${rect.width + 8}px;
        height: ${rect.height + 8}px;
        border: 3px solid #ff4444;
        border-radius: 4px;
        box-shadow: 0 0 12px rgba(255,68,68,0.6);
        z-index: 2147483647;
        pointer-events: none;
        animation: ai-pulse 0.8s ease-in-out infinite alternate;
    `;

    // 创建标签
    const label = document.createElement('div');
    label.id = '__ai_label__';
    const labelText = actionType === 'type'
        ? `✏️ ${actionType}: "${(value || '').slice(0, 20)}"`
        : `🖱️ ${actionType}`;
    label.textContent = labelText;
    label.style.cssText = `
        position: fixed;
        left: ${rect.left - 4}px;
        top: ${rect.top - 30}px;
        background: #ff4444;
        color: white;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 12px;
        font-family: monospace;
        z-index: 2147483647;
        pointer-events: none;
        white-space: nowrap;
    `;

    // 注入动画样式
    if (!document.getElementById('__ai_highlight_style__')) {
        const style = document.createElement('style');
        style.id = '__ai_highlight_style__';
        style.textContent = `
            @keyframes ai-pulse {
                from { opacity: 1; box-shadow: 0 0 12px rgba(255,68,68,0.6); }
                to { opacity: 0.7; box-shadow: 0 0 20px rgba(255,68,68,0.9); }
            }
        `;
        document.head.appendChild(style);
    }

    // 清除旧高亮
    const old = document.getElementById('__ai_highlight__');
    if (old) old.remove();
    const oldLabel = document.getElementById('__ai_label__');
    if (oldLabel) oldLabel.remove();

    document.body.appendChild(box);
    document.body.appendChild(label);

    return true;
}
"""

CLEAR_HIGHLIGHT_JS = """
() => {
    const el = document.getElementById('__ai_highlight__');
    if (el) el.remove();
    const label = document.getElementById('__ai_label__');
    if (label) label.remove();
}
"""


def _highlight(page, selector, action_type, value=""):
    """在页面上高亮显示目标元素"""
    try:
        # 处理 text= 和 role= 选择器，转为 CSS 选择器
        css_selector = selector
        if selector.startswith('text=') or selector.startswith('role='):
            # 对于 text/role 选择器，尝试用 get_by_text 定位后高亮
            try:
                if selector.startswith('text='):
                    text = selector[5:].strip('"')
                    loc = page.get_by_text(text, exact=False).first
                else:
                    loc = page.locator(selector).first
                loc.evaluate("""(el, args) => {
                    el.scrollIntoView({behavior: 'smooth', block: 'center'});
                    const rect = el.getBoundingClientRect();
                    const box = document.createElement('div');
                    box.id = '__ai_highlight__';
                    box.style.cssText = `
                        position: fixed; left: ${rect.left - 4}px; top: ${rect.top - 4}px;
                        width: ${rect.width + 8}px; height: ${rect.height + 8}px;
                        border: 3px solid #ff4444; border-radius: 4px;
                        box-shadow: 0 0 12px rgba(255,68,68,0.6);
                        z-index: 2147483647; pointer-events: none;
                        animation: ai-pulse 0.8s ease-in-out infinite alternate;
                    `;
                    const label = document.createElement('div');
                    label.id = '__ai_label__';
                    label.textContent = args.label;
                    label.style.cssText = `
                        position: fixed; left: ${rect.left - 4}px; top: ${rect.top - 30}px;
                        background: #ff4444; color: white; padding: 2px 8px;
                        border-radius: 3px; font-size: 12px; font-family: monospace;
                        z-index: 2147483647; pointer-events: none; white-space: nowrap;
                    `;
                    if (!document.getElementById('__ai_highlight_style__')) {
                        const s = document.createElement('style');
                        s.id = '__ai_highlight_style__';
                        s.textContent = '@keyframes ai-pulse{from{opacity:1}to{opacity:0.7}}';
                        document.head.appendChild(s);
                    }
                    document.getElementById('__ai_highlight__')?.remove();
                    document.getElementById('__ai_label__')?.remove();
                    document.body.appendChild(box);
                    document.body.appendChild(label);
                }""", {"label": f"🖱️ {action_type}"})
                return
            except Exception:
                return

        page.evaluate(HIGHLIGHT_JS, {
            "selector": css_selector,
            "actionType": action_type,
            "value": value or ""
        })
    except Exception:
        pass


def _clear_highlight(page):
    """清除高亮"""
    try:
        page.evaluate(CLEAR_HIGHLIGHT_JS)
    except Exception:
        pass


def execute_action(page, action):
    action_type = action.get("action", "")
    url_before = page.url

    try:
        if action_type == "navigate":
            return _navigate(page, action)
        elif action_type == "click":
            return _click(page, action)
        elif action_type == "type":
            return _type(page, action)
        elif action_type == "scroll":
            return _scroll(page, action)
        elif action_type == "wait":
            return _wait(page, action)
        elif action_type == "extract":
            return _extract(page, action)
        elif action_type == "done":
            return {"success": True, "action": action, "result": action.get("summary", "完成"),
                    "page_changed": False}
        else:
            return {"success": False, "action": action, "result": f"未知动作类型: {action_type}",
                    "page_changed": False}
    except Exception as e:
        page_changed = page.url != url_before
        return {"success": False, "action": action, "result": f"执行错误: {e}",
                "page_changed": page_changed, "new_url": page.url if page_changed else None}


def _navigate(page, action):
    url = action.get("url", "")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(PAGE_LOAD_WAIT_MS)
    return {"success": True, "action": action, "result": f"已导航到 {page.url}",
            "page_changed": True, "new_url": page.url}


def _click(page, action):
    selector = action.get("selector", "")
    text = action.get("text", "")

    # 尝试主选择器
    if selector:
        try:
            _highlight(page, selector, "click")
            page.wait_for_timeout(600)
            page.locator(selector).first.click(timeout=ACTION_TIMEOUT_MS)
            _clear_highlight(page)
            page.wait_for_timeout(800)
            return {"success": True, "action": action, "result": f"已点击 {selector}",
                    "page_changed": page.url != action.get("_url_before", ""),
                    "new_url": page.url}
        except Exception:
            _clear_highlight(page)

    # 尝试文本选择器
    if text:
        try:
            _highlight(page, f'text={text}', "click")
            page.wait_for_timeout(600)
            page.get_by_text(text, exact=False).first.click(timeout=ACTION_TIMEOUT_MS)
            _clear_highlight(page)
            page.wait_for_timeout(800)
            return {"success": True, "action": action, "result": f"已点击文本 '{text}'",
                    "page_changed": page.url != action.get("_url_before", ""),
                    "new_url": page.url}
        except Exception:
            _clear_highlight(page)

    # 尝试 role 选择器
    if text:
        try:
            _highlight(page, f'role=button[name="{text}"]', "click")
            page.wait_for_timeout(600)
            page.get_by_role("button", name=text).click(timeout=ACTION_TIMEOUT_MS)
            _clear_highlight(page)
            page.wait_for_timeout(800)
            return {"success": True, "action": action, "result": f"已点击按钮 '{text}'",
                    "page_changed": page.url != action.get("_url_before", ""),
                    "new_url": page.url}
        except Exception:
            _clear_highlight(page)

    return {"success": False, "action": action,
            "result": f"点击失败: 找不到元素 selector={selector} text={text}",
            "page_changed": False}


def _type(page, action):
    selector = action.get("selector", "")
    value = action.get("value", "")

    if not selector:
        return {"success": False, "action": action, "result": "缺少 selector",
                "page_changed": False}

    try:
        _highlight(page, selector, "type", value)
        page.wait_for_timeout(600)
        loc = page.locator(selector).first
        loc.click(timeout=ACTION_TIMEOUT_MS)
        loc.fill(value, timeout=ACTION_TIMEOUT_MS)
        _clear_highlight(page)
        page.wait_for_timeout(500)
        return {"success": True, "action": action,
                "result": f"已在 {selector} 输入 '{value[:10]}...'",
                "page_changed": False}
    except Exception as e:
        _clear_highlight(page)
        # fallback: 尝试通过 name 属性
        name = action.get("name", "")
        if name:
            try:
                _highlight(page, f'[name="{name}"]', "type", value)
                page.wait_for_timeout(600)
                loc = page.locator(f'[name="{name}"]').first
                loc.click(timeout=ACTION_TIMEOUT_MS)
                loc.fill(value, timeout=ACTION_TIMEOUT_MS)
                _clear_highlight(page)
                page.wait_for_timeout(500)
                return {"success": True, "action": action,
                        "result": f"已通过 name={name} 输入内容",
                        "page_changed": False}
            except Exception:
                _clear_highlight(page)
        return {"success": False, "action": action,
                "result": f"输入失败: {e}", "page_changed": False}


def _scroll(page, action):
    direction = action.get("direction", "down")
    amount = action.get("amount", "page")

    if amount == "page":
        pixels = "window.innerHeight"
    elif amount == "half":
        pixels = "window.innerHeight / 2"
    else:
        pixels = str(int(amount))

    sign = "-" if direction == "up" else ""
    page.evaluate(f"window.scrollBy(0, {sign}{pixels})")
    page.wait_for_timeout(500)

    return {"success": True, "action": action,
            "result": f"已向{direction}滚动 {amount}",
            "page_changed": False}


def _wait(page, action):
    ms = action.get("ms", 2000)
    page.wait_for_timeout(ms)
    return {"success": True, "action": action, "result": f"已等待 {ms}ms",
            "page_changed": False}


def _extract(page, action):
    selector = action.get("selector", "")
    desc = action.get("description", "内容")

    if not selector:
        return {"success": False, "action": action, "result": "缺少 selector",
                "page_changed": False}

    try:
        texts = page.locator(selector).all_inner_texts()
        content = "\n".join(texts[:20])
        return {"success": True, "action": action,
                "result": f"提取到 {desc}:\n{content}",
                "page_changed": False, "extracted": content}
    except Exception as e:
        return {"success": False, "action": action,
                "result": f"提取失败: {e}", "page_changed": False}
