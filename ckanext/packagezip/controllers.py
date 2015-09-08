import ckan.plugins.toolkit as t
from ckan import model
from ckan.lib.base import response

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

        response.headers['Content-type'] = 'application/zip'
        response.headers['Content-Disposition'] = str('attachment; filename=%s' % filename)

        with open(filepath) as zipfile:
            response.write(zipfile.read())
