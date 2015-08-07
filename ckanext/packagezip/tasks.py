from ckan.lib.celery_app import celery
from ckan import model
from ckan.logic import get_action
from ckanext.archiver.model import Archival
from pylons import config

import os
import zipfile
import tempfile
import json
import jinja2

@celery.task(name="packagezip.create_zip")
def create_zip(ckan_ini_filepath, package_id, queue='bulk'):
    context = {'model': model, 'ignore_auth': True, 'session': model.Session}
    pkg = get_action('package_show')(context, {'id': package_id})

    directory = config.get('ckanext.packagezip.destination_dir')
    filename = "{0}.zip".format(package_id)
    filepath = os.path.join(directory, filename)
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        datapackage = get_action('datapackage_show')(context, {'id': package_id})

        for res in datapackage['resources']:
           if res['cache_filepath']:
               zipf.write(res['cache_filepath'], res['path'])

        template = jinja2.Template('''<html>
                                        <h1>{{datapackage.title}}</h1>
                                        <ul>
                                        {% for resource in datapackage.resources %}
                                          <li><a href="{{resource.path}}">{{resource.description}}</a></li>
                                        {% endfor %}
                                        </ul>
                                      </html>''')

        zipf.writestr('index.html', template.render(datapackage=datapackage))
        zipf.writestr('datapackage.json', json.dumps(datapackage, indent=4))
