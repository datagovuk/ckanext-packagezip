from ckan.lib.cli import CkanCommand

import logging

class PackageZip(CkanCommand):
    """
    Usage:

        paster packagezip init
           - Creates the database table archiver needs to run

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
        else:
            self.log.error('Command %s not recognized' % (cmd,))
