from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tugasku.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    deadline = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route('/')
def index():
    if 'user_id' in session:
        tasks = Task.query.filter_by(user_id=session['user_id']).all()
        return render_template('dashboard.html', tasks=tasks)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, role=role, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/task/new', methods=['GET', 'POST'])
def new_task():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        try:
            deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('new_task'))
        
        new_task = Task(title=title, description=description, deadline=deadline, user_id=session['user_id'])
        db.session.add(new_task)
        db.session.commit()
        flash('Task added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('new_task.html')

@app.route('/task/edit/<int:id>', methods=['GET', 'POST'])
def edit_task(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        try:
            task.deadline = datetime.strptime(request.form['deadline'], '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return redirect(url_for('edit_task', id=id))
        db.session.commit()
        flash('Task updated successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('edit_task.html', task=task)


@app.route('/task/delete/<int:id>')
def delete_task(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/logout', methods=['GET'])
def logout_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))  
    return render_template('logout.html')

@app.route('/logout/confirm', methods=['GET'])
def logout_confirm():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
