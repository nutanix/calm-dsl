import logging

from colorlog import ColoredFormatter
import time
import click

# Used for looking at verbose level
VERBOSE_LEVEL = 20


class CustomLogging:
    """
    customization on logging module.

    custom logger with following log levels with appropriate color codes and
    custom formatting for messages::“

        * LOG.response  - [RESPONSE]
        * LOG.payload   - [PAYLOAD]
        * LOG.status    - [STATUS]
        * log.url       - [URL]
        * LOG.info      - [INFO]
        * LOG.warn      - [WARNING]
        * LOG.error     - [ERROR]
        * LOG.
        critical  - [CRITICAL]

    """

    NOTSET = 0
    RESPONSE = 5
    PAYLOAD = 6
    DEBUG = 10
    STATUS = 15
    URL = 16
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    def __init__(self, name):
        """
        Build CustomLogger based on logging module

        Args:
            name(str): name of the module/logger

        Returns:
           None
        """

        # create custom levels
        self.__addCustomLevels()

        # create console and file handler
        self._ch = logging.StreamHandler()

        # add custom formatter to console handler
        self.__addCustomFormatter()

        # create custom logger
        self._logger = logging.getLogger(name)

        # add console to logger
        self._logger.addHandler(self._ch)

        # set level to log level
        self._logger.setLevel("INFO")

    def get_logger(self):
        self.set_logger_level(VERBOSE_LEVEL)
        return self._logger

    def get_logging_levels(self):
        return [
            "NOTSET",
            "RESPONSE",
            "PAYLOAD",
            "DEBUG",
            "STATUS",
            "URL",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        ]

    def set_logger_level(self, lvl):
        """sets the logger verbose level"""
        self._logger.setLevel(lvl)

    def response(self, msg):
        """
        custom response log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        return logger.response(msg)

    def payload(self, msg):
        """
        custom payload log level

        Args:
            msg (str): message to log

        Returns:
            None
        """
        logger = self.get_logger()
        return logger.payload(msg)

    def url(self, msg):
        """
        custom url log level

        Args:
            msg (str): message to log

        Returns:
            None
        """
        logger = self.get_logger()
        return logger.url(msg)

    def status(self, msg):
        """
        custom status log level

        Args:
            msg (str): message to log

        Returns:
            None
        """
        logger = self.get_logger()
        return logger.status(msg)

    def info(self, msg):
        """
        info log level

        Args:
            msg (str): message to log

        Returns:
            None
        """
        logger = self.get_logger()
        return logger.info(msg)

    def warning(self, msg):
        """
        warning log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        return logger.warning(msg)

    def error(self, msg):
        """
        error log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        return logger.error(msg)

    def exception(self, msg):
        """
        exception log level

        Args:
            msg (str): message to log

        Returns:
            None
        """

        logger = self.get_logger()
        return logger.exception(msg)

    def red(self, string):
        """
        log red colored string, useful for highlighting errors

        Args:
            string(str): string to be colored red

        Returns:
            None
        """

        return self.__color(string, "31m")

    def green(self, string):
        """
        log green colored string, useful for highlighting success

        Args:
            string(str): string to be colored green

        Returns:
            None
        """

        return self.__color(string, "32m")

    def yellow(self, string):
        """
        log yellow colored string, useful for highlighting data

        Args:
            string(str): string to be colored green

        Returns:
            None
        """

        return self.__color(string, "33m")

    def blue(self, string):
        """
        log blue colored string, useful for highlighting data

        Args:
            string(str): string to be colored green

        Returns:
            None
        """

        return self.__color(string, "34m")

    def __addCustomLevels(self):
        """
        add new custom level RESPONSE, PAYLOAD, STATUS, URL to logging

        Args:
            None

        Returns:
            None
        """

        RESPONSE = 5
        PAYLOAD = 6
        STATUS = 15
        URL = 16

        levels = [
            (RESPONSE, "RESPONSE"),
            (PAYLOAD, "PAYLOAD"),
            (STATUS, "STATUS"),
            (URL, "URL"),
        ]

        for level in levels:
            value, name = level
            logging.addLevelName(value, name)
            setattr(logging, name, value)

        def response(self, *args, **kwargs):
            """
            new response log level

            Args:
                *args: variable arguments
                **kwargs: variable keyword arguments

            Returns:
                None
            """

            self.log(RESPONSE, *args, **kwargs)

        def payload(self, *args, **kwargs):
            """
            new payload log level

            Args:
                *args: variable arguments
                **kwargs: variable keyword arguments

            Returns:
                None
            """

            self.log(PAYLOAD, *args, **kwargs)

        def url(self, *args, **kwargs):
            """
            new url log level

            Args:
                *args: variable arguments
                **kwargs: variable keyword arguments

            Returns:
                None
            """

            self.log(URL, *args, **kwargs)

        def status(self, *args, **kwargs):
            """
            new status log level

            Args:
                *args: variable arguments
                **kwargs: variable keyword arguments

            Returns:
                None
            """

            self.log(STATUS, *args, **kwargs)

        logging.Logger.response = response
        logging.Logger.payload = payload
        logging.Logger.url = url
        logging.Logger.status = status

    def __addCustomFormatter(self):
        """
        add ColorFormatter with custom colors for each log level

        Args:
            None

        Returns
            None
        """

        fmt = (
            "\n[%(asctime)s %(name)s "
            "[%(log_color)s%(levelname)s%(reset)s] %(message)s"
        )

        formatter = ColoredFormatter(
            fmt,
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "RESPONSE": "purple",
                "PAYLOAD": "yellow",
                "DEBUG": "purple",
                "URL": "blue",
                "STATUS": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
            },
        )
        formatter.converter = time.gmtime

        # add formatter to console handler
        self._ch.setFormatter(formatter)

    def __color(self, string, color):
        """
        set specified color string

        Args:
            string(str): string to be color colded
            color(str): color to be set

        Returns:
            ascii colored string
        """

        if not isinstance(string, str):
            string = str(string)
        COLOR = "\033[0;{}".format(color)
        NC = "\033[0m"
        return COLOR + string + NC


def get_logging_handle(name):
    """returns the CustomLogging object"""

    logging_handle = CustomLogging(name)
    return logging_handle


def simple_verbosity_option(logging_mod=None, *names, **kwargs):
    """A decorator that adds a `--verbosity, -v` option to the decorated
    command.
    Name can be configured through ``*names``. Keyword arguments are passed to
    the underlying ``click.option`` decorator.
    """

    if not names:
        names = ["--verbosity", "-v"]

    if not isinstance(logging_mod, CustomLogging):
        raise TypeError("Logging object should be instance of CustomLogging.")

    kwargs.setdefault("default", "INFO")
    kwargs.setdefault("metavar", "LVL")
    kwargs.setdefault("expose_value", False)
    kwargs.setdefault("type", click.Choice(logging_mod.get_logging_levels()))
    kwargs.setdefault("help", "Verboses the output")
    kwargs.setdefault("is_eager", True)

    def decorator(f):
        def _set_level(ctx, param, value):
            x = getattr(logging_mod, value.upper(), None)
            logging_mod.set_logger_level(x)
            global VERBOSE_LEVEL
            VERBOSE_LEVEL = x

        return click.option(*names, callback=_set_level, **kwargs)(f)

    return decorator
