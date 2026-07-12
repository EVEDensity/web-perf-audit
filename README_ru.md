<h1 align="center">web-perf-audit</h1>

<p align="center">
  <a href="README.md">English</a>&nbsp;·&nbsp;
  <a href="README_zh-CN.md">简体中文</a>&nbsp;·&nbsp;
  <a href="README_zh-TW.md">繁體中文</a>&nbsp;·&nbsp;
  <a href="README_ja.md">日本語</a>&nbsp;·&nbsp;
  <a href="README_ko.md">한국어</a>&nbsp;·&nbsp;
  <a href="README_es.md">Español</a>&nbsp;·&nbsp;
  <a href="README_tr.md">Türkçe</a>&nbsp;·&nbsp;
  📖 <b>Русский</b>
</p>

<p align="center">
  <strong>Не просто оценка — готовые к внедрению решения по оптимизации.</strong><br>
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

## Зачем нужен web-perf-audit

Вы запустили Lighthouse. LCP 4.2s, оценка 62. Смотрите на экран. Что дальше?

Все инструменты говорят **что не так**. Ни один не говорит **что именно изменить, строку за строкой, и почему это сработает**. web-perf-audit заполняет этот пробел——

- **SCAN**: Lighthouse + Puppeteer для сбора сырых данных CWV
- **ANALYZE**: 5 агентов параллельно (критический путь, подсказки, изображения, шрифты, избыточный JS)
- **SCORE**: Взвешенная оценка по влиянию на CWV, приоритет P0/P1/P2
- **REPORT**: Отчёт с готовыми исправлениями, каждое связано с принципом web.dev

> *"Цель не 100/100 в Lighthouse — а страница, которая быстро загружается и мгновенно отвечает реальным пользователям."*

---

## ✨ Ключевые возможности

| Возможность | Описание |
|-------------|----------|
| 🎯 **Стандарты web.dev** | Все правила на основе [web.dev/learn/performance](https://web.dev/learn/performance). LCP ≤2.5s, INP ≤200ms, CLS ≤0.1, 75-й перцентиль. |
| 🤖 **Мульти-агентный аудит** | 5 специализированных агентов: сканер проекта → анализатор ресурсов → оценщик метрик → предиктор изменений → генератор решений. |
| 🔧 **Гибрид: детерминизм + измерения** | Статический анализ (`defer`, `font-display`, `srcset`) всегда даёт одинаковый результат. Метрики (LCP, TBT) — через реальные замеры в браузере Lighthouse. |
| 📊 **Офлайн-дашборд** | Интерактивная панель Chart.js. Кольцо оценки, карточки CWV, столбчатая диаграмма, список проблем по приоритету. Работает без интернета. |
| 🔁 **Инкрементальный аудит с Git** | Кэш SHA256-отпечатков. Нет изменений — пропуск пайплайна. `perf-diff` сравнивает аудиты между ветками. |
| 🧩 **Кроссплатформенность и мульти-IDE** | macOS / Linux / Windows. Нативный навык Claude Code, правила Cursor, инструкции VSCode Copilot. CI в одну строку. |

---

## 🏗 Архитектура

### Мульти-агентный конвейер аудита

```
Пользователь запускает /perf analyze <URL>
         │
         ├─ Этап 1: SCAN
         │   ├─ Агент-сканер проекта (определение фреймворка, .webperfignore)
         │   └─ Lighthouse + Puppeteer (LCP/CLS/INP/TBT/FCP)
         │
         ├─ Этап 2: ANALYZE (5 агентов параллельно)
         │   ├─ Агент критического пути (блокировка рендеринга, цепочки запросов, DOM)
         │   ├─ Агент подсказок (качество preload/prefetch/preconnect)
         │   ├─ Агент изображений (форматы/sizes/lazy loading/LCP)
         │   ├─ Агент шрифтов (font-display/woff2/сабсеттинг/preload)
         │   └─ Агент JS (Coverage, Long Tasks, сторонние скрипты)
         │
         ├─ Этап 3: SCORE
         │   └─ Агент-оценщик (влияние на CWV × серьёзность → P0/P1/P2)
         │
         └─ Этап 4: REPORT
             └─ Агент-планировщик (шаблоны исправлений, код до/после)
                    ↓
             audit-report.json / report.md / dashboard.html
```

---

## 🚀 Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/EVEDensity/web-perf-audit.git && cd web-perf-audit

# 2. Установить зависимости
npm install -g lighthouse && npm install

# 3. Запустить аудит
python scripts/fetch_metrics.py "https://example.com" --output-dir .web-perf
# ... (5 анализаторов параллельно) ...
python scripts/score_and_report.py "https://example.com" --output-dir .web-perf --format all

# 4. Открыть дашборд
open .web-perf/dashboard.html   # macOS
start .web-perf/dashboard.html  # Windows
```

### Claude Code (в один клик)

```
/plugin install web-perf-audit@EVEDensity/web-perf-audit
/perf analyze https://example.com
```

---

## 📦 Установка

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.sh | bash
```

### Windows PowerShell

```powershell
iwr -Uri https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.ps1 -OutFile install.ps1; ./install.ps1
```

### Требования

| Зависимость | Версия | Назначение |
|-------------|--------|------------|
| Python | ≥ 3.8 | Скрипты анализа и оценки |
| Node.js | ≥ 18 | Lighthouse CLI + Puppeteer |
| Lighthouse | latest | Сбор метрик CWV |
| Puppeteer | ^22.0.0 | JS Coverage + Long Task API |

---

## 📖 Справочник команд CLI

| Команда | Описание | Пример |
|---------|----------|--------|
| `/perf analyze` | Полный аудит | `python scripts/fetch_metrics.py <URL> --output-dir .web-perf` |
| `/perf dashboard` | Открыть дашборд | `open .web-perf/dashboard.html` |
| `/perf diff` | Сравнение производительности между ветками | `python scripts/diff_report.py before.json after.json` |
| `/perf resource` | Массовый аудит статических ресурсов | `python scripts/audit_images.py <URL> -o images.json` |
| `/perf explain` | Глубокий анализ одного измерения | `python scripts/analyze_critical_path.py metrics.json` |
| `/perf chat` | Консультация в диалоговом режиме | Встроенный диалог Claude Code |

---

## 💼 Примеры использования

### Локальный проект

```bash
npm run dev &
python scripts/fetch_metrics.py "http://localhost:5173" --output-dir .web-perf
python scripts/score_and_report.py "http://localhost:5173" --output-dir .web-perf --format all
```

### Шлюз производительности в CI

```yaml
- name: Performance Gate
  run: |
    python scripts/score_and_report.py "$STAGING_URL" --output-dir .web-perf --format json
    SCORE=$(python -c "import json; print(json.load(open('.web-perf/audit-report.json'))['overallScore']['overallScore'])")
    if [ "$SCORE" -lt 70 ]; then exit 1; fi
```

---

## ❓ Часто задаваемые вопросы

<details>
<summary><strong>Чем отличается от прямого запуска Lighthouse?</strong></summary>

Lighthouse даёт оценку и список аудитов. Мы дополнительно проводим 5-мерный глубокий анализ (качество подсказок, разбор @font-face, реальный JS Coverage, атрибуция сторонних скриптов, глубина DOM), приоритизируем по влиянию на CWV, генерируем готовый код исправлений, поддерживаем инкрементальный diff, и каждое предложение ссылается на документацию принципов web.dev.
</details>

<details>
<summary><strong>Сколько времени занимает аудит?</strong></summary>

30-90 секунд для типичной страницы. Lighthouse 15-40с, 5 параллельных анализаторов 10-30с, оценка < 1с.
</details>

<details>
<summary><strong>Поддерживаются ли SPA?</strong></summary>

Да. Puppeteer ожидает `networkidle2` перед сбором данных Coverage, поэтому динамически загружаемые чанки захватываются. Для SPA используйте `--strategy desktop`.
</details>

---

## 📄 Лицензия

MIT © 2026 [EVEDensity](https://github.com/EVEDensity)

<p align="center">
  На основе <a href="https://web.dev/learn/performance">web.dev/learn/performance</a> — официального курса Google Chrome по веб-производительности.<br>
  Архитектура конвейера вдохновлена <a href="https://github.com/Egonex-AI/Understand-Anything">Understand-Anything</a>.<br>
  Часть экосистемы <a href="https://github.com/EVEDensity/AgentHub">AgentHub</a>.
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
    <a href="README_tr.md">Türkçe</a> ·
    📖 Русский
  </sub>
</p>
