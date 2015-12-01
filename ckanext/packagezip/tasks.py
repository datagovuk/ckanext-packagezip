from ckan.lib.celery_app import celery
from ckan import model
from ckan.logic import get_action
from ckanext.archiver.model import Archival
from ckanext.packagezip.model import PackageZip
from pylons import config

import os
import zipfile
import tempfile
import json
import datetime
from jinja2 import Environment, PackageLoader

def load_config(ckan_ini_filepath):
    import paste.deploy
    config_abs_path = os.path.abspath(ckan_ini_filepath)
    conf = paste.deploy.appconfig('config:' + config_abs_path)
    import ckan
    ckan.config.environment.load_environment(conf.global_conf,
                                             conf.local_conf)

def register_translator():
    # Register a translator in this thread so that
    # the _() functions in logic layer can work
    from paste.registry import Registry
    from pylons import translator
    from ckan.lib.cli import MockTranslator
    global registry
    registry=Registry()
    registry.prepare()
    global translator_obj
    translator_obj=MockTranslator()
    registry.register(translator, translator_obj)

def datetimeformat(value, format='%d/%m/%Y - %H:%M'):
    return value.strftime(format)


@celery.task(name="packagezip.create_zip")
def create_zip(ckan_ini_filepath, package_id, queue='bulk'):
    load_config(ckan_ini_filepath)
    register_translator()
    log = create_zip.get_logger()

    context = {'model': model, 'ignore_auth': True, 'session': model.Session}
    pkg = get_action('package_show')(context, {'id': package_id})

    directory = config.get('ckanext.packagezip.destination_dir')
    if not os.path.exists(directory):
        log.info('Creating packagezip directory: %s' % directory)
        os.mkdir(directory)

    filename = "{0}.zip".format(pkg['name'])
    filepath = os.path.join(directory, filename)
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
        try:
            datapackage = get_action('datapackage_show')(context, {'id': package_id})
        except KeyError, e:
            log.error('Cannot find action - check this plugin is enabled: %s',
                      e)
            raise

        any_have_data = False
        for res in datapackage['resources']:
            if res['has_data']:
                any_have_data = True

            if res['cache_filepath'] and os.path.exists(res['cache_filepath']):
                zipf.write(res['cache_filepath'], res['path'])
                res['included_in_zip'] = True
            else:
                res['included_in_zip'] = False

        env = Environment(loader=PackageLoader('ckanext.packagezip', 'templates'))
        env.filters['datetimeformat'] = datetimeformat
        template = env.get_template('index.html')

        zipf.writestr('index.html',
                      template.render(datapackage=datapackage,
                                      date=datetime.datetime.now()).encode('utf8'))

        # Strip out unnecessary data from datapackage
        for res in datapackage['resources']:
            del res['has_data']
            if 'cache_filepath' in res:
                del res['cache_filepath']
            if 'reason' in res:
                del res['reason']
            if 'detected_format' in res:
                del res['detected_format']

        zipf.writestr('datapackage.json', json.dumps(datapackage, indent=4))

    statinfo = os.stat(filepath)
    filesize = statinfo.st_size

    package_zip = PackageZip.get_for_package(package_id)
    if not package_zip:
        PackageZip.create(package_id, filepath, filesize, has_data=any_have_data)
        log.info('Package zip created: %s', filepath)
    else:
        package_zip.filepath = filepath
        package_zip.updated = datetime.datetime.now()
        package_zip.size = filesize
        package_zip.has_data = any_have_data
        log.info('Package zip updated: %s', filepath)

        model.Session.add(package_zip)
        model.Session.commit()