import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os
from flask import Flask, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session
from config import Config
from flask_bootstrap import Bootstrap
import flask_excel as excel
from redis import Redis
import rq

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = ('Please log in to access this page.')
bootstrap = Bootstrap()
sess = Session()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    bootstrap.init_app(app)
    excel.init_excel(app)
    sess.init_app(app)

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('hlb-tasks', connection = app.redis)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.static import bp as static_bp
    app.register_blueprint(static_bp)

    # if not app.debug and not app.testing:
    #
    #     if app.config['LOG_TO_STDOUT']:
    #         stream_handler = logging.StreamHandler()
    #         stream_handler.setLevel(logging.INFO)
    #         app.logger.addHandler(stream_handler)
    #     else:
    #         if not os.path.exists('logs'):
    #             os.mkdir('logs')
    #         file_handler = RotatingFileHandler('logs/microblog.log',
    #                                            maxBytes=10240, backupCount=10)
    #         file_handler.setFormatter(logging.Formatter(
    #             '%(asctime)s %(levelname)s: %(message)s '
    #             '[in %(pathname)s:%(lineno)d]'))
    #         file_handler.setLevel(logging.INFO)
    #         app.logger.addHandler(file_handler)
    #
    #     app.logger.setLevel(logging.INFO)
    #     app.logger.info('HLB startup')

    return app

from app import models, errors
