<h1 align="center">web-perf-audit</h1>

<p align="center">
  <a href="README.md">English</a>&nbsp;·&nbsp;
  <a href="README_zh-CN.md">简体中文</a>&nbsp;·&nbsp;
  <a href="README_zh-TW.md">繁體中文</a>&nbsp;·&nbsp;
  <a href="README_ja.md">日本語</a>&nbsp;·&nbsp;
  <a href="README_ko.md">한국어</a>&nbsp;·&nbsp;
  <a href="README_es.md">Español</a>&nbsp;·&nbsp;
  📖 <b>Türkçe</b>&nbsp;·&nbsp;
  <a href="README_ru.md">Русский</a>
</p>

<p align="center">
  <strong>Sadece puan değil — doğrudan uygulanabilir optimizasyon çözümleri.</strong><br>
  Multi-Agent Web Performance Audit Pipeline — SCAN → ANALYZE → SCORE → REPORT.<br>
  Not another Lighthouse wrapper. A complete audit-to-fix workflow with CWV impact estimates.<br>
  Works with <strong>Claude Code, Cursor, VSCode Copilot,</strong> and any CI pipeline.
</p>

<p align="center">
  <img src="docs/pipeline.png" alt="web-perf-audit pipeline: SCAN → ANALYZE → SCORE → REPORT" width="800">
</p>



<p align="center">
  <a href="https://github.com/EVEDensity/web-perf-audit/stargazers">
    <img src="https://img.shields.io/github/stars/EVEDensity/web-perf-audit?style=for-the-badge&logo=github&labelColor=1e293b&color=f5c842" alt="Stars">
  </a>
  <a href="https://github.com/EVEDensity/web-perf-audit/blob/main/LICENSE">
    <img src="https://img.shields.io/badge/LICENSE-MIT-3b82f6?style=for-the-badge&logo=open-source-initiative&logoColor=white&labelColor=1e293b" alt="License">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/PYTHON-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white&labelColor=1e293b" alt="Python">
  </a>
  <a href="https://nodejs.org/">
    <img src="https://img.shields.io/badge/NODE.JS-18+-339933?style=for-the-badge&logo=nodedotjs&logoColor=white&labelColor=1e293b" alt="Node.js">
  </a>
  <a href="https://claude.ai/code">
    <img src="https://img.shields.io/badge/CLAUDE_CODE-skill-d97706?style=for-the-badge&logo=anthropic&logoColor=white&labelColor=1e293b" alt="Claude Code">
  </a>
  <br>
  <a href="https://github.com/EVEDensity/web-perf-audit/actions">
    <img src="https://img.shields.io/badge/BUILD-passing-22c55e?style=for-the-badge&logo=githubactions&logoColor=white&labelColor=1e293b" alt="Build">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/IDE-Cursor_|_Copilot_|_VSCode-8b5cf6?style=for-the-badge&logo=visualstudiocode&logoColor=white&labelColor=1e293b" alt="IDE">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/STANDARD-web.dev-4285F4?style=for-the-badge&logo=googlechrome&logoColor=white&labelColor=1e293b" alt="web.dev">
  </a>
  <a href="#">
    <img src="https://img.shields.io/badge/PLATFORM-win_|_mac_|_linux-6b7280?style=for-the-badge&logo=linux&logoColor=white&labelColor=1e293b" alt="Platform">
  </a>
</p>



---

## Neden web-perf-audit

Lighthouse çalıştırdınız. LCP 4.2s, skor 62. Ekrana bakıyorsunuz. Şimdi ne olacak?

Piyasadaki araçlar size "neyin yanlış olduğunu" söyler. Hiçbiri "hangi satırı, nasıl değiştireceğinizi ve bunun neden işe yarayacağını" söylemez. web-perf-audit bu boşluğu doldurur——

- **SCAN**: Lighthouse + Puppeteer ile ham CWV verileri toplama
- **ANALYZE**: 5 ajan paralel analiz (kritik yol, kaynak ipuçları, görseller, fontlar, JS fazlalığı)
- **SCORE**: CWV etkisine göre ağırlıklı puanlama, P0/P1/P2 önceliklendirme
- **REPORT**: Kopyalanabilir düzeltme kodları içeren rapor, her öneri web.dev prensiplerine bağlantılı

> *"Hedef Lighthouse 100 puanı değil — gerçek kullanıcılar için hızlı yüklenen ve anında yanıt veren bir sayfa."*

---

## ✨ Temel Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🎯 **web.dev standartlarına uygun** | Tüm kurallar [web.dev/learn/performance](https://web.dev/learn/performance) temelli. LCP ≤2.5s, INP ≤200ms, CLS ≤0.1, p75 yüzdebirliği. |
| 🤖 **Çoklu ajan paralel denetim** | 5 özel ajan: proje tarayıcı → kaynak analizci → metrik puanlayıcı → değişiklik tahminci → çözüm üretici. Paralel çalışır. |
| 🔧 **Deterministik + ölçüm hibrit** | Statik kontroller (`defer` eksik, `font-display` hatalı, `srcset` yok) her seferinde aynı sonuç. Çalışma zamanı metrikleri (LCP, TBT) Lighthouse ile gerçek tarayıcı ölçümü. |
| 📊 **Çevrimdışı dashboard** | Chart.js etkileşimli panel. Puan halkası, CWV kartları, kategori çubuk grafiği, öncelikli sorun listesi. Denetim sonrası çevrimdışı çalışır. |
| 🔁 **Git farkında artımlı denetim** | SHA256 parmak izi önbelleği. Sayfa değişmediyse tüm hat atlanır. `perf-diff` dallar arası performans gerilemesini yakalar. |
| 🧩 **Çapraz platform & çoklu IDE** | macOS / Linux / Windows desteği. Claude Code yerel skill, Cursor kuralları, VSCode Copilot talimatları. GitHub Actions tek satır entegrasyon. |

---

## 🏗 Mimari

### Çoklu ajan denetim hattı

```
Kullanıcı /perf analyze <URL> çalıştırır
         │
         ├─ Aşama 1: SCAN
         │   ├─ Proje Tarayıcı Ajan (framework tespiti, .webperfignore filtre)
         │   └─ Lighthouse + Puppeteer (LCP/CLS/INP/TBT/FCP ham veri)
         │
         ├─ Aşama 2: ANALYZE (5 ajan paralel)
         │   ├─ Kritik Yol Ajanı (render engelleme, istek zinciri derinliği, DOM boyutu)
         │   ├─ Kaynak İpuçları Ajanı (preload/prefetch/preconnect kalitesi)
         │   ├─ Görsel Denetim Ajanı (format/sizes/lazy loading/LCP adayı)
         │   ├─ Font Denetim Ajanı (font-display/woff2/alt kümeleme/preload)
         │   └─ JS Denetim Ajanı (Coverage verisi, Long Task, üçüncü taraf)
         │
         ├─ Aşama 3: SCORE
         │   └─ Metrik Puanlayıcı Ajan (CWV etkisi × şiddet çarpanı → P0/P1/P2)
         │
         └─ Aşama 4: REPORT
             └─ Optimizasyon Planı Ajanı (düzeltme şablonları, before/after kod)
                    ↓
             audit-report.json / report.md / dashboard.html
```

---

## 🚀 Hızlı Başlangıç

```bash
# 1. Depoyu klonla
git clone https://github.com/EVEDensity/web-perf-audit.git && cd web-perf-audit

# 2. Bağımlılıkları yükle
npm install -g lighthouse && npm install

# 3. Denetimi çalıştır
python scripts/fetch_metrics.py "https://example.com" --output-dir .web-perf
# ... (5 analizci paralel) ...
python scripts/score_and_report.py "https://example.com" --output-dir .web-perf --format all

# 4. Dashboard'u aç
open .web-perf/dashboard.html   # macOS
start .web-perf/dashboard.html  # Windows
```

### Claude Code tek tıkla kurulum

```
/plugin install web-perf-audit@EVEDensity/web-perf-audit
/perf analyze https://example.com
```

---

## 📦 Kurulum

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.sh | bash
```

### Windows PowerShell

```powershell
iwr -Uri https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.ps1 -OutFile install.ps1; ./install.ps1
```

### Ön Gereksinimler

| Bağımlılık | Sürüm | Kullanım |
|------------|-------|----------|
| Python | ≥ 3.8 | Tüm analiz + puanlama betikleri |
| Node.js | ≥ 18 | Lighthouse CLI + Puppeteer |
| Lighthouse | latest | CWV metrik toplama |
| Puppeteer | ^22.0.0 | JS Coverage + Long Task API |

---

## 📖 CLI Komut Referansı

| Komut | Açıklama | Örnek |
|-------|----------|-------|
| `/perf analyze` | Tam denetim | `python scripts/fetch_metrics.py <URL> --output-dir .web-perf` |
| `/perf dashboard` | Dashboard'u aç | `open .web-perf/dashboard.html` |
| `/perf diff` | Git değişiklik performans karşılaştırması | `python scripts/diff_report.py before.json after.json` |
| `/perf resource` | Statik kaynak toplu denetimi | `python scripts/audit_images.py <URL> -o images.json` |
| `/perf explain` | Tek boyutlu derin analiz | `python scripts/analyze_critical_path.py metrics.json` |
| `/perf chat` | Sohbet tabanlı performans danışmanlığı | Claude Code yerel diyalog |

---

## 💼 Kullanım Örnekleri

### Yerel proje denetimi

```bash
npm run dev &
python scripts/fetch_metrics.py "http://localhost:5173" --output-dir .web-perf
python scripts/score_and_report.py "http://localhost:5173" --output-dir .web-perf --format all
```

### CI performans kapısı

```yaml
- name: Performance Gate
  run: |
    python scripts/score_and_report.py "$STAGING_URL" --output-dir .web-perf --format json
    SCORE=$(python -c "import json; print(json.load(open('.web-perf/audit-report.json'))['overallScore']['overallScore'])")
    if [ "$SCORE" -lt 70 ]; then exit 1; fi
```

---

## ❓ Sık Sorulan Sorular

<details>
<summary><strong>Lighthouse'u doğrudan çalıştırmaktan farkı ne?</strong></summary>

Lighthouse puan ve denetim listesi verir. Biz ek olarak 5 boyutlu derin analiz (İpuçları kalite puanı, @font-face ayrıştırma, JS Coverage gerçek ölçümü, üçüncü taraf atıfı, DOM derinliği) yapar, CWV etkisine göre önceliklendirir, kopyalanabilir düzeltme kodu üretir, artımlı fark karşılaştırması sunar ve her öneri web.dev prensip belgelerine bağlantılıdır.
</details>

<details>
<summary><strong>Denetim ne kadar sürer?</strong></summary>

Tipik sayfa için 30-90 saniye. Lighthouse 15-40s (sayfa karmaşıklığına bağlı), 5 paralel analizci 10-30s, puanlama < 1s.
</details>

<details>
<summary><strong>SPA'leri destekliyor mu?</strong></summary>

Evet. Puppeteer, Coverage verisi toplamadan önce `networkidle2`'yi bekler, böylece dinamik yüklenen chunk'lar yakalanır. SPA'ler için `--strategy desktop` kullanın.
</details>

---

## 📄 Lisans

MIT © 2026 [EVEDensity](https://github.com/EVEDensity)

<p align="center">
  <a href="https://web.dev/learn/performance">web.dev/learn/performance</a> — Google Chrome resmi Web Performans kursu temelli.<br>
  Hat mimarisi <a href="https://github.com/Egonex-AI/Understand-Anything">Understand-Anything</a>'den esinlenmiştir.<br>
  <a href="https://github.com/EVEDensity/AgentHub">AgentHub</a> ekosisteminin bir parçası.
</p>

---

<p align="center">
  <sub>
    <a href="README.md">English</a> ·
    <a href="README_zh-CN.md">简体中文</a> ·
    <a href="README_zh-TW.md">繁體中文</a> ·
    <a href="README_ja.md">日本語</a> ·
    <a href="README_ko.md">한국어</a> ·
    <a href="README_es.md">Español</a> ·
    📖 Türkçe ·
    <a href="README_ru.md">Русский</a>
  </sub>
</p>
