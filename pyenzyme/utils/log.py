# File: log.py
# Project: utils
# Author: Jan Range
# License: BSD-2 clause
# Copyright (c) 2022 Institute of Biochemistry and Technical Biochemistry Stuttgart

import logging
import sys

from io import StringIO


def setup_custom_logger(name, log_stream: StringIO, level=logging.DEBUG):

    formatter = logging.Formatter(fmt="%(levelname)s - %(message)s")

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)

    string_formatter = logging.Formatter(
        fmt="%(asctime)s - %(message)s", datefmt="%Y-%m-%d,%H:%M"
    )
    string_handler = logging.StreamHandler(log_stream)
    string_handler.setFormatter(string_formatter)
    string_handler.setLevel(logging.NOTSET)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    logger.addHandler(handler)
    logger.addHandler(string_handler)

    return logger


def log_change(
    logger: logging.Logger,
    class_name: str,
    id: str,
    name: str,
    old_value: str,
    new_value: str,
):
    """Logs change of an object"""
    logger.debug(
        f"{class_name} '{id}' - {name} was set from '{old_value}' to '{new_value}'"
    )


def log_new(
    logger: logging.Logger, class_name: str, id: str, name: str, new_value: str
):
    """Logs initialization of an object"""

    logger.debug(f"{class_name} '{id}' - '{name}' was set to '{new_value}'")


def log_object(
    logger: logging.Logger,
    obj,
):
    """Logs an object when it is added to the EnzymeML document"""

    # Handle objects without an ID
    try:
        id = obj.id
    except AttributeError:
        id = obj.get_id()

    for attr_name, value in obj.dict(exclude_none=True).items():
        if isinstance(value, dict) is False and isinstance(value, list) is False:
            log_new(logger, type(obj).__name__, id, attr_name, value)
