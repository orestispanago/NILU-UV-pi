import os
import glob
import pandas as pd
import matplotlib.pyplot as plt


col_names = [
    "Date", "time",
    "UV_301nm",
    "UV_312nm",
    "UV_320nm",
    "UV_340nm",
    "UV_380nm",
    "PAR",
    "temp_int_C",
]

def read_txt_files(txt_files):
    df_list = []
    for txt_file in txt_files:
        print(txt_file)
        df = pd.read_csv(txt_file, sep=' ', 
                         skiprows=3, skipfooter=3,  engine='python',
                         names=col_names,
                         on_bad_lines = 'warn',
                         converters={'Date':str,'time': str})
        df_list.append(df)
    df_all = pd.concat(df_list)
    return df_all

def mkdir_if_not_exists(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

txt_files = glob.glob("historical_data/*.txt")



df_all = read_txt_files(txt_files)
print(f"Rows before groupping: {len(df_all)}")
print(f"Days before groupping: {len(df_all)/60/24}")
df_all["Datetime"] = pd.to_datetime(df_all['Date'] + df_all['time'], format='%Y%m%d%H%M')
df_all.drop(['Date', 'time'], axis=1, inplace=True)
df_all.set_index('Datetime', inplace=True)
df_all = df_all.sort_index()

days_list = [group[1] for group in df_all.groupby(df_all.index.date)]
print(f"Days after groupping: {len(days_list)}")

for day in days_list:
    date_str = day.index[0].date().strftime('%Y%m%d')
    folder = f"converted_historical/{day.index[0].year}"
    mkdir_if_not_exists(folder)
    day.to_csv(f"{folder}/{date_str}.csv")
    
# df_all = df_all.resample('1min').mean()
# for col in list(df_all):
#     plt.figure(figsize=(18,4))
#     df_all[col].plot(style=',')
#     plt.title(col)
#     plt.show()
