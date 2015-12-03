import ckan.plugins.toolkit as t
from ckan import model
from ckan.lib.base import response
from paste.fileapp import FileApp
from pylons import request

import json
import os

class PackageZipController(t.BaseController):
    def datapackage(self, name):
        context = {'model': model, 'session': model.Session}
        try:
            datapackage = t.get_action('datapackage_show')(context, {'id': name})
        except t.NotAuthorized:
            t.abort(401)

        # Strip fields that we don't want in the results
        for r in datapackage.get('resources', []):
            if 'has_data' in r:
                del r['has_data']
            if 'cache_filepath' in r:
                del r['cache_filepath']
            if 'detected_format' in r:
                r['format'] = r['detected_format']
                del r['detected_format']

        response.headers['Content-type'] = 'application/json'
        return json.dumps(datapackage, sort_keys=True, indent=4)

    def zipfile(self, name):
        context = {'model': model, 'session': model.Session}
        try:
            datapackage = t.get_action('datapackage_show')(context, {'id': name})
        except t.NotAuthorized:
            t.abort(401)

        filepath = datapackage.get('filepath')
        if not filepath or not os.path.exists(filepath):
            t.abort(404)

        filename = os.path.basename(filepath)

        headers = [('Content-Disposition', str('attachment; filename="%s"' % filename))]

        file_app = FileApp(filepath, headers=headers, content_type='application/octet-stream')
        return file_app(request.environ, self.start_response)
