#!/usr/bin/env python3
"""
audit_images.py — 图片性能审计

检测维度：
  1. 格式（是否使用 WebP/AVIF）
  2. 响应式（是否有 srcset/sizes）
  3. 懒加载（是否有 loading="lazy"）
  4. 尺寸匹配（显示尺寸 vs 实际尺寸）
  5. CLS 防护（是否有 width/height）
  6. LCP 图片优化（是否被懒加载、是否有 fetchpriority="high"）

输入：HTML 文件路径或 URL，可选 metrics.json（含 Lighthouse 图片审计数据）
输出：图片性能审计结果 JSON
"""

import sys
import json
import argparse
import re
from html.parser import HTMLParser
from collections import defaultdict
from urllib.parse import urljoin


class ImageParser(HTMLParser):
    def __init__(self, base_url=""):
        super().__init__()
        self.base_url = base_url
        self.images = []
        self.pictures = []
        self.css_backgrounds = []
        self.total_images = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "img":
            self.total_images += 1
            self.images.append({
                "src": attrs_dict.get("src", ""),
                "srcset": attrs_dict.get("srcset", ""),
                "sizes": attrs_dict.get("sizes", ""),
                "alt": attrs_dict.get("alt", ""),
                "loading": attrs_dict.get("loading", "auto"),
                "fetchpriority": attrs_dict.get("fetchpriority", "auto"),
                "width": attrs_dict.get("width", ""),
                "height": attrs_dict.get("height", ""),
                "decoding": attrs_dict.get("decoding", "auto"),
            })

        elif tag == "source":
            self.pictures.append({
                "srcset": attrs_dict.get("srcset", ""),
                "type": attrs_dict.get("type", ""),
                "media": attrs_dict.get("media", ""),
            })


def fetch_html(url: str) -> str:
    import urllib.request
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; WebPerfAudit/1.0)",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


def load_lighthouse_data(path: str) -> dict:
    """加载 Lighthouse JSON 报告中的图片相关审计"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_image_extension(src: str) -> str:
    """获取图片格式"""
    src = src.split("?")[0].lower()
    if src.endswith(".webp"):
        return "webp"
    if src.endswith(".avif"):
        return "avif"
    if src.endswith(".jpg") or src.endswith(".jpeg"):
        return "jpeg"
    if src.endswith(".png"):
        return "png"
    if src.endswith(".gif"):
        return "gif"
    if src.endswith(".svg"):
        return "svg"
    return "unknown"


def analyze_images(parser: ImageParser, lh_data: dict = None) -> dict:
    """执行图片审计分析"""
    issues = []
    warnings = []
    summary = {
        "totalImages": len(parser.images),
        "modernFormatCount": 0,
        "responsiveCount": 0,
        "lazyLoadedCount": 0,
        "withDimensionsCount": 0,
        "withFetchPriorityCount": 0,
    }

    # 候选 LCP 图片：前 3 张图片（简化判断，一般是第一张大图）
    lcp_candidates = parser.images[:3]

    for idx, img in enumerate(parser.images):
        src = img.get("src", "")
        ext = get_image_extension(src)

        # 1. 格式检查
        if ext in ("webp", "avif"):
            summary["modernFormatCount"] += 1
        elif ext in ("jpeg", "png") and src:
            issues.append({
                "severity": "warning",
                "type": "legacy-format",
                "resource": src,
                "format": ext,
                "description": f"Image uses {ext.upper()} — switching to WebP/AVIF could reduce size by 30-50%",
                "fix": "Convert to WebP or AVIF, and use <picture> for format fallback",
            })

        # 2. 响应式检查
        if img.get("srcset"):
            summary["responsiveCount"] += 1
        elif ext not in ("svg", "unknown") and src:
            warnings.append({
                "type": "missing-srcset",
                "resource": src,
                "description": "No srcset — mobile users download same resolution as desktop",
                "fix": "Add srcset with multiple widths: srcset='img-400w.webp 400w, img-800w.webp 800w'",
            })

        # 3. 懒加载检查
        if img.get("loading") == "lazy":
            summary["lazyLoadedCount"] += 1

        # 4. 尺寸属性检查
        if img.get("width") and img.get("height"):
            summary["withDimensionsCount"] += 1
        elif src and ext != "svg":
            issues.append({
                "severity": "warning",
                "type": "missing-dimensions",
                "resource": src,
                "description": "Missing width/height attributes — may cause Cumulative Layout Shift (CLS)",
                "fix": 'Add explicit width="X" height="Y" attributes matching the image\'s aspect ratio',
            })

        # 5. fetchpriority 检查
        if img.get("fetchpriority") == "high":
            summary["withFetchPriorityCount"] += 1

    # --- LCP 图片专项检查 ---
    lcp_issues = []
    for lcp_img in lcp_candidates:
        src = lcp_img.get("src", "")
        if not src:
            continue

        problems = []
        if lcp_img.get("loading") == "lazy":
            problems.append("LCP candidate is lazy-loaded — this delays LCP significantly")
        if lcp_img.get("fetchpriority") != "high":
            problems.append("LCP candidate should have fetchpriority='high'")
        if not lcp_img.get("width") or not lcp_img.get("height"):
            problems.append("LCP candidate missing explicit dimensions")

        if problems:
            lcp_issues.append({
                "resource": src,
                "problems": problems,
                "fix": (
                    '<img src="..." fetchpriority="high" width="W" height="H" '
                    'loading="eager">\n'
                    '<!-- Preload the LCP image for even better results: -->\n'
                    f'<link rel="preload" as="image" href="{src.split("/")[-1]}" fetchpriority="high">'
                ),
            })

    # --- Lighthouse 审计项补充 ---
    lighthouse_findings = []
    if lh_data:
        audits = lh_data.get("audits", {})

        for audit_id in ["modern-image-formats", "uses-responsive-images",
                         "offscreen-images", "uses-optimized-images"]:
            audit = audits.get(audit_id, {})
            if audit.get("score") is not None and audit["score"] < 0.9:
                lighthouse_findings.append({
                    "id": audit_id,
                    "title": audit.get("title", ""),
                    "score": audit["score"],
                    "displayValue": audit.get("displayValue", ""),
                    "savings": audit.get("details", {}).get("overallSavingsBytes", 0) if audit.get("details") else 0,
                })

    return {
        "summary": summary,
        "issues": issues,
        "warnings": warnings,
        "lcpCandidates": lcp_issues,
        "lighthouseFindings": lighthouse_findings,
        "score": _calculate_score(summary, len(issues), len(lcp_issues)),
    }


def _calculate_score(summary: dict, issue_count: int, lcp_issue_count: int) -> dict:
    """计算图片性能分数（0-100）"""
    score = 100
    total = summary["totalImages"]

    if total == 0:
        return {"score": 100, "grade": "A"}

    # 扣分规则
    modern_ratio = summary["modernFormatCount"] / total
    if modern_ratio < 0.7:
        score -= int((0.7 - modern_ratio) * 40)

    responsive_ratio = summary["responsiveCount"] / total
    if responsive_ratio < 0.5:
        score -= int((0.5 - responsive_ratio) * 30)

    dims_ratio = summary["withDimensionsCount"] / total
    if dims_ratio < 0.8:
        score -= int((0.8 - dims_ratio) * 30)

    score -= issue_count * 3
    score -= lcp_issue_count * 10

    score = max(0, min(100, score))

    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    return {"score": score, "grade": grade}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Audit image performance on a web page")
    parser.add_argument("target", help="URL or path to local HTML file")
    parser.add_argument("--lighthouse", "-l", default=None,
                        help="Path to Lighthouse JSON report for supplementary image audit data")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    # 获取 HTML
    if args.target.startswith(("http://", "https://")):
        html = fetch_html(args.target)
        base_url = args.target
    else:
        with open(args.target, "r", encoding="utf-8") as f:
            html = f.read()
        base_url = ""

    # 解析
    img_parser = ImageParser(base_url)
    img_parser.feed(html)

    # 加载 Lighthouse 数据
    lh_data = None
    if args.lighthouse:
        lh_data = load_lighthouse_data(args.lighthouse)

    # 分析
    result = analyze_images(img_parser, lh_data)
    result["url"] = args.target

    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"[audit_images] Saved to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    s = result["summary"]
    sc = result["score"]
    print(f"[audit_images] {s['totalImages']} images | "
          f"Modern format: {s['modernFormatCount']} | "
          f"Responsive: {s['responsiveCount']} | "
          f"Lazy: {s['lazyLoadedCount']} | "
          f"Issues: {len(result['issues'])} | "
          f"Score: {sc['score']} ({sc['grade']})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
