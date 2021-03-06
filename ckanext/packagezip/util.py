from itertools  import count

class FilenameDeduplicator(object):
    def __init__(self):
        self.reset()

    def  reset(self):
        self.seen = []

    def deduplicate(self, filename):
        if filename in self.seen:
            parts = filename.rsplit('.', 1)
            for i in count(1):
                if len(parts) == 2:
                    filename = u"{0}{1}.{2}".format(parts[0], i, parts[1])
                else:
                    filename = u"{0}{1}".format(parts[0], i)

                if filename not in self.seen:
                    break

        self.seen.append(filename)
        return filename

CKAN_FORMAT_TO_DATA_PACKAGE_FORMAT = {
    'csv': 'csv',
    'html': 'html',
    'xls': 'xls',
    'xml': 'xml',
    'pdf': 'pdf',
    'json': 'json',
    'rdf': 'rdf',
    'zip': 'zip',
    'ods': 'ods',
    'txt': 'txt',
    'aspx': 'aspx',
    'doc': 'doc',
    'xsd': 'xsd',
    'asp': 'asp',
    'ppt': 'ppt',
    'kml': 'kml',
    'exe': 'exe',
    'xlsx': 'xlsx',
    'application/pdf; charset=binary': 'pdf',
    'application/vnd.ms-excel; charset=binary': 'xls',
    'application/zip; charset=binary': 'zip',
    'txt/plain': 'txt',
}

def datapackage_format(resource_format):
    '''
    Convert from the format stored in resource.format into the format required by
    the datapackage spec:

    "Would be expected to be the the standard file extension for this type of resource"
    '''
    return CKAN_FORMAT_TO_DATA_PACKAGE_FORMAT.get(resource_format.lower())

def resource_has_data(resource):
    '''
    Checks the format, according to QA to ensure it is not in our list of
    formats that do not have data ("HTML", "API", "SPARQL", "WMS", "WFS",
    "API").  If it hasn't been through QA, fallback to the resource.

    Returns a boolean denoting whether it is not one of the formats we
    consider data-less, and the actual format as recorded by QA.
    '''
    from ckanext.qa.model import QA
    format = resource['format']
    qa = QA.get_for_resource(resource['id'])
    if qa:
        format = qa.format.upper() if qa.format else ''
    return format.upper() not in \
        ["HTML", "API", "SPARQL", "WMS", "WFS", "API"], format.upper()
