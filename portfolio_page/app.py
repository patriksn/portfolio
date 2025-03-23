from flask import Flask, render_template, request, flash, redirect, url_for, abort
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
        'style-src': ["'self'", "'unsafe-inline'", "cdnjs.cloudflare.com"],
        'img-src': ["'self'", "data:", "https:", "via.placeholder.com"],
        'font-src': ["'self'", "cdnjs.cloudflare.com"],
    },
    force_https=False  # Allow HTTP for development
)

mail = Mail(app)

# Project data
projects = {
    'neonatal-brain-maturation': {
        'title': 'Estimating neonatal brain maturation with explainable ML',
        'image': 'project1.JPG',
        'description': 'Developed an explainable ML model to predict the maturation of the brain in preterm neonates based on EEG data.',
        'content': '''
            <p>This project focused on developing a machine learning model to predict brain maturation in preterm neonates using EEG data. The model was designed to be explainable, allowing healthcare professionals to understand its decision-making process.</p>
            
            <h2>Key Features</h2>
            <ul>
                <li>Developed an explainable ML model that performed comparably to expert doctors</li>
                <li>Implemented feature importance analysis to identify key EEG patterns</li>
                <li>Created a robust data pipeline for processing and analyzing EEG data</li>
                <li>Utilized scikit-learn for model development and evaluation</li>
            </ul>
            
            <h2>Technical Details</h2>
            <p>The project involved extensive data wrangling and feature engineering to extract meaningful patterns from EEG data. The model was trained on a carefully curated dataset and validated against expert assessments.</p>
        ''',
        'technologies': ['python Notebook', 'scikit-learn', 'Data Wrangling', 'Feature importance'],
        'links': {
            'thesis': 'https://www.diva-portal.org/smash/record.jsf?dswid=9279&pid=diva2%3A1768830&c=18&searchType=SIMPLE&language=en&query=%22patrik+svensson%22&af=%5B%5D&aq=%5B%5B%5D%5D&aq2=%5B%5B%5D%5D&aqe=%5B%5D&noOfRows=50&sortOrder=author_sort_asc&sortOrder2=title_sort_asc&onlyFullText=true&sf=undergraduate'
        }
    },
    'activity-recognition': {
        'title': 'Human activity recognition with CNN and SVM',
        'image': 'project2.JPG',
        'description': 'Developing a CNN and a SVM model to classify human activity based on accelerometer and gyroscope data.',
        'content': '''
            <p>This project involved developing and comparing two different machine learning approaches for human activity recognition using sensor data.</p>
            
            <h2>Key Features</h2>
            <ul>
                <li>Implemented both CNN and SVM models for activity classification</li>
                <li>Collected and processed accelerometer and gyroscope data</li>
                <li>Developed a comprehensive data collection protocol</li>
                <li>Created a detailed mathematical framework for ML theory</li>
            </ul>
            
            <h2>Technical Details</h2>
            <p>The project utilized TensorFlow for the CNN implementation and scikit-learn for the SVM model. A significant portion of the work focused on data collection and preprocessing to ensure high-quality input for the models.</p>
        ''',
        'technologies': ['python Notebook', 'scikit-learn', 'TensorFlow', 'Data Collection', 'ML Mathematical Theory'],
        'links': {
            'thesis': 'https://www.diva-portal.org/smash/record.jsf?dswid=6950&pid=diva2%3A1635754&c=1&searchType=SIMPLE&language=en&query=%22Erik+Wendel%22+%22Patrik+Svensson%22&af=%5B%5D&aq=%5B%5B%5D%5D&aq2=%5B%5B%5D%5D&aqe=%5B%5D&noOfRows=50&sortOrder=author_sort_asc&sortOrder2=title_sort_asc&onlyFullText=false&sf=all',
            'pdf': 'pdfs/bachelors_thesis.pdf'
        }
    },
    # Add more projects here...
}

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

@app.route('/project/<project_id>')
def project_detail(project_id):
    project = projects.get(project_id)
    if project is None:
        abort(404)
    return render_template('project_detail.html', project=project)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 