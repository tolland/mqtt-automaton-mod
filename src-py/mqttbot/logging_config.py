import json
import sys
from pathlib import Path

from loguru import logger

"""Logging configuration using Loguru

Provides structured logging with:
- Console output (INFO and above) with colors
- File output (DEBUG and above) with rotation
- Per-package log level control
- MQTT traffic isolation to separate file
"""


def mqtt_only(record):
    return "mqtt" in record["extra"]


def configure_logging(
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    log_dir: str = "logs",
    mqtt_file_enabled: bool = True,
    package_levels: dict[str, str] | None = None,
) -> None:
    """Configure Loguru logging with console and file handlers

    Args:
        console_level: Minimum level for console output (INFO, DEBUG, etc.)
        file_level: Minimum level for file output
        log_dir: Directory for log files
        mqtt_file_enabled: Whether to send MQTT traffic to separate file
        package_levels: Per-package log levels, e.g. {"mqttbot.mqtt": "DEBUG"}
    """
    # Remove default handler
    logger.remove()

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Console handler - INFO and above with colors
    logger.add(
        sys.stderr,
        level=console_level,
        format=(
            "<green>{time:HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # Main log file - DEBUG and above with rotation
    logger.add(
        log_path / "mqttbot_{time:YYYY-MM-DD}.log",
        level=file_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
    )

    # Separate MQTT traffic file (verbose, for debugging protocol)
    if mqtt_file_enabled:
        logger.add(
            log_path / "mqtt_{time:YYYY-MM-DD}.log",
            level="DEBUG",
            filter=lambda record: "mqtt" in record["name"].lower(),
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="3 days",
            compression="zip",
        )

        # Sink callable that pretty-prints on-wire JSON strings only.
        # It intentionally raises for non-JSON inputs (including Python dict/list values),
        # as requested: callers must pass the on-wire JSON string.
        def _mqtt_json_sink(message):
            # message is a loguru.Message (subclass of str); structured record is at message.record
            record = getattr(message, "record", None)
            if record is None:
                raise TypeError("Invalid Loguru Message: missing record")
            raw = record.get("message")
            # Always treat the log message as JSON text. Use str(raw) so bytes etc convert.
            obj = json.loads(str(raw))  # will raise JSONDecodeError on invalid input
            pretty = json.dumps(obj, indent=2, ensure_ascii=False)
            path = log_path / "mqtt_dump.log"
            # Append pretty JSON and a newline. Open per-call for simplicity and thread-safety.
            with path.open("a", encoding="utf-8") as f:
                f.write(pretty)
                f.write("\n")

        logger.add(
            _mqtt_json_sink,
            level="TRACE",
            filter=mqtt_only,
            enqueue=True,
        )

        # Per-package log levels (if specified)
        if package_levels:
            for package, level in package_levels.items():
                logger.add(
                    sys.stderr,
                    level=level,
                    filter=lambda record, pkg=package: record["name"].startswith(pkg),
                    format=(
                        "<green>{time:HH:mm:ss.SSS}</green> | "
                        "<level>{level: <8}</level> | "
                        "<cyan>{name}</cyan> - "
                        "<level>{message}</level>"
                    ),
                    colorize=True,
                )

        logger.info(f"Logging configured: console={console_level}, file={file_level}, dir={log_dir}")


def get_logger(name: str):
    """Get a logger for the specified module

    This is a convenience wrapper that returns the loguru logger
    with the module name bound to it.

    Args:
        name: Usually __name__ from the calling module

    Returns:
        Configured loguru logger instance
    """
    return logger.bind(name=name)
