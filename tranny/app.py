import httplib
import os
from functools import partial
from json import dumps
from flask import Flask, g, request, redirect, url_for, current_app
from flask.ext.babel import Babel
from flask.ext.login import current_user, confirm_login


def _log(msg, level="info"):
    try:
        getattr(current_app.logger, level)(msg)
    except:
        print(msg)


class _logger(object):
    info = partial(_log, level='info')
    warn = partial(_log, level='warn')
    warning = warn
    debug = partial(_log, level='debug')
    error = partial(_log, level='error')
    exception = partial(_log, level='exception')

logger = _logger()

from .configuration import Configuration
config = Configuration()

from .models import User
from .manager import ServiceManager
from .util import file_size
from .ui import render_template
from .extensions import db, mail, cache, login_manager

service_manager = ServiceManager()

__all__ = ['create_app']


def create_app(app_name="tranny"):
    app = Flask(app_name)
    configure_app(app)
    configure_extensions(app)
    configure_hook(app)
    configure_blueprints(app)
    configure_logging(app)
    configure_template_filters(app)
    configure_error_handlers(app)
    configure_services(app)
    return app


def configure_services(app):
    service_manager.init()
    service_manager.start()


def configure_app(app):
    config.init_app(app)

    @app.route("/")
    def index():
        return redirect(url_for("home.index"))


def configure_extensions(app):
    # flask-sqlalchemy
    db.app = app
    db.init_app(app)

    # flask-mail
    mail.init_app(app)

    # flask-cache
    cache.init_app(app)

    # flask-babel
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        accept_languages = app.config.get('ACCEPT_LANGUAGES')
        return request.accept_languages.best_match(accept_languages)

    # flask-login
    login_manager.login_view = 'user.login'
    login_manager.refresh_view = 'frontend.reauth'

    @login_manager.user_loader
    def user_loader(user_id):
        return User.query.filter_by(user_id=user_id).first()

    @login_manager.needs_refresh_handler
    def refresh():
        # do stuff
        confirm_login()
        return True

    @login_manager.unauthorized_handler
    def login_redir():
        return redirect(url_for("user.login"))

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    login_manager.init_app(app)


def configure_hook(app):
    @app.before_request
    def before_request():
        g.user = current_user


def configure_blueprints(app):
    from .handlers.filters import filters
    from .handlers.home import home
    from .handlers.rss import rss
    from .handlers.services import services
    from .handlers.settings import settings
    from .handlers.stats import stats
    from .handlers.user import usr
    map(app.register_blueprint, [filters, home, rss, services, settings, stats, usr])


def configure_template_filters(app):

    @app.template_filter()
    def pretty_date(value):
        return pretty_date(value)

    @app.template_filter()
    def format_date(value, format='%Y-%m-%d'):
        return value.strftime(format)

    @app.template_filter()
    def human_size(value):
        return file_size(value)


def configure_logging(app):
    """Configure file(info) and email(error) logging."""

    if app.debug or app.testing:
        # Skip debug and test mode. Just check standard output.
        return

    import logging
    from logging.handlers import SMTPHandler

    # Set info level on logger, which might be overwritten by handers.
    # Suppress DEBUG messages.
    app.logger.setLevel(logging.INFO)

    info_log = os.path.join(app.config['LOG_FOLDER'], 'info.log')
    info_file_handler = logging.handlers.RotatingFileHandler(info_log, maxBytes=100000, backupCount=10)
    info_file_handler.setLevel(logging.INFO)
    info_file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(info_file_handler)

    # Testing
    #app.logger.info("testing info.")
    #app.logger.warn("testing warn.")
    #app.logger.error("testing error.")

    mail_handler = SMTPHandler(app.config['MAIL_SERVER'],
                               app.config['MAIL_USERNAME'],
                               config.get("general", "email"),
                               'O_ops... Tranny failed!',
                               (app.config['MAIL_USERNAME'],
                                app.config['MAIL_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]')
    )
    app.logger.addHandler(mail_handler)


def configure_error_handlers(app):

    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("errors/forbidden_page.html", error=error), httplib.FORBIDDEN

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/page_not_found.html", error=error), httplib.NOT_FOUND

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("errors/server_error.html", error=error), httplib.INTERNAL_SERVER_ERROR


def response(status=0, msg=None):
    return dumps({
        'status': status,
        'msg': msg
    })