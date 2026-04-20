import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
import warnings
warnings.filterwarnings('ignore')

pd.set_option('display.max_columns', None)
print("Libraries loaded.")

# Load and inspect 
bureau = pd.read_csv('bureau.csv')
print(f"Shape: {bureau.shape}")
print(f"Unique applicants: {bureau['SK_ID_CURR'].nunique()}")
print(f"\nMissing values (top 10):")
print((bureau.isnull().mean() * 100).sort_values(ascending=False).head(10))

# Clean bureau.csv 
# Step 1: Drop high-missing columns (>40% missing)
missing_pct = bureau.isnull().mean() * 100
cols_to_drop = missing_pct[missing_pct > 40].index.tolist()
bureau.drop(columns=cols_to_drop, inplace=True)
print(f"Dropped {len(cols_to_drop)} columns: {cols_to_drop}")

# Step 2: Fix DAYS columns — stored as negative, convert to positive
days_cols = [c for c in bureau.columns if 'DAYS' in c]
for col in days_cols:
    bureau[col] = bureau[col].abs()

# Step 3: Impute numeric columns with median
num_cols = bureau.select_dtypes(include=['float64', 'int64']).columns.tolist()
num_cols = [c for c in num_cols if c not in ['SK_ID_CURR', 'SK_ID_BUREAU']]
bureau[num_cols] = SimpleImputer(strategy='median').fit_transform(bureau[num_cols])

# Step 4: Impute categorical columns with mode
cat_cols = bureau.select_dtypes(include='object').columns.tolist()
if cat_cols:
    bureau[cat_cols] = SimpleImputer(strategy='most_frequent').fit_transform(bureau[cat_cols])

# Step 5: Encode categorical columns
bureau = pd.get_dummies(bureau, columns=cat_cols, drop_first=True)

print(f"\nCleaned bureau shape: {bureau.shape}")
print(f"Missing values remaining: {bureau.isnull().sum().sum()}")

# ── Cell 4: Aggregate bureau into ONE ROW per applicant ───────────────────
# We cannot merge bureau directly (multiple rows per SK_ID_CURR)
# We summarize each applicant's credit history into statistics

bureau_agg = bureau.groupby('SK_ID_CURR').agg(
    bureau_loan_count        = ('SK_ID_BUREAU', 'count'),
    bureau_days_credit_mean  = ('DAYS_CREDIT', 'mean'),
    bureau_days_credit_max   = ('DAYS_CREDIT', 'max'),
    bureau_credit_sum        = ('AMT_CREDIT_SUM', 'sum'),
    bureau_credit_mean       = ('AMT_CREDIT_SUM', 'mean'),
    bureau_debt_sum          = ('AMT_CREDIT_SUM_DEBT', 'sum'),
    bureau_overdue_mean      = ('AMT_CREDIT_SUM_OVERDUE', 'mean'),
    bureau_active_count      = ('CREDIT_ACTIVE_Active', 'sum')
                                    if 'CREDIT_ACTIVE_Active' in bureau.columns
                                    else ('SK_ID_BUREAU', 'count')
).reset_index()

# Rename to make clear these features come from bureau
bureau_agg.columns = ['SK_ID_CURR'] + [f'BUREAU_{c.upper()}' 
                       for c in bureau_agg.columns[1:]]

print(f"Bureau aggregated shape: {bureau_agg.shape}")
print(bureau_agg.head(3))

# **Dataset 2: bureau_balance.csv**
# This contains monthly status updates for each bureau loan (Active, Closed, DPD 1–30, etc.). It links to bureau.csv via SK_ID_BUREAU, not directly to the applicant.

# ── Cell 5: Load ──────────────────────────────────────────────────────────
bureau_bal = pd.read_csv('bureau_balance.csv')
print(f"Shape: {bureau_bal.shape}")
print(f"Unique bureau loans: {bureau_bal['SK_ID_BUREAU'].nunique()}")
print(f"\nSTATUS value counts:\n{bureau_bal['STATUS'].value_counts()}")

# ── Cell 6: Clean bureau_balance.csv ─────────────────────────────────────

# Step 1: Encode STATUS column
# C = Closed, X = unknown, 0 = no DPD, 1-5 = increasing overdue severity
bureau_bal['STATUS_ENCODED'] = bureau_bal['STATUS'].map(
    {'C': 0, 'X': -1, '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5}
).fillna(0)

# Step 2: Aggregate per SK_ID_BUREAU first
bureau_bal_agg = bureau_bal.groupby('SK_ID_BUREAU').agg(
    bureau_bal_months        = ('MONTHS_BALANCE', 'count'),
    bureau_bal_status_mean   = ('STATUS_ENCODED', 'mean'),
    bureau_bal_status_max    = ('STATUS_ENCODED', 'max'),
    bureau_bal_dpd_count     = ('STATUS_ENCODED', lambda x: (x > 0).sum())
).reset_index()

# Step 3: Now join back to bureau on SK_ID_BUREAU, then re-aggregate by SK_ID_CURR
bureau_with_bal = bureau[['SK_ID_CURR', 'SK_ID_BUREAU']].merge(
    bureau_bal_agg, on='SK_ID_BUREAU', how='left'
)

bureau_bal_final = bureau_with_bal.groupby('SK_ID_CURR').agg(
    bbal_months_mean     = ('bureau_bal_months', 'mean'),
    bbal_status_mean     = ('bureau_bal_status_mean', 'mean'),
    bbal_max_dpd         = ('bureau_bal_status_max', 'max'),
    bbal_total_dpd_count = ('bureau_bal_dpd_count', 'sum')
).reset_index()

bureau_bal_final.columns = ['SK_ID_CURR'] + [f'BBAL_{c.upper()}' 
                             for c in bureau_bal_final.columns[1:]]

print(f"Bureau balance aggregated shape: {bureau_bal_final.shape}")

# **Dataset 3: previous_application.csv**
# Every past loan application made to Home Credit by the same applicant — whether approved, refused, or cancelled. One applicant can have many past applications.

# ── Cell 7: Load ──────────────────────────────────────────────────────────
prev = pd.read_csv('previous_application.csv')
print(f"Shape: {prev.shape}")
print(f"Unique applicants: {prev['SK_ID_CURR'].nunique()}")
print(f"\nMissing % (top 10):")
print((prev.isnull().mean() * 100).sort_values(ascending=False).head(10))

# ── Cell 8: Clean previous_application.csv ───────────────────────────────

# Step 1: Drop >40% missing columns
missing_pct = prev.isnull().mean() * 100
cols_to_drop = missing_pct[missing_pct > 40].index.tolist()
prev.drop(columns=cols_to_drop, inplace=True)
print(f"Dropped {len(cols_to_drop)} columns with >40% missing")
print(f"Shape after drop: {prev.shape}")

# Step 2: Fix known anomaly — safe version (columns may have been dropped above)
sentinel_cols = [
    'DAYS_FIRST_DRAWING',
    'DAYS_FIRST_DUE',
    'DAYS_LAST_DUE_1ST_VERSION',
    'DAYS_LAST_DUE',
    'DAYS_TERMINATION'
]
existing_sentinel_cols = [c for c in sentinel_cols if c in prev.columns]
print(f"\nSentinel columns still present: {existing_sentinel_cols}")

if existing_sentinel_cols:
    prev[existing_sentinel_cols] = prev[existing_sentinel_cols].replace(365243, np.nan)
    print("365243 anomaly replaced with NaN in surviving columns")
else:
    print("All sentinel columns were dropped in Step 1 — nothing to fix")

# Step 3: Convert DAYS columns to positive
days_cols = [c for c in prev.columns if 'DAYS' in c]
for col in days_cols:
    prev[col] = prev[col].abs()
print(f"\nConverted {len(days_cols)} DAYS columns to positive")

# Step 4: Create useful ratio features before aggregating
if 'AMT_APPLICATION' in prev.columns and 'AMT_CREDIT' in prev.columns:
    prev['APP_CREDIT_RATIO'] = prev['AMT_APPLICATION'] / (prev['AMT_CREDIT'] + 1)
    print("Created APP_CREDIT_RATIO")

if 'AMT_DOWN_PAYMENT' in prev.columns and 'AMT_CREDIT' in prev.columns:
    prev['DOWN_PAYMENT_RATIO'] = prev['AMT_DOWN_PAYMENT'] / (prev['AMT_CREDIT'] + 1)
    print("Created DOWN_PAYMENT_RATIO")

# Step 5: Impute numeric columns with median
num_cols = prev.select_dtypes(include=['float64', 'int64']).columns
num_cols = [c for c in num_cols if c not in ['SK_ID_CURR', 'SK_ID_PREV']]

for col in num_cols:
    prev[col] = prev[col].fillna(prev[col].median())

print(f"\nImputed {len(num_cols)} numeric columns with median")
print(f"Numeric missing values remaining: {prev[num_cols].isnull().sum().sum()}")

# Step 6: Impute + encode categorical columns
cat_cols = prev.select_dtypes(include='object').columns.tolist()

if cat_cols:
    # Impute with most frequent
    for col in cat_cols:
        prev[col] = prev[col].fillna(prev[col].mode()[0])

    # Split by cardinality
    low_card  = [c for c in cat_cols if prev[c].nunique() <= 6]
    high_card = [c for c in cat_cols if prev[c].nunique() > 6]

    print(f"\nCategorical columns: {len(cat_cols)} total")
    print(f"  One-hot encoding {len(low_card)} low-cardinality columns")
    print(f"  Label encoding   {len(high_card)} high-cardinality columns")

    # One-hot encode low cardinality
    if low_card:
        prev = pd.get_dummies(prev, columns=low_card, drop_first=True)

    # Label encode high cardinality
    if high_card:
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        for col in high_card:
            prev[col] = le.fit_transform(prev[col].astype(str))
else:
    print("\nNo categorical columns found")

print(f"\nCleaned previous_application shape: {prev.shape}")
print(f"Total missing values remaining: {prev.isnull().sum().sum()}")

# ── Cell 9: Aggregate previous_application ───────────────────────────────

# Build agg dict safely — only include columns that actually exist
agg_dict = {}

if 'SK_ID_PREV' in prev.columns:
    agg_dict['prev_app_count'] = ('SK_ID_PREV', 'count')

if 'AMT_CREDIT' in prev.columns:
    agg_dict['prev_credit_sum']  = ('AMT_CREDIT', 'sum')
    agg_dict['prev_credit_mean'] = ('AMT_CREDIT', 'mean')

if 'AMT_ANNUITY' in prev.columns:
    agg_dict['prev_annuity_mean'] = ('AMT_ANNUITY', 'mean')

if 'DAYS_DECISION' in prev.columns:
    agg_dict['prev_days_decision_mean'] = ('DAYS_DECISION', 'mean')

if 'APP_CREDIT_RATIO' in prev.columns:
    agg_dict['prev_app_credit_ratio'] = ('APP_CREDIT_RATIO', 'mean')

if 'DOWN_PAYMENT_RATIO' in prev.columns:
    agg_dict['prev_down_payment_ratio'] = ('DOWN_PAYMENT_RATIO', 'mean')

print(f"Aggregating {len(agg_dict)} features: {list(agg_dict.keys())}")

# Run aggregation
prev_agg = prev.groupby('SK_ID_CURR').agg(**agg_dict).reset_index()

# Add approved/refused counts if those columns exist
if 'NAME_CONTRACT_STATUS_Approved' in prev.columns:
    status_dict = {
        'prev_approved_count': ('NAME_CONTRACT_STATUS_Approved', 'sum')
    }
    if 'NAME_CONTRACT_STATUS_Refused' in prev.columns:
        status_dict['prev_refused_count'] = ('NAME_CONTRACT_STATUS_Refused', 'sum')

    status_agg = prev.groupby('SK_ID_CURR').agg(**status_dict).reset_index()
    prev_agg = prev_agg.merge(status_agg, on='SK_ID_CURR', how='left')
    print(f"Added approval/refusal counts")

# Rename all columns with PREV_ prefix
prev_agg.columns = ['SK_ID_CURR'] + [
    f'PREV_{c.upper()}' for c in prev_agg.columns[1:]
]

print(f"\nPrevious application aggregated shape: {prev_agg.shape}")
print(prev_agg.head(3))

# **Datasets 4, 5, 6: POS_CASH, installments, credit_card**
# These three all link to previous_application via SK_ID_PREV. The cleaning pattern is identical for all three — load, fix, aggregate twice (first by SK_ID_PREV, then by SK_ID_CURR).

# ── Cell 10: Clean and aggregate POS_CASH_balance.csv ────────────────────
pos = pd.read_csv('POS_CASH_balance.csv')
print(f"POS_CASH shape: {pos.shape}")

# Impute
num_cols = pos.select_dtypes(include=['float64','int64']).columns
num_cols = [c for c in num_cols if c not in ['SK_ID_CURR','SK_ID_PREV']]
pos[num_cols] = SimpleImputer(strategy='median').fit_transform(pos[num_cols])

cat_cols = pos.select_dtypes(include='object').columns.tolist()
if cat_cols:
    pos[cat_cols] = SimpleImputer(strategy='most_frequent').fit_transform(pos[cat_cols])
    pos = pd.get_dummies(pos, columns=cat_cols, drop_first=True)

# Aggregate by SK_ID_CURR directly (SK_ID_CURR exists in this table)
pos_agg = pos.groupby('SK_ID_CURR').agg(
    pos_months_count         = ('MONTHS_BALANCE', 'count'),
    pos_instalment_mean      = ('CNT_INSTALMENT', 'mean'),
    pos_instalment_future_mean = ('CNT_INSTALMENT_FUTURE', 'mean'),
    pos_sk_dpd_mean          = ('SK_DPD', 'mean'),
    pos_sk_dpd_max           = ('SK_DPD', 'max'),
    pos_sk_dpd_def_mean      = ('SK_DPD_DEF', 'mean')
).reset_index()

pos_agg.columns = ['SK_ID_CURR'] + [f'POS_{c.upper()}' 
                   for c in pos_agg.columns[1:]]

print(f"POS aggregated shape: {pos_agg.shape}")

# ── Cell 11: Clean and aggregate installments_payments.csv ───────────────
inst = pd.read_csv('installments_payments.csv')
print(f"Installments shape: {inst.shape}")

# Create payment behavior features before aggregating
inst['PAYMENT_DIFF']  = inst['AMT_INSTALMENT'] - inst['AMT_PAYMENT']
inst['PAYMENT_RATIO'] = inst['AMT_PAYMENT'] / (inst['AMT_INSTALMENT'] + 1)
inst['DAYS_PAST_DUE'] = inst['DAYS_ENTRY_PAYMENT'] - inst['DAYS_INSTALMENT']
inst['DAYS_PAST_DUE'] = inst['DAYS_PAST_DUE'].clip(lower=0)

# Impute
num_cols = inst.select_dtypes(include=['float64','int64']).columns
num_cols = [c for c in num_cols if c not in ['SK_ID_CURR','SK_ID_PREV']]
inst[num_cols] = SimpleImputer(strategy='median').fit_transform(inst[num_cols])

# Aggregate
inst_agg = inst.groupby('SK_ID_CURR').agg(
    inst_count               = ('SK_ID_PREV', 'count'),
    inst_payment_diff_mean   = ('PAYMENT_DIFF', 'mean'),
    inst_payment_diff_max    = ('PAYMENT_DIFF', 'max'),
    inst_payment_ratio_mean  = ('PAYMENT_RATIO', 'mean'),
    inst_days_past_due_mean  = ('DAYS_PAST_DUE', 'mean'),
    inst_days_past_due_max   = ('DAYS_PAST_DUE', 'max'),
    inst_late_payment_count  = ('DAYS_PAST_DUE', lambda x: (x > 0).sum())
).reset_index()

inst_agg.columns = ['SK_ID_CURR'] + [f'INST_{c.upper()}' 
                    for c in inst_agg.columns[1:]]

print(f"Installments aggregated shape: {inst_agg.shape}")

# ── Cell 12: Clean and aggregate credit_card_balance.csv ─────────────────

cc = pd.read_csv('credit_card_balance.csv')
print(f"Credit card shape: {cc.shape}")

# Drop very high missing columns
missing_pct = cc.isnull().mean() * 100
cols_to_drop = missing_pct[missing_pct > 40].index.tolist()
cc.drop(columns=cols_to_drop, inplace=True)
print(f"Dropped {len(cols_to_drop)} columns: {cols_to_drop}")
print(f"Shape after drop: {cc.shape}")

# Utilization ratio — key credit signal (only if both columns survived)
if 'AMT_BALANCE' in cc.columns and 'AMT_CREDIT_LIMIT_ACTUAL' in cc.columns:
    cc['CREDIT_UTILIZATION'] = cc['AMT_BALANCE'] / (cc['AMT_CREDIT_LIMIT_ACTUAL'] + 1)
    print("Created CREDIT_UTILIZATION")
else:
    print("Skipped CREDIT_UTILIZATION — source columns missing")

# Impute numeric
num_cols = cc.select_dtypes(include=['float64', 'int64']).columns
num_cols = [c for c in num_cols if c not in ['SK_ID_CURR', 'SK_ID_PREV']]
for col in num_cols:
    cc[col] = cc[col].fillna(cc[col].median())
print(f"Imputed {len(num_cols)} numeric columns")

# Impute + encode categorical
cat_cols = cc.select_dtypes(include='object').columns.tolist()
if cat_cols:
    for col in cat_cols:
        cc[col] = cc[col].fillna(cc[col].mode()[0])
    cc = pd.get_dummies(cc, columns=cat_cols, drop_first=True)
    print(f"Encoded {len(cat_cols)} categorical columns")

# Build agg_dict safely — only include columns that still exist
agg_dict = {}

if 'MONTHS_BALANCE' in cc.columns:
    agg_dict['cc_months_count'] = ('MONTHS_BALANCE', 'count')

if 'AMT_BALANCE' in cc.columns:
    agg_dict['cc_balance_mean'] = ('AMT_BALANCE', 'mean')
    agg_dict['cc_balance_max']  = ('AMT_BALANCE', 'max')

if 'AMT_DRAWINGS_TOTAL' in cc.columns:
    agg_dict['cc_drawings_mean'] = ('AMT_DRAWINGS_TOTAL', 'mean')
else:
    print("Skipped cc_drawings_mean — AMT_DRAWINGS_TOTAL was dropped")

if 'SK_DPD' in cc.columns:
    agg_dict['cc_dpd_mean'] = ('SK_DPD', 'mean')
    agg_dict['cc_dpd_max']  = ('SK_DPD', 'max')

if 'CREDIT_UTILIZATION' in cc.columns:
    agg_dict['cc_utilization_mean'] = ('CREDIT_UTILIZATION', 'mean')
    agg_dict['cc_utilization_max']  = ('CREDIT_UTILIZATION', 'max')

print(f"\nAggregating {len(agg_dict)} features: {list(agg_dict.keys())}")

# Run aggregation
cc_agg = cc.groupby('SK_ID_CURR').agg(**agg_dict).reset_index()

# Rename with CC_ prefix
cc_agg.columns = ['SK_ID_CURR'] + [
    f'CC_{c.upper()}' for c in cc_agg.columns[1:]
]

print(f"\nCredit card aggregated shape: {cc_agg.shape}")
print(cc_agg.head(3))

# Final Step — Load Your Cleaned Train + Merge Everything

# ── Cell 13: Load your already-cleaned application_train ─────────────────

import os

# First let's see where Python is currently looking
print(f"Current working directory: {os.getcwd()}")

# Your file is here — use the full path
file_path = 'application_train_cleaned.csv'

# Verify the file actually exists before loading
if os.path.exists(file_path):
    df_train = pd.read_csv(file_path)
    print(f"File found and loaded successfully")
    print(f"Base training data shape: {df_train.shape}")
else:
    print(f"File NOT found at: {file_path}")
    print("\nSearching for it on your Desktop...")
    
    # Auto-search to help you find it
    search_root = r'C:\Users\jaina\Desktop'
    for root, dirs, files in os.walk(search_root):
        for file in files:
            if file == 'application_train_cleaned.csv':
                print(f"Found at: {os.path.join(root, file)}")

# ── Cell 14: Merge all aggregated tables one by one ───────────────────────

df_final = df_train.copy()

# Each merge is a LEFT join — if an applicant has no bureau history,
# they just get NaN for all BUREAU_ columns (which we'll impute below)

df_final = df_final.merge(bureau_agg,      on='SK_ID_CURR', how='left')
print(f"After bureau merge:      {df_final.shape}")

df_final = df_final.merge(bureau_bal_final, on='SK_ID_CURR', how='left')
print(f"After bureau_bal merge:  {df_final.shape}")

df_final = df_final.merge(prev_agg,         on='SK_ID_CURR', how='left')
print(f"After prev_app merge:    {df_final.shape}")

df_final = df_final.merge(pos_agg,          on='SK_ID_CURR', how='left')
print(f"After POS merge:         {df_final.shape}")

df_final = df_final.merge(inst_agg,         on='SK_ID_CURR', how='left')
print(f"After installments merge:{df_final.shape}")

df_final = df_final.merge(cc_agg,           on='SK_ID_CURR', how='left')
print(f"After credit card merge: {df_final.shape}")

# ── Cell 15: Final imputation pass for new NaNs from the joins ───────────
# Some applicants won't have records in every table — those get NaN after merge
# Fill with 0 for count columns, median for everything else

count_cols = [c for c in df_final.columns if 'COUNT' in c or 'count' in c]
df_final[count_cols] = df_final[count_cols].fillna(0)

# Impute remaining NaNs with median
num_cols = df_final.select_dtypes(include=['float64','int64']).columns.tolist()
num_cols = [c for c in num_cols if c != 'TARGET']
df_final[num_cols] = SimpleImputer(strategy='median').fit_transform(df_final[num_cols])

print(f"\nFinal missing values: {df_final.isnull().sum().sum()}")
print(f"Final shape:          {df_final.shape}")

# ── Cell 16: Save ─────────────────────────────────────────────────────────
df_final.to_csv('final_merged_cleaned.csv', index=False)
print("Saved as final_merged_cleaned.csv")
print(f"\nRows:    {df_final.shape[0]:,}")
print(f"Columns: {df_final.shape[1]:,}")
print(f"TARGET distribution:\n{df_final['TARGET'].value_counts()}")
