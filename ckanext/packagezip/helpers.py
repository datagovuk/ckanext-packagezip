import ckan.plugins.toolkit as toolkit

from ckanext.packagezip.model import PackageZip

def has_packagezip(pkg):
    return PackageZip.get_for_package(pkg.id) != None

def packagezip_url(pkg):
    return toolkit.url_for('zipfile', name=pkg.name)

def packagezip_size(pkg):
    pz = PackageZip.get_for_package(pkg.id)
    if pz:
        return pz.size

def packagezip_has_data(pkg):
    pz = PackageZip.get_for_package(pkg.id)
    if pz:
        return pz.has_data

def datapackage_url(pkg):
    return toolkit.url_for('datapackage', name=pkg.name)
