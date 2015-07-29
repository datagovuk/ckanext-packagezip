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
        datapackage = {
            'name': pkg['name'],
            'title': pkg['title'],
            'resources': [],
        }

        for res in pkg['resources']:
           archival = Archival.get_for_resource(res['id'])
           if archival and archival.cache_filepath:
               path, resource_id, filename = archival.cache_filepath.rsplit('/', 2)
               zipf.write(archival.cache_filepath, 'resources/{0}'.format(filename))

               datapackage['resources'].append({'path': 'resources/{0}'.format(filename),
                                                'description': res['description'],
                                                'url': res['url']})

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
