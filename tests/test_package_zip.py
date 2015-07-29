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
import random

from lxml.html import fromstring

from pylons import config

words = ['Ant', 'Bird', 'Cat', 'Dog', 'Elephant', 'Frog', 'Goat', 'Hippo']

class TestPackageZip(BaseCase):
    @classmethod
    def setup_class(cls):
        dest_dir = config.get('ckanext.packagezip.destination_dir')
        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)

        cls.config = config.__file__

    def setup(self):
        self.pkg = self._test_package('http://data.gov.uk/robots.txt')

    def _test_package(self, url, format=None):
        context = {'model': model, 'ignore_auth': True, 'session': model.Session, 'user': 'test'}
        title = " ".join(random.sample(words, 3))
        name = title.lower().replace(' ', '-') + '-' + str(uuid.uuid4())
        pkg = {'title': title, 'name': name, 'resources': [
            {'url': url, 'format': format or 'TXT', 'description': 'Robots.txt'}
            ]}
        pkg = get_action('package_create')(context, pkg)

        for res in pkg['resources']:
            update(self.config, res['id']) # This causes test to depend on internet

        return pkg

    def _create_zip_file(self, package_id):
        from ckanext.packagezip.tasks import create_zip
        # celery.send_task doesn't respect CELERY_ALWAYS_EAGER
        res = create_zip.apply_async(args=['CCC', package_id, 'queue1'])
        res.get()

        dest_dir = config.get('ckanext.packagezip.destination_dir')
        filename = "{0}.zip".format(package_id)
        filepath = os.path.join(dest_dir, filename)

        return filepath

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

        filepath = self._create_zip_file(package_id)

        assert os.path.exists(filepath), filepath

        zipf = zipfile.ZipFile(filepath, 'r')

        assert zipf.getinfo('resources/robots.txt').compress_type == zipfile.ZIP_DEFLATED

    def test_zip_index_file(self):
        package_id = self.pkg['id']

        filepath = self._create_zip_file(package_id)

        assert os.path.exists(filepath), filepath

        zipf = zipfile.ZipFile(filepath, 'r')

        assert zipf.getinfo('index.html').compress_type == zipfile.ZIP_DEFLATED

        doc = fromstring(zipf.read('index.html'))

        assert [self.pkg['title']] == doc.xpath('//h1/text()')
        assert doc.xpath('//ul/li/a/@href') == ['resources/robots.txt']
        assert doc.xpath('//ul/li/a/text()') == ['Robots.txt']

    def test_zip_datapackage_file(self):
        package_id = self.pkg['id']

        filepath = self._create_zip_file(package_id)

        assert os.path.exists(filepath), filepath

        zipf = zipfile.ZipFile(filepath, 'r')

        assert zipf.getinfo('datapackage.json').compress_type == zipfile.ZIP_DEFLATED
        datapackage = json.loads(zipf.read('datapackage.json'))

        assert datapackage['name'] == self.pkg['name']
        assert datapackage['title'] == self.pkg['title']
        assert len(datapackage['resources']) == 1
        assert datapackage['resources'][0]['path'] == 'resources/robots.txt'
        assert datapackage['resources'][0]['url'] == 'http://data.gov.uk/robots.txt'
