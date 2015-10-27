import ckan.plugins as p
import ckan.logic as logic
from ckanext.archiver.model import Archival
from ckan.logic.auth import get_package_object
from ckanext.packagezip.util import FilenameDeduplicator, datapackage_format
from ckanext.packagezip.model import PackageZip

LICENSE_LOOKUP = {
    'uk-ogl': 'OGL-UK-3.0',
}

@p.toolkit.side_effect_free
def datapackage_show(context, data_dict):
    """
    """
    model = context['model']

    try:
        p.toolkit.check_access('package_show', context, data_dict)
        pkg = get_package_object(context, data_dict).as_dict()
    except logic.NotFound:
        p.toolkit.abort(404)

    datapackage = {
        'id': pkg['id'],
        'name': pkg['name'],
        'title': pkg['title'],
        'license': LICENSE_LOOKUP.get(pkg['license_id'], ''),
        'resources': [],
    }

    if pkg['notes']:
        datapackage['description'] = pkg['notes']

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
            try:
                _, filename = res['url'].rsplit('/', 1)
            except ValueError:
                filename = res['id']
            cache_filepath = ''
        filename = fd.deduplicate(filename)
        resource_json = {'url': res['url'],
                         'path': u'data/{0}'.format(filename),
                         'cache_filepath': cache_filepath,
                         'description': res['description']}

        format = datapackage_format(res['format'])
        if format:
            resource_json['format'] = format

        datapackage['resources'].append(resource_json)

    return datapackage
