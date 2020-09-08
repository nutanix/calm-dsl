import click

from calm.dsl.config import get_context
from calm.dsl.log import CustomLogging


def simple_verbosity_option(logging_mod=None, *names, **kwargs):
    """A decorator that adds a `--verbose, -v` option to the decorated
    command.
    Name can be configured through ``*names``. Keyword arguments are passed to
    the underlying ``click.option`` decorator.
    """

    if not names:
        names = ["--verbose", "-v"]

    if not isinstance(logging_mod, CustomLogging):
        raise TypeError("Logging object should be instance of CustomLogging.")

    log_level = "INFO"
    try:
        ContextObj = get_context()
        log_config = ContextObj.get_log_config()

        if "level" in log_config:
            log_level = log_config.get("level") or log_level

    except (FileNotFoundError, ValueError):
        # At the time of initializing dsl, config file may not be present or incorrect
        pass

    logging_levels = logging_mod.get_logging_levels()
    if log_level not in logging_levels:
        raise ValueError(
            "Invalid log level in config. Select from {}".format(logging_levels)
        )

    log_level = logging_levels.index(log_level) + 1
    kwargs.setdefault("default", log_level)
    kwargs.setdefault("expose_value", False)
    kwargs.setdefault("help", "Verboses the output")
    kwargs.setdefault("is_eager", True)
    kwargs.setdefault("count", True)

    def decorator(f):
        def _set_level(ctx, param, value):
            logging_levels = logging_mod.get_logging_levels()
            if value < 1 or value > len(logging_levels):
                raise click.BadParameter(
                    "Should be atleast 1 and atmost {}".format(len(logging_levels))
                )

            log_level = logging_levels[value - 1]
            x = getattr(logging_mod, log_level, None)
            CustomLogging.set_verbose_level(x)

        return click.option(*names, callback=_set_level, **kwargs)(f)

    return decorator


def show_trace_option(logging_mod=None, **kwargs):
    """A decorator that add --show_trace/-st option to decorated command"""

    if not isinstance(logging_mod, CustomLogging):
        raise TypeError("Logging object should be instance of CustomLogging.")

    names = ["--show_trace", "-st"]
    kwargs.setdefault("is_flag", True)
    kwargs.setdefault("default", False)
    kwargs.setdefault("expose_value", False)
    kwargs.setdefault("help", "Show the traceback for the exceptions")
    kwargs.setdefault("is_eager", True)

    def decorator(f):
        def _set_show_trace(ctx, param, value):
            if value:
                CustomLogging.enable_show_trace()

        return click.option(*names, callback=_set_show_trace, **kwargs)(f)

    return decorator
