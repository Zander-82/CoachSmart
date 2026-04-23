# CoachSmart Security Rewrite Guide

**Inspired by:** 12SE_Task2_students VIP Pizza vulnerability fixes  
**Goal:** Rewrite CoachSmart to be secure from the ground up

---

## 🎯 Security Vulnerabilities to Address

### From VIP Pizza Analysis:
1. **Arbitrary File Read (Critical)** - Direct file access
2. **SQL Injection (Critical)** - Database manipulation  
3. **Stored XSS (High)** - Malicious script injection
4. **Insecure Authentication** - Weak password handling
5. **Missing Input Validation** - Unsanized user data
6. **Information Disclosure** - Sensitive data exposure
7. **Insecure Session Management** - Weak session handling
8. **Missing Access Controls** - Authorization bypass

---

## 🛡️ CoachSmart Security Implementation Plan

### 🔐 **1. Authentication & Authorization**

#### **Current Issues:**
- Plain text passwords in database
- No password hashing
- Weak session management
- Missing role-based access control

#### **Security Fixes:**
```python
# Password Hashing
from werkzeug.security import generate_password_hash, check_password_hash

# Secure Session Management
app.secret_key = os.urandom(32).hex()  # Random secret key
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Role-Based Access Control
@app.before_request
def check_permissions():
    if request.endpoint and request.endpoint.startswith('admin'):
        if not session.get('user') or not session.get('is_admin'):
            abort(403)

# Secure Login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Parameterized query
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid credentials'})
```

---

### 🎭 **2. Input Validation & XSS Prevention**

#### **Current Issues:**
- No input sanitization
- Direct database storage of user input
- XSS vulnerabilities in forms

#### **Security Fixes:**
```python
# Input Validation
from marshmallow import Schema, fields, validate
from bleach import clean

# User Input Schema
class UserSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8))

# Workout Input Schema  
class WorkoutSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    duration = fields.Int(required=True, validate=validate.Range(min=1, max=300))
    notes = fields.Str(validate=validate.Length(max=1000))

# XSS Prevention
def sanitize_input(text):
    if not text:
        return ""
    
    # Remove dangerous HTML
    dangerous_patterns = [
        '<script', '</script>', 'javascript:', 'onerror=', 
        'onclick=', 'onmouseover=', '<iframe', 'vbscript:'
    ]
    
    for pattern in dangerous_patterns:
        text = text.replace(pattern, '')
    
    # HTML entity encoding
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    
    return text

# Secure Form Handling
@app.route('/workout', methods=['POST'])
def create_workout():
    try:
        # Validate and sanitize input
        schema = WorkoutSchema()
        data = schema.load(request.form)
        
        # XSS prevention
        data['notes'] = sanitize_input(data['notes'])
        data['title'] = sanitize_input(data['title'])
        
        # Create workout with validated data
        workout = Workout(**data)
        db.session.add(workout)
        db.session.commit()
        
        return jsonify({'success': True, 'workout': workout.id})
        
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.messages})
```

---

### 💾 **3. Database Security**

#### **Current Issues:**
- SQL injection vulnerabilities
- No connection encryption
- Missing database backups
- Unprotected sensitive data

#### **Security Fixes:**
```python
# Parameterized Queries (NO SQL INJECTION)
def get_user_workouts(user_id):
    # SAFE: Parameterized query
    workouts = Workout.query.filter_by(user_id=user_id).all()
    return workouts

# DANGEROUS: String formatting (VULNERABLE)
# workouts = db.session.execute(f"SELECT * FROM workouts WHERE user_id = {user_id}")

# Database Encryption
from cryptography.fernet import Fernet
import os

# Encrypt sensitive data
def encrypt_sensitive_data(data):
    key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
    fernet = Fernet(key)
    return fernet.encrypt(data.encode())

# Database Connection Security
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,
    'pool_recycle': 3600,
    'connect_args': {
        'check_same_thread': False,
        'isolation_level': None
    }
}

# Secure Database Schema
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)  # Hashed, not plaintext
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_login = db.Column(db.DateTime)
```

---

### 🌐 **4. File Upload & Access Control**

#### **Current Issues:**
- Unrestricted file uploads
- No file type validation
- Directory traversal vulnerabilities
- Missing access controls

#### **Security Fixes:**
```python
import os
from werkzeug.utils import secure_filename
from PIL import Image

# Secure File Upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    # File validation
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    if len(file.read()) > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large'}), 400
    
    # Secure filename and storage
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Ensure directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    file.save(file_path)
    return jsonify({'success': True, 'filename': filename})

# Secure File Access
@app.route('/files/<filename>')
def serve_file(filename):
    # Directory traversal prevention
    if '..' in filename or filename.startswith('/'):
        abort(400, description='Invalid filename')
    
    # Whitelist approach
    ALLOWED_FILES = ['profile.jpg', 'workout.pdf', 'stats.csv']
    if filename not in ALLOWED_FILES:
        abort(404, description='File not found')
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        abort(404, description='File not available')
    
    return send_file(file_path, as_attachment=True)
```

---

### 📊 **5. API Security**

#### **Current Issues:**
- No rate limiting
- No API authentication
- Missing CORS configuration
- No input validation

#### **Security Fixes:**
```python
from flask_limiter import Limiter
from functools import wraps

# Rate Limiting
@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def api_login():
    # API endpoint with rate limiting
    pass

# API Key Authentication
API_KEYS = os.environ.get('API_KEYS', '').split(',')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key not in API_KEYS:
            abort(401, description='Invalid API key')
        return f(*args, **kwargs)
    return decorated_function

# Secure CORS Configuration
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://trusted-domain.com"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})

# Input Validation for API
@app.route('/api/workout', methods=['POST'])
@require_api_key
def create_workout_api():
    schema = WorkoutSchema()
    try:
        data = schema.load(request.json)
        # Process validated data
        return jsonify({'success': True, 'workout': data})
    except ValidationError as e:
        return jsonify({'success': False, 'errors': e.messages}), 400
```

---

### 🔍 **6. Error Handling & Logging**

#### **Current Issues:**
- Verbose error messages
- No security logging
- Stack trace exposure
- Missing error handling

#### **Security Fixes:**
```python
import logging
from logging.handlers import RotatingFileHandler

# Secure Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        RotatingFileHandler('security.log', maxBytes=10485760, backupCount=5)
    ]
)

# Security Event Logger
security_logger = logging.getLogger('security')

def log_security_event(event_type, details):
    security_logger.warning(f"{event_type}: {details}")

# Secure Error Handling
@app.errorhandler(500)
def internal_error(error):
    log_security_event('INTERNAL_ERROR', str(error))
    
    # Don't expose stack traces to users
    return jsonify({
        'error': 'Internal server error',
        'message': 'Something went wrong'
    }), 500

@app.errorhandler(404)
def not_found(error):
    log_security_event('NOT_FOUND', request.url)
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(403)
def forbidden(error):
    log_security_event('FORBIDDEN_ACCESS', f"{request.remote_addr} tried to access {request.url}")
    return jsonify({'error': 'Access forbidden'}), 403
```

---

### 🛡️ **7. Configuration & Environment Security**

#### **Current Issues:**
- Hardcoded secrets
- Debug mode in production
- Insecure default configurations
- Environment variable exposure

#### **Security Fixes:**
```python
import os
from dotenv import load_dotenv

# Environment Configuration
load_dotenv()

# Secure Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///coachsmart.db')
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY') or Fernet.generate_key()
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    
    # Production settings
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING = os.environ.get('FLASK_TESTING', 'False').lower() == 'true'

# Secure Flask App
app = Flask(__name__)
app.config.from_object(Config)

# Security Headers
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=315; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

---

## 🎯 Implementation Priority

### **Phase 1: Critical Security (Week 1)**
1. ✅ Fix authentication system
2. ✅ Implement password hashing
3. ✅ Add input validation
4. ✅ Prevent SQL injection
5. ✅ Basic XSS protection

### **Phase 2: Advanced Security (Week 2)**
1. ✅ Add comprehensive logging
2. ✅ Implement rate limiting
3. ✅ Secure file uploads
4. ✅ Add API authentication
5. ✅ Implement access controls

### **Phase 3: Production Hardening (Week 3)**
1. ✅ Security headers
2. ✅ Environment configuration
3. ✅ Error handling
4. ✅ Database encryption
5. ✅ Monitoring and alerting

---

## 🧪 Testing Strategy

### **Security Testing Tools:**
- **OWASP ZAP** - Automated vulnerability scanning
- **Burp Suite** - Manual penetration testing
- **SQLMap** - SQL injection testing
- **XSSer** - Cross-site scripting testing

### **Test Cases:**
```bash
# Authentication Tests
curl -X POST -d "username=admin'--&password=anything" http://localhost:5000/login
curl -X POST -d "username=' OR '1'='1&password=test" http://localhost:5000/login

# XSS Tests
curl -X POST -d "notes=<script>alert('xss')</script>" http://localhost:5000/workout

# File Access Tests
curl "http://localhost:5000/files/../../../etc/passwd"
curl -X POST -F "file=@malicious.php" http://localhost:5000/upload

# API Tests
curl -H "X-API-Key: invalid" http://localhost:5000/api/workout
```

---

## 📋 Security Checklist

### **Authentication:**
- [ ] Password hashing implemented
- [ ] Secure session management
- [ ] Rate limiting on auth
- [ ] Multi-factor authentication
- [ ] Password complexity requirements
- [ ] Account lockout protection

### **Input Validation:**
- [ ] All user inputs validated
- [ ] XSS prevention implemented
- [ ] SQL injection protection
- [ ] File upload validation
- [ ] API input sanitization

### **Data Protection:**
- [ ] Database encryption
- [ ] Sensitive data masking
- [ ] Secure file storage
- [ ] Backup encryption
- [ ] Data retention policies

### **Access Control:**
- [ ] Role-based permissions
- [ ] Resource ownership
- [ ] API authentication
- [ ] Secure file access
- [ ] Admin protection

### **Infrastructure:**
- [ ] Security headers
- [ ] HTTPS enforcement
- [ ] Environment variables
- [ ] Security logging
- [ ] Error handling
- [ ] Monitoring setup

---

## 🚀 Implementation Timeline

**Week 1:** Foundation Security
- Authentication overhaul
- Input validation framework
- Basic XSS protection

**Week 2:** Advanced Protection  
- API security
- File upload security
- Comprehensive logging

**Week 3:** Production Ready
- Security headers
- Environment hardening
- Monitoring integration

**Result:** CoachSmart becomes a secure, production-ready coaching platform! 🎯

---

## 📚 Resources

**Security Frameworks:**
- Flask-Security - Authentication and authorization
- Marshmallow - Input validation
- Bleach - XSS prevention
- Flask-Limiter - Rate limiting

**Documentation:**
- OWASP Top 10 - Security best practices
- Flask Security Patterns - Community guidelines
- Security Testing Guide - Penetration testing

**Tools:**
- Bandit - Python security scanning
- Safety - Dependency checking
- Semgrep - Code analysis

---

**This guide transforms CoachSmart from a vulnerable application into a secure, enterprise-ready platform using proven security patterns from the VIP Pizza vulnerability analysis.**
