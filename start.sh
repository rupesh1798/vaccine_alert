if [ $1 == 'celery' ]
then
    echo "statrting Celery...."
    exec celery -A care worker -l debug -c 1
else
    echo "starting server..."
        exec python manage.py runserver
fi