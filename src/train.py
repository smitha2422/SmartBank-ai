"""
SmartBank AI - Machine Learning Pipeline
Pre-Contact Term Deposit Subscription Prediction & Campaign Intelligence

This pipeline performs:
1. Leakage-safe data loading & inspection
2. EDA summary extraction
3. Stratified 3-way split (Train 64%, Validation 16%, Unseen Test 20%)
4. Scikit-learn ColumnTransformer preprocessing pipeline (fitted ONLY on train)
5. Class-imbalance handling with class_weight='balanced'
6. Model training: Logistic Regression (Baseline) vs Random Forest (Ensemble)
7. Model selection based on Validation F1-score & ROC-AUC
8. Final evaluation on unseen Test set
9. Feature importance / predictive signal analysis
10. Artifact generation (metrics, visual plots, and saved pipeline)
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Ensure UTF-8 output encoding for Windows compatibility
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    roc_curve
)

# Set styling for plots
sns.set_theme(style="whitegrid")
plt.rcParams.update({'font.sans-serif': 'DejaVu Sans', 'font.size': 11})

DATA_PATH = os.path.join("data", "bank-full.csv")
OUTPUTS_DIR = "outputs"
MODELS_DIR = "models"

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

# -------------------------------------------------------------
# STEP 1: READ DATA & INSPECTION
# -------------------------------------------------------------
def load_and_inspect_data(filepath):
    print("=" * 70)
    print(">> SMARTBANK AI: MACHINE LEARNING TRAINING PIPELINE")
    print("=" * 70)
    print(f"\n[1/7] Loading dataset from '{filepath}'...")
    
    # UCI Bank Marketing dataset is semicolon-delimited
    df = pd.read_csv(filepath, sep=";")
    rows, cols = df.shape
    print(f"      Rows: {rows:,}")
    print(f"      Columns: {cols}")
    
    # Check for duplicates & missing values
    duplicates = int(df.duplicated().sum())
    missing_vals = int(df.isnull().sum().sum())
    print(f"      Duplicate records: {duplicates}")
    print(f"      Missing values (NaN): {missing_vals}")
    
    # Target distribution
    target_counts = df['y'].value_counts().to_dict()
    target_pct = (df['y'].value_counts(normalize=True) * 100).to_dict()
    print("\n      Target distribution ('y'):")
    for k, v in target_counts.items():
        print(f"        - {k:>3}: {v:>6,} ({target_pct[k]:.2f}%)")
        
    eda_summary = {
        "dataset_name": "UCI Bank Marketing (bank-full.csv)",
        "rows": rows,
        "columns": cols,
        "duplicate_rows": duplicates,
        "missing_values_total": missing_vals,
        "target_distribution": {
            "counts": {str(k): int(v) for k, v in target_counts.items()},
            "percentages": {str(k): round(float(v), 2) for k, v in target_pct.items()}
        },
        "all_columns": list(df.columns)
    }
    
    with open(os.path.join(OUTPUTS_DIR, "eda_summary.json"), "w", encoding="utf-8") as f:
        json.dump(eda_summary, f, indent=4)
        
    print(f"      Saved EDA summary to '{OUTPUTS_DIR}/eda_summary.json'")
    return df, eda_summary

# -------------------------------------------------------------
# STEP 2: LEAKAGE-SAFE FEATURE SELECTION
# -------------------------------------------------------------
def prepare_features(df):
    print("\n[2/7] Applying Pre-Contact Leakage-Safe Feature Selection...")
    
    # Exclude post-contact & in-campaign leakage variables:
    # - duration: call duration (unknown prior to call)
    # - contact: communication type of current contact
    # - day, month: timing of the contact
    # - campaign: number of contacts performed during current campaign
    
    LEAKAGE_COLUMNS = ['contact', 'day', 'month', 'duration', 'campaign', 'pdays']
    dropped_cols = [c for c in LEAKAGE_COLUMNS if c in df.columns]
    print(f"      Excluded leakage features: {dropped_cols}")
    
    CATEGORICAL_FEATURES = ['job', 'marital', 'education', 'default', 'housing', 'loan', 'poutcome']
    NUMERICAL_FEATURES = ['age', 'balance', 'previous']
    
    # Verify presence
    for col in CATEGORICAL_FEATURES + NUMERICAL_FEATURES:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' missing from dataset!")
            
    X = df[CATEGORICAL_FEATURES + NUMERICAL_FEATURES].copy()
    y = (df['y'] == 'yes').astype(int) # Binary encoding: 1 for 'yes' (subscribed), 0 for 'no'
    
    print(f"      Active features ({len(X.columns)} total):")
    print(f"        - Categorical ({len(CATEGORICAL_FEATURES)}): {CATEGORICAL_FEATURES}")
    print(f"        - Numerical ({len(NUMERICAL_FEATURES)}):   {NUMERICAL_FEATURES}")
    
    return X, y, CATEGORICAL_FEATURES, NUMERICAL_FEATURES

# -------------------------------------------------------------
# STEP 3: TRAIN / VALIDATION / TEST SPLIT
# -------------------------------------------------------------
def split_data(X, y):
    print("\n[3/7] Performing 3-Way Stratified Data Splitting...")
    
    # 80% Development Data, 20% Final Unseen Test Data
    X_dev, X_test, y_dev, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    # From Development Data: 80% Train (64% overall), 20% Validation (16% overall)
    X_train, X_val, y_train, y_val = train_test_split(
        X_dev, y_dev, test_size=0.20, random_state=42, stratify=y_dev
    )
    
    print(f"      Train Set:      {len(X_train):>6,} records ({len(X_train)/len(X)*100:.1f}%) | Positives: {y_train.sum():,}")
    print(f"      Validation Set: {len(X_val):>6,} records ({len(X_val)/len(X)*100:.1f}%) | Positives: {y_val.sum():,}")
    print(f"      Final Test Set: {len(X_test):>6,} records ({len(X_test)/len(X)*100:.1f}%) | Positives: {y_test.sum():,}")
    print("      Note: Final Test Set is strictly isolated from model selection & preprocessing fit.")
    
    return X_dev, y_dev, X_train, y_train, X_val, y_val, X_test, y_test

# -------------------------------------------------------------
# STEP 4: PREPROCESSING & PIPELINE DEFINITION
# -------------------------------------------------------------
def build_preprocessor(cat_features, num_features):
    num_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    cat_transformer = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('ohe', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(transformers=[
        ('num', num_transformer, num_features),
        ('cat', cat_transformer, cat_features)
    ])
    
    return preprocessor

# -------------------------------------------------------------
# STEP 5: MODEL TRAINING & VALIDATION COMPARISON
# -------------------------------------------------------------
def evaluate_model(pipeline, X_eval, y_eval, model_name="Model"):
    y_pred = pipeline.predict(X_eval)
    y_prob = pipeline.predict_proba(X_eval)[:, 1]
    
    acc = accuracy_score(y_eval, y_pred)
    prec = precision_score(y_eval, y_pred, zero_division=0)
    rec = recall_score(y_eval, y_pred, zero_division=0)
    f1 = f1_score(y_eval, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_eval, y_prob)
    cm = confusion_matrix(y_eval, y_pred).tolist()
    
    return {
        "model_name": model_name,
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4),
        "confusion_matrix": cm,
        "y_prob": y_prob,
        "y_pred": y_pred
    }

def train_and_compare_models(X_train, y_train, X_val, y_val, cat_features, num_features):
    print("\n[4/7] Training & Comparing Models on Validation Set...")
    
    # Model 1: Logistic Regression (Interpretable Baseline)
    preprocessor_lr = build_preprocessor(cat_features, num_features)
    lr_pipeline = Pipeline([
        ('preprocessor', preprocessor_lr),
        ('classifier', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    print("      Training Logistic Regression (class_weight='balanced')...")
    lr_pipeline.fit(X_train, y_train)
    lr_val_metrics = evaluate_model(lr_pipeline, X_val, y_val, "Logistic Regression")
    
    # Model 2: Random Forest (Non-linear Ensemble)
    preprocessor_rf = build_preprocessor(cat_features, num_features)
    rf_pipeline = Pipeline([
        ('preprocessor', preprocessor_rf),
        ('classifier', RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=10,
            class_weight='balanced',
            random_state=42,
            n_jobs=-1
        ))
    ])
    
    print("      Training Random Forest (class_weight='balanced')...")
    rf_pipeline.fit(X_train, y_train)
    rf_val_metrics = evaluate_model(rf_pipeline, X_val, y_val, "Random Forest")
    
    # Comparison table
    print("\n" + "-" * 65)
    print(f"{'Metric':<18} | {'Logistic Regression':<20} | {'Random Forest':<20}")
    print("-" * 65)
    for m in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
        print(f"{m.upper():<18} | {lr_val_metrics[m]:<20.4f} | {rf_val_metrics[m]:<20.4f}")
    print("-" * 65)
    
    # Model selection based on F1 and ROC-AUC
    if (rf_val_metrics['f1'] + rf_val_metrics['roc_auc']) >= (lr_val_metrics['f1'] + lr_val_metrics['roc_auc']):
        selected_model_name = "Random Forest"
    else:
        selected_model_name = "Logistic Regression"
        
    print(f"\n      >> Selected Best Model: {selected_model_name} (Prioritizing F1 & ROC-AUC for positive class)")
    
    # Save Model Comparison Chart
    plot_model_comparison(lr_val_metrics, rf_val_metrics)
    
    return selected_model_name, lr_val_metrics, rf_val_metrics

def plot_model_comparison(lr_m, rf_m):
    metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC']
    lr_vals = [lr_m['accuracy'], lr_m['precision'], lr_m['recall'], lr_m['f1'], lr_m['roc_auc']]
    rf_vals = [rf_m['accuracy'], rf_m['precision'], rf_m['recall'], rf_m['f1'], rf_m['roc_auc']]
    
    x = np.arange(len(metrics_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    rects1 = ax.bar(x - width/2, lr_vals, width, label='Logistic Regression', color='#3b82f6', alpha=0.9)
    rects2 = ax.bar(x + width/2, rf_vals, width, label='Random Forest', color='#10b981', alpha=0.9)
    
    ax.set_ylabel('Score (0 to 1)')
    ax.set_title('Validation Performance Comparison (Leakage-Safe Pre-Contact)', fontsize=13, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names, fontweight='medium')
    ax.set_ylim(0, 1.05)
    ax.legend(loc='lower right', frameon=True)
    
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f'{h:.2f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f'{h:.2f}', xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9)
                    
    plt.tight_layout()
    comp_path = os.path.join(OUTPUTS_DIR, "model_comparison.png")
    plt.savefig(comp_path)
    plt.close()
    print(f"      Saved model comparison chart to '{comp_path}'")

# -------------------------------------------------------------
# STEP 6: REFIT ON FULL DEVELOPMENT DATA & UNSEEN TEST EVALUATION
# -------------------------------------------------------------
def refit_and_evaluate_test(selected_model_name, X_dev, y_dev, X_test, y_test, cat_features, num_features):
    print(f"\n[5/7] Refitting winning pipeline ({selected_model_name}) on full Development Data (80%)...")
    
    preprocessor = build_preprocessor(cat_features, num_features)
    if selected_model_name == "Random Forest":
        best_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier(
                n_estimators=150,
                max_depth=12,
                min_samples_split=10,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            ))
        ])
    else:
        best_pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
        ])
        
    best_pipeline.fit(X_dev, y_dev)
    
    print("\n[6/7] Evaluating Final Pipeline on 20% Unseen Test Set...")
    test_metrics = evaluate_model(best_pipeline, X_test, y_test, selected_model_name)
    
    print(f"      Test Accuracy:  {test_metrics['accuracy']:.4f}")
    print(f"      Test Precision: {test_metrics['precision']:.4f}")
    print(f"      Test Recall:    {test_metrics['recall']:.4f}")
    print(f"      Test F1-Score:  {test_metrics['f1']:.4f}")
    print(f"      Test ROC-AUC:   {test_metrics['roc_auc']:.4f}")
    
    cm = np.array(test_metrics['confusion_matrix'])
    print(f"\n      Confusion Matrix (Test Set):")
    print(f"        TN: {cm[0, 0]:>5,}  |  FP: {cm[0, 1]:>5,}")
    print(f"        FN: {cm[1, 0]:>5,}  |  TP: {cm[1, 1]:>5,}")
    
    # Save Pipeline
    model_save_path = os.path.join(MODELS_DIR, "best_pipeline.joblib")
    joblib.dump(best_pipeline, model_save_path)
    print(f"\n      Saved complete end-to-end pipeline to '{model_save_path}'")
    
    # Save test visual plots
    plot_confusion_matrix(cm)
    plot_roc_curve(y_test, test_metrics['y_prob'], test_metrics['roc_auc'])
    
    return best_pipeline, test_metrics

def plot_confusion_matrix(cm):
    fig, ax = plt.subplots(figsize=(6, 5), dpi=300)
    sns.heatmap(
        cm, annot=True, fmt=',d', cmap='Blues', cbar=False,
        xticklabels=['Predicted No', 'Predicted Yes'],
        yticklabels=['Actual No', 'Actual Yes'],
        ax=ax, annot_kws={"size": 14, "fontweight": "bold"}
    )
    ax.set_title('Test Set Confusion Matrix', fontsize=12, fontweight='bold', pad=12)
    plt.tight_layout()
    cm_path = os.path.join(OUTPUTS_DIR, "confusion_matrix.png")
    plt.savefig(cm_path)
    plt.close()
    print(f"      Saved confusion matrix plot to '{cm_path}'")

def plot_roc_curve(y_true, y_prob, auc_score):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(6.5, 5), dpi=300)
    ax.plot(fpr, tpr, color='#2563eb', lw=2.5, label=f'ROC Curve (AUC = {auc_score:.4f})')
    ax.plot([0, 1], [0, 1], color='#94a3b8', lw=1.5, linestyle='--', label='Random Chance (AUC = 0.50)')
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate (1 - Specificity)', fontweight='medium')
    ax.set_ylabel('True Positive Rate (Sensitivity / Recall)', fontweight='medium')
    ax.set_title('Test ROC-AUC Curve', fontsize=12, fontweight='bold', pad=12)
    ax.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    roc_path = os.path.join(OUTPUTS_DIR, "roc_curve.png")
    plt.savefig(roc_path)
    plt.close()
    print(f"      Saved ROC curve plot to '{roc_path}'")

# -------------------------------------------------------------
# STEP 7: FEATURE IMPORTANCE / PREDICTIVE SIGNALS & SAMPLES
# -------------------------------------------------------------
def extract_feature_importance(pipeline, cat_features, num_features, selected_model_name):
    print("\n[7/7] Extracting Predictive Signals & Sample Records...")
    
    preprocessor = pipeline.named_steps['preprocessor']
    classifier = pipeline.named_steps['classifier']
    
    # Extract transformed feature names
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['ohe']
    cat_names = cat_encoder.get_feature_names_out(cat_features).tolist()
    all_feature_names = num_features + cat_names
    
    feature_importance_list = []
    if hasattr(classifier, 'feature_importances_'):
        importances = classifier.feature_importances_
        for name, val in zip(all_feature_names, importances):
            feature_importance_list.append({"feature": name, "importance": round(float(val), 5)})
        feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)
    elif hasattr(classifier, 'coef_'):
        coefs = classifier.coef_[0]
        for name, val in zip(all_feature_names, coefs):
            feature_importance_list.append({"feature": name, "coefficient": round(float(val), 5), "importance": round(float(abs(val)), 5)})
        feature_importance_list.sort(key=lambda x: x["importance"], reverse=True)
        
    fi_data = {
        "model_type": selected_model_name,
        "interpretability_notice": "Features represent predictive associations in the model, not causal drivers.",
        "top_features": feature_importance_list[:15],
        "all_features": feature_importance_list
    }
    
    fi_path = os.path.join(OUTPUTS_DIR, "feature_importance.json")
    with open(fi_path, "w", encoding="utf-8") as f:
        json.dump(fi_data, f, indent=4)
    print(f"      Saved top {len(feature_importance_list[:15])} predictive signals to '{fi_path}'")
    
    print("\n      Top 5 Predictive Signals:")
    for i, item in enumerate(feature_importance_list[:5], 1):
        metric_str = f"imp={item.get('importance', 0):.4f}"
        if "coefficient" in item:
            metric_str += f", coef={item['coefficient']:+.4f}"
        print(f"        {i}. {item['feature']:<30} ({metric_str})")
        
    return fi_data

def generate_sample_test_records(pipeline, X_test, y_test):
    pos_idx = y_test[y_test == 1].index[:5]
    neg_idx = y_test[y_test == 0].index[:5]
    sample_indices = list(pos_idx) + list(neg_idx)
    
    samples_df = X_test.loc[sample_indices].copy()
    samples_df['actual_subscribed'] = y_test.loc[sample_indices].values
    
    probs = pipeline.predict_proba(samples_df.drop(columns=['actual_subscribed']))[:, 1]
    samples_df['predicted_probability'] = np.round(probs, 4)
    samples_df['opportunity_score'] = np.round(probs * 100, 1)
    samples_df['campaign_priority'] = pd.cut(
        samples_df['opportunity_score'],
        bins=[-1, 40, 70, 100],
        labels=['LOW', 'MEDIUM', 'HIGH']
    )
    
    sample_path = os.path.join(OUTPUTS_DIR, "sample_test_records.csv")
    samples_df.to_csv(sample_path, index=False)
    print(f"      Saved sample test demonstrations to '{sample_path}'")

# -------------------------------------------------------------
# MAIN EXECUTION ORCHESTRATION
# -------------------------------------------------------------
def main():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Missing '{DATA_PATH}'. Please ensure bank-full.csv is in 'data/' folder.")
        
    df, eda_summary = load_and_inspect_data(DATA_PATH)
    X, y, cat_features, num_features = prepare_features(df)
    X_dev, y_dev, X_train, y_train, X_val, y_val, X_test, y_test = split_data(X, y)
    
    selected_model_name, lr_val_m, rf_val_m = train_and_compare_models(
        X_train, y_train, X_val, y_val, cat_features, num_features
    )
    
    best_pipeline, test_m = refit_and_evaluate_test(
        selected_model_name, X_dev, y_dev, X_test, y_test, cat_features, num_features
    )
    
    fi_data = extract_feature_importance(best_pipeline, cat_features, num_features, selected_model_name)
    generate_sample_test_records(best_pipeline, X_test, y_test)
    
    # Save overall metrics.json
    all_metrics = {
        "validation_comparison": {
            "logistic_regression": {k: v for k, v in lr_val_m.items() if k not in ['y_prob', 'y_pred']},
            "random_forest": {k: v for k, v in rf_val_m.items() if k not in ['y_prob', 'y_pred']}
        },
        "selected_model": selected_model_name,
        "selection_rationale": "Selected based primarily on Validation F1-score & ROC-AUC for minority positive class detection.",
        "unseen_test_performance": {k: v for k, v in test_m.items() if k not in ['y_prob', 'y_pred']}
    }
    
    metrics_path = os.path.join(OUTPUTS_DIR, "metrics.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=4)
        
    print("\n" + "=" * 70)
    print(">> PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print(f"   Outputs generated in '{OUTPUTS_DIR}/'")
    print(f"   Saved Model: '{MODELS_DIR}/best_pipeline.joblib'")
    print("=" * 70)

if __name__ == "__main__":
    main()
