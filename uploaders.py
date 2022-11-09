import logging
from ftplib import FTP
import os

logger = logging.getLogger(__name__)
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)

FTP_IP = ""
FTP_USER = ""
FTP_PASSWORD = ""
FTP_DIR = "datalogger/test"


def upload_to_ftp(local_files):
    base_names = [os.path.basename(x) for x in local_files]
    logger.debug("Uploading to FTP server...")
    with FTP(FTP_IP, FTP_USER, FTP_PASSWORD) as ftp:
        ftp.cwd(FTP_DIR)
        for local_file, remote_file in zip(local_files, base_names):
            with open(local_file, "rb") as f:
                ftp.storbinary(f"STOR {remote_file}", f)
    logger.info(f"Uploaded {len(local_files)} files to FTP.")
