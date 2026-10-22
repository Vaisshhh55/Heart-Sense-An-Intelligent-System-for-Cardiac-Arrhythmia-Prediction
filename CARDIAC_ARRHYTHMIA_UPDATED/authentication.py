"""
User Authentication and Authorization Module
Provides secure user management, authentication, and role-based access control
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import json
import logging

logger = logging.getLogger('cardiac.auth')
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

class UserManager:
    """Manage users, authentication, and authorization"""
    
    # User roles
    ROLE_ADMIN = 'admin'
    ROLE_CARDIOLOGIST = 'cardiologist'
    ROLE_TECHNICIAN = 'technician'
    ROLE_PATIENT = 'patient'
    
    # Permission definitions
    PERMISSIONS = {
        'admin': ['view_all_patients', 'edit_all_patients', 'manage_users', 'export_data', 'view_analytics', 'manage_settings', 'run_predictions'],
        'cardiologist': ['view_assigned_patients', 'edit_assigned_patients', 'export_data', 'view_analytics', 'run_predictions'],
        'technician': ['view_patient_data', 'input_ecg_data', 'run_predictions'],
        'patient': ['view_own_data', 'view_own_predictions']
    }
    
    def __init__(self, db_path='cardiac_auth.db'):
        """Initialize user management"""
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize authentication database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                first_name TEXT,
                last_name TEXT,
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Patient-Doctor mapping table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patient_assignments (
                assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id TEXT NOT NULL,
                doctor_id TEXT NOT NULL,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES users(user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using PBKDF2"""
        return hashlib.pbkdf2_hmac('sha256', password.encode(), b'cardiac_salt', 100000).hex()
    
    @staticmethod
    def _generate_user_id() -> str:
        """Generate unique user ID"""
        return f"USR_{secrets.token_hex(8)}"
    
    @staticmethod
    def _generate_token() -> str:
        """Generate authentication token"""
        return secrets.token_urlsafe(32)
    
    def create_user(self, username: str, email: str, password: str, 
                   role: str, first_name: str = '', last_name: str = '', 
                   department: str = '') -> Tuple[bool, Dict]:
        """Create new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Validate role
            if role not in self.PERMISSIONS:
                return False, {'error': f'Invalid role: {role}'}
            
            # Check username/email uniqueness
            cursor.execute('SELECT user_id FROM users WHERE username = ? OR email = ?', 
                          (username, email))
            if cursor.fetchone():
                return False, {'error': 'Username or email already exists'}
            
            # Create user
            user_id = self._generate_user_id()
            password_hash = self._hash_password(password)
            
            cursor.execute('''
                INSERT INTO users 
                (user_id, username, email, password_hash, role, first_name, last_name, department)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, role, first_name, last_name, department))
            
            conn.commit()
            conn.close()
            
            return True, {
                'user_id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'message': 'User created successfully'
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    def authenticate(self, username: str, password: str, 
                    ip_address: str = '', user_agent: str = '') -> Tuple[bool, Dict]:
        """Authenticate user and create session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find user
            cursor.execute('''
                SELECT user_id, password_hash, role, is_active, first_name, last_name
                FROM users WHERE username = ?
            ''', (username,))
            
            user = cursor.fetchone()
            if not user:
                return False, {'error': 'Invalid credentials'}
            
            user_id, stored_hash, role, is_active, first_name, last_name = user
            
            # Check if active
            if not is_active:
                return False, {'error': 'User account is inactive'}
            
            # Verify password
            if self._hash_password(password) != stored_hash:
                return False, {'error': 'Invalid credentials'}
            
            # Update last login
            cursor.execute('UPDATE users SET last_login = ? WHERE user_id = ?',
                          (datetime.now().isoformat(), user_id))
            
            # Create session
            session_id = self._generate_user_id()
            token = self._generate_token()
            expires_at = (datetime.now() + timedelta(hours=8)).isoformat()
            
            cursor.execute('''
                INSERT INTO sessions 
                (session_id, user_id, token, expires_at, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, token, expires_at, ip_address, user_agent))
            
            # Log authentication
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, 'LOGIN', f'IP: {ip_address}'))
            
            conn.commit()
            conn.close()
            
            return True, {
                'user_id': user_id,
                'username': username,
                'role': role,
                'full_name': f"{first_name} {last_name}".strip(),
                'token': token,
                'expires_at': expires_at,
                'permissions': self.PERMISSIONS[role],
                'message': 'Authentication successful'
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    def verify_token(self, token: str) -> Tuple[bool, Dict]:
        """Verify authentication token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.user_id, u.username, u.role, u.is_active, s.expires_at
                FROM sessions s
                JOIN users u ON s.user_id = u.user_id
                WHERE s.token = ? AND s.is_active = 1
            ''', (token,))
            
            session = cursor.fetchone()
            if not session:
                return False, {'error': 'Invalid token'}
            
            user_id, username, role, is_active, expires_at = session
            
            # Check expiration
            if datetime.fromisoformat(expires_at) < datetime.now():
                cursor.execute('UPDATE sessions SET is_active = 0 WHERE token = ?', (token,))
                conn.commit()
                conn.close()
                return False, {'error': 'Token expired'}
            
            # Check if user is still active
            if not is_active:
                return False, {'error': 'User account is inactive'}
            
            conn.close()
            
            return True, {
                'user_id': user_id,
                'username': username,
                'role': role,
                'permissions': self.PERMISSIONS[role]
            }
        
        except Exception as e:
            return False, {'error': str(e)}
    
    def check_permission(self, user_id: str, permission: str) -> bool:
        """Check if user has specific permission"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT role FROM users WHERE user_id = ? AND is_active = 1', (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return False
            
            role = result[0]
            return permission in self.PERMISSIONS.get(role, [])
        
        except Exception as e:
            logger.exception('Error checking permissions for user %s permission %s', user_id, permission)
            return False
    
    def log_action(self, user_id: str, action: str, resource: str = '', details: str = '') -> bool:
        """Log user action for audit trail"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_log (user_id, action, resource, details)
                VALUES (?, ?, ?, ?)
            ''', (user_id, action, resource, details))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.exception('Error logging action %s for user %s', action, user_id)
            return False

    def get_audit_log(self, user_id: str = '', limit: int = 100) -> list:
        """Get audit log"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute('''
                    SELECT log_id, user_id, action, resource, details, timestamp
                    FROM audit_log
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, limit))
            else:
                cursor.execute('''
                    SELECT log_id, user_id, action, resource, details, timestamp
                    FROM audit_log
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            
            logs = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'log_id': log[0],
                    'user_id': log[1],
                    'action': log[2],
                    'resource': log[3],
                    'details': log[4],
                    'timestamp': log[5]
                }
                for log in logs
            ]
        
        except Exception as e:
            return []
    
    def assign_patient_to_doctor(self, patient_id: str, doctor_id: str) -> bool:
        """Assign patient to cardiologist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO patient_assignments (patient_id, doctor_id)
                VALUES (?, ?)
            ''', (patient_id, doctor_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.exception('Error assigning patient %s to doctor %s', patient_id, doctor_id)
            return False

    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('UPDATE users SET is_active = 0 WHERE user_id = ?', (user_id,))
            cursor.execute('UPDATE sessions SET is_active = 0 WHERE user_id = ?', (user_id,))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.exception('Error deactivating user %s', user_id)
            return False
