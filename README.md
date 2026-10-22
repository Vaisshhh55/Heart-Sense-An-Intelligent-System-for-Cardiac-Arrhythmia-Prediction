# Heart Sense: An Intelligent System for Cardiac Arrhythmia Prediction

A Python desktop application for exploring cardiac arrhythmia predictions from patient measurements and ECG intervals. The project combines a trained machine-learning model with a graphical interface for predictions, risk-score calculations, prediction explanations, patient records, and PDF reports.

## What the project does

The application accepts seven inputs: age, sex, height, weight, QRS duration, QT interval, and T interval. Its included voting classifier combines K-nearest neighbors, random forest, gradient boosting, and support vector machine models to produce a prediction.

The desktop interface also provides:

- Prediction probabilities and a display of the predicted class.
- Optional model explanations when the explainer can be initialized.
- Several risk-score calculations, including CHA2DS2-VASc, TIMI, Framingham, HAS-BLED, and a custom arrhythmia score.
- Local patient and prediction record management.
- PDF report generation.

The codebase also contains a Flask API for single and batch predictions.

## Project structure

- `CARDIAC_ARRHYTHMIA_UPDATED/UI_Working.py` — desktop application.
- `CARDIAC_ARRHYTHMIA_UPDATED/api_server.py` — prediction API.
- `CARDIAC_ARRHYTHMIA_UPDATED/ensemble_model.joblib` — trained model used by the application.
- `CARDIAC_ARRHYTHMIA_UPDATED/requirements.txt` — Python dependencies.

## Run the desktop app

Requires Windows and Python 3.10 or newer. From the repository root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\CARDIAC_ARRHYTHMIA_UPDATED\requirements.txt
python .\CARDIAC_ARRHYTHMIA_UPDATED\UI_Working.py
```

On first launch, the application creates an admin account and displays its randomly generated password once. Save the password securely.

## Data and privacy

The application stores records and generated reports locally. Do not use real patient information unless you have the authorization and safeguards required for your setting. Local databases, reports, test data, and other generated files are excluded from Git.

## Intended use

This project is for education and research. It is not a validated medical device and must not be used to diagnose, treat, or make clinical decisions. Predictions and risk scores require independent clinical validation and professional interpretation.
