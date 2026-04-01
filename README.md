# INSAF Salary Prediction

Flask web application for workforce and payroll forecasting using machine learning.
The project combines:
- employee lifecycle management (employees, recruitment, termination),
- historical analytics dashboard,
- salary mass prediction API and UI,
- prediction history tracking per authenticated user.

## Highlights

- Predict yearly salary mass from HR scenario inputs (`start_year`, `end_year`, `recruitments`, `departures`, `initial_employees`)
- Compare model behavior against historical data
- Visual dashboard built from `data/historical_data.csv`
- Authentication with session-based login
- SQLite default setup for local/offline use
- REST-style prediction endpoints ready for `curl` testing

## Tech Stack

- **Backend:** Flask, Flask-Login, Flask-SQLAlchemy, Flask-WTF
- **ML/Data:** XGBoost model artifacts, pandas, scikit-learn
- **Database:** SQLite (`instance/app.db` by default)
- **Frontend:** Jinja2 templates, Bootstrap, static JS/CSS

## Repository Layout

```text
Salary_prediction/
  app/                  # Flask app package (blueprints, models, prediction routes)
  artifacts/            # Trained model, scaler, metrics, feature names
  data/                 # Historical input data
  templates/            # HTML templates
  static/               # CSS/JS/images/fonts
  run.py                # App entrypoint
  config.py             # App config (secret key, DB URI)
  recreate_database.py  # Rebuild SQLite DB with sample INSAF-like data
  quick_api_test.txt    # Quick curl commands
  api_test_commands.txt # Extended curl command list
```

## Quick Start

### 1) Clone and enter project

```powershell
git clone <your-repo-url>
cd Salary_prediction
```

### 2) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Initialize the database

```powershell
python recreate_database.py
```

This creates `instance/app.db` and seeds sample data.

### 5) Run the application

```powershell
python run.py
```

Open: `http://127.0.0.1:5000`

## Default Demo Credentials

Created by `recreate_database.py`:

- **Username:** `admin`
- **Password:** `admin123`

> Change credentials before any real deployment.

## Main Web Routes

- `/` - landing page
- `/login` - authentication
- `/home` - user home
- `/dashboard` - historical charts and summary
- `/employees/` - employees listing and management
- `/recruitment` - recruitment records
- `/termination` - termination records
- `/prediction/` - prediction UI
- `/history` - saved prediction history

## Prediction API

Base URL: `http://127.0.0.1:5000`

### Health

```http
GET /prediction/health
```

### Metrics

```http
GET /prediction/metrics
```

### Predict

```http
POST /prediction/predict
POST /prediction/api/predict
Content-Type: application/json
```

Example request body:

```json
{
  "start_year": 2021,
  "end_year": 2025,
  "recruitments": 120,
  "departures": 80,
  "initial_employees": 3200
}
```

### Input Validation Rules

- `start_year` in `[2000, 2100]`
- `end_year >= start_year`
- maximum span: `20` years
- `recruitments`, `departures`, `initial_employees` must be non-negative
- `initial_employees` must be greater than `0`

## API Testing with curl

Use the ready-made files:
- `quick_api_test.txt` (minimal checks)
- `api_test_commands.txt` (full checks + error cases + optional authenticated test)

Quick commands:

```powershell
$BASE = "http://127.0.0.1:5000"
curl.exe "$BASE/prediction/health"
curl.exe "$BASE/prediction/metrics"
curl.exe -X POST "$BASE/prediction/predict" -H "Content-Type: application/json" -d '{"start_year":2021,"end_year":2025,"recruitments":120,"departures":80,"initial_employees":3200}'
```

## Model Artifacts

The app expects pre-trained artifacts in `artifacts/` (for example):
- `xgb_model.pkl`
- `scaler.pkl`
- `metrics.pkl`
- feature-name files (`feature_names.pkl`, yearly equivalents)

## Security Notes

- Secret key is configured in `config.py` and should be overridden via environment variable in production.
- Prediction blueprint is CSRF-exempt by design for API calls.
- Use a production WSGI server and environment-specific configuration for deployment.

## Roadmap Ideas

- Add automated tests for API and model-serving paths
- Add Docker setup
- Add role-based access and audit logging
- Add CI pipeline (lint + tests)

## License

MIT License
