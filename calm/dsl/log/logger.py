import logging
import inspect

from colorlog import ColoredFormatter
import time
import sys


class StdErrFilter(logging.Filter):
    """Filter for Stderr stream handler"""

    def filter(self, rec):
        return rec.levelno >= logging.DEBUG


class CustomLogging:
    """
    customization on logging module.

    custom logger with following log levels with appropriate color codes and
    custom formatting for messages::“

        * LOG.debug     - [DEBUG]
        * LOG.info      - [INFO]
        * LOG.warn      - [WARNING]
        * LOG.error     - [ERROR]
        * LOG.critical  - [CRITICAL]
        * LOG.exception - [ERROR]

    """

    _VERBOSE_LEVEL = 20
    _SHOW_TRACE = False

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    def __init__(self, name):
        """
        Build CustomLogger based on logging module

        Args:
            name(str): name of the module/logger

        Returns:
           None
        """

        self._ch1 = logging.StreamHandler()
        self._ch1.addFilter(StdErrFilter())

        # add custom formatter to console handler
        self.__addCustomFormatter(self._ch1)

        # create custom logger
        self._logger = logging.getLogger(name)

        # add console to logger
        self._logger.addHandler(self._ch1)

        # Add show trace option
        self.show_trace = False

    @staticmethod
    def __add_caller_info(msg):
        stack = inspect.stack()

        # filename = stack[2][1]
        # func = stack[2][3]
        ln = stack[2][2]

        return ":{}] {}".format(ln, msg)

    @classmethod
    def set_verbose_level(cls, lvl):
        cls._VERBOSE_LEVEL = lvl

    @classmethod
    def enable_show_trace(cls):
        cls._SHOW_TRACE = True

    def get_logger(self):
        self.set_logger_level(self._VERBOSE_LEVEL)
        self.show_trace = self._SHOW_TRACE
        return self._logger

    def get_logging_levels(self):
        return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def set_logger_level(self, lvl):
        """sets the logger verbose level"""
        self._logger.setLevel(lvl)

    def info(self, msg, nl=True, **kwargs):
        """
        info log level

        Args:
            msg (str): message to log
            nl (bool): Add newline (default: True)

        Returns:
            None
        """
        logger = self.get_logger()

        if not nl:
            for handler in logger.handlers:
                handler.terminator = " "

        logger.info(self.__add_caller_info(msg), **kwargs)

        if not nl:
            for handler in logger.handlers:
                handler.terminator = "\n"

    def warning(self, msg, *args, **kwargs):
        """
        warning log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        return logger.warning(self.__add_caller_info(msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """
        error log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        if self.show_trace:
            kwargs["stack_info"] = sys.exc_info()
        return logger.error(self.__add_caller_info(msg), *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """
        exception log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        if self.show_trace:
            kwargs["stack_info"] = sys.exc_info()
        return logger.exception(self.__add_caller_info(msg), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """
        critical log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        if self.show_trace:
            kwargs["stack_info"] = sys.exc_info()
        return logger.critical(self.__add_caller_info(msg), *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        """
        debug log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        return logger.debug(self.__add_caller_info(msg), *args, **kwargs)

    def __addCustomFormatter(self, ch):
        """
        add ColorFormatter with custom colors for each log level

        Args:
            None

        Returns
            None
        """

        fmt = (
            "[%(asctime)s] "
            "[%(log_color)s%(levelname)s%(reset)s] "
            "[%(name)s%(message)s"
        )

        formatter = ColoredFormatter(
            fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "purple",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
        )
        formatter.converter = time.gmtime

        # add formatter to console handler
        ch.setFormatter(formatter)


def get_logging_handle(name):
    """returns the CustomLogging object"""

    logging_handle = CustomLogging(name)
    return logging_handle
