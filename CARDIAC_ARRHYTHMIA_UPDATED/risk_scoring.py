"""
Risk Stratification Module
Calculates various cardiac risk scores
"""

from typing import Dict

class RiskScoring:
    """Calculate cardiac risk scores"""
    
    @staticmethod
    def calculate_cha2ds2_vasc(age: int, sex: str, has_chf: bool = False, 
                               has_hypertension: bool = False, has_stroke: bool = False,
                               has_diabetes: bool = False, has_vascular_disease: bool = False) -> Dict:
        """
        CHA2DS2-VASc Score: Predicts stroke risk in atrial fibrillation patients
        
        Points:
        - C: Congestive heart failure (1 point)
        - H: Hypertension (1 point)
        - A2: Age ≥75 (2 points)
        - D: Diabetes (1 point)
        - S2: Stroke/TIA/thromboembolism history (2 points)
        - V: Vascular disease (1 point)
        - A: Age 65-74 (1 point)
        - Sc: Sex category (female) (1 point)
        
        Score 0: Low risk (0%)
        Score 1: Low-moderate risk (1.3%)
        Score 2-4: Moderate-high risk (2-4%)
        Score ≥5: High risk (>6%)
        """
        score = 0
        details = {}
        
        # C: Congestive heart failure
        if has_chf:
            score += 1
            details['CHF'] = 1
        
        # H: Hypertension
        if has_hypertension:
            score += 1
            details['Hypertension'] = 1
        
        # A2: Age ≥75
        if age >= 75:
            score += 2
            details['Age ≥75'] = 2
        # A: Age 65-74
        elif age >= 65:
            score += 1
            details['Age 65-74'] = 1
        
        # D: Diabetes
        if has_diabetes:
            score += 1
            details['Diabetes'] = 1
        
        # S2: Stroke/TIA history
        if has_stroke:
            score += 2
            details['Stroke/TIA history'] = 2
        
        # V: Vascular disease
        if has_vascular_disease:
            score += 1
            details['Vascular disease'] = 1
        
        # Sc: Female sex
        if sex.lower() in ['female', 'f']:
            score += 1
            details['Female sex'] = 1
        
        # Risk stratification
        if score == 0:
            risk_level = "Low"
            annual_stroke_risk = 0.0
            interpretation = "Annual stroke risk: 0%. No anticoagulation needed."
        elif score == 1:
            risk_level = "Low-Moderate"
            annual_stroke_risk = 1.3
            interpretation = "Annual stroke risk: 1.3%. Consider anticoagulation."
        elif score <= 4:
            risk_level = "Moderate-High"
            annual_stroke_risk = 2.2 + (score - 2) * 0.6
            interpretation = f"Annual stroke risk: {annual_stroke_risk:.1f}%. Anticoagulation recommended."
        else:
            risk_level = "High"
            annual_stroke_risk = 4.0 + (score - 5) * 1.5
            interpretation = f"Annual stroke risk: {annual_stroke_risk:.1f}%. Anticoagulation strongly recommended."
        
        return {
            'score': score,
            'risk_level': risk_level,
            'annual_stroke_risk_percent': annual_stroke_risk,
            'interpretation': interpretation,
            'details': details
        }
    
    @staticmethod
    def calculate_timi_risk(age: int, is_male: bool, has_history_cad: bool = False,
                           has_risk_factors: int = 0, has_aspirin: bool = False,
                           is_elevated_markers: bool = False) -> Dict:
        """
        TIMI Risk Score: Predicts mortality and adverse outcomes
        
        Points:
        - Age ≥65: 1 point
        - Risk factors: 1 point per factor
        - Known CAD: 1 point
        - Elevated cardiac markers: 1 point
        - Aspirin use in past 7 days: 1 point
        
        Total: 0-7 points
        """
        score = 0
        details = {}
        
        if age >= 65:
            score += 1
            details['Age ≥65'] = 1
        
        if not is_male:
            score += 1
            details['Female'] = 1
        
        if has_history_cad:
            score += 1
            details['History of CAD'] = 1
        
        score += min(has_risk_factors, 2)  # Max 2 points for risk factors
        if has_risk_factors > 0:
            details['Risk factors'] = min(has_risk_factors, 2)
        
        if has_aspirin:
            score += 1
            details['Aspirin use'] = 1
        
        if is_elevated_markers:
            score += 1
            details['Elevated markers'] = 1
        
        # Risk stratification
        risk_percentages = {
            0: 4.7, 1: 8.3, 2: 13.2, 3: 19.9,
            4: 26.2, 5: 40.9, 6: 56.4, 7: 84.1
        }
        
        mortality_percent = risk_percentages.get(score, 84.1)
        
        if score <= 1:
            risk_level = "Low"
            interpretation = f"30-day mortality risk: {mortality_percent}%. Low risk patient."
        elif score <= 3:
            risk_level = "Moderate"
            interpretation = f"30-day mortality risk: {mortality_percent}%. Moderate risk - monitor closely."
        elif score <= 5:
            risk_level = "High"
            interpretation = f"30-day mortality risk: {mortality_percent}%. High risk - consider intensive care."
        else:
            risk_level = "Very High"
            interpretation = f"30-day mortality risk: {mortality_percent}%. Very high risk - immediate intervention needed."
        
        return {
            'score': score,
            'risk_level': risk_level,
            'serious_outcome_percent': mortality_percent,
            'interpretation': interpretation,
            'details': details
        }
    
    @staticmethod
    def calculate_framingham_risk(age: int, is_male: bool, total_cholesterol: float = None,
                                 hdl_cholesterol: float = None, systolic_bp: float = None,
                                 has_diabetes: bool = False, is_smoker: bool = False) -> Dict:
        """
        Framingham Risk Score: 10-year cardiovascular disease risk
        
        Parameters should be from latest measurements
        """
        details = {}
        
        # Simplified scoring (age is primary factor)
        score = 0
        
        if age < 40:
            score = 0
            risk_level = "Low"
            cvd_risk_10yr = 3
        elif age < 50:
            score = 1
            risk_level = "Low"
            cvd_risk_10yr = 6
        elif age < 60:
            score = 2
            risk_level = "Low-Moderate"
            cvd_risk_10yr = 8
        elif age < 70:
            score = 3
            risk_level = "Moderate"
            cvd_risk_10yr = 10
        else:
            score = 4
            risk_level = "High"
            cvd_risk_10yr = 15
        
        # Additional risk factors
        if is_smoker:
            score += 2
            details['Smoker'] = 2
        
        if has_diabetes:
            score += 1
            details['Diabetes'] = 1
        
        if not is_male:
            details['Female'] = 0
        
        if systolic_bp and systolic_bp > 140:
            score += 1
            details['High BP'] = 1
        
        details['Age'] = age
        
        # Add interpretation
        if risk_level == "Low":
            interpretation = f"10-year CVD risk: {cvd_risk_10yr}%. Low risk - maintain healthy lifestyle."
        elif risk_level == "Low-Moderate":
            interpretation = f"10-year CVD risk: {cvd_risk_10yr}%. Moderate risk - consider lifestyle modifications."
        elif risk_level == "Moderate":
            interpretation = f"10-year CVD risk: {cvd_risk_10yr}%. Moderate-high risk - consider medical intervention."
        else:
            interpretation = f"10-year CVD risk: {cvd_risk_10yr}%. High risk - aggressive risk factor management needed."
        
        return {
            'score': score,
            'risk_level': risk_level,
            '10_year_cvd_risk_percent': cvd_risk_10yr,
            'interpretation': interpretation,
            'details': details
        }
    
    @staticmethod
    def calculate_custom_arrhythmia_risk(age: int, sex: str, height: float, weight: float,
                                         qrs_duration: float, qt_interval: float,
                                         t_interval: float) -> Dict:
        """
        Custom Cardiac Arrhythmia Risk Score based on demographics and ECG parameters
        """
        score = 0
        details = {}
        
        # Age factor
        if age > 70:
            score += 3
            details['Age >70'] = 3
        elif age > 50:
            score += 2
            details['Age 50-70'] = 2
        elif age > 30:
            score += 1
            details['Age 30-50'] = 1
        
        # BMI factor
        bmi = weight / ((height / 100) ** 2) if height > 0 else 0
        if bmi > 30:
            score += 2
            details['Overweight (BMI>30)'] = 2
        elif bmi > 25:
            score += 1
            details['Overweight (BMI>25)'] = 1
        
        # QRS duration (normal: 80-120 ms)
        if qrs_duration > 120:
            score += 2
            details['Prolonged QRS'] = 2
        elif qrs_duration > 100:
            score += 1
            details['Slightly prolonged QRS'] = 1
        
        # QT interval (normal: 350-450 ms)
        if qt_interval > 480:
            score += 2
            details['Prolonged QT'] = 2
        elif qt_interval > 450:
            score += 1
            details['Slightly prolonged QT'] = 1
        
        # Sex factor (female higher risk)
        if sex.lower() in ['female', 'f']:
            score += 1
            details['Female'] = 1
        
        # Risk classification
        if score <= 2:
            risk_level = "Low"
            arrhythmia_risk_percent = 5
            interpretation = f"Arrhythmia risk: {arrhythmia_risk_percent}%. Low risk - routine monitoring."
        elif score <= 4:
            risk_level = "Moderate"
            arrhythmia_risk_percent = 15
            interpretation = f"Arrhythmia risk: {arrhythmia_risk_percent}%. Moderate risk - consider evaluation."
        elif score <= 6:
            risk_level = "High"
            arrhythmia_risk_percent = 35
            interpretation = f"Arrhythmia risk: {arrhythmia_risk_percent}%. High risk - cardiology consultation recommended."
        else:
            risk_level = "Very High"
            arrhythmia_risk_percent = 60
            interpretation = f"Arrhythmia risk: {arrhythmia_risk_percent}%. Very high risk - immediate evaluation needed."
        
        return {
            'score': score,
            'risk_level': risk_level,
            'arrhythmia_risk_percent': arrhythmia_risk_percent,
            'interpretation': interpretation,
            'details': details
        }
    
    @staticmethod
    def calculate_has_bled(age: int, has_hypertension: bool = False, has_abnormal_renal: bool = False,
                           has_abnormal_liver: bool = False, has_stroke_history: bool = False,
                           has_bleeding_history: bool = False, has_labile_inr: bool = False,
                           uses_drugs_alcohol: bool = False) -> Dict:
        """HAS-BLED Score: Estimates bleeding risk in anticoagulated patients."""
        score = 0
        details = {}

        if has_hypertension:
            score += 1
            details['Hypertension'] = 1
        if has_abnormal_renal:
            score += 1
            details['Abnormal renal function'] = 1
        if has_abnormal_liver:
            score += 1
            details['Abnormal liver function'] = 1
        if has_stroke_history:
            score += 1
            details['Stroke history'] = 1
        if has_bleeding_history:
            score += 1
            details['Bleeding history'] = 1
        if has_labile_inr:
            score += 1
            details['Labile INR'] = 1
        if age >= 65:
            score += 1
            details['Age ≥65'] = 1
        if uses_drugs_alcohol:
            score += 1
            details['Drugs/alcohol'] = 1

        if score <= 1:
            risk_level = 'Low'
            interpretation = 'Low bleeding risk. Standard monitoring is appropriate.'
        elif score <= 3:
            risk_level = 'Moderate'
            interpretation = 'Moderate bleeding risk. Monitor anticoagulation closely.'
        else:
            risk_level = 'High'
            interpretation = 'High bleeding risk. Consider specialist review and additional safeguards.'

        return {
            'score': score,
            'risk_level': risk_level,
            'interpretation': interpretation,
            'details': details
        }

    @staticmethod
    def calculate_all_scores(age: int, sex: str, height: float, weight: float,
                            qrs_duration: float, qt_interval: float, t_interval: float) -> Dict:
        """Calculate all risk scores at once"""
        
        return {
            'cha2ds2_vasc': RiskScoring.calculate_cha2ds2_vasc(age, sex),
            'timi': RiskScoring.calculate_timi_risk(age, sex.lower() == 'male'),
            'framingham': RiskScoring.calculate_framingham_risk(age, sex.lower() == 'male'),
            'custom_arrhythmia': RiskScoring.calculate_custom_arrhythmia_risk(
                age, sex, height, weight, qrs_duration, qt_interval, t_interval
            ),
            'has_bled': RiskScoring.calculate_has_bled(age)
        }
