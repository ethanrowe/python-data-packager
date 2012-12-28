from setuptools import setup
import os

readme = open(os.path.join(os.path.dirname(__file__), 'README'), 'r').read()
license = open(os.path.join(os.path.dirname(__file__), 'LICENSE'), 'r').read()

setup(
    name = "data_packager",
    version = "0.0.1",
    author = "Ethan Rowe",
    author_email = "ethan@the-rowes.com",
    description = ("Provides dirt-simple tool for releasing datasets as packages"),
    license = "MIT",
    keywords = "",
    url = "https://github.com/ethanrowe/python-data-packager",
    packages=['data_packager',
              'data_packager.test',
    ],
    long_description="%s\n\n# License #\n\n%s" % (readme, license),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Topic :: Utilities",
    ],
    tests_require=[
        'virtualenv',
        'nose',
    ],
    test_suite='nose.collector',
)

