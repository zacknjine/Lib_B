from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user
from flask_jwt_extended import jwt_required, get_jwt_identity

# admin access only
def admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_data = get_jwt_identity()  # Get the current user's identity
        if current_user_data['role'] not in ['admin', 'super_admin']:
            flash("You don't have the required permissions to access this page.", "warning")
            return redirect(url_for('home')) 
        return f(*args, **kwargs)
    return decorated_function

# super admin access only
def super_admin_required(f):
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_data = get_jwt_identity()
        if current_user_data['role'] != 'super_admin':
            flash("You don't have the required permissions to access this page.", "warning")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function
