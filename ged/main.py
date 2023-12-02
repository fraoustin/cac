from flask import Blueprint, render_template, current_app, flash, request, redirect, url_for, send_from_directory
from flask_login import current_user, login_required
from auth import checkAuthorization
import sys
import os
import tempfile
import random
from datetime import datetime
from db.models import add_dbml

__version__ = '0.0.1'


current_module = sys.modules[__name__]
add_dbml(os.path.join(os.path.dirname(os.path.abspath(__file__)), "map.dbml"), current_module)


@login_required
@checkAuthorization('Ged')
def geds():
    return render_template('geds.html', geds=Ged.query.order_by(Ged.name).all())


@login_required
@checkAuthorization('Ged')
def create_ged():
    print("coucou1")
    if request.method == 'POST':
        obj = Ged()
        for key in [key for key in request.form.keys() if key != 'file']:
            obj.__setattr__(key, request.form[key])
        print("coucou2")
        file = request.files['file']
        print("coucou3")
        if 'file' in request.files:
            print("coucou4")
            file = request.files['file']
            now = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = '%s_%s.%s' % (now, random.randrange(0, 10000), file.filename.rsplit('.', 1)[1].lower())
            pathfile = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            print("coucou5")
            file.save(pathfile)
            print("coucou6") 
            obj.path = filename
            obj.name = file.filename
        obj.save()
        flash('File %s is created' % obj.name, 'success')
        return redirect(url_for('ged.update_ged', id=obj.id))
    return render_template('ged.html', ged=Ged())


@login_required
@checkAuthorization('Ged')
def update_ged(id):
    if request.method == 'POST':
        obj = Ged.query.filter_by(id=id).first()
        if obj is None:
            flash("File %s doesn't exist" % id, 'warning')
        else:
            for key in [key for key in request.form.keys() if key != 'file']:
                obj.__setattr__(key, request.form[key])
            file = request.files['file']
            if 'file' in request.files:
                file = request.files['file']
                now = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = '%s_%s.%s' % (now, random.randrange(0, 10000), file.filename.rsplit('.', 1)[1].lower())
                pathfile = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(pathfile)
                obj.path = filename
            obj.save()
            flash('File %s is updated' % obj.name, 'success')
        return redirect(url_for('ged.update_ged', id=obj.id))
    return render_template('ged.html', ged=Ged.query.filter_by(id=id).first())


@login_required
@checkAuthorization('Ged')
def delete_ged(id):
    obj = Ged.query.filter_by(id=id).first()
    if not obj:
        flash('File doesn\'t exist', 'warning')
    else:
        name = obj.name
        obj.remove()
        flash('File %s is deleted' % name, 'danger')
    return redirect(url_for('ged.geds'))



class GedFile(Blueprint):

    def __init__(self, name='ged', import_name=__name__, dir_uploads="./files/uploads", *args, **kwargs):
        Blueprint.__init__(self, name, import_name, template_folder='templates', *args, **kwargs)
        self.before_app_first_request(self._init)
        self.dir_uploads = dir_uploads
        self.add_url_rule('/geds', 'geds', geds, methods=['GET', ])
        self.add_url_rule('/ged', 'new_ged', create_ged, methods=['POST', 'GET'])
        self.add_url_rule('/ged/<int:id>', 'update_ged', update_ged, methods=['POST', 'GET'])
        self.add_url_rule('/delged/<int:id>', 'delete_ged', delete_ged, methods=['POST', ])

    def _init(self):
        current_app.logger.debug("init financial on first request")
        current_app.config['APP_AUTHORIZATION'].append("Ged")
        current_app.config['APP_MENU'].append({"href": "/geds", "icon": "si-file", "title": "Fichiers", "authorization": "Ged"})
        current_app.config['UPLOAD_FOLDER'] = self.dir_uploads
        if not os.path.isdir(current_app.config['UPLOAD_FOLDER']):
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        
    def register(self, app, options):
        try:
            Blueprint.register(self, app, options)
        except Exception:
            app.logger.error("init ged on register is failed")
