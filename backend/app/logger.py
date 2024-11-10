import logging
import json
import traceback


LOGGER_NAME = 'app'

def json_formatter(record: logging.LogRecord):
    log_record = {
        "log": record.getMessage(),
        "level": record.levelname,
        "timestamp": record.asctime,
        "logger": record.name,
        "log_type": "app",
        "exception": ""
    }

    if record.exc_info:
        log_record["exception"] = ''.join(traceback.format_exception(*record.exc_info))
    return json.dumps(log_record)


class JsonFormatter(logging.Formatter):
    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        return json_formatter(record)


def init_logger():
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)

    # 기존 핸들러가 있다면 제거하여 중복 방지
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = logging.StreamHandler()
    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)

