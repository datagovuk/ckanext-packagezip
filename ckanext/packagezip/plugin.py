import ckan.plugins as p
from ckanext.archiver.interfaces import IPipe
from ckan.lib.celery_app import celery
from pylons import config

import os
import logging
import uuid

log = logging.getLogger(__name__)

class PackageZipPlugin(p.SingletonPlugin):
    p.implements(IPipe, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IRoutes, inherit=True)

    def receive_data(self, operation, queue, **params):
        if operation == 'package-archived':
            package_id = params.get('package_id')

            ckan_ini_filepath = os.path.abspath(config.__file__)
            task_id = str(uuid.uuid4())
            celery.send_task('packagezip.create_zip',
                             args=[ckan_ini_filepath, package_id, queue],
                             task_id=task_id, queue=queue)
            log.debug('Package zip of package put into celery queue %s: %s', queue, package_id)

    def get_actions(self):
        from ckanext.packagezip import logic_action as logic
        return {
            'datapackage_show': logic.datapackage_show,
            }

    def after_map(self, map):
        controller = 'ckanext.packagezip.controllers:PackageZipController'
        map.connect(
            '/dataset/{id}/datapackage.json',
            controller=controller,
            action='datapackage'
        )
        return map

