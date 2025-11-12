from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///coachsmart.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class TrainingPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sport = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    intensity = db.Column(db.String(50), nullable=False)  # low, medium, high
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<TrainingPlan {self.sport} - {self.intensity}>"

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    plans = TrainingPlan.query.order_by(TrainingPlan.date.desc()).all()
    return render_template('index.html', plans=plans)

@app.route('/plan/add', methods=['GET', 'POST'])
def add_plan():
    if request.method == 'POST':
        sport = request.form.get('sport')
        duration = request.form.get('duration')
        intensity = request.form.get('intensity')
        notes = request.form.get('notes', '')
        
        if not all([sport, duration, intensity]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('add_plan'))
        
        try:
            plan = TrainingPlan(
                sport=sport,
                duration=int(duration),
                intensity=intensity,
                notes=notes
            )
            db.session.add(plan)
            db.session.commit()
            flash('Training plan added successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            
    return render_template('add_plan.html')

@app.route('/plan/<int:plan_id>/edit', methods=['GET', 'POST'])
def edit_plan(plan_id):
    plan = TrainingPlan.query.get_or_404(plan_id)
    
    if request.method == 'POST':
        plan.sport = request.form.get('sport', plan.sport)
        plan.duration = int(request.form.get('duration', plan.duration))
        plan.intensity = request.form.get('intensity', plan.intensity)
        plan.notes = request.form.get('notes', plan.notes)
        
        try:
            db.session.commit()
            flash('Training plan updated successfully!', 'success')
            return redirect(url_for('index'))
        except:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('edit_plan.html', plan=plan)

@app.route('/plan/<int:plan_id>/delete', methods=['POST'])
def delete_plan(plan_id):
    plan = TrainingPlan.query.get_or_404(plan_id)
    
    try:
        db.session.delete(plan)
        db.session.commit()
        flash('Training plan deleted successfully!', 'success')
    except:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
    
    return redirect(url_for('index'))

@app.route('/ai-coach')
def ai_coach():
    # Basic AI Coach logic - can be enhanced later
    plans = TrainingPlan.query.all()
    total_duration = sum(plan.duration for plan in plans)
    avg_intensity = sum(1 if plan.intensity == 'high' else 0.5 if plan.intensity == 'medium' else 0.25 for plan in plans) / len(plans) if plans else 0
    
    feedback = ""
    if avg_intensity > 0.7:
        feedback = "You're training hard! Don't forget to include rest days for recovery."
    elif avg_intensity > 0.4:
        feedback = "Great consistency! Keep up the good work and listen to your body."
    else:
        feedback = "Consider increasing your training intensity for better results. You've got this!"
    
    return render_template('ai_coach.html', feedback=feedback, total_duration=total_duration)

if __name__ == '__main__':
    app.run(debug=True)
