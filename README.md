# ⚖️ AI Bias Detection System (Fair ML)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=flat&logo=scikit-learn&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-%2317A2B8.svg?style=flat)

An end-to-end fairness auditing system designed to detect, explain, and mitigate biases in Machine Learning models (specifically focusing on Lending and Hiring models). This project was built to address UN Sustainable Development Goals (SDGs 10 & 16) as part of the Google Solution Challenge.

## 🚀 Overview

Real-world ML models can inadvertently learn and amplify societal biases. This project is an **AI Fairness Auditor** that analyzes an XGBoost model to ensure fair outcomes. 

It specifically looks at how features like `CODE_GENDER` affect the model's predictions and measures the **Demographic Parity Difference**. It also exposes a clean, secure FastAPI backend to serve as a fairness governance layer.

## 📘 What I Learned

Building this project was a deep dive into the intersection of Machine Learning, MLOps, and AI Ethics:

- **Quantifying Bias:** I learned how to use `Fairlearn` to mathematically prove model bias (e.g., discovering a 17.27% Demographic Parity Diff on gender in the baseline model).
- **Model Explainability:** Integrated `SHAP` to crack open "black box" XGBoost models, extracting the top feature contributions to explain *why* a model made a specific decision.
- **Robust MLOps Pipelines:** Built a secure inference pipeline using FastAPI and Pydantic to ensure strict data validation bounds (e.g., age constraints) and safe categorical handling, preventing adversarial or malformed inputs from breaking the model.
- **Counterfactual Logic:** Developed a logic engine that not only rejects applicants but automatically provides deterministic recommendations ("path to approval") for rejected applicants.

## 🛠️ Tech Stack & Architecture

- **Core ML:** XGBoost, Random Forest, Scikit-Learn, Pandas
- **Fairness & Explainability:** Fairlearn, SHAP
- **Backend Infrastructure:** FastAPI, Pydantic (for data validation)
- **Deployment:** Docker (planned), Cloud Run (planned)

## 📊 Key Features

1. **MLOps Tournament System:** Natively evaluates algorithms using StratifiedKFold + RandomizedSearchCV to compute optimal F1-score thresholds before deployment.
2. **Multi-Domain API:** A robust API (`/v1/audit`) that dynamically switches logic between Lending and Hiring domains.
3. **Pydantic Adversarial Defense:** Strict data validation limits to prevent edge cases from entering the inference pipeline.
4. **SHAP Slicing:** Extracts and slices SHAP matrices down to the top 5 contributing features to maintain low latency (<500ms SLA).
5. **Live Bias Metrics:** API responses dynamically output a `fairness_score` and detailed `bias_metrics` (e.g., Demographic Parity gap) based on whether baseline or Fairlearn mitigation is applied.

## 🚀 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Krispymarty/AI_bias_detection.git
   cd AI_bias_detection
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the FastAPI server:**
   From the root directory:
   ```bash
   uvicorn app.main:app --reload
   ```
   *(Alternatively, you can `cd app` and run `uvicorn main:app --reload`)*

4. **Test the API:**
   Navigate to `http://127.0.0.1:8000/docs` to view the interactive Swagger documentation and test the `/v1/audit` endpoint.

---
*This project is continuously evolving as I explore deeper concepts in Agentic AI and fairness algorithms.*
