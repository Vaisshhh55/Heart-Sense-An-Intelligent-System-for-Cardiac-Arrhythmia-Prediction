"""

Enhanced Training with Ensemble Models
Trains multiple algorithms and creates an ensemble for better accuracy
"""

import pandas as pd
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import pickle
import joblib
import logging

logger = logging.getLogger('cardiac.trainer')
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

class EnsembleModel:
    def __init__(self):
        self.models = {}
        self.scaler = None
        self.feature_names = ['age', 'sex_id', 'height', 'weight', 'qrs_duration', 'p_r_interval', 't_interval']
    
    def train(self, X_train, X_test, y_train, y_test):
        """Train multiple models"""
        logger.info("Training Ensemble Models...")
        logger.info("%s", "=" * 60)
        
        # 1. Weighted KNN
        logger.info("\n1. Training Weighted KNN (k=13)...")
        knn = KNeighborsClassifier(n_neighbors=13, weights='distance')
        knn.fit(X_train, y_train)
        y_pred_knn = knn.predict(X_test)
        knn_acc = accuracy_score(y_pred_knn, y_test)
        self.models['knn'] = {
            'model': knn,
            'accuracy': knn_acc,
            'precision': precision_score(y_pred_knn, y_test, average='weighted', zero_division=0),
            'recall': recall_score(y_pred_knn, y_test, average='weighted', zero_division=0),
            'f1': f1_score(y_pred_knn, y_test, average='weighted', zero_division=0)
        }
        logger.info("   Accuracy: %.4f", knn_acc)
        
        # 2. Random Forest
        logger.info("\n2. Training Random Forest (n_estimators=200)...")
        rf = RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train)
        y_pred_rf = rf.predict(X_test)
        rf_acc = accuracy_score(y_pred_rf, y_test)
        self.models['random_forest'] = {
            'model': rf,
            'accuracy': rf_acc,
            'precision': precision_score(y_pred_rf, y_test, average='weighted', zero_division=0),
            'recall': recall_score(y_pred_rf, y_test, average='weighted', zero_division=0),
            'f1': f1_score(y_pred_rf, y_test, average='weighted', zero_division=0)
        }
        logger.info("   Accuracy: %.4f", rf_acc)
        
        # 3. Gradient Boosting
        logger.info("\n3. Training Gradient Boosting Classifier...")
        gb = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
        gb.fit(X_train, y_train)
        y_pred_gb = gb.predict(X_test)
        gb_acc = accuracy_score(y_pred_gb, y_test)
        self.models['gradient_boosting'] = {
            'model': gb,
            'accuracy': gb_acc,
            'precision': precision_score(y_pred_gb, y_test, average='weighted', zero_division=0),
            'recall': recall_score(y_pred_gb, y_test, average='weighted', zero_division=0),
            'f1': f1_score(y_pred_gb, y_test, average='weighted', zero_division=0)
        }
        logger.info("   Accuracy: %.4f", gb_acc)
        
        # 4. SVM with RBF kernel
        logger.info("\n4. Training Support Vector Machine (SVM)...")
        svm = SVC(kernel='rbf', C=1.0, probability=True, random_state=42)
        svm.fit(X_train, y_train)
        y_pred_svm = svm.predict(X_test)
        svm_acc = accuracy_score(y_pred_svm, y_test)
        self.models['svm'] = {
            'model': svm,
            'accuracy': svm_acc,
            'precision': precision_score(y_pred_svm, y_test, average='weighted', zero_division=0),
            'recall': recall_score(y_pred_svm, y_test, average='weighted', zero_division=0),
            'f1': f1_score(y_pred_svm, y_test, average='weighted', zero_division=0)
        }
        logger.info("   Accuracy: %.4f", svm_acc)
        
        # Voting Ensemble
        logger.info("\n5. Creating Voting Ensemble...")
        from sklearn.ensemble import VotingClassifier
        
        voting_clf = VotingClassifier(
            estimators=[
                ('knn', knn),
                ('rf', rf),
                ('gb', gb),
                ('svm', svm)
            ],
            voting='soft'
        )
        voting_clf.fit(X_train, y_train)
        y_pred_voting = voting_clf.predict(X_test)
        voting_acc = accuracy_score(y_pred_voting, y_test)
        self.models['voting'] = {
            'model': voting_clf,
            'accuracy': voting_acc,
            'precision': precision_score(y_pred_voting, y_test, average='weighted', zero_division=0),
            'recall': recall_score(y_pred_voting, y_test, average='weighted', zero_division=0),
            'f1': f1_score(y_pred_voting, y_test, average='weighted', zero_division=0)
        }
        logger.info("   Accuracy: %.4f", voting_acc)
        
        logger.info("\n%s", "=" * 60)
        logger.info("ENSEMBLE MODEL SUMMARY")
        logger.info("%s", "=" * 60)
        for name, metrics in self.models.items():
            logger.info("%s:", name.upper())
            logger.info("  Accuracy:  %.4f", metrics['accuracy'])
            logger.info("  Precision: %.4f", metrics['precision'])
            logger.info("  Recall:    %.4f", metrics['recall'])
            logger.info("  F1-Score:  %.4f", metrics['f1'])
        
        logger.info("\n%s", "=" * 60)
        logger.info("Best Model: %s", max(self.models.items(), key=lambda x: x[1]['accuracy'])[0].upper())
        logger.info("%s", "=" * 60)
    
    def predict(self, data):
        """Predict using voting ensemble"""
        voting_model = self.models['voting']['model']
        return voting_model.predict(data)
    
    def predict_proba(self, data):
        """Get prediction probabilities"""
        voting_model = self.models['voting']['model']
        try:
            # Try to get probabilities from voting classifier
            return voting_model.predict_proba(data)
        except Exception as e:
            logger.debug('Voting predict_proba failed: %s', e)
            # Fallback: get probabilities from RF which supports it
            try:
                rf_model = self.models['random_forest']['model']
                return rf_model.predict_proba(data)
            except Exception as e2:
                logger.debug('Random forest predict_proba failed: %s', e2)
                # Last resort: create dummy probabilities
                pred = voting_model.predict(data)
                n_classes = len(np.unique(pred))
                proba = np.zeros((data.shape[0], n_classes))
                for i, p in enumerate(pred):
                    proba[i, int(p)] = 0.95
                return proba
    
    def get_all_predictions(self, data):
        """Get predictions from all models"""
        results = {}
        for name, model_dict in self.models.items():
            model = model_dict['model']
            try:
                pred = model.predict(data)[0]
                results[name] = int(pred)
            except Exception as e:
                logger.debug('Model %s prediction failed: %s', name, e)
                results[name] = None
        return results
    
    def save(self, filepath='ensemble_model.joblib'):
        """Save ensemble to file"""
        joblib.dump(self, filepath)
        logger.info('Ensemble model saved to %s', filepath)
    
    @staticmethod
    def load(filepath='ensemble_model.joblib'):
        """Load ensemble from file"""
        return joblib.load(filepath)


# Training script
if __name__ == "__main__":
    # Load data
    logger.info('Loading data...')
    df = pd.read_csv('test.csv')
    x = df.iloc[:, :7]
    y = df.iloc[:, -1]
    
    # Split data
    logger.info('Splitting data (80% train, 20% test)...')
    X_train, X_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=100
    )
    
    # Create and train ensemble
    ensemble = EnsembleModel()
    ensemble.train(X_train, X_test, y_train, y_test)
    
    # Save ensemble
    ensemble.save('ensemble_model.joblib')
    
    # Also save individual models for backward compatibility
    logger.info('\nSaving individual models...')
    with open('knn_model.pkl', 'wb') as f:
        pickle.dump(ensemble.models['knn']['model'], f)
    logger.info('KNN model saved as knn_model.pkl')
    
    with open('ensemble_voting.pkl', 'wb') as f:
        pickle.dump(ensemble.models['voting']['model'], f)
    logger.info('Voting ensemble saved as ensemble_voting.pkl')
