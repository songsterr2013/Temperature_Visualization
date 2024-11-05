import sys
from datetime import datetime
from util import load_db_config
import mysql.connector
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton, QDateEdit, QComboBox, QTimeEdit
from PyQt5 import QtCore
import pyqtgraph as pg

class TemperaturePlotter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("2019-2022氣溫曲線繪製")

        # 設定主布局
        layout = QVBoxLayout()

        start_layout = QHBoxLayout() # 橫向布局，希望將日期和時間橫向排列
        self.start_date = QDateEdit() # 選擇日期的元件
        self.start_date.setCalendarPopup(True) # 跳出月曆
        self.start_date.setDate(QtCore.QDate.currentDate()) # 設定當前日期

        self.start_time = QTimeEdit()
        self.start_time.setTime(QtCore.QTime.currentTime())  # 設定當前時間

        start_layout.addWidget(QLabel("開始日期:"))
        start_layout.addWidget(self.start_date)
        start_layout.addWidget(QLabel("開始時間:"))
        start_layout.addWidget(self.start_time)

        layout.addLayout(start_layout)  # 將開始日期和時間布局添加到主布局

        end_layout = QHBoxLayout()
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QtCore.QDate.currentDate())

        self.end_time = QTimeEdit()
        self.end_time.setTime(QtCore.QTime.currentTime())

        end_layout.addWidget(QLabel("結束日期:"))
        end_layout.addWidget(self.end_date)
        end_layout.addWidget(QLabel("結束時間:"))
        end_layout.addWidget(self.end_time)

        layout.addLayout(end_layout)

        self.unit_selector = QComboBox()
        self.unit_selector.addItems(["分鐘", "小時", "日", "月", "年"])  # 增加年份選項
        layout.addWidget(QLabel("數據單位:"))  # 標籤
        layout.addWidget(self.unit_selector)  # 下拉選單

        # 添加繪圖按鈕
        self.plot_button = QPushButton("繪製氣溫")
        self.plot_button.clicked.connect(self.plot_temperature)
        layout.addWidget(self.plot_button)

        # 添加繪圖區域
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def plot_temperature(self):
        # 下面這3項，是把動態選擇後的選項傳進來
        start_date = self.start_date.date().toString("yyyy-MM-dd") + ' ' + self.start_time.time().toString("HH:mm") + ':00'
        end_date = self.end_date.date().toString("yyyy-MM-dd") + ' ' + self.end_time.time().toString("HH:mm") + ':00'
        unit = self.unit_selector.currentText()

        # 從資料庫獲取數據
        timestamps, high_temps, low_temps = self.fetch_temperature_data(start_date, end_date, unit)

        self.plot_widget.clear()

        # 設置 Y 軸範圍，確保資料放大和縮小時依然能呈現應有的溫度區間
        if high_temps and low_temps:  # 確保數據不為空
            min_temp = min(min(low_temps), min(high_temps))
            max_temp = max(max(low_temps), max(high_temps))
            self.plot_widget.setYRange(min_temp - 3, max_temp + 3)  # 增加一些緩衝區

        # 把資料打在畫布上
        self.plot_widget.plot(timestamps, high_temps, pen='r', label='最高氣溫')
        self.plot_widget.plot(timestamps, low_temps, pen='y', label='最低氣溫')

        self.plot_widget.setTitle(f"氣溫從 {start_date} 到 {end_date}")
        self.plot_widget.getAxis('left').setLabel('溫度 (°C)')
        self.plot_widget.getAxis('bottom').setLabel('日期時間')

        # 隨資料時間區間動態調整刻度的顯示
        self._x_axis_show_decision(timestamps, unit)
        self.plot_widget.addLegend()

    def fetch_temperature_data(self, start_date, end_date, unit):

        db_config = load_db_config('db_config.json')
        host = db_config['host']
        user = db_config['user']
        password = db_config['password']
        database = db_config['database']

        connection = mysql.connector.connect(
            host=host,  # 替換為你的主機
            user=user,  # 替換為你的用戶名
            password=password,  # 替換為你的密碼
            database=database  # 替換為你的數據庫名稱
        )
        cursor = connection.cursor()

        # 基於溫度變化的資料可觀察性去優化搜尋條件，善用SQL語法中的GROUP BY和AVG，減少資料量傳輸
        # 我們應隨著資料的時間間隔變長，去改變資料搜尋的方法，對1年來說，1分鐘的資料之間比較意義不大
        # 想觀察的應該是每月的溫度變化，因此我們可進行優化，取月平均溫度即可，點的減少即減少繪圖負擔
        query = self._query_decision(unit)
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()

        timestamps, high_temps, low_temps = [], [], []
        for row in results:
            str_to_datetime = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            timestamps.append(str_to_datetime.timestamp())  # 日期時間
            high_temp = float(row[1]) if row[1] is not None else float('nan')
            low_temp = float(row[2]) if row[2] is not None else float('nan')
            high_temps.append(high_temp)
            low_temps.append(low_temp)

        cursor.close()
        connection.close()
        return timestamps, high_temps, low_temps

    # 決定X軸顯示的刻度形式
    def _x_axis_show_decision(self, timestamps, unit):
        temp_format = '%Y-%m-%d %H:%M'

        if unit =='日':
            temp_format = '%Y-%m-%d'
        elif unit =='月':
            temp_format = '%Y-%m'
        elif unit =='年':
            temp_format = '%Y'

        ticks = []
        for ts in timestamps:
            dt = datetime.fromtimestamp(ts)  # 將時間戳轉換為 datetime 物件
            ticks.append((ts, dt.strftime(temp_format)))  # 格式化字符串
        self.plot_widget.getAxis('bottom').setTicks([ticks])  # 設置刻度標籤

    # 決定QUERY的SYNTAX
    def _query_decision(self, unit):
        if unit == "分鐘":
            query = """
                SELECT DATE_FORMAT(timestamp, '%Y-%m-%d %H:%i:00') AS minute, 
                       temp_high, 
                       temp_low 
                FROM temperature_records 
                WHERE timestamp BETWEEN %s AND %s 
                ORDER BY timestamp;
            """

        if unit == "小時":
            query = """
                SELECT DATE_FORMAT(timestamp, '%Y-%m-%d %H:00:00') AS hour, 
                       AVG(temp_high) AS avg_high, 
                       AVG(temp_low) AS avg_low 
                FROM temperature_records 
                WHERE timestamp BETWEEN %s AND %s 
                GROUP BY hour;
                """
        elif unit == "日":
            query = """
                SELECT DATE_FORMAT(timestamp, '%Y-%m-%d 00:00:00') AS date, 
                       AVG(temp_high) AS avg_high, 
                       AVG(temp_low) AS avg_low 
                FROM temperature_records 
                WHERE timestamp BETWEEN %s AND %s 
                GROUP BY date;
                """
        elif unit == "月":
            query = """
                SELECT DATE_FORMAT(timestamp, '%Y-%m-01 00:00:00') AS month, 
                       AVG(temp_high) AS avg_high, 
                       AVG(temp_low) AS avg_low 
                FROM temperature_records 
                WHERE timestamp BETWEEN %s AND %s 
                GROUP BY month;
                """
        elif unit == "年":
            query = """ 
                    SELECT DATE_FORMAT(timestamp, '%Y-01-01 00:00:00') AS year,
                           AVG(temp_high) AS avg_high, 
                           AVG(temp_low) AS avg_low 
                    FROM temperature_records 
                    WHERE timestamp BETWEEN %s AND %s 
                    GROUP BY year; 
                """
        return query

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TemperaturePlotter()
    window.show()
    sys.exit(app.exec_())