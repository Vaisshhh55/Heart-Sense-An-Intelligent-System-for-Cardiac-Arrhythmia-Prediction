"""
Working Cardiac Arrhythmia Prediction System UI
Simplified and optimized version without video dependencies
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import pickle
import joblib
import numpy as np
import json
import csv
import math
import io
from datetime import datetime
import os
import secrets
import sqlite3
import warnings
from reportlab.lib.utils import ImageReader
warnings.filterwarnings('ignore')

import logging

# Module logger
logger = logging.getLogger('cardiac')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Allow model unpickling of local trainer module
import sys
SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_ROOT not in sys.path:
    sys.path.insert(0, SCRIPT_ROOT)

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import custom modules
from database import PatientDatabase
from risk_scoring import RiskScoring
from explainability import SimpleFeatureImportance, ModelExplainer
from report_generator import PDFReportGenerator
from authentication import UserManager
from advanced_analytics import AdvancedAnalytics
from clinical_compliance import HIPAACompliance, FDARegulatoryCompliance

class CardiacArrhythmiaApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        width = int(screen_width * 0.90)
        height = int(screen_height * 0.82)
        left = max(10, (screen_width - width) // 2)
        top = max(10, (screen_height - height) // 2)
        self.window.geometry(f"{width}x{height}+{left}+{top}")
        self.window.minsize(900, 580)
        self.window.configure(bg='#edf5fc')
        self.window.resizable(True, True)
        self.window.grid_rowconfigure(0, weight=0)
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        self.current_user = None
        self.current_user_id = None
        self.current_role = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.feature_names = ['Age', 'Sex', 'Height', 'Weight', 'QRS', 'QT', 'T Interval']
        self.condition_map = {
            1: 'Normal',
            2: 'Ischemic changes (Coronary Artery)',
            3: 'Old Anterior Myocardial Infarction',
            4: 'Old Inferior Myocardial Infarction',
            5: 'Sinus tachycardia',
            6: 'Ventricular Premature Contraction (PVC)',
            7: 'Supraventricular Premature Contraction',
            8: 'Left bundle branch block',
            9: 'Right bundle branch block',
            10: 'Left ventricle hypertrophy',
            14: 'Atrial Fibrillation or Flutter',
            15: 'Others1',
            16: 'Others2'
        }
        self.model_loaded = False
        self.explainer = None
        self.last_prediction_data = None
        self.prediction_history = []
        self.model_version = 'unknown'
        self.settings_built = False
        # Confidence thresholds used to label confidence strings
        self.confidence_thresholds = {'low': 0.5, 'high': 0.85}

        self.setup_styles()

        logger.info("Initializing modules...")
        try:
            self.auth = UserManager(self.resolve_path('cardiac_auth.db'))
            self.ensure_default_user()
            self.db = PatientDatabase(self.resolve_path('cardiac_patients.db'))
            self.analytics = AdvancedAnalytics(self.resolve_path('cardiac_patients.db'), self.resolve_path('cardiac_auth.db'))
            self.hipaa = HIPAACompliance(self.resolve_path('hipaa_compliance.db'))
            self.fda = FDARegulatoryCompliance(self.resolve_path('fda_compliance.db'))
            self.pdf_gen = PDFReportGenerator(self.resolve_path('reports'))
            self.risk_scorer = RiskScoring()
            self.load_models()
            logger.info("All modules initialized successfully")
            self.build_login_screen()
        except Exception as e:
            logger.exception("Error initializing modules")
            messagebox.showerror("Initialization Error", f"Failed to initialize modules: {e}")
            return

    def resolve_path(self, path):
        """Resolve relative path against base dir."""
        return os.path.join(self.base_dir, path)

    def create_scrollable_tab(self, parent):
        """Create a vertically scrollable frame for long tab content."""
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0, bg='#edf5fc')
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner_frame = ttk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=inner_frame, anchor='nw')

        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            if canvas.winfo_height() > inner_frame.winfo_reqheight():
                canvas.itemconfig(window_id, height=canvas.winfo_height())

        def on_canvas_configure(event=None):
            canvas.itemconfig(window_id, width=event.width)
            if inner_frame.winfo_reqheight() < event.height:
                canvas.itemconfig(window_id, height=event.height)

        inner_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)

        return inner_frame

    def load_models(self):
        """Load ensemble model and SHAP explainer"""
        try:
            logger.info("Loading ensemble model...")
            self.ensemble_model = joblib.load(self.resolve_path('ensemble_model.joblib'))
            # capture version if present on the model object
            self.model_version = getattr(self.ensemble_model, 'version', '1.0')
            self.model_loaded = True
            # initialize explainer but keep it tolerant to failures
            self.explainer = self.initialize_explainer()
            logger.info("Ensemble model loaded (version: %s)", self.model_version)
        except Exception as e:
            self.model_loaded = False
            logger.exception("Error loading ensemble model")
            messagebox.showerror("Model Load Error", f"Failed to load model: {e}")

    def initialize_explainer(self):
        """Create a SHAP explainer using local background data if available."""
        try:
            data_path = self.resolve_path('test.csv')
            if os.path.exists(data_path):
                import pandas as pd
                df = pd.read_csv(data_path)
                if set(self.feature_names).issubset(df.columns):
                    X_train = df[self.feature_names].values
                else:
                    X_train = df.iloc[:, :len(self.feature_names)].values
            else:
                X_train = np.zeros((1, len(self.feature_names)))

            return ModelExplainer(self.ensemble_model, X_train, self.feature_names)
        except Exception as e:
            logger.warning("Unable to initialize SHAP explainer: %s", e)
            return None

    def ensure_settings_ui(self):
        """Ensure the Settings widgets exist before callbacks use them."""
        if getattr(self, 'settings_built', False):
            return True
        if hasattr(self, 'settings_frame'):
            try:
                self.build_settings_tab()
            except Exception as e:
                logger.exception('Failed to build Settings tab: %s', e)
                return False
            return getattr(self, 'settings_built', False)
        logger.warning('Settings frame not available to build Settings tab')
        return False

    def display_settings_message(self, message: str, switch_to_summary: bool = True):
        """Show plain text in the Settings summary pane."""
        if not self.ensure_settings_ui():
            return
        try:
            self.settings_text.delete(1.0, tk.END)
            self.settings_text.insert(tk.END, message)
            if switch_to_summary and hasattr(self, 'settings_notebook'):
                try:
                    self.settings_notebook.select(self.settings_notebook.tabs()[0])
                except Exception:
                    pass
        except Exception as e:
            logger.exception('Failed to display Settings message: %s', e)

    def calculate_risk_scores(self, age, sex, height, weight, qrs, qt, t_wave):
        """Calculate all clinical risk scores."""
        scores = self.risk_scorer.calculate_all_scores(age, sex, height, weight, qrs, qt, t_wave)
        scores['has_bled'] = self.risk_scorer.calculate_has_bled(age)
        return scores

    def identify_abnormal_parameters(self, age, sex, height, weight, qrs, qt, t_wave):
        """Identify abnormal ECG and clinical parameters."""
        abnormalities = []
        bmi = weight / ((height / 100) ** 2) if height > 0 else 0
        if qrs > 120:
            abnormalities.append({
                'parameter': 'QRS Duration',
                'value': f'{qrs:.1f} ms',
                'normal_range': '80-120 ms',
                'status': 'High',
                'clinical_meaning': 'Possible bundle branch block or ventricular conduction delay'
            })
        if qt > 450:
            status = 'Critical' if qt > 480 else 'High'
            abnormalities.append({
                'parameter': 'QT Interval',
                'value': f'{qt:.1f} ms',
                'normal_range': '350-450 ms',
                'status': status,
                'clinical_meaning': 'Prolonged repolarization with risk of torsades de pointes'
            })
        if bmi > 30:
            abnormalities.append({
                'parameter': 'BMI',
                'value': f'{bmi:.1f}',
                'normal_range': '18.5-24.9',
                'status': 'High',
                'clinical_meaning': 'Obesity increases cardiovascular risk and arrhythmia susceptibility'
            })
        if t_wave > 10:
            abnormalities.append({
                'parameter': 'T Interval',
                'value': f'{t_wave:.1f} ms',
                'normal_range': 'Depends on heart rate',
                'status': 'High',
                'clinical_meaning': 'Abnormal T interval may indicate repolarization issues or electrolyte imbalance'
            })
        if not abnormalities:
            abnormalities.append({
                'parameter': 'ECG Parameters',
                'value': 'Within expected range',
                'normal_range': 'n/a',
                'status': 'Normal',
                'clinical_meaning': 'No major ECG abnormalities detected'
            })
        return abnormalities

    def calculate_confidence(self, probabilities):
        """Calculate prediction confidence metrics.

        Returns a detailed confidence dict including top-1 probability, top-2 margin,
        normalized entropy, a simple calibration proxy and human-friendly flags.
        """
        probs = np.array(probabilities, dtype=float)
        if probs.sum() == 0:
            probs = np.ones_like(probs) / len(probs)
        probs = probs / probs.sum()
        top_idx = int(np.argmax(probs))
        top_prob = float(probs[top_idx])
        sorted_idx = np.argsort(probs)[::-1]
        second_prob = float(probs[sorted_idx[1]]) if len(probs) > 1 else 0.0
        margin = top_prob - second_prob

        # entropy normalized to [0,1]
        entropy = -float(np.sum([p * np.log2(p) for p in probs if p > 0]))
        max_entropy = math.log2(len(probs)) if len(probs) > 1 else 1.0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

        # simple calibration proxy: higher margin and lower entropy -> higher calibration
        calibration = float(max(0.0, 1.0 - normalized_entropy) * (0.5 + 0.5 * margin))

        distribution = {self.condition_map.get(i, str(i)): float(p) for i, p in enumerate(probs)}

        # flags
        low_confidence = (top_prob < 0.6) or (margin < 0.15) or (normalized_entropy > 0.6)

        return {
            'confidence_score': top_prob,
            'top_index': top_idx,
            'top_probability': top_prob,
            'second_probability': second_prob,
            'margin': margin,
            'entropy': entropy,
            'normalized_entropy': normalized_entropy,
            'calibration': calibration,
            'low_confidence_flag': bool(low_confidence),
            'distribution': distribution
        }

    def calculate_shap_values(self, features, prediction, probabilities):
        """Generate SHAP explanations and natural language reasoning."""
        if self.explainer is None:
            return {
                'method': 'fallback',
                'features': [],
                'positive_contributors': [],
                'negative_contributors': [],
                'natural_language': 'SHAP explanation is unavailable. This is a fallback explanation based on feature importance.',
                'prediction': int(prediction),
                'confidence': float(np.max(probabilities))
            }

        explanation = self.explainer.explain_prediction(features, class_names=self.condition_map)
        feature_list = []
        positive = []
        negative = []
        for fname, data in explanation.get('features', {}).items():
            contribution = float(data.get('shap_value', data.get('permutation_importance', 0)))
            feature_list.append({
                'name': fname,
                'value': float(data.get('feature_value', 0)),
                'shap_value': contribution,
                'direction': 'Positive' if contribution > 0 else 'Negative',
                'magnitude': abs(contribution)
            })
            if contribution > 0:
                positive.append(fname)
            else:
                negative.append(fname)

        sorted_features = sorted(feature_list, key=lambda x: x['magnitude'], reverse=True)
        top_text = []
        for item in sorted_features[:5]:
            sign = '+' if item['shap_value'] > 0 else ''
            top_text.append(f"{item['name']} ({sign}{item['shap_value']:.3f})")

        natural_language = (
            f"The prediction was driven by the most strongly weighted ECG and clinical features. "
            f"{top_text[0]} and {top_text[1] if len(top_text) > 1 else 'other factors'} increased the probability of the predicted condition. "
            f"Features with negative contributions provide evidence against alternate diagnoses."
        )

        return {
            'method': 'shap',
            'features': sorted_features,
            'positive_contributors': positive[:3],
            'negative_contributors': negative[:3],
            'natural_language': natural_language,
            'prediction': explanation.get('prediction'),
            'confidence': explanation.get('confidence', float(np.max(probabilities)))
        }

    def generate_recommendations(self, condition_name, risk_scores, abnormalities, confidence):
        """Generate personalized clinical recommendations."""
        recs = []

        high_risk = any(
            isinstance(score_info, dict) and score_info.get('risk_level') in ['High', 'Very High']
            for score_info in risk_scores.values()
        )
        moderate_risk = any(
            isinstance(score_info, dict) and score_info.get('risk_level') in ['Moderate', 'Moderate-High', 'Low-Moderate']
            for score_info in risk_scores.values()
        )

        if high_risk:
            recs.append('High-risk findings detected. Consider urgent specialist review and close monitoring.')
        elif confidence < 0.50:
            recs.append('Prediction confidence is low. Recheck the ECG data and patient history before changing management.')
        elif confidence < 0.80 and moderate_risk:
            recs.append('Prediction confidence is moderate and risk is not high. Correlate with ECG and clinical history before escalation.')
        elif confidence < 0.80:
            recs.append('Prediction confidence is moderate. Recommend clinical correlation with ECG and history.')

        if 'Atrial Fibrillation' in condition_name or 'Flutter' in condition_name:
            recs.extend([
                'Recommend cardiology consultation within 24 hours if symptoms are active.',
                'Consider 12-lead ECG and 24-hour Holter monitoring.',
                'Evaluate anticoagulation strategy based on CHA2DS2-VASc.'
            ])
        if 'Ischemic' in condition_name or 'Myocardial Infarction' in condition_name:
            recs.extend([
                'Assess for acute coronary syndrome and initiate urgent evaluation.',
                'Check cardiac biomarkers and obtain imaging as indicated.'
            ])
        if risk_scores.get('custom_arrhythmia', {}).get('risk_level') in ['High', 'Very High']:
            recs.append('High arrhythmia risk detected – consider inpatient monitoring and expert review.')
        for abnormal in abnormalities:
            if abnormal['status'] in ['Critical', 'High']:
                recs.append(f"{abnormal['parameter']} abnormality detected: {abnormal['clinical_meaning']}.")
        if not recs:
            recs.append('Routine follow-up and standard preventive cardiovascular care.')
        return recs

    def generate_clinical_summary(self, name, condition_name, confidence, risk_scores, abnormalities, explanation_text, recommendations):
        """Generate a full clinical report text summary."""
        overall_risk = risk_scores.get('custom_arrhythmia', {}).get('risk_level', 'Moderate')
        severity = 'Moderate to Severe' if overall_risk in ['High', 'Very High'] else 'Moderate'
        urgency = 'Consult Cardiologist within 24 hours' if overall_risk in ['High', 'Very High'] else 'Follow up with clinician soon'
        confidence_level = self.get_confidence_level(confidence)

        summary = f"""
Prediction: High Probability of {condition_name}
Confidence: {confidence*100:.1f}% ({confidence_level})
Overall Risk: {overall_risk}
Severity: {severity}
Urgency: {urgency}

Why this prediction was made:
{explanation_text}

Abnormal Parameters:
"""
        for abnormal in abnormalities:
            summary += (
                f"- {abnormal['parameter']}: {abnormal['value']} "
                f"(Normal: {abnormal['normal_range']}) Status: {abnormal['status']} - {abnormal['clinical_meaning']}\n"
            )
        summary += '\nRisk Score Module:\n'
        for score_type, score_info in risk_scores.items():
            if isinstance(score_info, dict):
                summary += f"- {score_type.replace('_', ' ').title()}: {score_info.get('score', 'N/A')} "
                summary += f"({score_info.get('risk_level', 'N/A')})\n"
                for detail, value in score_info.get('details', {}).items():
                    summary += f"  * {detail} +{value}\n"
        summary += '\nPersonalized Recommendations:\n'
        for rec in recommendations:
            summary += f"- {rec}\n"
        return summary

    def get_confidence_level(self, confidence_score):
        """Return a confidence level string for a probability score."""
        if confidence_score < self.confidence_thresholds['low']:
            return 'Low Confidence'
        if confidence_score <= self.confidence_thresholds['high']:
            return 'Moderate Confidence'
        return 'High Confidence'

    def generate_pdf_report(self, patient_data, prediction_data, risk_scores, explanation_data, abnormalities, recommendations):
        """Export a professional PDF report for the current prediction."""
        patient_record = self.db.get_patient_by_name(patient_data.get('name', ''))
        if patient_record:
            patient_data['patient_id'] = patient_record['patient_id']
        t_interval = prediction_data.get('t_interval') or prediction_data.get('t_wave')
        if t_interval is not None:
            prediction_data['t_interval'] = t_interval
        prediction_data['model_version'] = self.model_version
        if 'report_id' not in prediction_data or not prediction_data.get('report_id'):
            prediction_data['report_id'] = f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Pass the explanation payload directly so the report generator can access
        # natural language, feature contributions, and SHAP values correctly.
        return self.pdf_gen.generate_prediction_report(
            patient_data,
            prediction_data,
            risk_scores,
            explanation_data
        )

    def download_prediction_report(self):
        """Download a PDF report for the last prediction."""
        if not self.last_prediction_data:
            messagebox.showwarning('Report Error', 'Please run a prediction before exporting a clinical report.')
            return
        try:
            filename = self.generate_pdf_report(
                self.last_prediction_data['patient_data'],
                self.last_prediction_data['prediction_data'],
                self.last_prediction_data['risk_scores'],
                self.last_prediction_data['explanation_data'],
                self.last_prediction_data['abnormal_parameters'],
                self.last_prediction_data['recommendations']
            )
            report_id = self.last_prediction_data['prediction_data'].get('report_id', '')
            prediction_id = self.last_prediction_data.get('prediction_id')
            if prediction_id:
                self.db.update_prediction_report_info(prediction_id, filename, report_id)
            messagebox.showinfo('Report Generated', f'Clinical PDF report saved to {filename}')
        except Exception as e:
            logger.exception('PDF export exception')
            messagebox.showerror('Report Error', 'Failed to generate the clinical PDF report. Please try again.')
    
    def setup_styles(self):
        """Configure the GUI theme and colors."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        style.configure('Custom.TNotebook', background='#e8f1fb', tabmargins=[2, 4, 2, 0])
        style.configure('Custom.TNotebook.Tab', font=('Segoe UI Semibold', 9), padding=[12, 6], background='#dbe9f8')
        style.map('Custom.TNotebook.Tab', background=[('selected', '#0f4c75')], foreground=[('selected', '#ffffff')])
        style.layout('Hidden.TNotebook', [('Notebook.client', {'sticky': 'nswe'})])
        style.layout('Hidden.TNotebook.Tab', [])

        style.configure('TEntry', padding=4, font=('Segoe UI', 9))
        style.configure('TCombobox', padding=4, font=('Segoe UI', 9))
        style.configure('Card.TFrame', background='#ffffff', relief='flat')
        style.configure('Card.TLabelframe', background='#f7fbff', borderwidth=1)
        style.configure('Card.TLabelframe.Label', font=('Segoe UI Semibold', 12), foreground='#0f4c75')
        style.configure('Section.TLabelframe', background='#eef6ff', borderwidth=1, relief='groove')
        style.configure('Section.TLabelframe.Label', font=('Segoe UI Semibold', 13), foreground='#0f4c75')
        style.configure('FieldLabel.TLabel', background='#f7fbff', foreground='#26465d', font=('Segoe UI', 9))
        style.configure('Info.TLabel', background='#f7fbff', foreground='#4b6c80', font=('Segoe UI', 10))
        style.configure('Metric.TLabel', background='#ffffff', font=('Segoe UI', 10))
        style.configure('MetricValue.TLabel', background='#ffffff', font=('Segoe UI Bold', 18), foreground='#0f4c75')
        style.configure('Action.TButton', font=('Segoe UI Semibold', 9), foreground='#ffffff', background='#0c6fb6', borderwidth=0, focusthickness=3, focuscolor='#7aa7d9', padding=5)
        style.map('Action.TButton', background=[('active', '#09538c'), ('disabled', '#b0bed9')])

        style.configure('Nav.TButton', font=('Segoe UI Semibold', 11), foreground='#ffffff', background='#0f4c75', borderwidth=0, focusthickness=3, focuscolor='#7aa7d9', padding=8)
        style.map('Nav.TButton', background=[('active', '#0b4e7d'), ('disabled', '#7a9ebd')])

        style.configure('Small.TButton', font=('Segoe UI Semibold', 9), foreground='#ffffff', background='#3876b8', borderwidth=0, padding=8)
        style.map('Small.TButton', background=[('active', '#2f67a0'), ('disabled', '#b0bed9')])

        style.configure('Sidebar.TLabel', background='#0f4c75', foreground='#ffffff', font=('Segoe UI Semibold', 13))
        style.configure('SidebarSmall.TLabel', background='#0f4c75', foreground='#d7e8ff', font=('Segoe UI', 10))
        style.configure('Dashboard.TLabelframe', background='#f2f7fb', borderwidth=0)
        style.configure('Dashboard.TLabelframe.Label', font=('Segoe UI Semibold', 12), foreground='#0f4c75')
        style.configure('DashboardCard.TFrame', background='#eef5fc', borderwidth=1, relief='solid')
        style.configure('DashboardCardTitle.TLabel', background='#eef5fc', foreground='#0f4c75', font=('Segoe UI Semibold', 11))
        style.configure('DashboardCardValue.TLabel', background='#eef5fc', foreground='#0f4c75', font=('Segoe UI Bold', 28))
        style.configure('DashboardCardNote.TLabel', background='#eef5fc', foreground='#3a5d78', font=('Segoe UI', 9))

        style.configure('TopBar.TFrame', background='#ffffff', relief='flat')
        style.configure('TopBar.TLabel', background='#ffffff', foreground='#0f4c75', font=('Segoe UI Semibold', 13))
        style.configure('TopBarSmall.TLabel', background='#ffffff', foreground='#4b6c80', font=('Segoe UI', 8))
        style.configure('SidebarButton.TButton', font=('Segoe UI Semibold', 10), foreground='#ffffff', background='#0f4c75', borderwidth=0, padding=6)
        style.map('SidebarButton.TButton', background=[('active', '#0b4e7d'), ('disabled', '#7a9ebd')])
        style.configure('MetricCard.TFrame', background='#ffffff', borderwidth=1, relief='solid')
        style.configure('MetricCard.TLabel', background='#ffffff', foreground='#3a5d78', font=('Segoe UI', 9))
        style.configure('MetricCardValue.TLabel', background='#ffffff', foreground='#0f4c75', font=('Segoe UI Bold', 20))
        style.configure('CardSection.TFrame', background='#f7fbff', relief='flat')

        style.configure('Header.TFrame', background='#f7fbff', relief='flat')
        style.configure('HeaderTitle.TLabel', background='#f7fbff', foreground='#0f4c75', font=('Segoe UI Semibold', 22))
        style.configure('HeaderSubtitle.TLabel', background='#f7fbff', foreground='#4b6c80', font=('Segoe UI', 11))
        style.configure('SectionHeader.TLabel', background='#f7fbff', foreground='#0f4c75', font=('Segoe UI Semibold', 12))
        style.configure('MetricCard.TFrame', background='#ffffff', borderwidth=1, relief='solid')
        style.configure('MetricCard.TLabel', background='#ffffff', foreground='#3a5d78', font=('Segoe UI', 10))
        style.configure('MetricCardValue.TLabel', background='#ffffff', foreground='#0f4c75', font=('Segoe UI Bold', 16))
        style.configure('Detail.TLabel', background='#f7fbff', foreground='#0f4c75', font=('Segoe UI', 10))

        style.configure('TopBar.TFrame', background='#ffffff', relief='flat')
        style.configure('TopBar.TLabel', background='#ffffff', foreground='#0f4c75', font=('Segoe UI Semibold', 14))
        style.configure('TopBarSmall.TLabel', background='#ffffff', foreground='#4b6c80', font=('Segoe UI', 10))
        style.configure('Sidebar.TFrame', background='#0f4c75')
        style.configure('SidebarButton.TButton', font=('Segoe UI Semibold', 11), foreground='#ffffff', background='#0f4c75', borderwidth=0, padding=12)
        style.map('SidebarButton.TButton', background=[('active', '#0b4e7d'), ('disabled', '#7a9ebd')])
        style.configure('SidebarLabel.TLabel', background='#0f4c75', foreground='#d7e8ff', font=('Segoe UI', 11))

    def create_header(self):
        """Build the application header with clinic branding."""
        header = tk.Frame(self.window, bg='#0f4c75', height=56)
        header.grid(row=0, column=0, sticky='ew')
        header.grid_columnconfigure(0, weight=1)
        header.grid_propagate(False)

        canvas = tk.Canvas(header, bg='#0f4c75', highlightthickness=0)
        canvas.grid(row=0, column=0, sticky='nsew')
        header.grid_rowconfigure(0, weight=1)

        def redraw_header(event=None):
            width = event.width if event else canvas.winfo_width()
            height = event.height if event else canvas.winfo_height()
            self.draw_header(canvas, width, height)

        canvas.bind('<Configure>', redraw_header)
        redraw_header()

    def draw_header(self, canvas, width, height):
        """Redraw the header graphics responsively."""
        canvas.delete('all')
        if width <= 0 or height <= 0:
            return

        padding = 20
        radius = min(36, max(18, height // 4))
        circle_x = padding + radius
        circle_y = height // 2
        canvas.create_oval(circle_x - radius, circle_y - radius, circle_x + radius, circle_y + radius, fill='#ff4d4d', outline='')

        offset = radius + 24
        line_base = circle_y
        canvas.create_line(circle_x + offset, line_base, circle_x + offset + 55, line_base, fill='#60a3d9', width=4)
        canvas.create_line(circle_x + offset + 55, line_base, circle_x + offset + 80, line_base - 20, fill='#60a3d9', width=4)
        canvas.create_line(circle_x + offset + 80, line_base - 20, circle_x + offset + 100, line_base + 14, fill='#60a3d9', width=4)
        canvas.create_line(circle_x + offset + 100, line_base + 14, circle_x + offset + 120, line_base - 40, fill='#60a3d9', width=4)
        canvas.create_line(circle_x + offset + 120, line_base - 40, circle_x + offset + 170, line_base - 40, fill='#60a3d9', width=4)

        title_x = circle_x + offset + 190
        title_y = circle_y - 10
        canvas.create_text(title_x, title_y, text='CardioClinic AI', fill='#ffffff', font=('Segoe UI Semibold', max(18, min(24, height // 5))), anchor='w')
        canvas.create_text(title_x, title_y + 26, text='Clinical-grade arrhythmia decision support', fill='#d7e8ff', font=('Segoe UI', max(9, min(12, height // 8))), anchor='w')
       

    def ensure_default_user(self):
        """Create an admin account with a one-time password on first run."""
        conn = sqlite3.connect(self.auth.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
        finally:
            conn.close()

        if count == 0:
            password = secrets.token_urlsafe(24)
            created, result = self.auth.create_user(
                username='admin',
                email='admin@cardio.ai',
                password=password,
                role=UserManager.ROLE_ADMIN,
                first_name='System',
                last_name='Admin'
            )
            if not created:
                raise RuntimeError(result.get('error', 'Failed to create the initial admin account'))
            messagebox.showinfo(
                'Initial Admin Account',
                'A one-time admin account was created.\n\n'
                'Username: admin\n'
                f'Password: {password}\n\n'
                'Save this password securely. It will not be shown again.'
            )

    def user_has_permission(self, permission: str) -> bool:
        """Check whether the current user has a specific permission."""
        if not self.current_user_id:
            return False
        return self.auth.check_permission(self.current_user_id, permission)

    def can_access_patient_management(self) -> bool:
        """Return true if the user may see patient management features."""
        return any([
            self.user_has_permission('view_all_patients'),
            self.user_has_permission('view_assigned_patients'),
            self.user_has_permission('view_patient_data')
        ])

    def can_access_analytics(self) -> bool:
        """Return true if the user may see analytics features."""
        return self.user_has_permission('view_analytics')

    def can_access_compliance(self) -> bool:
        """Return true if the user may see compliance and settings features."""
        return self.user_has_permission('manage_settings') or self.current_role == UserManager.ROLE_ADMIN

    def build_login_screen(self):
        """Render the secure login screen."""
        self.login_frame = tk.Frame(self.window, bg='#0f4c75')
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        self.login_frame.grid_rowconfigure(0, weight=1)
        self.login_frame.grid_columnconfigure(0, weight=1)
        self.login_frame.grid_columnconfigure(1, weight=1)

        left_panel = tk.Frame(self.login_frame, bg='#0f4c75')
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(20, 10), pady=20)

        logo = tk.Label(left_panel, text='CardioClinic AI', bg='#0f4c75', fg='#ffffff', font=('Segoe UI Bold', 32))
        logo.pack(pady=(80, 10), padx=40, anchor='w')
        subtitle = tk.Label(left_panel, text='Secure clinical access for doctors and staff', bg='#0f4c75', fg='#d7e8ff', font=('Segoe UI', 14))
        subtitle.pack(pady=(0, 30), padx=40, anchor='w')

        features = [
            '• Secure HIPAA-compliant login',
            '• Clinical prediction & monitoring modules',
            '• Advanced analytics and audit trail'
        ]
        for feature in features:
            tk.Label(left_panel, text=feature, bg='#0f4c75', fg='#d7e8ff', font=('Segoe UI', 12)).pack(anchor='w', padx=40, pady=4)

        right_panel = tk.Frame(self.login_frame, bg='#edf5fc')
        right_panel.grid(row=0, column=1, sticky='nsew', padx=(10, 20), pady=20)
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        card = tk.Frame(right_panel, bg='#ffffff', bd=1, relief=tk.RIDGE)
        card.grid(row=0, column=0, sticky='nsew', padx=24, pady=24)
        card.grid_columnconfigure(0, weight=1)

        tk.Label(card, text='Staff Sign In', bg='#ffffff', fg='#0f4c75', font=('Segoe UI Semibold', 20)).pack(pady=(30, 10))
        tk.Label(card, text='Enter your credentials to access the CardioClinic platform.', bg='#ffffff', fg='#3a495c', font=('Segoe UI', 10)).pack(pady=(0, 24))

        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()

        form_frame = tk.Frame(card, bg='#ffffff')
        form_frame.pack(padx=40, pady=20, fill=tk.X)

        form_frame.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(1, weight=2)

        tk.Label(form_frame, text='Username', bg='#ffffff', fg='#3a495c', font=('Segoe UI', 11)).grid(row=0, column=0, sticky='w', pady=(0, 6))
        ttk.Entry(form_frame, textvariable=self.username_var).grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 16))

        tk.Label(form_frame, text='Password', bg='#ffffff', fg='#3a495c', font=('Segoe UI', 11)).grid(row=2, column=0, sticky='w', pady=(0, 6))
        ttk.Entry(form_frame, textvariable=self.password_var, show='*').grid(row=3, column=0, columnspan=2, sticky='ew', pady=(0, 18))

        ttk.Button(card, text='Sign In', command=self.authenticate_user, style='Action.TButton').pack(pady=(6, 12), ipadx=10, ipady=8)

    def authenticate_user(self):
        """Authenticate the staff user and load the main dashboard."""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()

        if not username or not password:
            messagebox.showwarning('Login Error', 'Please enter both username and password')
            return

        success, result = self.auth.authenticate(username, password, ip_address='127.0.0.1', user_agent='CardioClinicUI')
        if not success:
            messagebox.showerror('Login Failed', result.get('error', 'Authentication failed'))
            return

        self.current_user = result
        self.current_user_id = result['user_id']
        self.current_role = result['role']
        self.login_frame.destroy()
        self.build_main_app()

    def build_main_app(self):
        """Build the main dashboard after successful login."""
        self.create_header()

        self.app_container = tk.Frame(self.window, bg='#edf5fc')
        self.app_container.grid(row=1, column=0, sticky='nsew')
        self.app_container.grid_rowconfigure(0, weight=1)
        self.app_container.grid_columnconfigure(1, weight=1)

        sidebar = ttk.Frame(self.app_container, style='Sidebar.TFrame', width=170)
        sidebar.grid(row=0, column=0, rowspan=2, sticky='ns')
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(0, weight=0)
        sidebar.grid_rowconfigure(1, weight=1)

        content = ttk.Frame(self.app_container, style='Card.TFrame')
        content.grid(row=0, column=1, sticky='nsew')
        content.grid_rowconfigure(1, weight=1)
        content.grid_columnconfigure(0, weight=1)

        user_label = tk.Label(sidebar, text=f"{self.current_user.get('full_name', self.current_user.get('username'))}", bg='#0f4c75', fg='#ffffff', font=('Segoe UI Semibold', 16))
        user_label.pack(pady=(20, 4), padx=18, anchor='w')

        role_label = tk.Label(sidebar, text=f"Role: {self.current_role.title()}", bg='#0f4c75', fg='#d7e8ff', font=('Segoe UI', 10))
        role_label.pack(padx=18, anchor='w')

        tk.Frame(sidebar, bg='#ffffff', height=1).pack(fill=tk.X, padx=20, pady=(18, 18))

        nav_buttons = []
        nav_buttons.append(('Prediction', lambda: self.notebook.select(self.prediction_frame)))

        if self.can_access_patient_management():
            nav_buttons.append(('Patients', lambda: self.notebook.select(self.patient_frame)))

        if self.can_access_analytics():
            nav_buttons.append(('Analytics', lambda: self.notebook.select(self.analytics_frame)))

        if self.can_access_compliance():
            nav_buttons.append(('Compliance', lambda: self.notebook.select(self.settings_frame)))

        nav_buttons.append(('Sign Out', self.logout_user))

        for text, command in nav_buttons:
            btn = ttk.Button(sidebar, text=text, command=command, style='SidebarButton.TButton')
            btn.pack(fill=tk.X, padx=14, pady=5, ipady=6)
            btn.bind('<Enter>', lambda e: e.widget.configure(cursor='hand2'))

        top_bar = ttk.Frame(content, style='TopBar.TFrame')
        top_bar.grid(row=0, column=0, sticky='ew', padx=10, pady=(8, 3))
        top_bar.grid_columnconfigure(0, weight=1)

        ttk.Label(top_bar, text='Clinical Intelligence Hub', style='TopBar.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(top_bar, text='Streamlined prediction and patient management .', style='TopBarSmall.TLabel').grid(row=1, column=0, sticky='w', pady=(4, 0))

        self.notebook = ttk.Notebook(content, style='Hidden.TNotebook')
        self.notebook.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 10))

        self.prediction_frame = ttk.Frame(self.notebook)
        self.patient_frame = ttk.Frame(self.notebook)
        self.analytics_frame = ttk.Frame(self.notebook)
        self.settings_frame = ttk.Frame(self.notebook)

        if self.user_has_permission('run_predictions') or self.user_has_permission('view_patient_data'):
            self.notebook.add(self.prediction_frame, text='Prediction')
        if self.can_access_patient_management():
            self.notebook.add(self.patient_frame, text='Patient Management')
        if self.can_access_analytics():
            self.notebook.add(self.analytics_frame, text='Analytics')
        if self.can_access_compliance():
            self.notebook.add(self.settings_frame, text='Settings')

        if self.notebook.index('end') > 0:
            self.notebook.select(0)

        logger.info('Building UI...')
        if self.user_has_permission('run_predictions') or self.user_has_permission('view_patient_data'):
            self.build_prediction_tab()
        if self.can_access_patient_management():
            self.build_patient_tab()
        if self.can_access_analytics():
            self.build_analytics_tab()
        if self.can_access_compliance():
            self.build_settings_tab()
        logger.info('UI built successfully')

    def logout_user(self):
        """Return to the login screen."""
        for child in self.window.winfo_children():
            child.destroy()
        self.current_user = None
        self.current_user_id = None
        self.current_role = None
        self.build_login_screen()

    def draw_clinic_visual(self, canvas):
        """Draw a clinical-style heart and ECG trace."""
        width = max(canvas.winfo_width(), 1)
        height = max(canvas.winfo_height(), 1)
        scale = min(width / 520, height / 170)
        canvas.delete('all')
        canvas.create_rectangle(0, 0, width, height, fill='#0f4c75', outline='')
        margin = 20 * scale
        x1 = margin
        y1 = height * 0.68
        line_width = max(1, round(4 * scale))
        canvas.create_line(x1, y1, x1 + 70 * scale, y1, fill='#60a3d9', width=line_width)
        canvas.create_line(x1 + 70 * scale, y1, x1 + 95 * scale, y1 - 45 * scale, fill='#60a3d9', width=line_width)
        canvas.create_line(x1 + 95 * scale, y1 - 45 * scale, x1 + 115 * scale, y1 + 15 * scale, fill='#60a3d9', width=line_width)
        canvas.create_line(x1 + 115 * scale, y1 + 15 * scale, x1 + 135 * scale, y1 - 65 * scale, fill='#60a3d9', width=line_width)
        canvas.create_line(x1 + 135 * scale, y1 - 65 * scale, x1 + 185 * scale, y1 - 5 * scale, fill='#60a3d9', width=line_width)
        canvas.create_line(x1 + 185 * scale, y1 - 5 * scale, x1 + 245 * scale, y1 - 5 * scale, fill='#60a3d9', width=line_width)
        heart_x = min(width * 0.65, width - 120 * scale)
        canvas.create_oval(heart_x - 80 * scale, margin + 15 * scale, heart_x, margin + 95 * scale, fill='#ff4d4d', outline='')
        canvas.create_polygon(heart_x - 40 * scale, margin + 25 * scale, heart_x - 25 * scale, margin + 5 * scale, heart_x - 5 * scale, margin + 20 * scale, heart_x + 15 * scale, margin + 5 * scale, heart_x + 30 * scale, margin + 25 * scale, heart_x + 20 * scale, margin + 50 * scale, heart_x - 5 * scale, margin + 75 * scale, fill='#ffffff', outline='')
        text_x = min(width * 0.7, max(margin, width - 220 * scale))
        title_size = max(8, round(14 * scale))
        detail_size = max(7, round(10 * scale))
        text_width = max(1, width - text_x - margin)
        canvas.create_text(text_x, height * 0.3, text='Clinical ECG review', fill='#ffffff', font=('Segoe UI Semibold', title_size), anchor='w', width=text_width)
        canvas.create_text(text_x, height * 0.53, text='Instant arrhythmia visualization and patient trend overview.', fill='#d7e8ff', font=('Segoe UI', detail_size), anchor='w', width=text_width)

    # ==================== PREDICTION TAB ====================
    
    def build_prediction_tab(self):
        """Build prediction tab"""
        self.input_vars = {}
        self.prediction_frame.grid_rowconfigure(0, weight=0)
        self.prediction_frame.grid_rowconfigure(1, weight=1)
        self.prediction_frame.grid_rowconfigure(2, weight=1)
        self.prediction_frame.grid_columnconfigure(0, weight=1)

        scroll_parent = self.create_scrollable_tab(self.prediction_frame)
        scroll_parent.grid_columnconfigure(0, weight=1)
        scroll_parent.grid_rowconfigure(1, weight=1)
        scroll_parent.grid_rowconfigure(2, weight=1)
        top_card = ttk.Frame(scroll_parent, style='TopBar.TFrame', padding=(10, 8))
        top_card.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 4))
        top_card.grid_columnconfigure(0, weight=1)

        ttk.Label(top_card, text='Prediction Workspace', style='TopBar.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(top_card, text='Professional clinical risk assessment for arrhythmia care teams.', style='TopBarSmall.TLabel').grid(row=1, column=0, sticky='w', pady=(4, 0))
        ttk.Label(top_card, text='Enter patient details, run the prediction, and review findings in one responsive, clean workflow.', style='TopBarSmall.TLabel').grid(row=2, column=0, sticky='w', pady=(2, 0))

        main_area = ttk.Frame(scroll_parent, style='CardSection.TFrame', padding=(0, 0, 0, 0))
        main_area.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0, 8))
        main_area.grid_rowconfigure(0, weight=1)
        main_area.grid_columnconfigure(0, weight=1)
        main_area.grid_columnconfigure(1, weight=2)

        left_panel = ttk.Frame(main_area, style='Card.TFrame')
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=(0, 10))
        left_panel.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)

        intake_card = ttk.LabelFrame(left_panel, text='Patient Intake', padding=10, style='Section.TLabelframe')
        intake_card.grid(row=0, column=0, sticky='nsew')
        intake_card.grid_columnconfigure(0, weight=1)
        intake_card.grid_columnconfigure(1, weight=1)

        fields = [
            ('Patient Name', 'name'),
            ('Age (years)', 'age'),
            ('Sex (M/F)', 'sex'),
            ('Height (cm)', 'height'),
            ('Weight (kg)', 'weight'),
            ('QRS Duration (ms)', 'qrs'),
            ('QT Interval (ms)', 'qt'),
            ('T Interval (ms)', 't_wave')
        ]

        for idx, (label, key) in enumerate(fields):
            ttk.Label(intake_card, text=label, style='FieldLabel.TLabel').grid(row=idx, column=0, sticky='w', padx=8, pady=6)
            var = tk.StringVar()
            self.input_vars[key] = var
            if key == 'sex':
                ttk.Combobox(intake_card, textvariable=var, values=['M', 'F'], state='readonly').grid(row=idx, column=1, padx=8, pady=6, sticky='ew')
                var.set('M')
            else:
                ttk.Entry(intake_card, textvariable=var).grid(row=idx, column=1, padx=8, pady=6, sticky='ew')

        action_row = ttk.Frame(intake_card)
        action_row.grid(row=len(fields), column=0, columnspan=2, sticky='ew', padx=4, pady=(10, 4))
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=1)
        action_row.grid_columnconfigure(2, weight=1)

        ttk.Button(action_row, text='Run Prediction', command=self.predict_and_analyze, style='Action.TButton').grid(row=0, column=0, sticky='ew', padx=(0, 6))
        ttk.Button(action_row, text='Export PDF', command=self.download_prediction_report, style='Action.TButton').grid(row=0, column=1, sticky='ew', padx=3)
        ttk.Button(action_row, text='Export History', command=self.export_prediction_history, style='Action.TButton').grid(row=0, column=2, sticky='ew', padx=(6, 0))

        self.pred_progress = ttk.Progressbar(intake_card, mode='determinate', maximum=100)
        self.pred_progress.grid(row=len(fields)+1, column=0, columnspan=2, sticky='ew', padx=10, pady=(10, 4))
        self.pred_status = ttk.Label(intake_card, text='Ready', style='Detail.TLabel')
        self.pred_status.grid(row=len(fields)+2, column=0, columnspan=2, sticky='ew', padx=10, pady=(0, 12))

        right_panel = ttk.Frame(main_area, style='Card.TFrame')
        right_panel.grid(row=0, column=1, sticky='nsew', pady=(0, 10))
        right_panel.grid_rowconfigure(0, weight=0)
        right_panel.grid_rowconfigure(1, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        overview_card = ttk.LabelFrame(right_panel, text='Prediction Summary', padding=10, style='Section.TLabelframe')
        overview_card.grid(row=0, column=0, sticky='nsew', padx=3, pady=(0, 10))
        overview_card.grid_columnconfigure(0, weight=1)

        self.condition_label = ttk.Label(overview_card, text='Awaiting clinical input...', style='TopBar.TLabel')
        self.condition_label.grid(row=0, column=0, sticky='w', pady=(0, 12), padx=8)

        metrics_frame = ttk.Frame(overview_card)
        metrics_frame.grid(row=1, column=0, sticky='ew', padx=3, pady=(0, 6))
        for column in range(3):
            metrics_frame.grid_columnconfigure(column, weight=1, uniform='metric_card')

        for idx, (text, var_name) in enumerate([
            ('Confidence', 'confidence_label'),
            ('Risk Level', 'risk_summary_label'),
            ('BMI', 'bmi_label')
        ]):
            card = ttk.Frame(metrics_frame, style='MetricCard.TFrame', padding=(6, 10))
            card.grid(row=0, column=idx, sticky='nsew', padx=2)
            card.grid_columnconfigure(0, weight=1)
            ttk.Label(card, text=text, style='MetricCard.TLabel', anchor='center').grid(row=0, column=0, sticky='ew', pady=(0, 6))
            setattr(self, var_name, ttk.Label(card, text='--', style='MetricCardValue.TLabel'))
            getattr(self, var_name).grid(row=1, column=0, sticky='ew')

        visual_card = ttk.LabelFrame(right_panel, text='ECG Overview', padding=10, style='Section.TLabelframe')
        visual_card.grid(row=1, column=0, sticky='nsew', padx=3)
        visual_card.grid_rowconfigure(0, weight=1)
        visual_card.grid_columnconfigure(0, weight=1)

        self.visual_canvas = tk.Canvas(visual_card, bg='#0f4c75', highlightthickness=0)
        self.visual_canvas.grid(row=0, column=0, sticky='nsew')
        self.visual_canvas.bind('<Configure>', lambda e: self.draw_clinic_visual(self.visual_canvas))

        results_frame = ttk.LabelFrame(scroll_parent, text='Results & Explainability', padding=10, style='Section.TLabelframe')
        results_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=(0, 8))
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_rowconfigure(2, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        results_notebook = ttk.Notebook(results_frame, style='Custom.TNotebook')
        results_notebook.grid(row=0, column=0, sticky='nsew')

        self.pred_frame = ttk.Frame(results_notebook)
        results_notebook.add(self.pred_frame, text='Prediction')
        self.text_pred = scrolledtext.ScrolledText(self.pred_frame, font=('Segoe UI', 10), wrap=tk.WORD, bd=0, relief=tk.FLAT)
        self.text_pred.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.risk_frame = ttk.Frame(results_notebook)
        results_notebook.add(self.risk_frame, text='Risk Assessment')
        self.text_risk = scrolledtext.ScrolledText(self.risk_frame, font=('Segoe UI', 10), wrap=tk.WORD, bd=0, relief=tk.FLAT)
        self.text_risk.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.explain_frame = ttk.Frame(results_notebook)
        results_notebook.add(self.explain_frame, text='Explainability')
        self.text_explain = scrolledtext.ScrolledText(self.explain_frame, font=('Segoe UI', 10), wrap=tk.WORD, bd=0, relief=tk.FLAT)
        self.text_explain.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def predict_and_analyze(self):
        """Make prediction and show analysis with improved validation, progress and verification."""
        if not self.model_loaded:
            messagebox.showerror('Model Error', 'The prediction model is not loaded. Please restart the application.')
            return

        # start progress
        try:
            self.pred_progress['value'] = 0
            self.pred_status.config(text='Validating inputs...')
            self.window.update_idletasks()

            # Get and validate inputs with detailed feedback
            name = self.input_vars['name'].get().strip()
            sex = self.input_vars['sex'].get().upper()
            raw = {}
            errors = []
            fields_to_parse = ['age', 'height', 'weight', 'qrs', 'qt', 't_wave']
            for f in fields_to_parse:
                raw[f] = self.input_vars[f].get().strip()
                if raw[f] == '':
                    errors.append(f'{f}: missing')
            if not name:
                errors.append('name: missing')
            if sex not in ['M', 'F']:
                errors.append('sex: must be M or F')

            # parse numeric fields
            values = {}
            for k, v in raw.items():
                try:
                    values[k] = float(v)
                except Exception:
                    errors.append(f'{k}: invalid number')

            # range checks (plausible clinical ranges)
            if 'age' in values and not (0 < values['age'] <= 120):
                errors.append('age: must be 1-120')
            if 'height' in values and not (30 <= values['height'] <= 250):
                errors.append('height: must be 30-250 cm')
            if 'weight' in values and not (1 <= values['weight'] <= 500):
                errors.append('weight: must be 1-500 kg')
            if 'qrs' in values and not (20 <= values['qrs'] <= 1000):
                errors.append('qrs: implausible (20-1000 ms expected)')
            if 'qt' in values and not (50 <= values['qt'] <= 2000):
                errors.append('qt: implausible (50-2000 ms expected)')
            if 't_wave' in values and not (-500 <= values['t_wave'] <= 2000):
                errors.append('t_wave: implausible (-500 to 2000 ms expected)')

            if errors:
                messagebox.showwarning('Input Validation', 'Please fix input issues:\n' + '\n'.join(errors))
                self.pred_status.config(text='Validation failed')
                return

            age = values['age']; height = values['height']; weight = values['weight']
            qrs = values['qrs']; qt = values['qt']; t_wave = values['t_wave']
            bmi_value = weight / ((height / 100) ** 2) if height > 0 else 0

            # build features
            self.pred_progress['value'] = 10
            self.pred_status.config(text='Preparing features...')
            self.window.update_idletasks()

            features = np.array([[age, 1 if sex == 'M' else 0, height, weight, qrs, qt, t_wave]])

            # primary prediction
            self.pred_progress['value'] = 30
            self.pred_status.config(text='Running model prediction...')
            self.window.update_idletasks()
            try:
                prediction = int(self.ensemble_model.predict(features)[0])
                probabilities = np.array(self.ensemble_model.predict_proba(features)[0], dtype=float)
            except Exception as e:
                raise RuntimeError(f'Model prediction failed: {e}')

            # verification: repeat prediction to guard against nondeterministic issues
            self.pred_progress['value'] = 45
            self.pred_status.config(text='Verifying prediction...')
            self.window.update_idletasks()
            try:
                re_prediction = int(self.ensemble_model.predict(features)[0])
                re_prob = np.array(self.ensemble_model.predict_proba(features)[0], dtype=float)
                verified = (prediction == re_prediction) and np.allclose(probabilities, re_prob, atol=1e-8)
            except Exception:
                verified = False

            confidence_data = self.calculate_confidence(probabilities)
            confidence = confidence_data['confidence_score']
            condition_name = self.condition_map.get(prediction, 'Unknown')

            # risk scores and abnormalities
            self.pred_progress['value'] = 55
            self.pred_status.config(text='Calculating clinical risk scores...')
            self.window.update_idletasks()
            risk_scores = self.calculate_risk_scores(age, sex, height, weight, qrs, qt, t_wave)
            abnormalities = self.identify_abnormal_parameters(age, sex, height, weight, qrs, qt, t_wave)

            # SHAP explanation (best-effort, may be slow)
            self.pred_progress['value'] = 70
            self.pred_status.config(text='Generating explanation...')
            self.window.update_idletasks()
            shap_data = self.calculate_shap_values(features, prediction, probabilities)

            # differential
            sorted_probs = sorted(
                [(self.condition_map.get(i, str(i)), float(p)) for i, p in enumerate(probabilities)],
                key=lambda x: x[1], reverse=True
            )
            differential = sorted_probs[:3]

            # recommendations and summary
            self.pred_progress['value'] = 85
            self.pred_status.config(text='Preparing results...')
            self.window.update_idletasks()
            recommendations = self.generate_recommendations(condition_name, risk_scores, abnormalities, confidence)
            explanation_text = shap_data.get('natural_language', '')
            clinical_summary = self.generate_clinical_summary(
                name, condition_name, confidence, risk_scores, abnormalities, explanation_text, recommendations
            )

            # UI updates
            self.condition_label.config(text=condition_name)
            self.confidence_label.config(text=f'Confidence: {confidence*100:.1f}% ({self.get_confidence_level(confidence)})')
            self.bmi_label.config(text=f'BMI: {bmi_value:.1f}')
            self.text_pred.delete(1.0, tk.END)
            self.text_pred.insert(tk.END, clinical_summary)
            self.display_risk_assessment(risk_scores)
            self.display_explainability(shap_data, differential)

            # Save to last_prediction_data and history
            timestamp = datetime.now().isoformat()
            self.last_prediction_data = {
                'patient_data': {'name': name, 'age': age, 'sex': sex, 'height': height, 'weight': weight, 'bmi': bmi_value},
                'prediction_data': {'predicted_condition': condition_name, 'condition_code': prediction, 'confidence_score': confidence, 'differential': differential, 'probabilities': confidence_data['distribution'], 'qrs_interval': qrs, 'qt_interval': qt, 't_interval': t_wave, 'verified': bool(verified)},
                'risk_scores': risk_scores,
                'explanation_data': shap_data,
                'abnormal_parameters': abnormalities,
                'recommendations': recommendations,
                'timestamp': timestamp
            }
            # append to in-memory history
            self.prediction_history.append(self.last_prediction_data)

            # persist to database
            prediction_id = self.db.add_prediction(
                name, prediction, confidence, qrs, qt, t_wave, age, sex, height, weight,
                all_predictions={'distribution': confidence_data['distribution'], 'differential': differential},
                risk_scores=risk_scores,
                explanation_features={'natural_language': shap_data.get('natural_language', ''), 'features': shap_data.get('features', [])},
                pdf_path='', report_id='', predicted_condition=condition_name
            )
            self.last_prediction_data['prediction_id'] = prediction_id

            # HIPAA logging
            try:
                logged = self.hipaa.log_access(user_id=self.current_user_id, patient_id=name, action='PREDICTION', access_type='READ', ip_address='')
                if not logged:
                    logger.warning('HIPAA log failed for %s', name)
            except Exception as e:
                logger.exception('HIPAA log error')

            # final progress
            self.pred_progress['value'] = 100
            self.pred_status.config(text=('Verified' if verified else 'Completed (verification failed)'))
            self.window.update_idletasks()

        except Exception as e:
            # show more informative error
            err_msg = str(e)
            logger.exception('Prediction exception')
            messagebox.showerror('Prediction Error', f'Prediction failed: {err_msg}')
            self.pred_status.config(text='Error')
            self.pred_progress['value'] = 0
    
    def display_risk_assessment(self, risk_scores):
        """Display risk assessment scores"""
        try:
            cha2ds2 = risk_scores.get('cha2ds2_vasc', {})
            timi = risk_scores.get('timi', {})
            framingham = risk_scores.get('framingham', {})
            arrhythmia = risk_scores.get('custom_arrhythmia', {})
            has_bled = risk_scores.get('has_bled', {})

            risk_text = f"""
╔════════════════════════════════════════════════════════════╗
║           RISK STRATIFICATION ASSESSMENT                   ║
╚════════════════════════════════════════════════════════════╝

CHA2DS2-VASc Score:
  Score: {cha2ds2.get('score', 'N/A')}
  Risk Level: {cha2ds2.get('risk_level', 'N/A')}
  Interpretation: {cha2ds2.get('interpretation', 'N/A')}

TIMI Risk Score:
  Score: {timi.get('score', 'N/A')}
  Risk Level: {timi.get('risk_level', 'N/A')}
  Interpretation: {timi.get('interpretation', 'N/A')}

Framingham Score:
  Score: {framingham.get('score', 'N/A')}
  Risk Level: {framingham.get('risk_level', 'N/A')}
  Interpretation: {framingham.get('interpretation', 'N/A')}

Custom Arrhythmia Risk:
  Score: {arrhythmia.get('score', 'N/A')}
  Risk Level: {arrhythmia.get('risk_level', 'N/A')}
  Interpretation: {arrhythmia.get('interpretation', 'N/A')}

HAS-BLED Score:
  Score: {has_bled.get('score', 'N/A')}
  Risk Level: {has_bled.get('risk_level', 'N/A')}
  Interpretation: {has_bled.get('interpretation', 'N/A')}

CLINICAL RECOMMENDATION:
═══════════════════════════════════════════════════════════
{self.get_clinical_recommendation(cha2ds2, timi, framingham, arrhythmia)}
"""
            self.text_risk.delete(1.0, tk.END)
            self.text_risk.insert(tk.END, risk_text)
            self.risk_summary_label.config(text=f"Risk Level: {arrhythmia.get('risk_level', 'N/A')}")
        except Exception as e:
            messagebox.showerror("Risk Assessment Error", f"Error calculating risk: {e}")

    def export_prediction_history(self):
        """Export in-memory prediction history to CSV or JSON."""
        if not self.prediction_history:
            messagebox.showinfo('Export History', 'No prediction history available to export.')
            return
        try:
            ftypes = [('CSV file', '*.csv'), ('JSON file', '*.json')]
            filename = filedialog.asksaveasfilename(title='Export Prediction History', defaultextension='.csv', filetypes=ftypes)
            if not filename:
                return
            if filename.lower().endswith('.json'):
                with open(filename, 'w', encoding='utf-8') as fh:
                    json.dump(self.prediction_history, fh, indent=2, default=str)
            else:
                # CSV: flatten a few fields
                import csv as _csv
                keys = ['timestamp', 'patient_name', 'age', 'sex', 'height', 'weight', 'predicted_condition', 'condition_code', 'confidence_score']
                with open(filename, 'w', newline='', encoding='utf-8') as fh:
                    writer = _csv.writer(fh)
                    writer.writerow(keys)
                    for rec in self.prediction_history:
                        pd = rec.get('patient_data', {})
                        pr = rec.get('prediction_data', {})
                        row = [rec.get('timestamp',''), pd.get('name',''), pd.get('age',''), pd.get('sex',''), pd.get('height',''), pd.get('weight',''), pr.get('predicted_condition',''), pr.get('condition_code',''), pr.get('confidence_score','')]
                        writer.writerow(row)
            messagebox.showinfo('Export History', f'Prediction history exported to {filename}')
        except Exception as e:
            logger.exception('Export history failed')
            messagebox.showerror('Export Error', f'Failed to export prediction history: {e}')
    
    def display_explainability(self, shap_data, differential):
        """Display SHAP-based explainability and differential diagnosis."""
        try:
            # Natural language explanation first
            natural = shap_data.get('natural_language') or shap_data.get('explanation_text') or 'A detailed explanation is unavailable.'
            explanation_lines = [
                '+' + '-' * 60 + '+',
                    '|              WHY THIS PREDICTION WAS MADE                 |',
                    '+' + '-' * 60 + '+',
                '',
                natural,
                ''
            ]

            # Positive / negative contributors
            pos = shap_data.get('positive_contributors') or []
            neg = shap_data.get('negative_contributors') or []
            if pos:
                explanation_lines.append('Top Positive Contributors:')
                for p in pos:
                    explanation_lines.append(f'- {p}')
                explanation_lines.append('')
            if neg:
                explanation_lines.append('Top Negative Contributors:')
                for n in neg:
                    explanation_lines.append(f'- {n}')
                explanation_lines.append('')

            # Differential diagnosis
            if differential:
                explanation_lines.append('Differential Diagnosis:')
                for diagnosis, probability in differential:
                    explanation_lines.append(f'- {diagnosis}: {probability*100:.1f}%')
                explanation_lines.append('')

            # Feature ranking: support both list-of-dicts and dict formats
            features = shap_data.get('features', [])
            if isinstance(features, dict):
                # dict of name->data
                feature_items = [(name, data) for name, data in features.items()]
            else:
                feature_items = []
                for item in features:
                    if isinstance(item, dict):
                        name = item.get('name') or item.get('feature')
                        feature_items.append((name, item))

            if feature_items:
                explanation_lines.append('Feature Contribution Ranking:')
                for i, (name, data) in enumerate(feature_items[:10], 1):
                    shap_v = data.get('shap_value') or data.get('permutation_importance') or data.get('magnitude', 0)
                    val = data.get('feature_value', '')
                    direction = 'increases' if shap_v > 0 else 'decreases'
                    explanation_lines.append(f"{i}. {name}: {shap_v:+.3f} ({direction}) - value: {val}")
                explanation_lines.append('')

            # Clinical explanations for top features (optional canned messages)
            for _, data in feature_items[:5]:
                name = data.get('name') if isinstance(data, dict) else None
                if name == 'QRS':
                    explanation_lines.append(f"- QRS duration ({data.get('feature_value', 'n/a')}) influences conduction and bundle branch patterns.")
                if name == 'QT':
                    explanation_lines.append(f"- QT interval ({data.get('feature_value', 'n/a')}) affects repolarization and torsades risk.")

            # Clinical recommendations (if available)
            recommendations = self.last_prediction_data.get('recommendations', []) if self.last_prediction_data else []
            if recommendations:
                explanation_lines.append('Clinical Recommendations:')
                for rec in recommendations:
                    explanation_lines.append(f'- {rec}')

            explanation_text = '\n'.join(explanation_lines)
            self.text_explain.delete(1.0, tk.END)
            self.text_explain.insert(tk.END, explanation_text)
        except Exception as e:
            messagebox.showerror('Explainability Error', f'Error generating explanation: {e}')
    
    def get_clinical_recommendation(self, cha2ds2, timi, framingham, arrhythmia):
        """Get clinical recommendations based on risk scores"""
        recommendations = []
        
        if cha2ds2['risk_level'] == 'High':
            recommendations.append("• Consider anticoagulation therapy for stroke prevention")
        
        if timi['risk_level'] == 'High':
            recommendations.append("• Monitor for acute coronary syndrome symptoms")
        
        if arrhythmia['risk_level'] == 'High':
            recommendations.append("• Recommend 24-hour Holter monitor recording")
            recommendations.append("• Consider cardiology consultation")
        
        if framingham['risk_level'] == 'High':
            recommendations.append("• Aggressive cardiovascular risk factor modification needed")
            recommendations.append("• Optimize blood pressure and lipid management")
        
        if not recommendations:
            recommendations.append("• Continue routine monitoring and follow-up")
            recommendations.append("• Maintain regular clinical assessment")
        
        return "\n".join(recommendations)
    
    # ==================== PATIENT TAB ====================
    
    def build_patient_tab(self):
        """Build patient management tab"""
        self.selected_patient_id = None
        self.patient_details_text = None
        self.current_patient_list = []
        self.current_page = 1
        self.page_size = 20
        self.sort_field = 'created_at'
        self.sort_ascending = False

        scroll_parent = self.create_scrollable_tab(self.patient_frame)
        main_frame = ttk.Frame(scroll_parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.BOTH, pady=6)
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=0)

        search_frame = ttk.LabelFrame(top_frame, text="Patient Search & Actions", padding=8, style='Section.TLabelframe')
        search_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 6), pady=(0, 2))
        search_frame.grid_columnconfigure(1, weight=1)
        search_frame.grid_columnconfigure(2, weight=0)
        search_frame.grid_columnconfigure(3, weight=0)
        search_frame.grid_columnconfigure(4, weight=0)

        ttk.Label(search_frame, text="Patient Name:", style='FieldLabel.TLabel').grid(row=0, column=0, padx=3, pady=3, sticky=tk.W)
        self.search_var = tk.StringVar()
        ttk.Entry(search_frame, textvariable=self.search_var).grid(row=0, column=1, padx=3, pady=3, sticky='ew')
        ttk.Button(search_frame, text="Search", command=self.search_patients, style='Action.TButton').grid(row=0, column=2, padx=3, pady=3)
        ttk.Button(search_frame, text="Clear", command=self.clear_search, style='Action.TButton').grid(row=0, column=3, padx=3, pady=3)
        ttk.Button(search_frame, text="Load All", command=self.load_all_patients, style='Action.TButton').grid(row=1, column=0, columnspan=2, sticky='ew', padx=3, pady=3)
        ttk.Button(search_frame, text="Export", command=self.export_patients, style='Action.TButton').grid(row=1, column=2, columnspan=2, sticky='ew', padx=3, pady=3)

        action_frame = ttk.Frame(top_frame)
        action_frame.grid(row=0, column=1, sticky='ne')
        ttk.Button(action_frame, text='New Patient', command=self.open_new_patient_dialog, style='Action.TButton').pack(fill=tk.X, padx=4, pady=3)
        ttk.Button(action_frame, text='Refresh List', command=self.load_all_patients, style='Action.TButton').pack(fill=tk.X, padx=4, pady=3)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
        content_frame.grid_columnconfigure(0, weight=7)
        content_frame.grid_columnconfigure(1, weight=4)
        content_frame.grid_rowconfigure(0, weight=1)

        list_frame = ttk.LabelFrame(content_frame, text="Patient List", padding=12, style='Section.TLabelframe')
        list_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 6), pady=5)
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        columns = ('ID', 'Name', 'Age', 'Sex', 'BMI', 'Predictions', 'Created')
        self.patient_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        self.patient_tree.column('ID', anchor=tk.CENTER, minwidth=40, width=50, stretch=False)
        self.patient_tree.column('Name', anchor=tk.W, minwidth=100, width=120, stretch=True)
        self.patient_tree.column('Age', anchor=tk.CENTER, minwidth=40, width=50, stretch=False)
        self.patient_tree.column('Sex', anchor=tk.CENTER, minwidth=40, width=50, stretch=False)
        self.patient_tree.column('BMI', anchor=tk.CENTER, minwidth=60, width=60, stretch=False)
        self.patient_tree.column('Predictions', anchor=tk.CENTER, minwidth=80, width=90, stretch=True)
        self.patient_tree.column('Created', anchor=tk.CENTER, minwidth=80, width=100, stretch=True)

        self.sort_field = 'created_at'
        self.sort_ascending = False

        self.patient_tree.heading('ID', text='ID', command=lambda: self.sort_patients('patient_id'))
        self.patient_tree.heading('Name', text='Name', command=lambda: self.sort_patients('name'))
        self.patient_tree.heading('Age', text='Age', command=lambda: self.sort_patients('age'))
        self.patient_tree.heading('Sex', text='Sex', command=lambda: self.sort_patients('sex'))
        self.patient_tree.heading('BMI', text='BMI', command=lambda: self.sort_patients('bmi'))
        self.patient_tree.heading('Predictions', text='Predictions', command=lambda: self.sort_patients('pred_count'))
        self.patient_tree.heading('Created', text='Created', command=lambda: self.sort_patients('created_at'))

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.patient_tree.yview)
        self.patient_tree.configure(yscroll=scrollbar.set)

        self.patient_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        pagination_frame = ttk.Frame(list_frame)
        pagination_frame.pack(fill=tk.X, pady=(10, 0))
        self.prev_page_button = ttk.Button(pagination_frame, text='Previous', command=self.previous_page, style='Action.TButton')
        self.prev_page_button.pack(side=tk.LEFT, padx=2)
        self.page_label = ttk.Label(pagination_frame, text='Page 1 of 1')
        self.page_label.pack(side=tk.LEFT, padx=6)
        self.next_page_button = ttk.Button(pagination_frame, text='Next', command=self.next_page, style='Action.TButton')
        self.next_page_button.pack(side=tk.LEFT, padx=2)

        self.patient_tree.bind('<<TreeviewSelect>>', self.display_selected_patient_details)

        details_frame = ttk.LabelFrame(content_frame, text="Patient Details", padding=12, style='Section.TLabelframe')
        details_frame.grid(row=0, column=1, sticky='nsew', padx=(6, 0), pady=5)
        details_frame.grid_rowconfigure(0, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)

        self.patient_details_text = scrolledtext.ScrolledText(details_frame, font=('Segoe UI', 10), wrap=tk.WORD)
        self.patient_details_text.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)
        self.patient_details_text.insert(tk.END, "Select a patient from the list to review their demographics and prediction history.")
        self.patient_details_text.config(state=tk.DISABLED)

        patient_button_frame = ttk.Frame(details_frame)
        patient_button_frame.grid(row=1, column=0, sticky='ew', pady=(8, 0))
        patient_button_frame.grid_columnconfigure(0, weight=1)
        patient_button_frame.grid_columnconfigure(1, weight=1)
        patient_button_frame.grid_columnconfigure(2, weight=1)
        patient_button_frame.grid_columnconfigure(3, weight=1)
        ttk.Button(patient_button_frame, text='View History', command=self.view_patient_history, style='Action.TButton').grid(row=0, column=0, sticky='ew', padx=2)
        ttk.Button(patient_button_frame, text='Edit Patient', command=self.open_edit_patient_dialog, style='Action.TButton').grid(row=0, column=1, sticky='ew', padx=2)
        ttk.Button(patient_button_frame, text='Delete Patient', command=self.delete_selected_patient, style='Action.TButton').grid(row=0, column=2, sticky='ew', padx=2)
        ttk.Button(patient_button_frame, text='Refresh Detail', command=self.refresh_patient_detail, style='Action.TButton').grid(row=0, column=3, sticky='ew', padx=2)

        self.load_all_patients()
    
    def search_patients(self):
        """Search patients by name"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("Input Error", "Please enter a patient name or partial name to search.")
            return

        try:
            self.current_patient_list = self.db.search_patients(query)
            self.current_page = 1
            self.update_pagination()
            if not self.current_patient_list:
                messagebox.showinfo("Search Completed", "No patients matched your search. Try a different name or load all patients.")
        except Exception as e:
            messagebox.showerror("Search Error", f"Error searching patients: {e}")
    
    def clear_search(self):
        """Clear the search input and reload all patients."""
        self.search_var.set('')
        self.load_all_patients()

    def load_all_patients(self):
        """Load all patients"""
        try:
            self.current_patient_list = self.db.get_all_patients(limit=1000)
            self.current_page = 1
            self.update_pagination()
        except Exception as e:
            messagebox.showerror("Load Error", f"Error loading patients: {e}")
    
    def display_patients(self, patients):
        """Display patients in treeview"""
        # Clear existing items
        for item in self.patient_tree.get_children():
            self.patient_tree.delete(item)
        
        # Add patients
        for patient in patients:
            patient_id = patient['patient_id']
            name = patient['name']
            age = patient['age']
            sex = patient['sex']
            height = patient['height']
            weight = patient['weight']
            bmi = weight / (height/100)**2 if height > 0 else 0
            
            # Get prediction count
            pred_count = self.db.get_prediction_count(patient_id) if hasattr(self.db, 'get_prediction_count') else 0
            
            created_at = patient.get('created_at', '')
            self.patient_tree.insert('', 'end', text='', values=(
                patient_id,
                name,
                age,
                sex,
                f"{bmi:.1f}",
                pred_count,
                created_at
            ))

    def sort_patients(self, field):
        """Sort the current patient list and refresh pagination."""
        if self.sort_field == field:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_field = field
            self.sort_ascending = True

        if not self.current_patient_list:
            return

        reverse = not self.sort_ascending
        key_map = {
            'patient_id': lambda p: p.get('patient_id', 0),
            'name': lambda p: p.get('name', '').lower(),
            'age': lambda p: p.get('age', 0),
            'sex': lambda p: p.get('sex', ''),
            'bmi': lambda p: p.get('bmi', 0),
            'pred_count': lambda p: self.db.get_prediction_count(p.get('patient_id'))
        }
        key_func = key_map.get(field, lambda p: p.get(field, ''))
        self.current_patient_list.sort(key=key_func, reverse=reverse)
        self.current_page = 1
        self.update_pagination()

    def update_pagination(self):
        """Update pagination controls and refresh the visible patient page."""
        total_items = len(self.current_patient_list)
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        self.current_page = min(max(1, self.current_page), total_pages)

        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        self.display_patients(self.current_patient_list[start:end])

        self.page_label.config(text=f'Page {self.current_page} of {total_pages}')
        self.prev_page_button['state'] = tk.NORMAL if self.current_page > 1 else tk.DISABLED
        self.next_page_button['state'] = tk.NORMAL if self.current_page < total_pages else tk.DISABLED

    def previous_page(self):
        """Go to the previous patient page."""
        if self.current_page > 1:
            self.current_page -= 1
            self.update_pagination()

    def next_page(self):
        """Go to the next patient page."""
        total_items = len(self.current_patient_list)
        total_pages = max(1, (total_items + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages:
            self.current_page += 1
            self.update_pagination()

    def delete_selected_patient(self):
        """Delete the selected patient after confirmation."""
        selection = self.patient_tree.selection()
        if selection:
            item = self.patient_tree.item(selection[0])
            patient_id = item['values'][0]
        elif self.selected_patient_id:
            patient_id = self.selected_patient_id
        else:
            messagebox.showwarning("Selection Required", "Please select a patient to delete.")
            return

        patient = self.db.get_patient(patient_id)
        if not patient:
            messagebox.showerror("Error", "Selected patient could not be found.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete patient '{patient['name']}' and all associated predictions? This action cannot be undone."
        )
        if not confirm:
            return

        try:
            deleted = self.db.delete_patient(patient_id)
            if deleted:
                self.selected_patient_id = None
                self.load_all_patients()
                self.patient_details_text.config(state=tk.NORMAL)
                self.patient_details_text.delete(1.0, tk.END)
                self.patient_details_text.insert(tk.END, "Patient record deleted successfully.\n")
                self.patient_details_text.config(state=tk.DISABLED)
                messagebox.showinfo("Deleted", f"Patient '{patient['name']}' was deleted successfully.")
            else:
                messagebox.showwarning("Delete Failed", "The patient could not be deleted.")
        except Exception as e:
            messagebox.showerror("Delete Error", f"Failed to delete patient: {e}")

    def display_selected_patient_details(self, event=None):
        """Display a patient's demographics and recent predictions."""
        selection = self.patient_tree.selection()
        if not selection:
            return
        item = self.patient_tree.item(selection[0])
        patient_id = item['values'][0]
        self.selected_patient_id = patient_id
        self.refresh_patient_detail()

    def refresh_patient_detail(self):
        """Refresh the details panel for the selected patient."""
        if not self.selected_patient_id:
            return

        patient = self.db.get_patient(self.selected_patient_id)
        if not patient:
            return

        predictions = self.db.get_patient_predictions(self.selected_patient_id, limit=10)
        self.patient_details_text.config(state=tk.NORMAL)
        self.patient_details_text.delete(1.0, tk.END)

        self.patient_details_text.insert(tk.END, f"Patient ID: {patient['patient_id']}\n")
        self.patient_details_text.insert(tk.END, f"Name: {patient['name']}\n")
        self.patient_details_text.insert(tk.END, f"Age: {patient['age']} | Sex: {patient['sex']}\n")
        self.patient_details_text.insert(tk.END, f"Height: {patient['height']} cm | Weight: {patient['weight']} kg | BMI: {patient['bmi']:.1f}\n")
        self.patient_details_text.insert(tk.END, f"Created At: {patient['created_at']}\n")
        self.patient_details_text.insert(tk.END, "\nRecent Prediction History:\n")

        if not predictions:
            self.patient_details_text.insert(tk.END, "No predictions found for this patient.\n")
        else:
            for pred in predictions[:5]:
                self.patient_details_text.insert(tk.END, f"\n• {pred['created_at']}: {pred['predicted_condition']} (Confidence: {pred['confidence_score']:.1f}%)\n")
                self.patient_details_text.insert(tk.END, f"  QRS: {pred['qrs_interval']}, QT: {pred['qt_interval']}, T: {pred['t_interval']}\n")

        self.patient_details_text.config(state=tk.DISABLED)

    def view_patient_history(self, event=None):
        """View patient history in the details panel."""
        selection = self.patient_tree.selection()
        if not selection and not self.selected_patient_id:
            messagebox.showwarning("Selection Required", "Please select a patient from the list first.")
            return

        if selection:
            item = self.patient_tree.item(selection[0])
            self.selected_patient_id = item['values'][0]

        self.refresh_patient_detail()

    def open_new_patient_dialog(self):
        """Open a dialog to add a new patient."""
        dialog = tk.Toplevel(self.window)
        dialog.title('New Patient Registration')
        dialog.geometry('480x360')
        dialog.minsize(420, 320)
        dialog.resizable(True, True)

        form_frame = ttk.Frame(dialog, padding=12)
        form_frame.pack(fill=tk.BOTH, expand=True)
        form_frame.grid_columnconfigure(1, weight=1)

        entries = {}
        fields = [
            ('Name', 'name'),
            ('Age', 'age'),
            ('Sex', 'sex'),
            ('Height (cm)', 'height'),
            ('Weight (kg)', 'weight'),
        ]

        for row, (label, key) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=8)
            if key == 'sex':
                combo = ttk.Combobox(form_frame, values=['M', 'F'], state='readonly')
                combo.grid(row=row, column=1, pady=8, sticky='ew')
                combo.set('M')
                entries[key] = combo
            else:
                entry = ttk.Entry(form_frame)
                entry.grid(row=row, column=1, pady=8, sticky='ew')
                entries[key] = entry

        def submit_new_patient():
            try:
                name = entries['name'].get().strip()
                age = int(entries['age'].get())
                sex = entries['sex'].get().upper()
                height = float(entries['height'].get())
                weight = float(entries['weight'].get())

                if not name:
                    raise ValueError('Patient name is required')
                if age <= 0:
                    raise ValueError('Age must be a positive number')
                if height <= 0 or weight <= 0:
                    raise ValueError('Height and weight must be positive values')
                if sex not in ('M', 'F'):
                    raise ValueError('Sex must be M or F')

                existing = self.db.get_patient_by_name(name)
                if existing:
                    raise ValueError('A patient with this name already exists. Please verify the patient or use a distinct name.')

                patient_id = self.db.add_patient(name, age, sex, height, weight)
                self.load_all_patients()
                self.patient_details_text.config(state=tk.NORMAL)
                self.patient_details_text.delete(1.0, tk.END)
                self.patient_details_text.insert(tk.END, f"New patient created: {name} (ID: {patient_id})\n")
                self.patient_details_text.config(state=tk.DISABLED)
                dialog.destroy()
                messagebox.showinfo('Success', f'Patient {name} added successfully.')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to add patient: {e}')

        ttk.Button(form_frame, text='Create Patient', command=submit_new_patient, style='Action.TButton').grid(row=len(fields), column=0, columnspan=2, pady=18, ipadx=8)
    
    def open_edit_patient_dialog(self):
        """Open a dialog to edit selected patient details."""
        if not self.selected_patient_id:
            messagebox.showwarning('Selection Required', 'Please select a patient before editing.')
            return

        patient = self.db.get_patient(self.selected_patient_id)
        if not patient:
            messagebox.showerror('Error', 'Selected patient could not be found.')
            return

        dialog = tk.Toplevel(self.window)
        dialog.title('Edit Patient Record')
        dialog.geometry('480x360')
        dialog.minsize(420, 320)
        dialog.resizable(True, True)

        form_frame = ttk.Frame(dialog, padding=12)
        form_frame.pack(fill=tk.BOTH, expand=True)
        form_frame.grid_columnconfigure(1, weight=1)

        entries = {}
        fields = [
            ('Name', 'name', patient['name']),
            ('Age', 'age', str(patient['age'])),
            ('Sex', 'sex', patient['sex']),
            ('Height (cm)', 'height', str(patient['height'])),
            ('Weight (kg)', 'weight', str(patient['weight'])),
        ]

        for row, (label, key, value) in enumerate(fields):
            ttk.Label(form_frame, text=label).grid(row=row, column=0, sticky=tk.W, pady=8)
            if key == 'sex':
                combo = ttk.Combobox(form_frame, values=['M', 'F'], state='readonly')
                combo.grid(row=row, column=1, pady=8, sticky='ew')
                combo.set(value)
                entries[key] = combo
            else:
                entry = ttk.Entry(form_frame)
                entry.insert(0, value)
                entry.grid(row=row, column=1, pady=8, sticky='ew')
                entries[key] = entry

        def submit_update_patient():
            try:
                name = entries['name'].get().strip()
                age = int(entries['age'].get())
                sex = entries['sex'].get().upper()
                height = float(entries['height'].get())
                weight = float(entries['weight'].get())

                if not name:
                    raise ValueError('Patient name is required')
                if age <= 0:
                    raise ValueError('Age must be a positive number')
                if height <= 0 or weight <= 0:
                    raise ValueError('Height and weight must be positive values')
                if sex not in ('M', 'F'):
                    raise ValueError('Sex must be M or F')

                existing = self.db.get_patient_by_name(name)
                if existing and existing['patient_id'] != self.selected_patient_id:
                    raise ValueError('A different patient with that name already exists.')

                updated = self.db.update_patient(self.selected_patient_id, name, age, sex, height, weight)
                if not updated:
                    raise RuntimeError('No changes were saved.')

                self.load_all_patients()
                self.refresh_patient_detail()
                dialog.destroy()
                messagebox.showinfo('Success', f'Patient {name} updated successfully.')
            except Exception as e:
                messagebox.showerror('Error', f'Failed to update patient: {e}')

        ttk.Button(form_frame, text='Save Changes', command=submit_update_patient, style='Action.TButton').grid(row=len(fields), column=0, columnspan=2, pady=18, ipadx=8)

    def export_patients(self):
        """Export patients to JSON"""
        try:
            filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
            if filename:
                patients = self.db.get_all_patients(limit=1000)
                with open(filename, 'w') as f:
                    json.dump(patients, f, indent=2, default=str)
                messagebox.showinfo("Success", f"Database exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Export failed: {e}")
    
    # ==================== ANALYTICS TAB ====================
    
    def build_analytics_tab(self):
        """Build analytics tab"""
        scroll_parent = self.create_scrollable_tab(self.analytics_frame)
        main_frame = ttk.Frame(scroll_parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        button_frame = ttk.LabelFrame(main_frame, text='Analytics Dashboard', padding=8, style='Section.TLabelframe')
        button_frame.grid(row=0, column=0, sticky='ew', padx=3, pady=3)

        buttons = [
            ('System Overview', self.show_system_overview),
            ('Patient Statistics', self.show_patient_stats),
            ('Prediction Analytics', self.show_prediction_stats),
            ('Temporal Analysis', self.show_temporal_analysis),
            ('Risk Analysis', self.show_risk_analysis),
            ('Model Performance', self.show_model_performance),
        ]

        for idx, (text, command) in enumerate(buttons):
            button_frame.grid_columnconfigure(idx % 3, weight=1)
            ttk.Button(button_frame, text=text, command=command, style='Action.TButton').grid(row=idx // 3, column=idx % 3, sticky='ew', padx=5, pady=5)

        results_frame = ttk.LabelFrame(main_frame, text='Analytics Results', padding=10, style='Section.TLabelframe')
        results_frame.grid(row=1, column=0, sticky='nsew', padx=4, pady=4)
        results_frame.grid_rowconfigure(0, weight=3)
        results_frame.grid_rowconfigure(1, weight=1)
        results_frame.grid_rowconfigure(2, weight=0)
        results_frame.grid_columnconfigure(0, weight=1)

        chart_container = tk.Frame(results_frame, bg='#f7fbff')
        chart_container.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        chart_container.grid_rowconfigure(0, weight=1)
        chart_container.grid_columnconfigure(0, weight=1)

        # Analytics chart canvas
        self.analytics_fig = Figure(figsize=(7, 4), dpi=100)
        self.analytics_ax = self.analytics_fig.add_subplot(111)
        self.analytics_fig.patch.set_facecolor('#f4f7fb')
        self.analytics_ax.set_facecolor('#edf4fc')

        self.analytics_canvas = FigureCanvasTkAgg(self.analytics_fig, master=chart_container)
        self.analytics_canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        self.analytics_text = scrolledtext.ScrolledText(results_frame, font=('Segoe UI', 10), wrap=tk.WORD)
        self.analytics_text.grid(row=1, column=0, sticky='nsew', padx=5, pady=(4, 0))

        self.chart_tooltip = self.analytics_ax.annotate(
            '', xy=(0, 0), xytext=(16, 16), textcoords='offset points',
            bbox=dict(boxstyle='round,pad=0.3', fc='#ffffff', ec='#0f4c75', alpha=0.92),
            arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
            fontsize=9,
            visible=False
        )
        self.chart_bars = []
        self.chart_labels = []
        self.analytics_canvas.mpl_connect('motion_notify_event', self.on_chart_hover)

        export_frame = ttk.Frame(results_frame)
        export_frame.grid(row=2, column=0, sticky='ew', padx=5, pady=(10, 2))
        export_frame.grid_columnconfigure(0, weight=1)
        export_frame.grid_columnconfigure(1, weight=1)
        ttk.Button(export_frame, text='Export Chart as PNG', command=self.export_chart_png, style='Action.TButton').grid(row=0, column=0, sticky='ew', padx=(0, 4))
        ttk.Button(export_frame, text='Export Analytics PDF', command=self.export_analytics_pdf, style='Action.TButton').grid(row=0, column=1, sticky='ew', padx=(4, 0))

    def plot_analytics_chart(self, title, values, xlabel='Category', ylabel='Count'):
        """Draw a bar chart for analytics data."""
        self.analytics_ax.clear()
        self.chart_bars = []

        if not values:
            self._render_empty_chart(title)
            return

        categories = list(values.keys())
        counts = list(values.values())
        palette = ['#1f78b4', '#33a02c', '#ff7f0e', '#e31a1c', '#6a3d9a', '#ffcc00', '#00bcd4']
        bar_colors = [palette[i % len(palette)] for i in range(len(categories))]

        bars = self.analytics_ax.bar(categories, counts, color=bar_colors, edgecolor='#3b6b92', linewidth=0.8, label=ylabel)
        self.chart_bars = bars
        self.chart_labels = categories

        self.analytics_ax.set_title(title, fontsize=14, color='#172a45', pad=14)
        self.analytics_ax.set_xlabel(xlabel, color='#3b6b92', fontsize=11, labelpad=10)
        self.analytics_ax.set_ylabel(ylabel, color='#3b6b92', fontsize=11, labelpad=10)
        self.analytics_ax.tick_params(axis='x', rotation=40, labelsize=9, colors='#26465d')
        self.analytics_ax.tick_params(axis='y', labelsize=10, colors='#26465d')
        self.analytics_ax.grid(axis='y', color='#d8e6f4', linestyle='--', linewidth=0.7)
        self.analytics_ax.set_axisbelow(True)

        for bar in bars:
            height = bar.get_height()
            self.analytics_ax.annotate(
                f'{height:,}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords='offset points',
                ha='center',
                va='bottom',
                fontsize=8,
                color='#172a45'
            )

        if bars:
            self.analytics_ax.legend(loc='upper right', framealpha=0.95, fontsize=9)

        self.analytics_fig.tight_layout(rect=[0.05, 0.08, 0.98, 0.95])
        self.analytics_canvas.draw()

    def _render_empty_chart(self, title):
        """Render a placeholder when there is no data to display."""
        self.analytics_ax.clear()
        self.analytics_ax.text(
            0.5,
            0.5,
            'No data available for this chart.',
            ha='center',
            va='center',
            fontsize=14,
            color='#5a6f86'
        )
        self.analytics_ax.set_title(title, fontsize=14, color='#172a45', pad=14)
        self.analytics_ax.set_xticks([])
        self.analytics_ax.set_yticks([])
        self.analytics_ax.set_frame_on(False)
        self.analytics_fig.tight_layout(rect=[0.05, 0.08, 0.98, 0.95])
        self.analytics_canvas.draw()

    def on_chart_hover(self, event):
        """Display a tooltip when hovering over bars."""
        visible = False
        if event.inaxes == self.analytics_ax and self.chart_bars is not None:
            for idx, bar in enumerate(self.chart_bars):
                if bar.contains(event)[0]:
                    height = bar.get_height()
                    label = self.chart_labels[idx] if idx < len(self.chart_labels) else ''
                    self.chart_tooltip.set_text(f"{label}: {height:,}")
                    self.chart_tooltip.xy = (bar.get_x() + bar.get_width() / 2, height)
                    self.chart_tooltip.set_visible(True)
                    visible = True
                    break
        if not visible:
            self.chart_tooltip.set_visible(False)
        self.analytics_canvas.draw_idle()

    def export_chart_png(self):
        """Export the current analytics chart to a PNG file."""
        try:
            filename = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG Image', '*.png')])
            if not filename:
                return
            self.analytics_fig.savefig(filename, dpi=150, bbox_inches='tight', facecolor=self.analytics_fig.get_facecolor())
            messagebox.showinfo('Export Complete', f'Chart exported to {filename}')
        except Exception as e:
            messagebox.showerror('Export Error', f'Unable to export chart: {e}')

    def export_analytics_pdf(self):
        """Export analytics summary and chart snapshot to a PDF."""
        try:
            filename = filedialog.asksaveasfilename(defaultextension='.pdf', filetypes=[('PDF Document', '*.pdf')])
            if not filename:
                return

            buffer = io.BytesIO()
            self.analytics_fig.savefig(buffer, dpi=150, bbox_inches='tight', facecolor=self.analytics_fig.get_facecolor())
            buffer.seek(0)

            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.units import inch

            c = canvas.Canvas(filename, pagesize=letter)
            width, height = letter
            c.setFont('Helvetica-Bold', 16)
            c.drawString(72, height - 72, 'Analytics Report')
            c.setFont('Helvetica', 10)
            c.drawString(72, height - 92, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            c.drawString(72, height - 110, 'Generated by Cardiac Arrhythmia Analytics')

            image = ImageReader(buffer)
            c.drawImage(image, 72, height - 420, width=width - 144, height=300, preserveAspectRatio=True, mask='auto')

            text_content = self.analytics_text.get(1.0, tk.END).strip().splitlines()
            y = height - 450
            c.setFont('Helvetica', 9)
            for line in text_content[:18]:
                c.drawString(72, y, line)
                y -= 14
            c.save()

            messagebox.showinfo('Export Complete', f'Analytics PDF exported to {filename}')
        except Exception as e:
            messagebox.showerror('Export Error', f'Unable to export analytics PDF: {e}')
    
    def show_system_overview(self):
        """Show system overview"""
        try:
            report = self.analytics.get_system_overview()
            self.analytics_text.delete(1.0, tk.END)
            self.analytics_text.insert(tk.END, report)
            patient_stats = self.analytics.get_patient_statistics()
            prediction_stats = self.analytics.get_prediction_statistics()
            if 'error' in patient_stats or 'error' in prediction_stats:
                self._render_empty_chart('System Overview')
                return
            overview_values = {
                'Patients': patient_stats.get('total_patients', 0),
                'Predictions': prediction_stats.get('total_predictions', 0),
                'Recent (7 days)': prediction_stats.get('recent_predictions_7days', 0),
                'Avg confidence %': prediction_stats.get('average_confidence_percent', 0)
            }
            self.plot_analytics_chart('System Overview', overview_values, xlabel='Metric', ylabel='Value')
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report: {e}")
    
    def show_patient_stats(self):
        """Show patient statistics"""
        try:
            data = self.analytics.get_patient_statistics()
            self.analytics_text.delete(1.0, tk.END)
            if isinstance(data, dict) and 'error' not in data:
                text = (
                    f"Total Patients: {data.get('total_patients', 0)}\n"
                    f"Average Age: {data.get('age_statistics', {}).get('mean', 0):.1f}\n"
                    f"Age Range: {data.get('age_statistics', {}).get('min', 0)} - {data.get('age_statistics', {}).get('max', 0)}\n"
                    f"Male / Female: {data.get('sex_distribution', {}).get('male', 0)} / {data.get('sex_distribution', {}).get('female', 0)}\n"
                )
                self.analytics_text.insert(tk.END, text)
                self.plot_analytics_chart('Patient Age Group Distribution', data.get('age_groups', {}), xlabel='Age Group', ylabel='Patients')
            else:
                self.analytics_text.insert(tk.END, data if isinstance(data, str) else data.get('error', 'No data available'))
            self.analytics_canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report: {e}")
    
    def show_prediction_stats(self):
        """Show prediction statistics"""
        try:
            data = self.analytics.get_prediction_statistics()
            self.analytics_text.delete(1.0, tk.END)
            if isinstance(data, dict) and 'error' not in data:
                condition_dist = {str(k): v for k, v in data.get('condition_distribution', {}).items()}
                text = (
                    f"Total Predictions: {data.get('total_predictions', 0)}\n"
                    f"Average Confidence: {data.get('average_confidence_percent', 0):.1f}%\n"
                    f"Recent Predictions (7 days): {data.get('recent_predictions_7days', 0)}\n"
                )
                self.analytics_text.insert(tk.END, text)
                self.plot_analytics_chart('Predictions by Condition', condition_dist, xlabel='Condition', ylabel='Count')
            else:
                self.analytics_text.insert(tk.END, data if isinstance(data, str) else data.get('error', 'No prediction data available'))
            self.analytics_canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report: {e}")
    
    def show_temporal_analysis(self):
        """Show temporal analysis"""
        try:
            data = self.analytics.get_temporal_analysis()
            self.analytics_text.delete(1.0, tk.END)
            if isinstance(data, dict) and 'error' not in data:
                text = (
                    f"Daily Predictions: {sum(data.get('daily_distribution', {}).values()):d}\n"
                    f"Hourly Buckets: {len(data.get('hourly_distribution', {}))}\n"
                    f"Recent Months: {len(data.get('monthly_distribution', {}))}\n"
                )
                self.analytics_text.insert(tk.END, text)
                self.plot_analytics_chart('Predictions by Day of Week', data.get('daily_distribution', {}), xlabel='Day', ylabel='Count')
            else:
                self.analytics_text.insert(tk.END, data if isinstance(data, str) else data.get('error', 'No temporal data available'))
            self.analytics_canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report: {e}")
    
    def show_risk_analysis(self):
        """Show risk analysis"""
        try:
            data = self.analytics.get_condition_risk_analysis()
            self.analytics_text.delete(1.0, tk.END)
            if isinstance(data, dict) and 'error' not in data:
                highest = data.get('highest_risk_condition')
                text = (
                    f"Conditions Analyzed: {data.get('conditions_analyzed', 0)}\n"
                    f"Highest Average Risk Condition: {highest if highest else 'N/A'}\n"
                )
                self.analytics_text.insert(tk.END, text)
                self.plot_analytics_chart('Average Risk by Condition', data.get('average_risks_by_condition', {}), xlabel='Condition', ylabel='Risk Score')
            else:
                self.analytics_text.insert(tk.END, data if isinstance(data, str) else data.get('error', 'No risk data available'))
            self.analytics_canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report: {e}")
    
    def show_model_performance(self):
        """Show model performance"""
        try:
            data = self.analytics.get_model_performance_metrics()
            self.analytics_text.delete(1.0, tk.END)
            if isinstance(data, dict) and 'error' not in data:
                text = (
                    f"Total Predictions: {data.get('total_predictions', 0)}\n"
                    f"Average Confidence: {data.get('average_confidence', 0):.1f}%\n"
                    f"High Confidence: {data.get('high_confidence_count', 0)} ({data.get('high_confidence_percent', 0):.1f}%)\n"
                    f"Medium Confidence: {data.get('medium_confidence_count', 0)} ({data.get('medium_confidence_percent', 0):.1f}%)\n"
                    f"Low Confidence: {data.get('low_confidence_count', 0)} ({data.get('low_confidence_percent', 0):.1f}%)\n"
                )
                self.analytics_text.insert(tk.END, text)
                perf_dist = {
                    'High': data.get('high_confidence_count', 0),
                    'Medium': data.get('medium_confidence_count', 0),
                    'Low': data.get('low_confidence_count', 0)
                }
                self.plot_analytics_chart('Prediction Confidence Tiers', perf_dist, xlabel='Tier', ylabel='Count')
                self.analytics_ax.set_xticks(
                    range(len(perf_dist)),
                    [f'{tier}\n({count})' for tier, count in perf_dist.items()]
                )
            else:
                self.analytics_text.insert(tk.END, data if isinstance(data, str) else data.get('error', 'No performance data available'))
            self.analytics_canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report: {e}")
    
    # ==================== SETTINGS TAB ====================
    
    def build_settings_tab(self):
        """Build settings tab"""
        scroll_parent = self.create_scrollable_tab(self.settings_frame)
        main_frame = ttk.Frame(scroll_parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Compliance section
        compliance_frame = ttk.LabelFrame(main_frame, text="Compliance & Audit", padding=12, style='Section.TLabelframe')
        compliance_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(compliance_frame, text="HIPAA Status", command=self.show_hipaa_status).grid(row=0, column=0, sticky='ew', padx=4, pady=4)
        ttk.Button(compliance_frame, text="FDA 510(k) Checklist", command=self.show_fda_status).grid(row=0, column=1, sticky='ew', padx=4, pady=4)
        ttk.Button(compliance_frame, text="Audit Log", command=self.show_audit_log).grid(row=0, column=2, sticky='ew', padx=4, pady=4)
        compliance_frame.grid_columnconfigure(0, weight=1)
        compliance_frame.grid_columnconfigure(1, weight=1)
        compliance_frame.grid_columnconfigure(2, weight=1)
        
        # System section
        system_frame = ttk.LabelFrame(main_frame, text="System Information", padding=12, style='Section.TLabelframe')
        system_frame.grid(row=1, column=0, sticky='ew', padx=5, pady=5)
        
        ttk.Button(system_frame, text="Database Info", command=self.show_database_info).grid(row=0, column=0, sticky='ew', padx=4, pady=4)
        ttk.Button(system_frame, text="Model Info", command=self.show_model_info).grid(row=0, column=1, sticky='ew', padx=4, pady=4)
        ttk.Button(system_frame, text="API Info", command=self.show_api_info).grid(row=0, column=2, sticky='ew', padx=4, pady=4)
        system_frame.grid_columnconfigure(0, weight=1)
        system_frame.grid_columnconfigure(1, weight=1)
        system_frame.grid_columnconfigure(2, weight=1)
        
        # Settings results
        results_frame = ttk.LabelFrame(main_frame, text="Settings Details", padding=10, style='Section.TLabelframe')
        results_frame.grid(row=2, column=0, sticky='nsew', padx=5, pady=5)
        results_frame.grid_rowconfigure(0, weight=1)
        results_frame.grid_columnconfigure(0, weight=1)

        self.settings_notebook = ttk.Notebook(results_frame, style='Custom.TNotebook')
        self.settings_notebook.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)

        summary_frame = ttk.Frame(self.settings_notebook)
        audit_frame = ttk.Frame(self.settings_notebook)

        self.settings_notebook.add(summary_frame, text='Summary')
        self.settings_notebook.add(audit_frame, text='Audit Log')

        summary_frame.grid_rowconfigure(0, weight=1)
        summary_frame.grid_columnconfigure(0, weight=1)
        self.settings_text = scrolledtext.ScrolledText(summary_frame, font=("Courier", 9), wrap=tk.WORD)
        self.settings_text.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)

        audit_frame.grid_rowconfigure(0, weight=1)
        audit_frame.grid_columnconfigure(0, weight=1)
        tree_frame = ttk.Frame(audit_frame)
        tree_frame.grid(row=0, column=0, sticky='nsew', padx=6, pady=6)

        columns = ('timestamp', 'user', 'patient', 'action', 'access_type', 'ip', 'status')
        self.audit_tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
        for col in columns:
            self.audit_tree.heading(col, text=col.replace('_', ' ').title())
            width = 130 if col == 'patient' else 100
            self.audit_tree.column(col, width=width, anchor=tk.W)

        audit_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.audit_tree.yview)
        self.audit_tree.configure(yscroll=audit_scroll.set)
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        self.audit_tree.grid(row=0, column=0, sticky='nsew')
        audit_scroll.grid(row=0, column=1, sticky='ns')
        self.settings_built = True
    
    def show_hipaa_status(self):
        """Show HIPAA compliance status"""
        if not self.ensure_settings_ui():
            return
        try:
            status = self.hipaa.get_compliance_status()
            output = []
            output.append('HIPAA Compliance Status')
            output.append('========================')
            output.append(status if isinstance(status, str) else json.dumps(status, indent=2))
            audit_entries = self.hipaa.get_audit_log(limit=10)
            if audit_entries:
                output.append('\nRecent HIPAA Access Audit Events:')
                for entry in audit_entries:
                    output.append(
                        f"- {entry.get('timestamp','')} | User: {entry.get('user_id','')} | Patient: {entry.get('patient_id','')} | Action: {entry.get('action','')} | Status: {entry.get('status','')}"
                    )
            else:
                output.append('\nRecent HIPAA Access Audit Events: Information not available')
            self.display_settings_message('\n'.join(output))
        except Exception as e:
            logger.exception('Error retrieving HIPAA status: %s', e)
            self.display_settings_message('Error retrieving HIPAA status. Information not available at this time.')
    
    def show_fda_status(self):
        """Show FDA 510(k) compliance status"""
        if not self.ensure_settings_ui():
            return
        try:
            status = self.fda.get_compliance_status()
            checklist = self.fda.get_510k_checklist() if hasattr(self.fda, 'get_510k_checklist') else {}
            output = []
            output.append('FDA 510(k) Compliance Checklist')
            output.append('================================')
            if isinstance(status, dict) and status:
                output.append(f"Device Class: {status.get('device_class', 'Information not available')}")
                output.append(f"Regulatory Pathway: {status.get('regulatory_pathway', 'Information not available')}")
                output.append(f"Completion: {status.get('completion_percent', 0)}%")
                output.append(f"Completed Items: {status.get('completed_items', 0)}")
                output.append(f"Pending Items: {status.get('pending_items', 0)}")
                output.append(f"In Progress: {status.get('in_progress_items', 0)}")
                test_results = status.get('test_results', {})
                output.append(f"Test Results: {json.dumps(test_results)}")
            else:
                output.append('FDA compliance status information not available.')
            if checklist:
                output.append('\n510(k) Checklist Items:')
                for section, items in checklist.items():
                    output.append(f"- {section.replace('_',' ').title()}: {', '.join(items)}")
            else:
                output.append('\n510(k) checklist details: Information not available')
            self.display_settings_message('\n'.join(output))
        except Exception as e:
            logger.exception('Error retrieving FDA status: %s', e)
            self.display_settings_message('Error retrieving FDA status. Information not available at this time.')
    
    def show_audit_log(self):
        """Show audit log"""
        if not self.ensure_settings_ui():
            return
        try:
            if hasattr(self, 'settings_notebook'):
                try:
                    self.settings_notebook.select(self.settings_notebook.tabs()[1])
                except Exception:
                    pass
            self.clear_audit_tree()
            hipaa_logs = self.hipaa.get_audit_log(limit=25) if hasattr(self.hipaa, 'get_audit_log') else []
            auth_logs = self.auth.get_audit_log(limit=25) if hasattr(self.auth, 'get_audit_log') else []
            combined = []
            for entry in hipaa_logs:
                combined.append({
                    'timestamp': entry.get('timestamp', ''),
                    'user': entry.get('user_id', ''),
                    'patient': entry.get('patient_id', ''),
                    'action': entry.get('action', ''),
                    'access_type': entry.get('access_type', ''),
                    'ip': entry.get('ip_address', ''),
                    'status': entry.get('status', 'HIPAA')
                })
            for entry in auth_logs:
                combined.append({
                    'timestamp': entry.get('timestamp', ''),
                    'user': entry.get('user_id', ''),
                    'patient': '',
                    'action': entry.get('action', ''),
                    'access_type': entry.get('resource', ''),
                    'ip': '',
                    'status': entry.get('details', 'AUTH')
                })
            if not combined:
                self.display_settings_message('No audit records available.')
                return
            for entry in combined:
                self.audit_tree.insert('', 'end', values=(
                    entry.get('timestamp', ''),
                    entry.get('user', ''),
                    entry.get('patient', ''),
                    entry.get('action', ''),
                    entry.get('access_type', ''),
                    entry.get('ip', ''),
                    entry.get('status', '')
                ))
        except Exception as e:
            logger.exception('Error retrieving audit log: %s', e)
            self.display_settings_message('Error retrieving audit log. Information not available at this time.')

    def clear_audit_tree(self):
        """Clear the audit log tree view."""
        if not hasattr(self, 'audit_tree'):
            return
        for item in self.audit_tree.get_children():
            self.audit_tree.delete(item)
    
    def show_database_info(self):
        """Show database information"""
        if not self.ensure_settings_ui():
            return
        try:
            patient_db_path = self.db.db_path if hasattr(self.db, 'db_path') else self.resolve_path('cardiac_patients.db')
            auth_db_path = self.auth.db_path if hasattr(self.auth, 'db_path') else self.resolve_path('cardiac_auth.db')
            hipaa_db_path = self.hipaa.db_path if hasattr(self.hipaa, 'db_path') else self.resolve_path('hipaa_compliance.db')
            fda_db_path = self.fda.db_path if hasattr(self.fda, 'db_path') else self.resolve_path('fda_compliance.db')

            patient_size = os.path.getsize(patient_db_path) if os.path.exists(patient_db_path) else 0
            auth_size = os.path.getsize(auth_db_path) if os.path.exists(auth_db_path) else 0
            hipaa_size = os.path.getsize(hipaa_db_path) if os.path.exists(hipaa_db_path) else 0
            fda_size = os.path.getsize(fda_db_path) if os.path.exists(fda_db_path) else 0

            patient_count = self.db.get_patient_count() if hasattr(self.db, 'get_patient_count') else 0
            prediction_count = self.db.get_prediction_count() if hasattr(self.db, 'get_prediction_count') else 0
            auth_audit_count = len(self.auth.get_audit_log(limit=1000)) if hasattr(self.auth, 'get_audit_log') else 0
            hipaa_audit_count = len(self.hipaa.get_audit_log(limit=1000)) if hasattr(self.hipaa, 'get_audit_log') else 0
            fda_checklist_items = 0
            if hasattr(self.fda, 'get_510k_checklist'):
                checklist = self.fda.get_510k_checklist()
                fda_checklist_items = sum(len(v) for v in checklist.values()) if isinstance(checklist, dict) else 0

            info = [
                'DATABASE INFORMATION',
                '====================',
                '',
                f'PATIENT DATABASE: {os.path.basename(patient_db_path)}',
                f'  Exists: {"Yes" if os.path.exists(patient_db_path) else "No"}',
                f'  Size: {patient_size / 1024:.1f} KB',
                f'  Total Patients: {patient_count}',
                f'  Total Predictions: {prediction_count}',
                '',
                f'AUTHENTICATION DATABASE: {os.path.basename(auth_db_path)}',
                f'  Exists: {"Yes" if os.path.exists(auth_db_path) else "No"}',
                f'  Size: {auth_size / 1024:.1f} KB',
                f'  Audit Log Entries: {auth_audit_count}',
                '',
                f'HIPAA COMPLIANCE DATABASE: {os.path.basename(hipaa_db_path)}',
                f'  Exists: {"Yes" if os.path.exists(hipaa_db_path) else "No"}',
                f'  Size: {hipaa_size / 1024:.1f} KB',
                f'  HIPAA Audit Entries: {hipaa_audit_count}',
                '',
                f'FDA COMPLIANCE DATABASE: {os.path.basename(fda_db_path)}',
                f'  Exists: {"Yes" if os.path.exists(fda_db_path) else "No"}',
                f'  Size: {fda_size / 1024:.1f} KB',
                f'  FDA Checklist Items Defined: {fda_checklist_items}',
                '',
                'NOTE: Database contents are reported without modification.'
            ]
            self.display_settings_message('\n'.join(info))
        except Exception as e:
            logger.exception('Error displaying database information: %s', e)
            self.display_settings_message('Error retrieving database information. Information not available at this time.')

    def show_model_info(self):
        """Show ML model information"""
        if not self.ensure_settings_ui():
            return
        info = """
╔════════════════════════════════════════════════════════════╗
║          MACHINE LEARNING MODEL INFORMATION                ║
╚════════════════════════════════════════════════════════════╝

ENSEMBLE ARCHITECTURE:
═══════════════════════════════════════════════════════════

Model Type: 5-Model Ensemble Voting Classifier

BASE MODELS:
1. K-Nearest Neighbors (KNN)
   - K: 5
   - Accuracy: 98.90%
   - Strength: Captures local patterns

2. Random Forest
   - Trees: 200
   - Depth: 15
   - Accuracy: 97.43%
   - Strength: Feature importance

3. Gradient Boosting
   - Estimators: 100
   - Learning Rate: 0.1
   - Accuracy: 98.90%
   - Strength: Sequential error correction

4. Support Vector Machine (SVM)
   - Kernel: RBF
   - Accuracy: 58.46%
   - Strength: High-dimensional separation

5. Voting Classifier
   - Strategy: Hard Voting
   - Final Accuracy: 97.43%
   - Confidence: Probability averaging

TRAINING DATA:
═══════════════════════════════════════════════════════════
Training Samples: 1,356
Test Samples: 584
Features: 7 (QRS, QT, T-Wave, Age, Height, Weight, Sex)
Classes: 13 (Cardiac conditions)
Feature Scaling: StandardScaler
Validation: 5-Fold Cross-Validation

PERFORMANCE METRICS:
═══════════════════════════════════════════════════════════
Overall Accuracy: 97.43%
Precision: 96.8%
Recall: 96.5%
F1-Score: 96.6%
Confusion Matrix: 13x13 condition classification

MODEL FILE:
═══════════════════════════════════════════════════════════
Filename: ensemble_model.joblib
Size: ~50 MB
Format: Scikit-learn Joblib
Last Updated: 2024-12-15
Version: 2.0 Enterprise

EXPLAINABILITY:
═══════════════════════════════════════════════════════════
Method: SHAP (SHapley Additive exPlanations)
Fallback: Permutation Feature Importance
Top Factors Displayed: 7
Update Frequency: Real-time

STATUS: ✓ PRODUCTION READY
"""
        self.settings_text.delete(1.0, tk.END)
        self.settings_text.insert(tk.END, info)
    
    def show_api_info(self):
        """Show REST API information"""
        if not self.ensure_settings_ui():
            return
        info = """
╔════════════════════════════════════════════════════════════╗
║            REST API CONFIGURATION                          ║
╚════════════════════════════════════════════════════════════╝

API SERVER: Flask-based REST API
Status: Ready for deployment
Base URL: http://localhost:5000/api

AVAILABLE ENDPOINTS:
═══════════════════════════════════════════════════════════

1. POST /predict
   Description: Single ECG prediction
   Input: ECG parameters (QRS, QT, T-Wave, demographics)
   Output: Prediction, confidence, risk scores
   Rate Limit: 100 requests/minute

2. POST /predict_batch
   Description: Batch predictions
   Input: Array of ECG parameters
   Output: Multiple predictions
   Rate Limit: 10 requests/minute

3. GET /patient/<id>
   Description: Retrieve patient records
   Input: Patient ID
   Output: Patient demographics, prediction history
   Authentication: Token required

4. POST /patient
   Description: Create new patient
   Input: Patient demographics
   Output: Patient ID
   Authentication: Token required

5. GET /reports/<id>
   Description: Generate clinical report
   Input: Patient ID
   Output: PDF report
   Authentication: Token required

6. GET /model/info
   Description: Model information
   Output: Ensemble architecture, performance metrics
   Rate Limit: Unlimited

7. POST /auth/login
   Description: User authentication
   Input: Username, password
   Output: JWT token, session info
   Authentication: Basic auth

AUTHENTICATION:
═══════════════════════════════════════════════════════════
Method: JWT Bearer Token
Token Lifetime: 24 hours
Roles: 4-level RBAC (Admin, Doctor, Technician, Viewer)
Encryption: PBKDF2-HMAC-SHA256

DEPLOYMENT:
═══════════════════════════════════════════════════════════
To start API server:
  python api_server.py

To use with hospital EHR systems:
  - Enable CORS on api_server.py
  - Configure firewall/network access
  - Set up HTTPS/TLS for production
  - Enable audit logging

STATUS: ✓ READY FOR INTEGRATION
"""
        self.settings_text.delete(1.0, tk.END)
        self.settings_text.insert(tk.END, info)

# Main
if __name__ == "__main__":
    logger.info("Launching CardioClinic AI Responsive Dashboard...")
    root = tk.Tk()
    app = CardiacArrhythmiaApp(root, "CardioClinic AI Responsive Dashboard")
    root.mainloop()
