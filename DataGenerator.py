import random
from datetime import datetime, timedelta

class DataGenerator:
    def __init__(self, start_date, end_date):
        self.current_time = start_date
        self.end_date = end_date
        self.current_season_range = self.get_seasonal_temp_range(self.current_time.month)

    @staticmethod
    def get_seasonal_temp_range(month):
        """根據月份返回季節性的溫度範圍"""
        if month in [12, 1, 2]:  # 冬季
            return 5, 10
        elif month in [3, 4, 5]:  # 春季
            return 10, 20
        elif month in [6, 7, 8]:  # 夏季
            return 20, 35
        elif month in [9, 10, 11]:  # 秋季
            return 10, 25

    @staticmethod
    def smooth_transition(prev_range, next_range, factor):
        """線性插值來平滑過渡溫度範圍"""
        min_temp = prev_range[0] * (1 - factor) + next_range[0] * factor
        max_temp = prev_range[1] * (1 - factor) + next_range[1] * factor
        return min_temp, max_temp

    def __iter__(self):
        """使類可以作為可迭代對象"""
        return self

    def __next__(self):
        """生成下一個數據點"""
        if self.current_time > self.end_date:
            raise StopIteration

        month = self.current_time.month

        # 檢查是否處於季節過渡期（每個月的最後一週或下個月的第一週）
        if self.current_time.day >= 21 and month in [2, 5, 8, 11]:
            next_season_range = self.get_seasonal_temp_range((month % 12) + 1)
            transition_factor = (self.current_time.day - 21) / 10  # 假設過渡期為最後10天
            temp_range = self.smooth_transition(self.current_season_range, next_season_range, transition_factor)
        else:
            temp_range = self.current_season_range

        # 生成當前分鐘的最大和最小溫度，1分鐘之間合理的溫度變化應為0.1-0.3左右
        temp_max = round(random.uniform(temp_range[0], temp_range[1]), 1)
        temp_min = round(temp_max - random.uniform(0.1, 0.3), 1)

        # 更新時間，每次增加1分鐘
        data = (self.current_time, temp_max, temp_min)

        self.current_time += timedelta(minutes=1)

        # 動態更新季節性範圍，若上面的更新時間落入季節轉換，則需變更current_season_range
        if self.current_time.month != month:
            self.current_season_range = self.get_seasonal_temp_range(self.current_time.month)

        return data