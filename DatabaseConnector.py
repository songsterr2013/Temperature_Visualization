import mysql.connector
from mysql.connector import Error

class DatabaseConnector:
    def __init__(self, host_name, user_name, user_password, db_name):
        self.connection = None
        try:
            self.connection = mysql.connector.connect(
                host=host_name,
                user=user_name,
                password=user_password,
                database=db_name
            )
            print("成功連接到資料庫")
        except Error as e:
            print(f"無法連接到資料庫: {e}")

    def insert_temperature_data(self, table_name, columns, data_batch):
        if self.connection is None:
            print("未連接到資料庫，無法插入數據")
            return

        try:
            with self.connection.cursor() as cursor:

                self.connection.autocommit = False
                cursor.execute("START TRANSACTION;")

                self._insert_data_batch(cursor, table_name, columns, data_batch)

                cursor.execute("COMMIT;")

                print(f"成功插入 {len(data_batch)} 條數據")
        except Error as e:
            print(f"插入數據時發生錯誤: {e}")
            self.connection.rollback()

    def _insert_data_batch(self, cursor, table_name, columns, values):
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        sql_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        cursor.executemany(sql_query, values)

    def load_data_from_csv(self, table, columns, filename):
        columns_str = ", ".join(columns)
        try:
            with self.connection.cursor() as cursor:
                self.connection.autocommit = False
                cursor.execute("START TRANSACTION;")

                sql_query = f"""
                            LOAD DATA INFILE '{filename}'
                            INTO TABLE {table}
                            FIELDS TERMINATED BY ',' 
                            ENCLOSED BY '"'
                            LINES TERMINATED BY '\n'
                            IGNORE 1 ROWS
                            ({columns_str});
                            """
                cursor.execute(sql_query)
                cursor.execute("COMMIT;")
                print("成功導入數據")
        except Error as e:
            print(f"導入數據時發生錯誤: {e}")
            self.connection.rollback()

    def close_connection(self):
        if self.connection:
            self.connection.close()
            print("資料庫連接已關閉")