import os
import logging
from ftplib import FTP, error_perm
from datalogger import DATA_DIR

logger = logging.getLogger(__name__)

FTP_IP = ""
FTP_USER = ""
FTP_PASSWORD = ""
FTP_DIR = "/datalogger/test"


def mkdir_if_not_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logger.debug(f"Created local directory {dir_path}")


def ftp_mkdir_and_enter(ftp_session, dir_name):
    if dir_name not in ftp_session.nlst():
        ftp_session.mkd(dir_name)
        logger.debug(f"Created FTP directory {dir_name}")
    ftp_session.cwd(dir_name)


def ftp_make_dirs(ftp_session, folder_path):
    for f in folder_path.split("/"):
        ftp_mkdir_and_enter(ftp_session, f)


def ftp_upload_file(ftp_session, local_path, remote_path):
    with open(local_path, "rb") as f:
        ftp_session.storbinary(f"STOR {remote_path}", f)
    logger.info(f"Uploaded {local_path} to {remote_path}")


def upload_to_ftp(local_files):
    with FTP(FTP_IP, FTP_USER, FTP_PASSWORD) as ftp:
        ftp.cwd(FTP_DIR)
        for local_file in local_files:
            base_name = os.path.basename(local_file)
            year = base_name[:4]
            remote_path = f"{year}/{base_name}"
            try:
                ftp_upload_file(ftp, local_file, remote_path)
            except error_perm as e:
                if "55" in str(e):
                    ftp_make_dirs(ftp, os.path.dirname(remote_path))
                    ftp.cwd(FTP_DIR)
                    ftp_upload_file(ftp, local_file, remote_path)


def archive_past_days(local_files):
    if len(local_files) > 1:
        for local_file in local_files[:-1]:
            base_name = os.path.basename(local_file)
            year = base_name[:4]
            dest_folder = f"{DATA_DIR}/archive/{year}"
            dest_path = f"{dest_folder}/{base_name}"
            mkdir_if_not_exists(dest_folder)
            os.rename(local_file, dest_path)
            logger.info(f"Renamed local file {local_file} to {dest_path}")
