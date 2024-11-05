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
        self.unit_selector.addItems(["小時", "日", "月", "年"])  # 增加年份選項
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

        # 繪製溫度數據
        self.plot_widget.clear()

        # 設置 X 軸範圍
        if timestamps:  # 確保 timestamps 不為空
            self.plot_widget.setXRange(timestamps[0], timestamps[-1])  # 設定 X 軸範圍
        # 設置 Y 軸範圍
        if high_temps and low_temps:  # 確保數據不為空
            min_temp = min(min(low_temps), min(high_temps))
            max_temp = max(max(low_temps), max(high_temps))
            self.plot_widget.setYRange(min_temp - 5, max_temp + 5)  # 增加一些緩衝區

        self.plot_widget.plot(timestamps, high_temps, pen='r', label='最高氣溫')
        self.plot_widget.plot(timestamps, low_temps, pen='y', label='最低氣溫')
        self.plot_widget.setTitle(f"氣溫從 {start_date} 到 {end_date}")
        self.plot_widget.getAxis('left').setLabel('溫度 (°C)')

        # 格式化 X 軸的日期時間標籤
        ticks = []
        for ts in timestamps:
            dt = datetime.fromtimestamp(ts)  # 將時間戳轉換為 datetime 物件
            ticks.append((ts, dt.strftime('%Y-%m-%d %H:%M')))  # 格式化字符串

        self.plot_widget.getAxis('bottom').setTicks([ticks])  # 設置刻度標籤
        self.plot_widget.getAxis('bottom').setLabel('日期時間')
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

        query = self._query_decision(unit)
        #query = "SELECT timestamp, temp_high, temp_low FROM temperature_records WHERE timestamp BETWEEN %s AND %s"
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

    def _query_decision(self, unit):
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