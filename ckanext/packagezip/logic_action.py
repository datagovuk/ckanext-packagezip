import ckan.plugins as p
import ckan.logic as logic
from ckanext.archiver.model import Archival
from ckan.logic.auth import get_package_object
from ckanext.packagezip.util import (FilenameDeduplicator,
                                     datapackage_format,
                                     resource_has_data,)
from ckanext.packagezip.model import PackageZip

LICENSE_LOOKUP = {
    'uk-ogl': 'OGL-UK-3.0',
    'cc-zero': 'CC0-1.0',
}

@p.toolkit.side_effect_free
def datapackage_show(context, data_dict):
    """
    Generate the data required for a datapackage for the specified package.
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
            # We have archived it, and we have a path.
            _, resource_id, filename = archival.cache_filepath.rsplit('/', 2)
            cache_filepath = archival.cache_filepath
        else:
            # Try and work out the filename from the URL.
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
        resource_json['has_data'], resource_json['detected_format'] = \
            resource_has_data(res)

        # If we have archived the data, but the link was broken
        # then record the reason.
        if archival and archival.is_broken:
            resource_json['reason'] = archival.reason

        format = datapackage_format(res['format'])
        if format:
            resource_json['format'] = format

        datapackage['resources'].append(resource_json)

    return datapackage
