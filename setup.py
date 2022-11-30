#  Copyright 2022, The Cozo Project Authors.
#
#  This Source Code Form is subject to the terms of the Mozilla Public License, v. 2.0.
#  If a copy of the MPL was not distributed with this file,
#  You can obtain one at https://mozilla.org/MPL/2.0/.

from setuptools import setup

setup(
    name='pycozo',
    version='0.2.1',
    packages=['pycozo'],
    url='',
    license='MPL-2.0',
    author='Ziyang Hu',
    author_email='hu.ziyang@cantab.net',
    description='Python client for the Cozo database',
    install_requires=[],
    extras_require={
        'pandas': ['pandas', 'ipython'],
        'embedded': ['cozo-embedded==0.2.1'],
        'client': ['requests']
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Framework :: IPython",
        "Programming Language :: Python",
        "Topic :: Utilities",
    ],
)
