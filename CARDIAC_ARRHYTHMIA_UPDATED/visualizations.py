"""
Visualization Module
Creates charts and dashboards for cardiac data
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from typing import Dict, List, Any
import io
from PIL import Image
import base64

class CardiacVisualizations:
    """Create visualizations for cardiac data"""
    
    @staticmethod
    def create_risk_scores_chart(risk_scores: Dict) -> Figure:
        """Create bar chart of risk scores"""
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        scores = {}
        for score_type, data in risk_scores.items():
            if isinstance(data, dict) and 'score' in data:
                scores[score_type.replace('_', ' ').title()] = data['score']
        
        if scores:
            colors = ['#FF6B6B', '#FFA500', '#FFD93D', '#6BCB77']
            ax.bar(scores.keys(), scores.values(), color=colors[:len(scores)])
            ax.set_ylabel('Risk Score', fontsize=12)
            ax.set_title('Cardiac Risk Scores', fontsize=14, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_risk_levels_chart(risk_scores: Dict) -> Figure:
        """Create risk level visualization"""
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        risk_data = {}
        for score_type, data in risk_scores.items():
            if isinstance(data, dict) and 'risk_level' in data:
                risk_data[score_type.replace('_', ' ').title()] = data['risk_level']
        
        if risk_data:
            risk_colors = {
                'Low': '#6BCB77',
                'Low-Moderate': '#FFD93D',
                'Moderate': '#FFA500',
                'Moderate-High': '#FF8C42',
                'High': '#FF6B6B',
                'Very High': '#C41E3A'
            }
            
            colors = [risk_colors.get(level, '#808080') for level in risk_data.values()]
            
            ax.barh(list(risk_data.keys()), [1]*len(risk_data), color=colors)
            ax.set_xlim(0, 1)
            ax.set_xticks([])
            ax.set_title('Risk Level Assessment', fontsize=14, fontweight='bold')
            
            # Add risk level labels
            for i, (key, level) in enumerate(risk_data.items()):
                ax.text(0.5, i, level, ha='center', va='center', fontweight='bold', color='white')
            
            fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_feature_importance_chart(explanation: Dict) -> Figure:
        """Create feature importance bar chart"""
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        features = explanation.get('features', {})
        
        if features:
            # Get top 7 features
            top_features = dict(list(features.items())[:7])
            
            feature_names = list(top_features.keys())
            magnitudes = []
            colors = []
            
            for fname, data in top_features.items():
                if 'shap_value' in data:
                    magnitudes.append(abs(data['shap_value']))
                    colors.append('#FF6B6B' if data['shap_value'] > 0 else '#6BCB77')
                elif 'magnitude' in data:
                    magnitudes.append(data['magnitude'])
                    colors.append('#FFA500')
                else:
                    magnitudes.append(data.get('importance_score', 0))
                    colors.append('#FFD93D')
            
            ax.barh(feature_names, magnitudes, color=colors)
            ax.set_xlabel('Impact on Prediction', fontsize=12)
            ax.set_title('Top Contributing Factors', fontsize=14, fontweight='bold')
            ax.invert_yaxis()
            fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_prediction_distribution_chart(predictions: List[Dict]) -> Figure:
        """Create pie chart of prediction distribution"""
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        if not predictions:
            return fig
        
        # Count conditions
        condition_counts = {}
        for pred in predictions:
            condition = pred.get('predicted_condition', 'Unknown')
            condition_counts[condition] = condition_counts.get(condition, 0) + 1
        
        if condition_counts:
            colors = plt.cm.Set3(np.linspace(0, 1, len(condition_counts)))
            ax.pie(condition_counts.values(), labels=condition_counts.keys(), autopct='%1.1f%%',
                   colors=colors, startangle=90)
            ax.set_title('Prediction Distribution', fontsize=14, fontweight='bold')
            fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_patient_demographics_chart(patients: List[Dict]) -> Figure:
        """Create age distribution chart"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        if not patients:
            return fig
        
        # Age distribution
        ages = [p['age'] for p in patients if 'age' in p]
        if ages:
            ax1.hist(ages, bins=10, color='#6BCB77', edgecolor='black', alpha=0.7)
            ax1.set_xlabel('Age', fontsize=11)
            ax1.set_ylabel('Number of Patients', fontsize=11)
            ax1.set_title('Age Distribution', fontsize=12, fontweight='bold')
            ax1.grid(axis='y', alpha=0.3)
        
        # Sex distribution
        sex_counts = {}
        for p in patients:
            if 'sex' in p:
                sex = p['sex']
                sex_counts[sex] = sex_counts.get(sex, 0) + 1
        
        if sex_counts:
            colors = ['#FF6B6B', '#6BCB77']
            ax2.bar(sex_counts.keys(), sex_counts.values(), color=colors[:len(sex_counts)],
                   edgecolor='black', alpha=0.7)
            ax2.set_ylabel('Count', fontsize=11)
            ax2.set_title('Sex Distribution', fontsize=12, fontweight='bold')
            ax2.grid(axis='y', alpha=0.3)
        
        fig.tight_layout()
        return fig
    
    @staticmethod
    def create_bmi_vs_condition_chart(predictions: List[Dict]) -> Figure:
        """Create scatter plot of BMI vs prediction"""
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        if not predictions:
            return fig
        
        bmis = []
        conditions = []
        colors_map = {}
        color_list = ['#FF6B6B', '#FFA500', '#FFD93D', '#6BCB77', '#45B7D1']
        
        for pred in predictions:
            if 'weight' in pred and 'height' in pred:
                bmi = pred['weight'] / ((pred['height'] / 100) ** 2)
                bmis.append(bmi)
                cond = pred.get('predicted_condition', 'Unknown')
                conditions.append(cond)
                
                if cond not in colors_map:
                    colors_map[cond] = color_list[len(colors_map) % len(color_list)]
        
        if bmis:
            colors = [colors_map[c] for c in conditions]
            ax.scatter(bmis, range(len(bmis)), c=colors, s=100, alpha=0.6, edgecolors='black')
            ax.set_xlabel('BMI', fontsize=12)
            ax.set_ylabel('Patient Index', fontsize=12)
            ax.set_title('BMI Distribution by Patient', fontsize=14, fontweight='bold')
            ax.grid(alpha=0.3)
            fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_prediction_timeline(predictions: List[Dict]) -> Figure:
        """Create timeline of predictions"""
        fig = Figure(figsize=(12, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        if not predictions or len(predictions) < 2:
            return fig
        
        # Use indices as timeline
        indices = list(range(len(predictions)))
        conditions = [p.get('predicted_condition', 'Unknown') for p in predictions]
        condition_codes = [p.get('condition_code', 0) for p in predictions]
        
        color_map = {}
        color_list = plt.cm.tab10(np.linspace(0, 1, 10))
        
        for i, (idx, code) in enumerate(zip(indices, condition_codes)):
            if code not in color_map:
                color_map[code] = color_list[len(color_map) % len(color_list)]
            color = color_map[code]
            ax.scatter(idx, code, s=200, c=[color], edgecolors='black', linewidth=1.5)
        
        ax.plot(indices, condition_codes, 'k--', alpha=0.3)
        ax.set_xlabel('Prediction Number', fontsize=12)
        ax.set_ylabel('Condition Code', fontsize=12)
        ax.set_title('Prediction Timeline', fontsize=14, fontweight='bold')
        ax.grid(alpha=0.3)
        fig.tight_layout()
        
        return fig
    
    @staticmethod
    def create_confidence_distribution(predictions: List[Dict]) -> Figure:
        """Create histogram of prediction confidence"""
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        confidences = [p.get('confidence_score', 0) * 100 for p in predictions if 'confidence_score' in p]
        
        if confidences:
            ax.hist(confidences, bins=10, color='#45B7D1', edgecolor='black', alpha=0.7)
            ax.set_xlabel('Confidence (%)', fontsize=12)
            ax.set_ylabel('Frequency', fontsize=12)
            ax.set_title('Prediction Confidence Distribution', fontsize=14, fontweight='bold')
            ax.axvline(np.mean(confidences), color='red', linestyle='--', linewidth=2, label=f'Mean: {np.mean(confidences):.1f}%')
            ax.legend()
            ax.grid(axis='y', alpha=0.3)
            fig.tight_layout()
        
        return fig


class ChartEmbedder:
    """Embed matplotlib figures in Tkinter"""
    
    @staticmethod
    def embed_in_frame(frame, figure: Figure, width=5, height=4):
        """Embed matplotlib figure in tkinter frame"""
        canvas = FigureCanvasTkAgg(figure, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        return canvas
    
    @staticmethod
    def figure_to_image_bytes(figure: Figure) -> bytes:
        """Convert figure to image bytes"""
        buf = io.BytesIO()
        figure.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        return buf.getvalue()
