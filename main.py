import glob
import logging
import logging.config
import traceback
import os

from uploaders import upload_to_ftp
from datalogger import (
    get_data_since_last_readout,
    save_as_daily_files,
    archive_past_days,
    DATA_DIR,
)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.config.fileConfig("logging.conf", disable_existing_loggers=False)
logger = logging.getLogger(__name__)


def main():
    records = get_data_since_last_readout()
    save_as_daily_files(records)
    local_files = sorted(glob.glob(f"{DATA_DIR}/*.csv"))
    upload_to_ftp(local_files)
    archive_past_days(local_files, f"{DATA_DIR}/archive")
    logger.debug(f"{'-' * 15} SUCCESS {'-' * 15}")


if __name__ == "__main__":
    try:
        main()
    except:
        logger.error("uncaught exception: %s", traceback.format_exc())
