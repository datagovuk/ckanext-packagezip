import ckan.plugins.toolkit as t
from ckan import model
from ckan.lib.base import response

import json

class PackageZipController(t.BaseController):
    def datapackage(self, id):
        context = {'model': model, 'session': model.Session}
        try:
            datapackage = t.get_action('datapackage_show')(context, {'id': id})
        except t.NotAuthorized:
            t.abort(401)

        response.headers['Content-type'] = 'text/json'
        return json.dumps(datapackage, sort_keys=True, indent=4)
