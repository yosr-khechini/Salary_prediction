import joblib
import os
import pickle

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Paths to yearly model artifacts (better accuracy ~0.84% MAPE)
ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'artifacts')
MODEL_PATH = os.path.join(ARTIFACTS_DIR, 'xgb_yearly_model.pkl')
SCALER_PATH = os.path.join(ARTIFACTS_DIR, 'yearly_scaler.pkl')
FEATURE_NAMES_PATH = os.path.join(ARTIFACTS_DIR, 'yearly_feature_names.pkl')
METRICS_PATH = os.path.join(ARTIFACTS_DIR, 'yearly_metrics.pkl')

# Fallback to old monthly model paths
OLD_ARTIFACTS_DIR = os.path.join(PROJECT_ROOT, 'ml_models', 'artifacts')
OLD_MODEL_PATH = os.path.join(OLD_ARTIFACTS_DIR, 'xgb_model.pkl')
OLD_SCALER_PATH = os.path.join(OLD_ARTIFACTS_DIR, 'scaler.pkl')
OLD_FEATURE_NAMES_PATH = os.path.join(OLD_ARTIFACTS_DIR, 'feature_names.pkl')
OLD_METRICS_PATH = os.path.join(OLD_ARTIFACTS_DIR, 'metrics.pkl')

# Cache to avoid reloading artifacts on every prediction
_model_cache = None
_scaler_cache = None
_feature_names_cache = None
_metrics_cache = None
_model_type = None  # 'yearly' or 'monthly'


def get_model():
    """Load and return the ML model"""
    global _model_cache, _model_type
    if _model_cache is None:
        # Try yearly model first (better accuracy)
        if os.path.exists(MODEL_PATH):
            _model_cache = joblib.load(MODEL_PATH)
            _model_type = 'yearly'
            print(f"[OK] Loaded yearly model from {MODEL_PATH}")
        elif os.path.exists(OLD_MODEL_PATH):
            _model_cache = joblib.load(OLD_MODEL_PATH)
            _model_type = 'monthly'
            print(f"[WARN] Loaded old monthly model from {OLD_MODEL_PATH}")
        else:
            raise FileNotFoundError(f"Model not found: {MODEL_PATH} or {OLD_MODEL_PATH}")
    return _model_cache


def get_scaler():
    """Load and return the scaler"""
    global _scaler_cache
    if _scaler_cache is None:
        if os.path.exists(SCALER_PATH):
            _scaler_cache = joblib.load(SCALER_PATH)
        elif os.path.exists(OLD_SCALER_PATH):
            _scaler_cache = joblib.load(OLD_SCALER_PATH)
        else:
            raise FileNotFoundError(f"Scaler not found: {SCALER_PATH}")
    return _scaler_cache


def get_feature_names():
    """Load and return the list of feature names"""
    global _feature_names_cache
    if _feature_names_cache is None:
        if os.path.exists(FEATURE_NAMES_PATH):
            _feature_names_cache = joblib.load(FEATURE_NAMES_PATH)
        elif os.path.exists(OLD_FEATURE_NAMES_PATH):
            _feature_names_cache = joblib.load(OLD_FEATURE_NAMES_PATH)
        else:
            raise FileNotFoundError(f"Features not found: {FEATURE_NAMES_PATH}")
    return _feature_names_cache


def get_model_type():
    """Returns the type of model loaded ('yearly' or 'monthly')"""
    global _model_type
    if _model_type is None:
        get_model()  # This will set _model_type
    return _model_type


def get_model_metrics():
    """Get model metrics (R², MSE, etc.)"""
    global _metrics_cache

    if _metrics_cache is None:
        try:
            if os.path.exists(METRICS_PATH):
                _metrics_cache = joblib.load(METRICS_PATH)
            elif os.path.exists(OLD_METRICS_PATH):
                _metrics_cache = joblib.load(OLD_METRICS_PATH)
            else:
                print(f"Metrics file not found: {METRICS_PATH}")
                _metrics_cache = {'r2': 0.0, 'mse': 0.0, 'mape': 0.0}
        except Exception as e:
            print(f"Error loading metrics: {e}")
            _metrics_cache = {'r2': 0.0, 'mse': 0.0, 'mape': 0.0}

    return _metrics_cache


def reload_model():
    """Force reload of all artifacts (useful after retraining)"""
    global _model_cache, _scaler_cache, _feature_names_cache, _metrics_cache, _model_type
    _model_cache = None
    _scaler_cache = None
    _feature_names_cache = None
    _metrics_cache = None
    _model_type = None
    print("[OK] Model cache cleared. Next call will reload artifacts.")
