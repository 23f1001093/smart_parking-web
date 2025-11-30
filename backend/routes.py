from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, ParkingLot, ParkingSpot, Reservation
from functools import wraps
from datetime import datetime
import json
from flask import send_from_directory
import os
api = Blueprint('api', __name__)



def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'message': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Debug endpoint to inspect proxied requests
@api.route('/debug/proxy', methods=['GET', 'POST', 'OPTIONS'])
def debug_proxy():
    info = {
        'remote_addr': request.remote_addr,
        'method': request.method,
        'host_header': request.headers.get('Host'),
        'origin': request.headers.get('Origin'),
        'referer': request.headers.get('Referer'),
        'cookie_header': request.headers.get('Cookie'),
        'content_type': request.headers.get('Content-Type'),
        'all_headers': dict(request.headers)
    }
    if request.method == 'POST':
        try:
            info['body_text'] = request.get_data(as_text=True)
        except Exception as e:
            info['body_text'] = f'error reading body: {e}'
    current_app.logger.info("debug_proxy: %s", info)
    return jsonify(info), 200

# --- Authentication ---
@api.route('/register', methods=['POST'])
def register():
    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')

    if not email or not password or not username:
        return jsonify({'message': 'username, email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already taken'}), 409

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already taken'}), 409

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    new_user = User(email=email, password_hash=hashed_password, username=username, role='user')
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'Registration successful'}), 201

# Enhanced login route with debug logging (temporary)
@api.route('/login', methods=['POST'])
def login():
    current_app.logger.info("=== LOGIN DEBUG START ===")
    current_app.logger.info("Remote addr: %s", request.remote_addr)
    current_app.logger.info("Host header: %s", request.headers.get('Host'))
    current_app.logger.info("Origin header: %s", request.headers.get('Origin'))
    current_app.logger.info("Content-Type header: %s", request.headers.get('Content-Type'))
    current_app.logger.info("All headers: %s", dict(request.headers))
    try:
        current_app.logger.info("Raw body: %s", request.get_data(as_text=True))
    except Exception as e:
        current_app.logger.info("Error reading body: %s", e)

    data = request.json or {}
    email = data.get('email')
    password = data.get('password')
    current_app.logger.info("Parsed JSON email: %s, password present: %s", email, bool(password))

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        session['user_role'] = user.role
        current_app.logger.info("Login successful for user id %s", user.id)
        current_app.logger.info("=== LOGIN DEBUG END ===")
        return jsonify({'message': 'Login successful', 'user_id': user.id, 'role': user.role}), 200

    current_app.logger.info("Login failed (invalid credentials)")
    current_app.logger.info("=== LOGIN DEBUG END ===")
    return jsonify({'message': 'Invalid credentials'}), 401

@api.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200

@api.route('/me', methods=['GET'])
@login_required
def get_current_user():
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user.serialize()), 200

# --- Admin: Parking Lot Management ---
@api.route('/admin/parkinglots', methods=['GET'])
@admin_required
def list_parking_lots():
    lots = ParkingLot.query.all()
    return jsonify([lot.serialize() for lot in lots]), 200

@api.route('/admin/parkinglots', methods=['POST'])
@admin_required
def create_parking_lot():
    data = request.json or {}
    required = ['prime_location_name', 'price', 'number_of_spots']
    for r in required:
        if r not in data:
            return jsonify({'message': f'{r} is required'}), 400

    lot = ParkingLot(
        prime_location_name=data['prime_location_name'],
        address=data.get('address'),
        pin_code=data.get('pin_code'),
        price=data['price'],
        number_of_spots=data['number_of_spots']
    )
    db.session.add(lot)
    db.session.flush()
    for _ in range(lot.number_of_spots):
        spot = ParkingSpot(lot_id=lot.id, status='A')
        db.session.add(spot)
    db.session.commit()
    return jsonify(lot.serialize()), 201

@api.route('/admin/parkinglots/<int:lot_id>', methods=['PUT'])
@admin_required
def edit_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    data = request.json or {}
    if 'prime_location_name' in data:
        lot.prime_location_name = data['prime_location_name']
    if 'address' in data:
        lot.address = data['address']
    if 'pin_code' in data:
        lot.pin_code = data['pin_code']
    if 'price' in data:
        lot.price = data['price']
    if 'number_of_spots' in data:
        current_occupied = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
        if current_occupied > 0:
            return jsonify({'message': 'Cannot change spot count while spots are occupied'}), 400
        # Remove existing spots and recreate to match new count
        ParkingSpot.query.filter_by(lot_id=lot.id).delete()
        db.session.flush()
        for _ in range(data['number_of_spots']):
            spot = ParkingSpot(lot_id=lot.id, status='A')
            db.session.add(spot)
        lot.number_of_spots = data['number_of_spots']
    db.session.commit()
    return jsonify(lot.serialize()), 200

@api.route('/admin/parkinglots/<int:lot_id>', methods=['DELETE'])
@admin_required
def delete_parking_lot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    occupied = ParkingSpot.query.filter_by(lot_id=lot.id, status='O').count()
    if occupied > 0:
        return jsonify({'message': 'Cannot delete, spots are occupied'}), 400
    db.session.delete(lot)
    db.session.commit()
    return jsonify({'message': 'Deleted successfully'}), 200

@api.route('/admin/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.filter_by(role='user').all()
    return jsonify([u.serialize() for u in users]), 200

@api.route('/admin/reservations', methods=['GET'])
@admin_required
def list_reservations():
    reservations = Reservation.query.all()
    return jsonify([r.serialize() for r in reservations]), 200

# --- Admin: Spots status and details by lot ---
@api.route('/admin/parkinglots/<int:lot_id>/spots', methods=['GET'])
@admin_required
def get_spots_in_lot(lot_id):
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()
    out = []
    for spot in spots:
        d = spot.serialize()
        if spot.status == 'O':
            res = Reservation.query.filter_by(spot_id=spot.id, leaving_timestamp=None).first()
            if res:
                d['vehicle_number'] = res.vehicle_number
                d['user_id'] = res.user_id
        out.append(d)
    return jsonify(out), 200

# --- User: Parking Lot View & Reserve ---
@api.route('/parkinglots', methods=['GET'])
@login_required
def user_list_parkinglots():
    lots = ParkingLot.query.all()
    output = []
    for lot in lots:
        available_spots = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').count()
        out = lot.serialize()
        out['available_spots'] = available_spots
        output.append(out)
    return jsonify(output), 200

@api.route('/parkinglots/<int:lot_id>/reserve', methods=['POST'])
@login_required
def reserve_parking_spot(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    spot = ParkingSpot.query.filter_by(lot_id=lot.id, status='A').first()
    if not spot:
        return jsonify({'message': 'No spots available'}), 400
    spot.status = 'O'
    data = request.json or {}
    vehicle_number = data.get('vehicle_number')
    remarks = data.get('remarks')
    new_reservation = Reservation(
        user_id=session['user_id'],
        spot_id=spot.id,
        parking_timestamp=datetime.utcnow(),
        parking_cost=lot.price,
        vehicle_number=vehicle_number,
        remarks=remarks
    )
    db.session.add(new_reservation)
    db.session.commit()
    return jsonify({
        'message': 'Spot reserved',
        'reservation_id': new_reservation.id,
        'spot_id': spot.id
    }), 201

@api.route('/reservations/<int:reservation_id>/release', methods=['POST'])
@login_required
def release_spot(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != session['user_id']:
        return jsonify({'message': 'Unauthorized'}), 403
    if reservation.leaving_timestamp:
        return jsonify({'message': 'Already released'}), 400
    reservation.leaving_timestamp = datetime.utcnow()
    spot = ParkingSpot.query.get(reservation.spot_id)
    if spot:
        spot.status = 'A'
    db.session.commit()
    return jsonify({'message': 'Spot released'}), 200

@api.route('/my/reservations', methods=['GET'])
@login_required
def get_user_reservations():
    user_id = session['user_id']
    reservations = Reservation.query.filter_by(user_id=user_id).order_by(Reservation.parking_timestamp.desc()).all()
    return jsonify([r.serialize() for r in reservations]), 200

# --- Async Export Example using Celery batch job ---
@api.route('/my/export', methods=['POST'])
@login_required
def trigger_export():
    user_id = session['user_id']
    email = request.json.get("email")
    from tasks import export_user_reservations
    export_user_reservations.delay(user_id, email)
    return jsonify({'message': 'Your export job has started. You will receive an alert when done.'}), 202

# --- Simple Caching Example ---
import redis
r = redis.StrictRedis(host='localhost', port=6379, db=1, decode_responses=True)

@api.route('/cached/parkinglots', methods=['GET'])
@login_required
def cached_lots():
    cache_key = "parkinglots"
    cached = r.get(cache_key)
    if cached:
        try:
            return jsonify(json.loads(cached)), 200
        except Exception:
            # fallback, continue to rebuild cache
            pass
    lots = ParkingLot.query.all()
    out = [lot.serialize() for lot in lots]
    # Store JSON string safely instead of using eval
    r.setex(cache_key, 30, json.dumps(out))
    return jsonify(out), 200

@api.route("/download/<filename>")
def download_file(filename):
    export_dir = os.path.join(current_app.root_path, "..", "exports")
    return send_from_directory(export_dir, filename, as_attachment=True)