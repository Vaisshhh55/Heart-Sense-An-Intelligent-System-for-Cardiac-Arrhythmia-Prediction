from CARDIAC_ARRHYTHMIA_UPDATED.report_generator import PDFReportGenerator
import os

# Ensure output dir
out_dir = os.path.join(os.getcwd(), 'reports')
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

gen = PDFReportGenerator(output_dir=out_dir)

# Normal patient
patient = {
    'name': 'Test Patient',
    'patient_id': 'TP001',
    'age': 45,
    'sex': 'Male',
    'height': 175,
    'weight': 75,
    'bmi': 24.5
}
prediction = {
    'report_id': 'TEST-001',
    'model_version': 'Ensemble Model v1.0',
    'predicted_condition': 'Atrial Fibrillation',
    'condition_code': '14',
    'confidence_score': 0.92,
    'qrs_interval': 100,
    'qt_interval': 400,
    't_interval': 150
}

risk_scores = {
    'cha2ds2_vasc': {'score': 3, 'risk_level': 'Moderate', 'interpretation': 'Moderate risk of stroke; consider anticoagulation.'},
    'timI': {'score': 4, 'risk_level': 'High', 'serious_outcome_percent': 26.2}
}

explanation = {'clinical_interpretation': 'Top features: age, QT interval', 'features': []}

print('Generating normal PDF...')
file1 = gen.generate_prediction_report(patient, prediction, risk_scores, explanation)
print('Generated:', file1)

# Long text patient to validate wrapping
patient2 = patient.copy()
patient2['name'] = 'Very Long Named Patient With Extraordinarily Long Name To Test Wrapping'
prediction2 = prediction.copy()
prediction2['predicted_condition'] = 'Supercalifragilisticexpialidocious Cardiomyopathy With Extended Descriptor'
prediction2['condition_code'] = '999'
prediction2['confidence_score'] = 0.65

risk_scores2 = {
    'cha2ds2_vasc': {
        'score': 5,
        'risk_level': 'Low-Moderate',
        'interpretation': 'This is a very long clinical significance text intended to test automatic wrapping in the PDF generator. '
                          'It should wrap across multiple lines and not overlap adjacent columns. The description contains details about management, percentages, and recommended follow-up intervals. '
                          'Ensure margins and paddings prevent clipping and content flows to the next page if needed.'
    },
    'example_long_score': {
        'score': 12,
        'risk_level': 'Very High',
        'annual_stroke_risk_percent': 12.3456
    }
}

explanation2 = {'clinical_interpretation': 'Long explanation\nwith line breaks and verbose content to validate paragraph wrapping in the explanation section.'}

print('Generating long-text PDF...')
file2 = gen.generate_prediction_report(patient2, prediction2, risk_scores2, explanation2)
print('Generated:', file2)
