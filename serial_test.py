import serial
import time
import datetime


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
        print('\nReceived Keyboard Interrupt')
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

with ser:
    readline_until("PASSWORD")
    send_cmd("")
    ser.read_until(expected='\n').decode()

    send_cmd("L1M")
    send_cmd("20221016")
    send_cmd("0800")
    send_cmd("20221016")
    send_cmd("0802")
    send_cmd('N')

    readline_until("SITE")
    data = get_data_lines()    

data_line = data[0]
datetime_str = data_line[0]+data_line[1]
date_time = datetime.datetime.strptime(datetime_str, "%Y%m%d%H%M")

print(data)
