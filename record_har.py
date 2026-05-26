from cloakbrowser import launch


def main():
    browser = launch(headless=False)
    context = browser.new_context(viewport={"width": 1280, "height": 720})

    # Playwright 1.60.0: tracing.startHar() - 一行搞定 HAR 录制
    print(">>> [CloakBrowser] Starting HAR recording via tracing...")
    context.tracing.start(har_path="trace.har", screenshots=True, snapshots=True)

    page = context.new_page()

    # 反检测测试
    print(">>> [CloakBrowser] Anti-detection test...")
    page.goto("https://abrahamjuliot.github.io/creepjs/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)

    try:
        trust_score = page.locator(".score-title").first.inner_text(timeout=5000)
        print(f">>> [CloakBrowser] Trust score: {trust_score}")
    except Exception:
        print(">>> [CloakBrowser] Could not read trust score")

    print()

    # GitHub Trending
    print(">>> [CloakBrowser] Navigating to GitHub Trending...")
    page.goto("https://github.com/trending", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)
    print(">>> [CloakBrowser] Page loaded\n")

    # 保存 HAR（tracing 自动完成）
    context.tracing.stop(path="trace.har")
    print(">>> HAR + Trace saved to: trace.har")
    print(">>> Open with: npx playwright show-trace trace.har")

    browser.close()
    print("\n>>> Done")


if __name__ == "__main__":
    main()
