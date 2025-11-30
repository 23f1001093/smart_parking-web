from celery import Celery
from celery.schedules import crontab
from models import db, User, Reservation, ParkingLot, create_app    
from flask_mail import Message
from datetime import datetime, date
import csv
from jinja2 import Template
from __init__ import create_app, mail

celery = Celery("tasks", broker="redis://localhost:6379/0")
celery.conf.beat_schedule = {
    'daily_reminder': {
        'task': 'tasks.daily_reminders',
        'schedule': crontab(hour=18, minute=0)
    },
    'monthly_report': {
        'task': 'tasks.monthly_report',
        'schedule': crontab(day_of_month=1, hour=9, minute=0)
    }
}

# ---------- DAILY REMINDERS ----------
@celery.task
def daily_reminders():
    app = create_app()
    with app.app_context():
        today = date.today()
        users = User.query.all()
        for user in users:
            bookings_today = Reservation.query.filter_by(user_id=user.id).filter(
                Reservation.parking_timestamp >= datetime.combine(today, datetime.min.time()),
                Reservation.parking_timestamp < datetime.combine(today, datetime.max.time())
            ).count()
            if bookings_today == 0:
                send_email(user.email, "Parking Reminder", "You have not booked a parking spot today. Please check if you need to park.", app=app)

# ---------- MONTHLY ACTIVITY REPORT ----------
@celery.task
def monthly_report():
    app = create_app()
    with app.app_context():
        today = date.today()
        month_start = today.replace(day=1)
        users = User.query.all()
        for user in users:
            reservations = Reservation.query.filter_by(user_id=user.id).filter(
                Reservation.parking_timestamp >= month_start
            ).all()
            lot_usage = {}
            for r in reservations:
                if r.spot and r.spot.lot_id:
                    lot_id = r.spot.lot_id
                    lot_usage[lot_id] = lot_usage.get(lot_id, 0) + 1
            if lot_usage:
                most_used_lot_id = max(lot_usage, key=lot_usage.get)
                lot_obj = ParkingLot.query.get(most_used_lot_id)
                most_used_lot_name = lot_obj.prime_location_name if lot_obj else f"Lot {most_used_lot_id}"
                most_used_lot_count = lot_usage[most_used_lot_id]
            else:
                most_used_lot_name = "N/A"
                most_used_lot_count = 0
            total_spent = sum(r.parking_cost or 0 for r in reservations)
            html = Template("""
            <h2>Your Monthly Parking Report</h2>
            <ul>
              <li><strong>Total Reservations:</strong> {{ count }}</li>
              <li><strong>Most Used Lot:</strong> {{ lot_name }} ({{ lot_count }} times)</li>
              <li><strong>Total Spent:</strong> ₹{{ spent }}</li>
            </ul>
            """).render(
                count=len(reservations),
                lot_name=most_used_lot_name,
                lot_count=most_used_lot_count,
                spent=total_spent
            )
            send_email(user.email, "Monthly Parking Report", html, html=True, app=app)

# ---------- USER-TRIGGERED CSV EXPORT ----------
@celery.task
def export_user_reservations(user_id, email):
    app = create_app()
    with app.app_context():
        try:
            reservations = Reservation.query.filter_by(user_id=user_id).all()
            if not reservations:
                send_email(email, "Your Parking Export", "No reservations found for your account.", app=app)
                return
            filename = f"user_{user_id}_reservations.csv"
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(reservations[0].serialize().keys()))
                writer.writeheader()
                for r in reservations:
                    writer.writerow(r.serialize())
            subject = "Your Parking Reservation Export"
            body = "Please find your parking reservation details attached as CSV."
            send_email(email, subject, body, attachment_path=filename, app=app)
            return filename
        except Exception as e:
            send_email(email, "Parking Export Failed", f"An error occurred: {e}", app=app)
            raise

# ---------- SHARED EMAIL UTILITY ----------
@celery.task
def send_email(to, subject, body, attachment_path=None, html=False):
    with app.app_context():
        msg = Message(subject, recipients=[to])
        if html:
            msg.html = body
        else:
            msg.body = body
        if attachment_path:
            with open(attachment_path, "rb") as fp:
                msg.attach(
                    attachment_path.split('/')[-1],
                    "text/csv",
                    fp.read()
                )
        mail.send(msg)
