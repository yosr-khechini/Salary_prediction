import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

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
    plt.title("Feature Importance - Random Forest")
    plt.xlabel("Importance Score")
    plt.ylabel("Features")
    plt.tight_layout()
    plt.show()

# -----------------------------
# Step 1: Clean keys
# -----------------------------
def clean_keys(df):
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
    df.loc[:, "Year"] = df["Year"].astype(int)
    df.loc[:, "Month"] = df["Month"].astype(int)
    return df

# -----------------------------
# Step 2: Load and merge data
# -----------------------------
def load_data():
    df1 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\monthly_departures.csv")
    df2 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\recruitments_by_year_month.csv")
    df3 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\anne_mois_MS_nbemp.csv")

    df1 = clean_keys(df1)
    df2 = clean_keys(df2)
    df3 = clean_keys(df3)

    print("Missing values in df1:\n", df1.isna().sum())

    merged = df1.merge(df2, on=["Year", "Month"]).merge(df3, on=["Year", "Month"])
    return merged

# -----------------------------
# Step 3: Preprocess data
# -----------------------------
def preprocess(dataset):
    X = dataset.drop("mass_salary", axis=1)   # replace with your target column
    y = dataset["mass_salary"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X_scaled, y, scaler, X.columns

# -----------------------------
# Step 4: Train Random Forest
# -----------------------------
def train_random_forest(X_train, y_train):
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    return model

# -----------------------------
# Step 5: Evaluate model
# -----------------------------
def evaluate(model, X_test, y_test):
    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"Random Forest MSE: {mse:.2f}")
    print(f"Random Forest R²: {r2:.2f}")
    return y_pred

# -----------------------------
# Step 6: Feature importance
# -----------------------------
def show_feature_importance(model, feature_names):
    importance_scores = model.feature_importances_
    print("\nFeature Importance:")
    for name, score in sorted(zip(feature_names, importance_scores), key=lambda x: x[1], reverse=True):
        print(f"{name}: {score:.4f}")

# -----------------------------
# Step 7: Main workflow
# -----------------------------
if __name__ == "__main__":
    dataset = load_data()
    X_scaled, y, scaler, feature_names = preprocess(dataset)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    forest_model = train_random_forest(X_train, y_train)
    forest_predictions = evaluate(forest_model, X_test, y_test)

    show_feature_importance(forest_model, feature_names)
    plot_predictions(y_test, forest_predictions, "Random Forest")
    plot_feature_importance(forest_model, feature_names)