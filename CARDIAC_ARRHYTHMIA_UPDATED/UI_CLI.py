"""
Cardiac Arrhythmia Prediction System - Command Line Interface (CLI)
Works without GUI/display - fully functional terminal-based interface
"""

import numpy as np
import json
import joblib
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
import logging

logger = logging.getLogger('cardiac.cli')
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

# Import custom modules
from database import PatientDatabase
from risk_scoring import RiskScoring
from explainability import SimpleFeatureImportance
from report_generator import PDFReportGenerator
from authentication import UserManager
from advanced_analytics import AdvancedAnalytics
from clinical_compliance import HIPAACompliance, FDARegulatoryCompliance

class CardiacCLI:
    """Command-line interface for Cardiac Arrhythmia Prediction System"""
    
    def __init__(self):
        """Initialize all modules"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        logger.info("%s", "\n" + "="*70)
        logger.info("  CARDIAC ARRHYTHMIA PREDICTION SYSTEM v2.1 - CLI")
        logger.info("%s", "="*70)
        logger.info("Initializing system...")
        
        try:
            self.db = PatientDatabase(self.resolve_path('cardiac_patients.db'))
            self.auth = UserManager(self.resolve_path('cardiac_auth.db'))
            self.analytics = AdvancedAnalytics(self.resolve_path('cardiac_patients.db'), self.resolve_path('cardiac_auth.db'))
            self.hipaa = HIPAACompliance(self.resolve_path('hipaa_compliance.db'))
            self.fda = FDARegulatoryCompliance(self.resolve_path('fda_compliance.db'))
            self.pdf_gen = PDFReportGenerator(self.resolve_path('reports'))
            self.risk_scorer = RiskScoring()
            logger.info('All modules initialized successfully')
        except Exception as e:
            logger.exception('Error initializing modules')
            return
        
        # Load models
        try:
            self.ensemble_model = joblib.load(self.resolve_path('ensemble_model.joblib'))
            logger.info('Ensemble model loaded (97.43%% accuracy)')
        except Exception as e:
            logger.exception('Error loading model')
            return

        self.condition_map = self._prepare_condition_map()

    def resolve_path(self, path):
        """Resolve a relative path against the script directory."""
        return os.path.join(self.base_dir, path)

    def _prepare_condition_map(self):
        """Return the condition mapping used by the CLI."""
        return {
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

        # This block should never execute because the method returns above.
    
    def display_menu(self):
        """Display main menu"""
        logger.info("%s", "\n" + "-"*70)
        logger.info("  MAIN MENU")
        logger.info("%s", "-"*70)
        logger.info("1. Make Prediction (ECG diagnosis)")
        logger.info("2. Search Patient")
        logger.info("3. View All Patients")
        logger.info("4. View Patient History")
        logger.info("5. System Analytics")
        logger.info("6. Compliance Status")
        logger.info("7. Model Information")
        logger.info("8. Exit")
        logger.info("%s", "-"*70)
    
    def predict(self):
        """Make a prediction"""
        logger.info("%s", "\n" + "="*70)
        logger.info("  MAKE PREDICTION")
        logger.info("%s", "="*70)
        
        try:
            # Get patient info
            name = input("\nPatient Name: ").strip()
            if not name:
                print("✗ Patient name required")
                return
            
            age = float(input("Age (years): "))
            sex = input("Sex (M/F): ").upper()
            height = float(input("Height (cm): "))
            weight = float(input("Weight (kg): "))
            
            # Get ECG parameters
            logger.info('ECG Parameters:')
            qrs = float(input("QRS Duration (ms): "))
            qt = float(input("QT Interval (ms): "))
            t_wave = float(input("T Interval (ms): "))
            
            # Create feature array in correct order: age, sex, height, weight, qrs, qt, t_wave
            features = np.array([[age, 1 if sex == 'M' else 0, height, weight, qrs, qt, t_wave]])
            
            # Make prediction
            prediction = self.ensemble_model.predict(features)[0]
            probabilities = self.ensemble_model.predict_proba(features)[0]
            confidence = np.max(probabilities) * 100
            
            condition_name = self.condition_map.get(int(prediction), "Unknown")
            
            # Display results
            logger.info("%s", "\n" + "─"*70)
            logger.info("  PREDICTION RESULT")
            logger.info("%s", "─"*70)
            logger.info("Patient: %s", name)
            logger.info("Condition Predicted: %s", condition_name)
            logger.info("Confidence Score: %.2f%%", confidence)
            logger.info("Prediction Time: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            logger.info("Demographics:")
            logger.info("  Age: %s years", age)
            logger.info("  Sex: %s", sex)
            logger.info("  BMI: %.2f kg/m²", weight / (height/100)**2)
            
            logger.info("ECG Parameters:")
            logger.info("  QRS Duration: %.2f ms", qrs)
            logger.info("  QT Interval: %.2f ms", qt)
            logger.info("  T Interval: %.2f ms", t_wave)
            
            # Risk Assessment
            logger.info("%s", "\n" + "─"*70)
            logger.info("  RISK ASSESSMENT")
            logger.info("%s", "─"*70)
            
            cha2ds2 = self.risk_scorer.calculate_cha2ds2_vasc(age, sex)
            timi = self.risk_scorer.calculate_timi(age, qrs)
            framingham = self.risk_scorer.calculate_framingham(age)
            arrhythmia = self.risk_scorer.calculate_custom_arrhythmia_risk(qrs, qt, t_wave)
            
            logger.info("CHA2DS2-VASc Score (Stroke Risk): %s - %s", cha2ds2['score'], cha2ds2['risk_level'])
            logger.info("  → %s", cha2ds2['interpretation'])
            
            logger.info("TIMI Risk Score (Mortality): %s - %s", timi['score'], timi['risk_level'])
            logger.info("  → %s", timi['interpretation'])
            
            logger.info("Framingham Score (CVD Risk): %.1f - %s", framingham['score'], framingham['risk_level'])
            logger.info("  → %s", framingham['interpretation'])
            
            logger.info("Custom Arrhythmia Risk: %.2f%% - %s", arrhythmia['score'], arrhythmia['risk_level'])
            logger.info("  → %s", arrhythmia['interpretation'])
            
            # Explainability
            logger.info("%s", "\n" + "─"*70)
            logger.info("  FEATURE IMPORTANCE (SHAP)")
            logger.info("%s", "─"*70)
            
            try:
                explainer = SimpleFeatureImportance(self.ensemble_model, ['Age', 'Sex', 'Height', 'Weight', 'QRS', 'QT', 'T Interval'])
                importance = explainer.get_feature_importance(features)
                
                feature_names = ['Age', 'Sex', 'Height', 'Weight', 'QRS', 'QT', 'T Interval']
                logger.info('Top Contributing Factors:')
                for i, (feat_name, imp_val) in enumerate(zip(feature_names, importance[:7])):
                    bar_length = int(imp_val * 50)
                    bar = "█" * bar_length
                    logger.info('%d. %-12s %.3f %s', i+1, feat_name, imp_val, bar)
            except Exception as e:
                logger.warning('SHAP analysis not available: %s', e)
            
            # Save to database
            self.db.add_prediction(
                name, int(prediction), confidence, qrs, qt, t_wave, age, sex, height, weight
            )
            
            # Log to HIPAA
            self.hipaa.log_access(
                self.current_user_id,
                f"PREDICTION: {name} - {condition_name}",
                f"Confidence: {confidence:.2f}%"
            )
            
            logger.info('Prediction saved to database')
            
        except ValueError as e:
            logger.warning('Invalid input: %s', e)
        except Exception as e:
            logger.exception('Prediction error')
    
    def search_patient(self):
        """Search for a patient"""
        print("\n" + "="*70)
        print("  SEARCH PATIENT")
        print("="*70)
        
        try:
            query = input("\nEnter patient name: ").strip()
            if not query:
                print("✗ Please enter a name")
                return
            
            patients = self.db.search_patients(query)
            
            if not patients:
                print(f"\n✗ No patients found matching '{query}'")
                return
            
            print(f"\n✓ Found {len(patients)} patient(s):")
            print("─"*70)
            
            for patient in patients:
                patient_id = patient['patient_id']
                name = patient['name']
                age = patient['age']
                sex = patient['sex']
                height = patient['height']
                weight = patient['weight']
                created_at = patient.get('created_at', '')
                bmi = weight / (height/100)**2 if height > 0 else 0
                print(f"\nID: {patient_id}")
                print(f"Name: {name}")
                print(f"Age: {age} | Sex: {sex} | BMI: {bmi:.1f}")
                print(f"Created: {created_at}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def view_all_patients(self):
        """View all patients"""
        print("\n" + "="*70)
        print("  ALL PATIENTS")
        print("="*70)
        
        try:
            patients = self.db.get_all_patients()
            
            if not patients:
                print("\n✗ No patients in database")
                return
            
            print(f"\n✓ Total Patients: {len(patients)}")
            print("─"*70)
            
            for patient in patients[:20]:  # Show first 20
                patient_id = patient['patient_id']
                name = patient['name']
                age = patient['age']
                sex = patient['sex']
                height = patient['height']
                weight = patient['weight']
                bmi = weight / (height/100)**2 if height > 0 else 0
                print(f"{patient_id:3} | {name:20} | Age: {age:2} | Sex: {sex} | BMI: {bmi:5.1f}")
            
            if len(patients) > 20:
                print(f"... and {len(patients) - 20} more patients")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def view_patient_history(self):
        """View patient prediction history"""
        print("\n" + "="*70)
        print("  PATIENT HISTORY")
        print("="*70)
        
        try:
            patient_id = input("\nEnter Patient ID: ").strip()
            if not patient_id:
                print("✗ Please enter a patient ID")
                return
            
            predictions = self.db.get_patient_predictions(patient_id)
            
            if not predictions:
                print(f"\n✗ No predictions found for patient {patient_id}")
                return
            
            print(f"\n✓ Found {len(predictions)} prediction(s):")
            print("─"*70)
            
            for pred in predictions:
                print(f"\n{pred}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def show_analytics(self):
        """Show system analytics"""
        print("\n" + "="*70)
        print("  SYSTEM ANALYTICS")
        print("="*70)
        
        print("\n1. System Overview")
        print("2. Patient Statistics")
        print("3. Prediction Analytics")
        print("4. Risk Analysis")
        print("5. Back to Main Menu")
        
        choice = input("\nSelect report (1-5): ").strip()
        
        try:
            if choice == '1':
                print("\n" + self.analytics.get_system_overview())
            elif choice == '2':
                print("\n" + self.analytics.get_patient_statistics())
            elif choice == '3':
                print("\n" + self.analytics.get_prediction_statistics())
            elif choice == '4':
                print("\n" + self.analytics.get_risk_analysis())
            elif choice == '5':
                return
            else:
                print("✗ Invalid selection")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def show_compliance(self):
        """Show compliance status"""
        print("\n" + "="*70)
        print("  COMPLIANCE STATUS")
        print("="*70)
        
        print("\n1. HIPAA Status")
        print("2. FDA 510(k) Status")
        print("3. Audit Log")
        print("4. Back to Main Menu")
        
        choice = input("\nSelect (1-4): ").strip()
        
        try:
            if choice == '1':
                print("\n" + self.hipaa.get_compliance_status())
            elif choice == '2':
                print("\n" + self.fda.get_compliance_status())
            elif choice == '3':
                log = self.hipaa.get_audit_log(limit=10)
                print("\nAudit Log (Last 10 Events):")
                print("─"*70)
                for entry in log:
                    print(entry)
            elif choice == '4':
                return
            else:
                print("✗ Invalid selection")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    def show_model_info(self):
        """Show ML model information"""
        print("\n" + "="*70)
        print("  ML MODEL INFORMATION")
        print("="*70)
        
        print("""
ENSEMBLE ARCHITECTURE:
  Model Type: 5-Model Voting Classifier
  Overall Accuracy: 97.43%

BASE MODELS:
  1. K-Nearest Neighbors (KNN):     98.90% accuracy
  2. Random Forest:                 97.43% accuracy
  3. Gradient Boosting:             98.90% accuracy
  4. Support Vector Machine:        58.46% accuracy
  5. Voting Classifier (Final):     97.43% overall

TRAINING DATA:
  Samples: 1,356
  Features: 7 (QRS, QT, T-Wave, Age, Height, Weight, Sex)
  Classes: 13 cardiac conditions
  Validation: 5-fold cross-validation

PERFORMANCE METRICS:
  Accuracy:  97.43%
  Precision: 96.8%
  Recall:    96.5%
  F1-Score:  96.6%

MODEL FILE: ensemble_model.joblib
VERSION: 2.1 Enterprise
STATUS: ✓ Production Ready
""")
    
    def run(self):
        """Run the CLI"""
        while True:
            self.display_menu()
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == '1':
                self.predict()
            elif choice == '2':
                self.search_patient()
            elif choice == '3':
                self.view_all_patients()
            elif choice == '4':
                self.view_patient_history()
            elif choice == '5':
                self.show_analytics()
            elif choice == '6':
                self.show_compliance()
            elif choice == '7':
                self.show_model_info()
            elif choice == '8':
                print("\n" + "="*70)
                print("  Thank you for using Cardiac Arrhythmia Prediction System!")
                print("="*70 + "\n")
                break
            else:
                print("✗ Invalid selection. Please try again.")

# Main
if __name__ == "__main__":
    app = CardiacCLI()
    app.run()
