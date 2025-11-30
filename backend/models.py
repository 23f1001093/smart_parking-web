from __init__ import db
from datetime import datetime



class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = {"extend_existing": True}  # <--- This prevents duplicate table errors


    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    reservations = db.relationship('Reservation', back_populates='user', lazy=True)
    # In your User model
   
    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role
        }

class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'
    __table_args__ = {"extend_existing": True}  # <--- This prevents duplicate table errors


    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(200))
    pin_code = db.Column(db.String(10))
    price = db.Column(db.Float, nullable=False)
    number_of_spots = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    spots = db.relationship('ParkingSpot', back_populates='lot', cascade="all, delete-orphan", lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'prime_location_name': self.prime_location_name,
            'address': self.address,
            'pin_code': self.pin_code,
            'price': self.price,
            'number_of_spots': self.number_of_spots,
            'is_active': self.is_active
        }

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'
    __table_args__ = {"extend_existing": True}  # <--- This prevents duplicate table errors


    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), default='A')  # 'A' = Available, 'O' = Occupied
    is_active = db.Column(db.Boolean, default=True)
    lot = db.relationship('ParkingLot', back_populates='spots', lazy=True)
    reservations = db.relationship('Reservation', back_populates='spot', lazy=True)

    def serialize(self):
        return {
            'id': self.id,
            'lot_id': self.lot_id,
            'status': self.status,
            'is_active': self.is_active
        }

class Reservation(db.Model):
    __tablename__ = 'reservation'
    __table_args__ = {"extend_existing": True}  # <--- This prevents duplicate table errors


    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    parking_cost = db.Column(db.Float)
    vehicle_number = db.Column(db.String(20))  # For license plate, etc.
    remarks = db.Column(db.String(255))
    spot = db.relationship('ParkingSpot', back_populates='reservations')
    user = db.relationship('User', back_populates='reservations')

    def serialize(self):
        return {
            'id': self.id,
            'spot_id': self.spot_id,
            'user_id': self.user_id,
            'parking_timestamp': self.parking_timestamp.isoformat() if self.parking_timestamp else None,
            'leaving_timestamp': self.leaving_timestamp.isoformat() if self.leaving_timestamp else None,
            'parking_cost': self.parking_cost,
            'vehicle_number': self.vehicle_number,
            'remarks': self.remarks
        }

