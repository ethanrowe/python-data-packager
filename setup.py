from setuptools import setup
import os

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
    long_description="""
# Data Packager (python-data-packager) #

Provides simple tools to allow for the versioned packaging of arbitrary
assets.

For instance, suppose you have a given data set that your apps depend upon,
which change slowly, but have considerable impact on your appllication
behaviors.

You want to manage the data set on a versioned basis, such that somebody
can install a specific version of the data into their virtualenv.

This gives a simple way for organizing such packages and a simple interface
for accessing assets within them.

# License #

Copyright (c) 2012 Ethan Rowe <ethan at the-rowes dot com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
""",
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

