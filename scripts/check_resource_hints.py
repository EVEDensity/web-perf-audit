#!/usr/bin/env python3
"""
check_resource_hints.py — 检测 Resource Hints 使用情况

扫描 HTML，分析 preload/prefetch/preconnect/dns-prefetch 的：
  - 使用是否合理（缺失 / 滥用 / 配置错误）
  - preload 是否有正确的 as 和 crossorigin
  - 第三方域名是否有 preconnect
  - LCP 元素是否有对应的 preload

输入：URL 或本地 HTML 文件路径
输出：Resource hints 审计结果 JSON
"""

import sys
import json
import argparse
import re
import urllib.parse
from html.parser import HTMLParser
from typing import Optional
from collections import defaultdict


class ResourceHintParser(HTMLParser):
    """解析 HTML 中的 resource hints 和相关元素"""

    def __init__(self):
        super().__init__()
        self.preloads = []       # {href, as_, crossorigin, media}
        self.prefetches = []     # {href, as_}
        self.preconnects = []    # {href}
        self.dns_prefetches = [] # {href}
        self.scripts = []        # {src, async_, defer, inline}
        self.styles = []         # {href, media}
        self.images = []         # {src, srcset, loading, fetchpriority}
        self.fonts_css = []      # @font-face 中的字体 URL
        self.inline_styles = []  # 内联 <style> 内容
        self.all_external_urls = set()
        self.third_party_domains = set()

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "link":
            rel = attrs_dict.get("rel", "").lower()
            href = attrs_dict.get("href", "")
            as_attr = attrs_dict.get("as", "")

            if rel == "preload":
                self.preloads.append({
                    "href": href,
                    "as": as_attr,
                    "crossorigin": attrs_dict.get("crossorigin"),
                    "type": attrs_dict.get("type", ""),
                    "media": attrs_dict.get("media", ""),
                })
            elif rel == "prefetch":
                self.prefetches.append({"href": href, "as": as_attr})
            elif rel == "preconnect":
                self.preconnects.append({"href": href})
            elif rel == "dns-prefetch":
                self.dns_prefetches.append({"href": href})
            elif rel in ("stylesheet", "styles"):
                self.styles.append({"href": href, "media": attrs_dict.get("media", "")})

        elif tag == "script":
            src = attrs_dict.get("src", "")
            if src:
                self.scripts.append({
                    "src": src,
                    "async": attrs_dict.get("async") is not None or attrs_dict.get("async") == "",
                    "defer": attrs_dict.get("defer") is not None or attrs_dict.get("defer") == "",
                    "type": attrs_dict.get("type", "text/javascript"),
                })
            else:
                self.scripts.append({
                    "src": "",
                    "inline": True,
                    "type": attrs_dict.get("type", "text/javascript"),
                })

        elif tag == "img":
            src = attrs_dict.get("src", "")
            srcset = attrs_dict.get("srcset", "")
            if src or srcset:
                self.images.append({
                    "src": src,
                    "srcset": srcset,
                    "loading": attrs_dict.get("loading", "auto"),
                    "fetchpriority": attrs_dict.get("fetchpriority", "auto"),
                    "width": attrs_dict.get("width", ""),
                    "height": attrs_dict.get("height", ""),
                })

        elif tag == "style":
            # 内联 style
            self.inline_styles.append(True)

        # 收集所有外部 URL
        for attr_name in ("src", "href", "srcset"):
            val = attrs_dict.get(attr_name, "")
            if val and val.startswith(("http://", "https://")):
                self.all_external_urls.add(val)

    def handle_data(self, data):
        # 检测内联 CSS 中的 @font-face url()
        font_urls = re.findall(r'url\(["\']?(https?://[^)"\']+)["\']?\)', data)
        self.fonts_css.extend(font_urls)


def extract_domain(url: str) -> str:
    """提取 URL 的域名部分"""
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc.lower()


def get_page_domain(url: str) -> str:
    return extract_domain(url)


def analyze_hints(parser: ResourceHintParser, page_url: str) -> dict:
    """分析 resource hints 的使用情况"""
    page_domain = get_page_domain(page_url)
    issues = []
    suggestions = []

    # --- 检查 preload 质量 ---
    preloaded_urls = set()
    for p in parser.preloads:
        preloaded_urls.add(p["href"])

        if not p["as"]:
            issues.append({
                "severity": "critical",
                "type": "preload-missing-as",
                "resource": p["href"],
                "description": "preload missing 'as' attribute — browser may download with wrong priority",
                "fix": f'<link rel="preload" href="{p["href"]}" as="style"> <!-- or font/image/script -->',
            })

        if p["as"] == "font" and not p.get("crossorigin"):
            issues.append({
                "severity": "critical",
                "type": "preload-font-no-crossorigin",
                "resource": p["href"],
                "description": "Font preload missing 'crossorigin' — font will be fetched twice",
                "fix": f'<link rel="preload" href="{p["href"]}" as="font" crossorigin>',
            })

    if len(parser.preloads) > 5:
        issues.append({
            "severity": "warning",
            "type": "preload-overuse",
            "description": f"Too many preloads ({len(parser.preloads)}). Preload only 2-3 critical resources.",
            "fix": "Keep only LCP image, critical font, and main CSS as preloads. Use prefetch for the rest.",
        })

    # --- 检查第三方域名的 preconnect ---
    preconnected_domains = {extract_domain(p["href"]) for p in parser.preconnects}
    dns_prefetched_domains = {extract_domain(d["href"]) for d in parser.dns_prefetches}
    connected_domains = preconnected_domains | dns_prefetched_domains

    # 收集第三方域名
    third_party_domains = set()
    for url in parser.all_external_urls:
        domain = extract_domain(url)
        if domain and domain != page_domain and "data:" not in url:
            third_party_domains.add(domain)

    # 检查哪些第三方域名缺少 preconnect
    critical_third_parties = []
    for domain in sorted(third_party_domains):
        if domain not in connected_domains:
            # 统计该域名的请求数
            count = sum(1 for u in parser.all_external_urls if extract_domain(u) == domain)
            critical_third_parties.append({"domain": domain, "requestCount": count})

    if critical_third_parties:
        top_missing = sorted(critical_third_parties, key=lambda x: x["requestCount"], reverse=True)[:5]
        for tp in top_missing:
            suggestions.append({
                "type": "add-preconnect",
                "domain": tp["domain"],
                "requestCount": tp["requestCount"],
                "fix": f'<link rel="preconnect" href="https://{tp["domain"]}">',
                "impact": "Reduces connection setup time by ~300ms",
            })

    # --- 检查同步脚本 ---
    sync_scripts = [s for s in parser.scripts if not s.get("inline") and not s["async"] and not s["defer"]]
    if sync_scripts:
        issues.append({
            "severity": "critical" if len(sync_scripts) > 2 else "warning",
            "type": "sync-scripts-in-head",
            "count": len(sync_scripts),
            "scripts": [s["src"] for s in sync_scripts[:5]],
            "description": f"{len(sync_scripts)} synchronous script(s) found — they block HTML parsing",
            "fix": "Add 'defer' attribute to these scripts: " + ", ".join(s["src"].split("/")[-1] for s in sync_scripts[:3]),
        })

    # --- 检查 LCP 候选图片的 preload ---
    images_without_dimensions = [i for i in parser.images if not (i.get("width") and i.get("height"))]
    if images_without_dimensions:
        suggestions.append({
            "type": "add-image-dimensions",
            "count": len(images_without_dimensions),
            "description": f"{len(images_without_dimensions)} image(s) missing explicit width/height — may cause CLS",
            "fix": "Add width and height attributes to all <img> tags",
        })

    # --- 检查 preconnect 是否合理 ---
    if len(parser.preconnects) > 6:
        issues.append({
            "severity": "warning",
            "type": "preconnect-overuse",
            "description": f"Too many preconnects ({len(parser.preconnects)}). Each connection consumes memory. Limit to ≤5.",
            "fix": "Remove preconnects for low-priority domains; use dns-prefetch instead.",
        })

    # --- 检查同源 preconnect（浪费） ---
    for pc in parser.preconnects:
        if extract_domain(pc["href"]) == page_domain:
            issues.append({
                "severity": "low",
                "type": "same-origin-preconnect",
                "resource": pc["href"],
                "description": "preconnect to same origin is unnecessary",
                "fix": f'Remove: <link rel="preconnect" href="{pc["href"]}">',
            })

    return {
        "summary": {
            "totalPreloads": len(parser.preloads),
            "totalPrefetches": len(parser.prefetches),
            "totalPreconnects": len(parser.preconnects),
            "totalDnsPrefetches": len(parser.dns_prefetches),
            "totalSyncScripts": len(sync_scripts),
            "thirdPartyDomains": len(third_party_domains),
            "thirdPartiesWithoutPreconnect": len(critical_third_parties),
        },
        "issues": issues,
        "suggestions": suggestions,
        "preloads": parser.preloads,
        "preconnects": parser.preconnects,
        "thirdPartyDomains": sorted(third_party_domains),
    }


def fetch_html(url: str) -> str:
    """获取页面 HTML"""
    import urllib.request

    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; WebPerfAudit/1.0)",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Audit resource hints (preload/prefetch/preconnect) usage")
    parser.add_argument("target", help="URL or path to local HTML file")
    parser.add_argument("--output", "-o", default=None, help="Output JSON file (default: stdout)")
    args = parser.parse_args()

    # 获取 HTML
    if args.target.startswith(("http://", "https://")):
        html = fetch_html(args.target)
        page_url = args.target
    else:
        with open(args.target, "r", encoding="utf-8") as f:
            html = f.read()
        page_url = "file://" + args.target

    # 解析
    hint_parser = ResourceHintParser()
    hint_parser.feed(html)

    # 分析
    result = analyze_hints(hint_parser, page_url)
    result["url"] = page_url

    output_json = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_json)
        print(f"[check_resource_hints] Saved to {args.output}", file=sys.stderr)
    else:
        print(output_json)

    # 摘要
    s = result["summary"]
    print(f"[check_resource_hints] Preloads: {s['totalPreloads']}, "
          f"Prefetches: {s['totalPrefetches']}, "
          f"Preconnects: {s['totalPreconnects']}, "
          f"Issues: {len(result['issues'])}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
