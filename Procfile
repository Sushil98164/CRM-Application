web: gunicorn --bind :8000 bellsCRM.wsgi:application
celery_worker: celery -A bellsCRM worker --loglevel=info --concurrency=4
celery_beat: celery -A bellsCRM beat -l info -S django