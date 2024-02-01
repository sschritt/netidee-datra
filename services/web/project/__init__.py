from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from os import urandom
from .extensions import oauth
from flask_apscheduler import APScheduler
from .utils import celery_init_app

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)

    oauth.init_app(app)

    app.config['SECRET_KEY'] = urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:////usr/src/app/instance/{DB_NAME}'
    app.config['CELERY'] = {"broker_url": "amqp://guest:guest@rabbitmq:5672//", "result_backend": "rpc://"}
    db.init_app(app)

    celery = celery_init_app(app)
    celery.set_default()

    from .routes import views
    app.register_blueprint(views)

    from .models import User, GoogleUser, LinkedinUser, FacebookUser, delete_old_entries, DeepdiveResult

    create_db(app)

    scheduler = APScheduler()
    scheduler.init_app(app)

    # Schedule the task to run once a day
    @scheduler.task('interval', id='delete_old_entries', hours=24)
    def scheduled_delete_old_entries():
        with app.app_context():
            delete_old_entries()

    scheduler.start()

    return app, celery


# created database
def create_db(app):
    if not path.exists('/usr/src/app/instance/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Database created successfully.')

app, celery = create_app()
app.app_context().push()
