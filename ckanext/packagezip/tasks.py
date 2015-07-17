from ckan.lib.celery_app import celery
from ckan import model
from ckan.logic import get_action
from ckanext.archiver.model import Archival
from pylons import config

import os
import zipfile

@celery.task(name="packagezip.create_zip")
def create_zip(ckan_ini_filepath, package_id, queue='bulk'):
    context = {'model': model, 'ignore_auth': True, 'session': model.Session}
    pkg = get_action('package_show')(context, {'id': package_id})

    directory = config.get('ckanext.packagezip.destination_dir')
    filename = "{0}.zip".format(package_id)
    filepath = os.path.join(directory, filename)
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for res in pkg['resources']:
           archival = Archival.get_for_resource(res['id'])
           if archival and archival.cache_filepath:
               path, resource_id, filename = archival.cache_filepath.rsplit('/', 2)
               zipf.write(archival.cache_filepath, filename)
