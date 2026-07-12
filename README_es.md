<h1 align="center">web-perf-audit</h1>

<p align="center">
  <a href="README.md">English</a>&nbsp;·&nbsp;
  <a href="README_zh-CN.md">简体中文</a>&nbsp;·&nbsp;
  <a href="README_zh-TW.md">繁體中文</a>&nbsp;·&nbsp;
  <a href="README_ja.md">日本語</a>&nbsp;·&nbsp;
  <a href="README_ko.md">한국어</a>&nbsp;·&nbsp;
  📖 <b>Español</b>&nbsp;·&nbsp;
  <a href="README_tr.md">Türkçe</a>&nbsp;·&nbsp;
  <a href="README_ru.md">Русский</a>
</p>

<p align="center">
  <strong>Soluciones que se implementan > consejos que se quedan en un dashboard.</strong><br>
  Multi-Agent Web Performance Audit Pipeline — SCAN → ANALYZE → SCORE → REPORT.<br>
  Not another Lighthouse wrapper. A complete audit-to-fix workflow with CWV impact estimates.<br>
  Works with <strong>Claude Code, Cursor, VSCode Copilot,</strong> and any CI pipeline.
</p>

<p align="center">
  <img src="docs/pipeline.png" alt="web-perf-audit pipeline: SCAN → ANALYZE → SCORE → REPORT" width="800">
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/logo-dark.svg">
    <img alt="web-perf-audit" src="docs/logo.svg" width="520">
  </picture>
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

<p align="center">
  <code>npx web-perf-audit --url https://example.com --audience dev</code>
</p>

---

## Por qué web-perf-audit

Ejecutaste Lighthouse. LCP 4.2s, puntuación 62. Miras la pantalla. ¿Y ahora qué?

Todas las herramientas te dicen **qué está mal**. Ninguna te dice **qué cambiar, línea por línea, y por qué ese cambio funcionará**. web-perf-audit llena ese vacío——

- **SCAN**: Lighthouse + Puppeteer para datos CWV sin procesar
- **ANALYZE**: 5 agentes en paralelo (ruta crítica, hints, imágenes, fuentes, JS no utilizado)
- **SCORE**: Puntuación ponderada por impacto CWV, prioridad P0/P1/P2
- **REPORT**: Informe con correcciones copiables, cada una vinculada al principio de web.dev que la explica

> *"El objetivo no es un 100/100 en Lighthouse — es una página que cargue rápido y responda al instante para usuarios reales."*

---

## ✨ Funcionalidades

| Funcionalidad | Descripción |
|---------------|-------------|
| 🎯 **Alineado con web.dev** | Todas las reglas basadas en [web.dev/learn/performance](https://web.dev/learn/performance). LCP ≤2.5s, INP ≤200ms, CLS ≤0.1, percentil 75. |
| 🤖 **Pipeline multi-agente** | 5 agentes especializados: escáner de proyecto → analizador de recursos → puntuador de métricas → predictor de cambios → generador de soluciones. |
| 🔧 **Híbrido determinista + medición** | Análisis estático (`defer`, `font-display`, `srcset`) determinista. Métricas runtime (LCP, TBT) vía medición real del navegador con Lighthouse. |
| 📊 **Dashboard offline** | Panel interactivo Chart.js. Anillo de puntuación, tarjetas CWV, gráfico de barras, lista de incidencias priorizadas. Funciona sin conexión. |
| 🔁 **Auditoría incremental con Git** | Caché de huella SHA256. Sin cambios → se salta el pipeline. `perf-diff` compara auditorías entre ramas para detectar regresiones. |
| 🧩 **Multiplataforma & multi-IDE** | macOS / Linux / Windows. Skill nativo de Claude Code, reglas Cursor, instrucciones VSCode Copilot. Integración CI en una línea. |

---

## 🏗 Arquitectura

### Pipeline de auditoría multi-agente

```
Usuario ejecuta /perf analyze <URL>
         │
         ├─ Stage 1: SCAN
         │   ├─ Agente Escáner de Proyecto (detección de framework, .webperfignore)
         │   └─ Lighthouse + Puppeteer (LCP/CLS/INP/TBT/FCP)
         │
         ├─ Stage 2: ANALYZE (5 agentes en paralelo)
         │   ├─ Agente de Ruta Crítica (bloqueo de renderizado, cadenas, DOM)
         │   ├─ Agente de Hints (calidad de preload/prefetch/preconnect)
         │   ├─ Agente de Imágenes (formatos/sizes/lazy loading/LCP)
         │   ├─ Agente de Fuentes (font-display/woff2/subsetting/preload)
         │   └─ Agente de JS (Coverage, Long Tasks, terceros)
         │
         ├─ Stage 3: SCORE
         │   └─ Agente Puntuador (impacto CWV × severidad → P0/P1/P2)
         │
         └─ Stage 4: REPORT
             └─ Agente de Soluciones (plantillas de corrección, código before/after)
                    ↓
             audit-report.json / report.md / dashboard.html
```

---

## 🚀 Inicio rápido

```bash
# 1. Clonar
git clone https://github.com/EVEDensity/web-perf-audit.git && cd web-perf-audit

# 2. Instalar dependencias
npm install -g lighthouse && npm install

# 3. Ejecutar auditoría
python scripts/fetch_metrics.py "https://example.com" --output-dir .web-perf
# ... (5 analizadores en paralelo) ...
python scripts/score_and_report.py "https://example.com" --output-dir .web-perf --format all

# 4. Abrir dashboard
open .web-perf/dashboard.html   # macOS
start .web-perf/dashboard.html  # Windows
```

### Claude Code (un clic)

```
/plugin install web-perf-audit@EVEDensity/web-perf-audit
/perf analyze https://example.com
```

---

## 📦 Instalación

### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.sh | bash
```

### Windows PowerShell

```powershell
iwr -Uri https://raw.githubusercontent.com/EVEDensity/web-perf-audit/main/install.ps1 -OutFile install.ps1; ./install.ps1
```

### Requisitos previos

| Dependencia | Versión | Uso |
|-------------|---------|-----|
| Python | ≥ 3.8 | Scripts de análisis y puntuación |
| Node.js | ≥ 18 | Lighthouse CLI + Puppeteer |
| Lighthouse | latest | Recolección de métricas CWV |
| Puppeteer | ^22.0.0 | JS Coverage + Long Task API |

---

## 📖 Referencia de comandos CLI

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `/perf analyze` | Auditoría completa | `python scripts/fetch_metrics.py <URL> --output-dir .web-perf` |
| `/perf dashboard` | Abrir panel visual | `open .web-perf/dashboard.html` |
| `/perf diff` | Comparar rendimiento entre ramas | `python scripts/diff_report.py before.json after.json` |
| `/perf resource` | Auditoría de recursos estáticos | `python scripts/audit_images.py <URL> -o images.json` |
| `/perf explain` | Análisis profundo unidimensional | `python scripts/analyze_critical_path.py metrics.json` |
| `/perf chat` | Consulta conversacional | Claude Code nativo |

---

## 💼 Casos de uso

### Proyecto local

```bash
npm run dev &
python scripts/fetch_metrics.py "http://localhost:5173" --output-dir .web-perf
python scripts/score_and_report.py "http://localhost:5173" --output-dir .web-perf --format all
```

### Gate de rendimiento en CI

```yaml
- name: Performance Gate
  run: |
    python scripts/score_and_report.py "$STAGING_URL" --output-dir .web-perf --format json
    SCORE=$(python -c "import json; print(json.load(open('.web-perf/audit-report.json'))['overallScore']['overallScore'])")
    if [ "$SCORE" -lt 70 ]; then exit 1; fi
```

---

## ❓ Preguntas frecuentes

<details>
<summary><strong>¿En qué se diferencia de ejecutar Lighthouse directamente?</strong></summary>

Lighthouse da puntuación y lista de auditorías. Nosotros añadimos 5 dimensiones de análisis profundo (calidad de hints, parseo @font-face, Coverage JS real, atribución de terceros, profundidad DOM), priorizamos por impacto CWV, generamos código corregible, soportamos diff incremental, y cada sugerencia enlaza a la documentación de principios de web.dev.
</details>

<details>
<summary><strong>¿Cuánto tarda una auditoría?</strong></summary>

30-90 segundos para una página típica. Lighthouse 15-40s, 5 analizadores en paralelo 10-30s, puntuación < 1s.
</details>

<details>
<summary><strong>¿Funciona con SPAs?</strong></summary>

Sí. Puppeteer espera `networkidle2` antes de recolectar datos de Coverage, por lo que los chunks cargados dinámicamente se capturan. Para SPAs, usa `--strategy desktop`.
</details>

---

## 📄 Licencia

MIT © 2026 [EVEDensity](https://github.com/EVEDensity)

<p align="center">
  Basado en <a href="https://web.dev/learn/performance">web.dev/learn/performance</a> — El curso oficial de rendimiento web de Google Chrome.<br>
  Arquitectura inspirada en <a href="https://github.com/Egonex-AI/Understand-Anything">Understand-Anything</a>.<br>
  Parte del ecosistema <a href="https://github.com/EVEDensity/AgentHub">AgentHub</a>.
</p>

---

<p align="center">
  <sub>
    <a href="README.md">English</a> ·
    <a href="README_zh-CN.md">简体中文</a> ·
    <a href="README_zh-TW.md">繁體中文</a> ·
    <a href="README_ja.md">日本語</a> ·
    <a href="README_ko.md">한국어</a> ·
    📖 Español ·
    <a href="README_tr.md">Türkçe</a> ·
    <a href="README_ru.md">Русский</a>
  </sub>
</p>
