import ckan.plugins as p
from ckanext.archiver.interfaces import IPipe
from pylons import config

import os
import logging
import uuid

log = logging.getLogger(__name__)

class PackageZipPlugin(p.SingletonPlugin):
    p.implements(IPipe, inherit=True)
    p.implements(p.IActions, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)

    def receive_data(self, operation, queue, **params):
        from ckan.lib.celery_app import celery
        if operation == 'package-archived':
            package_id = params.get('package_id')

            ckan_ini_filepath = os.path.abspath(config['__file__'])
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
            'datapackage',
            '/dataset/{name}/datapackage.json',
            controller=controller,
            action='datapackage'
        )
        map.connect(
            'zipfile',
            '/dataset/{name}/datapackage.zip',
            controller=controller,
            action='zipfile'
        )
        return map

    def get_helpers(self):
        import ckanext.packagezip.helpers as helpers
        helper_dict = {
            'has_packagezip': helpers.has_packagezip,
            'packagezip_has_data': helpers.packagezip_has_data,
            'packagezip_url': helpers.packagezip_url,
            'packagezip_size': helpers.packagezip_size,
            'datapackage_url': helpers.datapackage_url,
        }
        return helper_dict
