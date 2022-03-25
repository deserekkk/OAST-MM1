from logging import getLogger, INFO, Formatter, StreamHandler, FileHandler


def setup_logger(level=INFO):
    """Configures logger with preset format."""

    _logger = getLogger()
    _logger.setLevel(level)

    formatter = Formatter(
        '%(asctime)s %(processName)s %(threadName)s - %(levelname)s - %('
        'message)s '
    )

    console_handler = StreamHandler()
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    file_handler = FileHandler('simulation.log')
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    return _logger
