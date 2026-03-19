import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt
import seaborn as sns
from xgboost import XGBRegressor
import joblib
import os

# -----------------------------
# Plotting functions
# -----------------------------
def plot_predictions(y_true, y_pred, model_name):
    plt.figure(figsize=(6,6))
    sns.scatterplot(x=y_true, y=y_pred, alpha=0.7)
    plt.plot([y_true.min(), y_true.max()],
             [y_true.min(), y_true.max()],
             'r--', lw=2)
    plt.xlabel("Actual Salary")
    plt.ylabel("Predicted Salary")
    plt.title(f"Predicted vs Actual - {model_name}")
    plt.tight_layout()
    plt.show()

def plot_feature_importance(model, feature_names):
    importance = model.feature_importances_
    sorted_idx = importance.argsort()[::-1]
    plt.figure(figsize=(8,5))
    sns.barplot(x=importance[sorted_idx],
                y=[feature_names[i] for i in sorted_idx],
                palette="viridis")
    plt.title("Feature Importance - XGBoost")
    plt.xlabel("Importance Score")
    plt.ylabel("Features")
    plt.tight_layout()
    plt.show()

# -----------------------------
# Clean keys
# -----------------------------
def clean_keys(df):
    # Normalize column names to Year/Month regardless of source format
    rename_map = {}
    for col in df.columns:
        cl = col.strip().lower()
        if cl in ('dep_annee', 'annee', 'year'):
            rename_map[col] = 'Year'
        elif cl in ('dep_mois', 'mois', 'month'):
            rename_map[col] = 'Month'
    df = df.rename(columns=rename_map)
    df["Year"] = pd.to_numeric(df["Year"].astype(str).str.strip(), errors="coerce")
    df["Month"] = pd.to_numeric(df["Month"].astype(str).str.strip(), errors="coerce")
    df = df.dropna(subset=["Year", "Month"])
    df["Year"] = df["Year"].astype(int)
    df["Month"] = df["Month"].astype(int)
    return df

# -----------------------------
# Step 1: Load Data
# -----------------------------
def load_data():
    df1 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\monthly_departures.csv")
    df2 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\recruitments_by_year_month.csv")
    df3 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\anne_mois_MS_nbemp.csv")

    df1 = clean_keys(df1)
    df2 = clean_keys(df2)
    df3 = clean_keys(df3)

    # Merge all data
    merged = df1.merge(df2, on=["Year", "Month"], how="left").merge(df3, on=["Year", "Month"], how="left")

    # Fill missing recruitments with 0 (only January has recruitments)
    merged["Recruitments"] = merged["Recruitments"].fillna(0)

    # Remove rows with missing critical data
    merged = merged.dropna(subset=["mass_salary", "nbemp"])

    print(f"Total rows after merge: {len(merged)}")
    print("Missing values:\n", merged.isna().sum())

    return merged

# -----------------------------
# Step 2: Preprocess Data (IMPROVED)
# -----------------------------
def preprocess(df):
    """
    Improved preprocessing that properly captures the relationship
    between number of employees and mass salary.

    Key insight: Mass salary = sum of individual salaries
    So it should be strongly correlated with nbemp (number of employees)
    """
    df = df.sort_values(["Year", "Month"]).reset_index(drop=True)

    # Calculate cumulative recruitments for the year
    df["cumulative_recruitments"] = df.groupby("Year")["Recruitments"].transform("sum")

    # Calculate average salary per employee (this is a key derived feature)
    df["avg_salary_per_emp"] = df["mass_salary"] / df["nbemp"]

    # Year-over-year growth features
    df["year_normalized"] = df["Year"] - df["Year"].min()  # Normalize year to start from 0

    # Net employee change (recruitments - departures)
    df["net_employee_change"] = df["Recruitments"] - df["nb_departures"]

    # Cumulative net change within year
    df["cumulative_net_change"] = df.groupby("Year")["net_employee_change"].cumsum()

    # Features to use - nbemp is the MOST IMPORTANT feature for mass salary prediction
    # We keep it unscaled relative importance high
    feature_cols = [
        "nbemp",                    # Number of employees (PRIMARY driver of mass salary)
        "Year",                     # Year (captures salary inflation over time)
        "Month",                    # Month (captures seasonal variations)
        "nb_departures",            # Monthly departures
        "cumulative_recruitments",  # Total recruitments for the year
        "cumulative_net_change"     # Net employee change
    ]

    X = df[feature_cols].copy()
    y = df["mass_salary"].copy()

    # Use StandardScaler but keep track of feature importance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X_scaled, y, scaler, feature_cols, df

# -----------------------------
# Step 3: Train XGBoost (IMPROVED)
# -----------------------------
def train_xgboost(X_train, y_train):
    """
    Improved XGBoost model with better hyperparameters
    for capturing the employee-salary relationship.
    """
    model = XGBRegressor(
        n_estimators=800,           # More trees for better learning
        learning_rate=0.05,         # Balanced learning rate
        max_depth=5,                # Slightly deeper for better pattern capture
        min_child_weight=2,         # Minimum sum of instance weight in a child
        subsample=0.85,             # Row sampling
        colsample_bytree=0.85,      # Column sampling
        reg_alpha=0.05,             # L1 regularization
        reg_lambda=0.5,             # L2 regularization
        random_state=42,
        n_jobs=-1,
        objective='reg:squarederror'
    )
    model.fit(X_train, y_train,
              eval_set=[(X_train, y_train)],
              verbose=False)
    return model

# -----------------------------
# Step 4: Evaluate Model (Monthly) - IMPROVED
# -----------------------------
def evaluate_model_monthly(model, X_test, y_test):
    """Evaluate model with comprehensive metrics."""
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print("\n" + "="*50)
    print("XGBoost Monthly Evaluation Metrics")
    print("="*50)
    print(f"Mean Squared Error (MSE): {mse:,.2f}")
    print(f"Root Mean Squared Error (RMSE): {rmse:,.2f}")
    print(f"Mean Absolute Error (MAE): {mae:,.2f}")
    print(f"R² Score: {r2:.4f}")

    # Calculate MAPE
    if not (y_test == 0).any():
        mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
        print(f"Mean Absolute Percentage Error (MAPE): {mape:.2f}%")

    return y_pred, {"mse": mse, "rmse": rmse, "mae": mae, "r2": r2}

# -----------------------------
# Step 5: Aggregate to Yearly Predictions (IMPROVED)
# -----------------------------
def aggregate_to_yearly(df_with_predictions):
    """Aggregate monthly predictions to yearly totals and evaluate."""
    yearly = df_with_predictions.groupby("Year").agg({
        "mass_salary": "sum",
        "predicted_salary": "sum",
        "nbemp": "mean"  # Average employees for the year
    }).reset_index()
    yearly.columns = ["Year", "actual_yearly_salary", "predicted_yearly_salary", "avg_employees"]

    # Calculate yearly metrics
    mse_yearly = mean_squared_error(yearly["actual_yearly_salary"], yearly["predicted_yearly_salary"])
    rmse_yearly = np.sqrt(mse_yearly)
    mae_yearly = mean_absolute_error(yearly["actual_yearly_salary"], yearly["predicted_yearly_salary"])
    r2_yearly = r2_score(yearly["actual_yearly_salary"], yearly["predicted_yearly_salary"])

    print("\n" + "="*50)
    print("XGBoost Yearly Evaluation Metrics")
    print("="*50)
    print(f"Mean Squared Error (MSE): {mse_yearly:,.2f}")
    print(f"Root Mean Squared Error (RMSE): {rmse_yearly:,.2f}")
    print(f"Mean Absolute Error (MAE): {mae_yearly:,.2f}")
    print(f"R² Score: {r2_yearly:.4f}")

    return yearly, mse_yearly, r2_yearly

# -----------------------------
# Step 6: Predict Future Years (IMPROVED)
# -----------------------------
def predict_future_years(model, scaler, feature_names, start_year, end_year,
                        annual_recruitments, monthly_departures, initial_employees):
    """
    Predict future years month by month, then aggregate to yearly totals.

    The model now properly accounts for:
    - Number of employees (primary driver)
    - Year (inflation/growth over time)
    - Monthly variations
    - Net employee changes

    Args:
        model: Trained XGBoost model
        scaler: Fitted StandardScaler
        feature_names: List of feature column names
        start_year: First year to predict
        end_year: Last year to predict
        annual_recruitments: Number of new hires per year (in January)
        monthly_departures: Average departures per month
        initial_employees: Starting employee count

    Returns:
        DataFrame with yearly predictions
    """
    predictions = []
    current_employees = initial_employees

    for year in range(start_year, end_year + 1):
        yearly_salary_sum = 0
        cumulative_net_change = 0

        for month in range(1, 13):
            # Recruitments only happen in January
            monthly_recruitment = annual_recruitments if month == 1 else 0

            # Update employee count at start of month
            if month == 1:
                current_employees += monthly_recruitment

            # Calculate net change for this month
            net_change = monthly_recruitment - monthly_departures
            cumulative_net_change += net_change

            # Create features matching the training feature order:
            # ["nbemp", "Year", "Month", "nb_departures", "cumulative_recruitments", "cumulative_net_change"]
            features = pd.DataFrame([{
                "nbemp": current_employees,
                "Year": year,
                "Month": month,
                "nb_departures": monthly_departures,
                "cumulative_recruitments": annual_recruitments,
                "cumulative_net_change": cumulative_net_change
            }])

            # Ensure column order matches training
            features = features[feature_names]

            # Scale and predict
            features_scaled = scaler.transform(features)
            monthly_prediction = model.predict(features_scaled)[0]

            # Ensure prediction is positive
            monthly_prediction = max(0, monthly_prediction)
            yearly_salary_sum += monthly_prediction

            # Update employee count (departures happen throughout the month)
            current_employees -= monthly_departures
            current_employees = max(0, current_employees)  # Can't have negative employees

        # Store yearly prediction
        avg_monthly = yearly_salary_sum / 12
        predictions.append({
            "Year": year,
            "total_yearly_salary": round(yearly_salary_sum, 2),
            "avg_monthly_salary": round(avg_monthly, 2),
            "employees_end_of_year": current_employees
        })

        print(f"Year {year}: Total Salary = {yearly_salary_sum:,.2f} MAD, "
              f"Avg Monthly = {avg_monthly:,.2f} MAD, "
              f"Employees EOY = {current_employees}")

    return pd.DataFrame(predictions)

# -----------------------------
# Step 7: Save Model (IMPROVED)
# -----------------------------
def save_model(model, scaler, feature_names, metrics=None):
    """
    Save model, scaler, feature names, and metrics to artifacts folder.

    This exports the trained model for use in the web application.
    You should run this after training to update the model used for predictions.
    """
    # Save to ml_models/artifacts (for development)
    os.makedirs("artifacts", exist_ok=True)
    joblib.dump(model, "artifacts/xgb_model.pkl")
    joblib.dump(scaler, "artifacts/scaler.pkl")
    joblib.dump(feature_names, "artifacts/feature_names.pkl")
    if metrics:
        joblib.dump(metrics, "artifacts/metrics.pkl")

    # Also save to root artifacts folder (for production/web app)
    root_artifacts = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
    os.makedirs(root_artifacts, exist_ok=True)
    joblib.dump(model, os.path.join(root_artifacts, "xgb_model.pkl"))
    joblib.dump(scaler, os.path.join(root_artifacts, "scaler.pkl"))
    joblib.dump(feature_names, os.path.join(root_artifacts, "feature_names.pkl"))
    if metrics:
        joblib.dump(metrics, os.path.join(root_artifacts, "metrics.pkl"))

    print("\n" + "="*50)
    print("MODEL EXPORT SUCCESSFUL")
    print("="*50)
    print(f"Saved to: artifacts/ and {root_artifacts}/")
    print("Files exported:")
    print("  - xgb_model.pkl (trained XGBoost model)")
    print("  - scaler.pkl (StandardScaler for feature normalization)")
    print("  - feature_names.pkl (list of feature column names)")
    if metrics:
        print("  - metrics.pkl (model evaluation metrics)")

# -----------------------------
# Step 8: Main Workflow
# -----------------------------
if __name__ == "__main__":
    print("="*60)
    print("SALARY PREDICTION MODEL - XGBoost Training")
    print("="*60)

    # Load and preprocess data
    print("\n📊 Loading and preprocessing data...")
    df = load_data()
    X_scaled, y, scaler, feature_names, df_full = preprocess(df)

    print(f"\nFeatures used: {list(feature_names)}")
    print(f"Total samples: {len(X_scaled)}")

    # Split data - keeping temporal order is important for time series
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, shuffle=False
    )
    print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")

    # Train model
    print("\n🔧 Training XGBoost model...")
    xgb_model = train_xgboost(X_train, y_train)

    # Show feature importance
    print("\n📊 Feature Importance:")
    importances = xgb_model.feature_importances_
    for name, score in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
        print(f"  {name}: {score:.4f}")

    # Evaluate on monthly predictions
    print("\n📈 Evaluating model...")
    monthly_predictions, monthly_metrics = evaluate_model_monthly(xgb_model, X_test, y_test)

    # Add predictions to dataframe for yearly aggregation
    df_test = df_full.iloc[-len(y_test):].copy()
    df_test["predicted_salary"] = monthly_predictions

    # Aggregate to yearly
    yearly_results, mse_yearly, r2_yearly = aggregate_to_yearly(df_test)
    print("\nYearly Comparison (Actual vs Predicted):")
    print(yearly_results.to_string(index=False))

    # Plot results
    print("\nGenerating plots...")
    plot_predictions(y_test, monthly_predictions, "XGBoost Monthly")
    plot_feature_importance(xgb_model, list(feature_names))

    # Save model with metrics
    all_metrics = {
        "monthly": monthly_metrics,
        "yearly": {"mse": mse_yearly, "r2": r2_yearly}
    }
    save_model(xgb_model, scaler, list(feature_names), all_metrics)

    # Example: Predict future years
    print("\n" + "="*60)
    print("FUTURE PREDICTIONS EXAMPLE")
    print("="*60)

    # Get last known employee count from data
    last_employees = int(df_full['nbemp'].iloc[-1])
    print(f"Last known employee count: {last_employees}")

    future_predictions = predict_future_years(
        model=xgb_model,
        scaler=scaler,
        feature_names=list(feature_names),
        start_year=2025,
        end_year=2027,
        annual_recruitments=100,   # Total recruitments in January
        monthly_departures=5,      # Average monthly departures
        initial_employees=last_employees
    )

    print("\nFuture Predictions Summary:")
    print(future_predictions.to_string(index=False))

    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print("\nTo use the new model in the web app, the artifacts have been")
    print("automatically exported to both locations.")
    print("\nIf you need to manually export, run:")
    print("  save_model(xgb_model, scaler, feature_names, metrics)")


