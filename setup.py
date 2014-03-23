#! /usr/bin/env python
#
# Copyright (C) 2012-2014 Michael Waskom <mwaskom@stanford.edu>

DESCRIPTION = "Seaborn: statistical data visualization"
DISTNAME = 'seaborn'
MAINTAINER = 'Michael Waskom'
MAINTAINER_EMAIL = 'mwaskom@stanford.edu'
URL = 'http://stanford.edu/~mwaskom/software/seaborn/'
LICENSE = 'BSD (3-clause)'
DOWNLOAD_URL = 'https://github.com/mwaskom/seaborn/'
VERSION = '0.3'

from setuptools import setup

def check_dependencies():

    # Just make sure dependencies exist, I haven't rigorously
    # tested what the minimal versions that will work are
    # (help on that would be awesome)
    try:
        import numpy
    except ImportError:
        raise ImportError("seaborn requires numpy")
    try:
        import scipy
    except ImportError:
        raise ImportError("seaborn requires scipy")
    try:
        import matplotlib
    except ImportError:
        raise ImportError("seaborn requires matplotlib")
    try:
        import pandas
    except ImportError:
        raise ImportError("seaborn requires pandas")

if __name__ == "__main__":
    import os
    if os.path.exists('MANIFEST'):
        os.remove('MANIFEST')

    import sys
    if not (len(sys.argv) >= 2 and ('--help' in sys.argv[1:] or
            sys.argv[1] in ('--help-commands', 'egg_info', '--version',
                            'clean'))):
        check_dependencies()

    setup(name=DISTNAME,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license=LICENSE,
        url=URL,
        version=VERSION,
        download_url=DOWNLOAD_URL,
        packages=['seaborn', 'seaborn.external', 'seaborn.tests'],
        classifiers=[
                     'Intended Audience :: Science/Research',
                     'Programming Language :: Python :: 2.7',
                     'Programming Language :: Python :: 3.3',
                     'License :: OSI Approved :: BSD License',
                     'Topic :: Scientific/Engineering :: Visualization',
                     'Topic :: Multimedia :: Graphics',
                     'Operating System :: POSIX',
                     'Operating System :: Unix',
                     'Operating System :: MacOS'],
        install_requires=["pandas"],
          )
