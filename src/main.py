# formatted with Google yapf
# Bryce Happel Walton

import platform, subprocess, sys, tomllib, can
from os import listdir, path
from math import pi
from time import time
from functools import reduce
from qutil import Image, Arc, delay, timed_func, property_animation
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, pyqtSlot, QPoint, QPropertyAnimation
from PyQt5.QtGui import QColor, QCursor, QFontDatabase, QFont, QPalette, QTransform
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QWidget
from can_handle import CanApplication, can_ids, conversation_ids
from dial import Dial

SYSTEM = platform.system()
CONFIG_PATH = "config"

START_WAIT = 1
CONVERSATION_WAIT = 2
CONVERSATION_PERIOD_MS = 50

with open(CONFIG_PATH + "/settings.toml", "rb") as f:
    SETTINGS = tomllib.load(f)

with open(CONFIG_PATH + "/gauge_config.toml", "rb") as f:
    GAUGE_PARAMS = tomllib.load(f)

RESOURCE_PATH = "resources"
IMAGE_PATH = RESOURCE_PATH + "/images"
FONT_PATH = RESOURCE_PATH + "/fonts"
FONT_GROUP = SETTINGS["fonts"]["main"]

SCREEN_SIZE = [1920, 720]
SCREEN_REFRESH_RATE = 75 if SYSTEM == "Linux" else 60 if SYSTEM == "Darwin" else 144
DIAL_SIZE_MAJOR = 660
DIAL_SIZE_MINOR = 525
SYMBOL_SIZE = 63
SYMBOL_SIZE_SMALL = 50
SYMBOL_SIZE_EXTRA_SMALL = 28
BACKGROUND_COLOR = [0, 0, 0]
AWAKEN_SEQUENCE_DURATION = 1500
VISUAL_UPDATE_INTERVALS = {"coolant_temp": 0.75, "oil_temp": 0.75}

for i in can_ids.keys():
    if i not in VISUAL_UPDATE_INTERVALS:
        VISUAL_UPDATE_INTERVALS[i] = 1 / (SCREEN_REFRESH_RATE * 2)

C_TO_F_SCALE = 1.8
C_TO_F_OFFSET = 32
KPH_TO_MPH_SCALE = 0.62137119

GEAR_CALC_CONSTANT = (5280 * 12) / (pi * 60)
GEAR_RATIOS = [3.454, 1.947, 1.296, 0.972, 0.78, 0.666]
TIRE_DIAMETER = 26
FINAL_DRIVE_RATIO = 4.111

AVG_FUEL_SAMPLES = 10

SYMBOL_BLUE_COLOR = QColor(0, 0, 255)
SYMBOL_GREEN_COLOR = QColor(0, 230, 0)
SYMBOL_WHITE_COLOR = QColor(255, 255, 255)
SYMBOL_GRAY_COLOR = QColor(125, 125, 125)
SYMBOL_DARK_GRAY_COLOR = QColor(75, 75, 75)
SYMBOL_YELLOW_COLOR = QColor(255, 179, 0)
SYMBOL_RED_COLOR = QColor(255, 0, 0)
BLUELINE_COLOR = QColor(175, 150, 255)


#! potential problem with this function and threading
def calcGear(rpm: int, speed: int) -> str:
    ratio = (rpm * TIRE_DIAMETER) / (FINAL_DRIVE_RATIO * speed * KPH_TO_MPH_SCALE * GEAR_CALC_CONSTANT)

    for i, v in enumerate(GEAR_RATIOS, 1):
        if ratio >= v:
            return str(i)

    return 'N'


class MainWindow(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        major_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32
        minor_dial_angle_range = 2 * pi - major_dial_angle_range - pi / 4 * 2

        vertical_mirror = QTransform().rotate(180)

        turn_signal_offset_x = 70
        turn_signal_offset_y = 40
        turn_signal_sze = SYMBOL_SIZE
        bottom_symbol_y_offset = 10
        dial_size_major = QSize(DIAL_SIZE_MAJOR, DIAL_SIZE_MAJOR)
        dial_size_minor = QSize(DIAL_SIZE_MINOR, DIAL_SIZE_MINOR)

        major_dial_opacity = 0.3
        major_dial_width = 120

        minor_dial_opacity = 0.25
        minor_dial_width = 20

        dial_int_params_major = {
            "buffer_radius": 20,
            "num_radius": 54,
            "section_radius": 20,
            "minor_section_rad_offset": 3,
            "middle_section_rad_offset": 43,
            "major_section_rad_offset": 40,
            "angle_offset": pi,
            "dial_opacity": major_dial_opacity,
            "dial_width": major_dial_width,
            "angle_range": major_dial_angle_range,
            "size": dial_size_major
        }

        dial_int_params_minor = {
            "buffer_radius": 20,
            "num_radius": 50,
            "section_radius": 15,
            "minor_section_rad_offset": 3,
            "middle_section_rad_offset": 58,
            "major_section_rad_offset": 40,
            "no_font": True,
            "dial_opacity": minor_dial_opacity,
            "dial_width": minor_dial_width,
            "angle_range": minor_dial_angle_range,
            "size": dial_size_minor,
        }

        self.tachometer = Dial(self,
                               min_unit=GAUGE_PARAMS["tachometer"]["min"],
                               max_unit=GAUGE_PARAMS["tachometer"]["max"],
                               redline=GAUGE_PARAMS["tachometer"]["redline"],
                               mid_sections=GAUGE_PARAMS["tachometer"]["mid_sections"],
                               denomination=GAUGE_PARAMS["tachometer"]["denomination"],
                               visual_num_gap=GAUGE_PARAMS["tachometer"]["major_step"],
                               label_font=QFont(FONT_GROUP, 20),
                               **dial_int_params_major)
        self.tachometer.move(int(DIAL_SIZE_MAJOR / 4), int(SCREEN_SIZE[1] / 2 - DIAL_SIZE_MAJOR / 2))

        self.speedometer = Dial(self,
                                min_unit=GAUGE_PARAMS["speedometer"]["min"],
                                max_unit=GAUGE_PARAMS["speedometer"]["max"],
                                redline=GAUGE_PARAMS["speedometer"]["max"] + 1,
                                mid_sections=GAUGE_PARAMS["speedometer"]["mid_sections"],
                                visual_num_gap=GAUGE_PARAMS["speedometer"]["major_step"],
                                label_font=QFont(FONT_GROUP, 18),
                                **dial_int_params_major)
        self.speedometer.move(int(SCREEN_SIZE[0] - DIAL_SIZE_MAJOR - DIAL_SIZE_MAJOR / 4),
                              int(SCREEN_SIZE[1] / 2 - DIAL_SIZE_MAJOR / 2))

        self.coolant_temp_gauge = Dial(self,
                                       min_unit=GAUGE_PARAMS["coolant_temp"]["min"],
                                       max_unit=GAUGE_PARAMS["coolant_temp"]["max"],
                                       redline=GAUGE_PARAMS["coolant_temp"]["redline"],
                                       blueline=GAUGE_PARAMS["coolant_temp"]["blueline"],
                                       blueline_color=BLUELINE_COLOR,
                                       mid_sections=GAUGE_PARAMS["coolant_temp"]["mid_sections"],
                                       visual_num_gap=GAUGE_PARAMS["coolant_temp"]["visual_num_gap"],
                                       angle_offset=major_dial_angle_range - pi + pi / 2.5,
                                       **dial_int_params_minor)
        self.coolant_temp_gauge.move(self.tachometer.pos() + QPoint(0, DIAL_SIZE_MAJOR // 7))
        self.coolant_temp_gauge.frame.setStyleSheet("background:transparent")

        self.fuel_level_gauge = Dial(self,
                                     min_unit=GAUGE_PARAMS["fuel_level"]["min"],
                                     max_unit=GAUGE_PARAMS["fuel_level"]["max"],
                                     redline=GAUGE_PARAMS["fuel_level"]["redline"],
                                     mid_sections=GAUGE_PARAMS["fuel_level"]["mid_sections"],
                                     visual_num_gap=GAUGE_PARAMS["fuel_level"]["visual_num_gap"],
                                     angle_offset=major_dial_angle_range - pi + pi / 2.5,
                                     **dial_int_params_minor)
        self.fuel_level_gauge.move(self.speedometer.pos() + QPoint(0, DIAL_SIZE_MAJOR // 7))
        self.fuel_level_gauge.frame.setStyleSheet("background:transparent")

        self.traction_control_mode_image = Image(self, IMAGE_PATH + "/traction-mode-indicator-light.png",
                                                 SYMBOL_GREEN_COLOR)
        self.traction_control_mode_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.traction_control_mode_image.move(int(SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2),
                                              int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset))

        self.traction_control_off_image = Image(self, IMAGE_PATH + "/vehicle-dynamics-control-off-indicator-light.png",
                                                SYMBOL_YELLOW_COLOR)
        self.traction_control_off_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.traction_control_off_image.move(int(SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + SYMBOL_SIZE + 5),
                                             int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset))

        self.door_open_warning_image = Image(self, IMAGE_PATH + "/dooropen-warning-light.png", SYMBOL_RED_COLOR)
        self.door_open_warning_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.door_open_warning_image.move(int(SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + 5 * (SYMBOL_SIZE + 5)),
                                          int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset))

        self.seatbelt_driver_warning_image = Image(self, IMAGE_PATH + "/seatbelt-warning-light.png", SYMBOL_RED_COLOR)
        self.seatbelt_driver_warning_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.seatbelt_driver_warning_image.move(int(SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + 4 * (SYMBOL_SIZE + 5)),
                                                int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset))

        self.cruise_control_status_image = Image(self, IMAGE_PATH + "/cruise-control-indicator-light.png",
                                                 SYMBOL_GRAY_COLOR)
        self.cruise_control_status_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.cruise_control_status_image.move(
            self.speedometer.pos() +
            QPoint(DIAL_SIZE_MAJOR // 2 - SYMBOL_SIZE // 2 - 3, DIAL_SIZE_MAJOR // 2 -
                   self.cruise_control_status_image.size().height() // 2) - QPoint(0, int(SYMBOL_SIZE * 1.2)))

        self.coolant_temp_indicator_image_normal = Image(self,
                                                         IMAGE_PATH + "/coolant-temp-low-high-indicator-light.png",
                                                         SYMBOL_DARK_GRAY_COLOR)
        self.coolant_temp_indicator_image_normal.resize(SYMBOL_SIZE_EXTRA_SMALL, SYMBOL_SIZE_EXTRA_SMALL)
        self.coolant_temp_indicator_image_normal.move(
            self.coolant_temp_gauge.pos() +
            QPoint(int(DIAL_SIZE_MINOR / 3) - SYMBOL_SIZE_EXTRA_SMALL, DIAL_SIZE_MINOR - SYMBOL_SIZE_EXTRA_SMALL * 4))

        self.coolant_temp_indicator_image_cold = Image(self, IMAGE_PATH + "/coolant-temp-low-high-indicator-light.png",
                                                       SYMBOL_BLUE_COLOR)
        self.coolant_temp_indicator_image_cold.resize(self.coolant_temp_indicator_image_normal.size())
        self.coolant_temp_indicator_image_cold.move(self.coolant_temp_indicator_image_normal.pos())

        self.coolant_temp_indicator_image_hot = Image(self, IMAGE_PATH + "/coolant-temp-low-high-indicator-light.png",
                                                      SYMBOL_RED_COLOR)
        self.coolant_temp_indicator_image_hot.resize(self.coolant_temp_indicator_image_normal.size())
        self.coolant_temp_indicator_image_hot.move(self.coolant_temp_indicator_image_normal.pos())

        angle_mid = 30
        arc_width = 1.5
        size_scale = 4.25

        self.cruise_control_status_widget = QWidget(self)
        self.cruise_control_status_widget.setStyleSheet("background:transparent")
        self.cruise_control_status_widget.resize(
            QSize(int(DIAL_SIZE_MAJOR / size_scale), int(DIAL_SIZE_MAJOR / size_scale)))
        self.cruise_control_status_widget.move(self.speedometer.pos() +
                                               QPoint(DIAL_SIZE_MAJOR // 2, DIAL_SIZE_MAJOR // 2) -
                                               QPoint(self.cruise_control_status_widget.size().width() // 2,
                                                      self.cruise_control_status_widget.size().height() // 2))
        self.cruise_control_arc_left = Arc(self.cruise_control_status_widget, self.cruise_control_status_widget.size(),
                                           SYMBOL_GRAY_COLOR, arc_width)
        self.cruise_control_arc_left.pen.setCapStyle(Qt.RoundCap)
        self.cruise_control_arc_left.setArc(90 + angle_mid, 180 - angle_mid * 2)

        self.cruise_control_arc_right = Arc(self.cruise_control_status_widget, self.cruise_control_status_widget.size(),
                                            SYMBOL_GRAY_COLOR, arc_width)
        self.cruise_control_arc_right.pen.setCapStyle(Qt.RoundCap)
        self.cruise_control_arc_right.setArc(270 + angle_mid, 180 - angle_mid * 2)

        label_font = QFont(FONT_GROUP, 22)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, SYMBOL_GRAY_COLOR)

        self.cruise_control_speed_label = QLabel(self)
        self.cruise_control_speed_label.setStyleSheet("background:transparent")
        self.cruise_control_speed_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.cruise_control_speed_label.setFont(label_font)
        self.cruise_control_speed_label.setText("0")
        self.cruise_control_speed_label.setPalette(palette)
        self.cruise_control_speed_label.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.cruise_control_speed_label.move(
            self.speedometer.pos() +
            QPoint(DIAL_SIZE_MAJOR // 2 - self.cruise_control_speed_label.size().width() // 2, DIAL_SIZE_MAJOR // 2 -
                   self.cruise_control_speed_label.size().height() // 2) + QPoint(0, int(SYMBOL_SIZE * 1.05)))

        self.high_beam_image = Image(self, IMAGE_PATH + "/highbeam-indicator-light.png", SYMBOL_BLUE_COLOR)
        self.high_beam_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.high_beam_image.move(self.tachometer.pos() + QPoint(SYMBOL_SIZE * 2, 0))

        self.low_beam_image = Image(self, IMAGE_PATH + "/headlight-indicator-light.png", SYMBOL_GREEN_COLOR)
        self.low_beam_image.resize(int(SYMBOL_SIZE * 1.2), int(SYMBOL_SIZE * 1.2))
        self.low_beam_image.move(self.speedometer.pos() + QPoint(self.tachometer.size().width() - SYMBOL_SIZE * 3, 0))

        self.fog_light_image = Image(self, IMAGE_PATH + "/front-fog-indicator-light.png", SYMBOL_GREEN_COLOR)
        self.fog_light_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.fog_light_image.move(self.tachometer.pos() + QPoint(int(SYMBOL_SIZE / 1.3), SYMBOL_SIZE))

        self.brake_warning_image = Image(self, IMAGE_PATH + "/brake-warning-indicator-light-letters-only.png",
                                         SYMBOL_RED_COLOR)
        self.brake_warning_image.resize(int(SYMBOL_SIZE * 1.4), int(SYMBOL_SIZE * 1.2))
        self.brake_warning_image.move(self.speedometer.pos() +
                                      QPoint(DIAL_SIZE_MAJOR // 2 - self.brake_warning_image.size().width() //
                                             2, DIAL_SIZE_MAJOR // 2 - self.brake_warning_image.size().height() // 2) +
                                      QPoint(0, int(SYMBOL_SIZE * 3)))

        self.right_turn_signal_image_active = Image(self, IMAGE_PATH + "/turn-signal-arrow.png", SYMBOL_GREEN_COLOR)
        self.right_turn_signal_image_active.resize(turn_signal_sze, turn_signal_sze)
        self.right_turn_signal_image_active.move(self.speedometer.pos() +
                                                 QPoint(turn_signal_offset_x, turn_signal_offset_y))

        self.left_turn_signal_image_active = Image(self, IMAGE_PATH + "/turn-signal-arrow.png", SYMBOL_GREEN_COLOR,
                                                   vertical_mirror)
        self.left_turn_signal_image_active.resize(turn_signal_sze, turn_signal_sze)
        self.left_turn_signal_image_active.move(self.tachometer.pos() +
                                                QPoint(self.tachometer.size().width() - SYMBOL_SIZE, 0) +
                                                QPoint(-turn_signal_offset_x, turn_signal_offset_y))

        label_font = QFont(FONT_GROUP, 34)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))

        self.speed_label = QLabel(self)
        self.speed_label.setStyleSheet("background:transparent")
        self.speed_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.speed_label.setFont(label_font)
        self.speed_label.setPalette(palette)
        self.speed_label.setText("0")
        self.speed_label.resize(DIAL_SIZE_MAJOR, DIAL_SIZE_MAJOR)
        sl_size = self.speed_label.size()
        self.speed_label.move(
            int(SCREEN_SIZE[0] - DIAL_SIZE_MAJOR - DIAL_SIZE_MAJOR / 4 + DIAL_SIZE_MAJOR / 2 - sl_size.width() / 2),
            int(SCREEN_SIZE[1] / 2 - sl_size.height() / 2))

        self.gear_indicator_label = QLabel(self)
        self.gear_indicator_label.setStyleSheet("background:transparent")
        self.gear_indicator_label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
        self.gear_indicator_label.setFont(label_font)
        self.gear_indicator_label.setPalette(palette)
        self.gear_indicator_label.setText("N")
        self.gear_indicator_label.resize(DIAL_SIZE_MAJOR, DIAL_SIZE_MAJOR)
        gl_size = self.speed_label.size()
        self.gear_indicator_label.move(int(DIAL_SIZE_MAJOR / 4 + DIAL_SIZE_MAJOR / 2 - gl_size.width() / 2),
                                       int(SCREEN_SIZE[1] / 2 - gl_size.height() / 2))


class Application(QApplication):

    awakened = pyqtSignal()
    init_wait = pyqtSignal()

    def __init__(self) -> None:
        super().__init__([])

        self.setOverrideCursor(QCursor(Qt.BlankCursor))
        primary_container = MainWindow()
        primary_container.setFixedSize(*SCREEN_SIZE)
        primary_container.setStyleSheet(
            f"background-color: rgb({BACKGROUND_COLOR[0]}, {BACKGROUND_COLOR[1]}, {BACKGROUND_COLOR[2]})")

        self.start_time = time()
        self.primary_container = primary_container
        self.update_funcs = {}
        self.cluster_vars = {}
        self.cluster_vars_update_ts = {i: time() for i in VISUAL_UPDATE_INTERVALS.keys()}
        self.average_fuel_table = [0 for _ in range(AVG_FUEL_SAMPLES)]

        angle_mid = 30
        duration = 500

        start_left_start = 180
        end_left_start = 180 - 90 + angle_mid
        start_left_end = 0
        end_left_end = 180 - angle_mid * 2

        start_right_start = 0
        end_right_start = 90 - angle_mid
        start_right_end = 0
        end_right_end = -180 + angle_mid * 2

        self.cruise_dial_left_animation_start = property_animation(self, self.primary_container.cruise_control_arc_left,
                                                                   "arc_start", start_left_start, end_left_start,
                                                                   duration)
        self.cruise_dial_left_animation_end = property_animation(self, self.primary_container.cruise_control_arc_left,
                                                                 "arc_end", start_left_end, end_left_end, duration)
        self.cruise_dial_right_animation_start = property_animation(self,
                                                                    self.primary_container.cruise_control_arc_right,
                                                                    "arc_start", start_right_start, end_right_start,
                                                                    duration)
        self.cruise_dial_right_animation_end = property_animation(self, self.primary_container.cruise_control_arc_right,
                                                                  "arc_end", start_right_end, end_right_end, duration)
        self.cruise_dial_left_animation_start_close = property_animation(self,
                                                                         primary_container.cruise_control_arc_left,
                                                                         "arc_start", end_left_start, start_left_start,
                                                                         duration)
        self.cruise_dial_left_animation_end_close = property_animation(self,
                                                                       self.primary_container.cruise_control_arc_left,
                                                                       "arc_end", end_left_end, start_left_end,
                                                                       duration)
        self.cruise_dial_right_animation_start_close = property_animation(
            self, self.primary_container.cruise_control_arc_right, "arc_start", end_right_start, start_right_start,
            duration)
        self.cruise_dial_right_animation_end_close = property_animation(self,
                                                                        self.primary_container.cruise_control_arc_right,
                                                                        "arc_end", end_right_end, start_right_end,
                                                                        duration)

        self.cruise_control_set_last = 1
        self.init_wait.connect(self.awakenClusters)
        delay(self, self.init_wait.emit, START_WAIT)

    @pyqtSlot()
    def awakenClusters(self) -> None:
        #todo: change to use QPropertyAnimation
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

    @pyqtSlot(bool)
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

    @pyqtSlot()
    def updateGearIndicator(self) -> None:
        speed = self.cluster_vars.get('vehicle_speed', 1)
        rpm = self.cluster_vars.get('rpm', 0)
        neutral = self.cluster_vars.get('neutral_switch', 0)
        reverse = self.cluster_vars.get('reverse_switch', 0)
        clutch_switch = self.cluster_vars.get("clutch_switch", 0)

        if reverse:
            gear = 'R'
        elif neutral:
            gear = 'N'
        else:
            if clutch_switch or speed == 0:
                gear = ''
            else:
                gear = calcGear(rpm, speed * KPH_TO_MPH_SCALE)

        self.primary_container.gear_indicator_label.setText(gear)

    @pyqtSlot(tuple)
    def updateVar(self, data: tuple) -> None:
        t = time()
        var, val = data
        self.cluster_vars[var] = val

        if t - self.cluster_vars_update_ts[var] <= VISUAL_UPDATE_INTERVALS[var]:
            return

        #? change to table lookup instead of long if statement. Unsure how speed will be affected on the RPi or readability
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
        elif var == "fuel_level":
            self.average_fuel_table.append(val)
            self.average_fuel_table.pop(0)

            avg = reduce(lambda x, y: x + y, self.average_fuel_table) / AVG_FUEL_SAMPLES
            self.primary_container.fuel_level_gauge.setUnit(avg)
        elif var == "coolant_temp":
            converted_val = val * C_TO_F_SCALE + C_TO_F_OFFSET
            self.primary_container.coolant_temp_gauge.setUnit(converted_val)
            if converted_val <= GAUGE_PARAMS["coolant_temp"]["blueline"]:
                self.primary_container.coolant_temp_indicator_image_normal.setVisible(False)
                self.primary_container.coolant_temp_indicator_image_cold.setVisible(True)
                self.primary_container.coolant_temp_indicator_image_hot.setVisible(False)
            elif converted_val >= GAUGE_PARAMS["coolant_temp"]["redline"]:
                self.primary_container.coolant_temp_indicator_image_normal.setVisible(False)
                self.primary_container.coolant_temp_indicator_image_cold.setVisible(False)
                self.primary_container.coolant_temp_indicator_image_hot.setVisible(True)
            else:
                self.primary_container.coolant_temp_indicator_image_normal.setVisible(True)
                self.primary_container.coolant_temp_indicator_image_cold.setVisible(False)
                self.primary_container.coolant_temp_indicator_image_hot.setVisible(False)
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
            # todo: make indicator blink the same way the factory indicator blinks
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
                self.primary_container.cruise_control_speed_label.setVisible(False)
        elif var == "cruise_control_set":
            if val != self.cruise_control_set_last:
                self.cruise_control_set_last = val
                if val and self.cluster_vars.get("cruise_control_status", 0):
                    self.animateCruiseControl()
                else:
                    self.animateCruiseControl(False)

        self.cluster_vars[var] = val
        self.cluster_vars_update_ts[var] = t


if __name__ == "__main__":
    app = Application()
    screens = app.screens()
    using_canbus = False

    for font_file in listdir(FONT_PATH + "/Montserrat/static"):
        if path.splitext(font_file)[0] in SETTINGS["fonts"].values():
            QFontDatabase.addApplicationFont(f"{FONT_PATH}/Montserrat/static/{font_file}")

    if SYSTEM == "Linux":
        screen = screens[0]
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()

        using_canbus = "nocan" not in sys.argv

        try:
            shutdown_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True)
            setup_can = subprocess.run(
                ["sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can", "bitrate", "500000"], check=True)

            bus = can.interface.Bus(channel='can0', bustype='socketcan', bitrate=500000)
        except:
            print("Could not find PiCan device. Switching to emulation.")
            using_canbus = False
    else:
        if len(screens) > 1:
            screen = screens[1]
            app.primary_container.move(screen.geometry().topLeft())
            app.primary_container.showFullScreen()

    if not using_canbus:
        import test_module

        bus_virtual_car = can.interface.Bus(channel="test", bustype="virtual")
        bus = can.interface.Bus(channel='test', bustype='virtual')

        @pyqtSlot()
        def emulate_car():
            bus_virtual_car.send(test_module.provide_random_message())

        @pyqtSlot()
        def emulate_conversation(msg: can.Message):
            response = test_module.provide_response_message(msg)
            bus_virtual_car.send(response)

        @pyqtSlot()
        def run():
            can.Notifier(bus_virtual_car, [emulate_conversation])
            timed_func(app, emulate_car, 1)

        app.awakened.connect(run)

    can_app = CanApplication(app, bus)
    can_app.updated.connect(app.updateVar)

    response_debounce = False
    last_response_time = time()

    @pyqtSlot()
    def run_conversation():
        global response_debounce, last_response_time
        if response_debounce:
            response_debounce = False
            message = can.Message(is_extended_id=False,
                                  arbitration_id=conversation_ids["send_id"],
                                  data=[0x02, 0x01, 0x0D, 0, 0, 0, 0, 0])
            can_app.send(message)
        elif time() - last_response_time >= CONVERSATION_PERIOD_MS / 3:
            print("[WARNING]: No response from ECU during conversation")
            response_debounce = True
            last_response_time = time()

    @pyqtSlot()
    def run():
        can.Notifier(bus, [can_app.parse_data])

        @pyqtSlot()
        def response_received():
            global response_debounce
            response_debounce = True

        can_app.response_recieved.connect(response_received)

        @pyqtSlot()
        def attemp_init_conversation():
            if not response_debounce:
                timed_func(app, run_conversation, CONVERSATION_PERIOD_MS)
            else:
                print("ECU Conversation busy; eavesdropping only.")

        delay(app, attemp_init_conversation, CONVERSATION_WAIT)

    app.awakened.connect(run)
    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
