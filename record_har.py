import json
from datetime import datetime, timezone
from cloakbrowser import launch


def main():
    requests_list = []

    # 使用 CloakBrowser 隐身浏览器（自带反检测补丁）
    browser = launch(headless=False)
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
    )
    page = context.new_page()

    # 监听请求
    def on_request(request):
        requests_list.append({
            "url": request.url,
            "method": request.method,
            "headers": request.headers,
            "post_data": request.post_data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    # 监听响应
    def on_response(response):
        entry = next(
            (r for r in requests_list if r["url"] == response.url and "status" not in r),
            None,
        )
        if entry:
            entry["status"] = response.status
            entry["status_text"] = response.status_text
            entry["response_headers"] = response.headers
            try:
                body = response.body()
                entry["body_size"] = len(body)
            except Exception:
                entry["body_size"] = 0

    page.on("request", on_request)
    page.on("response", on_response)

    # 先跑一下反检测检测页面
    print(">>> [CloakBrowser] 访问反检测测试页...")
    page.goto("https://abrahamjuliot.github.io/creepjs/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)

    # 抓取检测结果
    try:
        trust_score = page.locator(".score-title").first.inner_text(timeout=5000)
        print(f">>> [CloakBrowser] 反检测信任分: {trust_score}")
    except Exception:
        print(">>> [CloakBrowser] 未能读取信任分（页面可能还在加载）")

    print()

    # 清空请求列表，重新录制 HAR
    requests_list.clear()

    print(">>> [CloakBrowser] 访问 GitHub Trending 页面...")
    page.goto("https://github.com/trending", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(5000)
    print(f">>> [CloakBrowser] 页面加载完成，共捕获 {len(requests_list)} 条请求\n")

    # 构造 HAR
    har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "CloakBrowser HAR Demo", "version": "1.60.0"},
            "pages": [{
                "startedDateTime": datetime.now(timezone.utc).isoformat(),
                "id": "page_1",
                "title": "GitHub Trending",
                "pageTimings": {"onContentLoad": -1, "onLoad": -1},
            }],
            "entries": [],
        }
    }

    for req in requests_list:
        entry = {
            "startedDateTime": req["timestamp"],
            "time": 0,
            "request": {
                "method": req["method"],
                "url": req["url"],
                "httpVersion": "HTTP/2.0",
                "cookies": [],
                "headers": [{"name": k, "value": str(v)} for k, v in req["headers"].items()],
                "queryString": [],
                "headersSize": -1,
                "bodySize": len(req["post_data"]) if req["post_data"] else 0,
            },
            "response": {
                "status": req.get("status", 0),
                "statusText": req.get("status_text", ""),
                "httpVersion": "HTTP/2.0",
                "cookies": [],
                "headers": [
                    {"name": k, "value": str(v)}
                    for k, v in req.get("response_headers", {}).items()
                ],
                "content": {
                    "size": req.get("body_size", 0),
                    "mimeType": req.get("response_headers", {}).get("content-type", "unknown"),
                },
                "redirectURL": "",
                "headersSize": -1,
                "bodySize": req.get("body_size", 0),
            },
            "cache": {},
            "timings": {"send": 0, "wait": 0, "receive": 0},
        }
        if req["post_data"]:
            entry["request"]["postData"] = {
                "text": req["post_data"],
                "mimeType": "application/x-www-form-urlencoded",
            }
        har["log"]["entries"].append(entry)

    har_path = "cloakbrowser-trending.har"
    with open(har_path, "w", encoding="utf-8") as f:
        json.dump(har, f, ensure_ascii=False, indent=2)
    print(f">>> HAR 文件已保存到: {har_path}\n")

    # 打印请求摘要
    print("┌────┬────────┬──────────────────────────────────────────────────────────────────────────────────┐")
    print("│ #  │ 状态   │ URL                                                                              │")
    print("├────┼────────┼──────────────────────────────────────────────────────────────────────────────────┤")
    for i, req in enumerate(requests_list):
        num = str(i + 1).rjust(2)
        status = str(req.get("status", "---")).ljust(6)
        url = req["url"]
        if len(url) > 78:
            url = url[:75] + "..."
        url = url.ljust(78)
        print(f"│ {num} │ {status} │ {url} │")
    print("└────┴────────┴──────────────────────────────────────────────────────────────────────────────────┘")

    # 请求类型统计
    by_type = {}
    for req in requests_list:
        ct = req.get("response_headers", {}).get("content-type", "other")
        t = ct.split(";")[0].split("/")[0]
        by_type[t] = by_type.get(t, 0) + 1

    print("\n>>> 请求类型统计:")
    for t, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"    {t}: {count} 条")

    # 前 5 条详情
    print("\n>>> 前 5 条请求详情:")
    for i, req in enumerate(requests_list[:5]):
        print(f"\n--- 请求 #{i + 1} ---")
        print(f"  方法: {req['method']}")
        print(f"  URL:  {req['url']}")
        print(f"  状态: {req.get('status', 'N/A')}")
        print(f"  Content-Type: {req.get('response_headers', {}).get('content-type', 'N/A')}")
        print(f"  响应大小: {req.get('body_size', 0)} bytes")

    browser.close()
    print("\n>>> 完成")


if __name__ == "__main__":
    main()
