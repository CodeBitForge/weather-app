import logging
logging.getLogger('qt_material').setLevel(logging.ERROR)
logging.getLogger().setLevel(logging.ERROR)

import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFrame, QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from qt_material import apply_stylesheet
import qtawesome as qta
from datetime import datetime, timezone, timedelta
from collections import Counter

# --- API Key ---
API_KEY = "YOUR_API_KEY_HERE"



CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

class WeatherThread(QThread):
    result = pyqtSignal(dict, dict)
    error = pyqtSignal(str)

    def __init__(self, city):
        super().__init__()
        self.city = city

    def run(self):
        try:
            params = {'q': self.city, 'appid': API_KEY, 'units': 'metric', 'lang': 'fa'}
            current_resp = requests.get(CURRENT_URL, params=params, timeout=10)
            forecast_resp = requests.get(FORECAST_URL, params=params, timeout=10)

            if current_resp.status_code != 200:
                self.error.emit("شهر یافت نشد!")
                return

            current_data = current_resp.json()
            forecast_data = forecast_resp.json()
            self.result.emit(current_data, forecast_data)
        except requests.exceptions.ConnectionError:
            self.error.emit("عدم اتصال به اینترنت!")
        except requests.exceptions.Timeout:
            self.error.emit("درخواست زمان‌بر بود!")
        except Exception as e:
            self.error.emit(f"خطا: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("اپلیکیشن وضعیت آب و هوا")
        self.setWindowIcon(qta.icon('fa5s.cloud-sun'))
        self.resize(900, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        header = QLabel("وضعیت آب و هوا")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        input_layout = QHBoxLayout()
        self.city_input = QLineEdit()
        self.city_input.setPlaceholderText("نام شهر را وارد کنید (مثل تهران)")
        self.city_input.setFont(QFont("Arial", 14))
        search_btn = QPushButton("جستجو")
        search_btn.setIcon(qta.icon('fa5s.search'))
        search_btn.clicked.connect(self.search_weather)
        self.city_input.returnPressed.connect(self.search_weather)

        input_layout.addWidget(self.city_input)
        input_layout.addWidget(search_btn)
        layout.addLayout(input_layout)

        self.current_frame = QFrame()
        self.current_frame.setFrameShape(QFrame.StyledPanel)
        current_layout = QGridLayout(self.current_frame)

        self.city_label = QLabel("شهر: -")
        self.temp_label = QLabel("دما: -")
        self.feels_label = QLabel("احساس می‌شود: -")
        self.desc_label = QLabel("وضعیت: -")
        self.humidity_label = QLabel("رطوبت: -")
        self.wind_label = QLabel("باد: -")
        self.sunrise_label = QLabel("طلوع خورشید: -")
        self.sunset_label = QLabel("غروب خورشید: -")
        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignCenter)

        for label in [self.city_label, self.temp_label, self.feels_label, self.desc_label,
                     self.humidity_label, self.wind_label, self.sunrise_label, self.sunset_label]:
            label.setFont(QFont("Arial", 14))

        current_layout.addWidget(self.icon_label, 0, 0, 4, 1)
        current_layout.addWidget(self.city_label, 0, 1)
        current_layout.addWidget(self.temp_label, 1, 1)
        current_layout.addWidget(self.feels_label, 2, 1)
        current_layout.addWidget(self.desc_label, 3, 1)
        current_layout.addWidget(self.humidity_label, 4, 1)
        current_layout.addWidget(self.wind_label, 5, 1)
        current_layout.addWidget(self.sunrise_label, 6, 1)
        current_layout.addWidget(self.sunset_label, 7, 1)

        layout.addWidget(self.current_frame)

        forecast_label = QLabel("پیش‌بینی ۵ روز آینده")
        forecast_label.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(forecast_label)

        scroll = QScrollArea()
        scroll_widget = QWidget()
        self.forecast_layout = QHBoxLayout(scroll_widget)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        self.loading_label = QLabel("در حال بارگذاری...")
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setFont(QFont("Arial", 16))
        self.loading_label.hide()
        layout.addWidget(self.loading_label)

        footer = QLabel("Developed by Safari")
        footer.setFont(QFont("Arial", 10))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #888; padding: 10px;")
        layout.addWidget(footer)

    def search_weather(self):
        city = self.city_input.text().strip()
        if not city:
            self.loading_label.setText("لطفاً نام شهر را وارد کنید!")
            self.loading_label.show()
            return

        self.loading_label.show()
        self.loading_label.setText("در حال دریافت اطلاعات...")

        self.thread = WeatherThread(city)
        self.thread.result.connect(self.display_weather)
        self.thread.error.connect(self.show_error)
        self.thread.start()

    def display_weather(self, current, forecast):
        self.loading_label.hide()

        main = current['main']
        weather = current['weather'][0]
        wind = current['wind']
        sys_info = current['sys']

        self.city_label.setText(f"شهر: {current['name']}, {current['sys']['country']}")
        self.temp_label.setText(f"دما: {main['temp']:.1f} °C")
        self.feels_label.setText(f"احساس می‌شود: {main['feels_like']:.1f} °C")
        self.desc_label.setText(f"وضعیت: {weather['description'].capitalize()}")
        self.humidity_label.setText(f"رطوبت: {main['humidity']}%")
        self.wind_label.setText(f"سرعت باد: {wind['speed']} m/s")

        timezone_offset = current['timezone']
        local_offset = timedelta(seconds=timezone_offset)

        sunrise_dt = datetime.fromtimestamp(sys_info['sunrise'], tz=timezone.utc) + local_offset
        sunset_dt = datetime.fromtimestamp(sys_info['sunset'], tz=timezone.utc) + local_offset

        sunrise = sunrise_dt.strftime('%H:%M')
        sunset = sunset_dt.strftime('%H:%M')

        self.sunrise_label.setText(f"طلوع خورشید: {sunrise}")
        self.sunset_label.setText(f"غروب خورشید: {sunset}")

        icon_name = self.get_icon_name(weather['main'])
        icon = qta.icon(icon_name, color='white', size=128)
        self.icon_label.setPixmap(icon.pixmap(128, 128))

        
        for i in reversed(range(self.forecast_layout.count())):
            self.forecast_layout.itemAt(i).widget().setParent(None)

        
        daily = {}
        for item in forecast['list']:
            date = item['dt_txt'].split(' ')[0]
            temp_min = item['main']['temp_min']
            temp_max = item['main']['temp_max']
            main_weather = item['weather'][0]['main']

            if date not in daily:
                daily[date] = {
                    'temp_min': temp_min,
                    'temp_max': temp_max,
                    'weathers': []
                }
            daily[date]['temp_min'] = min(daily[date]['temp_min'], temp_min)
            daily[date]['temp_max'] = max(daily[date]['temp_max'], temp_max)
            daily[date]['weathers'].append(main_weather)

        
        for date in daily:
            counter = Counter(daily[date]['weathers'])
            important_conditions = ['Snow', 'Thunderstorm', 'Rain', 'Drizzle']
            has_important = any(cond in counter for cond in important_conditions)
            if has_important:
                
                important_counter = {k: counter[k] for k in counter if k in important_conditions}
                dominant = max(important_counter, key=important_counter.get)
            else:
                
                dominant = counter.most_common(1)[0][0]

            daily[date]['dominant_weather'] = dominant

        
        for i, (date, data) in enumerate(list(daily.items())[:5]):
            day_frame = QFrame()
            day_frame.setFrameShape(QFrame.StyledPanel)
            day_layout = QVBoxLayout(day_frame)

            dt = datetime.strptime(date, '%Y-%m-%d')
            day_name = dt.strftime('%A')
            persian_days = {'Monday': 'دوشنبه', 'Tuesday': 'سه‌شنبه', 'Wednesday': 'چهارشنبه',
                            'Thursday': 'پنج‌شنبه', 'Friday': 'جمعه', 'Saturday': 'شنبه', 'Sunday': 'یکشنبه'}
            day_label = QLabel(f"{persian_days.get(day_name, day_name)}\n{dt.strftime('%d/%m')}")
            day_label.setAlignment(Qt.AlignCenter)
            day_label.setFont(QFont("Arial", 12, QFont.Bold))

            icon_name = self.get_icon_name(data['dominant_weather'])
            day_icon = qta.icon(icon_name, color='white', size=64)
            icon_label = QLabel()
            icon_label.setPixmap(day_icon.pixmap(64, 64))
            icon_label.setAlignment(Qt.AlignCenter)

            temp_label = QLabel(f"{data['temp_max']:.0f}° / {data['temp_min']:.0f}°")
            temp_label.setAlignment(Qt.AlignCenter)

            day_layout.addWidget(day_label)
            day_layout.addWidget(icon_label)
            day_layout.addWidget(temp_label)

            self.forecast_layout.addWidget(day_frame)

    def get_icon_name(self, condition):
        icons = {
            'Thunderstorm': 'fa5s.bolt',
            'Snow': 'fa5s.snowflake',
            'Rain': 'fa5s.cloud-rain',
            'Drizzle': 'fa5s.cloud-showers-heavy',
            'Clouds': 'fa5s.cloud',
            'Clear': 'fa5s.sun',
            'Mist': 'fa5s.water',
            'Fog': 'fa5s.smog',
        }
        return icons.get(condition, 'fa5s.cloud-sun')

    def show_error(self, msg):
        self.loading_label.setText(msg)
        self.loading_label.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_stylesheet(app, theme='dark_teal.xml', invert_secondary=True)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())