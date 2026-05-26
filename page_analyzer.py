from config import MAX_SNAPSHOT_ELEMENTS, MAX_ELEMENT_TEXT_LENGTH


EXTRACT_JS = """
() => {
    const selectors = [
        'a[href]', 'button', 'input', 'select', 'textarea',
        '[role=button]', '[role=link]', '[role=textbox]',
        '[role=combobox]', '[role=listbox]', '[role=menuitem]',
        '[role=tab]', '[role=checkbox]', '[role=radio]',
        '[onclick]', '[tabindex]:not([tabindex="-1"])'
    ];
    const all = document.querySelectorAll(selectors.join(', '));
    const results = [];

    function getSelector(el) {
        if (el.id) return '#' + CSS.escape(el.id);
        if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
        if (el.getAttribute('aria-label'))
            return el.tagName.toLowerCase() + '[aria-label="' + el.getAttribute('aria-label') + '"]';
        const classes = Array.from(el.classList).filter(c => !c.match(/^[0-9]/)).slice(0, 2);
        if (classes.length) return el.tagName.toLowerCase() + '.' + classes.map(c => CSS.escape(c)).join('.');
        return null;
    }

    function getAltSelector(el) {
        const text = (el.innerText || el.value || el.placeholder || '').trim().slice(0, 60);
        if (text) {
            const tag = el.tagName.toLowerCase();
            if (tag === 'button' || tag === 'a' || el.getAttribute('role') === 'button')
                return 'text="' + text.replace(/"/g, '\\\\"') + '"';
            if (el.getAttribute('role'))
                return 'role=' + el.getAttribute('role') + '[name="' + text.replace(/"/g, '\\\\"') + '"]';
        }
        return null;
    }

    for (const el of all) {
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden') continue;
        if (el.offsetWidth === 0 && el.offsetHeight === 0) continue;

        const tag = el.tagName.toLowerCase();
        const text = (el.innerText || el.value || el.placeholder || '').trim();
        const truncated = text.length > 60 ? text.slice(0, 60) + '...' : text;

        const info = {
            index: results.length + 1,
            tag: tag,
            text: truncated,
            id: el.id || '',
            name: el.name || '',
            type: el.type || '',
            href: el.href ? el.href.slice(0, 100) : '',
            placeholder: el.placeholder || '',
            disabled: el.disabled,
            selector: getSelector(el),
            alt: getAltSelector(el),
            role: el.getAttribute('role') || '',
        };
        results.push(info);
    }
    return results;
}
"""


def get_page_snapshot(page):
    try:
        elements = page.evaluate(EXTRACT_JS)
    except Exception as e:
        return f"=== Page Snapshot ===\nURL: {page.url}\nError extracting elements: {e}"

    title = page.title()
    url = page.url

    # 优先显示 input 和 button
    priority = {"input": 0, "button": 1, "textarea": 2, "select": 3}
    elements.sort(key=lambda el: priority.get(el["tag"], 9))

    if len(elements) > MAX_SNAPSHOT_ELEMENTS:
        elements = elements[:MAX_SNAPSHOT_ELEMENTS]

    lines = [
        "=== Page Snapshot ===",
        f"URL: {url}",
        f"Title: {title}",
        f"Interactive elements ({len(elements)} shown):",
    ]

    for el in elements:
        parts = [f"[{el['index']}] {el['tag']}"]

        if el["type"]:
            parts.append(f"[type={el['type']}]")
        if el["text"]:
            parts.append(f'"{el["text"]}"')
        if el["name"]:
            parts.append(f'name="{el["name"]}"')
        if el["placeholder"]:
            parts.append(f'placeholder="{el["placeholder"]}"')
        if el["href"]:
            parts.append(f'-> {el["href"]}')
        if el["role"]:
            parts.append(f'role={el["role"]}')
        if el["disabled"]:
            parts.append("[DISABLED]")

        selector_str = ""
        if el["selector"]:
            selector_str = f"selector: {el['selector']}"
        if el["alt"]:
            selector_str += f", alt: {el['alt']}"

        if selector_str:
            parts.append(f"({selector_str})")

        lines.append(" ".join(parts))

    return "\n".join(lines)


def get_page_summary(page):
    return f"URL: {page.url}\nTitle: {page.title()}"
