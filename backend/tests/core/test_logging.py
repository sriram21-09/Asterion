import logging
from unittest import mock

from app.core.logging import log_execution_time, setup_logging


def test_setup_logging():
    test_logger = setup_logging()
    assert test_logger.name == "asterion"
    assert len(test_logger.handlers) > 0
    handler = test_logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.formatter is not None
    assert "%(asctime)s" in handler.formatter._fmt


def test_log_execution_time():
    mock_logger = mock.MagicMock()
    with log_execution_time("Test Block", logger_to_use=mock_logger):
        # Do some trivial work
        sum(i for i in range(100))

    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Test Block completed in" in log_message
    assert "s" in log_message
