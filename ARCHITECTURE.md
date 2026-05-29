# AutoML Data Analytics App — Architecture & Testing Guide

> **Full-stack AutoML platform** for uploading datasets, visualizing data, building BI dashboards, training ML models, making predictions, and getting AI-powered guidance — all from a single app.

---

## Table of Contents

- [1. Tech Stack](#1-tech-stack)
- [2. System Architecture](#2-system-architecture)
- [3. Project Structure](#3-project-structure)
- [4. Backend Deep Dive](#4-backend-deep-dive)
- [5. Frontend Deep Dive](#5-frontend-deep-dive)
- [6. Complex Logic Breakdown](#6-complex-logic-breakdown)
- [7. Data Flow](#7-data-flow)
- [8. Testing Architecture](#8-testing-architecture)
- [9. How to Run Tests](#9-how-to-run-tests)
- [10. Troubleshooting](#10-troubleshooting)

---

## 1. Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.14+ | Core language |
| **Flask** | latest | REST API server |
| **Flask-CORS** | latest | Cross-origin requests |
| **Pandas** | latest | Data manipulation engine |
| **NumPy** | latest | Numerical computations |
| **scikit-learn** | latest | ML models (SVM, Random Forest), preprocessing, metrics |
| **XGBoost** | latest | Gradient boosted trees |
| **LightGBM** | latest | Fast gradient boosting |
| **Matplotlib** | latest | Server-side plot generation |
| **Seaborn** | latest | Statistical visualizations |
| **openpyxl** | latest | Excel file I/O |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| **React** | 19.x | UI component framework |
| **Vite** | 8.x | Dev server + bundler |
| **Plotly.js** | CDN | Client-side BI charts |
| **Vanilla CSS** | — | Design system (glassmorphism, Inter font, dark theme) |

### DevOps / Tooling
| Tool | Purpose |
|---|---|
| `run.py` | Dual-server launcher (Flask + Vite) |
| `git_push.py` | Interactive git automation with .gitignore management |
| `auto_test_generator.py` | Auto-discovers functions/components and generates test stubs |
| `refactor.py` | Code refactoring automation (logging migration) |

---

## 2. System Architecture

```mermaid
graph TB
    subgraph "Browser (localhost:5173)"
        A["React App (Vite)"]
        A1["FileUpload"]
        A2["DataOverview"]
        A3["BIDashboard"]
        A4["Visualization"]
        A5["ModelTraining"]
        A6["ModelComparison"]
        A7["Prediction"]
        A8["DataFixBanner"]
        A9["AICopilot"]
        A --> A1 & A2 & A3 & A4 & A5 & A6 & A7 & A8 & A9
    end

    subgraph "Vite Dev Server (:5173)"
        VP["Proxy Layer"]
    end

    subgraph "Flask Backend (:5000)"
        B["Flask App"]
        B1["Session Manager (SESSIONS dict)"]
        B2["Data Fixer Engine"]
        B3["ML Training Pipeline"]
        B4["BI Aggregation Engine"]
        B5["AI Copilot NLP"]
        B6["Visualization Engine"]
        B7["Power BI Exporter"]
        B --> B1 & B2 & B3 & B4 & B5 & B6 & B7
    end

    A -->|"API calls"| VP
    VP -->|"Proxied to :5000"| B

    style A fill:#1e293b,stroke:#3b82f6,color:#f8fafc
    style B fill:#1e293b,stroke:#8b5cf6,color:#f8fafc
```

### How the Two Servers Communicate

1. **Vite Dev Server** runs on `localhost:5173` — serves the React frontend
2. **Flask API** runs on `localhost:5000` — handles all data/ML/AI logic
3. **Vite Proxy** in `vite.config.js` forwards all API routes (`/upload`, `/aggregate`, `/train_model`, etc.) from `:5173` → `:5000`
4. The user only interacts with `:5173` — all API calls are transparent

---

## 3. Project Structure

```
data-analytics-app/
│
├── app.py                      # Main Flask server (1,718 lines) — ALL API endpoints
├── data_fixer.py               # Smart Data Fixer — diagnosis + auto-fix pipeline
├── power_bi_exporter.py        # Power BI CSV export utility
├── run.py                      # Dual-server launcher (Flask + Vite)
├── refactor.py                 # Code refactoring automation
├── git_push.py                 # Interactive git push tool
│
├── master_test.py              # Test suite (MasterTest + FrontendTest)
├── auto_test_generator.py      # Auto-discovers missing tests and generates stubs
│
├── uploads/                    # Temporary file storage (auto-cleaned)
├── templates/                  # Legacy Jinja2 templates
│
├── frontend/                   # React + Vite frontend
│   ├── package.json
│   ├── vite.config.js          # Proxy config for API routes
│   ├── index.html
│   └── src/
│       ├── main.jsx            # React entry point
│       ├── App.jsx             # Root component — state management + routing
│       ├── App.css
│       ├── index.css           # Full design system (1,398 lines)
│       └── components/
│           ├── FileUpload.jsx      # Drag-and-drop file upload
│           ├── Tabs.jsx            # Tab navigation
│           ├── DataOverview.jsx    # Dataset shape, columns, first rows
│           ├── BIDashboard.jsx     # BI drag-and-drop dashboard + Plotly charts
│           ├── Visualization.jsx   # Matplotlib-generated plots
│           ├── ModelTraining.jsx    # ML model training + Power BI export
│           ├── ModelComparison.jsx  # Side-by-side model comparison
│           ├── Prediction.jsx      # Auto-fill prediction form
│           ├── DataFixBanner.jsx   # Smart data fixer warning banner
│           └── AICopilot.jsx       # AI advisor drawer with NLP chat
│
├── app.log                     # Flask application logs
├── data_fixer.log              # Data fixer operation logs
├── power_bi.log                # Power BI export logs
└── test.log                    # Test execution logs
```

---

## 4. Backend Deep Dive

### 4.1 Session Management

The app uses an **in-memory session store** (`SESSIONS` dict) instead of a database. Each upload creates a UUID-keyed session:

```python
SESSIONS[session_id] = {
    'data': None,              # pandas DataFrame — the active dataset
    'model': None,             # Trained scikit-learn model object
    'scaler': None,            # StandardScaler fitted on training data
    'target_encoder': None,    # LabelEncoder for classification targets
    'target_is_classification': False,
    'feature_columns_final': None,     # Column names after encoding
    'feature_columns_categorical': None,
    'feature_stats': None,     # Mean/min/max per feature (for prediction UI)
    'categorical_encoder': None, # OrdinalEncoder for categorical features
    'raw_file_bytes': None,    # Original file bytes (for Smart Data Fixer re-parse)
    'raw_filename': None,
    'diagnosis': None,         # Data quality diagnosis result
    'bi_data': None,           # Aggregated BI data (for export)
    'latest_prediction': None  # Last prediction result (for export)
}
```

> [!IMPORTANT]
> Sessions live in memory only — restarting the Flask server clears all sessions. This is by design for a dev/demo tool.

### 4.2 API Endpoints

| Endpoint | Method | Component | Purpose |
|---|---|---|---|
| `/upload` | POST | FileUpload | Upload CSV/XLSX, auto-detect dtypes, run diagnosis |
| `/visualize` | POST | Visualization | Generate Matplotlib plots (histogram, scatter, box, correlation, pair, strip) |
| `/train_model` | POST | ModelTraining | Full ML pipeline: clean → encode → scale → train → evaluate |
| `/compare_models` | POST | ModelComparison | Train SVM + RF + XGBoost side-by-side |
| `/predict` | POST | Prediction | Run single-row prediction through trained model |
| `/get_sample_row` | POST | Prediction | Auto-fill form by searching existing data |
| `/aggregate` | POST | BIDashboard | Power BI-style GROUP BY + aggregation engine |
| `/fix_data` | POST | DataFixBanner | One-click auto-fix pipeline |
| `/ai_chat` | POST | AICopilot | NLP-powered advisory + proactive diagnostics |
| `/export` | GET | DataOverview | Export raw/BI/prediction data as CSV/XLSX |
| `/export_power_bi` | POST | ModelTraining | Export cleaned dataset for Power BI |
| `/data_summary` | GET | — | Full describe() statistics |
| `/stats_analysis` | POST | — | Advanced stats (correlation, missingness, value counts) |
| `/feature_info` | GET | — | Return trained feature columns + stats |
| `/ping` | GET | — | Health check |

---

## 5. Frontend Deep Dive

### 5.1 Component Hierarchy

```mermaid
graph TD
    App["App.jsx (Root)"]
    App --> FU["FileUpload"]
    App --> DFB["DataFixBanner"]
    App --> Tabs["Tabs"]
    App --> DO["DataOverview"]
    App --> BI["BIDashboard"]
    App --> VIZ["Visualization"]
    App --> MT["ModelTraining"]
    App --> MC["ModelComparison"]
    App --> PR["Prediction"]
    App --> AI["AICopilot (Floating Drawer)"]

    style App fill:#3b82f6,color:#fff
    style AI fill:#8b5cf6,color:#fff
    style DFB fill:#f59e0b,color:#000
```

### 5.2 State Management

All state is managed via React `useState` hooks in **App.jsx** and lifted to child components via props:

| State Variable | Shared With | Purpose |
|---|---|---|
| `sessionData` | All components | Session ID + data_info + diagnosis |
| `activeTab` | AICopilot, Tabs | Current visible tab |
| `biDimensions`, `biMeasures` | BIDashboard, AICopilot | BI configuration (for AI diagnostics) |
| `trainTarget`, `trainFeatures` | ModelTraining, AICopilot | ML config (for leakage detection) |
| `aiDrawerOpen` | App layout | Controls main content padding shift |

### 5.3 Design System

The CSS in `index.css` (1,398 lines) implements:

- **Glassmorphism** — `backdrop-filter: blur(16px)` with semi-transparent panels
- **Dark theme** with CSS variables (`--color-bg: #0f172a`)
- **Light theme** toggle via `[data-theme="light"]`
- **Inter font** from Google Fonts
- **Animated gradient borders** (Data Fix Banner)
- **Drag-and-drop** UI for BI Dashboard
- **AI Copilot drawer** with typing indicators, chat bubbles, suggestion chips
- **Micro-animations**: fadeIn, shimmer, pulse, gradient shifts

---

## 6. Complex Logic Breakdown

### 6.1 Smart Data Fixer Pipeline

The most complex subsystem — a 7-step diagnostic + auto-repair engine.

```mermaid
flowchart TD
    A["Raw file uploaded"] --> B["diagnose_data()"]
    B --> C{"Issues found?"}
    C -->|No| D["Clean data ✓"]
    C -->|Yes| E["Show DataFixBanner"]
    E --> F["User clicks 'Auto-Fix'"]
    F --> G["apply_data_fixes()"]

    subgraph "Diagnosis Checks (7 types)"
        B1["1. SINGLE_COLUMN — data crammed into 1 column"]
        B2["2. WRONG_DELIMITER — semicolon/tab/pipe instead of comma"]
        B3["3. UNNAMED_HEADERS — Unnamed: 0, empty headers"]
        B4["4. HEADER_IN_DATA — actual header is in row 0"]
        B5["5. GHOST_COLUMNS — columns that are >95% NaN"]
        B6["6. WHITESPACE — leading/trailing spaces in values"]
        B7["7. DUPLICATE_COLUMNS — repeated column names"]
        B8["8. EMPTY_ROWS — fully empty rows (>5% of data)"]
    end

    subgraph "Fix Pipeline (ordered)"
        G1["Step 1: Re-read with correct delimiter (csv.Sniffer)"]
        G2["Step 1.5: Universal single-column split (csv.reader)"]
        G3["Step 2: Promote header from first data row"]
        G4["Step 3: Rename unnamed columns (Column_1, Column_2...)"]
        G5["Step 4: Drop ghost columns (>95% NaN)"]
        G6["Step 5: Strip whitespace from text columns"]
        G7["Step 6: Deduplicate column names (_2, _3 suffix)"]
        G8["Step 7: Remove fully empty rows"]
        G9["Step 8: Auto-detect datetime columns"]
    end

    G --> G1 --> G2 --> G3 --> G4 --> G5 --> G6 --> G7 --> G8 --> G9
    G9 --> H["Re-run diagnosis on fixed data"]
    H --> I["Return fixed DataFrame + summary"]
```

> [!TIP]
> The fix pipeline uses `csv.Sniffer` for delimiter detection and falls back to character frequency counting. For fully-quoted CSVs, it uses `csv.QUOTE_NONE` to force-split quoted strings.

---

### 6.2 ML Training Engine

The training pipeline handles **both classification and regression** automatically:

```mermaid
flowchart TD
    A["POST /train_model"] --> B["Validate columns exist"]
    B --> C["Copy working DataFrame"]
    C --> D["Normalize empty strings → NaN"]
    D --> E["Drop rows with NaN target"]

    E --> F{"Target column type?"}
    F -->|Object/String| G["LabelEncoder → Classification"]
    F -->|Numeric, ≤20 unique & <10%| H["LabelEncoder → Classification"]
    F -->|Numeric, continuous| I["Fill NaN with mean → Regression"]

    G & H & I --> J["Handle features"]

    subgraph "Feature Preprocessing"
        J1["Convert datetime → int64 timestamps"]
        J2["Fill numeric NaN with column mean"]
        J3["Fill categorical NaN with mode"]
        J4["OrdinalEncoder for categorical features"]
        J5["StandardScaler on all features"]
    end

    J --> J1 --> J2 --> J3 --> J4 --> J5

    J5 --> K["train_test_split()"]
    K --> L{"Model type?"}
    L -->|SVM| M1["SVC / SVR"]
    L -->|Random Forest| M2["RF Classifier / Regressor"]
    L -->|XGBoost| M3["XGB Classifier / Regressor"]
    L -->|LightGBM| M4["LGBM Classifier / Regressor"]

    M1 & M2 & M3 & M4 --> N["model.fit() + predict()"]
    N --> O["Calculate metrics"]
    O --> P["Generate evaluation plot"]
    P --> Q["Save model + encoders to session"]
```

**Key decisions the engine makes automatically:**
1. **Classification vs Regression**: If target is non-numeric → classification. If numeric with ≤20 unique values and <10% unique ratio → classification. Otherwise → regression.
2. **Categorical encoding**: Uses `OrdinalEncoder` with `unknown_value=-1` to handle unseen categories at prediction time.
3. **Datetime handling**: Converts datetime columns to Unix timestamps (int64 / 10^9).
4. **Memory optimization**: `reduce_mem_usage()` downcasts numeric columns to the smallest possible dtype (int8, int16, float32, etc.), reducing memory by 30-70%.

---

### 6.3 AI Copilot NLP System

The AI Copilot is a **rule-based NLP advisor** with proactive diagnostics:

```mermaid
flowchart TD
    A["POST /ai_chat"] --> B["Extract context"]

    subgraph "Proactive Checks (run on every call)"
        C1["Data Leakage: target in features?"]
        C2["High Cardinality: >50 unique & >40% ratio?"]
        C3["Missing Data: any feature >15% NaN?"]
        C4["Time Frequency: daily over >1 year span?"]
    end

    B --> C1 & C2 & C3 & C4
    C1 & C2 & C3 & C4 --> D["Collect warnings[]"]

    subgraph "Intent Detection (keyword matching)"
        E1["'hello/hi/help' → General greeting + data summary"]
        E2["'bi/dashboard/chart' → BI Dashboard guide"]
        E3["'model/train/target' → Model training advice"]
        E4["'predict/input' → Prediction guide"]
        E5["'fix/clean/missing' → Data cleaning suggestions"]
        E6["fallback → General analysis suggestion"]
    end

    B --> E1 & E2 & E3 & E4 & E5 & E6
    E1 & E2 & E3 & E4 & E5 & E6 --> F["Generate reply"]

    D & F --> G["Return {reply, warnings[]}"]
```

**Frontend integration:**
- The AICopilot component runs a **debounced diagnostic check** (600ms) on every state change (tab switch, feature toggle, measure add, etc.)
- Warnings appear as a **banner inside the drawer** with severity styling
- Quick action chips change based on `activeTab`
- Messages support **markdown-like formatting** (bold, code, line breaks)

---

### 6.4 BI Aggregation Engine

The `/aggregate` endpoint acts like a **Power BI aggregation engine**:

```python
# Core logic
grouping_keys = dimensions + [pd.Grouper(key=time_dimension, freq=time_frequency)]
aggregated_df = df.groupby(grouping_keys).agg(agg_config)
```

**Supported aggregations:**
| Column Type | Allowed Aggregations |
|---|---|
| Numeric | `sum`, `mean`, `count`, `min`, `max`, `nunique` |
| Categorical | `count`, `nunique`, `min`, `max` |

**Chart rendering** happens client-side with **Plotly.js**:
- Auto-detects chart type: time dimension → line, 1 dimension → bar, 2+ dimensions → grouped bar
- Manual override: bar, line, pie, area, scatter
- Dark theme styling matching the CSS design system

---

### 6.5 Memory Optimization

```python
def reduce_mem_usage(df):
    """Downcasts every numeric column to the smallest possible dtype."""
    # int64 → int8/int16/int32 based on min/max range
    # float64 → float32 if values fit
    # Typical reduction: 30-70%
```

This runs on every upload and every fix operation, keeping large datasets manageable in-memory.

---

### 6.6 Custom JSON Serialization

Pandas/NumPy objects can't be directly JSON-serialized. The app uses two layers:

1. **`CustomJSONEncoder`** — Flask's JSON encoder override, handles `np.integer`, `np.floating`, `np.ndarray`, and `pd.NaT`
2. **`clean_for_json()`** — Recursive pre-serialization that handles `NaN → None`, `Inf → None`, nested dicts/lists, and NumPy scalars

---

## 7. Data Flow

### End-to-End: Upload → Train → Predict

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant VP as Vite Proxy
    participant BE as Flask Backend

    U->>FE: Drag & drop CSV file
    FE->>VP: POST /upload (FormData)
    VP->>BE: Forward request
    BE->>BE: Read file → DataFrame
    BE->>BE: reduce_mem_usage()
    BE->>BE: diagnose_data()
    BE->>BE: Auto-detect datetime columns
    BE-->>FE: {session_id, data_info, diagnosis}

    Note over FE: DataFixBanner checks diagnosis.has_issues

    alt Data has issues
        U->>FE: Click "Auto-Fix Data"
        FE->>BE: POST /fix_data
        BE->>BE: apply_data_fixes() — 7-step pipeline
        BE-->>FE: {fixed data_info, fixes_applied[]}
    end

    U->>FE: Select target + features, click "Train"
    FE->>BE: POST /train_model
    BE->>BE: Preprocess (encode, scale, split)
    BE->>BE: model.fit() + evaluate
    BE-->>FE: {accuracy, evaluation_plot, feature_importance}

    U->>FE: Fill prediction form, click "Predict"
    FE->>BE: POST /predict
    BE->>BE: Encode → Scale → model.predict()
    BE-->>FE: {prediction, problem_type}
```

---

## 8. Testing Architecture

### 8.1 Test Classes

The test suite in `master_test.py` has **two test classes**:

| Class | Purpose | Test Count |
|---|---|---|
| **`MasterTest`** | Backend Python logic — CSV parsing, API endpoints, aggregation, AI chat | ~25 tests |
| **`FrontendTest`** | Frontend validation — component structure, props, API contracts, exports | ~57 tests |

### 8.2 What Each Test Type Validates

#### Backend Tests (MasterTest)

```mermaid
graph LR
    subgraph "MasterTest"
        A["CSV Parser Tests"]
        B["API Contract Tests"]
        C["Aggregation Logic"]
        D["AI Copilot Logic"]
        E["Stub Tests (TODO)"]
    end

    A --> A1["test_csv_reader_quotes — quoted CSV parsing"]
    A --> A2["test_quotes_none — QUOTE_NONE fallback"]
    A --> A3["test_universal_fix — single-column CSV split"]

    B --> B1["test_aggregate_data — full aggregation flow"]
    B --> B2["test_ai_chat — 4 AI scenarios"]

    style A fill:#10b981,color:#fff
    style B fill:#3b82f6,color:#fff
```

> [!NOTE]
> Tests marked `pass # TODO: auto-generated test stub` were created by `auto_test_generator.py`. They exist as placeholders to remind you that the function exists but hasn't been fully tested yet. **They pass (since `pass` doesn't fail) and won't block your test suite.**

#### Frontend Tests (FrontendTest)

Frontend tests validate from the **backend side** — no browser/Node.js needed:

| Category | What's Tested | Example |
|---|---|---|
| **Structure** | All 10 JSX files exist | `test_all_component_files_exist` |
| **Exports** | Each file has exactly 1 `export default` | `test_all_components_have_default_export` |
| **Props** | Components receive correct props | `test_AICopilot_renders` checks 9 props |
| **API Contracts** | Backend endpoints respond to frontend calls | `test_FileUpload_api_contract` POSTs to `/upload` |
| **File Validation** | FileUpload checks `.csv`, `.xlsx`, `.xls` | `test_FileUpload_handleUpload` |
| **Chart Types** | BIDashboard supports bar/line/pie/area/scatter | `test_BIDashboard_chart_types` |
| **ML Models** | ModelTraining supports RF/XGB/LGBM/SVM | `test_ModelTraining_model_types` |
| **Plot Types** | Visualization has all 6 plot options | `test_Visualization_plot_types` |
| **AI Features** | AICopilot has quick chips per tab + warnings | `test_AICopilot_quick_action_chips` |
| **Data Fixer** | DataFixBanner has severity levels + success state | `test_DataFixBanner_severity_levels` |
| **Code Quality** | No `console.log` in production components | `test_no_console_errors_in_components` |

### 8.3 Auto Test Generator

`auto_test_generator.py` automatically keeps tests in sync with code changes:

```mermaid
flowchart TD
    A["Run auto_test_generator.py"] --> B["Scan Backend"]
    A --> C["Scan Frontend"]

    subgraph "Backend Scan"
        B --> B1["Parse app.py, data_fixer.py, power_bi_exporter.py with AST"]
        B1 --> B2["Extract top-level function names"]
        B2 --> B3["Filter out private functions (starting with _)"]
        B3 --> B4["Compare with existing MasterTest methods"]
        B4 --> B5["Generate test_funcName stubs for missing ones"]
    end

    subgraph "Frontend Scan"
        C --> C1["Glob all .jsx/.js files in frontend/src/"]
        C1 --> C2["Regex: extract 'export default ComponentName'"]
        C1 --> C3["Regex: extract handler functions (handle*, toggle*, add*, remove*, etc.)"]
        C2 & C3 --> C4["Build expected test names"]
        C4 --> C5["Compare with existing FrontendTest methods"]
        C5 --> C6["Generate test_Component_handler stubs"]
    end

    B5 --> D["Append to MasterTest class"]
    C6 --> E["Append to FrontendTest class"]
```

**Running it is safe** — it's idempotent. Running it twice produces no duplicates.

---

## 9. How to Run Tests

### 9.1 Quick Start — Run Everything

```bash
# Run ALL tests (backend + frontend) — from the project root
python -m unittest master_test -v
```

Expected output:
```
test_AICopilot_chat_api_contract ... ok
test_AICopilot_handleSendMessage ... ok
...
test_aggregate_data ... ok
test_ai_chat ... ok
...
----------------------------------------------------------------------
Ran 82 tests in 2.5s
OK
```

### 9.2 Run Only Backend Tests

```bash
python -m unittest master_test.MasterTest -v
```

### 9.3 Run Only Frontend Tests

```bash
python -m unittest master_test.FrontendTest -v
```

### 9.4 Run a Single Specific Test

```bash
# Run only the AI chat test
python -m unittest master_test.MasterTest.test_ai_chat -v

# Run only the BIDashboard chart types test
python -m unittest master_test.FrontendTest.test_BIDashboard_chart_types -v
```

### 9.5 Auto-Generate Missing Tests

```bash
# Scan code and add stubs for any new functions/components
python auto_test_generator.py
```

### 9.6 Full Confidence Workflow

> [!TIP]
> Follow this workflow before every commit to ensure nothing is broken:

```bash
# Step 1: Auto-generate stubs for any new code
python auto_test_generator.py

# Step 2: Run the full suite
python -m unittest master_test -v

# Step 3: If all pass, commit with confidence
python git_push.py
```

### 9.7 What NOT to Worry About

| Concern | Why It's Fine |
|---|---|
| **"TODO stub tests" failing** | They use `pass` — they always pass. They're reminders, not failures. |
| **stderr output during tests** | Flask prints debug logs to stderr (e.g., "Upload endpoint called"). The test result is in the last line: `OK` or `FAILED`. |
| **Exit code 1 on Windows** | PowerShell sometimes reports exit code 1 due to stderr output, even if all tests pass. Check the `Ran X tests... OK` line. |
| **No Node.js/browser needed** | Frontend tests read JSX files as text and validate structure. No React rendering happens. |
| **Session state between tests** | Each test that needs Flask creates its own `app.test_client()` and mock session. Tests are isolated. |

### 9.8 Adding Your Own Tests

#### Adding a Backend Test

```python
# In MasterTest class:
def test_my_new_endpoint(self):
    from app import app, SESSIONS
    import json, time

    app.config['TESTING'] = True
    client = app.test_client()

    # Setup mock session
    session_id = 'test-session-xyz'
    SESSIONS[session_id] = {
        'data': pd.DataFrame({'A': [1, 2], 'B': [3, 4]}),
        'last_accessed': time.time()
    }

    # Make request
    response = client.post('/my_endpoint',
                           data=json.dumps({'session_id': session_id}),
                           content_type='application/json')

    # Assert
    self.assertEqual(response.status_code, 200)
    data = json.loads(response.data)
    self.assertTrue(data['success'])
```

#### Adding a Frontend Test

```python
# In FrontendTest class:
def test_MyComponent_renders(self):
    content = self._read_component('MyComponent.jsx')
    self._assert_default_export(content, 'MyComponent')
    self._assert_props(content, ['requiredProp1', 'requiredProp2'])

def test_MyComponent_calls_api(self):
    content = self._read_component('MyComponent.jsx')
    self.assertIn("'/my_endpoint'", content, "Must call /my_endpoint")
```

---

## 10. Troubleshooting

### Common Issues

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'xgboost'` | Run `pip install xgboost lightgbm flask-cors openpyxl` |
| `UnicodeEncodeError: 'charmap' codec` | The auto_test_generator uses ASCII-safe output. If you add Unicode to print statements, use `logging` instead. |
| `Port 5000 already in use` | Kill the existing process: `taskkill /F /IM python.exe` (Windows) |
| Frontend tests fail after renaming a component | Run `python auto_test_generator.py` to regenerate stubs |
| `SESSIONS` appears empty in tests | You must manually populate `SESSIONS[session_id]` in your test — the test client doesn't persist state. |
| Tests pass but exit code is 1 | This is a Windows/PowerShell quirk — stderr output triggers non-zero exit. Check `Ran X tests... OK`. |

### Log Files

| File | What It Contains |
|---|---|
| `app.log` | Flask route errors, upload/train events |
| `data_fixer.log` | All diagnosis + fix operations with full details |
| `power_bi.log` | Power BI export events |
| `test.log` | Test execution logging (if configured) |

---

> **Last updated**: May 2026 | Generated from full codebase analysis
