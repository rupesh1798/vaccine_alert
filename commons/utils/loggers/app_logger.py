import logging

from .logger import get_logger

app_logger = get_logger(logger_name='app', log_level=logging.ERROR)
