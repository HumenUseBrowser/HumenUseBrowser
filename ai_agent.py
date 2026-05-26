import json
import re
import sys
import io
import builtins
from openai import OpenAI

# Windows 终端 UTF-8 输出 + 实时刷新
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)

_orig_print = builtins.print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _orig_print(*args, **kwargs)
from config import (
    DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
    MAX_ACTIONS_PER_STEP, MAX_HISTORY_MESSAGES, MAX_ACTION_LOOP,
    PAGE_LOAD_WAIT_MS,
)
from browser_engine import BrowserEngine
from page_analyzer import get_page_snapshot, get_page_summary
from action_executor import execute_action

SYSTEM_PROMPT = f"""You are a browser automation agent. You control a web browser and execute tasks based on user instructions.

The browser has ALREADY been navigated to Bing (https://www.bing.com). You are now ON the Bing homepage. Do NOT navigate to Bing again.

Your job is to:
1. Generate a search query based on the user's instruction
2. Type it into the search box and search
3. Read the search results and click the most relevant link
4. Continue exploring until the task is complete

Supported action types:
1. {{"action": "click", "selector": "...", "text": "button text"}} - Click an element
2. {{"action": "type", "selector": "...", "value": "text to type"}} - Type into an input field
3. {{"action": "scroll", "direction": "down|up", "amount": "page|half"}} - Scroll the page
4. {{"action": "wait", "ms": 2000}} - Wait for specified milliseconds
5. {{"action": "extract", "selector": "...", "description": "what to extract"}} - Extract text content
6. {{"action": "done", "summary": "what was accomplished"}} - Task complete

Rules:
- Respond ONLY with a JSON array. No markdown fences, no explanation text.
- You are already on Bing. Your FIRST action should be to type a search query.
- Generate smart search keywords based on what the user wants.
- Use the selector or alt value from the snapshot as the selector.
- Maximum {MAX_ACTIONS_PER_STEP} actions per response
- Use scroll actions when you need to see more page content
- Always end with a "done" action when the task is complete
- If a previous action failed, try a different selector or approach
- Read the page snapshot carefully to find the correct selectors for elements
- If the user provides an explicit URL, navigate to it directly with a navigate action
- When login is required, ask the user for credentials
]"""


def call_deepseek(client, history):
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=history,
        temperature=0.1,
        max_tokens=1024,
    )
    raw = response.choices[0].message.content.strip()

    # 去掉 markdown 代码块
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    # 提取 JSON 数组
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(raw)


def compress_history(history):
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history
    # 保留 system prompt + 最近的消息
    system = history[0]
    recent = history[-(MAX_HISTORY_MESSAGES - 1):]
    return [system] + recent


def process_instruction(page, client, history, instruction):
    # 第一步：直接导航到必应（不经过 AI 决策）
    print("  [Auto] Navigating to Bing...")
    page.goto("https://www.bing.com", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(PAGE_LOAD_WAIT_MS)
    print(f"  [Auto] -> {page.url}")

    history.append({"role": "user", "content": instruction})

    action_count = 0
    while action_count < MAX_ACTION_LOOP:
        action_count += 1

        snapshot = get_page_snapshot(page)
        history.append({"role": "user", "content": f"Current page snapshot:\n{snapshot}"})
        history = compress_history(history)

        print(f"\n  [AI] Analyzing page... (step {action_count})")
        try:
            actions = call_deepseek(client, history)
        except json.JSONDecodeError:
            print("  [Error] Invalid JSON from AI, retrying...")
            history.append({"role": "user", "content": "Your response was not valid JSON. Please respond with only a JSON array."})
            continue
        except Exception as e:
            print(f"  [Error] API call failed: {e}")
            break

        if not isinstance(actions, list):
            actions = [actions]

        history.append({"role": "assistant", "content": json.dumps(actions, ensure_ascii=False)})

        done = False
        for act in actions:
            act_type = act.get("action", "?")
            print(f"  [Exec] {act_type}: ", end="")

            result = execute_action(page, act)
            print(result.get("result", ""))

            if not result.get("success"):
                print(f"  [Fail] {result.get('result')}")
                history.append({"role": "user", "content": f"Action failed: {result.get('result')}. Please try a different approach."})
                break

            if result.get("page_changed"):
                print(f"  [Nav] -> {result.get('new_url')}")

            if act_type == "done":
                print(f"\n  [Done] {act.get('summary', 'Task completed')}")
                done = True
                break

            if result.get("extracted"):
                print(f"  [Extracted]\n{result['extracted']}")

        if done:
            break

    if action_count >= MAX_ACTION_LOOP:
        print("  [Warning] Max action loop reached")


def run_agent():
    print("=" * 60)
    print("  AI Browser Automation Agent")
    print("  Powered by MiMo v2.5 Pro + CloakBrowser")
    print("=" * 60)

    # Command line mode: python ai_agent.py "帮我搜索 Python 教程"
    if len(sys.argv) > 1:
        instruction = " ".join(sys.argv[1:])
        print(f"\n  Instruction: {instruction}")
        print("-" * 60)

        engine = BrowserEngine()
        page = engine.start()
        client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
        history = [{"role": "system", "content": SYSTEM_PROMPT}]

        process_instruction(page, client, history, instruction)
        engine.close()
        return

    # Interactive mode
    engine = BrowserEngine()
    page = engine.start()
    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL)
    history = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("\nBrowser started. Type instructions (or 'quit' to exit)")
    print("-" * 60)

    while True:
        user_input = input("\n>>> ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            break

        process_instruction(page, client, history, user_input)
        history = [{"role": "system", "content": SYSTEM_PROMPT}]

    engine.close()
    print("\nBrowser closed. Bye!")


if __name__ == "__main__":
    run_agent()
