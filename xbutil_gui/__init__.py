# -*- coding: utf-8 -*-

from pathlib import Path

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