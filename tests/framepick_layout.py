"""Framepick test layout.

The suite runs unchanged against two layouts:

* combined repository (today): site served under ``/reel/``, files in ``reel/``
* standalone server (after the split): site served at ``/``, files at the root

Override with ``FRAMEPICK_BASE_PATH`` (``/reel/`` or ``/``) and
``FRAMEPICK_SITE_ROOT`` (directory holding ``index.html``).
"""
import os
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

_segment = os.environ.get('FRAMEPICK_BASE_PATH', '/reel/').strip('/')
BASE_PATH = f'/{_segment}/' if _segment else '/'
SITE_ROOT = Path(os.environ.get('FRAMEPICK_SITE_ROOT', ROOT / 'reel')).resolve()


def url(path=''):
    """Absolute site path for a page-relative query string such as ``?film=xianggu``."""
    return BASE_PATH + path.lstrip('/')


# Directory a plain static server must serve so that BASE_PATH resolves to SITE_ROOT.
SITE_SERVE_ROOT = ROOT if BASE_PATH != '/' else SITE_ROOT


def is_index(target):
    """Playwright route predicate matching the Framepick index in the current layout."""
    return urlparse(target).path in (BASE_PATH, BASE_PATH + 'index.html')


def site_file(url_path):
    """Local file for a site URL path such as ``/reel/framepick.js`` or ``/framepick.js``."""
    return SITE_SERVE_ROOT / urlparse(url_path).path.lstrip('/')
