import csv
import os
from io import StringIO
from datetime import datetime, timedelta, date 
from celery import Celery
from flask_mail import Mail, Message
from models import db, User, Quiz, Score 
from app import create_app 
import os
import csv
from io import StringIO
from datetime import datetime, timedelta, date

from celery import Celery
from flask_mail import Mail, Message

from models import db, User, Quiz, Score
from app import create_app


flask_app = create_app()

celery = Celery(__name__, broker=flask_app.config['CELERY_BROKER_URL'])
celery.conf.update(flask_app.config)

mail = Mail(flask_app)


@celery.task()
def send_daily_reminders():
    with flask_app.app_context():
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        
        inactive_users = User.query.filter(
            User.role == 'user',
            ~User.scores.any(Score.time_stamp_of_attempt > seven_days_ago) # Users with no score in last 7 days
        ).all()

    
        recent_quizzes = Quiz.query.filter(
            Quiz.created_at > datetime.utcnow() - timedelta(days=1)
        ).all()

        if not inactive_users and not recent_quizzes:
            print("No reminders to send today.")
            return "No reminders to send today."

        for user in inactive_users:
            msg = Message('Quiz Master Daily Reminder',
                          sender=flask_app.config['MAIL_USERNAME'],
                          recipients=[user.email])
            body = f"Hello {user.full_name or user.email},\n\n"
            body += "Just a friendly reminder to visit Quiz Master!\n"

            if recent_quizzes:
                body += "\nHere are some new quizzes you might be interested in:\n"
                for quiz in recent_quizzes:
                    body += f"- {quiz.name} (Subject: {quiz.chapter.subject.name if quiz.chapter else 'N/A'}, Chapter: {quiz.chapter.name if quiz.chapter else 'N/A'})\n"

            body += "\nKeep learning and happy quizzing!\n\nThanks,\nQuiz Master Team"
            msg.body = body

            try:
                mail.send(msg)
                print(f"Daily reminder sent to {user.email}")
            except Exception as e:
                print(f"Failed to send daily reminder to {user.email}: {str(e)}")
        return "Daily reminders sent."


@celery.task()
def generate_monthly_report():
    with flask_app.app_context():
        # Calculate the start and end of the previous month
        today = date.today()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_previous_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_previous_month = last_day_of_previous_month.replace(day=1)

        # Fetch all users
        users = User.query.filter_by(role='user').all()

        for user in users:
            # Get scores for  previous month for this user
            monthly_scores = Score.query.filter(
                Score.user_id == user.id,
                Score.time_stamp_of_attempt >= first_day_of_previous_month,
                Score.time_stamp_of_attempt <= last_day_of_previous_month
            ).all()

            if not monthly_scores:
                print(f"No activity for {user.email} last month. Skipping report.")
                continue

            total_quizzes_taken = len(monthly_scores)
            total_scored_sum = sum(s.total_scored for s in monthly_scores)
            total_possible_sum = sum(s.total_possible for s in monthly_scores)
            average_score = (total_scored_sum / total_possible_sum * 100) if total_possible_sum > 0 else 0

            # Generate HTML report
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ width: 80%; margin: 20px auto; padding: 20px; border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; }}
                    h2 {{ color: #0056b3; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #e2e6ea; }}
                    .summary {{ margin-top: 20px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Monthly Activity Report - {first_day_of_previous_month.strftime('%B %Y')}</h2>
                    <p>Dear {user.full_name or user.email},</p>
                    <p>Here's a summary of your activity on Quiz Master for the month of {first_day_of_previous_month.strftime('%B %Y')}:</p>

                    <div class="summary">
                        <p><strong>Quizzes Taken:</strong> {total_quizzes_taken}</p>
                        <p><strong>Average Score:</strong> {average_score:.2f}%</p>
                        </div>

                    <h3>Quiz Details:</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Quiz Name</th>
                                <th>Your Score</th>
                                <th>Date Attempted</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            for score in monthly_scores:
                quiz = Quiz.query.get(score.quiz_id)
                quiz_name = quiz.name if quiz else 'Unknown Quiz'
                html_body += f"""
                            <tr>
                                <td>{quiz_name}</td>
                                <td>{score.total_scored} / {score.total_possible}</td>
                                <td>{score.time_stamp_of_attempt.strftime('%Y-%m-%d %H:%M')}</td>
                            </tr>
                """
            html_body += """
                        </tbody>
                    </table>
                    <p style="margin-top: 30px;">Keep up the great work!</p>
                    <p>Thanks,</p>
                    <p>Quiz Master Team</p>
                </div>
            </body>
            </html>
            """

            msg = Message(f'Monthly Activity Report - {first_day_of_previous_month.strftime('%B %Y')}',
                          sender=flask_app.config['MAIL_USERNAME'],
                          recipients=[user.email])
            msg.html = html_body # Send as HTML

            try:
                mail.send(msg)
                print(f"Monthly report sent to {user.email}")
            except Exception as e:
                print(f"Failed to send monthly report to {user.email}: {str(e)}")
        return "Monthly reports generated and sent."