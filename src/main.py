# formatted with yapf
# Bryce Happel Walton

import platform
import subprocess
import sys
import tomllib
import can
from os import listdir
from math import pi
from time import time
from qutil import Image
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, pyqtSlot, QPoint
from PyQt5.QtGui import (QColor, QCursor, QFontDatabase, QFont, QImage,
                         QPalette, QPixmap, QTransform)
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from can_handle import CanApplication, can_ids
from dial import Dial

SYSTEM = platform.system()

CONFIG_PATH = "config"
RESOURCE_PATH = "resources"
IMAGE_PATH = RESOURCE_PATH + "/images"
FONT_PATH = RESOURCE_PATH + "/fonts"

SCREEN_SIZE = [1920, 720]
SCREEN_REFRESH_RATE = 75 if SYSTEM == "Linux" else 60 if SYSTEM == "Darwin" else 144
DIAL_SIZE = 660
BACKGROUND_COLOR = [0, 0, 0]

VISUAL_UPDATE_INTERVALS = {"coolant_temp": 0.75, "oil_temp": 0.75}

with open(CONFIG_PATH + "/gauge_config.toml", "rb") as f:
    GAUGE_PARAMS = tomllib.load(f)

for i in can_ids.keys():
    if not i in VISUAL_UPDATE_INTERVALS:
        VISUAL_UPDATE_INTERVALS[i] = 1 / (SCREEN_REFRESH_RATE * 2)

C_TO_F_SCALE = 1.8
C_TO_F_OFFSET = 32
KPH_TO_MPH_SCALE = 0.62137119

GEAR_CALC_CONSTANT = (5280 * 12) / (pi * 60)
GEAR_RATIOS = [3.454, 1.947, 1.296, 0.972, 0.78, 0.666]
TIRE_DIAMETER = 26
FINAL_DRIVE_RATIO = 4.111


def calcGear(rpm: int, speed: int):
    ratio = (rpm * TIRE_DIAMETER) / (FINAL_DRIVE_RATIO * speed *
                                     KPH_TO_MPH_SCALE * GEAR_CALC_CONSTANT)

    for i, v in enumerate(GEAR_RATIOS):
        if ratio >= v:
            return f'{i+1}'

    return 'N'


class MainWindow(QMainWindow):

    def __init__(self, scale: float = 1) -> None:
        super().__init__()
        font_group = "Montserrat Bold"

        major_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32
        minor_dial_angle_range = 2 * pi - major_dial_angle_range - pi / 4 * 2

        vertical_mirror = QTransform().rotate(180)
        symbol_blue_color = QColor(0, 0, 255)
        symbol_green_color = QColor(0, 230, 0)
        symbol_white_color = QColor(255, 255, 255)
        symbol_yellow_color = QColor(255, 179, 0)
        symbol_red_color = QColor(255, 0, 0)

        turn_signal_offset = int(-30 * scale)
        turn_signal_size = int(55 * scale)
        dial_size_int = int(DIAL_SIZE * scale)
        symbol_size = int(55 * scale)
        bottom_symbol_y_offset = int(10 * scale)
        dial_size = QSize(dial_size_int, dial_size_int)

        dial_opacity = 0.3
        dial_width = 120 * scale

        dial_int_params_minor = {
            "buffer_radius": 20 * scale,
            "num_radius": 50 * scale,
            "section_radius": 15 * scale,
            "minor_section_rad_offset": 3 * scale,
            "middle_section_rad_offset": 58 * scale,
            "major_section_rad_offset": 40 * scale
        }

        dial_int_params_major = {
            "buffer_radius": 20 * scale,
            "num_radius": 54 * scale,
            "section_radius": 20 * scale,
            "minor_section_rad_offset": 3 * scale,
            "middle_section_rad_offset": 43 * scale,
            "major_section_rad_offset": 40 * scale
        }

        for i, v in dial_int_params_minor.items():
            dial_int_params_minor[i] = int(v)
        for i, v in dial_int_params_major.items():
            dial_int_params_major[i] = int(v)

        self.coolant_temp_gauge = Dial(
            self,
            size=dial_size,
            min_unit=GAUGE_PARAMS["coolant_temp"]["min"],
            max_unit=GAUGE_PARAMS["coolant_temp"]["max"],
            redline=GAUGE_PARAMS["coolant_temp"]["redline"],
            blueline=GAUGE_PARAMS["coolant_temp"]["blueline"],
            blueline_color=QColor(125, 125, 255),
            dial_opacity=dial_opacity,
            dial_width=30,
            mid_sections=GAUGE_PARAMS["coolant_temp"]["mid_sections"],
            no_font=True,
            visual_num_gap=GAUGE_PARAMS["coolant_temp"]["visual_num_gap"],
            angle_offset=major_dial_angle_range - pi + pi / 2.5,
            angle_range=minor_dial_angle_range,
            **dial_int_params_minor)
        self.coolant_temp_gauge.move(
            int(dial_size_int / 4),
            int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))

        self.tachometer = Dial(
            self,
            size=dial_size,
            min_unit=GAUGE_PARAMS["tachometer"]["min"],
            max_unit=GAUGE_PARAMS["tachometer"]["max"],
            redline=GAUGE_PARAMS["tachometer"]["redline"],
            mid_sections=GAUGE_PARAMS["tachometer"]["mid_sections"],
            denomination=GAUGE_PARAMS["tachometer"]["denomination"],
            visual_num_gap=GAUGE_PARAMS["tachometer"]["denomination"],
            label_font=QFont(font_group, int(19 * scale)),
            angle_offset=pi,
            dial_opacity=dial_opacity,
            dial_width=dial_width,
            angle_range=major_dial_angle_range,
            **dial_int_params_major)
        self.tachometer.frame.setStyleSheet("background:transparent")
        self.tachometer.move(int(dial_size_int / 4),
                             int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))

        self.speedometer = Dial(
            self,
            size=dial_size,
            min_unit=GAUGE_PARAMS["speedometer"]["min"],
            max_unit=GAUGE_PARAMS["speedometer"]["max"],
            redline=GAUGE_PARAMS["speedometer"]["max"] + 1,
            mid_sections=GAUGE_PARAMS["speedometer"]["mid_sections"],
            visual_num_gap=20,
            dial_opacity=dial_opacity,
            dial_width=dial_width,
            label_font=QFont(font_group, int(16 * scale)),
            angle_offset=pi,
            angle_range=major_dial_angle_range,
            **dial_int_params_major)
        self.speedometer.move(
            int(SCREEN_SIZE[0] - dial_size_int - dial_size_int / 4),
            int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))

        self.traction_mode_image = Image(
            self, IMAGE_PATH + "/traction-mode-indicator-light.png",
            symbol_green_color)
        self.traction_mode_image.move(
            int(SCREEN_SIZE[0] / 2 - symbol_size / 2),
            int(SCREEN_SIZE[1] - symbol_size - bottom_symbol_y_offset))
        self.traction_mode_image.resize(symbol_size, symbol_size)

        self.traction_control_off_image = Image(
            self,
            IMAGE_PATH + "/vehicle-dynamics-control-off-indicator-light.png",
            symbol_yellow_color)
        self.traction_control_off_image.move(
            int(SCREEN_SIZE[0] / 2 - symbol_size / 2 + symbol_size + 5),
            int(SCREEN_SIZE[1] - symbol_size - bottom_symbol_y_offset))
        self.traction_control_off_image.resize(symbol_size, symbol_size)

        self.seatbelt_warning_image = Image(
            self, IMAGE_PATH + "/seatbelt-warning-light.png", symbol_red_color)
        self.seatbelt_warning_image.move(
            int(SCREEN_SIZE[0] / 2 - symbol_size / 2 + 4 * (symbol_size + 5)),
            int(SCREEN_SIZE[1] - symbol_size - bottom_symbol_y_offset))
        self.seatbelt_warning_image.resize(symbol_size, symbol_size)

        self.cruise_control_image = Image(
            self, IMAGE_PATH + "/cruise-control-indicator-light.png",
            symbol_white_color)
        self.cruise_control_image.move(self.speedometer.pos() + QPoint(
            dial_size_int // 2 - symbol_size // 2 - 4, dial_size_int // 2 -
            self.cruise_control_image.size().height() // 2) -
                                       QPoint(0, symbol_size))
        self.cruise_control_image.resize(symbol_size, symbol_size)

        self.high_beam_image = Image(
            self, IMAGE_PATH + "/highbeam-indicator-light.png",
            symbol_blue_color)
        self.high_beam_image.move(int(dial_size_int / 4 + symbol_size),
                                  int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))
        self.high_beam_image.resize(int(symbol_size * 1.25),
                                    int(symbol_size * 1.25))

        self.low_beam_image = Image(
            self, IMAGE_PATH + "/headlight-indicator-light.png",
            symbol_green_color)
        self.low_beam_image.move(
            int(SCREEN_SIZE[0] - dial_size_int - dial_size_int / 4 +
                dial_size_int - symbol_size * 2),
            int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))
        self.low_beam_image.resize(int(symbol_size * 1.25),
                                   int(symbol_size * 1.25))

        self.fog_light_image = Image(
            self, IMAGE_PATH + "/front-fog-indicator-light.png",
            symbol_green_color)
        self.fog_light_image.move(
            int(dial_size_int / 4),
            int(SCREEN_SIZE[1] / 2 - dial_size_int / 2 + symbol_size + 5))
        self.fog_light_image.resize(symbol_size, symbol_size)

        self.brake_warning_image = Image(
            self,
            IMAGE_PATH + "/brake-warning-indicator-light-letters-only.png",
            symbol_red_color)
        self.brake_warning_image.resize(int(symbol_size * 1.3),
                                        int(symbol_size * 1.3))
        self.brake_warning_image.move(self.speedometer.pos() + QPoint(
            dial_size_int // 2 -
            self.brake_warning_image.size().width() // 2, dial_size_int // 2 -
            self.brake_warning_image.size().height() // 2) +
                                      QPoint(0, int(symbol_size * 3)))

        self.right_turn_signal_image_active = Image(
            self, IMAGE_PATH + "/turn-signal-arrow.png", symbol_green_color)
        self.right_turn_signal_image_active.move(
            int(SCREEN_SIZE[0] - dial_size_int -
                dial_size_int / 4 - turn_signal_offset),
            int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))
        self.right_turn_signal_image_active.resize(turn_signal_size,
                                                   turn_signal_size)

        self.left_turn_signal_image_active = Image(
            self, IMAGE_PATH + "/turn-signal-arrow.png", symbol_green_color,
            vertical_mirror)
        self.left_turn_signal_image_active.move(
            int(dial_size_int / 4 + dial_size_int -
                turn_signal_size + turn_signal_offset),
            int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))
        self.left_turn_signal_image_active.resize(turn_signal_size,
                                                  turn_signal_size)

        rpm_label_size = 200
        label_font = QFont(font_group, int(30 * scale))
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        self.speed_label = QLabel(self)
        self.speed_label.setStyleSheet("background:transparent")
        self.speed_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.speed_label.setFont(label_font)
        self.speed_label.setPalette(palette)
        self.speed_label.setText("0")
        sl_size = self.speed_label.size()
        self.speed_label.move(
            int(SCREEN_SIZE[0] - dial_size_int - dial_size_int / 4 +
                dial_size_int / 2 - sl_size.width() / 2),
            int(SCREEN_SIZE[1] / 2 - sl_size.height() / 2))

        self.gear_label = QLabel(self)
        self.gear_label.setStyleSheet("background:transparent")
        self.gear_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.gear_label.setFont(label_font)
        self.gear_label.setPalette(palette)
        self.gear_label.setText("N")
        gl_size = self.speed_label.size()
        self.gear_label.move(
            int(dial_size_int / 4 + dial_size_int / 2 - gl_size.width() / 2),
            int(SCREEN_SIZE[1] / 2 - gl_size.height() / 2))

        label_font = QFont(font_group, int(16 * scale))
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        self.oil_temp_label = QLabel(self)
        self.oil_temp_label.setStyleSheet("background:transparent")
        self.oil_temp_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.oil_temp_label.setFont(label_font)
        self.oil_temp_label.setText("Oil Temp: 0 F")
        self.oil_temp_label.setPalette(palette)
        self.oil_temp_label.resize(int(200 * scale),
                                   int(rpm_label_size * scale))
        self.oil_temp_label.move(
            int(SCREEN_SIZE[0] / 2 -
                self.oil_temp_label.size().width() / 2),
            int(SCREEN_SIZE[1] / 2 -
                self.oil_temp_label.size().height() / 2))

        self.cruise_control_speed_label = QLabel(self)
        self.cruise_control_speed_label.setStyleSheet("background:transparent")
        self.cruise_control_speed_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.cruise_control_speed_label.setFont(label_font)
        self.cruise_control_speed_label.setText("Cruise Speed: 0")
        self.cruise_control_speed_label.setPalette(palette)
        self.cruise_control_speed_label.resize(int(200 * scale),
                                   int(rpm_label_size * scale))
        self.cruise_control_speed_label.move(
            int(SCREEN_SIZE[0] / 2 -
                self.cruise_control_speed_label.size().width() / 2),
            int(SCREEN_SIZE[1] / 2 -
                self.cruise_control_speed_label.size().height() / 2 + 30 * scale))

        label_font = QFont(font_group, int(17 * scale))
        color = QColor(255, 0, 0)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)


class Application(QApplication):

    awakened = pyqtSignal()

    cluster_vars = {}
    cluster_vars_update_ts = {
        i: time()
        for i in VISUAL_UPDATE_INTERVALS.keys()
    }

    awaken_sequence_duration_ms = 1750

    def __init__(self, scale: float = 1) -> None:
        super().__init__([])
        self.setOverrideCursor(QCursor(Qt.BlankCursor))
        primary_container = MainWindow(scale)
        primary_container.setStyleSheet(
            f"background-color: rgb({BACKGROUND_COLOR[0]}, {BACKGROUND_COLOR[1]}, {BACKGROUND_COLOR[2]})"
        )

        self.start_time = time()
        self.primary_container = primary_container
        self.update_funcs = {}

        self.awakenClusters()

    def awakenClusters(self) -> None:
        timer = QTimer(self)

        self._awaken_a = 0
        self._awaken_t = 0

        t_step = self.awaken_sequence_duration_ms // 1000
        a_step = t_step / self.awaken_sequence_duration_ms

        self.primary_container.tachometer.setDial(0)
        self.primary_container.speedometer.setDial(0)

        self._last_time = time() * 1000
        start_time = self._last_time

        @pyqtSlot()
        def dialMove():
            current_time = time() * 1000
            dt = current_time - self._last_time
            tdt = current_time - start_time

            if tdt >= self.awaken_sequence_duration_ms:
                timer.stop()
                timer.deleteLater()
                self.awakened.emit()
            elif dt >= t_step:
                step = dt / t_step * a_step * 2

                if tdt >= self.awaken_sequence_duration_ms / 2:
                    self._awaken_a -= step
                else:
                    self._awaken_a += step

            self.primary_container.tachometer.setDial(self._awaken_a)
            self.primary_container.speedometer.setDial(self._awaken_a)

            self._last_time = time() * 1000

        timer.timeout.connect(dialMove)
        timer.start(t_step)

    def updateGearIndicator(self) -> None:
        speed = self.cluster_vars.get('vehicle_speed', 1)
        rpm = self.cluster_vars.get('rpm', 0)
        neutral = self.cluster_vars.get('neutral_switch', 0)
        reverse = self.cluster_vars.get('reverse_switch', 0)

        if reverse:
            gear = 'R'
        elif neutral:
            gear = 'N'
        else:
            if speed == 0:
                gear = ''
            else:
                gear = calcGear(rpm, speed)

        self.primary_container.gear_label.setText(gear)

    @pyqtSlot(tuple)
    def updateVar(self, new_vars: tuple) -> None:
        t = time()
        var, val = new_vars
        self.cluster_vars[var] = val

        if t - self.cluster_vars_update_ts[var] <= VISUAL_UPDATE_INTERVALS[var]:
            return

        if var == "vehicle_speed":
            self.primary_container.speed_label.setText(
                f"{val * KPH_TO_MPH_SCALE:.0f}")
            self.primary_container.speedometer.setUnit(val * KPH_TO_MPH_SCALE)
        elif var == "rpm":
            self.updateGearIndicator()
            self.primary_container.tachometer.setUnit(val)
        elif var == "turn_signals":
            self.primary_container.left_turn_signal_image_active.setVisible(
                val["left_turn_signal"])
            self.primary_container.right_turn_signal_image_active.setVisible(
                val["right_turn_signal"])
        elif var == "fuel_level":
            pass
        elif var == "oil_temp":
            self.primary_container.oil_temp_label.setText(
                f"Oil Temp: {val * C_TO_F_SCALE + C_TO_F_OFFSET:.0f} F")
        elif var == "coolant_temp":
            self.primary_container.coolant_temp_gauge.setUnit(val *
                                                              C_TO_F_SCALE +
                                                              C_TO_F_OFFSET)
        elif var == "handbrake":
            self.primary_container.brake_warning_image.setVisible(val)
        elif var == "neutral_switch":
            self.updateGearIndicator()
        elif var == "reverse_switch":
            self.updateGearIndicator()
        elif var == "traction_control":
            self.primary_container.traction_control_off_image.setVisible(val)
        elif var == "trac_mode":
            self.primary_container.traction_mode_image.setVisible(val)
        elif var == "seatbelt_driver":
            self.primary_container.seatbelt_warning_image.setVisible(val)
        elif var == "cruise_control_status":
            self.primary_container.cruise_control_image.setVisible(val)
        elif var == "fog_lights":
            self.primary_container.fog_light_image.setVisible(val)
        elif var == "door_states":
            pass
        elif var == "headlights":
            self.primary_container.low_beam_image.setVisible(val["lowbeams"]
                                                             or val["drls"])
            self.primary_container.high_beam_image.setVisible(val["highbeams"])
        elif var == "cruise_control_speed":
            self.primary_container.cruise_control_speed_label.setText(
                f"Cruise Speed: {val * KPH_TO_MPH_SCALE:.0f}")

        self.cluster_vars[var] = val
        self.cluster_vars_update_ts[var] = t


if __name__ == "__main__":
    scale = 1
    if SYSTEM == "Darwin":
        scale = 1 / 1.3325
    elif SYSTEM == "Windows":
        scale = 1 / 1.25

    SCREEN_SIZE = [int(1920 * scale), int(720 * scale)]
    app = Application(scale=scale)

    for font_file in listdir(FONT_PATH + "/Montserrat/static"):
        QFontDatabase.addApplicationFont(
            f"{FONT_PATH}/Montserrat/static/{font_file}")

    screens = app.screens()
    if SYSTEM != "Linux":
        if len(screens) > 1:
            screen = screens[1]
            app.primary_container.move(screen.geometry().topLeft())
            app.primary_container.showFullScreen()
        else:
            app.primary_container.setFixedSize(SCREEN_SIZE[0], SCREEN_SIZE[1])
    else:
        screen = screens[0]
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
        app.primary_container.setFixedSize(SCREEN_SIZE[0], SCREEN_SIZE[1])

    if SYSTEM == "Linux" and len(sys.argv) > 1:
        using_canbus = sys.argv[1] != "nocan"
    elif SYSTEM != "Linux":
        using_canbus = False
    else:
        using_canbus = True

    if SYSTEM == "Linux":
        try:
            shutdown_can = subprocess.run(
                ["sudo", "/sbin/ip", "link", "set", "can0", "down"],
                check=True)
            setup_can = subprocess.run([
                "sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can",
                "bitrate", "500000"
            ],
                                       check=True)

            bus = can.interface.Bus(channel='can0',
                                    bustype='socketcan',
                                    bitrate=500000)
        except:
            print("Could not find PiCan device. Switching to emulation.")
            using_canbus = False

    if not using_canbus:
        import test_provider

        bus_virtual_car = can.interface.Bus(channel='test', bustype='virtual')
        bus = can.interface.Bus(channel='test', bustype='virtual')

        @pyqtSlot()
        def emulate_car():
            bus_virtual_car.send(test_provider.provide_random_message())

        @pyqtSlot()
        def run():
            timer = QTimer(app)
            timer.timeout.connect(emulate_car)
            timer.start(1000 // 500000)

        app.awakened.connect(run)

    can_app = CanApplication(app, bus)
    can_app.updated.connect(app.updateVar)

    @pyqtSlot()
    def run():
        can.Notifier(bus, [can_app.parse_data])

    app.awakened.connect(run)
    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
