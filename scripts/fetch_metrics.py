#!/usr/bin/env python3
"""
fetch_metrics.py — 获取 Core Web Vitals 原始数据

数据来源优先级：
  1. 本地 Lighthouse CLI（推荐，无需 API Key）
  2. PageSpeed Insights API（需要 KEY，可获取真实用户数据）
  3. Chrome User Experience Report（CrUX，仅 28 天聚合）

输出：JSON 到 stdout，包含 LCP/CLS/INP/TBT/FCP 的原始值和得分。
"""

import json
import subprocess
import sys
import os
import tempfile
import argparse
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR = ".web-perf"

# CWV 阈值 (web.dev 定义)
THRESHOLDS = {
    "lcp": {"good": 2500, "poor": 4000},       # ms
    "fcp": {"good": 1800, "poor": 3000},       # ms
    "cls": {"good": 0.1, "poor": 0.25},        # score
    "tbt": {"good": 200, "poor": 600},         # ms
    "inp": {"good": 200, "poor": 500},         # ms
    "si":  {"good": 3400, "poor": 5800},       # ms (Speed Index)
    "tti": {"good": 3800, "poor": 7300},       # ms
}


def rating(metric: str, value: float) -> str:
    """根据阈值返回 good/needs-improvement/poor"""
    t = THRESHOLDS.get(metric)
    if not t:
        return "unknown"
    if value <= t["good"]:
        return "good"
    if value <= t["poor"]:
        return "needs-improvement"
    return "poor"


def run_lighthouse(url: str, extra_flags: list = None) -> dict:
    """
    使用本地 Lighthouse CLI 采集数据。
    前提：npm install -g lighthouse（或 npx lighthouse）
    """
    flags = [
        "npx", "lighthouse", url,
        "--output=json",
        "--output-path=stdout",
        "--chrome-flags=--headless=new --no-sandbox",
        "--only-categories=performance",
        "--quiet",
    ]
    if extra_flags:
        flags.extend(extra_flags)

    print(f"[fetch_metrics] Running: {' '.join(flags)}", file=sys.stderr)

    try:
        result = subprocess.run(
            flags,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(f"[fetch_metrics] Lighthouse stderr: {result.stderr[:500]}", file=sys.stderr)
            raise RuntimeError(f"Lighthouse exited with code {result.returncode}")

        return json.loads(result.stdout)

    except FileNotFoundError:
        print("[fetch_metrics] Lighthouse not found. Install with: npm install -g lighthouse",
              file=sys.stderr)
        raise
    except subprocess.TimeoutExpired:
        raise RuntimeError("Lighthouse timed out after 120 seconds")


def extract_cwv(lh_json: dict) -> dict:
    """从 Lighthouse JSON 结果中提取 Core Web Vitals 指标"""
    audits = lh_json.get("audits", {})

    # 提取可观测指标
    metrics = {}
    audit_map = {
        "lcp": "largest-contentful-paint",
        "fcp": "first-contentful-paint",
        "cls": "cumulative-layout-shift",
        "tbt": "total-blocking-time",
        "si":  "speed-index",
        "tti": "interactive",
    }

    for key, audit_id in audit_map.items():
        audit = audits.get(audit_id, {})
        value = audit.get("numericValue")
        if value is not None:
            metrics[key] = {
                "value": round(value, 2),
                "displayValue": audit.get("displayValue", ""),
                "rating": rating(key, value),
                "score": audit.get("score"),
            }

    # INP 不一定有实测数据（需要真实用户交互），但尝试从 field-data / TBT 估算
    # 优先使用 CrUX field data
    field_data = lh_json.get("environment", {}).get("fieldData", {})
    if field_data:
        for metric in ["largest_contentful_paint", "cumulative_layout_shift",
                        "first_contentful_paint", "interaction_to_next_paint"]:
            fd = field_data.get(metric, {})
            if fd and fd.get("percentile"):
                short = metric.replace("_", "")[:3].lower() if metric != "interaction_to_next_paint" else "inp"
                metrics[f"crux_{short}"] = {
                    "value": fd["percentile"],
                    "rating": fd.get("category", "unknown"),
                }

    # 估算 INP（如果没有实测数据）
    if "inp" not in metrics:
        tbt_val = metrics.get("tbt", {}).get("value", 0)
        # 粗略估算：INP ≈ TBT * 0.3 + 50（粗略经验公式，仅供参考）
        estimated_inp = round(tbt_val * 0.3 + 50, 0)
        metrics["inp"] = {
            "value": estimated_inp,
            "rating": rating("inp", estimated_inp),
            "estimated": True,
            "note": "Estimated from TBT; run RUM for real INP data",
        }

    return metrics


def extract_opportunities(lh_json: dict) -> list:
    """提取优化机会（可节省的字节数/时间）"""
    audits = lh_json.get("audits", {})
    opportunities = []

    opportunity_ids = [
        "render-blocking-resources",
        "unused-javascript",
        "unused-css-rules",
        "modern-image-formats",
        "uses-responsive-images",
        "offscreen-images",
        "uses-optimized-images",
        "uses-text-compression",
        "uses-rel-preconnect",
        "uses-rel-preload",
        "efficient-animated-content",
        "total-byte-weight",
        "dom-size",
        "third-party-summary",
        "font-display",
        "legacy-javascript",
        "duplicated-javascript",
        "prioritize-lscp-image",
        "server-response-time",
    ]

    for audit_id in opportunity_ids:
        audit = audits.get(audit_id, {})
        if not audit:
            continue

        details = audit.get("details", {})
        opp = {
            "id": audit_id,
            "title": audit.get("title", ""),
            "description": audit.get("description", ""),
            "score": audit.get("score"),
            "displayValue": audit.get("displayValue", ""),
            "details": {},
        }

        # 提取节余数据
        if "overallSavingsMs" in details:
            opp["details"]["overallSavingsMs"] = details["overallSavingsMs"]
        if "overallSavingsBytes" in details:
            opp["details"]["overallSavingsBytes"] = details["overallSavingsBytes"]

        # 特定审计详情
        if audit_id == "render-blocking-resources" and "items" in details:
            opp["details"]["blockingResources"] = [
                {"url": i.get("url", ""), "wastedMs": i.get("wastedMs", 0)}
                for i in details.get("items", [])[:10]
            ]
        if audit_id == "third-party-summary" and "items" in details:
            opp["details"]["thirdParties"] = [
                {"entity": i.get("entity", {}).get("text", ""),
                 "wastedMs": i.get("mainThreadTime", 0),
                 "transferSize": i.get("transferSize", 0)}
                for i in details.get("items", [])[:10]
            ]

        opportunities.append(opp)

    return opportunities


def run_psi_api(url: str, api_key: str, strategy: str = "mobile") -> dict:
    """
    调用 PageSpeed Insights API。
    相比 Lighthouse CLI，多了一个 CrUX 真实用户数据维度。
    """
    import urllib.request
    import urllib.parse

    params = urllib.parse.urlencode({
        "url": url,
        "key": api_key,
        "strategy": strategy,
        "category": "performance",
    })
    api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?{params}"

    req = urllib.request.Request(api_url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Fetch Core Web Vitals metrics via Lighthouse or PSI")
    parser.add_argument("url", help="URL to audit")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--psi-key", default=None,
                        help="Google PageSpeed Insights API key (optional; uses Lighthouse CLI if omitted)")
    parser.add_argument("--strategy", default="mobile", choices=["mobile", "desktop"],
                        help="Device emulation strategy (default: mobile)")
    parser.add_argument("--extra-lighthouse-flags", nargs="*", default=[],
                        help="Extra flags to pass to Lighthouse CLI")
    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 采集数据
    if args.psi_key:
        print(f"[fetch_metrics] Using PageSpeed Insights API", file=sys.stderr)
        raw = run_psi_api(args.url, args.psi_key, args.strategy)
        lh_result = raw.get("lighthouseResult", {})
    else:
        lh_flags = args.extra_lighthouse_flags
        if args.strategy == "desktop":
            lh_flags.append("--preset=desktop")
        raw = run_lighthouse(args.url, lh_flags)
        lh_result = raw

    # 提取指标
    metrics = extract_cwv(lh_result)
    opportunities = extract_opportunities(lh_result)

    # 组装输出
    output = {
        "url": args.url,
        "strategy": args.strategy,
        "timestamp": lh_result.get("fetchTime", ""),
        "lighthouseVersion": lh_result.get("lighthouseVersion", ""),
        "performanceScore": (lh_result.get("categories", {})
                             .get("performance", {})
                             .get("score", 0) * 100),
        "metrics": metrics,
        "opportunities": opportunities,
    }

    # 落盘
    output_path = os.path.join(args.output_dir, "metrics.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # 同时输出到 stdout 供管道使用
    print(json.dumps(output, indent=2, ensure_ascii=False))

    print(f"\n[fetch_metrics] Saved to {output_path}", file=sys.stderr)
    perf_score = output["performanceScore"]
    print(f"[fetch_metrics] Performance Score: {perf_score:.0f}/100", file=sys.stderr)

    lcp = metrics.get("lcp", {}).get("value")
    if lcp:
        print(f"[fetch_metrics] LCP: {lcp}ms ({metrics['lcp']['rating']})", file=sys.stderr)

    return output


if __name__ == "__main__":
    main()
