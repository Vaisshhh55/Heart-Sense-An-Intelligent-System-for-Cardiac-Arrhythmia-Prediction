"""
Patient Database Management Module
Handles patient records, prediction history, and data persistence
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional
import os

class PatientDatabase:
    def __init__(self, db_path='cardiac_patients.db'):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                sex TEXT,
                height REAL,
                weight REAL,
                bmi REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Predictions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                age INTEGER,
                sex TEXT,
                height REAL,
                weight REAL,
                qrs_interval REAL,
                qt_interval REAL,
                t_interval REAL,
                predicted_condition TEXT,
                condition_code INTEGER,
                confidence_score REAL,
                all_predictions TEXT,
                risk_scores TEXT,
                explanation_features TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                doctor_notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        ''')
        
        # Medical history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medical_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                condition TEXT,
                diagnosis_date TIMESTAMP,
                medications TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
        ''')
        
        # Ensure prediction table includes optional history columns for PDF and report tracking.
        self._ensure_prediction_table_columns(cursor)
        
        conn.commit()
        conn.close()

    def _ensure_prediction_table_columns(self, cursor):
        """Add optional columns to predictions table if missing."""
        cursor.execute("PRAGMA table_info(predictions)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        if 'pdf_path' not in existing_columns:
            cursor.execute('ALTER TABLE predictions ADD COLUMN pdf_path TEXT')
        if 'report_id' not in existing_columns:
            cursor.execute('ALTER TABLE predictions ADD COLUMN report_id TEXT')
    
    def add_patient(self, name: str, age: int, sex: str, height: float, weight: float) -> int:
        """Add new patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        bmi = weight / ((height / 100) ** 2) if height > 0 else 0
        
        cursor.execute('''
            INSERT INTO patients (name, age, sex, height, weight, bmi)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, age, sex, height, weight, bmi))
        
        patient_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return patient_id
    
    def get_patient(self, patient_id: int) -> Optional[Dict]:
        """Get patient information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM patients WHERE patient_id = ?', (patient_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            columns = ['patient_id', 'name', 'age', 'sex', 'height', 'weight', 'bmi', 'created_at', 'updated_at']
            return dict(zip(columns, result))
        return None

    def get_patient_by_name(self, name: str) -> Optional[Dict]:
        """Get patient by exact name match."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients WHERE LOWER(name) = LOWER(?) LIMIT 1', (name.strip(),))
        result = cursor.fetchone()
        conn.close()

        if result:
            columns = ['patient_id', 'name', 'age', 'sex', 'height', 'weight', 'bmi', 'created_at', 'updated_at']
            return dict(zip(columns, result))
        return None

    def update_patient(self, patient_id: int, name: str, age: int, sex: str, height: float, weight: float) -> bool:
        """Update a patient's demographic record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        bmi = weight / ((height / 100) ** 2) if height > 0 else 0
        cursor.execute('''
            UPDATE patients
            SET name = ?, age = ?, sex = ?, height = ?, weight = ?, bmi = ?, updated_at = ?
            WHERE patient_id = ?
        ''', (name, age, sex, height, weight, bmi, datetime.now().isoformat(), patient_id))

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def delete_patient(self, patient_id: int) -> bool:
        """Delete a patient and associated records."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM predictions WHERE patient_id = ?', (patient_id,))
        cursor.execute('DELETE FROM medical_history WHERE patient_id = ?', (patient_id,))
        cursor.execute('DELETE FROM patients WHERE patient_id = ?', (patient_id,))

        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0

    def search_patient(self, name: str) -> List[Dict]:
        """Search patients by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM patients WHERE name LIKE ? ORDER BY created_at DESC', (f'%{name}%',))
        results = cursor.fetchall()
        conn.close()
        
        columns = ['patient_id', 'name', 'age', 'sex', 'height', 'weight', 'bmi', 'created_at', 'updated_at']
        return [dict(zip(columns, row)) for row in results]
    
    def search_patients(self, name: str) -> List[Dict]:
        """Search patients by name (alias for search_patient)"""
        if not name:
            return self.get_all_patients()
        return self.search_patient(name)

    def get_all_patients(self, limit: int = 1000) -> List[Dict]:
        """Retrieve all patients from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM patients ORDER BY created_at DESC LIMIT ?', (limit,))
        results = cursor.fetchall()
        conn.close()

        columns = ['patient_id', 'name', 'age', 'sex', 'height', 'weight', 'bmi', 'created_at', 'updated_at']
        return [dict(zip(columns, row)) for row in results]
    
    def add_prediction(self, name: str, condition_code: int, confidence: float, 
                      qrs: float, qt: float, t_interval: float,
                      age: int, sex: str, height: float, weight: float,
                      all_predictions: Dict = None, risk_scores: Dict = None,
                      explanation_features: Dict = None, pdf_path: str = None,
                      report_id: str = None, predicted_condition: str = None) -> int:
        """Add prediction record - simplified version"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First check if patient exists, if not create them
        cursor.execute('SELECT patient_id FROM patients WHERE name = ?', (name,))
        result = cursor.fetchone()
        
        if result:
            patient_id = result[0]
        else:
            # Create new patient
            bmi = weight / ((height / 100) ** 2) if height > 0 else 0
            cursor.execute('''
                INSERT INTO patients (name, age, sex, height, weight, bmi)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, age, sex, height, weight, bmi))
            patient_id = cursor.lastrowid
        
        all_predictions = all_predictions or {}
        risk_scores = risk_scores or {}
        explanation_features = explanation_features or {}
        predicted_condition = predicted_condition or f"Condition {condition_code}"

        cursor.execute('''
            INSERT INTO predictions 
            (patient_id, age, sex, height, weight, qrs_interval, qt_interval, t_interval,
             predicted_condition, condition_code, confidence_score, all_predictions, risk_scores, explanation_features, pdf_path, report_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, age, sex, height, weight, qrs, qt, t_interval,
              predicted_condition, condition_code, confidence,
              json.dumps(all_predictions),
              json.dumps(risk_scores),
              json.dumps(explanation_features),
              pdf_path or '',
              report_id or ''))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return prediction_id
    
    def add_prediction_full(self, patient_id: int, age: int, sex: str, height: float, weight: float,
                      qrs_interval: float, qt_interval: float, t_interval: float,
                      predicted_condition: str, condition_code: int, confidence_score: float,
                      all_predictions: Dict, risk_scores: Dict, explanation_features: Dict) -> int:
        """Add prediction record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions 
            (patient_id, age, sex, height, weight, qrs_interval, qt_interval, t_interval,
             predicted_condition, condition_code, confidence_score, all_predictions, risk_scores, explanation_features)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (patient_id, age, sex, height, weight, qrs_interval, qt_interval, t_interval,
              predicted_condition, condition_code, confidence_score,
              json.dumps(all_predictions),
              json.dumps(risk_scores),
              json.dumps(explanation_features)))
        
        prediction_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return prediction_id
    
    def get_patient_predictions(self, patient_id: int, limit: int = 10) -> List[Dict]:
        """Get prediction history for a patient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM predictions 
            WHERE patient_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (patient_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['prediction_id', 'patient_id', 'age', 'sex', 'height', 'weight',
                  'qrs_interval', 'qt_interval', 't_interval', 'predicted_condition',
                  'condition_code', 'confidence_score', 'all_predictions', 'risk_scores',
                  'explanation_features', 'created_at', 'doctor_notes']
        
        predictions = []
        for row in results:
            pred_dict = dict(zip(columns, row))
            # Parse JSON fields
            pred_dict['all_predictions'] = json.loads(pred_dict['all_predictions'])
            pred_dict['risk_scores'] = json.loads(pred_dict['risk_scores'])
            pred_dict['explanation_features'] = json.loads(pred_dict['explanation_features'])
            predictions.append(pred_dict)
        
        return predictions
    
    def update_doctor_notes(self, prediction_id: int, notes: str):
        """Update doctor notes for a prediction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE predictions 
            SET doctor_notes = ?
            WHERE prediction_id = ?
        ''', (notes, prediction_id))
        
        conn.commit()
        conn.close()

    def update_prediction_report_info(self, prediction_id: int, pdf_path: str, report_id: str):
        """Update PDF export and report metadata for a prediction."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE predictions
            SET pdf_path = ?, report_id = ?
            WHERE prediction_id = ?
        ''', (pdf_path, report_id, prediction_id))

        conn.commit()
        conn.close()
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM patients')
        total_patients = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total_predictions = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT predicted_condition, COUNT(*) as count 
            FROM predictions 
            GROUP BY predicted_condition 
            ORDER BY count DESC
        ''')
        condition_distribution = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            'total_patients': total_patients,
            'total_predictions': total_predictions,
            'condition_distribution': condition_distribution
        }
    
    def get_patient_count(self) -> int:
        """Get total patient count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM patients')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_prediction_count(self, patient_id: int = None) -> int:
        """Get total or patient-specific prediction count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if patient_id:
            cursor.execute('SELECT COUNT(*) FROM predictions WHERE patient_id = ?', (patient_id,))
        else:
            cursor.execute('SELECT COUNT(*) FROM predictions')
        
        count = cursor.fetchone()[0]
        conn.close()
        return count


# Global database instance
_db_instance = None

def get_database(db_path='cardiac_patients.db') -> PatientDatabase:
    """Get or create database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = PatientDatabase(db_path)
    return _db_instance
