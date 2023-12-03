from flask import Blueprint, render_template, current_app, flash, request, redirect, url_for, send_from_directory
from flask_login import current_user, login_required
from auth import checkAuthorization
import sys
import os
from datetime import datetime
from db import db
from db.models import add_dbml, getParamValue, Param
import json

__version__ = '0.0.3'


current_module = sys.modules[__name__]
add_dbml(os.path.join(os.path.dirname(os.path.abspath(__file__)), "map.dbml"), current_module)


@login_required
@checkAuthorization('Compte')
def comptes():
    return render_template('comptes.html', comptes=Compte.query.all())


@login_required
@checkAuthorization('Compte')
def create_compte():
    if request.method == 'POST':
        obj = Compte()
        for key in request.form.keys():
            obj.__setattr__(key, request.form[key])
        obj.save()
        if obj.status.name == typ_status.fermer.name:
            obj.default = typ_default.non.name
            obj.save()
        if obj.default.name == typ_default.oui.name:
            if len(Compte.query.filter_by(default=typ_default.oui.name).all()) > 1:
                obj.default = typ_default.non.name
                obj.save()
        flash('Compte %s is created' % obj.name, 'success')
        return redirect(url_for('financial.update_compte', id=obj.id))
    return render_template('compte.html', compte=Compte(status=typ_status.ouvert, default=typ_default.oui))


@login_required
@checkAuthorization('Compte')
def update_compte(id):
    if request.method == 'POST':
        obj = Compte.query.filter_by(id=id).first()
        if obj is None:
            flash("Compte %s doesn't exist" % id, 'warning')
        else:
            for key in request.form.keys():
                obj.__setattr__(key, request.form[key])
            obj.save()
            flash('Compte %s is updated' % obj.name, 'success')
        return redirect(url_for('financial.update_compte', id=obj.id))
    return render_template('compte.html', compte=Compte.query.filter_by(id=id).first())


@login_required
@checkAuthorization('Axe')
def axes():
    return render_template('axes.html', axes=Axe.query.all())


@login_required
@checkAuthorization('Axe')
def create_axe():
    if request.method == 'POST':
        obj = Axe()
        for key in request.form.keys():
            obj.__setattr__(key, request.form[key])
        obj.save()
        flash('Axe %s is created' % obj.name, 'success')
        return redirect(url_for('financial.update_axe', id=obj.id))
    return render_template('axe.html', axe=Axe())


@login_required
@checkAuthorization('Compte')
def update_axe(id):
    if request.method == 'POST':
        obj = Axe.query.filter_by(id=id).first()
        if obj is None:
            flash("Axe %s doesn't exist" % id, 'warning')
        else:
            for key in request.form.keys():
                obj.__setattr__(key, request.form[key])
            obj.save()
            flash('Axe %s is updated' % obj.name, 'success')
        return redirect(url_for('financial.update_axe', id=obj.id))
    return render_template('axe.html', axe=Axe.query.filter_by(id=id).first())


@login_required
@checkAuthorization('Mouvement')
def mouvements():
    if request.method == 'POST':
        obj = Mvt()
        for key in [ key for key in request.form.keys() if key.startswith('axe-') is False]:
            if key == 'value':
                val = float(request.form[key].replace(',','.'))
                if (request.form['typ'] == 'debit' and val > 0) or (request.form['typ'] == 'credit' and val < 0):
                    val = val * -1
                obj.__setattr__(key, val)
            elif key == 'dte':
                obj.__setattr__(key, datetime.strptime(str(request.form[key]), '%d/%m/%Y'))
            else:
                obj.__setattr__(key, request.form[key])
        obj.closed = 'non'
        obj.save()
        # create analytic
        ana = Analytic()
        ana.id_mvt = obj.id
        ana.value = obj.value
        ana.dte = obj.dte
        ana.tiers = obj.tiers
        ana.description  = obj.description
        ana.save()
        for key in [ key for key in request.form.keys() if key.startswith('axe-') is True]:
            anaaxe = Analyticaxe()
            anaaxe.id_analytic = ana.id
            anaaxe.id_axe = key[4:]
            anaaxe.value = request.form[key]
            anaaxe.save()
        flash('Mouvement %s is created with value %s' % (obj.id, '%.2f €' % obj.value), 'success')
    return render_template('mouvements.html', mvts=Mvt.query.order_by(Mvt.dte.desc()).all(), axes=Axe.query.all(), comptes=Compte.query.all(), tiers=getParamValue('tiers').split(";"), now=datetime.now())


@login_required
@checkAuthorization('Mouvement')
def mouvement(id):
    return render_template('mouvement.html', mvt=Mvt.query.filter_by(id=id).first(), axes=Axe.query.all())


@login_required
@checkAuthorization('Analytic')
def analytics():
    return render_template('analytics.html', analytics=Analytic.query.order_by(Analytic.dte.desc()).all(), axes=Axe.query.all())

@login_required
@checkAuthorization('Reconciliation')
def reconciliation():
    if request.method == 'POST': 
        for key in request.form.keys():
            obj = Mvt.query.filter_by(id=key).first()
            obj.closed = 'oui'
            obj.save()
        flash('Reconciliation is ok', 'success')
    return render_template('reconciliation.html', mvts=Mvt.query.order_by(Mvt.dte).all())

@login_required
@checkAuthorization('Note')
def notes():
    if current_user.has_authorization('Valid Note'):
        return render_template('notes.html', notes=Note.query.order_by(Note.dte.desc()).all())
    else:
        return render_template('notes.html', notes=Note.query.filter_by(who=current_user.name).order_by(Note.dte.desc()).all())


@login_required
@checkAuthorization('Note')
def create_note():
    if request.method == 'POST':
        obj = Note()
        for key in request.form.keys():
            if key == 'dte':
                obj.__setattr__(key, datetime.strptime(str(request.form[key]), '%d/%m/%Y'))
            else:
                obj.__setattr__(key, request.form[key])
        if 'who' not in request.form.keys():
            obj.who = current_user.name
        obj.save()
        flash('Note %s is created' % obj.title, 'success')
        return redirect(url_for('financial.update_note', id=obj.id))
    return render_template('note.html', note=Note(dte=datetime.now(), who=current_user.name, status=note_status.draft))


@login_required
@checkAuthorization('Note')
def update_note(id):
    if request.method == 'POST':
        obj = Note.query.filter_by(id=id).first()
        if obj is None or obj.status.name != 'draft' or ( obj.who != current_user.name and current_user.has_authorization('Valid Note') is False) or ('who' in request.form.keys() and  request.form['who'] != current_user.name  and current_user.has_authorization('Valid Note') is False):
            flash("Note %s doesn't exist or is not modified by you" % id, 'warning')
        else:
            for key in request.form.keys():
                if key == 'dte':
                    obj.__setattr__(key, datetime.strptime(str(request.form[key]), '%d/%m/%Y'))
                else:
                    obj.__setattr__(key, request.form[key])
            obj.save()
            flash('Note %s is updated' % obj.title, 'success')
        return redirect(url_for('financial.update_note', id=obj.id))
    return render_template('note.html', note=Note.query.filter_by(id=id).first(), axes=Axe.query.all())


@login_required
@checkAuthorization('Note')
def add_frais(id):
    if request.method == 'POST':
        obj = Note.query.filter_by(id=id).first()
        if obj is None or obj.status.name != 'draft' or (obj.who != current_user.name and current_user.has_authorization('Valid Note') is False):
            flash("Note %s doesn't exist or is not modified by you" % id, 'warning')
        else:
            # create noteanalytic
            ana = Noteanalytic()
            ana.id_note = id        
            val = float(request.form['value'].replace(',','.'))
            if val < 0:
                val = val * -1
            ana.value = val
            ana.dte = datetime.strptime(str(request.form['dte']), '%d/%m/%Y')
            ana.tiers = request.form['tiers']
            ana.description  = request.form['description']
            ana.save()
            for key in [ key for key in request.form.keys() if key.startswith('axe-') is True]:
                anaaxe = Noteanalyticaxe()
                anaaxe.id_analytic = ana.id
                anaaxe.id_axe = key[4:]
                anaaxe.value = request.form[key]
                anaaxe.save()
        return redirect(url_for('financial.update_note', id=id))
    return render_template('frais.html', axes=Axe.query.all(), tiers=getParamValue('tiers').split(";"), now=datetime.now(), note=Note.query.filter_by(id=id).first())


@login_required
@checkAuthorization('Note')
def rm_frais(id):
    obj = Noteanalytic.query.filter_by(id=id).first()
    if obj is None or obj.note.status.name != 'draft' or obj.note.who != current_user.name:
        flash("Frais %s doesn't exist or is not modified by you" % id, 'warning')
    else:
        # rm noteanalytic
        obj.remove()
    return redirect(url_for('financial.update_note', id=obj.note.id))



@login_required
@checkAuthorization('Valid Note')
def validnotes():
    return render_template('validnotes.html', notes=Note.query.filter_by(status='presented').order_by(Note.dte).all())

@login_required
@checkAuthorization('Valid Note')
def update_validnote(id, status):
    obj = Note.query.filter_by(id=id).first()
    if obj is None or obj.status.name != 'presented' :
        flash("Note %s doesn't exist or is not modified by you" % id, 'warning')
    else:
        obj.status = status
        if status == 'valided':            
            mvt = Mvt()
            mvt.id_compte = Compte.query.filter_by(default='oui').first().id
            mvt.typ = 'debit'
            mvt.dte = datetime.now()
            mvt.value = sum([ elt.value for elt in obj.noteanalytics]) * -1
            mvt.tiers = obj.who
            mvt.description = "note #%s" % obj.id
            mvt.closed = 'non'
            mvt.save()
            for noteanalytic in obj.noteanalytics:
                # create analytic
                ana = Analytic()
                ana.id_mvt = mvt.id
                ana.value = noteanalytic.value  * -1
                ana.dte = noteanalytic.dte
                ana.tiers = noteanalytic.tiers
                ana.description  = noteanalytic.description
                ana.save()
                for noteanalyticaxe in noteanalytic.noteanalyticaxes:
                    anaaxe = Analyticaxe()
                    anaaxe.id_analytic = ana.id
                    anaaxe.id_axe = noteanalyticaxe.id_axe
                    anaaxe.value = noteanalyticaxe.value
                    anaaxe.save()
        obj.save()
        flash('Note %s of %s is %s for %s €' % (obj.title, obj.who, obj.status.name, "%.2f" % sum([ elt.value for elt in obj.noteanalytics])), 'success')
    return redirect(url_for('financial.validnotes'))

@login_required
@checkAuthorization('Valid Note')
def update_fraisaxe(id, axe, value):
    anaaxe = Noteanalyticaxe.query.filter_by(id_analytic=id).filter_by(id_axe=axe).first()
    anaaxe.value = value
    anaaxe.save()
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 


class Financial(Blueprint):

    def __init__(self, name='financial', import_name=__name__, *args, **kwargs):
        Blueprint.__init__(self, name, import_name, template_folder='templates', *args, **kwargs)
        self.before_app_first_request(self._init)
        self.add_url_rule('/comptes', 'comptes', comptes, methods=['GET', ])
        self.add_url_rule('/compte', 'new_compte', create_compte, methods=['POST', 'GET'])
        self.add_url_rule('/compte/<int:id>', 'update_compte', update_compte, methods=['POST', 'GET'])
        self.add_url_rule('/axes', 'axes', axes, methods=['GET', ])
        self.add_url_rule('/axe', 'new_axe', create_axe, methods=['POST', 'GET'])
        self.add_url_rule('/axe/<int:id>', 'update_axe', update_axe, methods=['POST', 'GET'])
        self.add_url_rule('/mouvements', 'mouvements', mouvements, methods=['POST', 'GET'])
        self.add_url_rule('/mouvement/<int:id>', 'mouvement', mouvement, methods=['GET', ])
        self.add_url_rule('/analytics', 'analytics', analytics, methods=['GET', ])
        self.add_url_rule('/reconciliation', 'reconciliation', reconciliation, methods=['POST', 'GET'])
        self.add_url_rule('/notes', 'notes', notes, methods=['POST', 'GET'])
        self.add_url_rule('/note', 'new_note', create_note, methods=['POST', 'GET'])
        self.add_url_rule('/note/<int:id>', 'update_note', update_note, methods=['POST', 'GET'])
        self.add_url_rule('/frais/<int:id>', 'add_frais',add_frais, methods=['POST', 'GET'])
        self.add_url_rule('/rmfrais/<int:id>', 'rm_frais',rm_frais, methods=['GET', ])
        self.add_url_rule('/validnotes', 'validnotes', validnotes, methods=['GET', ])
        self.add_url_rule('/validnotes/<int:id>/<status>', 'update_validnote', update_validnote, methods=['GET', ])
        self.add_url_rule('/updatefraisaxe/<int:id>/<int:axe>/<value>', 'update_fraisaxe', update_fraisaxe, methods=['GET', ])

    def _init(self):
        current_app.logger.debug("init financial on first request")
        current_app.config['APP_AUTHORIZATION'].append("Compte")
        current_app.config['APP_AUTHORIZATION'].append("Axe")
        current_app.config['APP_AUTHORIZATION'].append("Mouvement")
        current_app.config['APP_AUTHORIZATION'].append("Analytic")
        current_app.config['APP_AUTHORIZATION'].append("Reconciliation")
        current_app.config['APP_AUTHORIZATION'].append("Note")
        current_app.config['APP_AUTHORIZATION'].append("Valid Note")
        current_app.config['APP_MENU'].append({"href": "/comptes", "icon": "si-address-book", "title": "Compte", "authorization": "Compte"})
        current_app.config['APP_MENU'].append({"href": "/axes", "icon": "si-bolt", "title": "Axe", "authorization": "Axe"})
        current_app.config['APP_MENU'].append({"href": "/mouvements", "icon": "si-credit-card", "title": "Mouvement", "authorization": "Mouvement"})
        current_app.config['APP_MENU'].append({"href": "/analytics", "icon": "si-eye", "title": "Analytique", "authorization": "Analytic"})
        current_app.config['APP_MENU'].append({"href": "/reconciliation", "icon": "si-check-square", "title": "Reconciliation", "authorization": "Reconciliation"})
        current_app.config['APP_MENU'].append({"href": "/notes", "icon": "si-note", "title": "Note de frais", "authorization": "Note"})
        current_app.config['APP_MENU'].append({"href": "/validnotes", "icon": "si-inbox", "title": "Validation Note de frais", "authorization": "Valid Note"})

    def init_db(self):
        if getParamValue('tiers') is None:
            param = Param(name='tiers', type="string", value="")
            db.session.add(param)
            db.session.commit()
            current_app.logger.info("create param tiers")
        else:
            current_app.logger.debug("we have already param tiers")

    def register(self, app, options):
        try:
            Blueprint.register(self, app, options)
        except Exception:
            app.logger.error("init doslot on register is failed")
