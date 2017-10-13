# -*- coding:utf-8 -*-

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from .exceptions import db, login_manager


from flask_pagedown import PageDown
from config import config
from .admin import CustomView, CustomModelView
from .models import User, Post, Comment
from flask_admin import Admin
from flask_babelex import Babel
from flask_cache import Cache

from flask_celery import Celery


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()

pagedown = PageDown()
babel = Babel()
admin = Admin(name=u'后台管理系统')

flask_celery = Celery()

#缓存
cache = Cache()



login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    app.config['BABEL_DEFAULT_LOCALE'] = 'zh_CN'
    bootstrap.init_app(app)
    babel.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    app.config['SERVER_NAME'] = 'localhost:5000'

    cache.init_app(app)

    flask_celery.init_app(app)

    admin.init_app(app)
    admin.add_view(CustomView(name='Custom'))
    admin.add_view(CustomModelView(User, db.session, category=u'用户'))
    admin.add_view(CustomModelView(Post, db.session, category=u'用户'))


    admin.add_view(CustomModelView(Comment, db.session, category=u'用户'))


    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint, url_prefix='/api/v1.0')

    return app
