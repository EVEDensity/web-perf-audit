#!/usr/bin/env node
/**
 * audit_js_bundles.js — JavaScript Bundle 性能审计
 *
 * 使用 Puppeteer 采集：
 *   1. Coverage 数据（未使用的 JS/CSS 字节数）
 *   2. 长任务（Long Task > 50ms）
 *   3. Bundle 体积和数量
 *   4. 第三方脚本影响
 *
 * 前置依赖：npm install puppeteer
 *
 * 输出：JSON 到 stdout
 */

const puppeteer = require('puppeteer');

// ---------------------------------------------------------------------------
// 配置
// ---------------------------------------------------------------------------
const CONFIG = {
  viewport: { width: 1366, height: 768 },
  userAgent: 'Mozilla/5.0 (compatible; WebPerfAudit/1.0)',
  timeout: 30000,
  // 排除不应审计的域名模式
  ignorePatterns: [
    'google-analytics.com',
    'googletagmanager.com',
    'facebook.net',
    'doubleclick.net',
    'hotjar.com',
  ],
};

// ---------------------------------------------------------------------------
// 辅助函数
// ---------------------------------------------------------------------------
function shouldIgnore(url, patterns) {
  return patterns.some((p) => url.includes(p));
}

function classifyResourceType(url) {
  if (url.endsWith('.js') || url.includes('/js/')) return 'javascript';
  if (url.endsWith('.css') || url.includes('/css/')) return 'stylesheet';
  if (url.endsWith('.woff2') || url.endsWith('.woff') || url.endsWith('.ttf')) return 'font';
  if (url.endsWith('.json')) return 'fetch';
  return 'other';
}

// ---------------------------------------------------------------------------
// 采集 Coverage
// ---------------------------------------------------------------------------
async function collectCoverage(page) {
  await page.coverage.startJSCoverage({ resetOnNavigation: false });
  await page.coverage.startCSSCoverage({ resetOnNavigation: false });

  // 等一等让页面充分执行
  await page.evaluate(() => new Promise((r) => setTimeout(r, 3000)));

  const [jsCoverage, cssCoverage] = await Promise.all([
    page.coverage.stopJSCoverage(),
    page.coverage.stopCSSCoverage(),
  ]);

  const results = [];

  for (const entry of [...jsCoverage, ...cssCoverage]) {
    const type = entry.url.endsWith('.css') ? 'css' : 'js';
    let usedBytes = 0;

    for (const range of entry.ranges) {
      usedBytes += range.end - range.start;
    }

    const totalBytes = entry.text ? entry.text.length : 0;
    const unusedBytes = totalBytes - usedBytes;
    const usagePercent = totalBytes > 0 ? ((usedBytes / totalBytes) * 100).toFixed(1) : '100.0';

    results.push({
      url: entry.url,
      type,
      totalBytes,
      usedBytes,
      unusedBytes,
      usagePercent: parseFloat(usagePercent),
      wastePercent: totalBytes > 0 ? parseFloat(((unusedBytes / totalBytes) * 100).toFixed(1)) : 0,
    });
  }

  // 按浪费量排序
  results.sort((a, b) => b.unusedBytes - a.unusedBytes);

  return results;
}

// ---------------------------------------------------------------------------
// 采集长任务
// ---------------------------------------------------------------------------
async function collectLongTasks(page) {
  const longTasks = await page.evaluate(() => {
    return new Promise((resolve) => {
      const tasks = [];
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          tasks.push({
            name: entry.name,
            duration: entry.duration,
            startTime: entry.startTime,
            attribution: entry.attribution ? entry.attribution.map((a) => ({
              containerType: a.containerType,
              containerName: a.containerName,
              containerSrc: a.containerSrc,
              containerId: a.containerId,
            })) : [],
          });
        }
      });
      observer.observe({ type: 'longtask', buffered: true });

      // 等 5 秒再收集
      setTimeout(() => {
        observer.disconnect();
        resolve(tasks);
      }, 5000);
    });
  });

  return longTasks;
}

// ---------------------------------------------------------------------------
// 采集第三方脚本
// ---------------------------------------------------------------------------
async function collectThirdPartyInfo(page, coverageData, pageDomain) {
  const requestStats = await page.evaluate(() => {
    const entries = performance.getEntriesByType('resource');
    const stats = {};

    for (const entry of entries) {
      const url = new URL(entry.name);
      const domain = url.hostname;
      const type = entry.initiatorType || 'other';

      if (!stats[domain]) {
        stats[domain] = {
          totalTransferSize: 0,
          requestCount: 0,
          types: {},
        };
      }

      stats[domain].totalTransferSize += entry.transferSize || 0;
      stats[domain].requestCount += 1;
      stats[domain].types[type] = (stats[domain].types[type] || 0) + 1;
    }

    return stats;
  });

  // 从 coverage 数据中计算每个域名的 JS 体积
  const domainBreakdown = {};
  for (const entry of coverageData) {
    try {
      const domain = new URL(entry.url).hostname;
      if (!domainBreakdown[domain]) {
        domainBreakdown[domain] = { jsBytes: 0, jsUnused: 0, cssBytes: 0, cssUnused: 0, urls: [] };
      }
      if (entry.type === 'js') {
        domainBreakdown[domain].jsBytes += entry.totalBytes;
        domainBreakdown[domain].jsUnused += entry.unusedBytes;
      } else {
        domainBreakdown[domain].cssBytes += entry.totalBytes;
        domainBreakdown[domain].cssUnused += entry.unusedBytes;
      }
      domainBreakdown[domain].urls.push(entry.url);
    } catch (_) {}
  }

  return { requestStats, domainBreakdown };
}

// ---------------------------------------------------------------------------
// 主分析函数
// ---------------------------------------------------------------------------
async function auditJSBundles(url, options = {}) {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const page = await browser.newPage();
  await page.setViewport(CONFIG.viewport);
  await page.setUserAgent(CONFIG.userAgent);

  console.error(`[audit_js_bundles] Navigating to ${url}...`);

  try {
    await page.goto(url, {
      waitUntil: 'networkidle2',
      timeout: CONFIG.timeout,
    });
  } catch (err) {
    console.error(`[audit_js_bundles] Navigation warning: ${err.message}`);
    // 即使超时也继续分析
  }

  // 等待页面充分加载
  await page.evaluate(() => new Promise((r) => setTimeout(r, 2000)));

  const pageUrl = page.url();
  const pageDomain = new URL(pageUrl).hostname;

  // 采集 Coverage
  console.error('[audit_js_bundles] Collecting coverage data...');
  const coverageData = await collectCoverage(page);

  // 采集长任务
  console.error('[audit_js_bundles] Collecting long task data...');
  const longTasks = await collectLongTasks(page);

  // 采集第三方脚本
  console.error('[audit_js_bundles] Analyzing third-party scripts...');
  const thirdPartyData = await collectThirdPartyInfo(page, coverageData, pageDomain);

  await browser.close();

  // --- 分析结果 ---
  const issues = [];
  const summary = {
    totalJSBytes: 0,
    totalCSSBytes: 0,
    totalUnusedJSBytes: 0,
    totalUnusedCSSBytes: 0,
    totalBundles: 0,
    longTaskCount: longTasks.length,
    totalLongTaskTime: Math.round(longTasks.reduce((sum, t) => sum + t.duration, 0)),
    thirdPartyDomainCount: Object.keys(thirdPartyData.domainBreakdown).length - 1, // exclude self
  };

  for (const entry of coverageData) {
    if (entry.type === 'js') {
      summary.totalJSBytes += entry.totalBytes;
      summary.totalUnusedJSBytes += entry.unusedBytes;
    } else {
      summary.totalCSSBytes += entry.totalBytes;
      summary.totalUnusedCSSBytes += entry.unusedBytes;
    }
    summary.totalBundles += 1;
  }

  // 问题：未使用的 JS 过多
  const wasteThreshold = 50 * 1024; // 50KB
  const topWasters = coverageData
    .filter((e) => e.type === 'js' && e.unusedBytes > wasteThreshold)
    .slice(0, 10);

  for (const entry of topWasters) {
    issues.push({
      severity: entry.wastePercent > 70 ? 'critical' : 'warning',
      type: 'unused-javascript',
      resource: entry.url,
      totalKB: (entry.totalBytes / 1024).toFixed(1),
      unusedKB: (entry.unusedBytes / 1024).toFixed(1),
      wastePercent: entry.wastePercent,
      description: `${(entry.unusedBytes / 1024).toFixed(0)}KB (${entry.wastePercent}%) of JS is unused`,
      fix: 'Code-split this bundle, use dynamic import(), or remove dead code',
      ref: 'references/js-performance.md#1-代码分割-code-splitting',
    });
  }

  // 问题：长任务过多
  if (longTasks.length > 3) {
    const topLongTasks = longTasks.sort((a, b) => b.duration - a.duration).slice(0, 5);
    issues.push({
      severity: 'critical',
      type: 'long-tasks',
      count: longTasks.length,
      totalDuration: summary.totalLongTaskTime,
      topTasks: topLongTasks.map((t) => ({
        duration: Math.round(t.duration),
        attribution: t.attribution.slice(0, 3),
      })),
      description: `${longTasks.length} long tasks detected (total ${summary.totalLongTaskTime}ms) — blocking main thread`,
      fix: 'Defer non-critical JS, use Web Workers for heavy computation, break up long tasks (>50ms)',
      ref: 'references/js-performance.md',
    });
  }

  // 问题：第三方脚本过多
  const thirdPartyDomains = Object.keys(thirdPartyData.domainBreakdown).filter(
    (d) => d !== pageDomain
  );

  for (const domain of thirdPartyDomains) {
    const info = thirdPartyData.domainBreakdown[domain];
    if (info.jsBytes > 100 * 1024) { // >100KB 第三方 JS
      issues.push({
        severity: 'warning',
        type: 'heavy-third-party',
        domain,
        jsKB: (info.jsBytes / 1024).toFixed(1),
        unusedKB: (info.jsUnused / 1024).toFixed(1),
        description: `Third-party domain "${domain}" contributes ${(info.jsBytes / 1024).toFixed(0)}KB JS`,
        fix: 'Load third-party scripts with async/defer, use facade pattern, or evaluate necessity',
      });
    }
  }

  // 估算 Bundle 优化收益
  const estimatedSavingsMs = summary.totalUnusedJSBytes / 1024 * 0.05; // ~0.05ms/KB unused JS
  const estimatedSavings = Math.round(estimatedSavingsMs);

  return {
    url,
    summary: {
      ...summary,
      totalJSFormatted: `${(summary.totalJSBytes / 1024).toFixed(0)} KB`,
      totalUnusedJSFormatted: `${(summary.totalUnusedJSBytes / 1024).toFixed(0)} KB`,
      totalUnusedCSSFormatted: `${(summary.totalUnusedCSSBytes / 1024).toFixed(0)} KB`,
      estimatedSavingsMs: estimatedSavings,
      estimatedSavingsFormatted: `${estimatedSavings}ms`,
    },
    issues,
    coverage: coverageData.slice(0, 30), // Top 30 by waste
    longTasks: longTasks.slice(0, 20),
    thirdParty: thirdPartyData,
  };
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------
(async () => {
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.error('Usage: node audit_js_bundles.js <url> [--output output.json]');
    process.exit(1);
  }

  const url = args[0];
  let outputPath = null;
  const outputIdx = args.indexOf('--output');
  if (outputIdx !== -1 && outputIdx + 1 < args.length) {
    outputPath = args[outputIdx + 1];
  }

  try {
    const result = await auditJSBundles(url);
    const json = JSON.stringify(result, null, 2);

    if (outputPath) {
      const fs = require('fs');
      fs.writeFileSync(outputPath, json);
      console.error(`[audit_js_bundles] Saved to ${outputPath}`);
    } else {
      console.log(json);
    }

    console.error(
      `[audit_js_bundles] JS: ${result.summary.totalJSFormatted} ` +
      `(${result.summary.totalUnusedJSFormatted} unused) | ` +
      `Long Tasks: ${result.summary.longTaskCount} ` +
      `(${result.summary.totalLongTaskTime}ms) | ` +
      `Issues: ${result.issues.length}`
    );
  } catch (err) {
    console.error(`[audit_js_bundles] Error: ${err.message}`);
    process.exit(1);
  }
})();
