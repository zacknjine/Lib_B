from flask import Blueprint, request, jsonify
from app import db,app
from models import Book, Borrow, User, Sale
from decorators import admin_required
from datetime import datetime 
from auth import hash_password
import os
from werkzeug.utils import secure_filename
import re

admin = Blueprint('admin', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# User registration route
@admin.route('/register', methods=['POST'])
@admin_required
def register():
    data = request.get_json()
    
    # Check if username already exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists!'}), 400

    # Hash the password and create a new user
    hashed_password = hash_password(data['password'])
    new_user = User(username=data['username'], password=hashed_password, role=data['role'])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201



# User deletion route
@admin.route('/delete_user/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    db.session.delete(user)
    db.session.commit()

    return jsonify({'message': 'User deleted successfully'}), 200

# User editing route
@admin.route('/edit_user/<int:user_id>', methods=['PUT'])
@admin_required
def edit_user(user_id):
    data = request.get_json()
    print("Incoming data:", data)  # Debugging line

    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found!'}), 404

    current_user_id = get_current_user_id()
    if current_user_id == user_id:
        return jsonify({'message': 'You cannot edit yourself!'}), 403

    # Check for username and ensure it's unique
    if 'username' in data:
        existing_user = User.query.filter_by(username=data['username']).first()
        # Allow updating to the same username
        if existing_user and existing_user.id != user_id:
            return jsonify({'message': 'Username already exists!'}), 400
        user.username = data['username']  # Update username

    # Password should be updated only if it's provided
    if 'password' in data and data['password']:
        user.password = hash_password(data['password'])

    if 'role' in data:
        user.role = data['role']

    db.session.commit()
    return jsonify({'message': 'User updated successfully'}), 200


@admin.route('/users', methods=['GET'])
@admin_required
def list_users():
    try:
        users = User.query.all()

        # Convert user objects into a list of dictionaries
        user_list = [
            {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
            for user in users
        ]

        return jsonify(user_list), 200
    except Exception as e:
        return jsonify({'message': 'Error retrieving users', 'error': str(e)}), 500


# Add book route
@admin.route('/add_book', methods=['POST'])
@admin_required
def add_book():
    try:
        # Check if request contains data
        if not request.form:
            print("No form data received")
            return jsonify({'message': 'No form data received'}), 400

        print("Raw form data received:", request.form)
        print("Files received:", request.files)

        # Extracting the form data
        data = request.form

        # Check if all required fields are present in the data
        required_fields = ['title', 'description', 'release_date', 'author', 'category', 'price', 'stock']
        if not all(field in data for field in required_fields):
            missing_fields = [field for field in required_fields if field not in data]
            print(f"Missing fields: {missing_fields}")
            return jsonify({'message': f'Missing fields: {missing_fields}'}), 400

        # Validate the release_date format
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', data['release_date']):
            return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

        # Handle the file upload for the photo
        if 'photo' not in request.files:
            print("Missing photo file")
            return jsonify({'message': 'Missing photo file'}), 400
        
        photo = request.files['photo']
        
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(file_path)
            print("Photo saved to:", file_path)
        else:
            print("Invalid photo file")
            return jsonify({'message': 'Invalid photo file'}), 400

        # Process and validate release_date
        try:
            release_date = datetime.strptime(data['release_date'], '%Y-%m-%d').date()
        except ValueError as e:
            print(f"Date format error: {e}")
            return jsonify({'message': f'Invalid date format: {e}'}), 400

        # Create a new book instance
        new_book = Book(
            title=data['title'],
            description=data.get('description', ''),
            release_date=release_date,
            author=data['author'],
            category=data['category'],
            photo=filename,
            price=float(data['price']),
            stock=int(data['stock'])
        )

        # Add the book to the database
        db.session.add(new_book)
        db.session.commit()

        print("Book added successfully, ID:", new_book.id)
        return jsonify({'message': 'Book added successfully!', 'book_id': new_book.id}), 201

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({'message': f'Failed to add book. Error: {e}'}), 500


# Manage books route
@admin.route('/manage_borrow_requests', methods=['GET'])
@admin_required
def manage_borrow_requests():
    borrow_requests = Borrow.query.all()
    requests_list = [
        {
            'id': request.id,
            'user_id': request.user_id,
            'book_id': request.book_id,
            'borrow_date': request.borrow_date,
            'return_date': request.return_date,
            'status': request.status,
            'borrow_price': request.borrow_price,
            'instructions': request.instructions
        }
        for request in borrow_requests
    ]
    return jsonify(requests_list), 200



# Approve borrow route
@admin.route('/approve_borrow/<int:borrow_id>', methods=['POST'])
@admin_required
def approve_borrow(borrow_id):
    borrow = Borrow.query.get(borrow_id)

    if borrow is None or borrow.status != 'pending':
        return jsonify({'message': 'Borrow request not found or already processed.'}), 404

    data = request.get_json()
    return_date_str = data.get('return_date')
    instructions = data.get('instructions')

    if not return_date_str:
        return jsonify({'message': 'Return date is required.'}), 400

    try:
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    borrow.return_date = return_date
    borrow.instructions = instructions
    borrow.status = 'awaiting_pickup'

    db.session.commit()

    return jsonify({'message': 'Borrow request approved!', 'borrow_id': borrow.id}), 200

# Mark picked up route
@admin.route('/mark_picked_up/<int:borrow_id>', methods=['POST'])
@admin_required
def mark_picked_up(borrow_id):
    borrow = Borrow.query.get(borrow_id)

    if borrow is None or borrow.status != 'awaiting_pickup':
        return jsonify({'message': 'Invalid borrow record or not ready for pick-up.'}), 404

    book = Book.query.get(borrow.book_id)
    if book.stock <= 0:
        return jsonify({'message': 'No stock available for this book.'}), 400

    borrow.status = 'picked up'
    book.stock -= 1
    db.session.commit()

    return jsonify({'message': 'Book marked as picked up, stock reduced by 1.'}), 200

# Mark returned route
@admin.route('/mark_returned/<int:borrow_id>', methods=['POST'])
@admin_required
def mark_returned(borrow_id):
    borrow = Borrow.query.get(borrow_id)

    if borrow is None or borrow.status != 'picked up':
        return jsonify({'message': 'Invalid borrow record or not picked up yet.'}), 404

    borrow.return_date = datetime.now()
    borrow.status = 'returned'

    book = Book.query.get(borrow.book_id)
    book.stock += 1
    db.session.commit()

    return jsonify({'message': 'Book marked as returned, stock increased by 1.'}), 200


@admin.route('/sales', methods=['GET'])
@admin_required
def get_sales():
    sales = Sale.query.all() 
    sales_list = [
        {
            "id": sale.id,
            "user_id": sale.user_id,
            "book_id": sale.book_id,
            "phone_number": sale.phone_number,
            "amount": sale.amount,
            "status": sale.status,
            "created_at": sale.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        }
        for sale in sales
    ]
    return jsonify(sales_list), 200


@admin.route('/sales/analytics', methods=['GET'])
@admin_required
def sales_analytics():
    results = (
        db.session.query(
            func.strftime('%Y-%m', Sale.created_at),  # Format date to YYYY-MM
            func.sum(Sale.amount)
        )
        .group_by(func.strftime('%Y-%m', Sale.created_at))
        .all()
    )

    analytics_data = [{"month": month, "total_sales": total} for month, total in results]
    return jsonify(analytics_data), 200