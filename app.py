from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
import os

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration settings
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'S)83@Jp0LqE0=pufzcI=jcW*0B#XLoBd6+g=y6P*rQ=8dpYfZ')
app.secret_key = os.getenv('SECRET_KEY', 'xNFzG46=+^CCqwTcMge07q-$5GZ^1vbNm$JBPvRMx2zY#Fb2D*')

# Initialize SQLAlchemy, Migrate, and JWTManager
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)


from models import User

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    username = jwt_data['sub']['username'] 
    return User.query.filter_by(username=username).one_or_none()


# Create the uploads directory if it does not exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Import and register blueprints
from auth import auth as auth_blueprint
from admin import admin as admin_blueprint
from user import user as user_blueprint

app.register_blueprint(user_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(admin_blueprint)

# Simple home route
@app.route('/')
def home():
    return jsonify(message="Welcome to Quiet Library Tracker API")

# Error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify(message="Resource not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify(message="An internal error occurred"), 500

if __name__ == '__main__':
    app.run(debug=True)
