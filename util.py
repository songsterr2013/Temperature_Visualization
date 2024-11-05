import json
import time
import csv
import os

def load_db_config(file_path):
    with open(file_path, 'r') as file:
        config = json.load(file)

    return config

def measure_execution_time(func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"執行耗時: {elapsed_time:.2f} 秒")
    return result

def save_data_to_csv(data_batch, filename):
    path = r"C:\ProgramData\MySQL\MySQL Server 8.0\Uploads"
    full_path = os.path.join(path, filename)
    with open(full_path, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'temp_high', 'temp_low'])  # 寫入表頭
        writer.writerows(data_batch)  # 寫入數據