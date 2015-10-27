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

ACCEPTABLE_EXTENSIONS = ['csv', 'html', 'xls', 'xml', 'pdf',
                         'json', 'rdf', 'zip', 'ods', 'txt',
                         'aspx', 'doc', 'xsd', 'asp', 'ppt',
                         'kml', 'exe', 'xlsx']

MIME_TO_FORMAT_MAPPING = {
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
    # Most of the resource formats when lowercase are acceptable file extensions
    if resource_format.lower() in ACCEPTABLE_EXTENSIONS:
        return resource_format.lower()

    # Others have the mimetype stored as the format so we map to the
    # appropriate file extension
    if MIME_TO_FORMAT_MAPPING.get(resource_format.lower()):
        return MIME_TO_FORMAT_MAPPING.get(resource_format.lower())
