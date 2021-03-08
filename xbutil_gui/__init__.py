# -*- coding: utf-8 -*-

from pathlib import Path
import sys

# Make sure it's running in Python 3.6 as it's required by tksheet.
if sys.version_info[0] < 2 or (sys.version_info[0] == 3 and sys.version_info[1] < 6):
    sys.exit('ERROR: This program require Python 3.6 or newer. You are running %s' %
             '.'.join(map(str, sys.version_info[0:3])))

VERSION = '0.0.7'
LABEL_WIDTH = 15
COMBO_WIDTH = 40
FIGURE_DPI = 100
DEFAULT_XBUTIL_REFRESH_INTERVAL = 5

# sheet column numbers
SHEET_TOTAL_ROWS = 200
SHEET_TOTAL_COLS = 8
SHEET_HOST_COL = 0
SHEET_DEVICE_COL = 1
SHEET_CU_COL = 2
SHEET_CU_STATUS_COL = 3
SHEET_CU_USAGE_COL = 4
SHEET_POWER_COL = 5
SHEET_TEMP_COL = 6
SHEET_LAST_UPDATED_COL = 7

CU_STATUS_DICT = {
    "0x1": "START",
    "0x4": "IDLE", 
    "0x8": "READY",
    "0x10": "RESTART"
}

__resource_path__ = Path(__file__).parent / 'resources'
__icon__ = __resource_path__ / 'xbutil-icon.gif'

STATUS_CODES = {
    'XRT_NOT_SETUP': {
        'code': 1,
        'message': 'ERROR: xbutil not found. Please set up XRT environment before running this application.'
    }
}
