"""
Advanced Analytics Module
Provides comprehensive analytics, statistics, and insights
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
import numpy as np
from collections import defaultdict, Counter

class AdvancedAnalytics:
    """Advanced analytics and reporting"""
    
    def __init__(self, patient_db_path='cardiac_patients.db', auth_db_path='cardiac_auth.db'):
        """Initialize analytics engine"""
        self.patient_db = patient_db_path
        self.auth_db = auth_db_path
    
    def get_patient_statistics(self) -> Dict:
        """Get comprehensive patient statistics"""
        try:
            conn = sqlite3.connect(self.patient_db)
            cursor = conn.cursor()
            
            # Total patients
            cursor.execute('SELECT COUNT(*) FROM patients')
            total_patients = cursor.fetchone()[0]
            
            # Demographics
            cursor.execute('SELECT age FROM patients')
            ages = [row[0] for row in cursor.fetchall()]
            
            cursor.execute('SELECT sex FROM patients')
            sexes = [row[0] for row in cursor.fetchall()]
            
            # Age statistics
            age_stats = {
                'mean': float(np.mean(ages)) if ages else 0,
                'median': float(np.median(ages)) if ages else 0,
                'std': float(np.std(ages)) if ages else 0,
                'min': int(np.min(ages)) if ages else 0,
                'max': int(np.max(ages)) if ages else 0
            }
            
            # Sex distribution
            sex_count = Counter(sexes)
            sex_dist = {
                'male': sex_count.get(1, 0),
                'female': sex_count.get(0, 0)
            }
            
            # Age groups
            age_groups = self._get_age_groups(ages)
            
            conn.close()
            
            return {
                'total_patients': total_patients,
                'age_statistics': age_stats,
                'sex_distribution': sex_dist,
                'age_groups': age_groups,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_prediction_statistics(self) -> Dict:
        """Get prediction statistics"""
        try:
            conn = sqlite3.connect(self.patient_db)
            cursor = conn.cursor()
            
            # Total predictions
            cursor.execute('SELECT COUNT(*) FROM predictions')
            total_predictions = cursor.fetchone()[0]
            
            # Predictions by condition
            cursor.execute('''
                SELECT predicted_condition, COUNT(*) as count
                FROM predictions
                GROUP BY predicted_condition
                ORDER BY count DESC
            ''')
            condition_dist = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Confidence scores
            cursor.execute('SELECT confidence_score FROM predictions')
            confidences = [row[0] for row in cursor.fetchall()]
            
            confidence_stats = {
                'mean': float(np.mean(confidences)) if confidences else 0,
                'median': float(np.median(confidences)) if confidences else 0,
                'std': float(np.std(confidences)) if confidences else 0,
                'min': float(np.min(confidences)) if confidences else 0,
                'max': float(np.max(confidences)) if confidences else 0
            }
            
            # Recent predictions (last 7 days)
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute('''
                SELECT COUNT(*) FROM predictions
                WHERE created_at > ?
            ''', (seven_days_ago,))
            recent_predictions = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_predictions': total_predictions,
                'condition_distribution': condition_dist,
                'confidence_statistics': confidence_stats,
                'recent_predictions_7days': recent_predictions,
                'average_confidence_percent': round(confidence_stats['mean'] * 100, 2),
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_user_activity(self, days: int = 30) -> Dict:
        """Get user activity over time period"""
        try:
            conn = sqlite3.connect(self.auth_db)
            cursor = conn.cursor()
            
            # Logins
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute('''
                SELECT user_id, COUNT(*) as count
                FROM audit_log
                WHERE action = 'LOGIN' AND timestamp > ?
                GROUP BY user_id
                ORDER BY count DESC
            ''', (start_date,))
            
            login_activity = [{
                'user_id': row[0],
                'login_count': row[1]
            } for row in cursor.fetchall()]
            
            # Total active users
            cursor.execute('''
                SELECT COUNT(DISTINCT user_id)
                FROM audit_log
                WHERE timestamp > ?
            ''', (start_date,))
            active_users = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'period_days': days,
                'active_users': active_users,
                'login_activity': login_activity,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_condition_risk_analysis(self) -> Dict:
        """Analyze risk distribution across conditions"""
        try:
            conn = sqlite3.connect(self.patient_db)
            cursor = conn.cursor()
            
            # Risk scores by condition
            cursor.execute('''
                SELECT 
                    predicted_condition,
                    json_extract(risk_scores, '$.cha2ds2_vasc.score') as cha2ds2,
                    json_extract(risk_scores, '$.timi_risk.score') as timi,
                    json_extract(risk_scores, '$.framingham.score') as framingham
                FROM predictions
            ''')
            
            condition_risks = defaultdict(list)
            for row in cursor.fetchall():
                condition = row[0]
                risks = [float(r) if r else 0 for r in row[1:]]
                condition_risks[condition].extend(risks)
            
            # Average risk by condition
            avg_risks = {}
            for condition, risks in condition_risks.items():
                avg_risks[condition] = float(np.mean(risks)) if risks else 0
            
            conn.close()
            
            return {
                'conditions_analyzed': len(avg_risks),
                'average_risks_by_condition': avg_risks,
                'highest_risk_condition': max(avg_risks.items(), key=lambda x: x[1]) if avg_risks else None,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_temporal_analysis(self) -> Dict:
        """Analyze temporal patterns in data"""
        try:
            conn = sqlite3.connect(self.patient_db)
            cursor = conn.cursor()
            
            # Predictions by day of week
            cursor.execute('''
                SELECT 
                    strftime('%w', created_at) as day_of_week,
                    COUNT(*) as count
                FROM predictions
                GROUP BY day_of_week
                ORDER BY day_of_week
            ''')
            
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            daily_dist = {
                day_names[int(row[0])]: row[1] if row[1] else 0 
                for row in cursor.fetchall()
            }
            
            # Predictions by hour
            cursor.execute('''
                SELECT 
                    strftime('%H', created_at) as hour,
                    COUNT(*) as count
                FROM predictions
                GROUP BY hour
                ORDER BY hour
            ''')
            
            hourly_dist = {row[0]: row[1] for row in cursor.fetchall()}
            
            # Predictions by month
            cursor.execute('''
                SELECT 
                    strftime('%Y-%m', created_at) as month,
                    COUNT(*) as count
                FROM predictions
                GROUP BY month
                ORDER BY month DESC
                LIMIT 12
            ''')
            
            monthly_dist = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'daily_distribution': daily_dist,
                'hourly_distribution': hourly_dist,
                'monthly_distribution': monthly_dist,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def get_model_performance_metrics(self) -> Dict:
        """Get model performance metrics"""
        try:
            conn = sqlite3.connect(self.patient_db)
            cursor = conn.cursor()
            
            # Confidence score distribution
            cursor.execute('SELECT confidence_score FROM predictions WHERE confidence_score IS NOT NULL')
            confidences = []
            for (score,) in cursor.fetchall():
                score = float(score)
                if 1 < score <= 100:
                    score /= 100
                elif not 0 <= score <= 1:
                    raise ValueError(f'Invalid confidence score: {score}')
                confidences.append(score)
            
            # Keep tier boundaries aligned with the prediction result labels.
            high_confidence = sum(1 for c in confidences if c > 0.85)
            medium_confidence = sum(1 for c in confidences if 0.50 <= c <= 0.85)
            low_confidence = sum(1 for c in confidences if c < 0.50)
            
            total = len(confidences)
            
            conn.close()
            
            return {
                'total_predictions': total,
                'high_confidence_count': high_confidence,
                'medium_confidence_count': medium_confidence,
                'low_confidence_count': low_confidence,
                'high_confidence_percent': round(high_confidence/total*100, 2) if total else 0,
                'medium_confidence_percent': round(medium_confidence/total*100, 2) if total else 0,
                'low_confidence_percent': round(low_confidence/total*100, 2) if total else 0,
                'average_confidence': round(np.mean(confidences)*100, 2) if confidences else 0,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            return {'error': str(e)}
    
    def generate_summary_report(self) -> Dict:
        """Generate comprehensive summary report"""
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'patient_statistics': self.get_patient_statistics(),
                'prediction_statistics': self.get_prediction_statistics(),
                'user_activity': self.get_user_activity(days=30),
                'condition_risk_analysis': self.get_condition_risk_analysis(),
                'temporal_analysis': self.get_temporal_analysis(),
                'model_performance': self.get_model_performance_metrics()
            }
            return report
        
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _get_age_groups(ages: List[int]) -> Dict:
        """Group ages into categories"""
        age_groups = {
            '18-30': 0,
            '31-40': 0,
            '41-50': 0,
            '51-60': 0,
            '61-70': 0,
            '71+': 0
        }
        
        for age in ages:
            if 18 <= age <= 30:
                age_groups['18-30'] += 1
            elif 31 <= age <= 40:
                age_groups['31-40'] += 1
            elif 41 <= age <= 50:
                age_groups['41-50'] += 1
            elif 51 <= age <= 60:
                age_groups['51-60'] += 1
            elif 61 <= age <= 70:
                age_groups['61-70'] += 1
            else:
                age_groups['71+'] += 1
        
        return age_groups
    
    def get_system_overview(self) -> str:
        """Generate human-readable system overview"""
        stats = self.get_patient_statistics()
        pred_stats = self.get_prediction_statistics()
        
        text = "╔═══════════════════════════════════════════════════════════╗\n"
        text += "║        SYSTEM OVERVIEW - CARDIAC ARRHYTHMIA             ║\n"
        text += "╚═══════════════════════════════════════════════════════════╝\n\n"
        
        text += "📊 PATIENT STATISTICS:\n"
        text += f"  Total Patients: {stats.get('total_patients', 0)}\n"
        if 'age_statistics' in stats:
            age_stat = stats['age_statistics']
            text += f"  Average Age: {age_stat.get('mean', 0):.1f} years\n"
            text += f"  Age Range: {age_stat.get('min', 0)} - {age_stat.get('max', 0)} years\n"
        
        if 'sex_distribution' in stats:
            sex = stats['sex_distribution']
            text += f"  Sex Distribution: {sex.get('male', 0)} Male, {sex.get('female', 0)} Female\n"
        
        text += "\n📈 PREDICTION STATISTICS:\n"
        text += f"  Total Predictions: {pred_stats.get('total_predictions', 0)}\n"
        text += f"  Average Confidence: {pred_stats.get('average_confidence', 0):.1f}%\n"
        
        return text
    
    def get_risk_analysis(self) -> str:
        """Generate human-readable risk analysis report"""
        risk_data = self.get_condition_risk_analysis()
        
        text = "╔═══════════════════════════════════════════════════════════╗\n"
        text += "║              RISK ANALYSIS BY CONDITION                  ║\n"
        text += "╚═══════════════════════════════════════════════════════════╝\n\n"
        
        text += f"Conditions Analyzed: {risk_data.get('conditions_analyzed', 0)}\n\n"
        text += "Average Risk by Condition:\n"
        
        for condition, risk in sorted(risk_data.get('average_risks_by_condition', {}).items(), 
                                       key=lambda x: x[1], reverse=True):
            text += f"  {condition}: {risk:.2f}\n"
        
        return text
