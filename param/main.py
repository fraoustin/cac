from flask import Blueprint, render_template, current_app, flash, request, redirect, url_for
import importlib
from auth import checkAuthorization, login_required
import sys
import os
from db import db
from db.models import add_dbml, Param


__version__ = '0.0.1'


@login_required
@checkAuthorization('Params')
def params():
    if request.method == 'POST':
        for name in request.form.keys():
            param = Param.query.filter_by(name=name).first()
            if param is not None:
                param.value = request.form[name]
                param.save()
        render_template('params.html', params=Param.query.all())
    return render_template('params.html', params=Param.query.all())


class Params(Blueprint):

    def __init__(self, name='param', import_name=__name__, *args, **kwargs):
        Blueprint.__init__(self, name, import_name, template_folder='templates', *args, **kwargs)
        self.before_app_first_request(self._init)
        self.add_url_rule('/params', 'params', params, methods=['POST', 'GET'])

    def _init(self):
        current_app.logger.debug("init param on first request")
        current_app.config['APP_AUTHORIZATION'].append("Params")
        current_app.config['APP_MENU'].append({"href": "/params", "icon": "si-tools", "title": "Paramètres", "authorization": "Params"})

    def register(self, app, options):
        try:
            Blueprint.register(self, app, options)
        except Exception:
            app.logger.error("init params on register is failed")
