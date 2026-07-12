#!/usr/bin/env python3
"""
score_and_report.py — 汇总所有审计结果，加权打分，生成结构化报告

输入：各审计脚本的 JSON 输出文件
输出：
  1. .web-perf/audit-report.json（结构化数据）
  2. .web-perf/report.md（人类可读报告）

评分权重基于 Core Web Vitals 影响面设计：
  - LCP 相关：关键路径、图片、资源提示 → 40%
  - CLS 相关：图片尺寸、字体 → 20%
  - TBT/INP 相关：JS bundle、长任务 → 30%
  - 综合：HTML 加载、视频 → 10%
"""

import json
import sys
import os
import argparse
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------
DEFAULT_OUTPUT_DIR = ".web-perf"

# 评分权重
WEIGHTS = {
    "metrics": 0.25,        # CWV 原始得分 (Lighthouse Performance Score)
    "criticalPath": 0.20,   # 关键渲染路径
    "resourceHints": 0.10,  # 资源提示
    "images": 0.15,         # 图片优化
    "fonts": 0.05,          # 字体优化
    "jsBundles": 0.20,      # JS 性能
    "thirdParty": 0.05,     # 第三方脚本
}

# 每个类别对 CWV 的影响映射
CATEGORY_CWV_IMPACT = {
    "criticalPath": {
        "primary": "LCP",
        "secondary": "FCP",
        "impactDescription": "Eliminating render-blocking resources directly shortens LCP",
    },
    "resourceHints": {
        "primary": "LCP",
        "secondary": "FCP",
        "impactDescription": "Preload/preconnect can reduce LCP by up to 2s",
    },
    "images": {
        "primary": "LCP",
        "secondary": "CLS",
        "impactDescription": "Image optimization is the highest ROI for LCP improvement",
    },
    "fonts": {
        "primary": "LCP",
        "secondary": "CLS",
        "impactDescription": "font-display:swap and preloading prevent FOIT/FOUT that affect LCP and CLS",
    },
    "jsBundles": {
        "primary": "TBT",
        "secondary": "INP",
        "impactDescription": "Unused JS and long tasks directly increase TBT and degrade INP",
    },
}


# ---------------------------------------------------------------------------
# 数据加载
# ---------------------------------------------------------------------------
def load_json(path: str) -> Optional[dict]:
    """安全加载 JSON 文件，不存在则返回 None"""
    p = Path(path)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_fingerprint(url: str, data: dict) -> str:
    """为页面生成内容指纹（用于增量对比）"""
    fingerprint_data = {
        "url": url,
    }
    # 包含关键指标
    if "metrics" in data:
        m = data["metrics"]
        fingerprint_data["metrics"] = {
            k: m[k].get("value") if isinstance(m.get(k), dict) else m[k]
            for k in ["lcp", "fcp", "cls", "tbt"]
            if k in m
        }
    if "opportunities" in data:
        fingerprint_data["oppCount"] = len(data["opportunities"])

    fp_str = json.dumps(fingerprint_data, sort_keys=True, default=str)
    return hashlib.sha256(fp_str.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# 评分引擎
# ---------------------------------------------------------------------------
def score_metrics(metrics_data: dict) -> dict:
    """从 metrics.json 计算分数（正常化为 0-100）"""
    if not metrics_data:
        return {"score": 0, "details": {}, "note": "No metrics data available"}

    perf_score = metrics_data.get("performanceScore", 0)
    metrics = metrics_data.get("metrics", {})

    sub_scores = {}
    # Lighthouse performance score 已经是一个加权总分
    sub_scores["performanceScore"] = perf_score

    # 单独检查每个 CWV
    for key in ("lcp", "fcp", "cls", "tbt", "inp"):
        m = metrics.get(key, {})
        if m:
            rating = m.get("rating", "unknown")
            sub_scores[key] = {
                "value": m.get("value"),
                "rating": rating,
                "score": 100 if rating == "good" else (60 if rating == "needs-improvement" else 30),
            }

    return {
        "score": perf_score,
        "details": sub_scores,
        "normalizedScore": perf_score,
    }


def score_category(data: dict, category: str) -> dict:
    """从审计结果中计算某类别的分数"""
    if not data:
        return {"score": 100, "note": "No data"}

    issues = data.get("issues", [])
    score_info = data.get("score", {})

    if isinstance(score_info, dict) and "score" in score_info:
        return {
            "score": score_info["score"],
            "grade": score_info.get("grade", "N/A"),
            "issueCount": len(issues),
            "criticalCount": sum(1 for i in issues if i.get("severity") == "critical"),
        }

    # 如果没有预计算分数，根据 issue 数量估算
    critical = sum(1 for i in issues if i.get("severity") == "critical")
    warnings = sum(1 for i in issues if i.get("severity") == "warning")
    score = max(0, 100 - critical * 15 - warnings * 5)

    return {
        "score": score,
        "grade": "A" if score >= 90 else "B" if score >= 75 else "C",
        "issueCount": len(issues),
        "criticalCount": critical,
    }


def compute_overall_score(scores: dict) -> dict:
    """计算加权总分数"""
    total = 0
    breakdown = {}

    for category, weight in WEIGHTS.items():
        if category in scores:
            cat_score = scores[category].get("score", 0)
            weighted = cat_score * weight
            total += weighted
            breakdown[category] = {
                "rawScore": cat_score,
                "weight": f"{weight * 100:.0f}%",
                "weightedScore": round(weighted, 1),
            }

    overall = round(total, 0)

    grade = (
        "A+" if overall >= 95 else
        "A" if overall >= 90 else
        "B" if overall >= 75 else
        "C" if overall >= 60 else
        "D" if overall >= 40 else
        "F"
    )

    return {
        "overallScore": overall,
        "grade": grade,
        "breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# 优先级排序
# ---------------------------------------------------------------------------
def prioritize_issues(all_issues: list) -> list:
    """按 Core Web Vitals 影响面排序（不是发现顺序）"""
    # 影响面权重
    impact_weights = {
        "render-blocking": 10,
        "lcp-image": 9,
        "unused-javascript": 8,
        "long-tasks": 8,
        "sync-scripts-in-head": 7,
        "font-display-block": 7,
        "legacy-format": 6,
        "missing-dimensions": 6,
        "missing-srcset": 5,
        "preload-missing-as": 7,
        "preload-font-no-crossorigin": 6,
        "font-preload-no-crossorigin": 6,
        "heavy-third-party": 5,
        "preconnect-overuse": 2,
        "same-origin-preconnect": 1,
        "no-font-preload": 4,
        "too-many-weights": 2,
        "legacy-font-format": 2,
        "preload-overuse": 2,
    }

    # 严重度加权
    severity_multiplier = {
        "critical": 3,
        "warning": 1.5,
        "low": 0.5,
    }

    scored = []
    for issue in all_issues:
        base = impact_weights.get(issue.get("type", ""), 3)
        sev_mult = severity_multiplier.get(issue.get("severity", "warning"), 1)
        priority_score = base * sev_mult

        scored.append({
            "priorityScore": round(priority_score, 1),
            **issue,
        })

    scored.sort(key=lambda x: x["priorityScore"], reverse=True)

    # 标注 P0/P1/P2
    for item in scored:
        if item["priorityScore"] >= 20:
            item["priority"] = "P0"
        elif item["priorityScore"] >= 10:
            item["priority"] = "P1"
        else:
            item["priority"] = "P2"

    return scored


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------
def generate_markdown_report(report_data: dict, audience: str = "dev") -> str:
    """生成人类可读的 Markdown 报告"""
    lines = []

    # Header
    lines.append(f"# Web Performance Audit Report")
    lines.append(f"")
    lines.append(f"**URL:** `{report_data['url']}`")
    lines.append(f"**Date:** {report_data['timestamp']}")
    lines.append(f"**Audience:** {audience}")
    lines.append(f"")

    # Overall Score
    overall = report_data["overallScore"]
    lines.append(f"## Overall Score: {overall['overallScore']}/100 — Grade {overall['grade']}")
    lines.append(f"")
    lines.append(f"| Category | Score | Weight | Weighted |")
    lines.append(f"|----------|-------|--------|----------|")
    for cat, bd in overall["breakdown"].items():
        lines.append(f"| {cat} | {bd['rawScore']} | {bd['weight']} | {bd['weightedScore']} |")
    lines.append(f"")

    # CWV Metrics
    metrics = report_data.get("metrics", {})
    if metrics:
        lines.append(f"## Core Web Vitals")
        lines.append(f"")
        lines.append(f"| Metric | Value | Rating |")
        lines.append(f"|--------|-------|--------|")
        for key in ("lcp", "fcp", "cls", "tbt", "inp"):
            m = metrics.get(key, {})
            if m:
                rating_emoji = "🟢" if m.get("rating") == "good" else "🟡" if m.get("rating") == "needs-improvement" else "🔴"
                estimated = " (estimated)" if m.get("estimated") else ""
                lines.append(f"| {key.upper()} | {m.get('displayValue', m.get('value', 'N/A'))}{estimated} | {rating_emoji} {m.get('rating', 'N/A')} |")
        lines.append(f"")

    # Prioritized Issues
    all_issues = report_data.get("allIssues", [])
    if all_issues:
        p0 = [i for i in all_issues if i.get("priority") == "P0"]
        p1 = [i for i in all_issues if i.get("priority") == "P1"]
        p2 = [i for i in all_issues if i.get("priority") == "P2"]

        lines.append(f"## Issues (P0 → P2, ordered by CWV impact)")
        lines.append(f"")

        for priority, issue_list in [("P0 — Critical", p0), ("P1 — High", p1), ("P2 — Moderate", p2)]:
            if not issue_list:
                continue
            lines.append(f"### {priority}")
            lines.append(f"")

            for idx, issue in enumerate(issue_list, 1):
                sev_emoji = "🔴" if issue.get("severity") == "critical" else "🟡"
                lines.append(f"**{idx}. [{issue.get('type', 'unknown')}]** {sev_emoji}")
                lines.append(f"")

                desc = issue.get("description", issue.get("title", ""))
                lines.append(f"> {desc}")
                lines.append(f"")

                # CWV impact
                for cat, impact_info in CATEGORY_CWV_IMPACT.items():
                    if issue.get("type", "").startswith(cat[:4]) or cat in issue.get("type", ""):
                        lines.append(f"- **Affects:** {impact_info['primary']} (primary), {impact_info['secondary']} (secondary)")
                        break

                # Resource info
                if issue.get("resource"):
                    lines.append(f"- **Resource:** `{issue['resource']}`")
                if issue.get("domain"):
                    lines.append(f"- **Domain:** `{issue['domain']}`")
                if issue.get("wastedMs"):
                    lines.append(f"- **Wasted time:** {issue['wastedMs']}ms")
                if issue.get("totalKB"):
                    lines.append(f"- **Size:** {issue['totalKB']}KB total, {issue.get('unusedKB', 'N/A')}KB unused")

                lines.append(f"")

                # Fix code
                fix = issue.get("fix", "")
                if fix and audience == "dev":
                    lines.append(f"**🔧 Fix:**")
                    lines.append(f"")
                    if "\n" in fix:
                        lines.append(f"```html")
                        lines.append(fix)
                        lines.append(f"```")
                    else:
                        lines.append(f"```")
                        lines.append(fix)
                        lines.append(f"```")
                    lines.append(f"")

                # Reference
                if issue.get("ref"):
                    lines.append(f"📚 See: `{issue['ref']}`")
                    lines.append(f"")

                lines.append(f"---")
                lines.append(f"")

    # Estimated Improvements
    if report_data.get("estimatedImprovements"):
        est = report_data["estimatedImprovements"]
        lines.append(f"## Estimated Improvements")
        lines.append(f"")
        for item in est:
            lines.append(f"- **{item['optimization']}:** Save ~{item['savings']} ({item['metric']})")
        lines.append(f"")

    # Generation info
    lines.append(f"---")
    lines.append(f"*Report generated by web-perf-audit skill*")
    lines.append(f"*References: See `references/` directory for web.dev-aligned optimization guides*")

    return "\n".join(lines)


def generate_html_dashboard(report_data: dict) -> str:
    """生成 HTML 仪表盘（简化版，供后续扩展）"""
    # 这是一个占位模板——完整的仪表盘使用 templates/dashboard.html
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Web Performance Dashboard — {report_data.get('url', 'N/A')}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
    .score-circle {{ width: 150px; height: 150px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 3rem; font-weight: 700; }}
    .grade-A {{ background: conic-gradient(#22c55e {report_data['overallScore']['overallScore']}%, #1e293b 0); }}
    .card {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; margin: 1rem 0; }}
    .metric-row {{ display: flex; gap: 1rem; flex-wrap: wrap; }}
    .metric-card {{ background: #334155; border-radius: 8px; padding: 1rem; flex: 1; min-width: 150px; }}
    .good {{ color: #22c55e; }} .poor {{ color: #ef4444; }} .needs-improvement {{ color: #eab308; }}
  </style>
</head>
<body>
  <h1>Web Performance Dashboard</h1>
  <p>URL: {report_data.get('url', 'N/A')} | {report_data.get('timestamp', '')}</p>
  <div class="card">
    <h2>Overall Score</h2>
    <div class="score-circle grade-A">{report_data['overallScore']['overallScore']}</div>
    <p>Grade: {report_data['overallScore']['grade']}</p>
  </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# 增量对比
# ---------------------------------------------------------------------------
def compare_with_previous(current: dict, output_dir: str) -> dict:
    """对比上次审计结果"""
    prev_path = Path(output_dir) / "audit-report.json"
    if not prev_path.exists():
        return {"note": "First audit — no previous data to compare"}

    prev = load_json(str(prev_path))
    if not prev:
        return {"note": "Could not load previous report"}

    curr_score = current.get("overallScore", {}).get("overallScore", 0)
    prev_score = prev.get("overallScore", {}).get("overallScore", 0)

    diff = curr_score - prev_score

    return {
        "previousScore": prev_score,
        "currentScore": curr_score,
        "change": diff,
        "direction": "improved" if diff > 0 else ("declined" if diff < 0 else "unchanged"),
        "previousAuditTime": prev.get("timestamp", ""),
        "currentAuditTime": current.get("timestamp", ""),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Aggregate audit results and generate performance report")
    parser.add_argument("url", help="Audited URL")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})")
    parser.add_argument("--metrics-file", default=None,
                        help="Path to metrics.json")
    parser.add_argument("--critical-path-file", default=None,
                        help="Path to critical path analysis JSON")
    parser.add_argument("--resource-hints-file", default=None,
                        help="Path to resource hints analysis JSON")
    parser.add_argument("--images-file", default=None,
                        help="Path to image audit JSON")
    parser.add_argument("--fonts-file", default=None,
                        help="Path to font audit JSON")
    parser.add_argument("--js-file", default=None,
                        help="Path to JS bundles audit JSON")
    parser.add_argument("--audience", default="dev", choices=["dev", "pm"],
                        help="Report detail level (dev=full code fixes, pm=summary only)")
    parser.add_argument("--format", default="all", choices=["json", "md", "html", "all"],
                        help="Output format(s)")
    args = parser.parse_args()

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    # 尝试默认路径加载文件
    def find_file(arg_val, default_name):
        if arg_val:
            return arg_val
        p = Path(args.output_dir) / default_name
        return str(p) if p.exists() else None

    metrics_file = find_file(args.metrics_file, "metrics.json")
    critical_path_file = find_file(args.critical_path_file, "critical-path.json")
    resource_hints_file = find_file(args.resource_hints_file, "resource-hints.json")
    images_file = find_file(args.images_file, "images.json")
    fonts_file = find_file(args.fonts_file, "fonts.json")
    js_file = find_file(args.js_file, "js-bundles.json")

    # 加载各审计结果
    metrics_data = load_json(metrics_file) if metrics_file else None
    critical_path_data = load_json(critical_path_file) if critical_path_file else None
    resource_hints_data = load_json(resource_hints_file) if resource_hints_file else None
    images_data = load_json(images_file) if images_file else None
    fonts_data = load_json(fonts_file) if fonts_file else None
    js_data = load_json(js_file) if js_file else None

    # 评分
    scores = {}
    scores["metrics"] = score_metrics(metrics_data) if metrics_data else {"score": 0, "note": "No data"}
    scores["criticalPath"] = score_category(critical_path_data or {}, "criticalPath")
    scores["resourceHints"] = score_category(resource_hints_data or {}, "resourceHints")
    scores["images"] = score_category(images_data or {}, "images")
    scores["fonts"] = score_category(fonts_data or {}, "fonts")
    scores["jsBundles"] = score_category(js_data or {}, "jsBundles")

    overall = compute_overall_score(scores)

    # 收集所有 issue
    all_issues = []
    for data, category in [
        (critical_path_data, "criticalPath"),
        (resource_hints_data, "resourceHints"),
        (images_data, "images"),
        (fonts_data, "fonts"),
        (js_data, "jsBundles"),
    ]:
        if data and "issues" in data:
            for issue in data["issues"]:
                issue["category"] = category
                all_issues.append(issue)

    # 优先级排序
    prioritized = prioritize_issues(all_issues)

    # 构建报告数据
    report = {
        "url": args.url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overallScore": overall,
        "scores": scores,
        "metrics": metrics_data.get("metrics", {}) if metrics_data else {},
        "performanceScore": metrics_data.get("performanceScore", 0) if metrics_data else 0,
        "opportunities": metrics_data.get("opportunities", []) if metrics_data else [],
        "allIssues": prioritized,
        "issueSummary": {
            "total": len(prioritized),
            "p0": sum(1 for i in prioritized if i.get("priority") == "P0"),
            "p1": sum(1 for i in prioritized if i.get("priority") == "P1"),
            "p2": sum(1 for i in prioritized if i.get("priority") == "P2"),
        },
    }

    # 增量对比
    report["comparison"] = compare_with_previous(report, args.output_dir)

    # --- 输出 ---
    report_path = Path(args.output_dir) / "audit-report.json"

    if args.format in ("json", "all"):
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[score_and_report] JSON report saved to {report_path}", file=sys.stderr)

    if args.format in ("md", "all"):
        md_content = generate_markdown_report(report, args.audience)
        md_path = Path(args.output_dir) / "report.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"[score_and_report] Markdown report saved to {md_path}", file=sys.stderr)

    if args.format in ("html", "all"):
        html_content = generate_html_dashboard(report)
        html_path = Path(args.output_dir) / "dashboard.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"[score_and_report] HTML dashboard saved to {html_path}", file=sys.stderr)

    # 指纹缓存
    fingerprint = compute_fingerprint(args.url, report)
    fingerprint_path = Path(args.output_dir) / "fingerprint.txt"
    with open(fingerprint_path, "w") as f:
        f.write(fingerprint)
    print(f"[score_and_report] Fingerprint: {fingerprint}", file=sys.stderr)

    # CLI 摘要
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  Overall: {overall['overallScore']}/100 ({overall['grade']})", file=sys.stderr)
    print(f"  Issues: {report['issueSummary']['total']} total "
          f"({report['issueSummary']['p0']} P0, {report['issueSummary']['p1']} P1, "
          f"{report['issueSummary']['p2']} P2)", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    return report


if __name__ == "__main__":
    main()
