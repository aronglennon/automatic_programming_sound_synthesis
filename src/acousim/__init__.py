

import os
import logging
import tempfile as tmp
import glob

eps = 2.0**(-16.0)

__version__ = '0.1'
__tempprefix = 'acousim-'

_kWAVE_EXT = 'wav'


# ---------------------------------
base_path = os.path.split(__file__)[0]
DEFAULT_PARAMS = os.path.join(base_path,"vsl_proj8D.pk")
# ---------------------------------


# Check for a pre-existing temp directory
tempdirs = glob.glob(os.path.join(tmp.gettempdir(),__tempprefix+'*'))
if len(tempdirs):
    _tempdir = tempdirs[0]
else:
    _tempdir = tmp.mkdtemp(prefix=__tempprefix)


def _sox_check():
    """
    Test for sox functionality
    """
    
    SOX = True
    if len(os.popen('sox -h').readlines())==0:
        logging.warning("""
        SoX could not be found!
        As a result, only wave files are supported.
        
        If you don't have SoX, proceed here:
         - - - http://sox.sourceforge.net/ - - -
         
        If you do (should) have SoX, double-check your
        path variables.""")
        SOX = False
    return SOX

_sox_check()