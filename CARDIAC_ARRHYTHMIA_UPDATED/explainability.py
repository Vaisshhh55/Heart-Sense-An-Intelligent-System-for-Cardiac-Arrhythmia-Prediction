"""
Explainability Module
Provides interpretable explanations for model predictions using SHAP
"""

import numpy as np
import shap
from typing import Dict, List, Any
import warnings
warnings.filterwarnings('ignore')
import logging

logger = logging.getLogger('cardiac.explain')
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

class ModelExplainer:
    """Explain model predictions with SHAP values"""
    
    def __init__(self, model, X_train: np.ndarray, feature_names: List[str]):
        """
        Initialize explainer
        
        Args:
            model: Trained model
            X_train: Training data for background
            feature_names: List of feature names
        """
        self.model = model
        self.X_train = X_train
        self.feature_names = feature_names
        self.explainer = None
        self._create_explainer()
    
    def _create_explainer(self):
        """Create SHAP explainer"""
        try:
            background = np.atleast_2d(self.X_train.astype(float) if hasattr(self.X_train, 'astype') else self.X_train)
            if background.size == 0 or background.shape[1] != len(self.feature_names):
                background = np.zeros((max(1, background.shape[0]), len(self.feature_names)), dtype=float)
            self.explainer = shap.KernelExplainer(
                self.model.predict_proba if hasattr(self.model, 'predict_proba') else self.model.predict,
                shap.sample(background, min(100, len(background)))
            )
        except Exception as e:
            logger.warning('SHAP explainer initialization failed: %s', e)
            self.explainer = None

    def explain_prediction(self, instance: np.ndarray, class_names: Dict[int, str] = None) -> Dict:
        """
        Explain a single prediction
        
        Args:
            instance: Single data point to explain
            class_names: Mapping of class indices to names
        
        Returns:
            Dictionary with explanation
        """
        instance = np.atleast_2d(np.asarray(instance, dtype=float))
        explanation = {
            'features': {},
            'prediction': None,
            'confidence': None
        }
        
        if self.explainer is None or instance.shape[1] != len(self.feature_names):
            logger.debug('Explainer missing or instance shape mismatch; using permutation fallback')
            return self._explain_with_permutation(instance, class_names)
        
        try:
            pred = self.model.predict(instance)[0]
            explanation['prediction'] = int(pred)
            
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(instance)[0]
                explanation['confidence'] = float(np.max(proba))
            
            shap_values = self.explainer.shap_values(instance)
            shap_values = getattr(shap_values, 'values', shap_values)
            shap_values = np.array(shap_values)
            
            if shap_values.ndim == 3:
                # SHAP returns shape (instances, features, classes) for multi-class models
                if shap_values.shape[0] == 1 and shap_values.shape[1] == len(self.feature_names):
                    class_index = int(pred) if int(pred) < shap_values.shape[2] else 0
                    shap_vals = shap_values[0, :, class_index]
                else:
                    shap_vals = shap_values.reshape(-1, len(self.feature_names))[0]
            elif shap_values.ndim == 2 and shap_values.shape[0] == 1:
                shap_vals = shap_values[0]
            elif shap_values.ndim == 1:
                shap_vals = shap_values
            else:
                shap_vals = np.asarray(shap_values).reshape(-1, len(self.feature_names))[0]
            
            if shap_vals.shape[0] != len(self.feature_names):
                raise ValueError('SHAP output feature count mismatch')
            
            feature_importance = {}
            for i, (fname, val, feature_val) in enumerate(zip(
                self.feature_names, shap_vals, instance[0]
            )):
                feature_importance[fname] = {
                    'shap_value': float(val),
                    'feature_value': float(feature_val),
                    'contribution': 'Increases' if val > 0 else 'Decreases',
                    'magnitude': abs(float(val))
                }
            
            sorted_features = sorted(
                feature_importance.items(),
                key=lambda x: x[1]['magnitude'],
                reverse=True
            )
            
            explanation['features'] = dict(sorted_features)
            explanation['model_type'] = type(self.model).__name__
            explanation['method'] = 'shap'
            # Build a natural-language summary for UI consumption
            try:
                explanation['natural_language'] = self.get_three_point_summary(explanation)
            except Exception:
                explanation['natural_language'] = self.get_feature_importance_text(explanation)
        except Exception as e:
            logger.warning('SHAP calculation failed: %s', e)
            explanation = self._explain_with_permutation(instance, class_names)

        return explanation
    
    def _explain_with_permutation(self, instance: np.ndarray, class_names: Dict = None) -> Dict:
        """
        Fallback explanation using permutation importance
        """
        explanation = {
            'features': {},
            'prediction': None,
            'confidence': None,
            'method': 'Permutation Importance (Fallback)'
        }
        
        # Get prediction
        pred = self.model.predict(instance.reshape(1, -1))[0]
        explanation['prediction'] = int(pred)
        
        # Get confidence
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(instance.reshape(1, -1))[0]
            explanation['confidence'] = float(np.max(proba))
        
        # Simple permutation importance
        baseline_pred = self.model.predict(instance.reshape(1, -1))
        
        feature_importance = {}
        for i, fname in enumerate(self.feature_names):
            perturbed = instance.copy()
            perturbed[0, i] = np.mean(self.X_train[:, i])  # Replace with mean
            
            perturbed_pred = self.model.predict(perturbed.reshape(1, -1))
            importance = 1 if perturbed_pred[0] != baseline_pred[0] else 0
            
            feature_importance[fname] = {
                'permutation_importance': float(importance),
                'feature_value': float(instance[0, i]),
                'contribution': 'Important' if importance > 0.5 else 'Less Important',
                'magnitude': float(importance)
            }
        
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1]['magnitude'],
            reverse=True
        )
        
        explanation['features'] = dict(sorted_features)
        explanation['model_type'] = type(self.model).__name__
        # Add a concise 3-point natural-language summary
        try:
            explanation['natural_language'] = self.get_three_point_summary(explanation)
        except Exception:
            try:
                explanation['natural_language'] = self.get_feature_importance_text(explanation)
            except Exception:
                explanation['natural_language'] = 'A fallback explanation based on permutation importance is provided.'
        
        return explanation
    
    def get_feature_importance_text(self, explanation: Dict) -> str:
        """Generate human-readable explanation text"""
        if not explanation['features']:
            return "Unable to generate explanation."
        
        text = f"Prediction: {explanation['prediction']}\n"
        if explanation['confidence']:
            text += f"Confidence: {explanation['confidence']*100:.1f}%\n"
        
        text += "\nTop Contributing Factors:\n"
        for i, (fname, data) in enumerate(list(explanation['features'].items())[:5], 1):
            if 'shap_value' in data:
                text += f"{i}. {fname}: {data['contribution']} risk "
                text += f"(Impact: {abs(data['shap_value']):.3f})\n"
            else:
                text += f"{i}. {fname}: {data['contribution']} "
                text += f"(Value: {data['feature_value']:.2f})\n"
        
        return text

    def get_three_point_summary(self, explanation: Dict) -> str:
        """Return a concise 3-point clinical-style summary for UI and reports.

        Points:
        1) Primary drivers increasing probability
        2) Main factors decreasing probability
        3) One-line clinical action / confidence note
        """
        feats = explanation.get('features', {})
        # normalize to list of (name, data)
        items = []
        if isinstance(feats, dict):
            items = list(feats.items())
        else:
            for f in feats:
                if isinstance(f, dict):
                    name = f.get('name') or f.get('feature')
                    items.append((name, f))

        # sort by magnitude
        items_sorted = sorted(items, key=lambda x: abs(x[1].get('shap_value', x[1].get('permutation_importance', 0) or 0)), reverse=True)

        positives = [ (n,d) for n,d in items_sorted if float(d.get('shap_value', d.get('permutation_importance', 0))) > 0 ]
        negatives = [ (n,d) for n,d in items_sorted if float(d.get('shap_value', d.get('permutation_importance', 0))) <= 0 ]

        def fmt_list(lst, maxn=2):
            out = []
            for name, data in lst[:maxn]:
                val = data.get('feature_value', '')
                sv = data.get('shap_value', data.get('permutation_importance', 0))
                out.append(f"{name} ({val}) [{sv:+.3f}]")
            return ', '.join(out) if out else 'none identified'

        top_pos = fmt_list(positives, 2)
        top_neg = fmt_list(negatives, 2)

        confidence = explanation.get('confidence')
        conf_text = f"Confidence: {confidence*100:.1f}%" if confidence is not None else "Confidence: n/a"

        # clinical action recommendation (simple)
        action = 'Recommend clinical correlation with ECG and history.'
        if confidence is not None and confidence >= 0.85:
            action = 'High model confidence; consider expedited cardiology review if clinically warranted.'
        elif confidence is not None and confidence < 0.6:
            action = 'Low model confidence; prioritize confirmatory testing and expert review.'

        summary = (
            f"1) Primary drivers increasing predicted probability: {top_pos}\n"
            f"2) Main factors decreasing predicted probability: {top_neg}\n"
            f"3) {conf_text} {action}"
        )
        return summary


class SimpleFeatureImportance:
    """Simple feature importance without SHAP (faster, no dependencies)"""
    
    def __init__(self, model, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
    
    def get_importance(self, instance: np.ndarray) -> Dict:
        """Get feature importance for a prediction"""
        
        importance_dict = {}
        
        # Get baseline prediction
        baseline = self.model.predict(instance.reshape(1, -1))[0]
        baseline_proba = None
        if hasattr(self.model, 'predict_proba'):
            baseline_proba = np.max(self.model.predict_proba(instance.reshape(1, -1))[0])
        
        # Calculate importance by feature ablation
        for i, fname in enumerate(self.feature_names):
            # Create perturbed sample
            perturbed = instance.copy()
            perturbed[0, i] = 0  # Remove feature by setting to 0
            
            # Check if prediction changes
            new_pred = self.model.predict(perturbed.reshape(1, -1))[0]
            change = 1 if new_pred != baseline else 0
            
            importance_dict[fname] = {
                'feature_value': float(instance[0, i]),
                'importance_score': float(change),
                'affects_prediction': change > 0.5
            }
        
        return {
            'features': importance_dict,
            'prediction': int(baseline),
            'confidence': float(baseline_proba) if baseline_proba else None
        }
    
    def get_feature_importance(self, instance: np.ndarray) -> List[float]:
        """Get feature importance scores as a list (for UI compatibility)"""
        result = self.get_importance(instance)
        # Return importance scores in the same order as feature_names
        return [result['features'][fname]['importance_score'] for fname in self.feature_names]
