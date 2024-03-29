import csv
import datetime
import glob
import itertools
import logging
import logging.config
import os
import re
import time

import serial

logger = logging.getLogger(__name__)

ser = serial.Serial(
    port=None,
    baudrate=9600,
    timeout=2,
    xonxoff=True,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=1,
)

ser.port = "/dev/ttyUSB0"

col_names = [
    "Datetime_UTC",
    "UV_301nm",
    "UV_312nm",
    "UV_320nm",
    "UV_340nm",
    "UV_380nm",
    "PAR",
    "temp_int_C",
]

DATA_DIR = "data"


def send_cmd(cmd):
    ser.write(f"{cmd}\r".encode())
    time.sleep(0.5)
    logger.debug(f"Sent '{cmd}' command")


def send_esc_cmd():
    ser.write(chr(27).encode())
    logger.debug("Sent <Esc> command")


def refresh_output():
    while True:
        raw = ser.read().decode()
        print(raw, sep="", end="", flush=True)


def show_output():
    try:
        refresh_output()
    except KeyboardInterrupt:
        logger.info("\nReceived Keyboard Interrupt")
        send_esc_cmd()


def readline_until(word):
    while True:
        line = ser.readline().decode()
        if word in line:
            logger.debug(f"Found {word}")
            break


def auth():
    readline_until("PASSWORD")
    send_cmd("")
    ser.read_until(expected="\n").decode()


def set_time():
    send_cmd("TIME")
    readline_until("Y")
    send_cmd("N")
    utc_now = datetime.datetime.utcnow()
    date_utc = utc_now.strftime("%Y%m%d")
    time_utc = utc_now.strftime("%H%M%S")
    send_cmd(date_utc)
    send_cmd(time_utc)
    send_cmd("Y")
    logger.debug(f"Set time to {utc_now} UTC")


def get_data_lines():
    data_lines = []
    while True:
        line = ser.readline().decode().split()
        if not line:
            return data_lines
        data_lines.append(line)


def convert(data):
    records = []
    for data_line in data:
        datetime_str = data_line[0] + data_line[1]
        date_time = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M")
        col_values = [float(val) for val in data_line[2:]]
        col_values.insert(0, date_time)
        record = {key: value for key, value in zip(col_names, col_values)}
        records.append(record)
    logger.debug(f"Converted {len(records)} records")
    return records


def get_date_range():
    send_cmd("L1M")
    date_range_lines = ser.read_until(expected="\n").decode()
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    stripped = ansi_escape.sub("", date_range_lines)
    from_date_str = stripped.split(":")[2][:12]
    to_date_str = stripped.split(":")[4][:12]
    from_date = datetime.datetime.strptime(from_date_str, "%Y%m%d%H%M")
    to_date = datetime.datetime.strptime(to_date_str, "%Y%m%d%H%M")
    logger.debug(f"Available data from: {from_date} to {to_date}")
    return from_date, to_date


def get_data_from_to(start, end):
    logger.debug(f"Reading data from {start} to {end}")
    start_date = start.strftime("%Y%m%d")
    start_time = start.strftime("%H%M")
    end_date = end.strftime("%Y%m%d")
    end_time = end.strftime("%H%M")
    send_cmd(start_date)
    send_cmd(start_time)
    send_cmd(end_date)
    send_cmd(end_time)
    send_cmd("N")
    readline_until("SITE")
    data = get_data_lines()
    logger.info(f"Retrieved {len(data)} records")
    return data


def group_by_date(records):
    dates = []
    date_func = lambda x: x["Datetime_UTC"].date()
    for key, group in itertools.groupby(records, date_func):
        dates.append([g for g in group])
    return dates


def dicts_to_csv(dict_list, fname, header=False):
    keys = dict_list[0].keys()
    with open(fname, "a", newline="") as f:
        dict_writer = csv.DictWriter(f, keys)
        if header:
            dict_writer.writeheader()
        dict_writer.writerows(dict_list)
    logger.debug(f"Wrote {len(dict_list)} lines in {fname}")


def save_as_daily_files(records, prefix=None):
    dates = group_by_date(records)
    for d in dates:
        fname = f'{prefix}{d[0].get("Datetime_UTC").strftime("%Y%m%d")}.csv'
        fpath = os.path.join(DATA_DIR, fname)
        if not os.path.exists(fpath):
            dicts_to_csv(d, fpath, header=True)
        else:
            dicts_to_csv(d, fpath)


def remove_last_line(fname):
    with open(fname, "r") as rf:
        lines = rf.readlines()
    with open(fname, "w") as wf:
        wf.writelines(lines[:-2])
    logger.warning(f"Removed last line from {fname}")


def get_last_readout_from_file(fname):
    with open(fname, "r") as f:
        last_line = f.readlines()[-1]
    last_record = last_line.split(",")[0]
    logger.debug(f"Last record: {last_record}")
    return datetime.datetime.strptime(last_record, "%Y-%m-%d %H:%M:%S")


def get_last_readout():
    local_files = sorted(glob.glob(f"{DATA_DIR}/*.csv"))
    if len(local_files) > 0:
        last_file = local_files[-1]
        try:
            return get_last_readout_from_file(last_file)
        except ValueError as e:
            logger.error(f"ValueError: {e}")
            logger.warning(f"removing last line from {last_file}")
            remove_last_line(last_file)
            return get_last_readout_from_file(last_file)
    logger.warning("No .csv file found, will read all datalogger memory...")
    return datetime.datetime(1990, 1, 1, 0, 0, 1)


def get_records_since_last_readout():
    with ser:
        auth()
        set_time()
        from_date, to_date = get_date_range()
        last_readout = get_last_readout()
        if last_readout:
            data = get_data_from_to(
                last_readout + datetime.timedelta(minutes=1), to_date
            )
        else:
            data = get_data_from_to(from_date, to_date)
    records = convert(data)
    return records
