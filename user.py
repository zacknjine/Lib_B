from flask import Blueprint, request, jsonify
from app import db
from models import Borrow, Book, User, Sale
from flask_jwt_extended import jwt_required, get_jwt_identity, current_user
from datetime import date
from mpesa import stk_push_request

user = Blueprint('user', __name__)

@user.route('/all_books', methods=['GET'])  
@jwt_required()  
def all_books():
    try:
        # Retrieve all books from the database
        books = Book.query.all()
        
        # Convert book objects into a list of dictionaries
        books_list = [
            {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'description': book.description,
                'release_date': book.release_date,
                'category': book.category,
                'price': book.price,
                'stock': book.stock,
                'photo': book.photo
            } for book in books
        ]
        
        return jsonify(books_list), 200  
    except Exception as e:
        return jsonify({'message': 'Error retrieving books', 'error': str(e)}), 500

@user.route('/borrow_book/<int:book_id>', methods=['POST'])
@jwt_required()
def borrow_book(book_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()

    if user is None:
        return jsonify({'message': 'User not found.'}), 404

    book = Book.query.get(book_id)
    if book is None:
        return jsonify({'message': 'Book not found.'}), 404

    if book.stock <= 0:
        return jsonify({'message': 'Book not available for borrowing.'}), 404

    existing_borrow = Borrow.query.filter_by(user_id=user.id, book_id=book.id, status='pending').first()
    if existing_borrow:
        return jsonify({'message': 'You have already requested to borrow this book.'}), 400

    new_borrow = Borrow(
        user_id=user.id,
        book_id=book.id,
        borrow_date=date.today(),
        return_date=None,
        status='pending',
        borrow_price=book.price * 0.2,
        instructions= None
    )

    db.session.add(new_borrow)
    db.session.commit()

    return jsonify({'message': 'Book borrowing request submitted successfully!', 'borrow_id': new_borrow.id}), 201


@user.route('/borrowed_books', methods=['GET'])
@jwt_required()
def get_borrowed_books():
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()

    borrowed_books = Borrow.query.filter_by(user_id=user.id).all()
    result = [{'id': b.id, 'book_id': b.book_id, 'borrow_date': b.borrow_date, 'return_date': b.return_date, 'status': b.status, 'borrow_price': b.borrow_price, 'instructions': b.instructions} for b in borrowed_books]

    return jsonify(result), 200

@user.route('/cancel_borrow/<int:borrow_id>', methods=['DELETE'])
@jwt_required()
def cancel_borrow(borrow_id):
    current_user = get_jwt_identity()
    user = User.query.filter_by(username=current_user['username']).first()

    if user is None:
        return jsonify({'message': 'User not found.'}), 404

    borrow_request = Borrow.query.filter_by(id=borrow_id, user_id=user.id).first()
    if borrow_request is None:
        return jsonify({'message': 'Borrow request not found or does not belong to user.'}), 404

    db.session.delete(borrow_request)
    db.session.commit()

    return jsonify({'message': 'Borrow request canceled successfully!'}), 200



@user.route('/checkout/<int:book_id>', methods=['POST'])
@jwt_required()
def checkout(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"message": "Book not found"}), 404

    phone_number = request.json.get('phone_number')
    if not phone_number:
        return jsonify({"message": "Phone number is required"}), 400

    phone_number = phone_number.strip()

    if phone_number.startswith('+254'):
        phone_number = phone_number[4:]
    elif phone_number.startswith('0'):
        phone_number = phone_number[1:]

    if not phone_number.startswith('254'):
        phone_number = '254' + phone_number

    if len(phone_number) != 12:
        return jsonify({"message": "Phone number must be 12 digits long (including '254')"}), 400

    sale = Sale(user_id=current_user.id, book_id=book_id, phone_number=phone_number, amount=book.price)
    db.session.add(sale)
    db.session.commit()

    mpesa_response = stk_push_request(phone_number, book.price)

    return jsonify({"message": "Checkout initiated", "sale_id": sale.id, "mpesa_response": mpesa_response}), 201


@user.route('/mpesa/notification', methods=['POST'])
def mpesa_notification():
    data = request.json

    # Log the callback for debugging
    print("M-Pesa Callback: ", data)

    # Process the callback and update sale status accordingly
    sale_id = data.get('sale_id')
    status = data.get('status')

    # Fetch the sale and update the status
    sale = Sale.query.get(sale_id)
    if sale:
        sale.status = status
        db.session.commit()

    return jsonify({"message": "Notification received"}), 200

@user.route('/payment_status/<int:sale_id>', methods=['GET'])
@jwt_required()
def payment_status(sale_id):
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({"message": "Sale not found"}), 404
    
    return jsonify({"message": f"Payment status is: {sale.status}"}), 200
