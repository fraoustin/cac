from flask_sqlalchemy import SQLAlchemy, Model
from sqlalchemy.engine import Engine
from sqlalchemy import event


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class GenericModel(Model):

    @classmethod
    def get(cls, id):
        try:
            return cls.query.filter_by(id=id).first()
        except Exception:
            return None

    @classmethod
    def all(cls, sortby=None):
        if sortby:
            return cls.query.order_by(sortby).all()
        return cls.query.all()

    @classmethod
    def remove(cls, id):
        try:
            cls.query.filter_by(id=id).first().remove()
            return True
        except Exception:
            return False

    def __getattribute__(self, name):
        if name not in ('id') and Model.__getattribute__(self, name) is None:
            return ""
        return Model.__getattribute__(self, name)

    def save(self):
        try:
            if self.id is None:
                db.session.add(self)
            db.session.commit()
            return True
        except Exception:
            db.session.commit()
            return False

    def remove(self):
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def filter(self, elt, key, target):
        return [obj for obj in getattr(self, elt) if getattr(obj, key) == target]


db = SQLAlchemy(model_class=GenericModel)
