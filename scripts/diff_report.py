#!/usr/bin/env python3
"""
diff_report.py — 对比两次审计结果，输出性能变化分析

用途：
  - CI/PR 场景：合并前后各跑一次，生成差异报告
  - 增量追踪：定期审计同一站点，追踪趋势

输入：两次 audit-report.json（或 metrics.json）
输出：差异分析报告（JSON + Markdown 摘要）
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# 辅助
# ---------------------------------------------------------------------------
def load_json(path: str) -> Optional[dict]:
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 对比指标
# ---------------------------------------------------------------------------
def diff_metrics(before: dict, after: dict) -> list:
    """对比 Core Web Vitals 指标变化"""
    metrics_before = before.get("metrics", {})
    metrics_after = after.get("metrics", {})

    changes = []
    for key in ("lcp", "fcp", "cls", "tbt", "inp"):
        b = metrics_before.get(key, {})
        a = metrics_after.get(key, {})

        b_val = b.get("value") if isinstance(b, dict) else b
        a_val = a.get("value") if isinstance(a, dict) else a

        if b_val is not None and a_val is not None:
            delta = a_val - b_val
            pct = (delta / b_val * 100) if b_val != 0 else 0

            change = {
                "metric": key.upper(),
                "before": round(b_val, 2),
                "after": round(a_val, 2),
                "delta": round(delta, 2),
                "deltaPercent": round(pct, 1),
            }

            # 判断是改善还是恶化
            if key in ("cls",):  # 越小越好
                change["direction"] = "improved" if delta < 0 else ("declined" if delta > 0 else "unchanged")
            else:  # lcp, fcp, tbt, inp: 越小越好
                change["direction"] = "improved" if delta < 0 else ("declined" if delta > 0 else "unchanged")

            changes.append(change)

    return changes


def diff_scores(before: dict, after: dict) -> dict:
    """对比总分和分类分数"""
    b_overall = before.get("overallScore", {})
    a_overall = after.get("overallScore", {})

    b_score = b_overall.get("overallScore", 0)
    a_score = a_overall.get("overallScore", 0)

    b_breakdown = b_overall.get("breakdown", {})
    a_breakdown = a_overall.get("breakdown", {})

    category_changes = {}
    for cat in set(list(b_breakdown.keys()) + list(a_breakdown.keys())):
        b_cat = b_breakdown.get(cat, {}).get("rawScore", 0)
        a_cat = a_breakdown.get(cat, {}).get("rawScore", 0)
        category_changes[cat] = round(a_cat - b_cat, 1)

    return {
        "overall": {
            "before": b_score,
            "after": a_score,
            "delta": round(a_score - b_score, 1),
            "direction": "improved" if a_score > b_score else ("declined" if a_score < b_score else "unchanged"),
        },
        "categories": category_changes,
    }


def diff_issues(before: dict, after: dict) -> dict:
    """对比 issue 数量和类型变化"""
    b_issues = before.get("allIssues", [])
    a_issues = after.get("allIssues", [])

    b_summary = before.get("issueSummary", {})
    a_summary = after.get("issueSummary", {})

    # 按类型分组计数
    from collections import Counter
    b_types = Counter(i.get("type", "unknown") for i in b_issues)
    a_types = Counter(i.get("type", "unknown") for i in a_issues)

    # 新增的 issue 类型
    new_types = set(a_types.keys()) - set(b_types.keys())
    # 消除的 issue 类型
    resolved_types = set(b_types.keys()) - set(a_types.keys())

    # 每种类型的变化
    type_changes = {}
    for t in set(list(b_types.keys()) + list(a_types.keys())):
        delta = a_types.get(t, 0) - b_types.get(t, 0)
        if delta != 0:
            type_changes[t] = delta

    return {
        "totalBefore": b_summary.get("total", len(b_issues)),
        "totalAfter": a_summary.get("total", len(a_issues)),
        "delta": a_summary.get("total", len(a_issues)) - b_summary.get("total", len(b_issues)),
        "resolved": sorted(resolved_types),
        "new": sorted(new_types),
        "byType": type_changes,
    }


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------
def generate_diff_markdown(diff_data: dict) -> str:
    lines = []

    lines.append("# Performance Diff Report")
    lines.append("")
    lines.append(f"**Before:** {diff_data['before']['timestamp']} ({diff_data['before']['url']})")
    lines.append(f"**After:** {diff_data['after']['timestamp']} ({diff_data['after']['url']})")
    lines.append("")

    # Overall Score
    score_diff = diff_data["scores"]["overall"]
    direction_emoji = "🟢" if score_diff["direction"] == "improved" else "🔴" if score_diff["direction"] == "declined" else "➡️"
    lines.append(f"## Overall Score {direction_emoji}")
    lines.append(f"")
    lines.append(f"| | Before | After | Delta |")
    lines.append(f"|---|--------|-------|-------|")
    lines.append(f"| **Score** | {score_diff['before']} | {score_diff['after']} | {score_diff['delta']:+.1f} |")
    lines.append(f"")

    # Category changes
    cat_changes = diff_data["scores"]["categories"]
    if cat_changes:
        lines.append(f"### Category Changes")
        lines.append(f"")
        lines.append(f"| Category | Delta |")
        lines.append(f"|----------|-------|")
        for cat, delta in sorted(cat_changes.items(), key=lambda x: x[1]):
            emoji = "🟢" if delta > 0 else "🔴" if delta < 0 else "➡️"
            lines.append(f"| {cat} | {emoji} {delta:+.1f} |")
        lines.append(f"")

    # Metrics
    metrics_diff = diff_data["metrics"]
    if metrics_diff:
        lines.append(f"## Core Web Vitals Changes")
        lines.append(f"")
        lines.append(f"| Metric | Before | After | Delta | % Change |")
        lines.append(f"|--------|--------|-------|-------|----------|")
        for m in metrics_diff:
            emoji = "🟢" if m["direction"] == "improved" else "🔴" if m["direction"] == "declined" else "➡️"
            lines.append(f"| {m['metric']} | {m['before']} | {m['after']} | {emoji} {m['delta']:+.2f} | {m['deltaPercent']:+.1f}% |")
        lines.append(f"")

    # Issues
    issue_diff = diff_data["issues"]
    lines.append(f"## Issue Changes")
    lines.append(f"")
    lines.append(f"- **Before:** {issue_diff['totalBefore']} issues")
    lines.append(f"- **After:** {issue_diff['totalAfter']} issues")
    lines.append(f"- **Delta:** {issue_diff['delta']:+d}")
    lines.append(f"")

    if issue_diff["resolved"]:
        lines.append(f"### ✅ Resolved Issue Types")
        for t in issue_diff["resolved"]:
            lines.append(f"- `{t}`")
        lines.append(f"")

    if issue_diff["new"]:
        lines.append(f"### ⚠️ New Issue Types")
        for t in issue_diff["new"]:
            lines.append(f"- `{t}`")
        lines.append(f"")

    if issue_diff["byType"]:
        lines.append(f"### Count Changes by Type")
        lines.append(f"")
        lines.append(f"| Type | Delta |")
        lines.append(f"|------|-------|")
        for t, delta in sorted(issue_diff["byType"].items(), key=lambda x: abs(x[1]), reverse=True):
            emoji = "🟢" if delta < 0 else "🔴" if delta > 0 else "➡️"
            lines.append(f"| `{t}` | {emoji} {delta:+d} |")
        lines.append(f"")

    lines.append(f"---")
    lines.append(f"*Diff report generated by web-perf-audit*")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Compare two web performance audit reports for CI/PR diff analysis"
    )
    parser.add_argument("before", help="Path to before audit-report.json")
    parser.add_argument("after", help="Path to after audit-report.json")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON file path (default: stdout)")
    parser.add_argument("--format", default="json", choices=["json", "md", "both"],
                        help="Output format")
    args = parser.parse_args()

    before = load_json(args.before)
    after = load_json(args.after)

    if not before:
        print(f"Error: Before file not found: {args.before}", file=sys.stderr)
        sys.exit(1)
    if not after:
        print(f"Error: After file not found: {args.after}", file=sys.stderr)
        sys.exit(1)

    # 执行对比
    diff_result = {
        "before": {
            "url": before.get("url", ""),
            "timestamp": before.get("timestamp", ""),
        },
        "after": {
            "url": after.get("url", ""),
            "timestamp": after.get("timestamp", ""),
        },
        "scores": diff_scores(before, after),
        "metrics": diff_metrics(before, after),
        "issues": diff_issues(before, after),
    }

    # 输出
    json_output = json.dumps(diff_result, indent=2, ensure_ascii=False)

    if args.format in ("json", "both"):
        if args.output:
            out_path = Path(args.output)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(json_output)
            print(f"[diff_report] JSON saved to {args.output}", file=sys.stderr)
        else:
            print(json_output)

    if args.format in ("md", "both"):
        md = generate_diff_markdown(diff_result)
        if args.output:
            md_path = Path(args.output).with_suffix(".md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"[diff_report] Markdown saved to {md_path}", file=sys.stderr)
        else:
            print(md)

    # CLI 摘要
    score_d = diff_result["scores"]["overall"]
    direction = score_d["direction"]
    print(f"[diff_report] Score: {score_d['before']} → {score_d['after']} "
          f"({score_d['delta']:+.1f}, {direction})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
