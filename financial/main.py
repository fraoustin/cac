from flask import Blueprint, render_template, current_app, flash, request, redirect, url_for, send_from_directory
from flask_login import current_user, login_required
from auth import checkAuthorization
import sys
import os
from datetime import datetime
from db import db
from db.models import add_dbml, getParamValue, Param

__version__ = '0.0.1'


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
        self.add_url_rule('/analytics', 'analytics', analytics, methods=['GET', ])
        self.add_url_rule('/reconciliation', 'reconciliation', reconciliation, methods=['POST', 'GET'])

    def _init(self):
        current_app.logger.debug("init financial on first request")
        current_app.config['APP_AUTHORIZATION'].append("Compte")
        current_app.config['APP_AUTHORIZATION'].append("Axe")
        current_app.config['APP_AUTHORIZATION'].append("Mouvement")
        current_app.config['APP_AUTHORIZATION'].append("Analytic")
        current_app.config['APP_AUTHORIZATION'].append("Closed Mouvement")
        current_app.config['APP_MENU'].append({"href": "/comptes", "icon": "si-address-book", "title": "Compte", "authorization": "Compte"})
        current_app.config['APP_MENU'].append({"href": "/axes", "icon": "si-bolt", "title": "Axe", "authorization": "Axe"})
        current_app.config['APP_MENU'].append({"href": "/mouvements", "icon": "si-credit-card", "title": "Mouvement", "authorization": "Mouvement"})
        current_app.config['APP_MENU'].append({"href": "/analytics", "icon": "si-eye", "title": "Analytique", "authorization": "Analytic"})
        current_app.config['APP_MENU'].append({"href": "/reconciliation", "icon": "si-check-square", "title": "Reconciliation", "authorization": "Reconciliation"})

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
