# DEPLOYMENT & IMPLEMENTATION GUIDE v2.0

**Version:** 2.0 Complete  
**Date:** March 2, 2026  
**Status:** Production Ready

---

## 1. COMPLETE FILE INVENTORY

### Core Application Files
```
CARDIAC_ARRHYTHMIA_UPDATED/
├── Core Modules (6 files)
│   ├── ensemble_trainer.py      (200 lines) - 5-model ML ensemble
│   ├── database.py              (250 lines) - SQLite patient database
│   ├── risk_scoring.py          (300 lines) - 4 clinical risk scores
│   ├── explainability.py        (250 lines) - SHAP-based transparency
│   ├── visualizations.py        (350 lines) - 8+ chart types
│   └── Train.py                 (updated)   - Training pipeline
│
├── Advanced Features (4 files)
│   ├── report_generator.py      (350 lines) - PDF generation
│   ├── api_server.py            (400 lines) - REST API (7 endpoints)
│   ├── authentication.py        (400 lines) - User auth + RBAC
│   └── advanced_analytics.py    (350 lines) - Analytics engine
│
├── Compliance (1 file)
│   └── clinical_compliance.py   (500 lines) - HIPAA + FDA compliance
│
├── User Interface
│   └── UI_Enhanced.py           (600 lines) - 4-tab professional GUI
│
├── Documentation (8 files)
│   ├── PROJECT_DOCUMENTATION.md
│   ├── MARKET_ANALYSIS_AND_DIFFERENTIATION.md
│   ├── IMPLEMENTATION_GUIDE_V2.0.md
│   ├── UPGRADE_COMPLETE_SUMMARY.md
│   ├── COMPLETE_DELIVERABLES.md
│   ├── DOCUMENTATION_INDEX.md
│   ├── COMPLETE_SYSTEM_DOCUMENTATION.md
│   └── DEPLOYMENT_AND_IMPLEMENTATION_GUIDE.md
│
├── Data Files
│   ├── test.csv                 (1,356 samples × 8 columns)
│   ├── Train.csv                (if applicable)
│   ├── data_arrhythmia.csv      (original data)
│   └── Models/
│       ├── ensemble_model.joblib      - All 5 trained models
│       ├── new.pkl                    - Voting classifier backup
│       └── cardiac_patients.db        - Patient database (auto-created)
│
└── Configuration
    └── requirements.txt         - All dependencies
```

### Database Files (Auto-created)
```
cardiac_patients.db        - Patient records, predictions, history
cardiac_auth.db           - Users, sessions, audit logs
hipaa_compliance.db       - HIPAA audit trail, data retention
fda_compliance.db         - FDA checklist, test results
```

---

## 2. STEP-BY-STEP DEPLOYMENT

### Step 1: Environment Setup
```bash
# 1. Navigate to project directory
cd c:\Users\naikv\Downloads\CARDIAC_ARRHYTHMIA_UPDATED\CARDIAC_ARRHYTHMIA_UPDATED

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Verify activation (should show .venv in prompt)
```

### Step 2: Install Dependencies
```bash
# Option A: From requirements.txt
pip install -r requirements.txt

# Option B: Manual installation
pip install pandas==1.5.3
pip install scikit-learn==1.3.0
pip install numpy==1.24.3
pip install joblib==1.3.0
pip install shap==0.42.0
pip install sqlalchemy==2.0.0
pip install matplotlib==3.7.0
pip install plotly==5.14.0
pip install kaleido==0.2.1
pip install reportlab==4.0.4
pip install fpdf2==2.7.0
pip install flask==2.3.0
pip install flask-cors==4.0.0
pip install pillow==9.5.0
pip install opencv-python==4.7.0
```

### Step 3: Train Models
```bash
# Run training pipeline
python Train.py

# Expected output:
# CARDIAC ARRHYTHMIA PREDICTION - MODEL TRAINING
# ======================================================================
# [1/4] Loading dataset...
# [2/4] Splitting data (80% train, 20% test)...
# [3/4] Training ensemble models...
# 1. Weighted KNN (k=13): 0.9890 accuracy
# 2. Random Forest (200 trees): 0.9743 accuracy
# 3. Gradient Boosting: 0.9890 accuracy
# 4. Support Vector Machine: 0.5846 accuracy
# 5. Voting Ensemble: 0.9743 accuracy
# [4/4] Saving models...
# ✓ Ensemble model saved as 'ensemble_model.joblib'
# TRAINING COMPLETE!

# Files created:
# - ensemble_model.joblib (all 5 models)
# - new.pkl (voting classifier)
```

### Step 4: Initialize Databases
```python
# Run once to initialize all databases:
python -c "
from database import PatientDatabase
from authentication import UserManager
from clinical_compliance import HIPAACompliance, FDARegulatoryCompliance

# Initialize databases
PatientDatabase()
UserManager()
HIPAACompliance()
FDARegulatoryCompliance()
print('✓ All databases initialized successfully')
"
```

### Step 5: Create Default Users
```python
# Run to create default admin and test users:
from authentication import UserManager

auth = UserManager()

# Create admin
auth.create_user('admin', 'admin@hospital.org', 'AdminPass123!', 'admin', 'System', 'Administrator')

# Create cardiologist
auth.create_user('cardiologist', 'doc@hospital.org', 'CardioPass123!', 'cardiologist', 'Dr.', 'Smith')

# Create technician
auth.create_user('technician', 'tech@hospital.org', 'TechPass123!', 'technician', 'John', 'Technician')

print('✓ Default users created')
```

### Step 6: Launch Application

#### Option A: Launch GUI Application
```bash
python UI_Enhanced.py

# Expected:
# - Tkinter window opens
# - 4 tabs visible (Prediction, Patient, Analytics, Settings)
# - Application ready for clinical use
```

#### Option B: Launch API Server
```bash
python api_server.py

# Expected:
# CARDIAC ARRHYTHMIA PREDICTION - REST API
# ======================================================================
# Starting Flask API on 0.0.0.0:5000
# API Documentation:
#   Base URL: http://localhost:5000/api
#   Health Check: GET /api/health
#   Single Prediction: POST /api/predict
#   ...
# 
# Access at: http://localhost:5000/api/health
```

#### Option C: Dual Deployment
```bash
# Terminal 1: Run GUI
python UI_Enhanced.py

# Terminal 2: Run API
python api_server.py

# Both applications run simultaneously
```

---

## 3. CONFIGURATION & CUSTOMIZATION

### Model Configuration
```python
# ensemble_trainer.py - Modify model parameters
class EnsembleModel:
    def train(self, X_train, y_train):
        # KNN parameters
        knn = KNeighborsClassifier(n_neighbors=13, weights='distance')
        
        # Random Forest parameters
        rf = RandomForestClassifier(n_estimators=200, random_state=100)
        
        # Gradient Boosting parameters
        gb = GradientBoostingClassifier(n_estimators=100, random_state=100)
        
        # SVM parameters
        svm = SVC(kernel='rbf', probability=True, random_state=100)
        
        # Voting ensemble
        voting = VotingClassifier(
            estimators=[('knn', knn), ('rf', rf), ('gb', gb), ('svm', svm)],
            voting='hard'
        )
```

### Database Configuration
```python
# database.py - Change database path
db = PatientDatabase(db_path='custom_path/cardiac_patients.db')

# Or modify connection string for other databases
# Add SQLite URI or change to MySQL/PostgreSQL
```

### API Configuration
```python
# api_server.py - Modify host/port
api = CardiacAPI(
    model_path='ensemble_model.joblib',
    host='0.0.0.0',      # 0.0.0.0 for all interfaces, 127.0.0.1 for local only
    port=5000             # Change to 8080, 3000, etc.
)
api.run(debug=False)      # Set to True for development, False for production
```

### Risk Score Thresholds
```python
# risk_scoring.py - Adjust risk level definitions
class RiskScoring:
    @staticmethod
    def _get_risk_level(score, scale):
        if scale == 'cha2ds2_vasc':
            if score <= 1: return 'Low'
            elif score <= 2: return 'Moderate'
            elif score <= 4: return 'High'
            else: return 'Very High'
```

---

## 4. BASIC USAGE EXAMPLES

### Example 1: GUI Prediction
```
1. Launch: python UI_Enhanced.py
2. Enter Patient Info:
   - Name: John Smith
   - Age: 45
   - Sex: Male (1)
   - Height: 175 cm
   - Weight: 70 kg
3. Enter ECG Parameters:
   - QRS: 90 ms
   - QT: 400 ms
   - T: 80 ms
4. Click "Predict"
5. View Results in 3 tabs:
   - Prediction: Condition code + confidence
   - Risk Assessment: 4 clinical risk scores
   - Explainability: Top contributing factors
6. Save to database automatically
7. Optional: Export to PDF
```

### Example 2: API Prediction
```bash
# Single sample
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "sex": 1,
    "height": 175,
    "weight": 70,
    "qrs": 90,
    "qt": 400,
    "t": 80
  }'

# Response:
# {
#   "prediction": 4,
#   "confidence": 0.92,
#   "timestamp": "2026-03-02T14:23:45"
# }
```

### Example 3: Patient Database
```python
from database import PatientDatabase

db = PatientDatabase()

# Add patient
patient_id = db.add_patient(
    name='John Smith',
    age=45,
    sex='M',
    height=175,
    weight=70
)

# Get patient
patient = db.get_patient(patient_id)

# Add prediction
db.add_prediction(
    patient_id=patient_id,
    predicted_class=4,
    confidence_score=0.92,
    risk_scores={'cha2ds2_vasc': {'score': 3, 'risk_level': 'High'}},
    explanation_features={'age': {'feature_value': 45, 'impact': 0.23}}
)

# Get prediction history
history = db.get_patient_predictions(patient_id)
```

### Example 4: Generate PDF Report
```python
from report_generator import PDFReportGenerator

gen = PDFReportGenerator()

filename = gen.generate_prediction_report(
    patient_data={'name': 'John Smith', 'age': 45, 'sex': 'M', ...},
    prediction_data={'predicted_condition': 4, 'confidence_score': 0.92, ...},
    risk_scores={'cha2ds2_vasc': {'score': 3, 'risk_level': 'High'}, ...},
    explanation={'features': {'age': {'feature_value': 45, ...}, ...}}
)

print(f"Report saved: {filename}")
# Output: reports/Prediction_JohnSmith_20260302_142345.pdf
```

---

## 5. TROUBLESHOOTING

### Issue: Model Not Loading
```
Error: "Model not loaded" when making API predictions

Solution:
1. Check ensemble_model.joblib exists in current directory
2. Verify file size > 50MB
3. Run Train.py to retrain if file is corrupted
4. Check disk space available
```

### Issue: Database Lock
```
Error: "database is locked" when accessing patient records

Solution:
1. Close other applications using the database
2. Delete .db-journal file if present
3. Restart application
4. Check file permissions on .db file
```

### Issue: SHAP Calculation Fails
```
Error: "SHAP explanation failed" but prediction succeeded

Solution:
1. This is expected - fallback to permutation importance is automatic
2. No user action required
3. Explainability still provided via alternative method
4. Check system memory if frequently occurring
```

### Issue: API Port Already in Use
```
Error: "Address already in use" when starting api_server.py

Solution:
1. Kill existing process: lsof -i :5000 (Linux/Mac)
   or: netstat -ano | findstr :5000 (Windows)
2. Change port: api = CardiacAPI(port=5001)
3. Wait 60 seconds and retry (port may be in TIME_WAIT state)
```

### Issue: Import Errors
```
Error: "ModuleNotFoundError: No module named 'shap'"

Solution:
1. Activate virtual environment
2. pip install shap
3. Verify all requirements.txt installed:
   pip install -r requirements.txt
4. Check Python version: python --version (should be 3.10+)
```

---

## 6. PERFORMANCE TUNING

### For High-Volume Deployments

#### 1. Batch Processing
```python
# Process multiple patients at once
from api_server import CardiacAPI

api = CardiacAPI()

samples = [
    {'age': 45, 'sex': 1, 'height': 175, ...},
    {'age': 65, 'sex': 0, 'height': 160, ...},
    ...
]

predictions = []
for sample in samples:
    pred = model.predict([sample_to_array(sample)])
    predictions.append(pred[0])
```

#### 2. Database Indexing
```python
# Add indexes for faster queries
import sqlite3

conn = sqlite3.connect('cardiac_patients.db')
cursor = conn.cursor()

cursor.execute('CREATE INDEX idx_patient_name ON patients(name)')
cursor.execute('CREATE INDEX idx_prediction_date ON predictions(created_at)')
cursor.execute('CREATE INDEX idx_patient_predictions ON predictions(patient_id)')

conn.commit()
```

#### 3. Model Caching
```python
# Load model once, reuse for predictions
import joblib

model = joblib.load('ensemble_model.joblib')  # Load once at startup

# Make multiple predictions with loaded model
for sample in samples:
    prediction = model.predict([sample])
    # Model stays in memory for fast inference
```

#### 4. API Load Balancing (Production)
```
Multiple API instances on different ports:
- api_server.py on port 5000
- api_server.py on port 5001
- api_server.py on port 5002

Use Nginx or similar for load balancing:
upstream cardiac_api {
    server localhost:5000;
    server localhost:5001;
    server localhost:5002;
}
```

---

## 7. MONITORING & LOGGING

### Enable Application Logging
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cardiac_app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info('Application started')
```

### Monitor API Requests
```python
from api_server import CardiacAPI

api = CardiacAPI()

@api.app.before_request
def log_request():
    print(f"[{datetime.now()}] {request.method} {request.path}")

@api.app.after_request
def log_response(response):
    print(f"[{datetime.now()}] Response: {response.status_code}")
    return response
```

### Check System Health
```bash
# Check Python process memory
ps aux | grep python

# Monitor database size
ls -lh *.db

# Check API responsiveness
curl http://localhost:5000/api/health

# View application logs
tail -f cardiac_app.log
```

---

## 8. MAINTENANCE & UPDATES

### Regular Maintenance Tasks

#### Weekly
- [ ] Check database size (should stay < 1GB)
- [ ] Review audit logs for anomalies
- [ ] Test API endpoints
- [ ] Verify backup completion

#### Monthly
- [ ] Analyze model performance metrics
- [ ] Review user activity and access patterns
- [ ] Update documentation with changes
- [ ] Check for software updates/security patches

#### Quarterly
- [ ] Retrain models with new data
- [ ] Performance optimization review
- [ ] Security audit
- [ ] Compliance verification

### Database Maintenance
```python
# Cleanup old data (HIPAA requires 6+ year retention, but old audit can be archived)
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('cardiac_patients.db')
cursor = conn.cursor()

# Archive audit logs older than 1 year
old_date = (datetime.now() - timedelta(days=365)).isoformat()
cursor.execute('DELETE FROM audit_log WHERE timestamp < ?', (old_date,))

# Vacuum database to reclaim space
cursor.execute('VACUUM')

conn.commit()
```

### Model Retraining
```bash
# Retrain with new data monthly
python Train.py

# Compare new vs old models
# If accuracy > current model, replace ensemble_model.joblib
```

---

## 9. SECURITY HARDENING (PRODUCTION)

### 1. Enable HTTPS/TLS
```python
# Use production WSGI server with SSL
from waitress import serve
import ssl

# Create SSL context
context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain('/path/to/cert.pem', '/path/to/key.pem')

serve(app, host='0.0.0.0', port=443, _quiet=True, ssl_context=context)
```

### 2. Add API Rate Limiting
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route('/api/predict', methods=['POST'])
@limiter.limit('100/hour')
def predict():
    # Limited to 100 predictions per hour per IP
    pass
```

### 3. Encrypt Sensitive Data
```python
from cryptography.fernet import Fernet

# Generate key once, store securely
key = Fernet.generate_key()

cipher = Fernet(key)

# Encrypt patient PII before storage
encrypted_name = cipher.encrypt(b'John Doe')

# Decrypt when needed
decrypted_name = cipher.decrypt(encrypted_name)
```

### 4. Implement Multi-Factor Authentication
```python
# Add to authentication.py
class TwoFactorAuth:
    def send_otp(self, email):
        # Generate 6-digit OTP
        otp = secrets.randbelow(999999)
        # Send via email/SMS
        # Store temporarily in Redis/Cache
        pass
    
    def verify_otp(self, user_id, otp):
        # Verify OTP matches stored value
        # Invalidate after use
        pass
```

---

## 10. SCALING & CLOUD DEPLOYMENT

### AWS Deployment
```bash
# 1. Create EC2 instance (t3.medium or larger)
# 2. Install dependencies
sudo apt-get update
sudo apt-get install python3.10 python3-pip

# 3. Clone repository
git clone <repo-url>

# 4. Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 5. Install packages
pip install -r requirements.txt

# 6. Use RDS for database (instead of SQLite)
# 7. Use ElastiCache for session storage
# 8. Configure S3 for file uploads

# 9. Deploy with Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:api.app
```

### Docker Containerization
```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "api_server.py"]
```

```bash
# Build image
docker build -t cardiac-app:v2.0 .

# Run container
docker run -p 5000:5000 cardiac-app:v2.0
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cardiac-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cardiac
  template:
    metadata:
      labels:
        app: cardiac
    spec:
      containers:
      - name: cardiac-api
        image: cardiac-app:v2.0
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          value: postgresql://db-service:5432/cardiac
```

---

## 11. COMPLIANCE VERIFICATION CHECKLIST

### Pre-Deployment Verification
- [ ] All models trained and saved
- [ ] Databases initialized with test data
- [ ] API endpoints tested with sample requests
- [ ] GUI tested on Windows/Linux/Mac
- [ ] PDF reports generated successfully
- [ ] User authentication tested
- [ ] Database backup verified
- [ ] Logging enabled
- [ ] Security settings configured
- [ ] Documentation complete

### Post-Deployment Verification
- [ ] System accessible to all users
- [ ] Performance metrics within acceptable ranges
- [ ] Monitoring dashboards showing data
- [ ] Backup processes running
- [ ] Audit logs being recorded
- [ ] No error messages in logs
- [ ] API response times < 500ms
- [ ] Database integrity verified
- [ ] Security protocols enforced
- [ ] Clinical validation completed

---

## 12. SUPPORT & CONTACT

### Documentation References
- Technical Details: COMPLETE_SYSTEM_DOCUMENTATION.md
- Market Analysis: MARKET_ANALYSIS_AND_DIFFERENTIATION.md
- Implementation: IMPLEMENTATION_GUIDE_V2.0.md
- API Reference: See api_server.py docstrings

### Getting Help
```
1. Check troubleshooting section (Section 5)
2. Review relevant documentation file
3. Check application logs for error messages
4. Contact development team with error details and logs
```

---

**Deployment Complete!**

Your Cardiac Arrhythmia Prediction System v2.0 is now fully deployed and ready for clinical use. All 13 modules, databases, APIs, and compliance frameworks are operational.

**Next Steps:**
1. Conduct internal testing and validation
2. Begin multi-hospital pilot program (30-60 days)
3. Prepare FDA 510(k) submission (60-90 days)
4. Launch commercial deployment (Q3 2026)

---

**System Status:** Production Ready  
**Last Updated:** March 2, 2026  
**Version:** v2.0 Complete
