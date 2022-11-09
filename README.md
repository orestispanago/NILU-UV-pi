# NILU-UV-pi

Read data from NILU-UV built-in datalogger and upload to FTP.

* Commands are sent to NILU-UV over serial connection.

* NILU time is set before data retrieval.

* Records since last readout (in last ```.csv``` data file) are retrieved from the datalogger. 

NOTE: If no ```csv``` data file is found, reads all memory. NILU can store approx 23 days of 1min data. Retrieval takes around 75 minutes.

* Records are grouped by date and saved as daily ```.csv``` files.

* The ```.csv``` files are uploaded to FTP servers.

* Older files are moved to ```data/archive``` folder. 

## Instructions

Edit the FTP parameters in ```uploaders.py```

To avoid overlapping cron job execution, use ```flock``` in crontab:

```
*/5 * * * * /usr/bin/flock -w 0 ~/flock_file.lock python3 ~/NILU-UV-pi/main.py
```

To check if your cron job is running:

```
grep CRON /var/log/syslog
```

To make sure that ```flock``` works:

```
flock -n -x ~/flock_file.lock true || echo "LOCKED"
```