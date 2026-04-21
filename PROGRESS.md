# 🚀 AI Fairness Auditor - Project State & Progress

This document serves as the "brain snapshot" for the project. If you return to this project in the future, feeding this document to the AI will instantly give it complete context on what has been built, how the architecture works, and what exactly needs to be done next.

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

---

## 🧩 3. System Architecture & Features
*   **The 11 Input Features:** `CODE_GENDER`, `AGE`, `AMT_INCOME_TOTAL`, `AMT_CREDIT`, `AMT_ANNUITY`, `NAME_EDUCATION_TYPE`, `OCCUPATION_TYPE`, `EXT_SOURCE_1`, `EXT_SOURCE_2`, `EXT_SOURCE_3`, `INCOME_GROUP`.

---

## 🚀 4. Team Structure & Future Roadmap

To ensure parallel development, we have divided into **Team 1: Brain (Logic/API)** and **Team 2: Body (UI/Automation)**.

### 🧠 Team 1 (The Backend API & AI Logic)

**Member A: The Infrastructure & API Architect (Currently Active)**
*   ✅ **Task 1:** FastAPI Core (`main.py`)
*   ✅ **Task 2:** Multi-Domain Switching (Lending vs Hiring logic)
*   ✅ **Task 4:** Counterfactual Logic ("Path to approval" loop)
*   ✅ **Task 5 (New):** Pydantic Adversarial Defense (Strict bounds like `AGE: 18-100` implemented on API).
*   ✅ **Task 6 (New):** MLOps API Architecture (Integrated `<500ms` SLA Latency Logging, extracted logic routing, added specific Exception tracebacks).
*   ✅ **Task 7 (New):** Model Serialization format (Bakes exact feature names, feature importances, training config, and version strings into `.joblib`).
*   ✅ **Task 8 (New):** Analytics Backend (Added prediction `confidence` logic directly to API payloads and structured JSON inference logging for downstream cloud metrics tracking).
*   ✅ **Task 9 (New):** Categorical Inference Safety (Fixed critical Pandas dummy zeroing bug ensuring single-row API inputs natively preserve sensitive values like `CODE_GENDER` instead of destroying them to baseline zeros).
*   ✅ **Task 10 (New):** Project Folder Reorganization (Cleaned up root directory into `logs/`, `reports/`, `scripts/`, and `pipeline/` for production readiness).
*   ⏳ **Task 3: Cloud Deployment (MLOps)** -> *NEXT IMMEDIATE STEP:* Member B has finished the Fairlearn and LLM hooks into `main.py`. Ready to execute the final `Dockerfile` build and deploy to Google Cloud Run.

**Member B: Fairness & Explainability Specialist**
*   ✅ **Task 1 (New): SHAP Integration & Slicing:** Crack open the XGBoost model to provide feature contributions (`explainability.py`). (API payload defense implemented: SHAP matrices must be sliced to TOP 5 to prevent latency spikes).
*   ✅ **Task 2: Fairlearn Mitigation:** Implement `ThresholdOptimizer` to correct the 17% Demographic Parity bias (completed via `python_mitigation.py`).
*   ✅ **Task 3: Gemini Agent:** Turn SHAP arrays into natural language audit logs (completed via `shap_llm_explainer.py`).
*   ✅ **Task 4 (New): Intersectional Bias:** Audit `CODE_GENDER_M` + `AGE` simultaneously. (API has been dynamically refactored to accept any `sensitive_col`).

### 🖥️ Team 2 (The UI, DB, & Automation)

**Member C: UX & Frontend Developer**
*   ⏳ **Task 1:** Build Streamlit Governance UI (Domain switches & Auditor workbench).
*   ⏳ **Task 2:** Interactive 11-feature "What-If" Sliders invoking `main.py`.
*   ⏳ **Task 3:** Data Visualizations for SHAP and risk scores.
*   ⏳ **Task 4:** Generate Fairness Certificate PDF.

**Member D: Automation & Integration Engineer**
*   ⏳ **Task 1:** Python `requests` logic to call Member A's FastAPI backend and handle loading states.
*   ⏳ **Task 2:** Wire up Firebase/Firestore to permanently save "Audit Logs".
*   ⏳ **Task 3:** Deploy the Streamlit frontend to Cloud Run.
*   ⏳ **Task 4:** Build the historical "Audit History" Review Tab.
