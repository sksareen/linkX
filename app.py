from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import os
from dotenv import load_dotenv
import tweepy
from functools import wraps
import logging
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///linkx.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'mp4', 'webm', 'mov'}

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# X API Configuration
api_key = os.getenv('X_API_KEY')
api_secret = os.getenv('X_API_SECRET')
callback_url = os.getenv('X_CALLBACK_URL')

logger.debug(f"API Key length: {len(api_key) if api_key else 'None'}")
logger.debug(f"API Secret length: {len(api_secret) if api_secret else 'None'}")
logger.debug(f"Callback URL: {callback_url}")

# Create OAuth 1.0a handler
oauth1_user_handler = tweepy.OAuth1UserHandler(
    api_key, api_secret,
    callback=callback_url
)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    x_id = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(120), unique=True, nullable=False)
    links = db.relationship('Link', backref='user', lazy=True)

class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    demo_url = db.Column(db.String(500))  # Video demo URL
    github_url = db.Column(db.String(500))  # GitHub repo URL
    webapp_url = db.Column(db.String(500))  # Live webapp URL
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    description = db.Column(db.String(1000))  # Added description for better previews

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
@app.route('/<username>')
def index(username=None):
    if username:
        user = User.query.filter_by(username=username).first_or_404()
        return render_template('index.html', profile_user=user)
    return render_template('index.html')

@app.route('/login')
def login():
    try:
        logger.debug("Starting login process...")
        authorization_url = oauth1_user_handler.get_authorization_url()
        logger.debug(f"Got authorization URL: {authorization_url}")
        session['request_token'] = oauth1_user_handler.request_token
        return redirect(authorization_url)
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return f'Error during login process: {str(e)}'

@app.route('/callback')
def callback():
    try:
        verifier = request.args.get('oauth_verifier')
        request_token = session.get('request_token')
        
        if not verifier or not request_token:
            logger.error("Missing verifier or request token")
            return redirect(url_for('index'))

        # Remove request token from session
        session.pop('request_token', None)

        # Get the access token
        access_token, access_token_secret = oauth1_user_handler.get_access_token(verifier)
        
        # Create API client
        client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret
        )
        
        # Get user info
        user_data = client.get_me()
        
        # Create or get user
        user = User.query.filter_by(x_id=str(user_data.data.id)).first()
        if not user:
            user = User(x_id=str(user_data.data.id), username=user_data.data.username)
            db.session.add(user)
            db.session.commit()
        
        session['user_id'] = user.id
        return redirect(url_for('dashboard'))
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return f'Error during authentication: {str(e)}'

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/links', methods=['GET', 'POST'])
@login_required
def links():
    if request.method == 'POST':
        demo_url = request.form.get('demo_url')
        video_file = request.files.get('video_file')
        
        # Handle video file upload
        if video_file and video_file.filename != '':
            if allowed_file(video_file.filename):
                filename = secure_filename(video_file.filename)
                video_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                demo_url = url_for('uploaded_file', filename=filename, _external=True)
        
        link = Link(
            title=request.form['title'],
            demo_url=demo_url,
            github_url=request.form.get('github_url'),
            webapp_url=request.form.get('webapp_url'),
            description=request.form.get('description'),
            user_id=session['user_id']
        )
        db.session.add(link)
        db.session.commit()
        return redirect(url_for('dashboard'))
    
    user = User.query.get(session['user_id'])
    return jsonify([{
        'id': link.id,
        'title': link.title,
        'demo_url': link.demo_url,
        'github_url': link.github_url,
        'webapp_url': link.webapp_url,
        'description': link.description,
        'created_at': link.created_at.isoformat()
    } for link in user.links])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/links/<int:user_id>')
def user_links(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify([{
        'id': link.id,
        'title': link.title,
        'demo_url': link.demo_url,
        'github_url': link.github_url,
        'webapp_url': link.webapp_url,
        'description': link.description,
        'created_at': link.created_at.isoformat()
    } for link in user.links])

@app.route('/embed/<int:link_id>')
def embed(link_id):
    link = Link.query.get_or_404(link_id)
    # Return an HTML page optimized for X card preview
    return render_template('embed.html', link=link)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    app.run(debug=True, port=port)
