from celery.schedules import crontab

beat_schedule = {
    'daily_reminder': {
        'task': 'tasks.daily_reminders',
        'schedule': crontab(hour=18, minute=0),
    },
    'monthly_report': {
        'task': 'tasks.monthly_report',
        'schedule': crontab(day_of_month=1, hour=9, minute=0),
    }
}