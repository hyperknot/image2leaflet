#!/usr/bin/env python

from setuptools import setup

requirements = [
    'click',
    'jinja2',
]

setup(
    name='image2leaflet',
    version='0.1.1',
    description='A command line tool for converting big images to Leaflet maps',
    author='Zsolt Ero',
    author_email='zsolt.ero@gmail.com',
    url='https://github.com/hyperknot/image2leaflet',
    packages=['image2leaflet'],
    package_dir={'image2leaflet': 'image2leaflet'},
    include_package_data=True,
    install_requires=requirements,
    license='MIT',
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'image2leaflet = image2leaflet.cli:main',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ]
)
