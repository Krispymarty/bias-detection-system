"""
=============================================================================
  UNBIASED AI -- SHAP EXPLAINABILITY + GEMINI LLM TRANSLATOR
=============================================================================
  Project  : Home Credit Default Risk -- Fairness Analysis
  Module   : 2 (SHAP) + 3 (LLM Interpreter)
  Goal     : Compute SHAP values, detect gender/age bias, and translate
             every model decision into plain English using Gemini API.
             All results are saved to llm_explanations.json for the
             What-If Simulator (Module 4 -- teammate's component).

  Run with : python shap_llm_explainer.py

  Outputs  :
    shap_beeswarm.png           -- global feature importance plot
    bias_gender_shap.png        -- gender bias bar + violin plot
    bias_age_shap.png           -- age vs SHAP scatter plot
    shap_waterfall_individual.png -- single-applicant decision breakdown
    shap_values.csv             -- raw SHAP values for Fairlearn (Module 4)
    llm_explanations.json       -- Gemini explanations for What-If simulator
=============================================================================
"""

# -----------------------------------------------------------------------------
# SECTION 0 -- IMPORTS
# All libraries must be installed before running:
#   pip install pandas numpy scikit-learn xgboost shap joblib
#               matplotlib google-generativeai
# -----------------------------------------------------------------------------

import os
import sys
# Force UTF-8 output on Windows — prevents UnicodeEncodeError on cp1252 terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
import time
import warnings
import joblib
import numpy  as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")           # non-interactive backend -- safe for scripts
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import shap
from google import genai
from google.genai import types

warnings.filterwarnings("ignore")   # suppress minor sklearn/xgboost warnings
# Always run from the script's own folder
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(f"Working directory: {os.getcwd()}")

# -----------------------------------------------------------------------------
# SECTION 1 -- CONFIGURATION
# Change these values if your file names or API key differ.
# -----------------------------------------------------------------------------

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the saved XGBoost model (dict with 'model', 'training_columns',
# 'income_bins' keys -- produced by your teammate's training notebook)
MODEL_PATH = os.path.join(BASE_DIR, "pipeline", "production_model_v1.joblib")

# Path to your cleaned and merged dataset (output of your cleaning notebook)
DATA_PATH  = os.path.join(BASE_DIR, "data", "final_merged_cleaned.csv")

# Your Gemini API key from https://aistudio.google.com/app/apikey (free)
import os
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# How many rows to sample for SHAP computation.
# 2000 is enough for statistically valid results and runs in ~30 seconds.
SHAP_SAMPLE_SIZE = 2000

# Random seed -- keeps results reproducible across runs
RANDOM_SEED = 42

# Protected attributes -- features that should NOT influence loan decisions
# by law (gender, age). Used to flag bias in SHAP analysis.
PROTECTED_ATTRIBUTES = ["CODE_GENDER_M", "AGE"]

# How many applicants to explain with Gemini and save to JSON.
# Breakdown: 5 rejected + 3 approved + 2 borderline = 10 total.
# Your teammate gets one JSON entry per applicant for the What-If simulator.
N_REJECTED   = 2
N_APPROVED   = 1
N_BORDERLINE = 0


# -----------------------------------------------------------------------------
# SECTION 2 -- LOAD MODEL
# The joblib file is a Python dict, not a bare model object.
# We unpack the 3 components we need: model, feature names, income bin edges.
# -----------------------------------------------------------------------------

def load_model(path):
    """
    Load the saved production model bundle.

    Returns
    -------
    model            : XGBClassifier -- the trained XGBoost model
    training_columns : list[str]     -- exact 10 feature names in training order
    income_bins      : np.ndarray    -- bin edges used to create INCOME_GROUP
    """
    print(f"\n{'='*60}")
    print("SECTION 2 -- Loading model")
    print(f"{'='*60}")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Model file not found: {path}\n"
            "Make sure production_model.joblib is in the same folder as this script."
        )

    saved = joblib.load(path)
    print(f"  Keys in file     : {list(saved.keys())}")

    model            = saved["model"]
    training_columns = saved["training_columns"]
    income_bins      = saved["income_bins"]

    print(f"  Model type       : {type(model).__name__}")
    print(f"  Features ({len(training_columns)})     : {training_columns}")
    print(f"  Income bins      : {income_bins}")
    print(f"  n_estimators     : {model.n_estimators}")
    print(f"  scale_pos_weight : {model.scale_pos_weight:.2f}  (handles class imbalance)")
    return model, training_columns, income_bins


# -----------------------------------------------------------------------------
# SECTION 3 -- LOAD AND PREPARE DATA
# We need to recreate the exact same feature engineering that was used
# during training, otherwise the model will give wrong predictions.
# Key steps:
#   - AGE_YEARS already exists in cleaned CSV -- use it directly
#   - INCOME_GROUP must be binned with the SAME bin edges from training
#   - OCCUPATION_TYPE must be label-encoded (it's a string in the CSV)
# -----------------------------------------------------------------------------

def load_and_prepare_data(data_path, training_columns, income_bins):
    """
    Load the cleaned CSV and reproduce the exact feature engineering
    that was applied during model training.

    Returns
    -------
    X        : pd.DataFrame -- full feature matrix (307511 x 10)
    y        : pd.Series    -- target labels (0 = no default, 1 = default)
    X_sample : pd.DataFrame -- stratified random sample of 2000 rows for SHAP
    y_sample : pd.Series    -- matching target labels for the sample
    """
    print(f"\n{'='*60}")
    print("SECTION 3 -- Loading and preparing data")
    print(f"{'='*60}")

    if not os.path.exists(data_path):
        raise FileNotFoundError(
            f"Dataset not found: {data_path}\n"
            "Make sure final_merged_cleaned.csv is in the same folder."
        )

    df = pd.read_csv(data_path)
    print(f"  CSV loaded       : {df.shape[0]:,} rows x {df.shape[1]} columns")

    # -- Step 1: Create AGE column ------------------------------------------
    # The model was trained with a column called 'AGE' (integer years).
    # The cleaned CSV stores it as 'AGE_YEARS'. We just rename it.
    # Do NOT use DAYS_BIRTH here -- that gives negative values.
    if "AGE_YEARS" in df.columns:
        df["AGE"] = df["AGE_YEARS"].astype(int)
        print(f"  AGE source       : AGE_YEARS column  "
              f"(range: {df['AGE'].min()}–{df['AGE'].max()} years)")
    elif "DAYS_BIRTH" in df.columns:
        # Fallback: DAYS_BIRTH is positive days since birth in cleaned data
        df["AGE"] = (df["DAYS_BIRTH"].abs() / 365).astype(int)
        print(f"  AGE source       : DAYS_BIRTH → converted to years")
    else:
        raise ValueError(
            "Cannot find AGE_YEARS or DAYS_BIRTH in the dataset. "
            "Check your cleaned CSV column names."
        )

    # -- Step 2: Recreate INCOME_GROUP one-hot encoding -------------------
    # The model expects TWO binary columns: INCOME_GROUP_Medium and
    # INCOME_GROUP_High (Low is the implicit reference category -- dropped).
    # We must use the EXACT same bin edges that were used at training time,
    # which are saved inside the model file.
    df["INCOME_GROUP"] = pd.cut(
        df["AMT_INCOME_TOTAL"],
        bins=income_bins,
        labels=["Low", "Medium", "High"]
    )
    income_dummies = pd.get_dummies(df["INCOME_GROUP"], prefix="INCOME_GROUP")
    df = pd.concat([df, income_dummies], axis=1)

    # Safety: ensure both dummy columns exist even if one category has 0 rows
    for col in ["INCOME_GROUP_Medium", "INCOME_GROUP_High"]:
        if col not in df.columns:
            df[col] = 0

    # -- Step 3: Encode OCCUPATION_TYPE (string → integer) -----------------
    # XGBoost requires numeric inputs. The cleaned CSV stores OCCUPATION_TYPE
    # as a string. We convert to category codes (0, 1, 2, ...).
    # This must match the encoding used at training time.
    if df["OCCUPATION_TYPE"].dtype == object:
        df["OCCUPATION_TYPE"] = df["OCCUPATION_TYPE"].astype("category").cat.codes

    # -- Step 4: Verify all 10 features exist -----------------------------
    missing = [c for c in training_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing features: {missing}\nCheck your CSV column names.")
    print(f"  All 10 features  : found OK")

    # -- Step 5: Select features and target -------------------------------
    X = df[training_columns]    # shape: (307511, 10)
    y = df["TARGET"]            # 0 = repaid, 1 = defaulted

    print(f"  X shape          : {X.shape}")
    print(f"  Missing values   : {X.isnull().sum().sum()} total")
    print(f"  Default rate     : {y.mean():.1%}  (expected ~8%)")

    # -- Step 6: Fill any remaining nulls in EXT_SOURCE columns -----------
    # EXT_SOURCE_1/2/3 are credit bureau scores -- some applicants have none.
    # We fill with the median (population average) -- same strategy as training.
    for col in ["EXT_SOURCE_2", "EXT_SOURCE_3"]:
        if X[col].isnull().any():
            median_val = X[col].median()
            X = X.copy()
            X[col] = X[col].fillna(median_val)
            print(f"  Filled nulls     : {col} → median {median_val:.4f}")

    # -- Step 7: Sample 2000 rows for SHAP --------------------------------
    # SHAP computes one value per feature per row. On 307k rows that takes
    # ~20 minutes. 2000 rows gives statistically representative results
    # in ~30 seconds. We use the same index for X and y to keep them aligned.
    sample_idx = X.sample(n=SHAP_SAMPLE_SIZE, random_state=RANDOM_SEED).index
    X_sample   = X.loc[sample_idx].reset_index(drop=True)
    y_sample   = y.loc[sample_idx].reset_index(drop=True)

    print(f"  Sample shape     : {X_sample.shape}  (for SHAP computation)")
    print(f"  Sample default % : {y_sample.mean():.1%}  (should match full dataset)")

    return X, y, X_sample, y_sample


# -----------------------------------------------------------------------------
# SECTION 4 -- COMPUTE SHAP VALUES
# SHAP (SHapley Additive exPlanations) explains WHY the model made each
# decision by measuring how much each feature pushed the prediction above
# or below the baseline (average prediction).
#
# Positive SHAP value → feature pushed toward DEFAULT (higher risk)
# Negative SHAP value → feature pushed toward REPAYMENT (lower risk)
#
# We use TreeExplainer which is specifically optimised for tree-based models
# like XGBoost -- it's 100x faster than the generic KernelExplainer.
# -----------------------------------------------------------------------------

def compute_shap_values(model, X_sample):
    """
    Compute SHAP values for all rows in X_sample.

    Returns
    -------
    explainer  : shap.TreeExplainer -- fitted explainer object
    shap_values: np.ndarray         -- shape (2000, 10), one value per feature per row
    base_val   : float              -- baseline prediction (average across all data)
    """
    print(f"\n{'='*60}")
    print("SECTION 4 -- Computing SHAP values")
    print(f"{'='*60}")
    print("  Creating TreeExplainer (optimised for XGBoost)...")

    explainer = shap.TreeExplainer(model)

    # Fix for SHAP 0.51+: expected_value is returned as a numpy array.
    # float() on an array silently returns 0.0 -- .item() correctly extracts
    # the single scalar value regardless of array shape.
    ev = explainer.expected_value
    base_val = ev.item() if hasattr(ev, "item") else float(ev)
    print(f"  Baseline (expected value) : {base_val:.4f} log-odds")
    print(f"  Baseline probability      : {1/(1+np.exp(-base_val)):.1%}"
          "  (should be ~8%)")

    print(f"  Computing SHAP values for {SHAP_SAMPLE_SIZE} rows... (30–60 sec)")
    shap_values = explainer.shap_values(X_sample)
    print(f"  SHAP values shape : {shap_values.shape}")

    # Sanity check: SHAP values + baseline should approximately equal
    # the model's raw prediction for the same row (in log-odds space)
    row_idx    = 0
    shap_sum   = shap_values[row_idx].sum() + base_val
    model_pred = model.predict_proba(X_sample.iloc[[row_idx]])[0][1]
    print(f"  Sanity check row 0: SHAP sum+baseline={shap_sum:.4f}, "
          f"model predict_proba={model_pred:.4f}")

    return explainer, shap_values, base_val


# -----------------------------------------------------------------------------
# SECTION 5 -- GENERATE SHAP PLOTS
# Four visualisations:
#   1. Beeswarm  -- which features matter most globally, and how
#   2. Gender    -- does gender systematically push predictions?
#   3. Age       -- does age systematically push predictions?
#   4. Waterfall -- full breakdown for one specific high-risk applicant
# -----------------------------------------------------------------------------

def generate_plots(shap_values, X_sample, training_columns, base_val, model):
    """
    Generate and save all SHAP visualisation plots.
    Also computes and returns the gender fairness gap (used later for LLM).
    """
    print(f"\n{'='*60}")
    print("SECTION 5 -- Generating SHAP plots")
    print(f"{'='*60}")

    # -- Plot 1: Beeswarm (global feature importance) ----------------------
    # Each row = one feature. Each dot = one applicant.
    # X-axis = SHAP value (right = pushed toward default).
    # Color  = feature value (red = high, blue = low).
    # Features sorted by mean |SHAP| -- most important at top.
    print("  Generating beeswarm plot...")
    plt.figure(figsize=(10, 6))
    shap.summary_plot(
        shap_values,
        X_sample,
        feature_names=training_columns,
        plot_type="dot",
        max_display=10,
        show=False
    )
    plt.title("SHAP Beeswarm -- Global Feature Importance\n"
              "Rightward = pushes toward default risk", fontsize=12)
    plt.tight_layout()
    plt.savefig("shap_beeswarm.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved → shap_beeswarm.png")

    # -- Plot 2: Gender bias ----------------------------------------------
    # Left : bar chart of mean SHAP by gender group
    # Right: violin plot showing full distribution
    # If bars differ significantly → model treats gender as a risk factor
    print("  Generating gender bias plot...")
    gender_idx = training_columns.index("CODE_GENDER_M")

    # .astype(int) is required because the CSV stores this as boolean
    # True/False. Without it, .map({1:..., 0:...}) matches nothing → crash.
    gender_df = pd.DataFrame({
        "SHAP_value": shap_values[:, gender_idx],
        "Gender":     X_sample["CODE_GENDER_M"].astype(int)
                      .map({1: "Male", 0: "Female"})
    })

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    mean_shap_by_gender = gender_df.groupby("Gender")["SHAP_value"].mean()

    mean_shap_by_gender.plot(
        kind="bar", ax=axes[0],
        color=["#e07070", "#7090d0"],
        edgecolor="black", width=0.5
    )
    axes[0].axhline(0, color="black", linewidth=0.8, linestyle="--")
    axes[0].set_title(
        "Average SHAP value for gender feature\n"
        "Positive bar = that group is pushed toward default risk", fontsize=11
    )
    axes[0].set_ylabel("Mean SHAP value")
    axes[0].tick_params(axis="x", rotation=0)

    female_shap = gender_df[gender_df["Gender"] == "Female"]["SHAP_value"]
    male_shap   = gender_df[gender_df["Gender"] == "Male"]["SHAP_value"]
    axes[1].violinplot([female_shap, male_shap], positions=[0, 1], showmedians=True)
    axes[1].set_xticks([0, 1])
    axes[1].set_xticklabels(["Female", "Male"])
    axes[1].axhline(0, color="red", linewidth=0.8, linestyle="--")
    axes[1].set_title(
        "SHAP distribution by gender\n"
        "Width = density of applicants at each SHAP value", fontsize=11
    )
    axes[1].set_ylabel("SHAP value for gender feature")

    plt.tight_layout()
    plt.savefig("bias_gender_shap.png", dpi=150, bbox_inches="tight")
    plt.close()

    # Compute the fairness gap -- this number goes into every LLM prompt
    male_mean   = float(shap_values[X_sample["CODE_GENDER_M"].astype(int)==1, gender_idx].mean())
    female_mean = float(shap_values[X_sample["CODE_GENDER_M"].astype(int)==0, gender_idx].mean())
    gender_fairness_gap = abs(male_mean - female_mean)

    print(f"  Saved → bias_gender_shap.png")
    print(f"  Male mean SHAP   : {male_mean:+.4f}")
    print(f"  Female mean SHAP : {female_mean:+.4f}")
    print(f"  Fairness gap     : {gender_fairness_gap:.4f}  "
          f"({'BIAS DETECTED' if gender_fairness_gap > 0.05 else 'within acceptable range'})")

    # -- Plot 3: Age scatter -----------------------------------------------
    # If there's a consistent trend (e.g., older → negative SHAP = lower risk),
    # the model is using age as a proxy -- regardless of actual creditworthiness.
    print("  Generating age bias scatter...")
    age_idx = training_columns.index("AGE")
    plt.figure(figsize=(9, 5))
    sc = plt.scatter(
        X_sample["AGE"],
        shap_values[:, age_idx],
        alpha=0.25, s=8,
        c=shap_values[:, age_idx], cmap="RdBu_r"
    )
    plt.colorbar(sc, label="SHAP value (red = toward default, blue = toward repayment)")
    plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
    plt.xlabel("Age (years)")
    plt.ylabel("SHAP value for AGE feature")
    plt.title(
        "Age vs SHAP value\n"
        "A downward trend means older applicants are systematically scored as lower risk",
        fontsize=11
    )
    plt.tight_layout()
    plt.savefig("bias_age_shap.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved → bias_age_shap.png")

    # -- Plot 4: Waterfall for highest-risk applicant ----------------------
    # Shows exactly how each feature shifted the prediction for one person.
    # Starts at baseline, each bar is one feature's contribution.
    # Red bars push toward default, blue bars push away from default.
    print("  Generating waterfall plot for highest-risk applicant...")
    high_risk_idx = int(shap_values.sum(axis=1).argmax())
    explanation = shap.Explanation(
        values        = shap_values[high_risk_idx],
        base_values   = base_val,
        data          = X_sample.iloc[high_risk_idx].values,
        feature_names = training_columns
    )
    plt.figure(figsize=(10, 6))
    shap.plots.waterfall(explanation, show=False)
    plt.title(
        f"Why was applicant #{high_risk_idx} predicted high-risk?\n"
        "Each bar = one feature's contribution to the decision",
        fontsize=11
    )
    plt.tight_layout()
    plt.savefig("shap_waterfall_individual.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("  Saved → shap_waterfall_individual.png")

    return gender_fairness_gap, mean_shap_by_gender


# -----------------------------------------------------------------------------
# SECTION 6 -- SAVE RAW SHAP VALUES
# The raw SHAP matrix (2000 rows x 10 features) is saved as a CSV.
# This is the input for Module 4 (Fairlearn bias mitigation notebook).
# -----------------------------------------------------------------------------

def save_shap_csv(shap_values, training_columns, y_sample):
    """Save raw SHAP values + target labels to CSV for Fairlearn notebook."""
    print(f"\n{'='*60}")
    print("SECTION 6 -- Saving raw SHAP values to CSV")
    print(f"{'='*60}")

    shap_df = pd.DataFrame(shap_values, columns=training_columns)
    shap_df["TARGET"] = y_sample.values
    shap_df.to_csv("shap_values.csv", index=False)
    print(f"  Saved → shap_values.csv  ({shap_df.shape[0]} rows x {shap_df.shape[1]} cols)")
    print("  Your teammate's Fairlearn notebook can load this directly.")


# -----------------------------------------------------------------------------
# SECTION 7 -- GEMINI LLM SETUP
# We use gemini-1.5-flash which is free, fast, and supports the
# structured prompts we need. No billing required for hackathon usage.
# -----------------------------------------------------------------------------

GEMINI_MODEL = "gemini-2.5-flash"   # confirmed available via ListModels

def setup_gemini(api_key):
    """Configure and return the Gemini client. Free tier, no billing needed."""
    print(f"\n{'='*60}")
    print("SECTION 7 -- Setting up Gemini LLM")
    print(f"{'='*60}")
    if not api_key:
        print("  WARNING: GEMINI_API_KEY is not set. LLM features will be disabled.")
        return None
        
    client = genai.Client(api_key=api_key)
    # Quick connectivity test -- list one model to confirm the key works
    try:
        models = list(client.models.list())
        model_names = [m.name for m in models[:3]]
        print(f"  Gemini client connected OK  (sample models: {model_names})")
    except Exception as e:
        print(f"  WARNING: Could not list models -- {e}")
        print(f"  Will still attempt generation calls.")
    print(f"  Active model: {GEMINI_MODEL}")
    return client


# -----------------------------------------------------------------------------
# SECTION 8 -- LLM TRANSLATION HELPERS
# Two helper functions:
#   get_top_features() -- extracts top N features by |SHAP| and flags protected ones
#   explain_with_llm() -- builds a structured prompt and calls Gemini
# -----------------------------------------------------------------------------

def get_top_features(shap_row, feature_names, top_n=5):
    """
    Extract the most influential features for one applicant.

    Sorts by absolute SHAP value (largest impact first).
    Flags CODE_GENDER_M and AGE as protected attributes -- these are the
    features that should NOT be influencing credit decisions but often do.

    Parameters
    ----------
    shap_row     : np.ndarray -- SHAP values for one applicant (length 10)
    feature_names: list[str]  -- feature names in the same order
    top_n        : int        -- how many features to return

    Returns
    -------
    list of dicts with keys:
        feature, shap_value, direction, is_protected
    """
    pairs = sorted(zip(feature_names, shap_row),
                   key=lambda x: abs(x[1]), reverse=True)
    return [{
        "feature":      name,
        "shap_value":   round(float(val), 4),
        # Human-readable direction label for the JSON and prompt
        "direction":    "increases default risk" if val > 0 else "decreases default risk",
        # True if this feature is legally protected -- should not drive decisions
        "is_protected": name in PROTECTED_ATTRIBUTES
    } for name, val in pairs[:top_n]]


def explain_with_llm(applicant_idx, X_sample, shap_values, training_columns,
                     model, base_val, gender_fairness_gap, llm):
    """
    Translate one applicant's SHAP output into plain English using Gemini.

    Process:
    1. Compute prediction probability from XGBoost
    2. Extract top 5 SHAP features (sorted by impact)
    3. Build a structured prompt with full context
    4. Call Gemini API
    5. Return a rich dict containing EVERYTHING the What-If simulator needs

    The returned dict is directly JSON-serialisable -- no further processing
    needed before saving to file.

    Parameters
    ----------
    applicant_idx       : int    -- row index in X_sample (0–1999)
    X_sample            : pd.DataFrame -- the 2000-row sample
    shap_values         : np.ndarray   -- SHAP values (2000, 10)
    training_columns    : list[str]    -- feature names
    model               : XGBClassifier -- loaded model for predict_proba
    base_val            : float        -- baseline prediction (log-odds)
    gender_fairness_gap : float        -- computed gap between male/female SHAP
    llm                 : GenerativeModel -- configured Gemini instance

    Returns
    -------
    dict -- fully structured explanation ready for JSON export
    """
    # -- Get prediction ----------------------------------------------------
    row      = X_sample.iloc[[applicant_idx]]
    shap_row = shap_values[applicant_idx]
    proba    = float(model.predict_proba(row)[0][1])

    # Decision threshold: probability > 50% → REJECTED (predicted to default)
    decision = "REJECTED" if proba > 0.5 else "APPROVED"

    # -- Extract top features ----------------------------------------------
    top_feats = get_top_features(shap_row, training_columns, top_n=5)

    # -- Build feature table string for the prompt -------------------------
    # This gives Gemini a structured, readable table of what drove the decision
    feat_lines = []
    for f in top_feats:
        protected_tag = "PROTECTED ATTRIBUTE -- " if f["is_protected"] else ""
        feat_lines.append(
            f"  - {f['feature']}: SHAP = {f['shap_value']:+.4f}  "
            f"({protected_tag}{f['direction']})"
        )
    feat_table = "\n".join(feat_lines)

    # -- Read applicant profile values -------------------------------------
    # .astype(int) handles boolean storage of CODE_GENDER_M
    gender_label = "Male" if int(row["CODE_GENDER_M"].values[0]) == 1 else "Female"
    age          = int(row["AGE"].values[0])
    ext2         = round(float(row["EXT_SOURCE_2"].values[0]), 3)
    ext3         = round(float(row["EXT_SOURCE_3"].values[0]), 3)
    income       = round(float(row["AMT_INCOME_TOTAL"].values[0]), 0)
    credit       = round(float(row["AMT_CREDIT"].values[0]), 0)
    annuity      = round(float(row["AMT_ANNUITY"].values[0]), 0)
    occ_code     = int(row["OCCUPATION_TYPE"].values[0])

    # Convert base_val from log-odds to probability for the prompt
    base_prob    = round(1 / (1 + np.exp(-base_val)) * 100, 1)

    # -- Build the structured prompt ---------------------------------------
    # We give Gemini:
    #   - Full applicant profile (context)
    #   - The model's decision and confidence
    #   - Top 5 SHAP values with direction labels
    #   - The fairness gap number
    #   - Explicit instructions for 3 focused paragraphs
    prompt = f"""You are an AI Ethics Assistant reviewing a loan application decision made by a machine learning model.

APPLICANT PROFILE:
  - Gender           : {gender_label}
  - Age              : {age} years
  - Annual income    : {income:,.0f}
  - Loan requested   : {credit:,.0f}
  - Monthly payment  : {annuity:,.0f}
  - Credit score 1   : {ext2:.3f}  (EXT_SOURCE_2, external bureau -- higher is better)
  - Credit score 2   : {ext3:.3f}  (EXT_SOURCE_3, external bureau -- higher is better)
  - Occupation code  : {occ_code}

MODEL DECISION: {decision}
  - Default probability : {proba:.1%}
  - Population baseline : {base_prob:.1f}%  (average default rate)

TOP 5 FEATURES DRIVING THIS DECISION (SHAP values):
{feat_table}

HOW TO READ SHAP VALUES:
  - Positive SHAP (+) means the feature INCREASED the default risk for this person
  - Negative SHAP (-) means the feature DECREASED the default risk for this person
  - The magnitude (size) shows how strongly that feature influenced the outcome

FAIRNESS CONTEXT:
  - Gender fairness gap (SHAP): {gender_fairness_gap:.4f}
  - Interpretation: If this number is above 0.05, gender is systematically
    shifting predictions -- meaning the model treats male and female applicants
    differently even when their financial profiles are similar.

YOUR TASK -- Answer in exactly 3 short paragraphs, total under 140 words:

Paragraph 1 -- DECISION REASON:
  Explain in plain English why this applicant was {decision}.
  Reference the specific feature names and their SHAP values.
  Avoid technical jargon -- write as if explaining to the applicant.

Paragraph 2 -- BIAS CHECK:
  Does gender (CODE_GENDER_M) or age (AGE) appear in the top features?
  If yes, is the SHAP value large enough to be concerning?
  State clearly whether bias appears to be present or not.

Paragraph 3 -- RECOMMENDATION:
  Give one specific, actionable recommendation to make this decision fairer.
  Be concrete -- name the feature to remove or the policy to change."""

    # -- Call Gemini with retry + fallback model --------------------------
    # llm is now a google.genai.Client instance.
    if llm is None:
        llm_text = "[LLM explanation unavailable: GEMINI_API_KEY is not set]"
        models_to_try = []
    else:
        FALLBACK_MODEL = "gemini-2.0-flash-lite"
        models_to_try  = [GEMINI_MODEL, FALLBACK_MODEL]
        llm_text       = None

    for attempt_model in models_to_try:
        max_retries = 4
        for attempt in range(max_retries):
            try:
                response = llm.models.generate_content(
                    model=attempt_model,
                    contents=prompt,
                )
                llm_text = response.text
                break   # success -- stop retrying
            except Exception as api_err:
                err_str = str(api_err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    # Try to extract the retry delay seconds from the message
                    import re as _re
                    delay_match = _re.search(r"retryDelay.*?(\d+)s", err_str)
                    wait_secs   = int(delay_match.group(1)) + 5 if delay_match else 40
                    if attempt < max_retries - 1:
                        print(f"\n    [Rate limit] model={attempt_model}, "
                              f"sleeping {wait_secs}s then retrying "
                              f"(attempt {attempt+1}/{max_retries})...")
                        time.sleep(wait_secs)
                    else:
                        print(f"\n    [Rate limit] model={attempt_model} exhausted "
                              f"after {max_retries} attempts, trying fallback...")
                else:
                    # Non-rate-limit error -- don't retry
                    print(f"\n  WARNING: Gemini error (model={attempt_model}): {api_err}")
                    llm_text = (
                        f"[LLM call failed: {api_err}]\n"
                        "SHAP values and applicant profile are still available."
                    )
                    break
        if llm_text is not None:
            break   # got a response from one of the models

    if llm_text is None:
        llm_text = (
            "[All Gemini models returned quota errors. "
            "SHAP values and applicant profile are still valid in this record. "
            "Re-run tomorrow when the daily quota resets, or upgrade your API plan.]"
        )

    # -- Build complete output dict ----------------------------------------
    # Everything is included so your teammate can use it without
    # reloading the model or CSV.
    return {
        # Identity
        "applicant_index":      applicant_idx,

        # Model output
        "decision":             decision,
        "default_probability":  round(proba, 4),
        "baseline_probability": round(1 / (1 + np.exp(-base_val)), 4),

        # Applicant profile (all values the What-If simulator needs)
        "applicant_profile": {
            "gender":       gender_label,
            "age":          age,
            "income":       income,
            "loan_amount":  credit,
            "monthly_payment": annuity,
            "credit_score_1":  ext2,
            "credit_score_2":  ext3,
            "occupation_code": occ_code
        },

        # SHAP analysis
        "top_shap_features":     top_feats,
        "gender_fairness_gap":   round(gender_fairness_gap, 4),
        "bias_detected":         gender_fairness_gap > 0.05,

        # Gemini's human-readable explanation (3 paragraphs)
        "llm_explanation": llm_text,

        # Raw feature values for all 10 columns -- teammate uses these
        # to pre-populate What-If simulator sliders without extra CSV reads
        "raw_feature_values": {
            col: round(float(row[col].values[0]), 4)
            for col in training_columns
        }
    }


# -----------------------------------------------------------------------------
# SECTION 9 -- BATCH EXPLAIN AND SAVE JSON
# We explain 10 applicants (5 rejected + 3 approved + 2 borderline).
# This variety helps the What-If simulator demonstrate different scenarios.
# All results are saved to llm_explanations.json.
# -----------------------------------------------------------------------------

def batch_explain_and_save(X_sample, shap_values, training_columns,
                           model, base_val, gender_fairness_gap, llm):
    """
    Explain a diverse set of applicants with Gemini and save to JSON.

    Selects:
      - N_REJECTED   high-confidence rejections (proba > 0.6)
      - N_APPROVED   high-confidence approvals  (proba < 0.3)
      - N_BORDERLINE cases closest to the 0.5 decision boundary

    The JSON output includes a metadata section (for context) and
    an explanations array (one entry per applicant).
    """
    print(f"\n{'='*60}")
    print("SECTION 9 -- Batch LLM explanation + JSON export")
    print(f"{'='*60}")

    probas = model.predict_proba(X_sample)[:, 1]

    # Select diverse applicant indices
    rejected_idx   = [i for i, p in enumerate(probas) if p > 0.6][:N_REJECTED]
    approved_idx   = [i for i, p in enumerate(probas) if p < 0.3][:N_APPROVED]
    borderline_idx = sorted(range(len(probas)),
                            key=lambda i: abs(probas[i] - 0.5))[:N_BORDERLINE]
    all_idx = rejected_idx + approved_idx + borderline_idx

    print(f"  Applicants selected : {len(all_idx)} total")
    print(f"    Rejected   : {rejected_idx}")
    print(f"    Approved   : {approved_idx}")
    print(f"    Borderline : {borderline_idx}")
    print()

    all_explanations = []
    for i, idx in enumerate(all_idx):
        label = ("REJECTED" if probas[idx] > 0.5 else "APPROVED")
        print(f"  [{i+1:02d}/{len(all_idx)}] Applicant index {idx:4d}  "
              f"proba={probas[idx]:.1%}  {label} ... ", end="", flush=True)

        result = explain_with_llm(
            applicant_idx       = idx,
            X_sample            = X_sample,
            shap_values         = shap_values,
            training_columns    = training_columns,
            model               = model,
            base_val            = base_val,
            gender_fairness_gap = gender_fairness_gap,
            llm                 = llm
        )
        all_explanations.append(result)
        print("done OK")

        # 1 second pause between Gemini calls to respect free-tier rate limits
        # (Free tier: 15 requests/minute, this ensures we stay well under)
        time.sleep(1)

    # -- Build final JSON structure -----------------------------------------
    output = {
        "metadata": {
            "description":
                "SHAP + Gemini LLM explanations for Home Credit Default Risk model. "
                "Used by What-If Simulator (Module 4).",
            "model":                     "XGBClassifier",
            "features_used":             training_columns,
            "total_explained":           len(all_explanations),
            "shap_sample_size":          SHAP_SAMPLE_SIZE,
            "gender_fairness_gap":       round(gender_fairness_gap, 4),
            "bias_detected":             gender_fairness_gap > 0.05,
            "baseline_default_prob":     round(1 / (1 + np.exp(-base_val)), 4),
            "breakdown": {
                "rejected":   len(rejected_idx),
                "approved":   len(approved_idx),
                "borderline": len(borderline_idx)
            },
            "json_structure_guide": {
                "metadata":    "Summary info about the whole run",
                "explanations": "Array -- one entry per applicant",
                "  .decision":             "APPROVED or REJECTED",
                "  .default_probability":  "0.0–1.0 (model's confidence)",
                "  .applicant_profile":    "gender, age, income, loan, credit scores",
                "  .top_shap_features":    "top 5 features, SHAP values, is_protected flag",
                "  .bias_detected":        "True if gender gap > 0.05",
                "  .llm_explanation":      "Gemini's 3-paragraph plain-English explanation",
                "  .raw_feature_values":   "all 10 features -- use for What-If sliders"
            }
        },
        "explanations": all_explanations
    }

    # -- Save to file ------------------------------------------------------
    output_path = "llm_explanations.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size_kb = os.path.getsize(output_path) / 1024
    print(f"\n  Saved → {output_path}  ({file_size_kb:.1f} KB)")
    return output


# -----------------------------------------------------------------------------
# SECTION 10 -- PRINT SAMPLE OUTPUT
# Prints one full entry from the JSON so you can verify the format
# before handing it to your teammate.
# -----------------------------------------------------------------------------

def print_sample_output(output):
    """Print the first explanation entry in a clean, readable format."""
    print(f"\n{'='*60}")
    print("SECTION 10 -- Sample output (first entry from JSON)")
    print(f"{'='*60}")

    meta = output["metadata"]
    first = output["explanations"][0]

    print(f"\n  METADATA SUMMARY")
    print(f"  Total explained     : {meta['total_explained']}")
    print(f"  Gender fairness gap : {meta['gender_fairness_gap']}")
    print(f"  Bias detected       : {meta['bias_detected']}")
    print(f"  Baseline default %  : {meta['baseline_default_prob']:.1%}")

    print(f"\n  FIRST APPLICANT (index {first['applicant_index']})")
    print(f"  Decision            : {first['decision']}")
    print(f"  Default probability : {first['default_probability']:.1%}")
    print(f"  Gender              : {first['applicant_profile']['gender']}")
    print(f"  Age                 : {first['applicant_profile']['age']}")
    print(f"  Income              : {first['applicant_profile']['income']:,.0f}")
    print(f"  Loan amount         : {first['applicant_profile']['loan_amount']:,.0f}")

    print(f"\n  TOP SHAP FEATURES:")
    for feat in first["top_shap_features"]:
        tag = "  *** PROTECTED ***" if feat["is_protected"] else ""
        print(f"    {feat['feature']:<25} {feat['shap_value']:+.4f}  "
              f"{feat['direction']}{tag}")

    print(f"\n  GEMINI EXPLANATION:")
    print("  " + first["llm_explanation"].replace("\n", "\n  "))

    print(f"\n  RAW FEATURE VALUES (for What-If simulator sliders):")
    for k, v in first["raw_feature_values"].items():
        print(f"    {k:<25} {v}")


# -----------------------------------------------------------------------------
# MAIN -- Run all sections in order
# -----------------------------------------------------------------------------

def main():
    print("\n" + "="*60)
    print("  UNBIASED AI -- SHAP + GEMINI EXPLAINER")
    print("  Home Credit Default Risk -- Fairness Analysis")
    print("="*60)

    # 1. Load model bundle
    model, training_columns, income_bins = load_model(MODEL_PATH)

    # 2. Load and prepare dataset
    X, y, X_sample, y_sample = load_and_prepare_data(
        DATA_PATH, training_columns, income_bins
    )

    # 3. Compute SHAP values (~30 seconds)
    explainer, shap_values, base_val = compute_shap_values(model, X_sample)

    # 4. Generate all 4 plots and compute fairness gap
    gender_fairness_gap, mean_shap_by_gender = generate_plots(
        shap_values, X_sample, training_columns, base_val, model
    )

    # 5. Save raw SHAP values CSV for Fairlearn (Module 4)
    save_shap_csv(shap_values, training_columns, y_sample)

    # 6. Setup Gemini LLM
    llm = setup_gemini(GEMINI_API_KEY)

    # 7. Batch explain and save JSON
    output = batch_explain_and_save(
        X_sample, shap_values, training_columns,
        model, base_val, gender_fairness_gap, llm
    )

    # 8. Print sample output to verify
    print_sample_output(output)

    # -- Final summary -----------------------------------------------------
    print(f"\n{'='*60}")
    print("  ALL DONE -- Files produced:")
    print(f"{'='*60}")
    files = [
        ("shap_beeswarm.png",            "Global feature importance plot"),
        ("bias_gender_shap.png",         "Gender bias bar + violin plot"),
        ("bias_age_shap.png",            "Age vs SHAP scatter plot"),
        ("shap_waterfall_individual.png","Single-applicant waterfall plot"),
        ("shap_values.csv",              "Raw SHAP values → Fairlearn notebook"),
        ("llm_explanations.json",        "Gemini explanations → What-If simulator"),
    ]
    for filename, description in files:
        exists = "OK" if os.path.exists(filename) else "MISSING"
        print(f"  {exists}  {filename:<38} {description}")
    print()


if __name__ == "__main__":
    main()
