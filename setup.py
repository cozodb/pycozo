from setuptools import setup

setup(
    name='pycozo',
    version='0.1.0',
    packages=['pycozo'],
    url='',
    license='MIT',
    author='Ziyang Hu',
    author_email='hu.ziyang@cantab.net',
    description='Python client for the Cozo database',
    install_requires=[
        'requests',
    ],
    extras_require={
        'pandas': ['pandas']
    }
)
