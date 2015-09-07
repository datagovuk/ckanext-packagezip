from ckan.lib.cli import CkanCommand

import logging
import uuid
import os

from pylons import config

from ckan.lib.celery_app import celery

class PackageZip(CkanCommand):
    """
    Usage:

        paster packagezip init
           - Creates the database table archiver needs to run
        paster packagezip create-zip <package name>
           - Creates the zipfile for a given package

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
            package_name = self.args[1]

            pkg = model.Package.get(package_name)

            ckan_ini_filepath = os.path.abspath(config['__file__'])
            task_id = str(uuid.uuid4())
            queue = 'priority'

            celery.send_task('packagezip.create_zip',
                             args=[ckan_ini_filepath, pkg.id, queue],
                             task_id=task_id, queue=queue)
        else:
            self.log.error('Command %s not recognized' % (cmd,))
