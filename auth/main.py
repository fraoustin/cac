from flask import Blueprint, current_app, flash, request, render_template, redirect, url_for
import uuid
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
import datetime
import base64
import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash

from db import db
from db.models import add_dbml, getParamValue, Param

__version__ = '0.0.1'


getBool = {'on': True, 'off': False}
current_module = sys.modules[__name__]
add_dbml(os.path.join(os.path.dirname(os.path.abspath(__file__)), "map.dbml"), current_module)


class ModelUser(User):

    def __setattr__(self, name, value):
        if name in ('isadmin', 'gravatar') and isinstance(value, str):
            if value in ['true', 'True']:
                value = True
            else:
                value = False
        if name == 'password':
            value = generate_password_hash(value)
        db.Model.__setattr__(self, name, value)

    def __getattribute__(self, name):
        if name in ('lastconnection'):
            if db.Model.__getattribute__(self, name) is not None:
                return db.Model.__getattribute__(self, name).strftime('%d/%m/%Y')
            else:
                return ""
        if name not in ('id') and db.Model.__getattribute__(self, name) is None:
            return ""
        return db.Model.__getattribute__(self, name)

    def is_active(self):
        """True, as all users are active."""
        return not self.is_deleted

    def get_id(self):
        """Return the id to satisfy Flask-Login's requirements."""
        return self.id

    def is_anonymous(self):
        """False, as anonymous users aren't supported."""
        return False

    def is_authenticated(self):
        return True

    def check_password(self, password):
        if self.is_deleted is False:
            return check_password_hash(self.password, password)
        return False

    def has_authorization(self, key):
        if self.isadmin is True:
            return True
        if key in self.authorization.split(";"):
            return True
        return False

    def remove(self):
        if len(self.lastconnection) > 0:
            self.is_deleted = True
            self.save()
        else:
            db.session.delete(self)
            db.session.commit()


class checkAuthorization(object):

    def __init__(self, key):
        self.key = key

    def __call__(self, fn):
        def wrapped_f(*args, **kwargs):
            if current_user.has_authorization(self.key):
                return fn(*args, **kwargs)
            flash('You are not authorized', 'danger')
            return redirect("/")
        return wrapped_f


@login_required
def currentuser():
    return render_template('currentuser.html', backurl=None, authorizations=[])


@login_required
def view_user(id):
    try:
        user = ModelUser.query.filter_by(id=id).first()
        if user is not None:
            return render_template('user.html', user=user, backurl="/users", authorizations=[])
        else:
            raise ('user not found')
    except Exception:
        flash('Not user identified', 'danger')
        return render_template('user.html', user=current_user, backurl=None, authorizations=[])


@login_required
@checkAuthorization('Admin.new_user')
def new_user():
    return render_template('user.html', user=ModelUser(), backurl="/users", authorizations=[])


@login_required
@checkAuthorization('Admin.new_user')
def create_user():
    backurl = request.form.get('backurl', '/')
    user = ModelUser.query.filter_by(email=request.form['email']).first()
    if user is None:
        user = ModelUser()
        user.email = request.form['email']
        password = request.form['password']
        if len(password) == 0:
            password = str(uuid.uuid4())
        apikey = str(uuid.uuid4())
        token = str(uuid.uuid4())
        user.password = password
        user.apikey = apikey
        user.token = token
        user.name = request.form['name']
        user.forname = request.form['forname']
        user.isadmin = getBool.get(request.form.get('isadmin', 'off'), False)
        authorization = ""
        for key in [key for key in request.form.keys() if key.startswith('autho-')]:
            if getBool.get(request.form.get(key, 'off'), False) is True:
                authorization = "%s%s;" % (authorization, key[6:])
        user.authorization = authorization
        user.save()
        flash('User %s is created' % user.name, 'success')
        return redirect(backurl)
    else:
        if user.is_deleted is True:
            return update_user(user.id)
        else:
            flash('User %s is already created' % user.name, 'success')
            return redirect(backurl)


@login_required
def update_user(id):
    backurl = request.form.get('backurl', '/')
    user = ModelUser.query.filter_by(id=id).first()
    if user is not None:
        if current_user.isadmin or current_user.id == user.id:
            if "email" in request.form:
                user.email = request.form['email']
            if "name" in request.form:
                user.name = request.form['name']
            if "forname" in request.form:
                user.forname = request.form['forname']
            if 'password' in request.form and len(request.form['password']):
                user.password = request.form['password']
            if current_user.isadmin:
                if len(request.form.get('apikey', '')):
                    user.apikey = request.form['apikey']
                if len(request.form.get('token', '')):
                    user.token = request.form['token']
                if len(request.form.get('isadmin', '')) and current_user.id != user.id:
                    user.isadmin = getBool.get(request.form['isadmin'], False)
                authorization = ""
                for key in [key for key in request.form.keys() if key.startswith('autho-')]:
                    if getBool.get(request.form.get(key, 'off'), False) is True:
                        authorization = "%s%s;" % (authorization, key[6:])
                user.authorization = authorization
            user.save()
            flash('User is saved', 'success')
        else:
            flash('You are not authorized', 'danger')
    else:
        flash('User doesn\'t exist', 'warning')
    return redirect(backurl)


@login_required
@checkAuthorization('Admin.delete_user')
def delete_user(id):
    backurl = request.form.get('backurl', '/')
    del_user(id)
    return redirect(backurl)


@login_required
@checkAuthorization('Admin.delete_user')
def del_user(id):
    user = ModelUser.query.filter_by(id=id).first()
    if not user:
        flash('ModelUser doesn\'t exist', 'warning')
        return {}, 404
    if user.id == current_user.id:
        flash('You can not delete yourself', 'warning')
        return {}, 403
    if user is not None:
        name = user.name
        user.remove()
        flash('User %s is deleted' % name, 'danger')
        return {}, 200


@login_required
@checkAuthorization('Admin.users')
def users():
    return render_template("users.html", users=ModelUser.query.filter_by(is_deleted=False).order_by(ModelUser.name).all(), backurl=None, authorizations=[])


def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = ModelUser.query.filter_by(email=email).first()
        if user is not None and user.check_password(password):
            user.lastconnection = datetime.date.today()
            db.session.commit()
            login_user(user, remember=True)
            return redirect("%s/" % current_app.config['APP_BASE_URL'])
        else:
            flash('User or password is wrong', 'danger')
            return render_template('login.html'), 403
    return render_template('login.html')


def logout():
    logout_user()
    return redirect(url_for('home'))


@login_required
def get_all_users():
    users = ModelUser.query.all()
    liste_users = []
    for user in users:
        liste_users.append(user.to_dict())
    return {"ModelUsers": liste_users}, 200


@login_required
def get_user(id):
    try:
        user = ModelUser.query.filter_by(id=id).first()
        return user.to_dict(), 200
    except Exception as e:
        return {"Erreur": str(e)}, 404


class Auth(Blueprint):

    def __init__(self, name='auth', import_name=__name__, *args, **kwargs):
        Blueprint.__init__(self, name, import_name, template_folder='templates', *args, **kwargs)
        self.before_app_first_request(self._init)
        self.add_url_rule('/logout', 'logout', logout, methods=['GET'])
        self.add_url_rule('/login', 'login', login, methods=['POST', 'GET'])
        self.add_url_rule('/currentuser', 'currentuser', currentuser, methods=['GET'])
        self.add_url_rule('/user/<int:id>', 'view_user', view_user, methods=['GET'])
        self.add_url_rule('/user', 'new_user', new_user, methods=['GET'])
        self.add_url_rule('/user', 'create_user', create_user, methods=['POST'])
        self.add_url_rule('/user/<int:id>', 'update_user', update_user, methods=['POST'])
        self.add_url_rule('/deluser/<int:id>', 'delete_user', delete_user, methods=['POST'])
        self.add_url_rule('/users', 'users', users, methods=['GET'])

    def _init(self):
        current_app.logger.debug("init auth on first request")
        current_app.config['APP_AUTHORIZATION'].append("Admin.users")
        current_app.config['APP_AUTHORIZATION'].append("Admin.delete_user")
        current_app.config['APP_AUTHORIZATION'].append("Admin.new_user")
        current_app.config['APP_AUTHORIZATION'].append("Admin.update_user")
        current_app.config['APP_MENU'].append({"href": "/users", "icon": "si-user", "title": "Utilisateurs", "authorization": "Admin.users"})
        self._login_manager = LoginManager()
        self._login_manager.init_app(current_app)
        if not current_app.secret_key:
            current_app.secret_key = str(uuid.uuid4())
            current_app.logger.warning("not secret key for app, generate secret key")

        @self._login_manager.user_loader
        def user_loader(id):
            return ModelUser.query.get(id)

        @self._login_manager.unauthorized_handler
        def unauthorized():
            return redirect(url_for('auth.login'))

        @self._login_manager.request_loader
        def load_user_from_request(request):
            # first, try to login using the api_key url arg
            apikey = request.args.get('api')
            if apikey:
                user = ModelUser.query.filter_by(apikey=apikey).first()
                if user is not None:
                    return user

            # next, try to login using Basic Auth
            token = request.headers.get('Authorization')
            if token:
                token = token.replace('Basic ', '', 1)
                try:
                    token = base64.b64decode(token)
                except Exception:
                    pass
                user = ModelUser.query.filter_by(token=token).first()
                if user is not None:
                    return user

            # finally, return None if both methods did not login the user
            return None

    def init_db(self):
        if len(ModelUser.query.all()) == 0:
            u = ModelUser(email='admin@localhost', name="Admin", password="admin", isadmin=True)
            db.session.add(u)
            db.session.commit()
            current_app.logger.info("create user admin@localhost")
        else:
            current_app.logger.debug("we have least one user")

    def register(self, app, options):
        try:
            Blueprint.register(self, app, options)
        except Exception:
            app.logger.error("init auth on register is failed")
