set -e

exec python data_pull.py &
exec python manage.py runserver 0.0.0.0:8000