import os
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
from xgboost import XGBRegressor

# Définir les chemins
ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "xgb_model.pkl")
SCALER_PATH = os.path.join(ARTIFACTS_DIR, "scaler.pkl")
FEATURES_PATH = os.path.join(ARTIFACTS_DIR, "feature_names.pkl")
METRICS_PATH = os.path.join(ARTIFACTS_DIR, "metrics.pkl")

def ensure_dir():
    """Créer le dossier artifacts s'il n'existe pas"""
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def clean_keys(df):
    """Nettoie les colonnes Year et Month"""
    df["Year"] = pd.to_numeric(df["Year"].astype(str).str.strip(), errors="coerce")
    df["Month"] = pd.to_numeric(df["Month"].astype(str).str.strip(), errors="coerce")
    df = df.dropna(subset=["Year", "Month"])
    df["Year"] = df["Year"].astype(int)
    df["Month"] = df["Month"].astype(int)
    return df

def load_data():
    """Charge et fusionne les données depuis les fichiers CSV"""
    df1 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\monthly_departures.csv")
    df2 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\recruitments_by_year_month.csv")
    df3 = pd.read_csv(r"C:\L2 DSI\Stage\Project_Salary_Prediction\data\processed\anne_mois_MS_nbemp.csv")

    df1 = clean_keys(df1)
    df2 = clean_keys(df2)
    df3 = clean_keys(df3)

    # Fusionner les données
    merged = df1.merge(df2, on=["Year", "Month"], how="left").merge(df3, on=["Year", "Month"], how="left")
    merged["Recruitments"] = merged["Recruitments"].fillna(0)
    merged = merged.dropna(subset=["mass_salary", "nbemp"])

    return merged

def preprocess(df):
    """Prétraite les données avec l'effet de recrutement mensuel"""
    df = df.sort_values(["Year", "Month"])
    df["cumulative_recruitments"] = df.groupby("Year")["Recruitments"].transform("sum")
    df["monthly_recruitment_effect"] = df["cumulative_recruitments"] / 12

    feature_cols = ["Year", "Month", "nb_departures", "monthly_recruitment_effect", "nbemp"]
    X = df[feature_cols]
    y = df["mass_salary"]

    return X, y, feature_cols

def export_model():
    """
    Entraîne et exporte le modèle XGBoost + scaler + métriques
    """
    try:
        ensure_dir()

        # Charger les données
        print("Chargement des données...")
        df = load_data()

        # Préparer les features et target
        print("Prétraitement des données...")
        X, y, feature_names = preprocess(df)

        # Normaliser les données
        print("Normalisation des données...")
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Split train/test (garder l'ordre temporel)
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, shuffle=False
        )

        # Entraîner le modèle
        print("Entraînement du modèle XGBoost...")
        model = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)

        # Évaluer le modèle
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)

        print("\nModèle entraîné avec succès!")
        print(f"   R² Score: {r2:.4f}")
        print(f"   MSE: {mse:.2f}")

        # Sauvegarder les artefacts
        print("\nSauvegarde des artefacts...")
        joblib.dump(model, MODEL_PATH)
        joblib.dump(scaler, SCALER_PATH)
        joblib.dump(feature_names, FEATURES_PATH)

        metrics = {'r2': r2, 'mse': mse}
        joblib.dump(metrics, METRICS_PATH)

        print(f"   ✅ Modèle sauvegardé: {MODEL_PATH}")
        print(f"   ✅ Scaler sauvegardé: {SCALER_PATH}")
        print(f"   ✅ Features sauvegardées: {FEATURES_PATH}")
        print(f"   ✅ Métriques sauvegardées: {METRICS_PATH}")

        return {
            "status": "success",
            "model_path": MODEL_PATH,
            "scaler_path": SCALER_PATH,
            "features_path": FEATURES_PATH,
            "metrics_path": METRICS_PATH,
            "r2_score": r2,
            "mse": mse
        }

    except Exception as e:
        print(f"\n Erreur lors de l'exportation: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    result = export_model()
    print("\n📦 Exportation terminée!")
    print(f"Résultats: {result}")