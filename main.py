from datetime import datetime, timedelta
from DataGenerator import DataGenerator
from DatabaseConnector import DatabaseConnector
from util import load_db_config, measure_execution_time, save_data_to_csv

def main():
    db_config = load_db_config('db_config.json')
    host = db_config['host']
    user = db_config['user']
    password = db_config['password']
    database = db_config['database']
    db_connector = DatabaseConnector(host, user, password, database)

    start_date = datetime(2019, 1, 1, 0, 0)
    end_date = datetime(2022, 12, 31, 23, 59)
    temperature_generator = DataGenerator(start_date, end_date)

    batch_size = 1000000
    data_batch = []
    table = 'temperature_records'
    columns = ['timestamp', 'temp_high', 'temp_low']

    for data in temperature_generator:
        data_batch.append(data)

    save_data_to_csv(data_batch, 'temperature_data.csv')
    db_connector.load_data_from_csv(table,
                                    columns,
                                    'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/temperature_data.csv')


''' # 不透過CSV插入，使用這種方法插入200萬筆數據將耗時約1分鐘，用CSV的方式導入只需30秒左右，
    for data in temperature_generator:
        data_batch.append(data)

        if len(data_batch) >= batch_size:
            db_connector.insert_temperature_data(table, columns, data_batch)
            data_batch = []
    if data_batch:
        db_connector.insert_temperature_data(table, columns, data_batch)'''

if __name__ == "__main__":
    measure_execution_time(main)
