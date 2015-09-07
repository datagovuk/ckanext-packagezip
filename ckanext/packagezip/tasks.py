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
import jinja2

def load_config(ckan_ini_filepath):
    import paste.deploy
    config_abs_path = os.path.abspath(ckan_ini_filepath)
    conf = paste.deploy.appconfig('config:' + config_abs_path)
    import ckan
    ckan.config.environment.load_environment(conf.global_conf,
                                             conf.local_conf)

@celery.task(name="packagezip.create_zip")
def create_zip(ckan_ini_filepath, package_id, queue='bulk'):
    load_config(ckan_ini_filepath)

    context = {'model': model, 'ignore_auth': True, 'session': model.Session}
    pkg = get_action('package_show')(context, {'id': package_id})

    directory = config.get('ckanext.packagezip.destination_dir')
    filename = "{0}.zip".format(pkg['name'])
    filepath = os.path.join(directory, filename)
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        datapackage = get_action('datapackage_show')(context, {'id': package_id})

        for res in datapackage['resources']:
           if res['cache_filepath'] and os.path.exists(res['cache_filepath']):
               zipf.write(res['cache_filepath'], res['path'])

        template = jinja2.Template('''<html>
                                        <head>
                                          <meta charset="UTF-8">
                                        </head>
                                        <body>
                                        <h1>{{datapackage.title}}</h1>
                                        <ul>
                                        {% for resource in datapackage.resources %}
                                          <li><a href="{{resource.path}}">{{resource.description}}</a></li>
                                        {% endfor %}
                                        </ul>
                                        </body>
                                      </html>''')

        zipf.writestr('index.html',
                      template.render(datapackage=datapackage).encode('utf8'))
        zipf.writestr('datapackage.json', json.dumps(datapackage, indent=4))

    PackageZip.create(package_id, filepath)
