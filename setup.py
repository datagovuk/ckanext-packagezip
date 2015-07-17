from setuptools import setup, find_packages
import sys, os

version = '0.1.3'

setup(
    name='ckanext-packagezip',
    version=version,
    description="Create a zip file of a package's resources",
    long_description='''
    ''',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Cabinet Office',
    author_email='',
    url='http://data.gov.uk',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.packagezip'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points='''
        [ckan.plugins]
        # Add plugins here, e.g.
        packagezip=ckanext.packagezip.plugin:PackageZipPlugin

        [ckan.celery_task]
        tasks=ckanext.packagezip.celery_import:task_imports
    ''',
)
