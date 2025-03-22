from flask import Flask, render_template, request, flash, redirect, url_for
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from email_validator import validate_email, EmailNotValidError
import os
from flask_mail import Mail, Message
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Initialize rate limiter with fallback
try:
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"  # Use in-memory storage instead of Redis
    )
except Exception as e:
    logger.warning(f"Rate limiter initialization failed: {str(e)}")
    limiter = None

# Configure Talisman with more permissive settings for Railway
Talisman(app, 
    content_security_policy={
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "cdn.tailwindcss.com"],
        'style-src': ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com", "use.fontawesome.com"],
        'img-src': ["'self'", "data:", "https:", "via.placeholder.com"],
        'font-src': ["'self'", "cdnjs.cloudflare.com", "use.fontawesome.com"],
    },
    force_https=False  # Allow HTTP for development
)

mail = Mail(app)

@app.route('/')
def home():
    try:
        return render_template('home.html')
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}")
        return "An error occurred", 500

@app.route('/about')
def about():
    try:
        return render_template('about.html')
    except Exception as e:
        logger.error(f"Error rendering about page: {str(e)}")
        return "An error occurred", 500

@app.route('/projects')
def projects():
    try:
        return render_template('projects.html')
    except Exception as e:
        logger.error(f"Error rendering projects page: {str(e)}")
        return "An error occurred", 500

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    try:
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
                logger.error(f"Error sending email: {str(e)}")
                flash('An error occurred. Please try again later.', 'error')
                return redirect(url_for('contact'))

        return render_template('contact.html')
    except Exception as e:
        logger.error(f"Error in contact route: {str(e)}")
        return "An error occurred", 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 