#!/usr/bin/env python3
"""
audit_fonts.py — Web 字体性能审计

检测维度：
  1. font-display 设置（swap / optional / block / auto / fallback）
  2. 关键字体是否 preload
  3. 未使用的字重
  4. 字体文件格式（woff2 优先）
  5. 字体文件体积
  6. 是否使用了系统字体栈

输入：URL 或本地 HTML + CSS 文件
输出：字体审计结果 JSON
"""

import sys
import json
import argparse
import re
from html.parser import HTMLParser
from urllib.parse import urljoin


class FontAuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.font_faces = []      # @font-face 声明
        self.font_preloads = []   # preload as="font"
        self.font_links = []      # Google Fonts link 等
        self.style_contents = []  # 内联 <style> 块内容
        self.external_css = []    # 外部 CSS 链接
        self.uses_system_font = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            href = attrs_dict.get("href", "")

            if rel == "preload" and attrs_dict.get("as") == "font":
                self.font_preloads.append({
                    "href": href,
                    "crossorigin": attrs_dict.get("crossorigin"),
                    "type": attrs_dict.get("type", ""),
                })
            elif "font" in href.lower() or "googleapis" in href:
                self.font_links.append({
                    "href": href,
                    "rel": rel,
                })

        elif tag == "style":
            self.style_contents.append({"inline": True})

    def handle_data(self, data):
        # 解析 @font-face 规则
        font_face_pattern = re.compile(
            r'@font-face\s*\{([^}]+)\}',
            re.IGNORECASE | re.DOTALL
        )
        for match in font_face_pattern.finditer(data):
            block = match.group(1)

            font_family = re.search(r'font-family\s*:\s*["\']?([^"\';\n]+)["\']?', block, re.IGNORECASE)
            src = re.search(r'src\s*:\s*url\(["\']?([^)"\']+)["\']?\)', block, re.IGNORECASE)
            font_display = re.search(r'font-display\s*:\s*(\w+)', block, re.IGNORECASE)
            font_weight = re.search(r'font-weight\s*:\s*(\d+)', block, re.IGNORECASE)

            self.font_faces.append({
                "fontFamily": font_family.group(1).strip() if font_family else "unknown",
                "src": src.group(1) if src else "",
                "fontDisplay": font_display.group(1).lower() if font_display else "auto",
                "fontWeight": int(font_weight.group(1)) if font_weight else 400,
            })

        # 检测系统字体栈
        system_font_patterns = [
            r'system-ui', r'-apple-system', r'Segoe UI',
        ]
        for pattern in system_font_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                self.uses_system_font = True
                break


def fetch_resource(url: str) -> str:
    import urllib.request
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; WebPerfAudit/1.0)",
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")


def analyze_fonts(parser: FontAuditParser) -> dict:
    """执行字体审计"""
    issues = []
    suggestions = []

    summary = {
        "totalFontFaces": len(parser.font_faces),
        "totalFontPreloads": len(parser.font_preloads),
        "swapCount": 0,
        "optionalCount": 0,
        "blockCount": 0,
        "autoCount": 0,
        "woff2Count": 0,
        "usesSystemFont": parser.uses_system_font,
    }

    # 统计 font-display
    for ff in parser.font_faces:
        fd = ff["fontDisplay"]
        if fd == "swap":
            summary["swapCount"] += 1
        elif fd == "optional":
            summary["optionalCount"] += 1
        elif fd == "block":
            summary["blockCount"] += 1
        else:
            summary["autoCount"] += 1

        if ff["src"].endswith(".woff2"):
            summary["woff2Count"] += 1

        # 检查 font-display
        if fd == "block" or fd == "auto":
            issues.append({
                "severity": "critical" if fd == "block" else "warning",
                "type": "font-display-block",
                "fontFamily": ff["fontFamily"],
                "currentDisplay": fd,
                "description": (
                    f"font-display: {fd} causes FOIT (text invisible up to 3s)"
                    if fd == "block" else
                    f"font-display is '{fd}' (browser default) — set explicitly to 'swap'"
                ),
                "fix": (
                    f"@font-face {{\n"
                    f"  font-family: '{ff['fontFamily']}';\n"
                    f"  src: url('{ff['src']}') format('woff2');\n"
                    f"  font-display: swap;\n"
                    f"}}"
                ),
            })

        # 检查格式
        if ff["src"] and not ff["src"].endswith(".woff2"):
            warnings_or = suggestions
            warnings_or.append({
                "type": "legacy-font-format",
                "fontFamily": ff["fontFamily"],
                "formatUsed": ff["src"].split(".")[-1] if "." in ff["src"] else "unknown",
                "description": "Use woff2 format — 30% smaller than woff",
                "fix": f'Convert to .woff2 and update src: url("{ff["src"].rsplit(".", 1)[0]}.woff2") format("woff2")',
            })

    # 检查 preload 是否覆盖了关键字体
    preloaded_fonts = {p["href"].split("/")[-1] for p in parser.font_preloads}
    if parser.font_faces and not parser.font_preloads:
        suggestions.append({
            "type": "no-font-preload",
            "description": "No fonts are preloaded — critical fonts should be preloaded to avoid FOIT/FOUT",
            "fix": (
                '<link rel="preload" href="/fonts/main.woff2" as="font" type="font/woff2" crossorigin>\n'
                '<!-- Preload the most important font family used in above-the-fold text -->'
            ),
        })

    # 检查字体 preload 是否有 crossorigin
    for p in parser.font_preloads:
        if not p.get("crossorigin"):
            issues.append({
                "severity": "critical",
                "type": "font-preload-no-crossorigin",
                "resource": p["href"],
                "description": "Font preload missing 'crossorigin' — causes double download",
                "fix": f'<link rel="preload" href="{p["href"]}" as="font" type="font/woff2" crossorigin>',
            })

    # 第三方字体服务检查
    third_party_fonts = [l for l in parser.font_links if
                         "fonts.googleapis.com" in l.get("href", "") or
                         "fonts.gstatic.com" in l.get("href", "")]
    if third_party_fonts:
        suggestions.append({
            "type": "third-party-fonts",
            "description": "Using third-party font services — ensure preconnect is configured",
            "fix": (
                '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            ),
        })

    # 字重优化建议
    weights_used = set(ff["fontWeight"] for ff in parser.font_faces)
    if len(weights_used) > 3:
        suggestions.append({
            "type": "too-many-weights",
            "description": f"{len(weights_used)} font weights declared ({sorted(weights_used)}) — "
                           f"each adds a download; consider limiting to 2-3 weights",
            "fix": "Remove unused @font-face declarations; use only Regular (400) and Bold (700)",
        })

    return {
        "summary": summary,
        "issues": issues,
        "suggestions": suggestions,
        "fontFaces": parser.font_faces,
        "fontPreloads": parser.font_preloads,
        "score": _calculate_score(summary, len(issues)),
    }


def _calculate_score(summary: dict, issue_count: int) -> dict:
    score = 100
    total = summary["totalFontFaces"]

    if total == 0 and summary["usesSystemFont"]:
        return {"score": 100, "grade": "A", "note": "Using system font stack — optimal"}

    if total == 0:
        return {"score": 100, "grade": "A"}

    # 扣分
    if summary["blockCount"] + summary["autoCount"] > 0:
        bad_ratio = (summary["blockCount"] + summary["autoCount"]) / total
        score -= int(bad_ratio * 40)

    if summary["woff2Count"] < total:
        non_woff2_ratio = 1 - summary["woff2Count"] / total
        score -= int(non_woff2_ratio * 20)

    score -= issue_count * 5

    score = max(0, min(100, score))
    grade = "A" if score >= 90 else "B" if score >= 75 else "C" if score >= 60 else "D" if score >= 40 else "F"
    return {"score": score, "grade": grade}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Audit web font performance")
    parser.add_argument("target", help="URL or path to local HTML file")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    if args.target.startswith(("http://", "https://")):
        html = fetch_resource(args.target)
    else:
        with open(args.target, "r", encoding="utf-8") as f:
            html = f.read()

    font_parser = FontAuditParser()
    font_parser.feed(html)

    result = analyze_fonts(font_parser)
    result["url"] = args.target

    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"[audit_fonts] Saved to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    s = result["summary"]
    sc = result["score"]
    print(f"[audit_fonts] {s['totalFontFaces']} @font-face(s) | "
          f"swap:{s['swapCount']} optional:{s['optionalCount']} block:{s['blockCount']} | "
          f"woff2:{s['woff2Count']} | "
          f"Issues: {len(result['issues'])} | "
          f"Score: {sc['score']} ({sc['grade']})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
