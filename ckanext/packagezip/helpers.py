import ckan.plugins.toolkit as toolkit

from ckanext.packagezip.model import PackageZip

def has_packagezip(pkg):
    return PackageZip.get_for_package(pkg.id) != None

def packagezip_url(pkg):
    return toolkit.url_for('zipfile', name=pkg.name)

def datapackage_url(pkg):
    return toolkit.url_for('datapackage', name=pkg.name)
