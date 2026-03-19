document.addEventListener('DOMContentLoaded', function() {
    console.log('JavaScript loaded');

    const form = document.getElementById('predictionForm');

    if (!form) {
        console.error('Form not found');
        return;
    }

    console.log('Form found');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form submission...');

        const loadingSpinner = document.getElementById('loadingSpinner');
        const errorAlert = document.getElementById('errorAlert');
        const resultsSection = document.getElementById('resultsSection');

        // Show spinner
        if (loadingSpinner) loadingSpinner.style.display = 'block';
        if (errorAlert) errorAlert.style.display = 'none';
        if (resultsSection) resultsSection.style.display = 'none';

        const formData = {
            start_year: parseInt(document.getElementById('start_year').value),
            end_year: parseInt(document.getElementById('end_year').value),
            recruitments: parseInt(document.getElementById('recruitments').value),
            departures: parseInt(document.getElementById('departures').value),
            initial_employees: parseInt(document.getElementById('initial_employees').value)
        };

        console.log('Data sent:', formData);

        try {
            // Fixed URL - use relative path to /predict endpoint
            const url = '/prediction/predict';
            console.log('URL called:', url);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            console.log('Response received:', response.status);

            const data = await response.json();
            console.log('Data received:', data);

            if (!response.ok || data.status === 'error') {
                showError(data.message || 'Prediction error');
                return;
            }

            displayResults(data);

        } catch (error) {
            console.error('Detailed error:', error);
            showError('Server connection error. Check that the server is running');
        } finally {
            if (loadingSpinner) loadingSpinner.style.display = 'none';
        }
    });
});

function showError(message) {
    console.error('Error displayed:', message);
    const errorAlert = document.getElementById('errorAlert');
    if (errorAlert) {
        errorAlert.textContent = message;
        errorAlert.style.display = 'block';
    }
}

function displayResults(data) {
    console.log('Displaying results...');
    const resultsSection = document.getElementById('resultsSection');
    if (!resultsSection) {
        console.error('Results section not found');
        return;
    }

    // Display the graph
    const graphImage = document.getElementById('graphImage');
    if (graphImage && data.graph) {
        graphImage.src = data.graph;
        console.log('Graph displayed');
    } else {
        console.warn('No graph or img element missing');
    }

    // Display metrics if available
    const metricsDiv = document.getElementById('modelMetrics');
    if (metricsDiv && data.metrics) {
        const m = data.metrics;
        metricsDiv.innerHTML =
            `<strong>Monthly:</strong> R² = ${m.monthly_r2} | RMSE = ${m.monthly_rmse.toLocaleString()} | MAE = ${m.monthly_mae.toLocaleString()}`;
        metricsDiv.style.display = 'block';
        console.log('Metrics displayed');
    }

    // Fill the table
    const tbody = document.getElementById('predictionsTable');
    if (tbody && data.predictions) {
        tbody.innerHTML = '';

        data.predictions.forEach(pred => {
            const row = tbody.insertRow();
            row.innerHTML = `
                <td>${pred.Year}</td>
                <td>${pred.Total_Salary.toLocaleString('en-US', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2
                })}</td>
                <td>${pred.End_Employees}</td>
            `;
        });

        console.log(`${data.predictions.length} rows added to table`);
    } else {
        console.error('No predictions or table missing');
    }

    resultsSection.style.display = 'block';
    console.log('Results section displayed');
}