# ckanext-packagezip

This is an extension to CKAN that creates a Data Package - a zip file containing:
* the data files of dataset
* metadata in Data Package JSON format
* metadata as an HTML page

The data files are taken from the local 'cached resources', saved by ckanext-archiver (datagovuk fork).

The Data Package JSON is also made available on an Action API: /dataset/{name}/datapackage.json

On data.gov.uk, the Data Package (zip) is shown on the dataset page - the template for this is in ckanext-dgu.

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

# Usage

The zipping takes place on a Celery queue, so you need to be running the Celery daemon (in another terminal for debug purposes) for the correct queue name:

    paster --plugin=ckan celeryd run concurrency=1 --queue=priority
    paster --plugin=ckan celeryd run concurrency=1 --queue=bulk

The creation of Data Package zips is triggered by the archival of a dataset (which is in turn triggered by an edit, and data.gov.uk also has set-up a weekly cron.) Dataset edits trigger the 'priority' queue and weekly cron trigger the 'bulk' queue.

A dataset's zip can also be queued (in the priority queue) using paster:

    paster --plugin=ckanext-packagezip packagezip create-zip <package name/url>

# Software Licence

This software is developed by Cabinet Office. It is Crown Copyright and opened up under dual licences:

1. Open Government Licence (OGL) (which is compatible with Creative Commons Attibution License). OGL terms: http://www.nationalarchives.gov.uk/doc/open-government-licence/

2. GNU Affero General Public License (AGPL-3.0). Terms: http://opensource.org/licenses/AGPL-3.0
