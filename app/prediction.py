import pandas as pd
import numpy as np
from app.model_loader import get_model, get_scaler, get_model_type, get_feature_names

def validate_inputs(start_year, end_year, recruitments, departures, initial_employees):
    """Validate input parameters"""
    if start_year < 2000 or start_year > 2100:
        return False, "Invalid start year (2000-2100)"

    if end_year < start_year:
        return False, "End year must be greater than or equal to start year"

    if end_year - start_year > 20:
        return False, "Maximum range: 20 years"

    if recruitments < 0 or departures < 0 or initial_employees < 0:
        return False, "Values must be positive"

    if initial_employees == 0:
        return False, "Initial employees cannot be zero"

    return True, None


def predict_salaries_yearly(start_year, end_year, recruitments, departures, initial_employees):
    """
    Predict using the yearly model (better accuracy ~0.84% MAPE)
    Features: ['nbemp', 'Year', 'nb_departures', 'Recruitments', 'net_change']

    For future years beyond training data (2010-2020), we:
    1. Use the model to get a base prediction
    2. Apply realistic growth based on historical trends
    """
    try:
        model = get_model()
        scaler = get_scaler()

        if model is None or scaler is None:
            raise ValueError("Modèle ou scaler non chargé")

        monthly_predictions = []
        yearly_predictions = []
        current_employees = float(initial_employees)

        # Historical reference: Last known year from training data
        # 2020: mass_salary = 239,227,929.56, nbemp = 3220
        LAST_KNOWN_YEAR = 2020
        LAST_KNOWN_SALARY = 239_227_929.56
        LAST_KNOWN_EMPLOYEES = 3220

        # Average salary per employee (from 2020 data) - yearly
        AVG_SALARY_PER_EMPLOYEE = LAST_KNOWN_SALARY / LAST_KNOWN_EMPLOYEES  # ~74,303

        # Historical average salary growth rate per year (~5% for public sector)
        ANNUAL_GROWTH_RATE = 0.05

        # Track previous prediction for growth calculation
        prev_yearly_salary = None

        for year in range(start_year, end_year + 1):
            # Calculate net change for this year
            net_change = recruitments - departures

            # Build features for yearly model
            # For years beyond training range, clamp Year to last known year
            model_year = min(year, LAST_KNOWN_YEAR)

            input_data = {
                'nbemp': current_employees,
                'Year': model_year,
                'nb_departures': departures,
                'Recruitments': recruitments,
                'net_change': net_change
            }

            df = pd.DataFrame([input_data])
            # Ensure column order matches training
            feature_names = get_feature_names()
            df = df[feature_names]

            # Scale and predict using model
            scaled_data = scaler.transform(df)
            base_prediction = model.predict(scaled_data)[0]

            # For future years, apply growth projection
            if year > LAST_KNOWN_YEAR:
                years_ahead = year - LAST_KNOWN_YEAR

                if prev_yearly_salary is None:
                    # First prediction year: Calculate based on employees and historical per-employee salary
                    # Apply growth for years since 2020
                    adjusted_avg_salary = AVG_SALARY_PER_EMPLOYEE * ((1 + ANNUAL_GROWTH_RATE) ** years_ahead)
                    yearly_salary = current_employees * adjusted_avg_salary
                else:
                    # Subsequent years: Apply compound growth
                    # Factor in: inflation + employee change effect
                    employee_change_rate = net_change / (current_employees - net_change) if (current_employees - net_change) > 0 else 0
                    yearly_salary = prev_yearly_salary * (1 + ANNUAL_GROWTH_RATE + employee_change_rate * 0.7)
            else:
                yearly_salary = base_prediction

            yearly_salary = max(0, yearly_salary)

            # Generate monthly breakdown (divide yearly by 12)
            monthly_salary = yearly_salary / 12

            for month in range(1, 13):
                # Calculate monthly employee count (linear interpolation)
                monthly_change = net_change / 12
                month_employees = current_employees + (month - 1) * monthly_change

                monthly_predictions.append({
                    'Year': year,
                    'Month': month,
                    'Month_Name': pd.to_datetime(f'{year}-{month:02d}-01').strftime('%B'),
                    'Predicted_Salary': round(monthly_salary, 2),
                    'Employees': int(round(month_employees))
                })

            # Store yearly prediction
            yearly_predictions.append({
                'Year': year,
                'Total_Salary': round(yearly_salary, 2),
                'End_Employees': int(round(current_employees + net_change))
            })

            print(f"Année {year}: Masse salariale = {yearly_salary:,.2f}, Effectif = {int(current_employees)}")

            # Update for next iteration
            prev_yearly_salary = yearly_salary
            current_employees += net_change
            current_employees = max(1, current_employees)

        monthly_df = pd.DataFrame(monthly_predictions)
        yearly_df = pd.DataFrame(yearly_predictions)

        return monthly_df, yearly_df

    except Exception as e:
        print(f"Erreur dans predict_salaries_yearly: {e}")
        import traceback
        traceback.print_exc()
        raise


def predict_salaries_monthly(start_year, end_year, recruitments, departures, initial_employees):
    """
    Original monthly prediction (fallback if yearly model not available)
    """
    try:
        model = get_model()
        scaler = get_scaler()

        if model is None or scaler is None:
            raise ValueError("Modèle ou scaler non chargé")

        monthly_predictions = []
        yearly_predictions = []
        current_employees = float(initial_employees)

        # Les recrutements se font en janvier, les départs sont mensuels
        annual_recruitments = recruitments
        monthly_departures = departures / 12

        for year in range(start_year, end_year + 1):
            yearly_salary = 0
            cumulative_net_change = 0

            for month in range(1, 13):
                # Recrutements seulement en janvier
                monthly_recruitment = annual_recruitments if month == 1 else 0

                # Mettre à jour les employés au début du mois (ajout des recrues de janvier)
                if month == 1:
                    current_employees += monthly_recruitment

                # Calculer le changement net pour ce mois
                net_change = monthly_recruitment - monthly_departures
                cumulative_net_change += net_change

                # Utiliser current_employees pour chaque mois
                month_employees = max(1, current_employees)

                # Créer les features dans l'ordre attendu par le modèle
                input_data = {
                    'nbemp': month_employees,
                    'Year': year,
                    'Month': month,
                    'nb_departures': monthly_departures,
                    'cumulative_recruitments': annual_recruitments,
                    'cumulative_net_change': cumulative_net_change
                }

                df = pd.DataFrame([input_data])
                df = df[['nbemp', 'Year', 'Month', 'nb_departures', 'cumulative_recruitments', 'cumulative_net_change']]

                scaled_data = scaler.transform(df)
                monthly_prediction = model.predict(scaled_data)[0]
                monthly_prediction = max(0, monthly_prediction)
                yearly_salary += monthly_prediction

                monthly_predictions.append({
                    'Year': year,
                    'Month': month,
                    'Month_Name': pd.to_datetime(f'{year}-{month:02d}-01').strftime('%B'),
                    'Predicted_Salary': round(monthly_prediction, 2),
                    'Employees': int(round(month_employees))
                })

                # Mettre à jour current_employees pour le mois suivant (départs)
                current_employees -= monthly_departures
                current_employees = max(1, current_employees)

            yearly_predictions.append({
                'Year': year,
                'Total_Salary': round(yearly_salary, 2),
                'End_Employees': int(round(current_employees))
            })

        monthly_df = pd.DataFrame(monthly_predictions)
        yearly_df = pd.DataFrame(yearly_predictions)

        return monthly_df, yearly_df

    except Exception as e:
        print(f"Erreur dans predict_salaries_monthly: {e}")
        import traceback
        traceback.print_exc()
        raise


def predict_salaries(start_year, end_year, recruitments, departures, initial_employees):
    """
    Main prediction function - uses yearly model if available (better accuracy)
    Falls back to monthly model if needed
    """
    model_type = get_model_type()

    if model_type == 'yearly':
        print("Using yearly model (MAPE ~0.84%)")
        return predict_salaries_yearly(start_year, end_year, recruitments, departures, initial_employees)
    else:
        print("Using monthly model (fallback)")
        return predict_salaries_monthly(start_year, end_year, recruitments, departures, initial_employees)

def generate_graph(monthly_df):
    """Generate monthly prediction graph"""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import io
        import base64

        plt.figure(figsize=(14, 6))

        # Create X axis labels (Year-Month format)
        monthly_df['Period'] = monthly_df['Year'].astype(str) + '-' + monthly_df['Month'].astype(str).str.zfill(2)

        # Plot monthly predictions
        plt.plot(range(len(monthly_df)),
                 monthly_df['Predicted_Salary'],
                 marker='o', linewidth=2, markersize=6,
                 label='Monthly Mass Salary', color='#4CAF50')

        plt.xlabel('Period (Year-Month)', fontsize=12)
        plt.ylabel('Mass Salary', fontsize=12)
        plt.title('Mass Salary Prediction (Monthly Breakdown)', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3, linestyle='--')
        plt.legend(fontsize=10, labels=['Predicted Mass Salary'])

        # Format Y axis without currency symbol
        ax = plt.gca()
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        # Show fewer labels on X axis (every 3 months)
        step = max(1, len(monthly_df) // 12)
        tick_positions = range(0, len(monthly_df), step)
        tick_labels = [monthly_df['Period'].iloc[i] if i < len(monthly_df) else ''
                       for i in tick_positions]
        plt.xticks(tick_positions, tick_labels, rotation=45, ha='right', fontsize=9)

        plt.tight_layout()

        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        graph_base64 = base64.b64encode(buffer.read()).decode()
        plt.close()

        return f'data:image/png;base64,{graph_base64}'

    except Exception as e:
        print(f"Error generating graph: {e}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Graph error: {str(e)}")
