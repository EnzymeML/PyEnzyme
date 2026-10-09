import sys

from loguru import logger


def add_logger(
    name: str,
    channel=sys.stderr,
) -> None:
    """Initialize the logger with the given name and module.

    Args:
        name (str): The name of the logger.
        channel (str, optional): The channel to log to. Defaults to sys.stderr.

    Returns:
        None

    Example:
        Will create a logger with the name "SBML" and log to the file "file.log":

            >> add_logger("SBML", "test", "file.log")

        Will create a logger with the name "SBML" and log to the standard error channel:

            >> add_logger("SBML", "test")

        Will create a logger with the name "SBML" and log to the standard output channel:

            >> import sys
            >> add_logger("SBML", "test", sys.stdout)

    """
    format = (
        f"  <cyan>{name}</cyan>\t{{module: >10}}\t<level>{{level}}</level>: {{message}}"
    )

    if isinstance(channel, str):
        format = f"{{time:YYYY-MM-DD HH:mm:ss}} {name} {{level}}: {{message}}"

    logger.remove()
    logger.add(
        channel,
        colorize=True,
        format=format,
    )
