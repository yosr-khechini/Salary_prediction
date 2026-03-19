"""
Retrain XGBoost model using yearly aggregates for better accuracy.
This model predicts yearly mass salary directly from yearly employee/recruitment/departure data.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from xgboost import XGBRegressor
import joblib
import os

def load_yearly_data():
    """Load and prepare yearly aggregate data"""
    # Load historical yearly data
    historical_df = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\historical_data.csv")

    print("Loaded historical data:")
    print(historical_df)
    print()

    return historical_df

def load_monthly_data():
    """Load monthly data and aggregate to yearly"""
    # Load processed monthly data
    monthly_salary = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\anne_mois_MS_nbemp.csv")
    monthly_departures = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\monthly_departures.csv")
    monthly_recruitments = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\recruitments_by_year_month.csv")

    # Rename columns for consistency
    monthly_salary = monthly_salary.rename(columns={'annee': 'Year', 'mois': 'Month'})

    # Clean departures columns - they use DEP_ANNEE, DEP_MOIS
    monthly_departures = monthly_departures.rename(columns={
        'DEP_ANNEE': 'Year',
        'DEP_MOIS': 'Month',
        'dep_annee': 'Year',
        'dep_mois': 'Month'
    })

    print("Monthly salary columns:", monthly_salary.columns.tolist())
    print("Monthly departures columns:", monthly_departures.columns.tolist())
    print("Monthly recruitments columns:", monthly_recruitments.columns.tolist())

    # Clean and convert Year column in all dataframes
    for df in [monthly_salary, monthly_departures, monthly_recruitments]:
        df['Year'] = pd.to_numeric(df['Year'].astype(str).str.strip(), errors='coerce')
        df.dropna(subset=['Year'], inplace=True)
        df['Year'] = df['Year'].astype(int)

    # Aggregate monthly to yearly
    yearly_salary = monthly_salary.groupby('Year').agg({
        'mass_salary': 'sum',
        'nbemp': 'mean'  # Average employees for the year
    }).reset_index()

    yearly_departures = monthly_departures.groupby('Year').agg({
        'nb_departures': 'sum'
    }).reset_index()

    yearly_recruitments = monthly_recruitments.groupby('Year').agg({
        'Recruitments': 'sum'
    }).reset_index()

    # Merge all yearly data
    yearly_data = yearly_salary.merge(yearly_departures, on='Year', how='left')
    yearly_data = yearly_data.merge(yearly_recruitments, on='Year', how='left')

    # Fill NaN
    yearly_data = yearly_data.fillna(0)

    print("\nAggregated yearly data from monthly files:")
    print(yearly_data)
    print()

    return yearly_data

def engineer_features(df):
    """Create features for yearly prediction"""
    df = df.copy()

    # Basic features
    df['net_change'] = df['Recruitments'] - df['nb_departures']

    # Lagged features (previous year)
    df['prev_salary'] = df['mass_salary'].shift(1)
    df['prev_employees'] = df['nbemp'].shift(1)

    # Growth rates
    df['salary_growth'] = df['mass_salary'].pct_change()
    df['employee_growth'] = df['nbemp'].pct_change()

    # Salary per employee
    df['salary_per_employee'] = df['mass_salary'] / df['nbemp']

    # Fill NaN from lag/pct_change with backward fill or 0
    df = df.bfill().fillna(0)

    return df

def train_yearly_model():
    """Train XGBoost on yearly aggregate data"""

    # Load monthly data and aggregate
    yearly_df = load_monthly_data()

    # Engineer features
    yearly_df = engineer_features(yearly_df)

    print("\nPrepared data for training:")
    print(yearly_df)
    print()

    # Define features and target
    feature_cols = ['nbemp', 'Year', 'nb_departures', 'Recruitments', 'net_change']

    X = yearly_df[feature_cols]
    y = yearly_df['mass_salary']

    print(f"Features: {feature_cols}")
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print()

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train XGBoost with regularization to prevent overfitting on small dataset
    model = XGBRegressor(
        n_estimators=100,
        max_depth=3,  # Shallow trees for small dataset
        learning_rate=0.1,
        min_child_weight=2,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,  # L1 regularization
        reg_lambda=1.0,  # L2 regularization
        random_state=42
    )

    # Fit the model
    model.fit(X_scaled, y)

    # Predict on training data
    y_pred = model.predict(X_scaled)

    # Calculate metrics
    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mse)

    # Calculate MAPE
    mape = np.mean(np.abs((y - y_pred) / y)) * 100

    print("=" * 60)
    print("YEARLY MODEL TRAINING RESULTS")
    print("=" * 60)
    print(f"R² Score: {r2:.4f}")
    print(f"MSE: {mse:,.2f}")
    print(f"RMSE: {rmse:,.2f}")
    print(f"MAE: {mae:,.2f}")
    print(f"MAPE: {mape:.2f}%")
    print()

    # Show predictions vs actual
    print("Year-by-Year Comparison:")
    print("-" * 80)
    print(f"{'Year':<8} {'Actual':>20} {'Predicted':>20} {'Error %':>12}")
    print("-" * 80)

    for i, row in yearly_df.iterrows():
        actual = row['mass_salary']
        pred = y_pred[i]
        error_pct = abs(pred - actual) / actual * 100
        print(f"{int(row['Year']):<8} {actual:>20,.2f} {pred:>20,.2f} {error_pct:>11.2f}%")

    print("-" * 80)
    print(f"{'AVERAGE':>49} {mape:>11.2f}%")
    print()

    # Save model and scaler
    artifacts_dir = r"C:\L2 DSI\Stage\Project_Salary_Prediction\artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)

    joblib.dump(model, os.path.join(artifacts_dir, 'xgb_yearly_model.pkl'))
    joblib.dump(scaler, os.path.join(artifacts_dir, 'yearly_scaler.pkl'))
    joblib.dump(feature_cols, os.path.join(artifacts_dir, 'yearly_feature_names.pkl'))

    metrics = {
        'r2': r2,
        'mse': mse,
        'rmse': rmse,
        'mae': mae,
        'mape': mape
    }
    joblib.dump(metrics, os.path.join(artifacts_dir, 'yearly_metrics.pkl'))

    print(f"Model saved to {artifacts_dir}")

    return model, scaler, feature_cols, metrics

if __name__ == "__main__":
    train_yearly_model()

