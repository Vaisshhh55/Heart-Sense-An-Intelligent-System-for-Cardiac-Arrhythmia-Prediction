# 🎬 VISUAL GUIDE - HOW TO USE THE SYSTEM

## Step 1️⃣: Open PowerShell

Click on your PowerShell window or press `Win + R` and type `powershell`

---

## Step 2️⃣: Copy the Command

Copy this exact command:

```powershell
Push-Location "c:\Users\naikv\Downloads\CARDIAC_ARRHYTHMIA_UPDATED\CARDIAC_ARRHYTHMIA_UPDATED"; C:/Users/naikv/Downloads/CARDIAC_ARRHYTHMIA_UPDATED/.venv/Scripts/python.exe UI_Working.py
```

---

## Step 3️⃣: Paste and Run

Right-click in PowerShell and paste, then press **ENTER**

---

## Step 4️⃣: Wait for Startup

You should see:
```
Launching Cardiac Arrhythmia Prediction System...
Initializing modules...
✓ All modules initialized successfully
✓ Ensemble model loaded
Building UI...
✓ UI built successfully
```

Then a GUI window appears with 4 tabs.

---

## 📊 Tab 1: PREDICTION

### What It Shows:
- **Input Form** (left side)
- **Results** (right side with 3 sub-tabs)

### How to Use:
1. **Fill in patient data:**
   ```
   Patient Name: John Smith
   Age (years): 65
   Sex (M/F): M
   Height (cm): 175
   Weight (kg): 85
   QRS Duration (ms): 100
   QT Interval (ms): 380
   T Wave Amplitude (mm): 250
   ```

2. **Click PREDICT button**

3. **View 3 result tabs:**

   **Tab A: Prediction**
   ```
   Patient: John Smith
   Condition Predicted: Atrial Fibrillation
   Condition Code: 14
   Model Confidence: 92.30%
   Prediction Timestamp: 2024-01-15 14:32:15
   
   ECG Parameters:
     QRS Duration: 100.00 ms
     QT Interval: 380.00 ms
     T Wave Amplitude: 250.00 mm
   
   Status: ✓ PREDICTION COMPLETED
   ```

   **Tab B: Risk Assessment**
   ```
   CHA2DS2-VASc Score:
     Score: 2
     Risk Level: Low
     Contributing Factors:
       - Age: +1 points
       - Sex: +0 points
   
   TIMI Risk Score:
     Score: 1
     Risk Level: Low
   
   Framingham Score:
     Score: 15.5
     Risk Level: Moderate
   
   Custom Arrhythmia Risk:
     Score: 62.50%
     Risk Level: Moderate
   ```

   **Tab C: Explainability**
   ```
   TOP CONTRIBUTING FACTORS (in order of impact):
   
   1. QRS          ████████ 0.95
   2. QT           ███████  0.87
   3. T-Wave       ██████   0.72
   4. Age          █████    0.65
   5. Heart Rate   ████     0.58
   6. Weight       ███      0.42
   7. Height       ██       0.35
   ```

---

## 👥 Tab 2: PATIENT MANAGEMENT

### What It Shows:
- **Search box** (top)
- **Patient list** (table below)

### How to Use:

**Option A: Load All Patients**
1. Click **Load All** button
2. See all patients in database table
3. Columns: ID, Name, Age, Sex, BMI, Predictions

**Option B: Search Patient**
1. Type patient name in search box
2. Click **Search** button
3. See matching patients

**Option C: View Patient History**
1. Double-click on any patient in table
2. A popup shows their prediction history:
   ```
   Date: 2024-01-15 14:32:15
   Condition: Atrial Fibrillation
   Confidence: 92.3%
   QRS: 100.5ms | QT: 380.2ms | T: 250.1ms
   ```

**Option D: Export Data**
1. Click **Export** button
2. Choose location to save
3. All patient data exported to JSON file

---

## 📈 Tab 3: ANALYTICS

### What It Shows:
- **6 buttons** for different reports
- **Large text area** displaying results

### How to Use:

**Click any button to see that report:**

**Report 1: System Overview**
```
📊 PATIENT STATISTICS:
  Total Patients: 45
  Average Age: 62.3 years
  Age Range: 35 - 82 years

📈 PREDICTION STATISTICS:
  Total Predictions: 156
  Average Confidence: 89.5%
```

**Report 2: Patient Statistics**
```
📊 OVERVIEW:
  Total Patients: 45

📈 AGE STATISTICS:
  Mean Age: 62.3 years
  Age Groups:
    30-40: 3 patients (6.7%)
    40-50: 8 patients (17.8%)
    50-60: 15 patients (33.3%)
```

**Report 3: Prediction Analytics**
```
📊 OVERALL STATISTICS:
  Total Predictions: 156

🏥 CONDITION DISTRIBUTION:
  Atrial Fibrillation: 34 (21.8%)
  Normal Sinus Rhythm: 28 (17.9%)
  Bradycardia: 22 (14.1%)
```

**Report 4: Temporal Analysis**
```
📅 DAILY DISTRIBUTION:
  Monday: 25 predictions
  Tuesday: 22 predictions
  Wednesday: 19 predictions

⏰ HOURLY DISTRIBUTION:
  Peak Hours: 9-11 AM (12-15 predictions)
```

**Report 5: Risk Analysis**
```
⚠️  AVERAGE RISK BY CONDITION:
  Atrial Fibrillation: 8.50
  Ventricular Fibrillation: 8.20
  Complete Heart Block: 7.90
```

**Report 6: Model Performance**
```
📊 PREDICTION CONFIDENCE DISTRIBUTION:

✅ HIGH CONFIDENCE (>85%):
  Count: 132 | Percentage: 84.6%

⚠️  MEDIUM CONFIDENCE (75-85%):
  Count: 18 | Percentage: 11.5%
```

---

## ⚙️ Tab 4: SETTINGS

### What It Shows:
- **6 buttons** for different settings
- **Large text area** displaying information

### How to Use:

**COMPLIANCE BUTTONS:**

**Button 1: HIPAA Status**
```
╔════════════════════════════════════════════════════╗
║           HIPAA COMPLIANCE STATUS                  ║
╚════════════════════════════════════════════════════╝

ENCRYPTION:
  ✓ Field-Level PHI Encryption: ENABLED
  ✓ Method: AES-256-GCM
  ✓ Key Management: SECURE

AUDIT LOGGING:
  ✓ Access Logging: ENABLED
  ✓ Breach Detection: ACTIVE
  ✓ Retention Period: 90 days
```

**Button 2: FDA 510(k) Checklist**
```
╔════════════════════════════════════════════════════╗
║        FDA 510(k) REGULATORY COMPLIANCE            ║
╚════════════════════════════════════════════════════╝

DEVICE CLASSIFICATION:
  ✓ Class II Device: YES
  ✓ Substantial Equivalence: ESTABLISHED
  ✓ Predicate Devices: 15 identified

VALIDATION & TESTING:
  ✓ IEC 62304 Compliance: YES
  ✓ ISO 14971 Risk Analysis: YES
  ✓ Clinical Validation: COMPLETE
  ✓ Accuracy Validation: 97.43%
```

**Button 3: Audit Log**
```
HIPAA AUDIT LOG (Last 50 Events)

[2024-01-15 14:32:15] PREDICTION | John Smith
[2024-01-15 14:15:22] LOGIN | doctor_user
[2024-01-15 13:45:10] PATIENT_VIEW | John Smith
[2024-01-15 12:20:33] DATA_EXPORT | All Patients
...
```

**SYSTEM BUTTONS:**

**Button 4: Database Info**
```
DATABASE INFORMATION

1. PATIENT DATABASE (cardiac_patients.db)
   Purpose: Store patient records and predictions
   Encryption: AES-256-GCM
   Status: ✓ Active

2. AUTHENTICATION DATABASE (cardiac_auth.db)
   Purpose: User credentials and sessions
   Encryption: PBKDF2-HMAC-SHA256
   Status: ✓ Active

3. HIPAA COMPLIANCE DATABASE (hipaa_compliance.db)
   Purpose: HIPAA audit logs and breach detection
   Encryption: AES-256-GCM
   Status: ✓ Active

4. FDA COMPLIANCE DATABASE (fda_compliance.db)
   Purpose: FDA 510(k) regulatory tracking
   Encryption: AES-256-GCM
   Status: ✓ Active
```

**Button 5: Model Info**
```
MACHINE LEARNING MODEL INFORMATION

ENSEMBLE ARCHITECTURE:
  Model Type: 5-Model Voting Classifier

BASE MODELS:
  1. K-Nearest Neighbors: 98.90% accuracy
  2. Random Forest: 97.43% accuracy
  3. Gradient Boosting: 98.90% accuracy
  4. Support Vector Machine: 58.46% accuracy
  5. Voting Classifier: 97.43% overall

PERFORMANCE METRICS:
  Overall Accuracy: 97.43%
  Precision: 96.8%
  Recall: 96.5%
  F1-Score: 96.6%
```

**Button 6: API Info**
```
REST API CONFIGURATION

Base URL: http://localhost:5000/api

AVAILABLE ENDPOINTS:
  1. POST /predict - Single ECG prediction
  2. POST /predict_batch - Batch predictions
  3. GET /patient/<id> - Retrieve patient records
  4. POST /patient - Create new patient
  5. GET /reports/<id> - Generate clinical report
  6. GET /model/info - Model information
  7. POST /auth/login - User authentication

STATUS: ✓ READY FOR INTEGRATION
```

---

## 🎯 QUICK TEST WALKTHROUGH

### **Step 1: Prediction**
1. Go to **Prediction Tab**
2. Enter test data (see above)
3. Click **PREDICT**
4. View the 3 result tabs
5. **You should see:**
   - A cardiac condition (e.g., "Atrial Fibrillation")
   - 4 risk scores with clinical interpretation
   - Top 7 factors that influenced the prediction

### **Step 2: Patient Management**
1. Go to **Patient Tab**
2. Click **Load All**
3. **You should see:**
   - "John Smith" in the patient list
   - His age, sex, BMI, prediction count
4. **Double-click** on John Smith
5. **You should see:**
   - His prediction history
   - All ECG parameters from the prediction

### **Step 3: Analytics**
1. Go to **Analytics Tab**
2. Click **System Overview**
3. **You should see:**
   - Total patients count
   - Total predictions count
   - Most common conditions
   - Average confidence

### **Step 4: Settings**
1. Go to **Settings Tab**
2. Click **HIPAA Status**
3. **You should see:**
   - Encryption status: ENABLED
   - Audit logging: ACTIVE
   - Breach detection: ACTIVE
4. Click **Model Info**
5. **You should see:**
   - 97.43% accuracy
   - 5-model ensemble
   - 13 cardiac conditions

---

## ✅ EVERYTHING WORKING?

If you see:
- ✅ Prediction results displayed
- ✅ 4 risk scores calculated
- ✅ Patient saved to database
- ✅ Patient visible in Patient tab
- ✅ Analytics reports generated
- ✅ HIPAA status showing "ENABLED"

**Then everything is working perfectly!** 🎉

---

## 🆘 TROUBLESHOOTING

| Issue | Solution |
|-------|----------|
| App won't open | Use exact command from Step 2 above |
| App crashes on start | Ensure you're using `UI_Working.py` |
| No prediction results | Make sure all input fields have values |
| Patient not showing | Click "Load All" in Patient tab |
| Analytics empty | Make sure you made at least 1 prediction |
| HIPAA shows "DISABLED" | Database might need initialization |

---

## 📚 RELATED DOCUMENTATION

- [RUN_APPLICATION.md](RUN_APPLICATION.md) - How to run
- [SYSTEM_FIXES.md](SYSTEM_FIXES.md) - What was fixed
- [COMPLETE_SYSTEM_STATUS.md](COMPLETE_SYSTEM_STATUS.md) - Full system details
- [FEATURE_VERIFICATION_REPORT.md](FEATURE_VERIFICATION_REPORT.md) - Feature details

---

## 🎉 YOU'RE ALL SET!

The system is ready to use. Follow the steps above and everything should work perfectly!
