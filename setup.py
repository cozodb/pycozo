from setuptools import setup

setup(
    name='pycozo',
    version='0.1.4',
    packages=['pycozo'],
    url='',
    license='MIT',
    author='Ziyang Hu',
    author_email='hu.ziyang@cantab.net',
    description='Python client for the Cozo database',
    install_requires=[],
    extras_require={
        'pandas': ['pandas', 'ipython'],
        'embedded': ['cozo-embedded==0.1.3'],
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
