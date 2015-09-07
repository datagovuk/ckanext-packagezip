import ckan.plugins as p
from ckanext.archiver.model import Archival
from ckan.logic.auth import get_package_object
from ckanext.packagezip.util import FilenameDeduplicator
from ckanext.packagezip.model import PackageZip

@p.toolkit.side_effect_free
def datapackage_show(context, data_dict):
    """
    """
    model = context['model']
    p.toolkit.check_access('package_show', context, data_dict)

    pkg = get_package_object(context, data_dict).as_dict()

    datapackage = {
        'id': pkg['id'],
        'name': pkg['name'],
        'title': pkg['title'],
        'resources': [],
    }

    try:
        package_zip = PackageZip.get_for_package(pkg['id'])
        datapackage['filepath'] = package_zip.filepath
    except Exception, ex:
        pass

    fd = FilenameDeduplicator()
    for res in pkg['resources']:
        archival = Archival.get_for_resource(res['id'])
        if archival and archival.cache_filepath:
            _, resource_id, filename = archival.cache_filepath.rsplit('/', 2)
            cache_filepath = archival.cache_filepath
        else:
            _, filename = res['url'].rsplit('/', 1)
            cache_filepath = ''
        filename = fd.deduplicate(filename)
        datapackage['resources'].append({'url': res['url'],
                                         'path': 'data/{0}'.format(filename),
                                         'cache_filepath': cache_filepath,
                                         'description': res['description']})

    return datapackage
