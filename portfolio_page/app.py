from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from email_validator import validate_email, EmailNotValidError
import os
from flask_mail import Mail, Message

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Security Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv('CSRF_SECRET_KEY', 'csrf-secret-key')

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASSWORD')

# Initialize security extensions
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
Talisman(app, 
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "cdn.tailwindcss.com"],
        'style-src': ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com"],
        'img-src': ["'self'", "data:", "https:", "via.placeholder.com"],
        'font-src': ["'self'", "cdnjs.cloudflare.com"],
    }
)

mail = Mail(app)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/contact', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        # Validate inputs
        if not all([name, email, subject, message]):
            flash('All fields are required.', 'error')
            return redirect(url_for('contact'))

        try:
            validate_email(email)
        except EmailNotValidError:
            flash('Invalid email address.', 'error')
            return redirect(url_for('contact'))

        try:
            # Create email message
            msg = Message(
                subject=f'Portfolio Contact: {subject}',
                sender=email,
                recipients=[os.getenv('EMAIL_USER')]
            )
            msg.body = f"""
            From: {name}
            Email: {email}
            Subject: {subject}
            
            Message:
            {message}
            """

            # Send email
            mail.send(msg)
            flash('Your message has been sent successfully!', 'success')
            return redirect(url_for('contact'))

        except Exception as e:
            flash('An error occurred. Please try again later.', 'error')
            return redirect(url_for('contact'))

    return render_template('contact.html')

if __name__ == '__main__':
    app.run(debug=False)  # Set debug to False in production 