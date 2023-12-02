from flask import Flask, render_template
import os
import logging
# ---------------- for ihm -----------------------------
from db import db
from auth import Auth, login_required
from param import Params
from info import Info
from static import Static
from financial import Financial
from ged import GedFile

__prg_version__ = "0.0.1"
__prg_name__ = "financial cac"

toBoolean = {'true': True, 'false': False}

app = Flask(__name__)
app.config["VERSION"] = __prg_version__
app.config["APP_PORT"] = int(os.environ.get('APP_PORT', '5000'))
app.config["APP_HOST"] = os.environ.get('APP_HOST', '0.0.0.0')
app.config["APP_DEBUG"] = toBoolean.get(os.environ.get('APP_DEBUG', 'false'), True)
app.config['APP_NAME'] = os.environ.get('APP_NAME', 'CAC Financial')
app.config['APP_MENU'] = []
app.config['APP_AUTHORIZATION'] = []
app.config['APP_BASE_URL'] = os.environ.get('APP_BASE_URL', '')

# db SQLAlchemy
DATABASE_DIR = os.environ.get('DATABASE_DIR', os.path.dirname(os.path.abspath(__file__)))
database_file = "sqlite:///{}".format(os.path.join(DATABASE_DIR, "app.db"))
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



# register Financial
app.register_blueprint(Financial(url_prefix="/"))

# register Ged
app.register_blueprint(GedFile(url_prefix="/"))

# register Auth
app.register_blueprint(Auth(url_prefix="/"))

# register Param
app.register_blueprint(Params(url_prefix="/"))

# register Info
app.register_blueprint(Info(url_prefix="/"))

# register Static
APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
app.register_blueprint(Static(name="js", url_prefix="/js/", path=os.path.join(APP_PATH, "js")))
app.register_blueprint(Static(name="tabler", url_prefix="/tabler/", path=os.path.join(APP_PATH, "tabler")))
app.register_blueprint(Static(name="css", url_prefix="/css/", path=os.path.join(APP_PATH, "css")))
app.register_blueprint(Static(name="img", url_prefix="/img/", path=os.path.join(APP_PATH, "img")))
app.register_blueprint(Static(name="uploads", url_prefix="/uploads/", path=os.path.join(APP_PATH, "uploads")))


@app.route("/", methods=["GET", "POST"])
@login_required
def home():
    return render_template('index.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error-404.html'), 404


def create_app():
    db.init_app(app)
    with app.app_context():
        db.create_all()
    with app.app_context():
        for bp in app.blueprints:
            if 'init_db' in dir(app.blueprints[bp]):
                app.blueprints[bp].init_db()
    app.logger.setLevel(logging.DEBUG)
    return app


app = create_app()
if __name__ == "__main__":
    app.run(host=app.config["APP_HOST"], port=app.config["APP_PORT"], debug=app.config["APP_DEBUG"])
