web: python manage.py collectstatic --noinput && python manage.py migrate && python manage.py clearsessions && gunicorn college_app.wsgi --bind 0.0.0.0:$PORT
