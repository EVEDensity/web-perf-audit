#!/usr/bin/env python3
"""
analyze_critical_path.py — 分析关键渲染路径

输入：metrics.json（由 fetch_metrics.py 生成）或完整的 Lighthouse JSON
输出：关键路径分析结果 JSON，包括：
  - 阻塞渲染的资源列表
  - 关键请求链深度
  - 关键路径总字节数
  - 每个阻塞资源的优化建议
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Optional


def load_metrics(input_path: str) -> dict:
    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_full_lighthouse(path: str) -> dict:
    """加载完整的 Lighthouse JSON 报告"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_render_blocking(lh_json: dict) -> dict:
    """分析渲染阻塞资源"""
    audits = lh_json.get("audits", {})
    rbr = audits.get("render-blocking-resources", {})
    details = rbr.get("details", {})

    if not details:
        return {"blockingResources": [], "totalWastedMs": 0, "analysis": "No render-blocking resources detected"}

    items = details.get("items", [])
    total_wasted = details.get("overallSavingsMs", 0)

    resources = []
    for item in items:
        url = item.get("url", "")
        wasted_ms = item.get("wastedMs", 0)
        signal = item.get("signal", "")  # 阻塞信号
        location = item.get("location", {})

        res = {
            "url": url,
            "wastedMs": wasted_ms,
            "type": "script" if url.endswith(".js") else "stylesheet",
            "location": {
                "type": location.get("type", ""),
                "line": location.get("line", 0),
                "column": location.get("column", 0),
            },
        }

        # 优化建议
        if res["type"] == "script":
            res["suggestion"] = "Add 'defer' or 'async' attribute, or move to end of <body>"
            res["fix"] = f'<script src="{url.split("/")[-1]}" defer></script>'
        else:
            res["suggestion"] = "Inline critical CSS, load remaining asynchronously with media='print' + onload swap"
            res["fix"] = (
                f'<link rel="preload" href="{url.split("/")[-1]}" as="style" '
                f'onload="this.rel=\'stylesheet\'">'
            )

        resources.append(res)

    return {
        "blockingResources": resources,
        "totalWastedMs": total_wasted,
        "count": len(resources),
        "severity": "critical" if total_wasted > 500 else ("warning" if total_wasted > 200 else "low"),
    }


def analyze_critical_chains(lh_json: dict) -> dict:
    """分析关键请求链"""
    audits = lh_json.get("audits", {})
    chains_audit = audits.get("critical-request-chains", {})
    details = chains_audit.get("details", {})

    chains = details.get("chains", {})
    if not chains:
        return {"maxDepth": 0, "totalBytes": 0, "chains": []}

    def traverse(node, depth=1):
        """递归遍历请求链，收集 URL、字节数、深度"""
        results = []
        request = node.get("request", {})
        url = request.get("url", "")
        transfer_size = request.get("transferSize", 0)
        results.append({
            "url": url,
            "depth": depth,
            "transferSize": transfer_size,
        })
        children = node.get("children", {})
        for child_url, child_node in children.items():
            results.extend(traverse(child_node, depth + 1))
        return results

    all_requests = []
    for root_url, root_node in chains.items():
        all_requests.extend(traverse(root_node))

    if not all_requests:
        return {"maxDepth": 0, "totalBytes": 0, "chains": []}

    max_depth = max(r["depth"] for r in all_requests)
    total_bytes = sum(r["transferSize"] for r in all_requests)

    return {
        "maxDepth": max_depth,
        "totalBytes": total_bytes,
        "totalBytesFormatted": f"{total_bytes / 1024:.1f} KB",
        "requests": all_requests,
        "analysis": (
            "Deep chains detected — reduce by inlining or flattening dependencies"
            if max_depth > 3 else "Chain depth is acceptable"
        ),
    }


def analyze_dom(lh_json: dict) -> dict:
    """分析 DOM 大小"""
    audits = lh_json.get("audits", {})
    dom_audit = audits.get("dom-size", {})
    details = dom_audit.get("details", {})

    items = details.get("items", [])
    if not items:
        return {"totalElements": 0, "maxDepth": 0, "analysis": "N/A"}

    first_item = items[0]
    total_elements = first_item.get("value", 0)

    # 查找 maxDepth
    max_depth = 0
    for item in items:
        if "depth" in str(item.get("statistic", "")).lower():
            val = item.get("value", "")

    return {
        "totalElements": total_elements,
        "maxDOMDepth": max_depth,
        "severity": (
            "warning" if total_elements > 800 else
            "critical" if total_elements > 1500 else
            "good"
        ),
        "suggestion": (
            "DOM size exceeds 1500 nodes — consider virtual scrolling, pagination, or reducing inline elements"
            if total_elements > 1500 else
            "DOM size is within reasonable range"
            if total_elements <= 800 else
            "DOM size is acceptable but consider trimming for mobile devices"
        ),
    }


def analyze_resource_summary(lh_json: dict) -> dict:
    """分析资源大小分布"""
    audits = lh_json.get("audits", {})
    rs = audits.get("resource-summary", {})
    details = rs.get("details", {})

    items = details.get("items", [])
    if not items:
        return {"resources": [], "analysis": "N/A"}

    resources = []
    for item in items:
        resources.append({
            "type": item.get("resourceType", ""),
            "count": item.get("requestCount", 0),
            "transferSize": item.get("transferSize", 0),
            "sizeFormatted": f"{item.get('transferSize', 0) / 1024:.1f} KB",
        })

    # 计算占比最大的资源类型
    total_size = sum(r["transferSize"] for r in resources)
    for r in resources:
        r["percentage"] = round(r["transferSize"] / total_size * 100, 1) if total_size > 0 else 0

    return {
        "resources": resources,
        "totalSize": total_size,
        "totalSizeFormatted": f"{total_size / 1024:.1f} KB",
        "heaviestType": max(resources, key=lambda r: r["transferSize"])["type"] if resources else "N/A",
    }


def estimate_optimal_crp(crp_analysis: dict) -> dict:
    """估算优化后的关键路径时间"""
    blocking = crp_analysis.get("renderBlocking", {})
    chains = crp_analysis.get("criticalChains", {})

    wasted_ms = blocking.get("totalWastedMs", 0)
    current_depth = chains.get("maxDepth", 0)

    # 估算：消除阻塞 + 减少链深度，通常可节省 30-70% 的关键路径时间
    estimated_savings = wasted_ms  # 直接的阻塞时间节省
    if current_depth > 3:
        estimated_savings += (current_depth - 3) * 150  # 每多一层额外 ~150ms

    return {
        "estimatedSavingsMs": estimated_savings,
        "estimatedSavingsFormatted": f"{estimated_savings / 1000:.2f}s",
        "targetMaxDepth": 3,
        "targetMaxBlocking": 0,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Analyze critical rendering path from Lighthouse data")
    parser.add_argument("input", help="Path to metrics.json or full Lighthouse JSON report")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file path (default: stdout)")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    lh_json = load_full_lighthouse(args.input) if "lighthouse" in str(input_path).lower() else load_metrics(args.input)

    # 分析各维度
    result = {
        "url": lh_json.get("url", lh_json.get("requestedUrl", "")),
        "renderBlocking": analyze_render_blocking(lh_json),
        "criticalChains": analyze_critical_chains(lh_json),
        "domSize": analyze_dom(lh_json),
        "resourceSummary": analyze_resource_summary(lh_json),
    }

    result["estimatedOptimal"] = estimate_optimal_crp(result)

    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"[analyze_critical_path] Saved to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    # Summary
    blocking_count = result["renderBlocking"]["count"]
    print(f"[analyze_critical_path] Render-blocking resources: {blocking_count} "
          f"(wasted {result['renderBlocking']['totalWastedMs']}ms)",
          file=sys.stderr)
    print(f"[analyze_critical_path] Critical chain depth: {result['criticalChains']['maxDepth']}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
