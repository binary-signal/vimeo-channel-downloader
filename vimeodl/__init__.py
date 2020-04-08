#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys

__version__ = "0.2.0"

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler(sys.stdout)
log_handler.setFormatter(
    logging.Formatter(
        "%(asctime)-5s %(name)-12s %(funcName)20s() [%(levelname)-5.5s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
)
log.addHandler(log_handler)


__all__ = [
    "__version__",
    "log",
]
