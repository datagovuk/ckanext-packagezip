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

        headers = [('Content-type', 'application/zip'),
                   ('Content-Disposition', str('attachment; filename=%s' % filename))]

        file_app = FileApp(filepath, headers=headers)
        return file_app(request.environ, self.start_response)
