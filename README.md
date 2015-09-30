# ckanext-packagezip

This is an extension to CKAN that creates a zip file containing the cached resources of a CKAN package and makes it available to download.

# Install

Install this CKAN extension as normal:

    git clone git@github.com:datagovuk/ckanext-packagezip.git
    pip install -e ckanext-packagezip

Now edit your CKAN .ini and enable the plugin:

    vim $CKAN_INI
        ckan.plugins += packagezip

# Configuration

In the CKAN .ini you need to set the directory where the zips will be saved:

    ckanext.packagezip.destination_dir = /mnt/ckan/packagezips

(The directory will be created on the first archival)

# Software Licence

This software is developed by Cabinet Office. It is Crown Copyright and opened up under dual licences:

1. Open Government Licence (OGL) (which is compatible with Creative Commons Attibution License). OGL terms: http://www.nationalarchives.gov.uk/doc/open-government-licence/

2. GNU Affero General Public License (AGPL-3.0). Terms: http://opensource.org/licenses/AGPL-3.0
