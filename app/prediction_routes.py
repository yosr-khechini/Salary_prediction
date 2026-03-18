from flask import Blueprint, render_template, request, jsonify, current_app
from app.prediction import predict_salaries, generate_graph, validate_inputs
from app.model_loader import get_model, get_scaler, get_model_metrics
from flask_login import login_required, current_user
import pandas as pd
from app import db
from app.models import PredictionHistory
import json
import os



# Créer le blueprint
prediction_bp = Blueprint('prediction', __name__, url_prefix='/prediction')

@prediction_bp.route('/')
@login_required
def prediction_page():
    """Page d'accueil avec le formulaire de prédiction"""
    return render_template('prediction.html')


@prediction_bp.route('/test-page')
@login_required
def test_page():
    """Render the test prediction page"""
    return render_template('test_prediction.html')


@prediction_bp.route('/test', methods=['POST'])
@login_required
def test_model():
    """Test the model against ALL historical years using historical_data.csv - returns comparison table with average error"""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Load historical data from the main CSV file
        historical_file = os.path.join(base_dir, 'data', 'historical_data.csv')
        historical_df = pd.read_csv(historical_file)

        # Clean data
        historical_df['year'] = pd.to_numeric(historical_df['year'], errors='coerce')
        historical_df = historical_df.dropna(subset=['year'])
        historical_df['year'] = historical_df['year'].astype(int)

        # Get all unique years
        all_years = sorted(historical_df['year'].unique())

        results = []
        total_absolute_error = 0
        total_percentage_error = 0

        for year in all_years:
            year_data = historical_df[historical_df['year'] == year]

            if year_data.empty:
                continue

            # Get actual values from historical data
            actual_salary = float(year_data['mass_salary'].values[0])
            employees = int(year_data['number_employees'].values[0])
            departures = int(year_data['departures'].values[0])
            recruitments = int(year_data['recruitment'].values[0])

            # Run prediction
            monthly_df, yearly_df = predict_salaries(
                start_year=year,
                end_year=year,
                recruitments=recruitments,
                departures=departures,
                initial_employees=employees
            )

            predicted_salary = yearly_df.iloc[0]['Total_Salary']
            absolute_error = abs(predicted_salary - actual_salary)
            percentage_error = (absolute_error / actual_salary) * 100 if actual_salary > 0 else 0

            total_absolute_error += absolute_error
            total_percentage_error += percentage_error

            results.append({
                'year': int(year),
                'employees': employees,
                'recruitments': recruitments,
                'departures': departures,
                'actual': round(actual_salary, 2),
                'predicted': round(predicted_salary, 2),
                'difference': round(predicted_salary - actual_salary, 2),
                'absolute_error': round(absolute_error, 2),
                'error_percent': round(percentage_error, 2)
            })

        num_years = len(results)
        avg_absolute_error = total_absolute_error / num_years if num_years > 0 else 0
        avg_percentage_error = total_percentage_error / num_years if num_years > 0 else 0

        return jsonify({
            'status': 'success',
            'results': results,
            'metrics': {
                'mae': round(avg_absolute_error, 2),
                'mape': round(avg_percentage_error, 2),
                'num_years': num_years,
                'avg_error_message': f"Average error: {round(avg_percentage_error, 2)}% - This error is used to adjust future predictions"
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Test error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@prediction_bp.route('/predict', methods=['POST'])
def predict():
    """
    JSON endpoint for AJAX requests
    Returns JSON instead of HTML with error-adjusted predictions
    """
    try:
        # Get JSON data from request
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No JSON data received'
            }), 400

        # Validate required fields
        required_fields = ['start_year', 'end_year', 'recruitments', 'departures', 'initial_employees']
        missing_fields = [field for field in required_fields if field not in data or data[field] is None]

        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing fields: {", ".join(missing_fields)}'
            }), 400

        # Convert with error handling
        try:
            start_year = int(data['start_year'])
            end_year = int(data['end_year'])
            recruitments = int(data['recruitments'])
            departures = int(data['departures'])
            initial_employees = int(data['initial_employees'])
        except (ValueError, TypeError) as ve:
            current_app.logger.error(f"Conversion error: {ve}")
            return jsonify({
                'status': 'error',
                'message': 'Invalid numeric values'
            }), 400

        # Business validation
        is_valid, error_msg = validate_inputs(start_year, end_year, recruitments, departures, initial_employees)
        if not is_valid:
            return jsonify({
                'status': 'error',
                'message': error_msg
            }), 400

        # Get predictions (returns TWO dataframes)
        monthly_df, yearly_df = predict_salaries(start_year, end_year, recruitments, departures, initial_employees)

        # Calculate error adjustment factor from historical data
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            historical_file = os.path.join(base_dir, 'data', 'historical_data.csv')
            historical_df = pd.read_csv(historical_file)

            # Calculate average error percentage from historical data
            total_error = 0
            count = 0
            for _, row in historical_df.iterrows():
                year = int(row['year'])
                _, test_yearly = predict_salaries(year, year, int(row['recruitment']),
                                                   int(row['departures']), int(row['number_employees']))
                predicted = test_yearly.iloc[0]['Total_Salary']
                actual = row['mass_salary']
                error_pct = (predicted - actual) / actual if actual > 0 else 0
                total_error += error_pct
                count += 1

            avg_error_factor = total_error / count if count > 0 else 0

            # Apply correction factor to predictions (subtract average overestimation)
            correction_factor = 1 - avg_error_factor
            yearly_df['Total_Salary'] = yearly_df['Total_Salary'] * correction_factor
            monthly_df['Predicted_Salary'] = monthly_df['Predicted_Salary'] * correction_factor

        except Exception as adj_err:
            current_app.logger.warning(f"Could not apply error adjustment: {adj_err}")
            # Continue without adjustment

        # Generate graph from MONTHLY data
        graph_base64 = generate_graph(monthly_df)

        # Get model metrics (stored as nested dict: {'monthly': {...}, 'yearly': {...}})
        try:
            model_metrics = get_model_metrics()
            # Handle nested structure from training
            if 'monthly' in model_metrics:
                monthly_m = model_metrics['monthly']
                yearly_m = model_metrics.get('yearly', {})
                metrics_data = {
                    'monthly_r2': round(monthly_m.get('r2', 0.0), 4),
                    'monthly_mse': round(monthly_m.get('mse', 0.0), 2),
                    'monthly_rmse': round(monthly_m.get('rmse', 0.0), 2),
                    'monthly_mae': round(monthly_m.get('mae', 0.0), 2),
                    'yearly_r2': round(yearly_m.get('r2', 0.0), 4),
                    'yearly_mse': round(yearly_m.get('mse', 0.0), 2),
                }
            else:
                # Fallback for flat structure
                metrics_data = {
                    'monthly_r2': round(model_metrics.get('r2', 0.0), 4),
                    'monthly_mse': round(model_metrics.get('mse', 0.0), 2),
                    'monthly_rmse': round(model_metrics.get('rmse', 0.0), 2),
                    'monthly_mae': round(model_metrics.get('mae', 0.0), 2),
                    'yearly_r2': 0.0,
                    'yearly_mse': 0.0,
                }
        except Exception as me:
            current_app.logger.warning(f"Could not retrieve metrics: {me}")
            metrics_data = {
                'monthly_r2': 0.0,
                'monthly_mse': 0.0,
                'monthly_rmse': 0.0,
                'monthly_mae': 0.0,
                'yearly_r2': 0.0,
                'yearly_mse': 0.0,
            }

        # Convert annual dataframe to list of dictionaries
        predictions_list = yearly_df.to_dict('records')

        # Build JSON response
        response = {
            'status': 'success',
            'predictions': predictions_list,
            'graph': graph_base64,
            'metrics': metrics_data
        }

        if current_user.is_authenticated:
            history = PredictionHistory(
                user_id=current_user.id,
                start_year=start_year,
                end_year=end_year,
                recruitments=recruitments,
                departures=departures,
                initial_employees=initial_employees,
                result_json=json.dumps(response)
            )
            db.session.add(history)
            db.session.commit()

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"API Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500

@prediction_bp.route('/api/predict', methods=['POST'])
def api_predict():
    """Alternative API endpoint (identical to /predict)"""
    return predict()

@prediction_bp.route('/health')
def health():
    """API health check endpoint"""
    try:
        model = get_model()
        scaler = get_scaler()
        model_loaded = model is not None and scaler is not None

        response = {
            'status': 'ok',
            'message': 'API operational',
            'model_loaded': model_loaded
        }

        if model_loaded:
            try:
                model_metrics = get_model_metrics()
                response['metrics'] = {
                    'r2_score': round(model_metrics.get('r2', 0.0), 4),
                    'mse': round(model_metrics.get('mse', 0.0), 2)
                }
            except Exception as me:
                current_app.logger.warning(f"Metrics not available: {me}")

        return jsonify(response), 200

    except Exception as e:
        current_app.logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@prediction_bp.route('/metrics', methods=['GET'])
def get_metrics_route():
    """Get model metrics"""
    try:
        model_metrics = get_model_metrics()
        if 'monthly' in model_metrics:
            monthly_m = model_metrics['monthly']
            yearly_m = model_metrics.get('yearly', {})
            metrics_out = {
                'monthly_r2': round(monthly_m.get('r2', 0.0), 4),
                'monthly_mse': round(monthly_m.get('mse', 0.0), 2),
                'monthly_rmse': round(monthly_m.get('rmse', 0.0), 2),
                'monthly_mae': round(monthly_m.get('mae', 0.0), 2),
                'yearly_r2': round(yearly_m.get('r2', 0.0), 4),
                'yearly_mse': round(yearly_m.get('mse', 0.0), 2),
            }
        else:
            metrics_out = {
                'monthly_r2': round(model_metrics.get('r2', 0.0), 4),
                'monthly_mse': round(model_metrics.get('mse', 0.0), 2),
            }
        return jsonify({
            'status': 'success',
            'metrics': metrics_out
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error retrieving metrics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500