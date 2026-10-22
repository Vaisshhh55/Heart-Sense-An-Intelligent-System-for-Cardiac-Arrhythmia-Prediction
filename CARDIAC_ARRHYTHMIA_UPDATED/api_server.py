"""
REST API Module - Flask-based API for system integration
Enables integration with hospital EHR systems and external applications
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import pickle
import json
from datetime import datetime
import traceback
from typing import Dict, Tuple
import numpy as np
import os
import logging

logger = logging.getLogger('cardiac.api')
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

class CardiacAPI:
    """REST API for Cardiac Prediction System"""
    
    def __init__(self, model_path='ensemble_model.joblib', host='0.0.0.0', port=5000):
        """Initialize Flask API"""
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for cross-origin requests
        
        self.host = host
        self.port = port
        self.model = None
        self.model_path = model_path if os.path.isabs(model_path) else os.path.join(self.base_dir, model_path)
        
        self._load_model()
        self._setup_routes()
    
    def _load_model(self):
        """Load trained ensemble model"""
        try:
            self.model = joblib.load(self.model_path)
            logger.info("Model loaded successfully from %s", self.model_path)
        except Exception as e:
            logger.exception("Error loading model: %s", e)
            self.model = None
    
    def _setup_routes(self):
        """Setup API routes"""
        
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'model_loaded': self.model is not None
            }), 200
        
        @self.app.route('/api/model/info', methods=['GET'])
        def model_info():
            """Get model information"""
            return jsonify({
                'model_type': 'Ensemble Voting Classifier',
                'components': ['KNN', 'RandomForest', 'GradientBoosting', 'SVM'],
                'input_features': 7,
                'output_classes': 13,
                'model_path': self.model_path,
                'timestamp': datetime.now().isoformat()
            }), 200
        
        @self.app.route('/api/predict', methods=['POST'])
        def predict():
            """Make prediction - single sample"""
            try:
                data = request.get_json()
                
                # Validate input
                features = [
                    float(data.get('age', 0)),
                    float(data.get('sex', 0)),
                    float(data.get('height', 0)),
                    float(data.get('weight', 0)),
                    float(data.get('qrs', 0)),
                    float(data.get('qt', 0)),
                    float(data.get('t', 0))
                ]
                
                if self.model is None:
                    return jsonify({'error': 'Model not loaded'}), 500
                
                # Make prediction
                X = np.array([features])
                prediction = self.model.predict(X)[0]
                
                # Get prediction probabilities
                try:
                    probabilities = self.model.predict_proba(X)[0]
                    confidence = float(np.max(probabilities))
                except Exception:
                    logger.debug('Model does not support predict_proba or failed; setting confidence=0')
                    confidence = 0.0
                
                return jsonify({
                    'prediction': int(prediction),
                    'confidence': float(confidence),
                    'timestamp': datetime.now().isoformat(),
                    'input_features': {
                        'age': features[0],
                        'sex': features[1],
                        'height': features[2],
                        'weight': features[3],
                        'qrs': features[4],
                        'qt': features[5],
                        't': features[6]
                    }
                }), 200
            
            except Exception as e:
                logger.exception('Error in /api/predict: %s', e)
                return jsonify({
                    'error': str(e),
                    'trace': traceback.format_exc()
                }), 400
        
        @self.app.route('/api/predict/batch', methods=['POST'])
        def predict_batch():
            """Make predictions - multiple samples"""
            try:
                data = request.get_json()
                samples = data.get('samples', [])
                
                if not samples:
                    return jsonify({'error': 'No samples provided'}), 400
                
                if self.model is None:
                    return jsonify({'error': 'Model not loaded'}), 500
                
                # Prepare data
                X = np.array([
                    [
                        float(s.get('age', 0)),
                        float(s.get('sex', 0)),
                        float(s.get('height', 0)),
                        float(s.get('weight', 0)),
                        float(s.get('qrs', 0)),
                        float(s.get('qt', 0)),
                        float(s.get('t', 0))
                    ]
                    for s in samples
                ])
                
                # Make predictions
                predictions = self.model.predict(X)
                
                # Get probabilities
                try:
                    probabilities = self.model.predict_proba(X)
                    confidences = np.max(probabilities, axis=1)
                except Exception:
                    logger.debug('Batch predict_proba failed or unsupported; using zeros for confidences')
                    confidences = np.zeros(len(predictions))
                
                # Format results
                results = []
                for i, (pred, conf) in enumerate(zip(predictions, confidences)):
                    results.append({
                        'sample_id': i,
                        'prediction': int(pred),
                        'confidence': float(conf)
                    })
                
                return jsonify({
                    'total_samples': len(samples),
                    'predictions': results,
                    'timestamp': datetime.now().isoformat()
                }), 200
            
            except Exception as e:
                logger.exception('Error in /api/predict/batch: %s', e)
                return jsonify({
                    'error': str(e),
                    'trace': traceback.format_exc()
                }), 400
        
        @self.app.route('/api/features/info', methods=['GET'])
        def features_info():
            """Get feature information"""
            return jsonify({
                'features': [
                    {
                        'name': 'age',
                        'type': 'numeric',
                        'unit': 'years',
                        'range': [18, 100]
                    },
                    {
                        'name': 'sex',
                        'type': 'categorical',
                        'values': [0, 1],
                        'meaning': {0: 'Female', 1: 'Male'}
                    },
                    {
                        'name': 'height',
                        'type': 'numeric',
                        'unit': 'cm',
                        'range': [140, 220]
                    },
                    {
                        'name': 'weight',
                        'type': 'numeric',
                        'unit': 'kg',
                        'range': [40, 150]
                    },
                    {
                        'name': 'qrs',
                        'type': 'numeric',
                        'unit': 'ms',
                        'range': [60, 160],
                        'normal_range': '80-120'
                    },
                    {
                        'name': 'qt',
                        'type': 'numeric',
                        'unit': 'ms',
                        'range': [200, 600],
                        'normal_range': '350-450'
                    },
                    {
                        'name': 't',
                        'type': 'numeric',
                        'unit': 'ms',
                        'range': [0, 200]
                    }
                ]
            }), 200
        
        @self.app.route('/api/conditions', methods=['GET'])
        def conditions():
            """Get list of cardiac conditions"""
            condition_codes = {
                1: "Normal",
                2: "Sinus Tachycardia",
                3: "Sinus Bradycardia",
                4: "Atrial Fibrillation",
                5: "Atrial Flutter",
                6: "Atrioventricular Block",
                7: "Nodal Escape Rhythm",
                8: "Junctional Rhythm",
                9: "Left Anterior Fascicular Block",
                10: "Right Bundle Branch Block",
                14: "Ventricular Premature Beats",
                15: "Ventricular Tachycardia",
                16: "Wolff-Parkinson-White Syndrome"
            }
            return jsonify({
                'total_conditions': len(condition_codes),
                'conditions': condition_codes
            }), 200
        
        @self.app.route('/api/status', methods=['GET'])
        def status():
            """Get API status"""
            return jsonify({
                'api_version': '1.0',
                'status': 'operational',
                'model_status': 'loaded' if self.model else 'not_loaded',
                'uptime': datetime.now().isoformat(),
                'endpoints': {
                    'health': '/api/health',
                    'model_info': '/api/model/info',
                    'predict': '/api/predict',
                    'predict_batch': '/api/predict/batch',
                    'features': '/api/features/info',
                    'conditions': '/api/conditions',
                    'status': '/api/status'
                }
            }), 200
        
        @self.app.errorhandler(404)
        def not_found(error):
            """Handle 404 errors"""
            return jsonify({'error': 'Endpoint not found'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            """Handle 500 errors"""
            return jsonify({'error': 'Internal server error'}), 500
    
    def run(self, debug=False):
        """Start the API server"""
        logger.info('%s', '\n' + '=' * 60)
        logger.info('CARDIAC ARRHYTHMIA PREDICTION - REST API')
        logger.info('%s', '=' * 60)
        logger.info('Starting Flask API on %s:%s', self.host, self.port)
        logger.info('Debug mode: %s', debug)
        logger.info('%s', '\nAPI Documentation:')
        logger.info('  Base URL: http://localhost:%s/api', self.port)
        logger.info('  Health Check: GET /api/health')
        logger.info('  Single Prediction: POST /api/predict')
        logger.info('  Batch Prediction: POST /api/predict/batch')
        logger.info('  Model Info: GET /api/model/info')
        logger.info('  Features Info: GET /api/features/info')
        logger.info('  Conditions: GET /api/conditions')
        logger.info('%s', '\nSample Request:')
        logger.info('  curl -X POST http://localhost:%s/api/predict \\', self.port)
        logger.info('    -H "Content-Type: application/json" \\')
        logger.info('    -d ''{"age": 45, "sex": 1, "height": 175, "weight": 70, "qrs": 90, "qt": 400, "t": 80}''')
        logger.info('%s', '=' * 60 + '\n')

        self.app.run(host=self.host, port=self.port, debug=debug)


if __name__ == '__main__':
    # Create and run API
    api = CardiacAPI(model_path='ensemble_model.joblib', port=5000)
    api.run(debug=True)
