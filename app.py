from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coachsmart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # Relationships
    workouts = db.relationship('Workout', backref='user', lazy=True, cascade='all, delete-orphan')
    user_stats = db.relationship('UserStats', backref='user', lazy=True, uselist=False, cascade='all, delete-orphan')
    challenges = db.relationship('UserChallenge', backref='user', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('Activity', backref='user', lazy=True, cascade='all, delete-orphan')

# User Stats Model
class UserStats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    total_workouts = db.Column(db.Integer, default=0)
    total_time_minutes = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

# Goal Model
class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    goal_type = db.Column(db.String(50), nullable=False)  # 'weight_loss', 'muscle_gain', 'endurance', 'strength', 'custom'
    target_value = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(20), nullable=False)  # 'kg', 'lbs', 'minutes', 'workouts', 'km', etc.
    target_date = db.Column(db.Date)
    is_completed = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    completed_at = db.Column(db.DateTime)
    
    # Relationship to user
    user = db.relationship('User', backref='goals')

# Workout Model
class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    workout_type = db.Column(db.String(50), nullable=False)  # Upper Body, Lower Body, etc.
    duration_minutes = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # Easy, Medium, Hard, Intense
    points_earned = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, server_default=db.func.now())

# Custom Workout Model
class CustomWorkout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    workout_type = db.Column(db.String(50), nullable=False)
    exercises = db.Column(db.Text, nullable=False)  # JSON string of exercises
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Activity Model
class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # workout, achievement, personal_record, challenge
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    points_earned = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

# Challenge Model
class Challenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    target_value = db.Column(db.Integer, nullable=False)
    points_reward = db.Column(db.Integer, nullable=False)
    badge_name = db.Column(db.String(50))
    challenge_type = db.Column(db.String(50), nullable=False)  # streak, workout_count, etc.

# User Challenge Model (tracks user progress in challenges)
class UserChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenge.id'), nullable=False)
    current_progress = db.Column(db.Integer, default=0)
    is_completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, server_default=db.func.now())
    completed_at = db.Column(db.DateTime)
    
    # Relationship to challenge
    challenge = db.relationship('Challenge', backref='user_challenges')

# Create tables
def create_tables():
    with app.app_context():
        db.create_all()

# Flask CLI command to initialize database
@app.cli.command('init-db')
def init_db_command():
    """Initialize the database."""
    create_tables()
    
    # Create default challenges if they don't exist
    if Challenge.query.count() == 0:
        default_challenges = [
            # Regular Challenges (50-99 points)
            Challenge(name='30-Day Streak', description='Keep the fire burning! Work out every day for 30 days.', 
                     target_value=30, points_reward=500, badge_name='Fire Badge', challenge_type='streak'),
            Challenge(name='Strength Builder', description='Complete 20 strength workouts to build muscle power.', 
                     target_value=20, points_reward=300, badge_name='Strength Badge', challenge_type='workout_count'),
            Challenge(name='Speed Demon', description='Run 5K under 22 minutes', 
                     target_value=1, points_reward=400, badge_name='Speed Badge', challenge_type='personal_record'),
            Challenge(name='Zen Master', description='Complete 15 yoga sessions', 
                     target_value=15, points_reward=250, badge_name='Zen Badge', challenge_type='workout_count'),
            Challenge(name='Fighter', description='Complete 10 boxing workouts', 
                     target_value=10, points_reward=350, badge_name='Fighter Badge', challenge_type='workout_count'),
            Challenge(name='HIIT Hero', description='Complete 25 HIIT workouts', 
                     target_value=25, points_reward=450, badge_name='HIIT Badge', challenge_type='workout_count'),
            Challenge(name='Early Bird', description='10 morning workouts (6-8 AM)', 
                     target_value=10, points_reward=200, badge_name='Early Bird Badge', challenge_type='workout_count'),
            Challenge(name='Perfect Week', description='7 workouts in one week', 
                     target_value=7, points_reward=300, badge_name='Perfect Week Badge', challenge_type='weekly_goal'),
            
            # New Regular Challenges
            Challenge(name='Cardio King', description='Complete 30 cardio workouts', 
                     target_value=30, points_reward=350, badge_name='Cardio Badge', challenge_type='workout_count'),
            Challenge(name='Weekend Warrior', description='15 weekend workouts', 
                     target_value=15, points_reward=280, badge_name='Weekend Badge', challenge_type='workout_count'),
            Challenge(name='Mind & Body', description='20 yoga or meditation sessions', 
                     target_value=20, points_reward=320, badge_name='Mindfulness Badge', challenge_type='workout_count'),
            Challenge(name='Quick Fire', description='25 quick workouts (under 20 minutes)', 
                     target_value=25, points_reward=300, badge_name='Quick Badge', challenge_type='workout_count'),
            Challenge(name='Marathon Ready', description='Run 50km total distance', 
                     target_value=50, points_reward=400, badge_name='Distance Badge', challenge_type='distance'),
            Challenge(name='Calorie Crusher', description='Burn 10,000 calories', 
                     target_value=10000, points_reward=380, badge_name='Burn Badge', challenge_type='calories'),
            Challenge(name='Consistency Champion', description='Work out 3x per week for 8 weeks', 
                     target_value=24, points_reward=450, badge_name='Consistency Badge', challenge_type='workout_count'),
            
            # Gold Medal Challenges (100+ points or gold badge)
            Challenge(name='100 Day Warrior', description='Work out every day for 100 days straight!', 
                     target_value=100, points_reward=1500, badge_name='gold', challenge_type='streak'),
            Challenge(name='Elite Athlete', description='Complete 100 total workouts', 
                     target_value=100, points_reward=1200, badge_name='gold', challenge_type='workout_count'),
            Challenge(name='Century Club', description='Accumulate 10,000 workout minutes', 
                     target_value=10000, points_reward=1000, badge_name='gold', challenge_type='time'),
            Challenge(name='Master of All', description='Complete 20 workouts of each type (5 types)', 
                     target_value=100, points_reward=1100, badge_name='gold', challenge_type='variety'),
            Challenge(name='Legendary Streak', description='Maintain a 50-day workout streak', 
                     target_value=50, points_reward=800, badge_name='gold', challenge_type='streak'),
            Challenge(name='Point Master', description='Earn 5,000 total points', 
                     target_value=5000, points_reward=900, badge_name='gold', challenge_type='points'),
            Challenge(name='Challenge Conqueror', description='Complete 50 different challenges', 
                     target_value=50, points_reward=1300, badge_name='gold', challenge_type='challenge_count'),
            Challenge(name='Fitness Guru', description='Work out 500 times total', 
                     target_value=500, points_reward=2000, badge_name='gold', challenge_type='workout_count'),
            Challenge(name='Time Titan', description='Spend 200 hours working out', 
                     target_value=12000, points_reward=1500, badge_name='gold', challenge_type='time'),
            Challenge(name='Ultimate Champion', description='Complete all challenge types and maintain 30-day streak', 
                     target_value=1, points_reward=2500, badge_name='gold', challenge_type='ultimate'),
        ]
        
        for challenge in default_challenges:
            db.session.add(challenge)
        
        db.session.commit()
        print('Default challenges created.')
    
    # Create default goal templates if they don't exist
    # Note: These are templates, users will create their own instances
    print('Database initialized.')

@app.route('/')
def index():
    username = session.get('username')
    return render_template('index.html', username=username)

@app.route('/features')
def features():
    return render_template('features.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Here you would typically process the form data
        # For now, we'll just show a success message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

@app.route('/get-started')
def get_started():
    return render_template('get_started.html')

# Authentication Routes
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
            return redirect(url_for('get_started'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('get_started'))
            
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('get_started'))
            
        # Create new user
        try:
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            
            # Initialize user stats
            user_stats = UserStats(user_id=new_user.id)
            db.session.add(user_stats)
            
            db.session.commit()
            
            # Log the user in
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            flash('Account created successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('get_started'))
    
    return redirect(url_for('get_started'))

@app.route('/signin', methods=['POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([email, password]):
            flash('Please enter both email and password.', 'error')
            return redirect(url_for('get_started'))
            
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            # Log the user in
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('get_started'))
    
    return redirect(url_for('get_started'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']
    
    # Get or create user stats
    user_stats = UserStats.query.filter_by(user_id=user_id).first()
    if not user_stats:
        user_stats = UserStats(user_id=user_id)
        db.session.add(user_stats)
        db.session.commit()
    
    # Get recent activities
    recent_activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.created_at.desc()).limit(10).all()
    
    # Get active challenges
    active_challenges = db.session.query(UserChallenge, Challenge).join(Challenge).filter(
        UserChallenge.user_id == user_id,
        UserChallenge.is_completed == False
    ).all()
    
    return render_template('dashboard.html', 
                         username=session.get('username'),
                         user_stats=user_stats,
                         recent_activities=recent_activities,
                         active_challenges=active_challenges)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Workout Routes
@app.route('/start-workout')
def start_workout():
    if 'user_id' not in session:
        flash('Please sign in to start a workout.', 'error')
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']

    # Get user stats for display
    user_stats = UserStats.query.filter_by(user_id=user_id).first()
    
    # Get recent workouts for recommendations
    recent_workouts = Workout.query.filter_by(user_id=user_id).order_by(Workout.completed_at.desc()).limit(10).all()
    
    # Get custom workouts for this user
    custom_workouts_db = CustomWorkout.query.filter_by(user_id=user_id).order_by(CustomWorkout.created_at.desc()).all()
    custom_workouts = []
    for workout in custom_workouts_db:
        custom_workouts.append({
            'id': workout.id,
            'name': workout.name,
            'duration_minutes': workout.duration_minutes,
            'difficulty': workout.difficulty,
            'workout_type': workout.workout_type,
            'exercises': workout.exercises,
            'description': workout.description,
            'created_at': workout.created_at.isoformat() if workout.created_at else None
        })
    
    # Determine user preferences based on past activities
    workout_preferences = {}
    if recent_workouts:
        workout_types = [w.workout_type for w in recent_workouts]
        difficulties = [w.difficulty for w in recent_workouts]
        
        # Count frequency of workout types
        from collections import Counter
        type_counts = Counter(workout_types)
        difficulty_counts = Counter(difficulties)
        
        workout_preferences['favorite_type'] = type_counts.most_common(1)[0][0] if type_counts else 'Cardio'
        workout_preferences['preferred_difficulty'] = difficulty_counts.most_common(1)[0][0] if difficulty_counts else 'Medium'
        workout_preferences['workout_count'] = len(recent_workouts)
    else:
        workout_preferences['favorite_type'] = 'Cardio'
        workout_preferences['preferred_difficulty'] = 'Medium'
        workout_preferences['workout_count'] = 0

    return render_template('workout.html',
                         username=session.get('username'),
                         user_stats=user_stats,
                         workout_preferences=workout_preferences,
                         custom_workouts=custom_workouts)

@app.route('/training-plan')
def training_plan():
    if 'user_id' not in session:
        flash('Please sign in to view your training plan.', 'error')      
        return redirect(url_for('get_started'))

    user_id = session['user_id']

    # Get user stats and workouts
    user_stats = UserStats.query.filter_by(user_id=user_id).first()
    if not user_stats:
        # Create default user stats if not exists
        user_stats = UserStats(
            user_id=user_id,
            current_streak=0,
            total_workouts=0,
            total_time_minutes=0,
            total_points=0,
            level=1
        )
        db.session.add(user_stats)
        db.session.commit()
    
    # Get recent workouts
    user_workouts = Workout.query.filter_by(user_id=user_id).order_by(Workout.completed_at.desc()).limit(10).all()
    
    # Get today's workout
    today = datetime.now().date()
    todays_workout = Workout.query.filter_by(user_id=user_id).filter(
        db.func.date(Workout.completed_at) == today
    ).first()
    
    # Calculate weekly workouts (last 7 days)
    week_ago = today - timedelta(days=7)
    weekly_workouts_count = Workout.query.filter_by(user_id=user_id).filter(
        Workout.completed_at >= week_ago
    ).count()
    
    # Create weekly schedule dictionary
    weekly_workouts = {
        'monday': 'Upper Body',
        'tuesday': 'Lower Body',
        'wednesday': 'Cardio',
        'thursday': 'Core',
        'friday': 'Full Body',
        'saturday': 'HIIT',
        'sunday': 'Rest'
    }
    
    # Update user stats with current weekly workouts
    user_stats.current_streak = weekly_workouts_count
    user_stats.total_workouts = len(user_workouts)
    user_stats.total_time_minutes = sum(w.duration_minutes for w in user_workouts)
    db.session.commit()
    
    # Calculate percentages for template
    weekly_percent = ((user_stats.current_streak or 0) / 7 * 100)
    level_percent = ((user_stats.level or 1) / 10 * 100)
    endurance_percent = (min(user_stats.total_workouts or 0, 20) / 20 * 100)
    weight_loss_percent = ((user_stats.total_points or 0) / 500 * 100)
    muscle_gain_percent = ((user_stats.level or 1) / 10 * 100)
    stamina_percent = (min((user_stats.total_time_minutes or 0) / 60, 25) / 25 * 100)
    
    # Get user goals
    active_goals = Goal.query.filter_by(user_id=user_id, is_active=True, is_completed=False).all()
    completed_goals = Goal.query.filter_by(user_id=user_id, is_completed=True).all()
    
    return render_template('training_plan.html',
                         username=session.get('username'),
                         user_stats=user_stats,
                         user_workouts=user_workouts,
                         weekly_workouts=weekly_workouts,
                         todays_workout=todays_workout,
                         active_goals=active_goals,
                         completed_goals=completed_goals,
                         weekly_percent=weekly_percent,
                         level_percent=level_percent,
                         endurance_percent=endurance_percent,
                         weight_loss_percent=weight_loss_percent,
                         muscle_gain_percent=muscle_gain_percent,
                         stamina_percent=stamina_percent)

# Goal Management Routes
@app.route('/goals')
def goals():
    if 'user_id' not in session:
        flash('Please sign in to view your goals.', 'error')
        return redirect(url_for('get_started'))
    
    # Redirect to training plan since goals are now integrated there
    return redirect(url_for('training_plan'))

@app.route('/add-goal', methods=['GET', 'POST'])
def add_goal():
    if 'user_id' not in session:
        flash('Please sign in to create goals.', 'error')
        return redirect(url_for('get_started'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        goal_type = request.form.get('goal_type')
        target_value = float(request.form.get('target_value'))
        unit = request.form.get('unit')
        target_date_str = request.form.get('target_date')
        
        # Parse target date
        target_date = None
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        
        # Create new goal
        new_goal = Goal(
            user_id=session['user_id'],
            title=title,
            description=description,
            goal_type=goal_type,
            target_value=target_value,
            current_value=0.0,
            unit=unit,
            target_date=target_date
        )
        
        db.session.add(new_goal)
        db.session.commit()
        
        # Create activity log
        activity = Activity(
            user_id=session['user_id'],
            activity_type='goal_created',
            title=f'Goal Created: {title}',
            description=f'Created new goal: {title}',
            points_earned=0
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Goal created successfully!', 'success')
        return redirect(url_for('training_plan'))
    
    return redirect(url_for('training_plan'))

@app.route('/update-goal/<int:goal_id>', methods=['POST'])
def update_goal(goal_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    goal = Goal.query.filter_by(id=goal_id, user_id=session['user_id']).first()
    if not goal:
        return jsonify({'error': 'Goal not found'}), 404
    
    try:
        new_value = float(request.form.get('current_value'))
        goal.current_value = new_value
        
        # Check if goal is completed
        if new_value >= goal.target_value:
            goal.is_completed = True
            goal.completed_at = datetime.now()
            
            # Award points for completing goal
            points_awarded = int(goal.target_value * 10)  # 10 points per target unit
            
            # Update user stats
            user_stats = UserStats.query.filter_by(user_id=session['user_id']).first()
            if user_stats:
                user_stats.total_points += points_awarded
            
            # Create activity log
            activity = Activity(
                user_id=session['user_id'],
                activity_type='goal_completed',
                title=f'Goal Completed: {goal.title}',
                description=f'Completed goal: {goal.title}',
                points_earned=points_awarded
            )
            db.session.add(activity)
            
            flash(f'Congratulations! Goal completed and earned {points_awarded} points! 🎉', 'success')
        
        db.session.commit()
        return jsonify({'success': True, 'is_completed': goal.is_completed})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/delete-goal/<int:goal_id>', methods=['POST'])
def delete_goal(goal_id):
    if 'user_id' not in session:
        flash('Please sign in to manage goals.', 'error')
        return redirect(url_for('get_started'))
    
    goal = Goal.query.filter_by(id=goal_id, user_id=session['user_id']).first()
    if not goal:
        flash('Goal not found.', 'error')
        return redirect(url_for('training_plan'))
    
    db.session.delete(goal)
    db.session.commit()
    
    flash('Goal deleted successfully.', 'success')
    return redirect(url_for('training_plan'))

@app.route('/activity')
def activity():
    if 'user_id' not in session:
        flash('Please sign in to view your activity.', 'error')
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']
    
    # Get user stats and all activities
    user_stats = UserStats.query.filter_by(user_id=user_id).first()
    user_activities = Activity.query.filter_by(user_id=user_id).order_by(Activity.created_at.desc()).all()
    
    # Calculate monthly stats
    from datetime import datetime, timedelta
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_workouts = Workout.query.filter_by(user_id=user_id).filter(
        Workout.completed_at >= month_start
    ).all()
    
    monthly_stats = {
        'workout_count': len(monthly_workouts),
        'total_time_minutes': sum(w.duration_minutes for w in monthly_workouts),
        'points_earned': sum(w.points_earned for w in monthly_workouts)
    }
    
    return render_template('activity.html',
                         username=session.get('username'),
                         user_stats=user_stats,
                         activities=user_activities,
                         monthly_stats=monthly_stats)

@app.route('/challenges')
def challenges():
    if 'user_id' not in session:
        flash('Please sign in to view challenges.', 'error')
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']
    
    # Get user stats and challenges
    user_stats = UserStats.query.filter_by(user_id=user_id).first()
    
    # Get active challenges
    active_challenges = db.session.query(UserChallenge, Challenge).join(Challenge).filter(
        UserChallenge.user_id == user_id,
        UserChallenge.is_completed == False
    ).all()
    
    # Get available challenges (not joined yet)
    joined_challenge_ids = [uc.challenge_id for uc, _ in active_challenges]
    available_challenges = Challenge.query.filter(~Challenge.id.in_(joined_challenge_ids)).all()
    
    # Get completed challenges
    completed_challenges = db.session.query(UserChallenge, Challenge).join(Challenge).filter(
        UserChallenge.user_id == user_id,
        UserChallenge.is_completed == True
    ).order_by(UserChallenge.completed_at.desc()).limit(10).all()
    
    # Calculate gold medals (completed challenges with gold badge or high points)
    gold_medals = 0
    for user_challenge, challenge in completed_challenges:
        if challenge.badge_name == 'gold' or challenge.points_reward >= 100:
            gold_medals += 1
    
    return render_template('challenges.html', 
                         username=session.get('username'),
                         user_stats=user_stats,
                         active_challenges=active_challenges,
                         available_challenges=available_challenges,
                         completed_challenges=completed_challenges,
                         gold_medals=gold_medals)

# Action Routes
@app.route('/complete-workout', methods=['POST'])
def complete_workout():
    if 'user_id' not in session:
        flash('Please sign in to complete a workout.', 'error')
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']
    workout_type = request.form.get('workout_type')
    duration = int(request.form.get('duration', 30))
    difficulty = request.form.get('difficulty', 'Medium')
    
    # Calculate points based on duration and difficulty
    difficulty_multipliers = {'Easy': 1, 'Medium': 1.5, 'Hard': 2, 'Intense': 2.5}
    base_points = duration * 2  # 2 points per minute
    points_earned = int(base_points * difficulty_multipliers.get(difficulty, 1.5))
    
    try:
        # Create workout record
        workout = Workout(
            user_id=user_id,
            workout_type=workout_type,
            duration_minutes=duration,
            difficulty=difficulty,
            points_earned=points_earned
        )
        db.session.add(workout)
        
        # Update user stats
        user_stats = UserStats.query.filter_by(user_id=user_id).first()
        if user_stats:
            user_stats.total_workouts += 1
            user_stats.total_time_minutes += duration
            user_stats.total_points += points_earned
            
            # Check for level up (100 points per level)
            new_level = (user_stats.total_points // 100) + 1
            if new_level > user_stats.level:
                user_stats.level = new_level
                flash(f'🎉 Level Up! You\'re now level {new_level}!', 'success')
            
            # Update streak (check if workout today)
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            # Get last workout date
            last_workout = Workout.query.filter_by(user_id=user_id).order_by(Workout.completed_at.desc()).offset(1).first()
            if last_workout and last_workout.completed_at.date() == yesterday:
                user_stats.current_streak += 1
            elif not last_workout or last_workout.completed_at.date() < yesterday:
                user_stats.current_streak = 1
            
            db.session.commit()
        
        # Create activity record
        activity = Activity(
            user_id=user_id,
            activity_type='workout',
            title=f'Completed {workout_type} Workout',
            description=f'{duration} minute {difficulty.lower()} {workout_type} session',
            points_earned=points_earned
        )
        db.session.add(activity)
        
        # Update challenge progress
        workout_challenges = db.session.query(UserChallenge, Challenge).join(Challenge).filter(
            UserChallenge.user_id == user_id,
            UserChallenge.is_completed == False,
            Challenge.challenge_type.in_(['workout_count', 'streak', 'weekly_goal'])
        ).all()
        
        for user_challenge, challenge in workout_challenges:
            if challenge.challenge_type == 'workout_count':
                user_challenge.current_progress += 1
            elif challenge.challenge_type == 'streak':
                user_challenge.current_progress = user_stats.current_streak
            elif challenge.challenge_type == 'weekly_goal':
                # Check if workout was this week
                if workout.completed_at.date().isocalendar().week == datetime.now().date().isocalendar().week:
                    # Count workouts this week
                    week_workouts = Workout.query.filter(
                        Workout.user_id == user_id,
                        Workout.completed_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=datetime.now().weekday())
                    ).count()
                    user_challenge.current_progress = week_workouts
            
            # Check if challenge is completed
            if user_challenge.current_progress >= challenge.target_value:
                user_challenge.is_completed = True
                user_challenge.completed_at = datetime.now()
                user_stats.total_points += challenge.points_reward
                
                # Create achievement activity
                achievement = Activity(
                    user_id=user_id,
                    activity_type='achievement',
                    title=f'🏆 Challenge Completed: {challenge.name}',
                    description=f'Earned {challenge.points_reward} points and {challenge.badge_name}',
                    points_earned=challenge.points_reward
                )
                db.session.add(achievement)
        
        db.session.commit()
        flash(f'🔥 Workout completed! +{points_earned} points earned!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/delete-custom-workout/<int:workout_id>', methods=['POST'])
def delete_custom_workout(workout_id):
    if 'user_id' not in session:
        flash('Please sign in to delete workouts.', 'error')
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']
    
    # Get the custom workout to delete
    workout = CustomWorkout.query.filter_by(id=workout_id, user_id=user_id).first()
    
    if workout:
        db.session.delete(workout)
        db.session.commit()
        flash('🗑️ Workout deleted successfully!', 'success')
    else:
        flash('Workout not found.', 'error')
    
    return redirect(url_for('my_custom_workouts'))

@app.route('/my-custom-workouts')
def my_custom_workouts():
    if 'user_id' not in session:
        flash('Please sign in to view your custom workouts.', 'error')
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']
    
    # Get all custom workouts for this user
    custom_workouts_db = CustomWorkout.query.filter_by(user_id=user_id).order_by(CustomWorkout.created_at.desc()).all()
    custom_workouts = []
    for workout in custom_workouts_db:
        custom_workouts.append({
            'id': workout.id,
            'name': workout.name,
            'duration_minutes': workout.duration_minutes,
            'difficulty': workout.difficulty,
            'workout_type': workout.workout_type,
            'exercises': workout.exercises,
            'description': workout.description,
            'created_at': workout.created_at
        })
    
    return render_template('my_custom_workouts.html',
                         username=session.get('username'),
                         custom_workouts=custom_workouts)

@app.route('/create-custom-workout', methods=['POST'])
def create_custom_workout():
    if 'user_id' not in session:
        flash('Please sign in to create a custom workout.', 'error')
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']
    name = request.form.get('name')
    duration = int(request.form.get('duration', 30))
    difficulty = request.form.get('difficulty')
    workout_type = request.form.get('type')
    exercises = request.form.get('exercises')
    description = request.form.get('description')
    
    try:
        # Create custom workout record
        custom_workout = CustomWorkout(
            user_id=user_id,
            name=name,
            duration_minutes=duration,
            difficulty=difficulty,
            workout_type=workout_type,
            exercises=exercises,
            description=description
        )
        db.session.add(custom_workout)
        db.session.commit()
        
        flash(f'🎨 Custom workout "{name}" created successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while creating your custom workout. Please try again.', 'error')
    
    return redirect(url_for('start_workout'))

@app.route('/join-challenge/<int:challenge_id>', methods=['POST'])
def join_challenge(challenge_id):
    if 'user_id' not in session:
        flash('Please sign in to join challenges.', 'error')
        return redirect(url_for('get_started'))
    
    user_id = session['user_id']
    
    try:
        # Check if user already joined this challenge
        existing = UserChallenge.query.filter_by(user_id=user_id, challenge_id=challenge_id).first()
        if existing:
            flash('You have already joined this challenge!', 'info')
            return redirect(url_for('challenges'))
        
        # Create user challenge
        user_challenge = UserChallenge(user_id=user_id, challenge_id=challenge_id)
        db.session.add(user_challenge)
        
        # Get challenge details for activity
        challenge = Challenge.query.get(challenge_id)
        
        # Create activity
        activity = Activity(
            user_id=user_id,
            activity_type='challenge',
            title=f'🎯 Joined Challenge: {challenge.name}',
            description=challenge.description,
            points_earned=0
        )
        db.session.add(activity)
        
        db.session.commit()
        flash(f'🎯 Successfully joined: {challenge.name}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('challenges'))

if __name__ == '__main__':
    app.run(debug=True)
