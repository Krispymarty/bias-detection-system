# 🚀 AI Fairness Auditor - Project State & Progress

This document serves as the "brain snapshot" for the project. If you return to this project in the future, feeding this document to the AI will instantly give it complete context on what has been built, how the architecture works, and what exactly needs to be done next.

**Last Updated:** 2026-04-26

---

## 🎯 1. Project Goal
Building a production-ready **AI Fairness Auditor** for the Google Solution Challenge (addressing UN SDGs 10 & 16). The system detects biases in ML models, explains them using SHAP, mitigates them algorithmically, and exposes a clean API for Team 2 to build a What-If Dashboard.

---

## ✅ 2. What We Have Completed

### Step 1: Core ML Pipeline & Preprocessing (`model.py`)
*   **Status:** DONE
*   **Tech Stack:** `XGBoost`, `Random Forest`, `pandas`, `joblib`
*   **What it does:** Modularity and inference safety (dynamic `AGE` calculation, `INCOME_GROUP` bucketing, strict column matching).
*   ✅ **Update 1:** Explicit `OCCUPATION_MAP` string-to-float lookup mechanism dynamically integrated to bypass flawed Pandas dummy defaults.
*   ✅ **Update 2:** MLOps Tournament implemented. Natively evaluates algorithms using StratifiedKFold + RandomizedSearchCV (with early stopping) and automatically computes the optimal F1-score threshold before baking `production_model_v1.joblib` (Achieved ROC-AUC 0.7319).

### Step 2: Bias Detection Engine (`bias.py`)
*   **Status:** DONE
*   **Tech Stack:** `Fairlearn`
*   **What it does:** Extracts exact probabilities and proves XGBoost is mathematically biased (17.27% Demographic Parity Diff on `CODE_GENDER_M`).

### Step 3: Backend API Integration (`app/main.py`)
*   **Status:** DONE *(Member A)*
*   **Tech Stack:** `FastAPI`, `Pydantic`
*   **What it does:** Exposes `/v1/audit` which safely translates our 11 UI features into the exact Pandas format for XGBoost.
*   **Features:** Implements Multi-Domain switching (selects Lending vs Hiring models via `request.domain`) and a Counterfactual Logic engine that automatically provides deterministic recommendations for rejected applicants.

### Step 4: Enterprise-Grade API Restructure *(NEW — 2026-04-22)*
*   **Status:** DONE
*   **What changed:** The `/v1/audit` response was completely restructured into clean, separated sections:
    *   **`fairness`** — Score (0–100), badge (🟢🟡🔴), bias source classification, bias metrics, sensitive feature alerts
    *   **`governance`** — Confidence level, confidence warning (human review flag for borderline 0.45–0.55 decisions), model version, mitigation toggle
    *   **`explanation`** — Top 5 SHAP feature contributions with protected attribute flagging (triggers when `|SHAP| > 0.1` for `CODE_GENDER_M` or `AGE`)
    *   **`system`** — Response latency in ms, domain

### Step 5: Before vs After Comparison Endpoint *(NEW — 2026-04-22)*
*   **Status:** DONE
*   **Endpoint:** `POST /v1/audit/compare`
*   **What it does:** Runs the same applicant through BOTH the baseline (biased) and fair (mitigated) models and returns a side-by-side comparison with fairness gain calculation.
*   **Example output:** Baseline fairness 53.6 → Mitigated fairness 96.3 → **+42.7 point gain**

### Step 6: Expanded Intersectional Fairness *(NEW — 2026-04-22)*
*   **Status:** DONE
*   **Before:** 4 groups (Gender × Age)
*   **After:** **12 groups** (Gender × Age × Income)
*   **Result:** Selection rate gap reduced from **0.4635 → 0.0373** (92% bias reduction, 0 AUC loss)

### Step 7: Frontend Integration *(NEW — 2026-04-26)*
*   **Status:** DONE
*   **Tech Stack:** `Streamlit`, `Plotly`, `ReportLab`
*   **What it does:** A comprehensive UI (`frontend/`) that integrates with the FastAPI backend. It features interactive "What-If" sliders, SHAP data visualizations, dynamic API URL routing, and a multi-page setup isolated from the main backend repository structure.

---

## 🧩 3. System Architecture & Features

### Input Features (11)
`CODE_GENDER`, `AGE`, `AMT_INCOME_TOTAL`, `AMT_CREDIT`, `AMT_ANNUITY`, `NAME_EDUCATION_TYPE`, `OCCUPATION_TYPE`, `EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3`, `INCOME_GROUP`

### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/audit` | Full fairness audit with structured response |
| `POST` | `/v1/audit/compare` | Side-by-side baseline vs mitigated comparison |
| `GET`  | `/v1/fairness_report` | Complete before/after metrics for all 12 groups |
| `GET`  | `/health` | Health check for deployment |

### Fairness Results — Before vs After
| Metric | Before (Biased) | After (Fair) | Change |
|--------|-----------------|--------------|--------|
| Selection Rate Gap | 0.4635 (46.4%) | 0.0373 (3.7%) | **-92% bias** ✅ |
| ROC-AUC | 0.7319 | 0.7319 | **0 drop** ✅ |
| Accuracy | 0.6744 | 0.6048 | -0.07 (minimal) |
| Demographic Groups | 4 | **12** | Gender × Age × Income |

---

## 🚀 4. Team Structure & Future Roadmap

To ensure parallel development, we have divided into **Team 1: Brain (Logic/API)** and **Team 2: Body (UI/Automation)**.

### 🧠 Team 1 (The Backend API & AI Logic)

**Member A: The Infrastructure & API Architect**
*   ✅ **Task 1:** FastAPI Core (`main.py`)
*   ✅ **Task 2:** Multi-Domain Switching (Lending vs Hiring logic)
*   ✅ **Task 4:** Counterfactual Logic ("Path to approval" loop)
*   ✅ **Task 5:** Pydantic Adversarial Defense (Strict bounds like `AGE: 18-100` implemented on API).
*   ✅ **Task 6:** MLOps API Architecture (Integrated `<500ms` SLA Latency Logging, extracted logic routing, added specific Exception tracebacks).
*   ✅ **Task 7:** Model Serialization format (Bakes exact feature names, feature importances, training config, and version strings into `.joblib`).
*   ✅ **Task 8:** Analytics Backend (Added prediction `confidence` logic directly to API payloads and structured JSON inference logging for downstream cloud metrics tracking).
*   ✅ **Task 9:** Categorical Inference Safety (Fixed critical Pandas dummy zeroing bug ensuring single-row API inputs natively preserve sensitive values like `CODE_GENDER` instead of destroying them to baseline zeros).
*   ✅ **Task 10:** Project Folder Reorganization (Cleaned up root directory into `logs/`, `reports/`, `scripts/`, and `pipeline/` for production readiness).
*   ✅ **Task 11 (NEW):** Enterprise API Restructure — Separated response into `fairness`, `governance`, `explanation`, `system` sections.
*   ✅ **Task 12 (NEW):** Confidence Warning System — Flags borderline decisions (0.45–0.55) for human review.
*   ✅ **Task 13 (NEW):** Protected Feature Alert — Detects when sensitive attributes (`CODE_GENDER_M`, `AGE`) have SHAP impact > 0.1.
*   ✅ **Task 14 (NEW):** Bias Source Classification — Distinguishes "Historical Data Bias" from "Model Bias (Mitigated/Detected)".
*   ✅ **Task 15 (NEW):** Fairness Badge System — 🟢 Fair (>85), 🟡 Moderate (70–85), 🔴 Risky (<70).
*   ✅ **Task 16 (NEW):** Before vs After Comparison Endpoint (`/v1/audit/compare`).
*   ✅ **Task 17 (NEW):** Live Bias Metrics — `fairness_score` and `bias_metrics` populated from `mitigation_report.json`.
*   ✅ **Task 18 (NEW):** sys.path fix for teammate compatibility (uvicorn from `app/` directory).
*   ⏳ **Task 3: Cloud Deployment (MLOps)** -> *NEXT STEP:* Execute the final `Dockerfile` build and deploy to Google Cloud Run.

**Member B: Fairness & Explainability Specialist**
*   ✅ **Task 1:** SHAP Integration & Slicing (`explainability.py`). SHAP matrices sliced to TOP 5 to prevent latency spikes.
*   ✅ **Task 2:** Fairlearn Mitigation — `ThresholdOptimizer` to correct bias (completed via `python_mitigation.py`).
*   ✅ **Task 3:** Gemini Agent — Turn SHAP arrays into natural language audit logs (`shap_llm_explainer.py`).
*   ✅ **Task 4:** Intersectional Bias — Originally `CODE_GENDER_M` + `AGE` (4 groups).
*   ✅ **Task 5 (NEW):** Expanded Intersectional Bias to `Gender × Age × Income` (12 groups). Selection rate gap reduced by 92%.

### 🖥️ Team 2 (The UI, DB, & Automation)

**Member C: UX & Frontend Developer**
*   ✅ **Task 1:** Build Streamlit Governance UI (Domain switches & Auditor workbench).
*   ✅ **Task 2:** Interactive 11-feature "What-If" Sliders invoking `main.py`.
*   ✅ **Task 3:** Data Visualizations for SHAP and risk scores.
*   ✅ **Task 4:** Generate Fairness Certificate PDF.

**Member D: Automation & Integration Engineer**
*   ✅ **Task 1:** Python `requests` logic to call Member A's FastAPI backend — **API is now live and tested**.
*   ⏳ **Task 2:** Wire up Firebase/Firestore to permanently save "Audit Logs".
*   ⏳ **Task 3:** Deploy the Streamlit frontend to Cloud Run.
*   ⏳ **Task 4:** Build the historical "Audit History" Review Tab.
