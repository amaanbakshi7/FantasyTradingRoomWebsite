from flask import Flask, request, render_template, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import bcrypt
import secrets
import datetime
import pymysql
pymysql.install_as_MySQLdb()


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sql3672369:F5Gxn5CUcf@sql3.freemysqlhosting.net:3306/sql3672369'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ftrhelp123@gmail.com'  # Replace with your Gmail email
app.config['MAIL_PASSWORD'] = 'hffc kwpb ihwd dkqi'  # Replace with your Gmail password

mail = Mail(app)

db = SQLAlchemy(app)
app.secret_key = 'secret_key'


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    reset_token = db.Column(db.String(50), unique=True, default=None)
    reset_token_expiration = db.Column(db.DateTime, default=None)

    def __init__(self, email, password, name):
        self.name = name
        self.email = email
        self.password = password
        self.reset_token = None
        self.reset_token_expiration = None

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(10)
        self.reset_token_expiration = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        db.session.commit()
        return self.reset_token

    def check_reset_token_validity(self):
        return self.reset_token_expiration > datetime.datetime.utcnow()


    def check_password(self, password):
        # Replace this with your actual password checking logic
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/locked')
def locked():
    return render_template('locked.html')


@app.route('/locked2')
def locked2():
    return render_template('locked2.html')


@app.route('/exclusive')
def exclusive():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()

        if user:
            return render_template('exclusive.html', user=user)

        else:
            return render_template('error.html', error='User not found')
    else:
        return redirect('/locked2')


@app.route('/rankings')
def rankings():
    return render_template('rankings.html')


@app.route('/article1')
def article1():
    return render_template('article1.html')


@app.route('/article2')
def article2():
    return render_template('article2.html')


@app.route('/article3')
def article3():
    return render_template('article3.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()

        if user:
            return render_template('dashboard.html', user=user)


    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('Email already associated with an account. Please use a different email.', 'danger')
            return redirect('/register')
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        new_user = User(name=name, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect('/login')

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()

        if user:
            return render_template('dashboard.html', user=user)

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email'] = user.email
            flash('Login successful!', 'success')
            return redirect('/dashboard')
        else:
            flash('Login failed. Please check your email and password.', 'error')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'email' in session:
        user = User.query.filter_by(email=session['email']).first()

        if user:
            return render_template('dashboard.html', user=user)

        else:
            return render_template('locked.html')
    else:
        return redirect('/locked')


@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('Logout successful!', 'success')
    return redirect('/login')


@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            reset_token = user.generate_reset_token()

            reset_link = f"{request.url_root}reset/{reset_token}"

            subject = "Password Reset Request"
            body = f"Hi {user.name},\n You recently requested to reset the password for your Fantasy Trading Room account. Click the link to proceed.{reset_link} If you did not request a password reset, please ignore this email or reply to let us know. This password reset link is only valid for the next 30 minutes. \nThanks, the Fantasy Trading Room team "
            msg = Message(subject=subject,sender='ftrhelp123@gmail.com', recipients=[email], body=body)
            mail.send(msg)

            flash('Password reset email sent. Check your inbox.', 'success')
            return redirect('/login')
        else:
            flash('No user found with that email address.', 'error')

    return render_template('forgot.html')


@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if user and user.check_reset_token_validity():
        if request.method == 'POST':
            new_password = bcrypt.hashpw(request.form['new_password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            user.password = new_password
            user.reset_token = None
            user.reset_token_expiration = None
            db.session.commit()

            flash('Password reset successful. You can now log in with your new password.', 'success')
            return redirect('/login')

        return render_template('reset_password.html', token=token)
    else:
        flash('Invalid or expired reset link.', 'error')
        return redirect('/login')


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000)
