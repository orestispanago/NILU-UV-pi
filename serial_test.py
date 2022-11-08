import csv
import datetime
import itertools
import os
import re
import time

import serial

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
    "Datetime",
    "UV_301nm",
    "UV_312nm",
    "UV_320nm",
    "UV_340nm",
    "UV_380nm",
    "PAR",
    "temp_int_C",
]


def send_cmd(cmd):
    ser.write(f"{cmd}\r".encode())
    time.sleep(0.5)
    print(f"Sent '{cmd}' command")


def send_esc_cmd():
    ser.write(chr(27).encode())
    print("Sent <Esc> command")


def refresh_output():
    while True:
        raw = ser.read().decode()
        print(raw, sep="", end="", flush=True)


def show_output():
    try:
        refresh_output()
    except KeyboardInterrupt:
        print("\nReceived Keyboard Interrupt")
        send_esc_cmd()


def readline_until(word):
    while True:
        line = ser.readline().decode()
        if word in line:
            print(f"Found {word}")
            break


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
    return records


def get_date_range():
    date_range_lines = ser.read_until(expected="\n").decode()
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    stripped = ansi_escape.sub("", date_range_lines)
    from_date_str = stripped.split(":")[2][:12]
    to_date_str = stripped.split(":")[4][:12]
    from_date = datetime.datetime.strptime(from_date_str, "%Y%m%d%H%M")
    to_date = datetime.datetime.strptime(to_date_str, "%Y%m%d%H%M")
    print(f"Available data from: {from_date} to {to_date}")
    return from_date, to_date


def readout(
    start=datetime.datetime(2022, 11, 8),
    end=datetime.datetime(2022, 11, 8, 0, 1),
):
    print(f"Reading data from {start} to {end}")
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
    return data


def group_by_date(records):
    dates = []
    date_func = lambda x: x["Datetime"].date()
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
    print(f"Wrote {len(dict_list)} lines in {fname}")


def save_as_daily_files(records):
    dates = group_by_date(records)
    for d in dates:
        fname = f'{d[0].get("Datetime").strftime("%Y%m%d")}.csv'
        fpath = os.path.join("data", fname)
        if not os.path.exists(fpath):
            dicts_to_csv(d, fpath, header=True)
        else:
            dicts_to_csv(d, fpath)


with ser:
    readline_until("PASSWORD")
    send_cmd("")
    ser.read_until(expected="\n").decode()
    send_cmd("L1M")
    from_date, to_date = get_date_range()
    data = readout()

records = convert(data)
save_as_daily_files(records)
print(records)
