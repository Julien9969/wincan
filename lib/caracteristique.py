import logging
from typing import List

from pywinauto import WindowSpecification
from pywinauto.timings import TimeoutError as PyWinAutoTimeoutError


LOGGER = logging.getLogger(__name__)