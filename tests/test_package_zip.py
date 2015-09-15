from ckan import model
from ckan.tests import BaseCase
from ckan.logic import get_action
from ckanext.archiver.interfaces import IPipe
from ckanext.archiver.tasks import update_resource
from ckanext.archiver import model as archiver_model
from ckanext.packagezip import model as packagezip_model

import mock
import os
import zipfile
import uuid
import json
import random

from nose.tools import assert_equals, assert_true, assert_false

from lxml.html import fromstring

from pylons import config

words = ['Ant', 'Bird', 'Cat', 'Dog', 'Elephant', 'Frog', 'Goat', 'Hippo']

class TestPackageZip(BaseCase):
    @classmethod
    def setup_class(cls):
        dest_dir = config.get('ckanext.packagezip.destination_dir')
        if not os.path.isdir(dest_dir):
            os.mkdir(dest_dir)

        cls.config = config['__file__']

        archiver_model.init_tables(model.meta.engine)
        packagezip_model.init_tables(model.meta.engine)

    def setup(self):
        resources = [
            {'url': 'http://data.gov.uk/robots.txt',
             'description': 'DGU Robots.txt',
             'format': 'TXT'},
            {'url': 'https://www.gov.uk/robots.txt',
             'description': 'Gov.UK Robots.txt',
             'format': 'TXT'},
            {'url': 'https://httpbin.org/status/404',
             'description': 'Missing Resource',
             'format': 'TXT'},
        ]
        self.pkg = self._test_package(resources)

    def _test_package(self, resources):
        context = {'model': model, 'ignore_auth': True, 'session': model.Session, 'user': 'test'}
        title = " ".join(random.sample(words, 3))
        name = title.lower().replace(' ', '-') + '-' + str(uuid.uuid4())
        notes = """
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Phasellus a velit lectus. Maecenas magna turpis, consequat et nibh a, porta tincidunt arcu. Pellentesque et venenatis ligula. Nam luctus luctus odio rutrum pulvinar. Cras vestibulum dolor eget elit cursus facilisis. Fusce eu nulla a justo euismod feugiat dictum a nisi. Donec porta, est nec euismod elementum, ligula odio fermentum orci, nec aliquam leo neque sed felis. Ut sed neque et neque gravida efficitur. Praesent efficitur tortor nunc, sed placerat ligula elementum nec. Nunc a augue et leo feugiat ornare in in urna. Nam ut sapien rutrum erat tincidunt suscipit. Pellentesque pulvinar diam eget nisl hendrerit, interdum posuere odio lobortis."""
        pkg = {'title': title,
               'name': name,
               'resources': resources,
               'notes': notes,
               'license_id': 'uk-ogl'}
        pkg = get_action('package_create')(context, pkg)

        for res in pkg['resources']:
            update_resource(self.config, res['id']) # This causes test to depend on internet

        return pkg

    def _create_zip_file(self, package_id):
        from ckanext.packagezip.tasks import create_zip
        # celery.send_task doesn't respect CELERY_ALWAYS_EAGER
        res = create_zip.apply_async(args=[self.config, package_id, 'queue1'])
        res.get()

        pz = packagezip_model.PackageZip.get_for_package(package_id)

        return pz.filepath

    @mock.patch('ckan.lib.celery_app.celery.send_task')
    def test_package_archive_event_causes_create_zip_task(self, send_task):
        package_id = 'abc123'
        queue = 'queue1'
        
        # Signal from ckanext-archiver that a package has been archived
        IPipe.send_data('package-archived',
                        package_id=package_id,
                        queue=queue,
                        cache_filepath=self.config)

        assert_true(send_task.called)

        args, kwargs = send_task.call_args
        assert_equals(args, ('packagezip.create_zip',))

        assert_equals(kwargs['args'][1], package_id)
        assert_equals(kwargs['args'][2], queue)

    @mock.patch('ckan.lib.celery_app.celery.send_task')
    def test_resource_archive_event_doesnt_causes_create_zip_task(self, send_task):
        resource_id = 'abc123'
        queue = 'queue1'
        
        # Signal from ckanext-archiver that a resource has been archived
        IPipe.send_data('archived',
                        resource_id=resource_id,
                        queue=queue,
                        cache_filepath=self.config)

        assert_false(send_task.called)

    def test_create_zip_task(self):
        package_id = self.pkg['id']

        filepath = self._create_zip_file(package_id)

        assert_true(os.path.exists(filepath))

        zipf = zipfile.ZipFile(filepath, 'r')

        assert_equals(zipf.getinfo('data/robots.txt').compress_type, zipfile.ZIP_DEFLATED)

    def test_zip_filename(self):
        package_id = self.pkg['id']
        package_name = self.pkg['name']

        filepath = self._create_zip_file(package_id)

        assert_equals('{0}.zip'.format(package_name), os.path.basename(filepath)) 

    def test_zip_directory(self):
        package_id = self.pkg['id']

        filepath = self._create_zip_file(package_id)

        assert_equals(config.get('ckanext.packagezip.destination_dir'),
                      os.path.dirname(filepath))

    def test_zip_index_file(self):
        package_id = self.pkg['id']

        filepath = self._create_zip_file(package_id)

        assert_true(os.path.exists(filepath))

        zipf = zipfile.ZipFile(filepath, 'r')

        assert_equals(zipf.getinfo('index.html').compress_type, zipfile.ZIP_DEFLATED)

        doc = fromstring(zipf.read('index.html'))

        assert_equals([self.pkg['title']], doc.xpath('//h1/text()'))
        assert_equals([self.pkg['notes']], doc.xpath('//p[@id=\'description\']/text()'))
        assert_equals(['License', 'OGL-UK-3.0'],
                      doc.xpath('//tr[@id=\'license\']/td/text()'))
        assert_equals(doc.xpath('//ul/li/a/@href'), ['data/robots.txt',
                                                     'data/robots1.txt'])
        assert_equals(doc.xpath('//ul/li/a/text()'), ['DGU Robots.txt',
                                                      'Gov.UK Robots.txt'])
        assert_equals(doc.xpath('//ul/li/span[@class=\'missing\']/text()'), ['Missing Resource'])

    def test_zip_datapackage_file(self):
        package_id = self.pkg['id']

        filepath = self._create_zip_file(package_id)

        assert_true(os.path.exists(filepath))

        zipf = zipfile.ZipFile(filepath, 'r')

        assert zipf.getinfo('datapackage.json').compress_type == zipfile.ZIP_DEFLATED
        datapackage = json.loads(zipf.read('datapackage.json'))

        assert_equals(datapackage['id'], self.pkg['id'])
        assert_equals(datapackage['name'], self.pkg['name'])
        assert_equals(datapackage['title'], self.pkg['title'])
        assert_equals(datapackage['description'], self.pkg['notes'])
        assert_equals(datapackage['license'], 'OGL-UK-3.0')

        assert_equals(len(datapackage['resources']), 3)

        assert_equals(datapackage['resources'][0]['path'], 'data/robots.txt')
        assert_equals(datapackage['resources'][0]['url'], 'http://data.gov.uk/robots.txt')

        assert_equals(datapackage['resources'][1]['path'], 'data/robots1.txt')
        assert_equals(datapackage['resources'][1]['url'], 'https://www.gov.uk/robots.txt')

        assert_equals(datapackage['resources'][2]['path'], 'data/404')
        assert_equals(datapackage['resources'][2]['url'], 'https://httpbin.org/status/404')
