import logging
import json
from datetime import datetime, timezone, timedelta

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(IST).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }

        # Add request_id if present
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        return json.dumps(log_record)


def get_logger():
    logger = logging.getLogger("websec")
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler("logs/app.log")
    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)

    return logger