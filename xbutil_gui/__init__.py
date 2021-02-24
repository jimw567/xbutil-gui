# -*- coding: utf-8 -*-

from pathlib import Path
import sys

# Make sure it's running in Python 3.6 as it's required by tksheet.
if sys.version_info[0] < 2 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
    sys.exit('ERROR: This program require Python 3.6 or newer. You are running %s' %
             '.'.join(map(str, sys.version_info[0:3])))

VERSION = '0.0.3'
LABEL_WIDTH = 15
COMBO_WIDTH = 50
FIGURE_DPI = 100
DEFAULT_XBUTIL_REFRESH_INTERVAL = 5

__resource_path__ = Path(__file__).parent / 'resources'
__icon__ = __resource_path__ / 'xbutil-icon.gif'

STATUS_CODES = {
    'XRT_NOT_SETUP': {
        'code': 1,
        'message': 'ERROR: xbutil not found. Please set up XRT environment before running this application.'
    }
}