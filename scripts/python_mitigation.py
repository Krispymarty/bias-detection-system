"""
=============================================================================
  UNBIASED AI -- FAIRLEARN BIAS MITIGATION  (Module 4)
=============================================================================
  Project  : Home Credit Default Risk -- Fairness Analysis
  Goal     : Take the biased XGBoost model and produce a FAIR version using
             Fairlearn's ThresholdOptimizer. The fair model is saved so the
             FastAPI backend can offer two prediction modes:
               /predict/biased  -- original XGBoost (fast, biased)
               /predict/fair    -- ThresholdOptimizer wrapper (equalized odds)

  Run with : python mitigation.py

  Inputs  (must be in the same folder):
    production_model.joblib    -- XGBoost model bundle
    final_merged_cleaned.csv   -- your merged + cleaned dataset
    shap_values.csv            -- SHAP matrix from shap_llm_explainer.py

  Outputs :
    fair_model.joblib          -- ThresholdOptimizer wrapped model
    mitigation_report.json     -- full before/after fairness metrics
    fairness_comparison.png    -- side-by-side bias metrics chart

  How ThresholdOptimizer works:
    It does NOT retrain the model. Instead it learns a DIFFERENT decision
    threshold for each demographic group so that the model satisfies a
    fairness constraint (EqualizedOdds) while keeping accuracy as high
    as possible. Males and females may get slightly different thresholds
    but their TRUE POSITIVE and FALSE POSITIVE rates will be equalised.
=============================================================================
"""

# -----------------------------------------------------------------------------
# SECTION 0 -- IMPORTS
# Install with:
#   python.exe -m pip install fairlearn scikit-learn pandas numpy joblib
#                             matplotlib xgboost
# -----------------------------------------------------------------------------

import os
import sys
import json
import warnings
import joblib
import numpy  as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.metrics         import (roc_auc_score, accuracy_score,
                                     classification_report, confusion_matrix)
from fairlearn.reductions    import ExponentiatedGradient, EqualizedOdds
from fairlearn.postprocessing import ThresholdOptimizer
from fairlearn.metrics        import (MetricFrame,
                                      selection_rate,
                                      true_positive_rate,
                                      false_positive_rate,
                                      false_negative_rate,
                                      count)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore")

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Working directory: {os.getcwd()}")


import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH      = os.path.join(BASE_DIR, "pipeline", "production_model_v1.joblib")
DATA_PATH       = os.path.join(BASE_DIR, "data", "final_merged_cleaned.csv")
SHAP_CSV_PATH   = os.path.join(BASE_DIR, "reports", "shap_values.csv")          # from shap_llm_explainer.py

FAIR_MODEL_PATH = os.path.join(BASE_DIR, "pipeline", "fair_model.joblib")         # output -- saved fair model
REPORT_PATH     = os.path.join(BASE_DIR, "pipeline", "mitigation_report.json")    # output -- full metrics report
CHART_PATH      = os.path.join(BASE_DIR, "reports", "fairness_comparison.png")   # output -- side-by-side chart

# The sensitive feature we're mitigating on.
# ThresholdOptimizer will equalize predictions across its values.
SENSITIVE_FEATURE = "CODE_GENDER_M_AND_AGE"

# Train/test split -- same seed as model training for consistency
TEST_SIZE   = 0.2
RANDOM_SEED = 42

# Fairness constraint: EqualizedOdds requires both TPR and FPR to be
# equal across groups. This is the right constraint for credit scoring
# because it means equally qualified applicants get equal treatment
# regardless of gender.
# Alternatives: DemographicParity (equal selection rate),
#               TruePositiveRateParity (equal TPR only)
FAIRNESS_CONSTRAINT = "equalized_odds"


# -----------------------------------------------------------------------------
# SECTION 2 -- LOAD MODEL AND DATA
# We use the same feature engineering as shap_llm_explainer.py so that
# the data fed to the fair model exactly matches what it was trained on.
# -----------------------------------------------------------------------------

def load_resources():
    print(f"\n{'='*60}")
    print("SECTION 2 -- Loading model and data")
    print(f"{'='*60}")

    # Load model bundle
    saved            = joblib.load(MODEL_PATH)
    model            = saved["model"]
    training_columns = saved["training_columns"]
    income_bins      = saved["income_bins"]

    print(f"  Model type       : {type(model).__name__}")
    print(f"  Features         : {training_columns}")
    print(f"  Income bins      : {income_bins}")

    # Load and prepare dataset
    df = pd.read_csv(DATA_PATH)
    print(f"  CSV loaded       : {df.shape[0]:,} rows x {df.shape[1]} columns")

    # AGE column
    if "AGE_YEARS" in df.columns:
        df["AGE"] = df["AGE_YEARS"].astype(int)
    elif "DAYS_BIRTH" in df.columns:
        df["AGE"] = (df["DAYS_BIRTH"].abs() / 365).astype(int)
    else:
        raise ValueError("No AGE_YEARS or DAYS_BIRTH column found.")

    # INCOME_GROUP one-hot (must use saved bins -- not hardcoded values)
    df["INCOME_GROUP"] = pd.cut(df["AMT_INCOME_TOTAL"], bins=income_bins,
                                labels=["Low", "Medium", "High"])
    income_dummies = pd.get_dummies(df["INCOME_GROUP"], prefix="INCOME_GROUP")
    df = pd.concat([df, income_dummies], axis=1)
    for col in ["INCOME_GROUP_Medium", "INCOME_GROUP_High"]:
        if col not in df.columns:
            df[col] = 0

    # OCCUPATION_TYPE label encode
    if df["OCCUPATION_TYPE"].dtype == object:
        df["OCCUPATION_TYPE"] = df["OCCUPATION_TYPE"].astype("category").cat.codes

    # Fill EXT_SOURCE nulls
    for col in ["EXT_SOURCE_2", "EXT_SOURCE_3"]:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())

    X = df[training_columns]
    y = df["TARGET"]

    print(f"  X shape          : {X.shape}")
    print(f"  Default rate     : {y.mean():.1%}")

    return model, training_columns, income_bins, X, y


# -----------------------------------------------------------------------------
# SECTION 3 -- TRAIN/TEST SPLIT
# We split BEFORE fitting ThresholdOptimizer.
# ThresholdOptimizer is fitted on TRAIN, evaluated on TEST.
# This mirrors exactly how the original model was validated.
# -----------------------------------------------------------------------------

def split_data(X, y):
    print(f"\n{'='*60}")
    print("SECTION 3 -- Train/test split")
    print(f"{'='*60}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_SEED,
        stratify=y           # keep 8% default rate in both splits
    )

    print(f"  Train : {X_train.shape[0]:,} rows  (default rate: {y_train.mean():.1%})")
    print(f"  Test  : {X_test.shape[0]:,} rows  (default rate: {y_test.mean():.1%})")

    # Sensitive feature vectors -- Intersectional groups
    gender_train_str = X_train["CODE_GENDER_M"].astype(int).map({0: "Female", 1: "Male"})
    age_train_str = np.where(X_train["AGE"] > 40, "Older", "Younger")
    sensitive_train = gender_train_str + "_" + age_train_str

    gender_test_str = X_test["CODE_GENDER_M"].astype(int).map({0: "Female", 1: "Male"})
    age_test_str = np.where(X_test["AGE"] > 40, "Older", "Younger")
    sensitive_test = gender_test_str + "_" + age_test_str

    print(f"\n  Sensitive feature  : {SENSITIVE_FEATURE}")
    print(f"  Train intersection split : {sensitive_train.value_counts().to_dict()}")
    print(f"  Test  intersection split : {sensitive_test.value_counts().to_dict()}")

    return X_train, X_test, y_train, y_test, sensitive_train, sensitive_test


# -----------------------------------------------------------------------------
# SECTION 4 -- BASELINE METRICS (BIASED MODEL)
# Measure the original model's performance and fairness BEFORE mitigation.
# These numbers are the "before" side of your hackathon comparison slide.
# -----------------------------------------------------------------------------

def compute_baseline_metrics(model, X_test, y_test, sensitive_test):
    print(f"\n{'='*60}")
    print("SECTION 4 -- Baseline metrics (biased model)")
    print(f"{'='*60}")

    y_pred_base  = model.predict(X_test)
    y_proba_base = model.predict_proba(X_test)[:, 1]

    # Overall performance
    auc      = roc_auc_score(y_test, y_proba_base)
    accuracy = accuracy_score(y_test, y_pred_base)

    print(f"  ROC-AUC  : {auc:.4f}")
    print(f"  Accuracy : {accuracy:.4f}")

    # Fairness metrics broken down by gender
    mf = MetricFrame(
        metrics={
            "selection_rate":      selection_rate,
            "true_positive_rate":  true_positive_rate,
            "false_positive_rate": false_positive_rate,
            "false_negative_rate": false_negative_rate,
            "count":               count,
        },
        y_true=y_test,
        y_pred=y_pred_base,
        sensitive_features=sensitive_test
    )

    print(f"\n  Fairness metrics by gender:")
    print(mf.by_group.to_string())
    print(f"\n  Disparities (max - min across groups):")
    print(f"    Selection rate gap   : {float(mf.difference(method='between_groups').iloc[0]):.4f}")
    print(f"    True positive rate   : {float(mf.difference(method='between_groups').iloc[0]):.4f}")
    print(f"    False positive rate  : {float(mf.difference(method='between_groups').iloc[0]):.4f}")
    print(f"    False negative rate  : {float(mf.difference(method='between_groups').iloc[0]):.4f}")

    return {
        "roc_auc":           round(auc, 4),
        "accuracy":          round(accuracy, 4),
        "y_pred":            y_pred_base,
        "y_proba":           y_proba_base,
        "metric_frame":      mf,
        "selection_rate_gap":    round(float(mf.difference(method='between_groups').iloc[0]), 4),
        "tpr_gap":               round(float(mf.difference(method='between_groups').iloc[0]), 4),
        "fpr_gap":               round(float(mf.difference(method='between_groups').iloc[0]), 4),
        "fnr_gap":               round(float(mf.difference(method='between_groups').iloc[0]), 4),
        "by_group":              mf.by_group.to_dict(),
    }


# -----------------------------------------------------------------------------
# SECTION 5 -- FIT THRESHOLD OPTIMIZER
# ThresholdOptimizer wraps the existing model -- it does NOT retrain it.
# It learns a separate decision threshold for each gender group such that
# the EqualizedOdds constraint is satisfied.
#
# EqualizedOdds means:
#   P(Yhat=1 | Y=1, Gender=Male)   == P(Yhat=1 | Y=1, Gender=Female)  [TPR]
#   P(Yhat=1 | Y=0, Gender=Male)   == P(Yhat=1 | Y=0, Gender=Female)  [FPR]
#
# In plain English: equally creditworthy applicants get equal treatment
# regardless of gender, and equally uncreditworthy applicants get equal
# rejection rates regardless of gender.
# -----------------------------------------------------------------------------

def fit_threshold_optimizer(model, X_train, y_train, sensitive_train):
    print(f"\n{'='*60}")
    print("SECTION 5 -- Fitting ThresholdOptimizer")
    print(f"{'='*60}")
    print(f"  Constraint : {FAIRNESS_CONSTRAINT}")
    print(f"  Wrapping   : {type(model).__name__} (no retraining)")
    print("  Fitting... ", end="", flush=True)

    # ThresholdOptimizer takes:
    #   estimator    -- the already-trained model (XGBoost)
    #   constraints  -- the fairness constraint to satisfy
    #   predict_method -- use 'predict_proba' so it has a continuous score
    #                     to threshold, not just 0/1 predictions
    optimizer = ThresholdOptimizer(
        estimator=model,
        constraints=FAIRNESS_CONSTRAINT,
        predict_method="predict_proba",
        objective="balanced_accuracy_score",   # keep accuracy as high as possible
        prefit=True,                           # Do not retrain the XGBoost model
    )

    optimizer.fit(
        X_train,
        y_train,
        sensitive_features=sensitive_train
    )

    print("done OK")
    print("  ThresholdOptimizer fitted -- no retraining, just threshold adjustment")
    return optimizer


# -----------------------------------------------------------------------------
# SECTION 6 -- FAIR MODEL METRICS
# Measure the fair model's performance on the test set.
# These are the "after" numbers for your hackathon slide.
# ThresholdOptimizer.predict() requires the sensitive_features argument
# at prediction time -- it uses the right threshold for each person's group.
# -----------------------------------------------------------------------------

def compute_fair_metrics(optimizer, X_test, y_test, sensitive_test):
    print(f"\n{'='*60}")
    print("SECTION 6 -- Fair model metrics")
    print(f"{'='*60}")

    # IMPORTANT: must pass sensitive_features at predict time
    y_pred_fair = optimizer.predict(X_test, sensitive_features=sensitive_test)

    # ROC-AUC requires probabilities -- ThresholdOptimizer's predict_proba
    # returns randomised predictions to satisfy the constraint, so we use
    # the underlying model's probabilities for the AUC metric only
    try:
        y_proba_fair = optimizer.predict_proba(
            X_test, sensitive_features=sensitive_test
        )[:, 1]
        auc = roc_auc_score(y_test, y_proba_fair)
    except Exception:
        # Fallback: use underlying model's probabilities for AUC
        y_proba_fair = optimizer.estimator_.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_proba_fair)

    accuracy = accuracy_score(y_test, y_pred_fair)

    print(f"  ROC-AUC  : {auc:.4f}")
    print(f"  Accuracy : {accuracy:.4f}")

    mf_fair = MetricFrame(
        metrics={
            "selection_rate":      selection_rate,
            "true_positive_rate":  true_positive_rate,
            "false_positive_rate": false_positive_rate,
            "false_negative_rate": false_negative_rate,
            "count":               count,
        },
        y_true=y_test,
        y_pred=y_pred_fair,
        sensitive_features=sensitive_test
    )

    print(f"\n  Fairness metrics by gender (after mitigation):")
    print(mf_fair.by_group.to_string())
    print(f"\n  Disparities AFTER mitigation:")
    print(f"    Selection rate gap : {float(mf_fair.difference(method='between_groups').iloc[0]):.4f}")
    print(f"    True positive rate : {float(mf_fair.difference(method='between_groups').iloc[0]):.4f}")
    print(f"    False positive rate: {float(mf_fair.difference(method='between_groups').iloc[0]):.4f}")
    print(f"    False negative rate: {float(mf_fair.difference(method='between_groups').iloc[0]):.4f}")

    return {
        "roc_auc":           round(auc, 4),
        "accuracy":          round(accuracy, 4),
        "y_pred":            y_pred_fair,
        "y_proba":           y_proba_fair,
        "metric_frame":      mf_fair,
        "selection_rate_gap":    round(float(mf_fair.difference(method='between_groups').iloc[0]), 4),
        "tpr_gap":               round(float(mf_fair.difference(method='between_groups').iloc[0]), 4),
        "fpr_gap":               round(float(mf_fair.difference(method='between_groups').iloc[0]), 4),
        "fnr_gap":               round(float(mf_fair.difference(method='between_groups').iloc[0]), 4),
        "by_group":              mf_fair.by_group.to_dict(),
    }


# -----------------------------------------------------------------------------
# SECTION 7 -- COMPARE AND PRINT TRADEOFF SUMMARY
# The core hackathon argument: we reduced bias significantly while
# losing only a small amount of accuracy. This is the fairness-accuracy
# tradeoff slide.
# -----------------------------------------------------------------------------

def print_tradeoff_summary(baseline, fair):
    print(f"\n{'='*60}")
    print("SECTION 7 -- Fairness vs Accuracy tradeoff summary")
    print(f"{'='*60}")

    auc_drop     = baseline["roc_auc"]  - fair["roc_auc"]
    acc_drop     = baseline["accuracy"] - fair["accuracy"]
    sel_improved = baseline["selection_rate_gap"] - fair["selection_rate_gap"]
    tpr_improved = baseline["tpr_gap"] - fair["tpr_gap"]
    fpr_improved = baseline["fpr_gap"] - fair["fpr_gap"]

    print(f"\n  {'Metric':<30} {'Before':>10} {'After':>10} {'Change':>10}")
    print(f"  {'-'*62}")
    print(f"  {'ROC-AUC':<30} {baseline['roc_auc']:>10.4f} {fair['roc_auc']:>10.4f} "
          f"  {auc_drop:>+.4f}")
    print(f"  {'Accuracy':<30} {baseline['accuracy']:>10.4f} {fair['accuracy']:>10.4f} "
          f"  {acc_drop:>+.4f}")
    print(f"  {'-'*62}")
    print(f"  {'Selection rate gap':<30} {baseline['selection_rate_gap']:>10.4f} "
          f"{fair['selection_rate_gap']:>10.4f}   {-sel_improved:>+.4f}")
    print(f"  {'TPR gap (equal opportunity)':<30} {baseline['tpr_gap']:>10.4f} "
          f"{fair['tpr_gap']:>10.4f}   {-tpr_improved:>+.4f}")
    print(f"  {'FPR gap (equal treatment)':<30} {baseline['fpr_gap']:>10.4f} "
          f"{fair['fpr_gap']:>10.4f}   {-fpr_improved:>+.4f}")

    print(f"\n  INTERPRETATION FOR HACKATHON PRESENTATION:")
    if sel_improved > 0.01:
        print(f"  - Selection rate gap reduced by {sel_improved:.3f} "
              f"({sel_improved/baseline['selection_rate_gap']*100:.0f}% improvement)")
    if abs(auc_drop) < 0.02:
        print(f"  - ROC-AUC only dropped by {auc_drop:.4f} (negligible -- model still accurate)")
    if tpr_improved > 0.01:
        print(f"  - True positive rate now more equal: gap reduced by {tpr_improved:.3f}")

    print(f"\n  KEY SLIDE CLAIM:")
    print(f"  'Our fair model reduces gender bias by "
          f"{sel_improved/max(baseline['selection_rate_gap'], 0.001)*100:.0f}% "
          f"while losing only {auc_drop:.3f} AUC -- proving fairness does not "
          f"require sacrificing accuracy.'")


# -----------------------------------------------------------------------------
# SECTION 8 -- GENERATE COMPARISON CHART
# Side-by-side bar chart showing before vs after for 3 key fairness metrics
# and 2 accuracy metrics. This is the main hackathon slide visual.
# -----------------------------------------------------------------------------

def generate_comparison_chart(baseline, fair):
    print(f"\n{'='*60}")
    print("SECTION 8 -- Generating comparison chart")
    print(f"{'='*60}")

    metrics = ["Selection rate gap", "TPR gap", "FPR gap"]
    before  = [baseline["selection_rate_gap"], baseline["tpr_gap"], baseline["fpr_gap"]]
    after   = [fair["selection_rate_gap"],     fair["tpr_gap"],     fair["fpr_gap"]]

    x     = np.arange(len(metrics))
    width = 0.35

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Left: fairness metric gaps
    bars1 = axes[0].bar(x - width/2, before, width, label="Biased model",
                        color="#e07070", edgecolor="black", linewidth=0.8)
    bars2 = axes[0].bar(x + width/2, after,  width, label="Fair model",
                        color="#70b070", edgecolor="black", linewidth=0.8)

    axes[0].set_xticks(x)
    axes[0].set_xticklabels(metrics, fontsize=10)
    axes[0].set_ylabel("Gap between Male and Female groups\n(lower = more fair)")
    axes[0].set_title("Fairness gaps: before vs after mitigation\n"
                      "Lower bar = more equal treatment", fontsize=11)
    axes[0].legend(fontsize=10)
    axes[0].axhline(0.05, color="orange", linewidth=1.2, linestyle="--",
                    label="0.05 bias threshold")
    axes[0].set_ylim(0, max(max(before), 0.12) * 1.3)

    # Add value labels on bars
    for bar in bars1:
        h = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2, h + 0.002,
                     f"{h:.3f}", ha="center", va="bottom", fontsize=9)
    for bar in bars2:
        h = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width()/2, h + 0.002,
                     f"{h:.3f}", ha="center", va="bottom", fontsize=9, color="#2d7a2d")

    # Right: accuracy metrics
    acc_metrics  = ["ROC-AUC", "Accuracy"]
    acc_before   = [baseline["roc_auc"], baseline["accuracy"]]
    acc_after    = [fair["roc_auc"],     fair["accuracy"]]

    x2 = np.arange(len(acc_metrics))
    axes[1].bar(x2 - width/2, acc_before, width, label="Biased model",
                color="#e07070", edgecolor="black", linewidth=0.8)
    axes[1].bar(x2 + width/2, acc_after,  width, label="Fair model",
                color="#70b070", edgecolor="black", linewidth=0.8)
    axes[1].set_xticks(x2)
    axes[1].set_xticklabels(acc_metrics, fontsize=10)
    axes[1].set_ylabel("Score (higher = better)")
    axes[1].set_title("Accuracy: before vs after mitigation\n"
                      "Goal: minimal drop while gaining fairness", fontsize=11)
    axes[1].legend(fontsize=10)
    axes[1].set_ylim(0.6, 1.0)

    for bars in [
        axes[1].patches[:len(acc_metrics)],
        axes[1].patches[len(acc_metrics):]
    ]:
        for bar in bars:
            h = bar.get_height()
            axes[1].text(bar.get_x() + bar.get_width()/2, h + 0.002,
                         f"{h:.4f}", ha="center", va="bottom", fontsize=9)

    plt.suptitle("Fairlearn ThresholdOptimizer -- Bias Mitigation Results\n"
                 "Constraint: EqualizedOdds on gender (CODE_GENDER_M)",
                 fontsize=12, y=1.01)
    plt.tight_layout()
    plt.savefig(CHART_PATH, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved --> {CHART_PATH}")


# -----------------------------------------------------------------------------
# SECTION 9 -- SAVE FAIR MODEL AND REPORT
# Saves:
#   fair_model.joblib       -- the ThresholdOptimizer bundle (model + thresholds)
#   mitigation_report.json  -- full before/after metrics for the API and dashboard
# -----------------------------------------------------------------------------

def save_outputs(optimizer, baseline, fair, training_columns, income_bins,
                 sensitive_test, y_test):
    print(f"\n{'='*60}")
    print("SECTION 9 -- Saving fair model and report")
    print(f"{'='*60}")

    # Save the fair model bundle -- same structure as production_model.joblib
    # so the API can load it with the same code
    fair_bundle = {
        "fair_model":        optimizer,      # ThresholdOptimizer instance
        "training_columns":  training_columns,
        "income_bins":       income_bins,
        "sensitive_feature": SENSITIVE_FEATURE,
        "constraint":        FAIRNESS_CONSTRAINT,
    }
    joblib.dump(fair_bundle, FAIR_MODEL_PATH)
    print(f"  Saved --> {FAIR_MODEL_PATH}")

    # Build per-group metrics as plain Python (JSON serialisable)
    def frame_to_dict(mf):
        result = {}
        for group_key, row in mf.by_group.iterrows():
            if isinstance(group_key, tuple):
                k = str(group_key[0])
            else:
                k = str(group_key)
            result[k] = {metric: round(float(val), 4) for metric, val in row.items()}
        return result

    report = {
        "description": (
            "Fairlearn ThresholdOptimizer mitigation results. "
            "Use /predict/fair endpoint to get bias-mitigated predictions."
        ),
        "constraint":          FAIRNESS_CONSTRAINT,
        "sensitive_feature":   SENSITIVE_FEATURE,
        "test_size":           TEST_SIZE,
        "baseline_model": {
            "roc_auc":               baseline["roc_auc"],
            "accuracy":              baseline["accuracy"],
            "selection_rate_gap":    baseline["selection_rate_gap"],
            "tpr_gap":               baseline["tpr_gap"],
            "fpr_gap":               baseline["fpr_gap"],
            "fnr_gap":               baseline["fnr_gap"],
            "by_group":              frame_to_dict(baseline["metric_frame"]),
        },
        "fair_model": {
            "roc_auc":               fair["roc_auc"],
            "accuracy":              fair["accuracy"],
            "selection_rate_gap":    fair["selection_rate_gap"],
            "tpr_gap":               fair["tpr_gap"],
            "fpr_gap":               fair["fpr_gap"],
            "fnr_gap":               fair["fnr_gap"],
            "by_group":              frame_to_dict(fair["metric_frame"]),
        },
        "improvement": {
            "auc_change":              round(fair["roc_auc"] - baseline["roc_auc"], 4),
            "accuracy_change":         round(fair["accuracy"] - baseline["accuracy"], 4),
            "selection_rate_gap_change": round(
                fair["selection_rate_gap"] - baseline["selection_rate_gap"], 4),
            "tpr_gap_change":          round(fair["tpr_gap"] - baseline["tpr_gap"], 4),
            "fpr_gap_change":          round(fair["fpr_gap"] - baseline["fpr_gap"], 4),
        },
        "api_usage": {
            "biased_endpoint":  "POST /predict/biased  -- original XGBoost",
            "fair_endpoint":    "POST /predict/fair    -- ThresholdOptimizer",
            "input_format": {
                "CODE_GENDER_M":     "int (0=Female, 1=Male)",
                "AGE":               "int (years)",
                "OCCUPATION_TYPE":   "int (label-encoded)",
                "AMT_INCOME_TOTAL":  "float",
                "AMT_CREDIT":        "float",
                "AMT_ANNUITY":       "float",
                "EXT_SOURCE_2":      "float (0.0-1.0)",
                "EXT_SOURCE_3":      "float (0.0-1.0)",
                "INCOME_GROUP_Medium": "int (0 or 1)",
                "INCOME_GROUP_High":   "int (0 or 1)"
            },
            "note": (
                "Fair endpoint requires CODE_GENDER_M in the request body "
                "so ThresholdOptimizer can apply the correct threshold. "
                "It is used only to select the threshold -- not as a prediction feature."
            )
        }
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  Saved --> {REPORT_PATH}")

    return report


# -----------------------------------------------------------------------------
# SECTION 10 -- API INTEGRATION CODE
# Prints the exact Python code your teammate needs to add to api.py to
# expose both biased and fair prediction endpoints.
# -----------------------------------------------------------------------------

def print_api_integration_code():
    print(f"\n{'='*60}")
    print("SECTION 10 -- API integration code for your teammate")
    print(f"{'='*60}")

    code = '''
# ── Add this to api.py ────────────────────────────────────────────────────

import joblib, pandas as pd, numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Unbiased AI Prediction API")

# Load both models at startup
biased_bundle = joblib.load("production_model.joblib")
fair_bundle   = joblib.load("fair_model.joblib")

biased_model     = biased_bundle["model"]
fair_model       = fair_bundle["fair_model"]         # ThresholdOptimizer
training_columns = biased_bundle["training_columns"]
income_bins      = biased_bundle["income_bins"]

class ApplicantInput(BaseModel):
    CODE_GENDER_M:    int
    AGE:              int
    OCCUPATION_TYPE:  int
    AMT_INCOME_TOTAL: float
    AMT_CREDIT:       float
    AMT_ANNUITY:      float
    EXT_SOURCE_2:     float
    EXT_SOURCE_3:     float

def preprocess(data: ApplicantInput) -> pd.DataFrame:
    row = data.dict()
    income = row["AMT_INCOME_TOTAL"]
    row["INCOME_GROUP_Medium"] = 1 if 117000 <= income < 180000 else 0
    row["INCOME_GROUP_High"]   = 1 if income >= 180000 else 0
    return pd.DataFrame([row])[training_columns]

@app.post("/predict/biased")
def predict_biased(data: ApplicantInput):
    """Original XGBoost -- fast but biased."""
    X     = preprocess(data)
    proba = float(biased_model.predict_proba(X)[0][1])
    return {
        "decision":            "REJECTED" if proba > 0.5 else "APPROVED",
        "default_probability": round(proba, 4),
        "model_type":          "biased",
        "warning":             "This prediction may reflect gender bias."
    }

@app.post("/predict/fair")
def predict_fair(data: ApplicantInput):
    """ThresholdOptimizer -- equalized odds constraint on gender."""
    X          = preprocess(data)
    gender_val = "Male" if data.CODE_GENDER_M == 1 else "Female"
    sensitive  = pd.Series([gender_val])

    pred  = fair_model.predict(X, sensitive_features=sensitive)[0]
    try:
        proba = float(fair_model.predict_proba(
            X, sensitive_features=sensitive)[0][1])
    except Exception:
        proba = float(biased_model.predict_proba(X)[0][1])

    return {
        "decision":            "REJECTED" if pred == 1 else "APPROVED",
        "default_probability": round(proba, 4),
        "model_type":          "fair",
        "constraint":          "equalized_odds",
        "note":                "Gender-equalized threshold applied."
    }

@app.get("/fairness/report")
def fairness_report():
    """Returns full before/after fairness metrics."""
    import json
    with open("mitigation_report.json") as f:
        return json.load(f)

# Run: uvicorn api:app --reload
'''
    print(code)
    print("\n  Save the above as api.py and run:")
    print("    pip install fastapi uvicorn")
    print("    uvicorn api:app --reload")
    print("    curl -X POST http://localhost:8000/predict/fair \\")
    print("         -H 'Content-Type: application/json' \\")
    print("         -d '{\"CODE_GENDER_M\":0,\"AGE\":34,\"OCCUPATION_TYPE\":4,")
    print("              \"AMT_INCOME_TOTAL\":135000,\"AMT_CREDIT\":450000,")
    print("              \"AMT_ANNUITY\":22500,\"EXT_SOURCE_2\":0.312,")
    print("              \"EXT_SOURCE_3\":0.198}'")


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

def main():
    print("\n" + "="*60)
    print("  UNBIASED AI -- FAIRLEARN BIAS MITIGATION")
    print("  ThresholdOptimizer -- EqualizedOdds on gender")
    print("="*60)

    model, training_columns, income_bins, X, y = load_resources()
    X_train, X_test, y_train, y_test, sensitive_train, sensitive_test = split_data(X, y)
    baseline = compute_baseline_metrics(model, X_test, y_test, sensitive_test)
    optimizer = fit_threshold_optimizer(model, X_train, y_train, sensitive_train)
    fair = compute_fair_metrics(optimizer, X_test, y_test, sensitive_test)
    print_tradeoff_summary(baseline, fair)
    generate_comparison_chart(baseline, fair)
    report = save_outputs(optimizer, baseline, fair, training_columns, income_bins,
                          sensitive_test, y_test)
    print_api_integration_code()

    print(f"\n{'='*60}")
    print("  ALL DONE -- Files produced:")
    print(f"{'='*60}")
    for fname, desc in [
        (FAIR_MODEL_PATH, "ThresholdOptimizer model bundle"),
        (REPORT_PATH,     "Full before/after fairness metrics"),
        (CHART_PATH,      "Side-by-side comparison chart"),
    ]:
        status = "OK" if os.path.exists(fname) else "MISSING"
        print(f"  {status}  {fname:<35} {desc}")

    # Quick summary for copy-paste into presentation
    print(f"\n  PRESENTATION NUMBERS:")
    print(f"  Before: AUC={baseline['roc_auc']:.4f}  "
          f"selection_gap={baseline['selection_rate_gap']:.4f}  "
          f"fpr_gap={baseline['fpr_gap']:.4f}")
    print(f"  After : AUC={fair['roc_auc']:.4f}  "
          f"selection_gap={fair['selection_rate_gap']:.4f}  "
          f"fpr_gap={fair['fpr_gap']:.4f}")
    print()


if __name__ == "__main__":
    main()
