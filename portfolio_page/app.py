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
        'technologies': ['python', 'scikit-learn', 'Data Wrangling', 'Feature importance'],
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
        'technologies': ['python', 'scikit-learn', 'TensorFlow'],
        'links': {
            'thesis': 'https://www.diva-portal.org/smash/record.jsf?dswid=6950&pid=diva2%3A1635754&c=1&searchType=SIMPLE&language=en&query=%22Erik+Wendel%22+%22Patrik+Svensson%22&af=%5B%5D&aq=%5B%5B%5D%5D&aq2=%5B%5B%5D%5D&aqe=%5B%5D&noOfRows=50&sortOrder=author_sort_asc&sortOrder2=title_sort_asc&onlyFullText=false&sf=all',
            'pdf': 'pdfs/BachelorThesisSvenssonWendel.pdf'
        }
    },
    'lung-segmentation': {
        'title': 'Lung segmentation using Neural Networks',
        'image': 'project3.JPG',
        'description': 'Designing a neural network to segment lungs in CT scans. Model was deployed in a Docker container and accessed using CLI.',
        'content': '''
            <p>This project focused on developing a neural network model for automated lung segmentation in CT scans, with a focus on deployment and accessibility.</p>
            
            <h2>Key Features</h2>
            <ul>
                <li>Developed a custom neural network architecture for lung segmentation</li>
                <li>Containerized the model using Docker for easy deployment</li>
                <li>Created a CLI interface for model interaction</li>
                <li>Implemented robust data preprocessing pipeline</li>
            </ul>
            
            <h2>Technical Details</h2>
            <p>The project utilized TensorFlow for the neural network implementation and Docker for containerization. The model was trained on a curated dataset of CT scans and validated against expert annotations.</p>
        ''',
        'technologies': ['python','Tensorflow', 'keras', 'Docker'],
        'links': {}
    },
    'kth-project': {
        'title': 'SW responsible for KTH project',
        'image': 'project3.JPG',
        'description': 'Software responsible for a group project at KTH where we built an automatic plant watering and lighting system.',
        'content': '''
            <p>Led the software development for an automated plant care system at KTH, focusing on system integration and control logic.</p>
            
            <h2>Key Features</h2>
            <ul>
                <li>Developed control software for automated plant care system</li>
                <li>Implemented sensor integration and actuator control</li>
                <li>Created user interface for system monitoring</li>
                <li>Managed team coordination and project planning</li>
            </ul>
            
            <h2>Technical Details</h2>
            <p>The project combined C++ for the main control logic with Arduino for hardware interaction. The system included sensors for soil moisture and light levels, controlling water pumps and LED lights accordingly.</p>
        ''',
        'technologies': ['C++', 'Arduino', 'Soft skills'],
        'links': {}
    },
    'housebot': {
        'title': 'HouseBot',
        'image': 'project5.JPG',
        'description': 'Made a script that scrapes a specific website for new apartment ads and sends them to a Discord server.',
        'content': '''
            <p>Developed an automated apartment hunting assistant that monitors housing websites and notifies users through Discord.</p>
            
            <h2>Key Features</h2>
            <ul>
                <li>Automated web scraping of housing websites</li>
                <li>Real-time Discord notifications</li>
                <li>Multi-threaded design for efficient monitoring</li>
                <li>Customizable search criteria</li>
            </ul>
            
            <h2>Technical Details</h2>
            <p>The project utilized Python for web scraping and API integration with Discord. The multi-threaded design ensures efficient monitoring of multiple housing websites simultaneously.</p>
        ''',
        'technologies': ['API calls', 'Web Scraping', 'python', 'Threading'],
        'links': {}
    },
    'nightscout': {
        'title': 'Nightscout',
        'image': 'project6.JPG',
        'description': 'Set up a server to host a website that displays my blood sugar data. Not my code design but I learnt about server management and data flows.',
        'content': '''
            <p>Implemented and managed a Nightscout server for continuous glucose monitoring data visualization. </p>
            
            <h2>Key Features</h2>
            <ul>
                <li>Server setup and configuration</li>
                <li>Database management and optimization</li>
                <li>Data flow implementation</li>
                <li>System monitoring and maintenance</li>
            </ul>
            
            <h2>Technical Details</h2>
            <p>The project involved setting up and managing a MongoDB database, implementing data flows from glucose monitoring devices, and ensuring reliable server operation.</p>
        ''',
        'technologies': ['Databases', 'Server Management', 'MongoDB'],
        'links': {}
    },
    # Add more projects here...
}

@app.route('/')
def home():
    try:
        return render_template('home.html', projects=projects)
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
def projects_page():
    try:
        return render_template('projects.html', projects=projects)
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

@app.route('/neonatal-brain-maturation')
def project1():
    try:
        logger.info("Attempting to render project1 page")
        project = projects.get('neonatal-brain-maturation')
        logger.info(f"Project data retrieved: {project}")
        if project:
            return render_template('project1.html', project=project)
        else:
            logger.error("Project not found")
            return render_template('404.html'), 404
    except Exception as e:
        logger.error(f"Error rendering project1: {str(e)}", exc_info=True)
        return render_template('500.html'), 500

@app.route('/activity-recognition')
def project2():
    try:
        logger.info("Attempting to render project2 page")
        project = projects.get('activity-recognition')
        logger.info(f"Project data retrieved: {project}")
        if project:
            return render_template('project2.html', project=project)
        else:
            logger.error("Project not found")
            return render_template('404.html'), 404
    except Exception as e:
        logger.error(f"Error rendering project2: {str(e)}", exc_info=True)
        return render_template('500.html'), 500

@app.route('/lung-segmentation')
def project3():
    try:
        logger.info("Attempting to render project3 page")
        project = projects.get('lung-segmentation')
        logger.info(f"Project data retrieved: {project}")
        if project:
            return render_template('project3.html', project=project)
        else:
            logger.error("Project not found")
            return render_template('404.html'), 404
    except Exception as e:
        logger.error(f"Error rendering project3: {str(e)}", exc_info=True)
        return render_template('500.html'), 500

@app.route('/kth-project')
def project4():
    try:
        logger.info("Attempting to render project4 page")
        project = projects.get('kth-project')
        logger.info(f"Project data retrieved: {project}")
        if project:
            return render_template('project4.html', project=project)
        else:
            logger.error("Project not found")
            return render_template('404.html'), 404
    except Exception as e:
        logger.error(f"Error rendering project4: {str(e)}", exc_info=True)
        return render_template('500.html'), 500

@app.route('/housebot')
def project5():
    try:
        logger.info("Attempting to render project5 page")
        project = projects.get('housebot')
        logger.info(f"Project data retrieved: {project}")
        if project:
            return render_template('project5.html', project=project)
        else:
            logger.error("Project not found")
            return render_template('404.html'), 404
    except Exception as e:
        logger.error(f"Error rendering project5: {str(e)}", exc_info=True)
        return render_template('500.html'), 500

@app.route('/nightscout')
def project6():
    try:
        logger.info("Attempting to render project6 page")
        project = projects.get('nightscout')
        logger.info(f"Project data retrieved: {project}")
        if project:
            return render_template('project6.html', project=project)
        else:
            logger.error("Project not found")
            return render_template('404.html'), 404
    except Exception as e:
        logger.error(f"Error rendering project6: {str(e)}", exc_info=True)
        return render_template('500.html'), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.railway.app;"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)  # Enable debug mode 