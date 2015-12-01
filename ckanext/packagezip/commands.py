from ckan.lib.cli import CkanCommand

import logging
import uuid
import os
import sys

from pylons import config


def name_stripped_of_url(url_or_name):
    '''Returns a name. If it is in a URL it strips that bit off.

    e.g. https://data.gov.uk/publisher/barnet-primary-care-trust
         -> barnet-primary-care-trust

         barnet-primary-care-trust
         -> barnet-primary-care-trust
    '''
    if url_or_name.startswith('http'):
        return url_or_name.split('/')[-1]
    return url_or_name


class PackageZip(CkanCommand):
    """
    Usage:

        paster packagezip init
           - Creates the database table archiver needs to run
        paster packagezip create-zip <package name/url> [<package name/url> ...]
           - Creates the package zip for given package(s)

    """
    summary = __doc__.split('\n')[0]
    usage = __doc__

    def command(self):
        """
        Parse command line arguments and call appropriate method.
        """
        if not self.args or self.args[0] in ['--help', '-h', 'help']:
            print self.usage
            sys.exit(1)

        cmd = self.args[0]
        self._load_config()

        self.log = logging.getLogger(__name__)

        if cmd == 'init':
            import ckan.model as model
            from ckanext.packagezip.model import init_tables
            init_tables(model.meta.engine)
            self.log.info('Package Zip tables are initialized')
        elif cmd == 'create-zip':
            import ckan.model as model
            from ckan.lib.celery_app import celery

            datasets = []
            for name in self.args[1:]:
                name_ = name_stripped_of_url(name)
                dataset = model.Package.get(name_)
                assert dataset, 'Could not find dataset: %s' % name
                datasets.append(dataset)
            assert datasets, 'No datasets to zip!'

            ckan_ini_filepath = os.path.abspath(config['__file__'])
            task_id = str(uuid.uuid4())
            queue = 'priority'

            for dataset in datasets:
                from ckanext.packagezip.tasks import create_zip
                create_zip(ckan_ini_filepath, dataset.id)
        else:
            self.log.error('Command %s not recognized' % (cmd,))
