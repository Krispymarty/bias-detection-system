# ======================
# 1. Imports
# ======================
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
from xgboost import XGBClassifier


# ======================
# 2. Load Dataset
# ======================
df = pd.read_csv("application_train_cleaned.csv")


# ======================
# 3. Feature Selection
# ======================
features = [
    "CODE_GENDER", "CNT_CHILDREN", "CNT_FAM_MEMBERS", "NAME_EDUCATION_TYPE", "OCCUPATION_TYPE",
    "AMT_INCOME_TOTAL", "AMT_CREDIT", "AMT_ANNUITY", "AMT_GOODS_PRICE",
    "FLAG_OWN_CAR", "FLAG_OWN_REALTY",
    "EXT_SOURCE_1", "EXT_SOURCE_2", "EXT_SOURCE_3",
    "DAYS_BIRTH", "DAYS_EMPLOYED", "DAYS_REGISTRATION", "DAYS_ID_PUBLISH",
    "REGION_POPULATION_RELATIVE", "REGION_RATING_CLIENT", "REGION_RATING_CLIENT_W_CITY",
    "HOUR_APPR_PROCESS_START", "DAYS_LAST_PHONE_CHANGE",
    "OBS_30_CNT_SOCIAL_CIRCLE", "DEF_30_CNT_SOCIAL_CIRCLE"
]

# Keep only available columns
features = [f for f in features if f in df.columns]

X = df[features]
y = df["TARGET"]


# ======================
# 4. Preprocessing
# ======================
# Encode categorical variables
X = pd.get_dummies(X, drop_first=True)

# Fill missing values
X = X.fillna(X.median())


# ======================
# 5. Train-Test Split
# ======================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)


# ======================
# 6. Model Training
# ======================
model = XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric="logloss"
)

model.fit(X_train, y_train)


# ======================
# 7. Evaluation
# ======================
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("Accuracy:", accuracy_score(y_test, y_pred))
print("ROC-AUC:", roc_auc_score(y_test, y_prob))