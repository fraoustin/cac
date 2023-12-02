import os
from db import db
from pydbml import PyDBML
from dbml_to_sqlalchemy import createModel
from pathlib import Path
import sys

current_module = sys.modules[__name__]


def add_dbml(path, module=current_module):
    parsed = PyDBML(Path(path))
    for table in parsed.tables:
        createModel(table, db.Model, module=module)


add_dbml(os.path.join(os.path.dirname(os.path.abspath(__file__)), "map.dbml"), current_module)


def getParamValue(name):
    param = Param.query.filter_by(name=name).first()
    if param is None:
        return None
    try:
        if param.type == 'string':
            return str(param.value)
        if param.type == 'int':
            return int(param.value)
        if param.type == 'float':
            return float(param.value)
    except Exception:
        return None


def addParam(name, type='string', value=''):
    param = Param()
    param.name = name
    param.type = string
    param.value = value
    param.save()
