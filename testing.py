import psutil
import logging
from Logging_Config import configure_logging


def main():
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info(psutil.net_io_counters(pernic=False, nowrap=True))


if __name__ == "__main__":
    main()
