from flask import Blueprint, request, jsonify
from bcrypt import gensalt, hashpw, checkpw
from models import User
from app import db
from flask_jwt_extended import create_access_token

auth = Blueprint('auth', __name__)

def hash_password(password):
    salt = gensalt()
    return hashpw(password.encode('utf-8'), salt)


def check_password(stored_password, provided_password):
    return checkpw(provided_password.encode('utf-8'), stored_password)


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()

    if not user or not check_password(user.password, data['password']):
        return jsonify({'message': 'Invalid username or password!'}), 401

    access_token = create_access_token(identity={'username': user.username, 'role': user.role})

    redirect_url = 'user-dashboard'  
    if user.role == 'admin':
        redirect_url = 'admin-dashboard'
    elif user.role == 'super_admin':
        redirect_url = 'super_admin_dashboard'

    return jsonify({
        'message': 'Login successful',
        'redirect': redirect_url,
        'access_token': access_token
    }), 200