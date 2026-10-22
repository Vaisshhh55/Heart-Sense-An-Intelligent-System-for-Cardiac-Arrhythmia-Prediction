"""
PDF Report Generation Module
Creates professional patient reports in PDF format
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import json
from typing import Dict, List
import os

class PDFReportGenerator:
    """Generate professional clinical PDF reports"""
    
    def __init__(self, output_dir=None):
        """Initialize PDF generator.

        If `output_dir` is not provided, use a canonical `reports/` folder located
        at the repository root (one level up from this module). This avoids creating
        multiple `reports/` folders when scripts are run from different CWDs.
        """
        # Determine canonical repo root (parent of this package directory)
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if output_dir:
            # allow absolute or relative path passed by caller
            resolved = os.path.abspath(output_dir)
        else:
            resolved = os.path.join(repo_root, 'reports')

        self.output_dir = resolved
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=18,
            spaceBefore=0,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=26
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2a5caa'),
            spaceAfter=8,
            spaceBefore=16,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=18
        ))
        
        # Normal style
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=13,
            spaceAfter=4,
            spaceBefore=0
        ))

        self.styles.add(ParagraphStyle(
            name='CustomFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        ))
        # Table header and cell styles for wrapped text
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='TableCellLeft',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=TA_LEFT
        ))
        self.styles.add(ParagraphStyle(
            name='TableCellCenter',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            alignment=TA_CENTER
        ))
    
    def generate_prediction_report(self, patient_data: Dict, prediction_data: Dict, 
                                   risk_scores: Dict, explanation: Dict) -> str:
        """Generate comprehensive prediction report"""
        
        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"Prediction_{patient_data['name']}_{timestamp}.pdf")
        
        # Create PDF with A4 layout and consistent margins
        doc = SimpleDocTemplate(filename, pagesize=A4,
                                rightMargin=0.7*inch, leftMargin=0.7*inch,
                                topMargin=0.8*inch, bottomMargin=0.8*inch)
        doc.title = 'Cardiac Arrhythmia Prediction Report'
        doc.author = 'CardioClinic AI'
        story = []
        
        # Title and top metadata
        story.append(Paragraph(
            "CARDIAC ARRHYTHMIA PREDICTION REPORT",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 0.15*inch))

        # Report metadata and logo
        report_id = prediction_data.get('report_id') or f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        prediction_data['report_id'] = report_id
        model_version = prediction_data.get('model_version', 'Ensemble Model v1.0')
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logo_cell = Paragraph('<b>Hospital / Project Logo</b>', self.styles['CustomNormal'])
        logo_path = self._find_logo_path()
        if logo_path:
            try:
                logo_cell = Image(logo_path, width=1.6*inch, height=0.9*inch)
            except Exception:
                logo_cell = Paragraph('<b>Hospital / Project Logo</b>', self.styles['CustomNormal'])

        logo_data = [
            [logo_cell,
             Paragraph(
                 f'<b>Report ID:</b> {report_id}<br/><b>Generated:</b> {generated_at}<br/><b>Model Version:</b> {model_version}',
                 self.styles['CustomNormal']
             )]
        ]
        logo_table = Table(logo_data, colWidths=[2.2*inch, 3.8*inch], hAlign='LEFT')
        logo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#dbe9f8')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica') ,
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ]))
        story.append(logo_table)
        story.append(Spacer(1, 0.18*inch))

        # Report info
        info_data = [
            ["Patient Name:", patient_data.get('name', 'N/A')],
            ["Patient ID:", str(patient_data.get('patient_id', 'N/A'))],
            ["Report Generated:", generated_at],
            ["Model Version:", model_version],
            ["Report ID:", report_id]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 4*inch], hAlign='LEFT')
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fbff')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ]))
        story.append(info_table)
        story.append(Spacer(1, 0.24*inch))
        
        # Patient demographics
        story.append(Paragraph("PATIENT DEMOGRAPHICS", self.styles['CustomHeading']))
        
        demo_data = [
            ["Age:", f"{patient_data.get('age', 'N/A')} years"],
            ["Sex:", patient_data.get('sex', 'N/A')],
            ["Height:", f"{patient_data.get('height', 'N/A')} cm"],
            ["Weight:", f"{patient_data.get('weight', 'N/A')} kg"],
            ["BMI:", f"{patient_data.get('bmi', 0):.1f}" if patient_data.get('bmi') else "N/A"],
        ]
        
        demo_table = Table(demo_data, colWidths=[1.5*inch, 3.5*inch])
        demo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        story.append(demo_table)
        story.append(Spacer(1, 0.3*inch))
        
        # ECG Parameters
        story.append(Paragraph("ECG PARAMETERS", self.styles['CustomHeading']))
        
        ecg_data = [
            ["Parameter", "Value", "Normal Range"],
            ["QRS Interval", f"{prediction_data.get('qrs_interval', 'N/A')} ms", "80-120 ms"],
            ["QT Interval", f"{prediction_data.get('qt_interval', 'N/A')} ms", "350-450 ms"],
            ["T Interval", f"{prediction_data.get('t_interval', 'N/A')} ms", "100-200 ms"],
        ]
        
        ecg_table = Table(ecg_data, colWidths=[1.8*inch, 1.5*inch, 2.2*inch])
        ecg_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5caa')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')])
        ]))
        story.append(ecg_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Prediction Results
        story.append(Paragraph("PREDICTION RESULTS", self.styles['CustomHeading']))
        
        confidence = prediction_data.get('confidence_score', 0) * 100
        if confidence < 50:
            confidence_level = 'Low Confidence'
        elif confidence <= 80:
            confidence_level = 'Moderate Confidence'
        else:
            confidence_level = 'High Confidence'

        pred_result = f"""
        <b>Predicted Condition:</b> {prediction_data.get('predicted_condition', 'Unknown')}<br/>
        <b>Condition Code:</b> {prediction_data.get('condition_code', 'N/A')}<br/>
        <b>Confidence Score:</b> {confidence:.1f}%<br/>
        <b>Confidence Level:</b> {confidence_level}
        """
        story.append(Paragraph(pred_result, self.styles['CustomNormal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Risk Assessment
        story.append(Paragraph("RISK STRATIFICATION ASSESSMENT", self.styles['CustomHeading']))
        
        # Build risk table using Paragraphs so long text wraps and rows grow
        # Determine usable width based on page size and margins
        page_width, _ = A4
        usable_width = page_width - (doc.leftMargin + doc.rightMargin)

        # Recommended column width percentages
        col_percents = [0.22, 0.10, 0.18, 0.50]
        col_widths = [usable_width * p for p in col_percents]

        # Header row using Paragraph for consistent wrapping/centering
        risk_rows = [
            [
                Paragraph('Score Type', self.styles['TableHeader']),
                Paragraph('Score', self.styles['TableHeader']),
                Paragraph('Risk Level', self.styles['TableHeader']),
                Paragraph('Clinical Significance', self.styles['TableHeader'])
            ]
        ]

        for score_type, score_info in risk_scores.items():
            if not isinstance(score_info, dict):
                continue
            # Build significance text defensively
            significance = score_info.get('interpretation', '')
            if not significance:
                # fallback to any percent-like fields
                percent = score_info.get('annual_stroke_risk_percent') or score_info.get('serious_outcome_percent') or score_info.get('10_year_cvd_risk_percent') or score_info.get('arrhythmia_risk_percent')
                try:
                    significance = f"{float(percent):.1f}% risk" if percent is not None else ''
                except Exception:
                    significance = str(percent) if percent is not None else ''

            score_type_par = Paragraph(score_type.replace('_', ' ').title(), self.styles['TableCellLeft'])
            score_par = Paragraph(str(score_info.get('score', 'N/A')), self.styles['TableCellCenter'])
            risk_level_par = Paragraph(str(score_info.get('risk_level', 'N/A')), self.styles['TableCellCenter'])
            significance_par = Paragraph(str(significance), self.styles['TableCellLeft'])

            risk_rows.append([score_type_par, score_par, risk_level_par, significance_par])

        risk_table = Table(risk_rows, colWidths=col_widths, hAlign='LEFT', repeatRows=1)
        risk_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#c41e3a')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fff5f5')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ALIGN', (1, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'LEFT')
        ]))
        story.append(risk_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Explanation
        story.append(Paragraph("PREDICTION EXPLANATION", self.styles['CustomHeading']))
        
        if isinstance(explanation, dict) and 'shap' in explanation and explanation.get('natural_language') is None:
            explanation = explanation.get('shap', explanation)

        # Clinical interpretation
        clinical_interpretation = explanation.get('clinical_interpretation') or explanation.get('natural_language') or explanation.get('explanation_text') or ''
        if clinical_interpretation:
            story.append(Paragraph('<b>Clinical Interpretation:</b>', self.styles['CustomNormal']))
            story.append(Paragraph(clinical_interpretation.replace('\n', '<br/>'), self.styles['CustomNormal']))
            story.append(Spacer(1, 0.1*inch))

        # Confidence explanation
        confidence_score = float(prediction_data.get('confidence_score', 0) or 0)
        if confidence_score >= 0:
            confidence_level = 'Low' if confidence_score < 0.50 else 'Moderate' if confidence_score <= 0.80 else 'High'
            confidence_explanation = (
                f"The prediction confidence is {confidence_score * 100:.1f}% ({confidence_level} confidence). "
                f"This means the model {'is less certain and clinical review is recommended' if confidence_level == 'Low' else 'has moderate certainty and should be interpreted with care' if confidence_level == 'Moderate' else 'has strong certainty based on the available features'}."
            )
            story.append(Paragraph('<b>Confidence Explanation:</b>', self.styles['CustomNormal']))
            story.append(Paragraph(confidence_explanation, self.styles['CustomNormal']))
            story.append(Spacer(1, 0.1*inch))

        # Feature importance table
        features = explanation.get('features', [])
        feature_items = []
        if isinstance(features, dict):
            for name, data in features.items():
                if not name or not isinstance(data, dict):
                    continue
                impact = data.get('shap_value', data.get('permutation_importance', data.get('magnitude', None)))
                if impact is None:
                    continue
                feature_items.append({
                    'name': str(name),
                    'value': str(data.get('feature_value', '')),
                    'impact': float(impact)
                })
        elif isinstance(features, list):
            for item in features:
                if not isinstance(item, dict):
                    continue
                name = item.get('name') or item.get('feature') or ''
                if not name:
                    continue
                impact = item.get('shap_value', item.get('permutation_importance', item.get('magnitude', None)))
                if impact is None:
                    continue
                feature_items.append({
                    'name': str(name),
                    'value': str(item.get('feature_value', item.get('value', ''))),
                    'impact': float(impact)
                })

        feature_items = [f for f in feature_items if f['name']]
        feature_items.sort(key=lambda x: abs(x['impact']), reverse=True)

        positives = [f for f in feature_items if f['impact'] > 0]
        negatives = [f for f in feature_items if f['impact'] < 0]

        if positives:
            story.append(Paragraph('<b>Positive Contributors:</b>', self.styles['CustomNormal']))
            for f in positives[:5]:
                story.append(Paragraph(f"• {f['name']} ({f['impact']:+.3f})", self.styles['CustomNormal']))
            story.append(Spacer(1, 0.08*inch))

        if negatives:
            story.append(Paragraph('<b>Negative Contributors:</b>', self.styles['CustomNormal']))
            for f in negatives[:5]:
                story.append(Paragraph(f"• {f['name']} ({f['impact']:+.3f})", self.styles['CustomNormal']))
            story.append(Spacer(1, 0.08*inch))

        if feature_items:
            rows = [['Feature', 'Value', 'SHAP Impact']]
            for f in feature_items:
                rows.append([f['name'], f['value'], f"{f['impact']:+.3f}"])
            tbl = Table(rows, colWidths=[2.6*inch, 1.1*inch, 1.2*inch], hAlign='LEFT')
            tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f8fb')]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))
            story.append(KeepTogether(tbl))
            story.append(Spacer(1, 0.2*inch))

        story.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        story.append(Paragraph("CLINICAL RECOMMENDATIONS", self.styles['CustomHeading']))
        
        recommendations = self._get_recommendations(prediction_data, risk_scores)
        for rec in recommendations:
            if isinstance(rec, str) and rec.startswith('<b>'):
                story.append(Paragraph(rec, self.styles['CustomNormal']))
            else:
                story.append(Paragraph(f"• {rec}", self.styles['CustomNormal']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Disclaimer
        story.append(Paragraph(
            "<b>IMPORTANT DISCLAIMER:</b><br/>" +
            "This report is generated by an artificial intelligence system and should NOT be used " +
            "as a substitute for professional medical advice, diagnosis, or treatment. " +
            "Always consult with a qualified cardiologist or healthcare professional for final diagnosis and treatment decisions.",
            ParagraphStyle(
                name='Disclaimer',
                parent=self.styles['Normal'],
                fontSize=9,
                leading=12,
                textColor=colors.red,
                alignment=TA_LEFT,
                borderPadding=8,
                borderColor=colors.red,
                borderWidth=1,
                spaceBefore=12,
                spaceAfter=8
            )
        ))

        # Build PDF with page decorations
        doc.build(story, onFirstPage=self._add_page_decorations, onLaterPages=self._add_page_decorations)
        return filename

    def _add_page_decorations(self, canvas, doc):
        """Add header/footer layout elements to every page."""
        canvas.saveState()
        width, height = A4

        # Footer line
        canvas.setStrokeColor(colors.HexColor('#d3d3d3'))
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, doc.bottomMargin + 18, width - doc.rightMargin, doc.bottomMargin + 18)

        # Footer text
        report_id = getattr(doc, 'report_id', '')
        model_version = getattr(doc, 'model_version', '')
        generated_at = getattr(doc, 'generated_at', datetime.now().strftime('%Y-%m-%d'))
        footer_text = f"Report ID: {report_id} | Date: {generated_at.split(' ')[0]} | Model: {model_version}"
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(width / 2.0, doc.bottomMargin + 8, footer_text)

        # Page number
        page_number_text = f"Page {canvas.getPageNumber()}"
        canvas.drawRightString(width - doc.rightMargin, doc.bottomMargin + 8, page_number_text)
        canvas.restoreState()

    def _get_recommendations(self, prediction_data: Dict, risk_scores: Dict) -> list:
        """Generate recommendation text based on condition, risk, confidence, and ECG parameters."""
        recommendations = []
        condition = str(prediction_data.get('predicted_condition', '')).lower()
        confidence = float(prediction_data.get('confidence_score', 0) or 0)
        qrs = float(prediction_data.get('qrs_interval', 0) or 0)
        qt = float(prediction_data.get('qt_interval', 0) or 0)
        t_interval = float(prediction_data.get('t_interval', 0) or 0)

        # Immediate actions
        high_risk = any(
            isinstance(v, dict) and v.get('risk_level') in ('High', 'Very High')
            for v in risk_scores.values()
        )
        moderate_risk = any(
            isinstance(v, dict) and v.get('risk_level') in ('Moderate', 'Moderate-High', 'Low-Moderate')
            for v in risk_scores.values()
        )

        if high_risk:
            recommendations.append('<b>Immediate Actions:</b> Prioritize specialist review and close monitoring because the risk profile is elevated.')
        elif confidence < 0.50:
            recommendations.append('<b>Immediate Actions:</b> Clinical correlation is important; repeat ECG and verify data before definitive management.')
        elif confidence < 0.80 and moderate_risk:
            recommendations.append('<b>Immediate Actions:</b> Review the ECG and history, but avoid escalating treatment solely on low-to-moderate confidence when the risk is not high.')
        elif confidence < 0.80:
            recommendations.append('<b>Immediate Actions:</b> Review the ECG and consider cardiology input if the clinical picture remains concerning.')
        else:
            recommendations.append('<b>Immediate Actions:</b> Proceed with appropriate care pathways guided by the predicted condition and risk profile.')

        if 'atrial' in condition or 'fibrillation' in condition or 'flutter' in condition:
            recommendations.append('Initiate rhythm monitoring and assess anticoagulation eligibility immediately.')
        if 'ischemic' in condition or 'infarction' in condition:
            recommendations.append('Activate acute coronary syndrome pathway and obtain cardiac biomarkers without delay.')
        if 'tachycardia' in condition:
            recommendations.append('Assess hemodynamic stability and consider rate control in the acute phase.')
        if 'block' in condition:
            recommendations.append('Review conduction abnormality severity and arrange urgent electrophysiology review if symptomatic.')

        # Recommended investigations
        investigations = []
        if 'atrial' in condition or 'fibrillation' in condition or 'flutter' in condition:
            investigations.append('12-lead ECG, Holter monitoring, and echocardiography.')
        if 'ischemic' in condition or 'infarction' in condition:
            investigations.append('Cardiac enzymes, serial ECGs, and coronary imaging.')
        if qrs > 120:
            investigations.append('Conduction study or cardiac imaging to evaluate bundle branch block.')
        if qt > 450:
            investigations.append('Electrolyte panel and QT-prolonging medication review.')
        if not investigations:
            investigations.append('Standard ECG review and targeted lab testing as clinically indicated.')
        recommendations.append('<b>Recommended Investigations:</b> ' + ' '.join(investigations))

        # Lifestyle advice
        lifestyle = []
        lifestyle.append('Encourage heart-healthy lifestyle changes including low-sodium diet, regular activity, and optimized blood pressure control.')
        if 'atrial' in condition or 'fibrillation' in condition or 'flutter' in condition:
            lifestyle.append('Avoid stimulants, caffeine excess, and decongestant medications that may trigger arrhythmia.')
        if 'ischemic' in condition or 'infarction' in condition:
            lifestyle.append('Promote smoking cessation, dietary modification, and weight optimization.')
        recommendations.append('<b>Lifestyle Advice:</b> ' + ' '.join(lifestyle))

        # Follow-up interval
        follow_up = 'Follow-up interval should be tailored to clinical risk and acuity.'
        high_risk = any(
            isinstance(v, dict) and v.get('risk_level') in ('High', 'Very High')
            for v in risk_scores.values()
        )
        if high_risk or confidence >= 0.80:
            follow_up = 'Arrange follow-up within 1-2 weeks for high-risk findings and treatment review.'
        elif confidence >= 0.50:
            follow_up = 'Schedule follow-up within 4-6 weeks for moderate risk and reassessment.'
        else:
            follow_up = 'Recommend follow-up within 8-12 weeks with repeat ECG if symptoms persist.'
        recommendations.append(f'<b>Follow-up Interval:</b> {follow_up}')

        # Emergency warnings
        if 'ischemic' in condition or 'infarction' in condition or qrs > 140 or qt > 500:
            recommendations.append('<b>Emergency Warning:</b> If chest pain, syncope, palpitations, or shortness of breath occur, seek emergency care immediately.')
        elif 'atrial' in condition or 'fibrillation' in condition or 'flutter' in condition:
            recommendations.append('<b>Emergency Warning:</b> If symptoms worsen or hemodynamic instability develops, refer to emergency services promptly.')

        # Risk-based summary
        if high_risk:
            recommendations.append('High-risk features detected; consider specialist cardiology review without delay.')
        else:
            recommendations.append('Low to moderate risk profile; standard clinical monitoring is appropriate.')

        # remove duplicates and empty items
        cleaned = []
        for item in recommendations:
            if not item or not str(item).strip():
                continue
            if item in cleaned:
                continue
            cleaned.append(item)

        return cleaned
    
    def generate_patient_summary_report(self, patient_data: Dict, prediction_history: List[Dict]) -> str:
        """Generate patient summary report with prediction history"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"PatientSummary_{patient_data['name']}_{timestamp}.pdf")
        
        doc = SimpleDocTemplate(filename, pagesize=A4,
                                rightMargin=0.7*inch, leftMargin=0.7*inch,
                                topMargin=0.8*inch, bottomMargin=0.8*inch)
        doc.title = 'Cardiac Arrhythmia Patient Summary Report'
        doc.author = 'CardioClinic AI'
        story = []
        
        # Title
        story.append(Paragraph(
            "PATIENT SUMMARY REPORT",
            self.styles['CustomTitle']
        ))
        story.append(Spacer(1, 0.2*inch))
        
        # Patient Info
        story.append(Paragraph(
            f"Patient: {patient_data['name']} | Age: {patient_data['age']} | Sex: {patient_data['sex']}",
            self.styles['CustomNormal']
        ))
        story.append(Spacer(1, 0.3*inch))
        
        # Prediction History Table
        story.append(Paragraph("PREDICTION HISTORY", self.styles['CustomHeading']))
        
        hist_data = [["Date", "Condition", "Confidence", "Status"]]
        for pred in prediction_history[-10:]:  # Last 10 predictions
            hist_data.append([
                pred.get('created_at', 'N/A')[:10],
                pred.get('predicted_condition', 'N/A'),
                f"{pred.get('confidence_score', 0)*100:.1f}%",
                "Recorded"
            ])
        
        hist_table = Table(hist_data, colWidths=[1.5*inch, 2.5*inch, 1.2*inch, 1.3*inch], hAlign='LEFT')
        hist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2a5caa')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f8fb')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
        ]))
        story.append(hist_table)
        
        doc.report_id = report_id
        doc.model_version = model_version
        doc.generated_at = generated_at

        # Build PDF with page decorations and managed page breaks
        doc.build(story, onFirstPage=self._add_page_decorations, onLaterPages=self._add_page_decorations)
        return filename

    def _find_logo_path(self) -> str:
        """Look for a logo file in the project folder if available."""
        candidates = ['logo.png', 'logo.jpg', 'logo.jpeg', 'hospital_logo.png', 'hospital_logo.jpg']
        for candidate in candidates:
            candidate_path = os.path.join(self.output_dir, '..', candidate)
            if os.path.exists(candidate_path):
                return candidate_path
        # fallback to workspace root as well
        for candidate in candidates:
            if os.path.exists(candidate):
                return candidate
        return ''
