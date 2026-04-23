from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import logging
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(32).hex()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coachsmart_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Secure Session Configuration
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

db = SQLAlchemy(app)

# Role-Based Access Control Decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id') or not session.get('is_admin'):
            abort(403, description='Admin access required')
        return f(*args, **kwargs)
    return decorated_function

# Security Headers Middleware
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

# Security Event Logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.WARNING)
handler = logging.FileHandler('security.log')
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
security_logger.addHandler(handler)

# Secure Error Handlers
@app.errorhandler(403)
def forbidden(error):
    security_logger.warning(f"FORBIDDEN_ACCESS: ip={request.remote_addr}, url={request.url}")
    return render_template('403.html'), 403

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    security_logger.error(f"INTERNAL_ERROR: ip={request.remote_addr}, url={request.url}, error={str(error)}")
    return render_template('500.html'), 500

# User Model - Simplified
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    last_login = db.Column(db.DateTime)

# Muscle Group Model
class MuscleGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100))
    exercises = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# User Progress Model
class UserProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    muscle_group_id = db.Column(db.Integer, db.ForeignKey('muscle_group.id'), nullable=False)
    last_accessed = db.Column(db.DateTime, server_default=db.func.now())
    access_count = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    
    user = db.relationship('User', backref='progress')
    muscle_group = db.relationship('MuscleGroup', backref='progress')

# Initialize Database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Add default muscle groups if they don't exist
        if MuscleGroup.query.count() == 0:
            muscle_groups = [
                {
                    'name': 'Chest (Pectoralis)',
                    'description': 'The chest muscles are responsible for pushing movements and arm adduction. They consist of the pectoralis major and minor muscles.',
                    'location': 'upper_body',
                    'exercises': '["Bench Press", "Push-ups", "Dumbbell Flyes", "Incline Press"]'
                },
                {
                    'name': 'Back (Latissimus)',
                    'description': 'The back muscles, particularly the latissimus dorsi, are responsible for pulling movements and arm extension.',
                    'location': 'upper_body',
                    'exercises': '["Pull-ups", "Rows", "Lat Pulldowns", "Deadlifts"]'
                },
                {
                    'name': 'Shoulders (Deltoids)',
                    'description': 'The shoulder muscles provide mobility and strength for arm movements in multiple directions.',
                    'location': 'upper_body',
                    'exercises': '["Overhead Press", "Lateral Raises", "Front Raises", "Shrugs"]'
                },
                {
                    'name': 'Biceps',
                    'description': 'The biceps are responsible for elbow flexion and forearm supination.',
                    'location': 'upper_body',
                    'exercises': '["Bicep Curls", "Hammer Curls", "Chin-ups", "Preacher Curls"]'
                },
                {
                    'name': 'Triceps',
                    'description': 'The triceps are responsible for elbow extension and make up two-thirds of the upper arm mass.',
                    'location': 'upper_body',
                    'exercises': '["Tricep Dips", "Skull Crushers", "Close Grip Bench Press", "Tricep Pushdowns"]'
                },
                {
                    'name': 'Quadriceps',
                    'description': 'The quadriceps are the large muscles at the front of the thigh responsible for knee extension.',
                    'location': 'lower_body',
                    'exercises': '["Squats", "Leg Press", "Lunges", "Leg Extensions"]'
                },
                {
                    'name': 'Hamstrings',
                    'description': 'The hamstrings are located at the back of the thigh and are responsible for knee flexion and hip extension.',
                    'location': 'lower_body',
                    'exercises': '["Deadlifts", "Leg Curls", "Good Mornings", "Glute Bridges"]'
                },
                {
                    'name': 'Calves',
                    'description': 'The calf muscles are responsible for plantar flexion of the ankle.',
                    'location': 'lower_body',
                    'exercises': '["Calf Raises", "Jump Rope", "Box Jumps", "Sprints"]'
                },
                {
                    'name': 'Core (Abs)',
                    'description': 'The core muscles provide stability for the entire body and are essential for proper posture and movement.',
                    'location': 'core',
                    'exercises': '["Crunches", "Planks", "Leg Raises", "Russian Twists"]'
                },
                {
                    'name': 'Glutes',
                    'description': 'The gluteal muscles are the largest muscles in the body and are responsible for hip extension and abduction.',
                    'location': 'lower_body',
                    'exercises': '["Squats", "Hip Thrusts", "Glute Bridges", "Lunges"]'
                }
            ]
            
            for mg_data in muscle_groups:
                muscle_group = MuscleGroup(**mg_data)
                db.session.add(muscle_group)
            
            # Create default admin user
            admin_password = generate_password_hash('admin123', method='pbkdf2:sha256')
            admin_user = User(
                username='admin',
                email='admin@coachsmart.com',
                password_hash=admin_password,
                is_admin=True
            )
            db.session.add(admin_user)
            
            db.session.commit()
            print('Database initialized with muscle groups and admin user.')

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index_dark.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('index'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('index'))
            
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('index'))
            
        # Create new user
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password_hash=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            # Log user in
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['is_admin'] = new_user.is_admin
            session.permanent = True
            flash('Account created successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/signin', methods=['POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash('Please enter both email and password.', 'error')
            return redirect(url_for('index'))
            
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Log successful login
            security_logger.info(f"SUCCESSFUL_LOGIN: user_id={user.id}, email={email}, ip={request.remote_addr}")
            
            # Log user in
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            session.permanent = True
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Log failed login attempt
            security_logger.warning(f"FAILED_LOGIN: email={email}, ip={request.remote_addr}")
            flash('Invalid email or password.', 'error')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Get all muscle groups
    muscle_groups = MuscleGroup.query.all()
    
    # Get user progress
    user_progress = UserProgress.query.filter_by(user_id=user_id).all()
    progress_dict = {p.muscle_group_id: p for p in user_progress}
    
    return render_template('dashboard_dark.html', 
                         user=user, 
                         muscle_groups=muscle_groups,
                         progress_dict=progress_dict)

@app.route('/muscle/<int:muscle_id>')
def muscle_detail(muscle_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    muscle = MuscleGroup.query.get_or_404(muscle_id)
    user_id = session['user_id']
    
    # Update or create user progress
    progress = UserProgress.query.filter_by(user_id=user_id, muscle_group_id=muscle_id).first()
    if progress:
        progress.last_accessed = datetime.utcnow()
        progress.access_count += 1
    else:
        progress = UserProgress(
            user_id=user_id,
            muscle_group_id=muscle_id,
            access_count=1
        )
        db.session.add(progress)
    
    db.session.commit()
    
    return render_template('muscle_detail_simplified.html', muscle=muscle, progress=progress)

@app.route('/save_notes/<int:muscle_id>', methods=['POST'])
def save_notes(muscle_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    muscle = MuscleGroup.query.get_or_404(muscle_id)
    user_id = session['user_id']
    notes = request.form.get('notes', '')
    
    # Update or create user progress
    progress = UserProgress.query.filter_by(user_id=user_id, muscle_group_id=muscle_id).first()
    if progress:
        progress.notes = notes
    else:
        progress = UserProgress(
            user_id=user_id,
            muscle_group_id=muscle_id,
            notes=notes,
            access_count=1
        )
        db.session.add(progress)
    
    db.session.commit()
    
    return jsonify({'success': True, 'notes': notes})

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5002)
