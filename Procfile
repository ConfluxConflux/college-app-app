web: gunicorn college_app.wsgi
release: python manage.py collectstatic --noinput && python manage.py migrate
