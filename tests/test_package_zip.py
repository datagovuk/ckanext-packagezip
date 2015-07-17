from ckan import model
from ckan.tests import BaseCase
from ckan.logic import get_action
from ckanext.archiver.interfaces import IPipe
from ckanext.archiver.tasks import update

import mock
import os
import zipfile
import uuid
import json

from pylons import config

class TestPackageZip(BaseCase):
    @classmethod
    def setup_class(cls):
        dest_dir = config.get('ckanext.packagezip.destination_dir')
        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)

        cls.config = config.__file__

    def setup(self):
        self.pkg = self._test_package('http://example.com/index.html')

    def _test_package(self, url, format=None):
        context = {'model': model, 'ignore_auth': True, 'session': model.Session, 'user': 'test'}
        name = str(uuid.uuid4())
        pkg = {'name': name, 'resources': [
            {'url': url, 'format': format or 'TXT', 'description': 'Test'}
            ]}
        pkg = get_action('package_create')(context, pkg)

        for res in pkg['resources']:
            update(self.config, res['id']) # This causes test to depend on internet

        return pkg

    @mock.patch('ckan.lib.celery_app.celery.send_task')
    def test_package_archive_event_causes_create_zip_task(self, send_task):
        package_id = 'abc123'
        queue = 'queue1'
        
        # Signal from ckanext-archiver that a package has been archived
        IPipe.send_data('package-archived',
                        package_id=package_id,
                        queue=queue,
                        cache_filepath='CCC')

        assert send_task.called == True

        args, kwargs = send_task.call_args
        assert args == ('packagezip.create_zip',)

        assert kwargs['args'][1] == package_id
        assert kwargs['args'][2] == queue

    @mock.patch('ckan.lib.celery_app.celery.send_task')
    def test_resource_archive_event_doesnt_causes_create_zip_task(self, send_task):
        resource_id = 'abc123'
        queue = 'queue1'
        
        # Signal from ckanext-archiver that a resource has been archived
        IPipe.send_data('archived',
                        resource_id=resource_id,
                        queue=queue,
                        cache_filepath='CCC')

        assert send_task.called == False

    def test_create_zip_task(self):
        package_id = self.pkg['id']

        from ckanext.packagezip.tasks import create_zip
        # celery.send_task doesn't respect CELERY_ALWAYS_EAGER
        res = create_zip.apply_async(args=['CCC', package_id, 'queue1'])
        res.get()

        dest_dir = config.get('ckanext.packagezip.destination_dir')
        filename = "{0}.zip".format(package_id)
        filepath = os.path.join(dest_dir, filename)

        assert os.path.exists(filepath), filepath

        zipf = zipfile.ZipFile(filepath, 'r')

        assert zipf.getinfo('index.html').compress_type == zipfile.ZIP_DEFLATED
