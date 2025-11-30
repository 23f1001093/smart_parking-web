import os
import csv
import tempfile
from datetime import datetime, timedelta, date
from jinja2 import Template
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

from app import create_app
from models import db, User, ParkingLot, ParkingSpot, Reservation


flask_app = create_app()

celery = Celery(
    __name__,
    broker=flask_app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
)

celery.conf.update(
    broker_url=flask_app.config.get("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    result_backend=flask_app.config.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

@celery.task()
def send_monthly_activity_report_for_all():
    """
    Send monthly activity report to all users.
    """
    
    with flask_app.app_context():
        users = User.query.all()
        for user in users:
            send_monthly_activity_report.delay(user.id)
    print("[Monthly Report] Scheduled for all users.")

@celery.task()
def send_daily_reminder(user_id):
    with flask_app.app_context():
        user = User.query.get(user_id)
        if not user:
            return
        # logic to send reminder email
        send_email(user.email, "Daily Parking Reminder", "This is your daily reminder!")
        print(f"[Daily Reminder] Sent to {user.email}")

@celery.task()
def send_daily_reminder_for_all():
    """Send daily parking reminder to all users."""
    with flask_app.app_context():
        from backend.models import User  # lazy import
        users = User.query.all()
        for user in users:
            send_daily_reminder.delay(user.id)
    print("[Daily Reminder] Scheduled for all users.")

@celery.task()
def send_monthly_activity_report(user_id):
    """
    Sends a monthly activity report to a user:
    - Number of reservations per month
    - Most used parking lot
    - Total spent
    """
    with flask_app.app_context():
        user = User.query.get(user_id)
        if not user:
            print(f"[Monthly Report] User {user_id} not found.")
            return

        # Calculate first and last day of previous month
        today = datetime.today()
        first_day_prev_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_prev_month = today.replace(day=1) - timedelta(days=1)

        # Fetch reservations for last month
        reservations = (
            Reservation.query
            .filter(
                Reservation.user_id == user_id,
                Reservation.parking_timestamp >= first_day_prev_month,
                Reservation.parking_timestamp <= last_day_prev_month,
            )
            .all()
        )

        if not reservations:
            send_email(
                user.email,
                f"Monthly Parking Report - {first_day_prev_month.strftime('%B %Y')}",
                "<p>No reservations found for last month.</p>"
            )
            return

        # Stats
        total_spent = sum(r.parking_cost or 0 for r in reservations)
        total_reservations = len(reservations)

        # Most used parking lot
        lot_counts = {}
        for r in reservations:
            if r.spot and r.spot.lot:
                lot_counts[r.spot.lot.prime_location_name] = lot_counts.get(r.spot.lot.prime_location_name, 0) + 1
        most_used_lot = max(lot_counts, key=lot_counts.get) if lot_counts else "N/A"

        # Render HTML
        html_template = Template("""
        <h2>Monthly Parking Report - {{ month_year }}</h2>
        <p>Hello {{ username }},</p>
        <ul>
            <li>Total Reservations: {{ total_reservations }}</li>
            <li>Most Used Parking Lot: {{ most_used_lot }}</li>
            <li>Total Spent: ₹{{ total_spent }}</li>
        </ul>
        <h3>Reservation Details:</h3>
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Reservation ID</th>
                <th>Lot</th>
                <th>Spot ID</th>
                <th>Start Time</th>
                <th>Leaving Time</th>
                <th>Vehicle Number</th>
                <th>Parking Cost</th>
            </tr>
            {% for r in reservations %}
            <tr>
                <td>{{ r.id }}</td>
                <td>{{ r.spot.lot.prime_location_name if r.spot and r.spot.lot else '' }}</td>
                <td>{{ r.spot.id if r.spot else '' }}</td>
                <td>{{ r.parking_timestamp.strftime('%Y-%m-%d %H:%M') if r.parking_timestamp else '' }}</td>
                <td>{{ r.leaving_timestamp.strftime('%Y-%m-%d %H:%M') if r.leaving_timestamp else '' }}</td>
                <td>{{ r.vehicle_number or '' }}</td>
                <td>{{ r.parking_cost or '' }}</td>
            </tr>
            {% endfor %}
        </table>
        """)

        html_body = html_template.render(
            month_year=first_day_prev_month.strftime("%B %Y"),
            username=user.username or user.email,
            total_reservations=total_reservations,
            most_used_lot=most_used_lot,
            total_spent=total_spent,
            reservations=reservations,
        )

        send_email(user.email, f"Monthly Parking Report - {first_day_prev_month.strftime('%B %Y')}", html_body)
        print(f"[Monthly Report] Sent to {user.email}")


def send_email(to, subject, body, attachment_path=None, html=False):
   
    
    print("To:", to)
    print("Subject:", subject)
    print("HTML:" if html else "Text:", (body or "")[:300])
    if attachment_path:
        print("Attachment:", attachment_path)

    return True



def _fmt_dt(dt):
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return str(dt)


@celery.task()
def export_user_reservations(user_id, email):
    """
    Async task:
    - Fetch all reservations for given user_id.
    - Write them to a temp CSV file.
    - 'Send' an email with CSV attached (mocked).
    """
    with flask_app.app_context():
        user = User.query.get(user_id)
        if not user:
            print(f"[export_user_reservations] User {user_id} not found.")
            send_email(
                email,
                "Parking Export Failed",
                "Your account was not found in the system.",
            )
            return {"status": "error", "message": "user_not_found"}

        reservations = (
            Reservation.query.filter_by(user_id=user_id)
            .order_by(Reservation.parking_timestamp.desc())
            .all()
        )

        if not reservations:
            print(f"[export_user_reservations] No reservations for user {user_id}.")
            send_email(
                email,
                "Your Parking Export",
                "No reservations found for your account.",
            )
            return {"status": "no_data", "count": 0}

        tmp_name = None
        try:
            # Create temp CSV
            tmp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".csv",
                prefix=f"user_{user_id}_reservations_",
                mode="w",
                newline="",
                encoding="utf-8",
            )
            tmp_name = tmp.name

            writer = csv.writer(tmp)
            writer.writerow(
                [
                    "Reservation ID",
                    "Lot",
                    "Spot ID",
                    "Start Time",
                    "Leaving Time",
                    "Vehicle Number",
                    "Parking Cost",
                    "Remarks",
                ]
            )

            for r in reservations:
                lot_name = ""
                spot_id = ""
                if r.spot:
                    spot_id = r.spot.id
                    if getattr(r.spot, "lot", None):
                        lot_name = r.spot.lot.prime_location_name
                writer.writerow(
                    [
                        r.id,
                        lot_name,
                        spot_id,
                        _fmt_dt(r.parking_timestamp),
                        _fmt_dt(r.leaving_timestamp),
                        r.vehicle_number or "",
                        r.parking_cost if r.parking_cost is not None else "",
                        r.remarks or "",
                    ]
                )

            tmp.close()

            subject = f"Your Parking Reservations Export ({len(reservations)} records)"
            body = (
                f"Hello {user.username or user.email},\n\n"
                f"Attached is your parking reservation history as a CSV file "
                f"containing {len(reservations)} records.\n\n"
                "Thanks,\nVehicle Parking App"
            )

            send_email(email, subject, body, attachment_path=tmp_name)
            print(
                f"[export_user_reservations] Export complete for user {user_id}, file: {tmp_name}"
            )

            return {
                "status": "success",
                "count": len(reservations),
                "user": user.username,
                "sent_to": email,
            }

        except Exception as e:
            print(f"[export_user_reservations] Error for user {user_id}: {e}")
            send_email(
                email,
                "Parking Export Failed",
                f"An error occurred while generating your export: {e}",
            )
            return {"status": "error", "message": str(e)}

        finally:
            if tmp_name and os.path.exists(tmp_name):
                try:
                    os.remove(tmp_name)
                except Exception as cleanup_err:
                    print(f"Failed to delete temp file {tmp_name}: {cleanup_err}")

from celery.schedules import crontab

celery.conf.beat_schedule = {
    "monthly-activity-report": {
        "task": "backend.tasks.send_monthly_activity_report_for_all",
        "schedule": crontab(minute=0, hour=0, day_of_month=1),
    }
}

from celery.schedules import crontab

celery.conf.beat_schedule = {
    "monthly-activity-report": {
        "task": "backend.tasks.send_monthly_activity_report_for_all",
        "schedule": crontab(minute=0, hour=0, day_of_month=1),  # 1st of every month at 00:00
    },
    "daily-parking-reminder": {
        "task": "backend.tasks.send_daily_reminder_for_all",
        "schedule": crontab(minute=0, hour=8),  # every day at 08:00
    },
}