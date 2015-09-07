import uuid
from datetime import datetime

from sqlalchemy import Column, MetaData
from sqlalchemy import types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound

import ckan.model as model

log = __import__('logging').getLogger(__name__)

Base = declarative_base()


def make_uuid():
    return unicode(uuid.uuid4())

metadata = MetaData()

class PackageZip(Base):
    """
    Details of the zip of cached resources in a package. 
    """
    __tablename__ = 'package_zip'

    id = Column(types.UnicodeText, primary_key=True, default=make_uuid)
    package_id = Column(types.UnicodeText, nullable=False, index=True)

    # Details of last successful zip
    filepath = Column(types.UnicodeText)
    size = Column(types.BigInteger, default=0)

    created = Column(types.DateTime, default=datetime.now)
    updated = Column(types.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return '<PackageZip {0}>'.format(self.filepath)

    @classmethod
    def get_for_package(cls, package_id):
        '''Returns the package zip for the given package.'''
        try:
            return model.Session.query(cls) \
                        .filter(cls.package_id==package_id) \
                        .one()
        except NoResultFound:
            return None

    @classmethod
    def create(cls, package_id, filepath):
        pz = cls()
        pz.package_id = package_id
        pz.filepath = filepath

        model.Session.add(pz)
        model.Session.commit()

def init_tables(engine):
    Base.metadata.create_all(engine)
    log.info('Package Zip database tables are set-up')
