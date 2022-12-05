# formatted with Google yapf
# Bryce Happel Walton

import platform
import subprocess
import sys
import tomllib
import can
from os import listdir
from math import pi
from time import time
from qutil import Image, Arc
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, pyqtSlot, QPoint, QPropertyAnimation
from PyQt5.QtGui import QColor, QCursor, QFontDatabase, QFont, QPalette, QTransform
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QWidget
from can_handle import CanApplication, can_ids
from dial import Dial

SYSTEM = platform.system()

CONFIG_PATH = "config"
RESOURCE_PATH = "resources"
IMAGE_PATH = RESOURCE_PATH + "/images"
FONT_PATH = RESOURCE_PATH + "/fonts"

FONT_GROUP = "Montserrat Bold"

SCREEN_SIZE = [1920, 720]
SCREEN_REFRESH_RATE = 75 if SYSTEM == "Linux" else 60 if SYSTEM == "Darwin" else 144
DIAL_SIZE = 660
BACKGROUND_COLOR = [0, 0, 0]
AWAKEN_SEQUENCE_DURATION = 1500
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
    ratio = (rpm * TIRE_DIAMETER) / (FINAL_DRIVE_RATIO * speed * KPH_TO_MPH_SCALE * GEAR_CALC_CONSTANT)

    for i, v in enumerate(GEAR_RATIOS):
        if ratio >= v:
            return f'{i+1}'

    return 'N'


class MainWindow(QMainWindow):

    def __init__(self, scale: float = 1) -> None:
        super().__init__()
        major_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32
        minor_dial_angle_range = 2 * pi - major_dial_angle_range - pi / 4 * 2

        vertical_mirror = QTransform().rotate(180)
        symbol_blue_color = QColor(0, 0, 255)
        symbol_green_color = QColor(0, 230, 0)
        symbol_white_color = QColor(255, 255, 255)
        symbol_gray_color = QColor(125, 125, 125)
        symbol_yellow_color = QColor(255, 179, 0)
        symbol_red_color = QColor(255, 0, 0)

        turn_signal_offset_x = int(70 * scale)
        turn_signal_offset_y = int(40 * scale)
        dial_size_int = int(DIAL_SIZE * scale)
        symbol_size = int(63 * scale)
        bottom_symbol_y_offset = int(10 * scale)
        dial_size = QSize(dial_size_int, dial_size_int)

        major_dial_opacity = 0.3
        major_dial_width = 120 * scale

        minor_dial_opacity = 0.15
        minor_dial_width = 20 * scale

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

        self.coolant_temp_gauge = Dial(self,
                                       size=dial_size,
                                       min_unit=GAUGE_PARAMS["coolant_temp"]["min"],
                                       max_unit=GAUGE_PARAMS["coolant_temp"]["max"],
                                       redline=GAUGE_PARAMS["coolant_temp"]["redline"],
                                       blueline=GAUGE_PARAMS["coolant_temp"]["blueline"],
                                       blueline_color=QColor(175, 150, 255),
                                       dial_opacity=minor_dial_opacity,
                                       dial_width=minor_dial_width,
                                       mid_sections=GAUGE_PARAMS["coolant_temp"]["mid_sections"],
                                       no_font=True,
                                       visual_num_gap=GAUGE_PARAMS["coolant_temp"]["visual_num_gap"],
                                       angle_offset=major_dial_angle_range - pi + pi / 2.5,
                                       angle_range=minor_dial_angle_range,
                                       **dial_int_params_minor)
        self.coolant_temp_gauge.move(int(dial_size_int / 4), int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))

        self.tachometer = Dial(self,
                               size=dial_size,
                               min_unit=GAUGE_PARAMS["tachometer"]["min"],
                               max_unit=GAUGE_PARAMS["tachometer"]["max"],
                               redline=GAUGE_PARAMS["tachometer"]["redline"],
                               mid_sections=GAUGE_PARAMS["tachometer"]["mid_sections"],
                               denomination=GAUGE_PARAMS["tachometer"]["denomination"],
                               visual_num_gap=GAUGE_PARAMS["tachometer"]["denomination"],
                               label_font=QFont(FONT_GROUP, int(20 * scale)),
                               angle_offset=pi,
                               dial_opacity=major_dial_opacity,
                               dial_width=major_dial_width,
                               angle_range=major_dial_angle_range,
                               **dial_int_params_major)
        self.tachometer.frame.setStyleSheet("background:transparent")
        self.tachometer.move(int(dial_size_int / 4), int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))

        self.speedometer = Dial(self,
                                size=dial_size,
                                min_unit=GAUGE_PARAMS["speedometer"]["min"],
                                max_unit=GAUGE_PARAMS["speedometer"]["max"],
                                redline=GAUGE_PARAMS["speedometer"]["max"] + 1,
                                mid_sections=GAUGE_PARAMS["speedometer"]["mid_sections"],
                                visual_num_gap=20,
                                dial_opacity=major_dial_opacity,
                                dial_width=major_dial_width,
                                label_font=QFont(FONT_GROUP, int(18 * scale)),
                                angle_offset=pi,
                                angle_range=major_dial_angle_range,
                                **dial_int_params_major)
        self.speedometer.move(int(SCREEN_SIZE[0] - dial_size_int - dial_size_int / 4),
                              int(SCREEN_SIZE[1] / 2 - dial_size_int / 2))

        self.traction_control_mode_image = Image(self, IMAGE_PATH + "/traction-mode-indicator-light.png",
                                                 symbol_green_color)
        self.traction_control_mode_image.resize(symbol_size, symbol_size)
        self.traction_control_mode_image.move(int(SCREEN_SIZE[0] / 2 - symbol_size / 2),
                                              int(SCREEN_SIZE[1] - symbol_size - bottom_symbol_y_offset))

        self.traction_control_off_image = Image(self, IMAGE_PATH + "/vehicle-dynamics-control-off-indicator-light.png",
                                                symbol_yellow_color)
        self.traction_control_off_image.resize(symbol_size, symbol_size)
        self.traction_control_off_image.move(int(SCREEN_SIZE[0] / 2 - symbol_size / 2 + symbol_size + 5),
                                             int(SCREEN_SIZE[1] - symbol_size - bottom_symbol_y_offset))

        self.door_open_warning_image = Image(self, IMAGE_PATH + "/dooropen-warning-light.png", symbol_red_color)
        self.door_open_warning_image.resize(symbol_size, symbol_size)
        self.door_open_warning_image.move(int(SCREEN_SIZE[0] / 2 - symbol_size / 2 + 5 * (symbol_size + 5)),
                                          int(SCREEN_SIZE[1] - symbol_size - bottom_symbol_y_offset))

        self.seatbelt_driver_warning_image = Image(self, IMAGE_PATH + "/seatbelt-warning-light.png", symbol_red_color)
        self.seatbelt_driver_warning_image.resize(symbol_size, symbol_size)
        self.seatbelt_driver_warning_image.move(int(SCREEN_SIZE[0] / 2 - symbol_size / 2 + 4 * (symbol_size + 5)),
                                                int(SCREEN_SIZE[1] - symbol_size - bottom_symbol_y_offset))

        self.cruise_control_status_image = Image(self, IMAGE_PATH + "/cruise-control-indicator-light.png",
                                                 symbol_gray_color)
        self.cruise_control_status_image.resize(symbol_size, symbol_size)
        self.cruise_control_status_image.move(
            self.speedometer.pos() + QPoint(dial_size_int // 2 - symbol_size // 2 - 3, dial_size_int // 2 -
                                            self.cruise_control_status_image.size().height() // 2) -
            QPoint(0, int(symbol_size * 1.2)))

        angle_mid = 30
        arc_width = 1.5
        size_scale = 4.25

        self.cruise_control_status_widget = QWidget(self)
        self.cruise_control_status_widget.setStyleSheet("background:transparent")
        self.cruise_control_status_widget.resize(QSize(int(dial_size_int / size_scale),
                                                       int(dial_size_int / size_scale)))
        self.cruise_control_status_widget.move(self.speedometer.pos() + QPoint(dial_size_int // 2, dial_size_int // 2) -
                                               QPoint(self.cruise_control_status_widget.size().width() // 2,
                                                      self.cruise_control_status_widget.size().height() // 2))
        self.cruise_control_arc_left = Arc(self.cruise_control_status_widget, self.cruise_control_status_widget.size(),
                                           symbol_gray_color, arc_width)
        self.cruise_control_arc_left.pen.setCapStyle(Qt.RoundCap)
        self.cruise_control_arc_left.setArc(90 + angle_mid, 180 - angle_mid * 2)

        self.cruise_control_arc_right = Arc(self.cruise_control_status_widget, self.cruise_control_status_widget.size(),
                                            symbol_gray_color, arc_width)
        self.cruise_control_arc_right.pen.setCapStyle(Qt.RoundCap)
        self.cruise_control_arc_right.setArc(270 + angle_mid, 180 - angle_mid * 2)

        label_font = QFont(FONT_GROUP, int(22 * scale))
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, symbol_gray_color)

        self.cruise_control_speed_label = QLabel(self)
        self.cruise_control_speed_label.setStyleSheet("background:transparent")
        self.cruise_control_speed_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.cruise_control_speed_label.setFont(label_font)
        self.cruise_control_speed_label.setText("0")
        self.cruise_control_speed_label.setPalette(palette)
        self.cruise_control_speed_label.resize(symbol_size, symbol_size)
        self.cruise_control_speed_label.move(
            self.speedometer.pos() +
            QPoint(dial_size_int // 2 - self.cruise_control_speed_label.size().width() // 2, dial_size_int // 2 -
                   self.cruise_control_speed_label.size().height() // 2) + QPoint(0, int(symbol_size * 1.05)))

        self.high_beam_image = Image(self, IMAGE_PATH + "/highbeam-indicator-light.png", symbol_blue_color)
        self.high_beam_image.resize(symbol_size, symbol_size)
        self.high_beam_image.move(self.tachometer.pos() + QPoint(symbol_size * 2, 0))

        self.low_beam_image = Image(self, IMAGE_PATH + "/headlight-indicator-light.png", symbol_green_color)
        self.low_beam_image.resize(int(symbol_size * 1.2), int(symbol_size * 1.2))
        self.low_beam_image.move(self.speedometer.pos() + QPoint(self.tachometer.size().width() - symbol_size * 3, 0))

        self.fog_light_image = Image(self, IMAGE_PATH + "/front-fog-indicator-light.png", symbol_green_color)
        self.fog_light_image.resize(symbol_size, symbol_size)
        self.fog_light_image.move(self.tachometer.pos() + QPoint(symbol_size, symbol_size))

        self.brake_warning_image = Image(self, IMAGE_PATH + "/brake-warning-indicator-light-letters-only.png",
                                         symbol_red_color)
        self.brake_warning_image.resize(int(symbol_size * 1.3), int(symbol_size * 1.3))
        self.brake_warning_image.move(self.speedometer.pos() +
                                      QPoint(dial_size_int // 2 - self.brake_warning_image.size().width() //
                                             2, dial_size_int // 2 - self.brake_warning_image.size().height() // 2) +
                                      QPoint(0, int(symbol_size * 3)))

        self.right_turn_signal_image_active = Image(self, IMAGE_PATH + "/turn-signal-arrow.png", symbol_green_color)
        self.right_turn_signal_image_active.resize(symbol_size, symbol_size)
        self.right_turn_signal_image_active.move(self.speedometer.pos() +
                                                 QPoint(turn_signal_offset_x, turn_signal_offset_y))

        self.left_turn_signal_image_active = Image(self, IMAGE_PATH + "/turn-signal-arrow.png", symbol_green_color,
                                                   vertical_mirror)
        self.left_turn_signal_image_active.resize(symbol_size, symbol_size)
        self.left_turn_signal_image_active.move(self.tachometer.pos() +
                                                QPoint(self.tachometer.size().width() - symbol_size, 0) +
                                                QPoint(-turn_signal_offset_x, turn_signal_offset_y))

        label_font = QFont(FONT_GROUP, int(34 * scale))
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))

        self.speed_label = QLabel(self)
        self.speed_label.setStyleSheet("background:transparent")
        self.speed_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.speed_label.setFont(label_font)
        self.speed_label.setPalette(palette)
        self.speed_label.setText("0")
        self.speed_label.resize(dial_size_int, dial_size_int)
        sl_size = self.speed_label.size()
        self.speed_label.move(
            int(SCREEN_SIZE[0] - dial_size_int - dial_size_int / 4 + dial_size_int / 2 - sl_size.width() / 2),
            int(SCREEN_SIZE[1] / 2 - sl_size.height() / 2))

        self.gear_indicator_label = QLabel(self)
        self.gear_indicator_label.setStyleSheet("background:transparent")
        self.gear_indicator_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.gear_indicator_label.setFont(label_font)
        self.gear_indicator_label.setPalette(palette)
        self.gear_indicator_label.setText("N")
        self.gear_indicator_label.resize(dial_size_int, dial_size_int)
        gl_size = self.speed_label.size()
        self.gear_indicator_label.move(int(dial_size_int / 4 + dial_size_int / 2 - gl_size.width() / 2),
                                       int(SCREEN_SIZE[1] / 2 - gl_size.height() / 2))


class Application(QApplication):

    awakened = pyqtSignal()
    init_wait = pyqtSignal()
    cluster_vars = {}
    cluster_vars_update_ts = {i: time() for i in VISUAL_UPDATE_INTERVALS.keys()}

    def __init__(self, scale: float = 1) -> None:
        super().__init__([])
        self.setOverrideCursor(QCursor(Qt.BlankCursor))
        primary_container = MainWindow(scale)
        primary_container.setStyleSheet(
            f"background-color: rgb({BACKGROUND_COLOR[0]}, {BACKGROUND_COLOR[1]}, {BACKGROUND_COLOR[2]})")

        self.start_time = time()
        self.primary_container = primary_container
        self.update_funcs = {}

        start_time = 0.4

        angle_mid = 30
        duration = 100

        start_left_start = 180
        end_left_start = 180 - 90 + angle_mid
        start_left_end = 0
        end_left_end = 180 - angle_mid * 2

        start_right_start = 0
        end_right_start = 90 - angle_mid
        start_right_end = 0
        end_right_end = -180 + angle_mid * 2

        self.cruise_dial_left_animation_start = QPropertyAnimation(self)
        self.cruise_dial_left_animation_start.setTargetObject(self.primary_container.cruise_control_arc_left)
        self.cruise_dial_left_animation_start.setPropertyName(b"arc_start")
        self.cruise_dial_left_animation_start.setStartValue(start_left_start)
        self.cruise_dial_left_animation_start.setEndValue(end_left_start)
        self.cruise_dial_left_animation_start.setDuration(duration)

        self.cruise_dial_left_animation_end = QPropertyAnimation(self)
        self.cruise_dial_left_animation_end.setTargetObject(self.primary_container.cruise_control_arc_left)
        self.cruise_dial_left_animation_end.setPropertyName(b"arc_end")
        self.cruise_dial_left_animation_end.setStartValue(start_left_end)
        self.cruise_dial_left_animation_end.setEndValue(end_left_end)
        self.cruise_dial_left_animation_end.setDuration(duration)

        self.cruise_dial_right_animation_start = QPropertyAnimation(self)
        self.cruise_dial_right_animation_start.setTargetObject(self.primary_container.cruise_control_arc_right)
        self.cruise_dial_right_animation_start.setPropertyName(b"arc_start")
        self.cruise_dial_right_animation_start.setStartValue(start_right_start)
        self.cruise_dial_right_animation_start.setEndValue(end_right_start)
        self.cruise_dial_right_animation_start.setDuration(duration)

        self.cruise_dial_right_animation_end = QPropertyAnimation(self)
        self.cruise_dial_right_animation_end.setTargetObject(self.primary_container.cruise_control_arc_right)
        self.cruise_dial_right_animation_end.setPropertyName(b"arc_end")
        self.cruise_dial_right_animation_end.setStartValue(start_right_end)
        self.cruise_dial_right_animation_end.setEndValue(end_right_end)
        self.cruise_dial_right_animation_end.setDuration(duration)

        self.cruise_dial_left_animation_start_close = QPropertyAnimation(self)
        self.cruise_dial_left_animation_start_close.setTargetObject(self.primary_container.cruise_control_arc_left)
        self.cruise_dial_left_animation_start_close.setPropertyName(b"arc_start")
        self.cruise_dial_left_animation_start_close.setStartValue(end_left_start)
        self.cruise_dial_left_animation_start_close.setEndValue(start_left_start)
        self.cruise_dial_left_animation_start_close.setDuration(duration)

        self.cruise_dial_left_animation_end_close = QPropertyAnimation(self)
        self.cruise_dial_left_animation_end_close.setTargetObject(self.primary_container.cruise_control_arc_left)
        self.cruise_dial_left_animation_end_close.setPropertyName(b"arc_end")
        self.cruise_dial_left_animation_end_close.setStartValue(end_left_end)
        self.cruise_dial_left_animation_end_close.setEndValue(start_left_end)
        self.cruise_dial_left_animation_end_close.setDuration(duration)

        self.cruise_dial_right_animation_start_close = QPropertyAnimation(self)
        self.cruise_dial_right_animation_start_close.setTargetObject(self.primary_container.cruise_control_arc_right)
        self.cruise_dial_right_animation_start_close.setPropertyName(b"arc_start")
        self.cruise_dial_right_animation_start_close.setStartValue(end_right_start)
        self.cruise_dial_right_animation_start_close.setEndValue(start_right_start)
        self.cruise_dial_right_animation_start_close.setDuration(duration)

        self.cruise_dial_right_animation_end_close = QPropertyAnimation(self)
        self.cruise_dial_right_animation_end_close.setTargetObject(self.primary_container.cruise_control_arc_right)
        self.cruise_dial_right_animation_end_close.setPropertyName(b"arc_end")
        self.cruise_dial_right_animation_end_close.setStartValue(end_right_end)
        self.cruise_dial_right_animation_end_close.setEndValue(start_right_end)
        self.cruise_dial_right_animation_end_close.setDuration(duration)

        t = time()
        timer2 = QTimer(self)

        self.init_wait.connect(self.awakenClusters)

        @pyqtSlot()
        def init_wait():
            if time() - t > start_time:
                timer2.stop()
                timer2.deleteLater()
                self.init_wait.emit()

        timer2.timeout.connect(init_wait)
        timer2.start(1)


    def awakenClusters(self) -> None:
        timer = QTimer(self)

        self._awaken_a = 0
        self._awaken_t = 0

        t_step = AWAKEN_SEQUENCE_DURATION // 1000
        a_step = t_step / AWAKEN_SEQUENCE_DURATION

        self.primary_container.tachometer.setDial(0)
        self.primary_container.speedometer.setDial(0)

        self._last_time = time() * 1000
        start_time = self._last_time

        @pyqtSlot()
        def dialMove():
            current_time = time() * 1000
            dt = current_time - self._last_time
            tdt = current_time - start_time

            if tdt >= AWAKEN_SEQUENCE_DURATION:
                timer.stop()
                timer.deleteLater()
                self.awakened.emit()
            elif dt >= t_step:
                step = dt / t_step * a_step * 2

                if tdt >= AWAKEN_SEQUENCE_DURATION / 2:
                    self._awaken_a -= step
                else:
                    self._awaken_a += step

            self.primary_container.tachometer.setDial(self._awaken_a)
            self.primary_container.speedometer.setDial(self._awaken_a)

            self._last_time = time() * 1000

        timer.timeout.connect(dialMove)
        timer.start(t_step)

    def animateCruiseControl(self, opening: bool = True) -> None:
        if opening:
            self.cruise_dial_left_animation_start.start()
            self.cruise_dial_left_animation_end.start()
            self.cruise_dial_right_animation_start.start()
            self.cruise_dial_right_animation_end.start()
        else:
            self.cruise_dial_left_animation_start_close.start()
            self.cruise_dial_left_animation_end_close.start()
            self.cruise_dial_right_animation_start_close.start()
            self.cruise_dial_right_animation_end_close.start()

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

        self.primary_container.gear_indicator_label.setText(gear)

    @pyqtSlot(tuple)
    def updateVar(self, data: tuple) -> None:
        t = time()
        var, val = data
        self.cluster_vars[var] = val

        if t - self.cluster_vars_update_ts[var] <= VISUAL_UPDATE_INTERVALS[var]:
            return

        if var == "vehicle_speed":
            val *= KPH_TO_MPH_SCALE
            self.primary_container.speed_label.setText(f"{val:.0f}")
            self.primary_container.speedometer.setUnit(val)
        elif var == "rpm":
            self.updateGearIndicator()
            self.primary_container.tachometer.setUnit(val)
        elif var == "turn_signals":
            self.primary_container.left_turn_signal_image_active.setVisible(val[0])
            self.primary_container.right_turn_signal_image_active.setVisible(val[1])
        # elif var == "fuel_level":
        #     pass
        # elif var == "oil_temp":
        #     pass
        elif var == "coolant_temp":
            self.primary_container.coolant_temp_gauge.setUnit(val * C_TO_F_SCALE + C_TO_F_OFFSET)
        elif var == "handbrake":
            self.primary_container.brake_warning_image.setVisible(val)
        elif var == "neutral_switch":
            self.updateGearIndicator()
        elif var == "reverse_switch":
            self.updateGearIndicator()
        elif var == "traction_control":
            self.primary_container.traction_control_off_image.setVisible(val)
        elif var == "traction_control_mode":
            self.primary_container.traction_control_mode_image.setVisible(val)
        elif var == "seatbelt_driver":
            self.primary_container.seatbelt_driver_warning_image.setVisible(val)
        elif var == "cruise_control_status":
            self.primary_container.cruise_control_status_image.setVisible(val)
        elif var == "fog_lights":
            self.primary_container.fog_light_image.setVisible(val)
        elif var == "door_states":
            self.primary_container.door_open_warning_image.setVisible('1' in val)
        elif var == "headlights":
            self.primary_container.low_beam_image.setVisible(val[0] or val[1])
            self.primary_container.high_beam_image.setVisible(val[2])
        elif var == "cruise_control_speed":
            if val > 0 and self.cluster_vars.get("cruise_control_status", 0):
                self.primary_container.cruise_control_speed_label.setVisible(True)
                self.primary_container.cruise_control_speed_label.setText(f"{val}")
            else:
                self.primary_container.cruise_control_status_widget.setVisible(False)
                self.primary_container.cruise_control_speed_label.setVisible(False)
        elif var == "cruise_control_set":
            if val and self.cluster_vars.get("cruise_control_status", 0):
                print(True)
                self.animateCruiseControl()
            else:
                self.animateCruiseControl(False)

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
        QFontDatabase.addApplicationFont(f"{FONT_PATH}/Montserrat/static/{font_file}")

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
            shutdown_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True)
            setup_can = subprocess.run(
                ["sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can", "bitrate", "500000"], check=True)

            bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=500000)
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
