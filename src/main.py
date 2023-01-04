import platform
import subprocess
import sys
from typing import Any
import tomlkit
import can
from os import listdir, path
from math import pi
from time import time
from functools import reduce
from qutil import Image, Arc, delay, timed_func, property_animation
from PyQt5.QtCore import Qt, pyqtSignal, QSize, pyqtSlot, QPoint, QAbstractAnimation
from PyQt5.QtGui import (
    QColor,
    QCursor,
    QFontDatabase,
    QFont,
    QPalette,
    QTransform,
    QCloseEvent,
)
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QWidget
from can_handle import CanApplication, can_ids
from dial import Dial

SYSTEM = platform.system()
CONFIG_PATH = "config"


def reload_settings(init: bool = False) -> None:
    global settings_toml, SETTINGS

    # todo: implement external settings file so that settings don't get reset with every software update
    # if not init:
    #     with open(CONFIG_PATH + "/settings.toml", "wb") as f:
    #         tomlkit.dump(settings_toml, f)

    with open(CONFIG_PATH + "/settings.toml", "rb") as f:
        settings_toml = tomlkit.load(f)
        SETTINGS = settings_toml.unwrap()


reload_settings(True)

with open(CONFIG_PATH + "/gauge_config.toml", "rb") as f:
    gauge_params_toml = tomlkit.load(f)
    GAUGE_PARAMS = gauge_params_toml.unwrap()

START_WAIT = 1
CONVERSATION_WAIT = 2
CONVERSATION_PERIOD_MS = 50

RESOURCE_PATH = "resources"
IMAGE_PATH = RESOURCE_PATH + "/images"
FONT_PATH = RESOURCE_PATH + "/fonts"
FONT_GROUP = SETTINGS["fonts"]["main"]

SCREEN_SIZE = [1920, 720]
SCREEN_REFRESH_RATE = 75
DIAL_SIZE_MAJOR = 660
DIAL_SIZE_MINOR = 525
SYMBOL_SIZE = 63
SYMBOL_BUFFER = 5
SYMBOL_SIZE_SMALL = 50
SYMBOL_SIZE_EXTRA_SMALL = 28
BACKGROUND_COLOR = QColor(0, 0, 0)
AWAKEN_SEQUENCE_DURATION = 1750
AWAKEN_SEQUENCE_DURATION_STALL = 250
VISUAL_UPDATE_INTERVALS = {}

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

AVG_FUEL_SAMPLES = 50
LOW_FUEL_THRESHHOLD = 15

SYMBOL_BLUE_COLOR = QColor(0, 0, 255)
SYMBOL_GREEN_COLOR = QColor(0, 230, 0)
SYMBOL_WHITE_COLOR = QColor(255, 255, 255)
SYMBOL_GRAY_COLOR = QColor(125, 125, 125)
SYMBOL_DARK_GRAY_COLOR = QColor(75, 75, 75)
SYMBOL_YELLOW_COLOR = QColor(255, 179, 0)
SYMBOL_RED_COLOR = QColor(255, 0, 0)
BLUELINE_COLOR = QColor(175, 150, 255)


class MainWindow(QMainWindow):

    closed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        background_palette = QPalette()
        background_palette.setColor(QPalette.ColorRole.Background, BACKGROUND_COLOR)
        self.setPalette(background_palette)

        major_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32

        vertical_mirror = QTransform().rotate(180)

        turn_signal_offset_x = 70
        turn_signal_offset_y = 40
        turn_signal_sze = SYMBOL_SIZE
        bottom_symbol_y_offset = 10
        dial_size_major = QSize(DIAL_SIZE_MAJOR, DIAL_SIZE_MAJOR)
        dial_size_minor = QSize(DIAL_SIZE_MINOR, DIAL_SIZE_MINOR)

        all_dial_params = {
            "blueline_color": BLUELINE_COLOR,
            "gradient": True,
            "border_width": 2,
            "line_width": 1.5,
        }

        dial_params_major = {
            "buffer_radius": 22,
            "num_radius": 54,
            "section_radius": 20,
            "minor_section_rad_offset": 5,
            "middle_section_rad_offset": 43,
            "major_section_rad_offset": 40,
            "angle_offset": pi,
            "dial_opacity": 0.5,
            "dial_width": 140,
            "angle_range": major_dial_angle_range,
            "size": dial_size_major,
        }

        dial_params_minor = {
            "buffer_radius": 22,
            "num_radius": 50,
            "section_radius": 15,
            "minor_section_rad_offset": 5,
            "middle_section_rad_offset": 58,
            "major_section_rad_offset": 40,
            "no_font": True,
            "dial_opacity": 0.5,
            "dial_width": 35,
            "angle_range": 2 * pi - major_dial_angle_range - pi / 4 * 2,
            "size": dial_size_minor,
            "angle_offset": major_dial_angle_range - pi + pi / 2.5,
        }

        self.tachometer = Dial(
            self,
            label_font=QFont(FONT_GROUP, 20),
            **GAUGE_PARAMS["tachometer"],
            **dial_params_major,
            **all_dial_params,
        )
        self.tachometer.move(
            int(DIAL_SIZE_MAJOR / 4), int(SCREEN_SIZE[1] / 2 - DIAL_SIZE_MAJOR / 2)
        )

        self.speedometer = Dial(
            self,
            label_font=QFont(FONT_GROUP, 18),
            redline=GAUGE_PARAMS["speedometer"]["max_unit"] + 1,
            **GAUGE_PARAMS["speedometer"],
            **dial_params_major,
            **all_dial_params,
        )
        self.speedometer.move(
            int(SCREEN_SIZE[0] - DIAL_SIZE_MAJOR - DIAL_SIZE_MAJOR / 4),
            int(SCREEN_SIZE[1] / 2 - DIAL_SIZE_MAJOR / 2),
        )

        self.coolant_temp_gauge = Dial(
            self, **GAUGE_PARAMS["coolant_temp"], **dial_params_minor, **all_dial_params
        )
        self.coolant_temp_gauge.move(
            self.tachometer.pos() + QPoint(0, DIAL_SIZE_MAJOR // 7)
        )
        self.coolant_temp_gauge.frame.setStyleSheet("background:transparent")

        self.fuel_level_gauge = Dial(
            self, **GAUGE_PARAMS["fuel_level"], **dial_params_minor, **all_dial_params
        )
        self.fuel_level_gauge.move(
            self.speedometer.pos() + QPoint(0, DIAL_SIZE_MAJOR // 7)
        )
        self.fuel_level_gauge.frame.setStyleSheet("background:transparent")

        self.traction_control_mode_image = Image(
            self, IMAGE_PATH + "/traction-mode-indicator-light.png", SYMBOL_GREEN_COLOR
        )
        self.traction_control_mode_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.traction_control_mode_image.move(
            int(SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + 3 * (SYMBOL_SIZE + SYMBOL_BUFFER)),
            int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset),
        )

        self.check_engine_light_image = Image(
            self,
            IMAGE_PATH + "/check-engine-warning-linght-icon.png",
            SYMBOL_YELLOW_COLOR,
        )
        self.check_engine_light_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.check_engine_light_image.move(
            int(
                SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 - 5 * (SYMBOL_SIZE + SYMBOL_BUFFER)
            ),
            int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset),
        )

        self.traction_control_off_image = Image(
            self,
            IMAGE_PATH + "/vehicle-dynamics-control-off-indicator-light.png",
            SYMBOL_YELLOW_COLOR,
        )
        self.traction_control_off_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.traction_control_off_image.move(
            int(SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + 4 * (SYMBOL_SIZE + SYMBOL_BUFFER)),
            int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset),
        )

        self.door_open_warning_image = Image(
            self, IMAGE_PATH + "/dooropen-warning-light.png", SYMBOL_RED_COLOR
        )
        self.door_open_warning_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.door_open_warning_image.move(
            int(
                SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + 6 * (SYMBOL_SIZE + SYMBOL_BUFFER)
            ),
            int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset),
        )

        self.seatbelt_driver_warning_image = Image(
            self, IMAGE_PATH + "/seatbelt-warning-light.png", SYMBOL_RED_COLOR
        )
        self.seatbelt_driver_warning_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.seatbelt_driver_warning_image.move(
            int(
                SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + 5 * (SYMBOL_SIZE + SYMBOL_BUFFER)
            ),
            int(SCREEN_SIZE[1] - SYMBOL_SIZE - bottom_symbol_y_offset),
        )

        self.cruise_control_status_image = Image(
            self, IMAGE_PATH + "/cruise-control-indicator-light.png", SYMBOL_GRAY_COLOR
        )
        self.cruise_control_status_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.cruise_control_status_image.move(
            self.speedometer.pos()
            + QPoint(
                DIAL_SIZE_MAJOR // 2 - SYMBOL_SIZE // 2 - 3,
                DIAL_SIZE_MAJOR // 2 - self.cruise_control_status_image.height() // 2,
            )
            - QPoint(0, int(SYMBOL_SIZE * 1.2))
        )

        self.coolant_temp_indicator_image_normal = Image(
            self,
            IMAGE_PATH + "/coolant-temp-low-high-indicator-light.png",
            SYMBOL_GRAY_COLOR,
        )
        self.coolant_temp_indicator_image_normal.resize(
            SYMBOL_SIZE_EXTRA_SMALL, SYMBOL_SIZE_EXTRA_SMALL
        )
        self.coolant_temp_indicator_image_normal.move(
            self.coolant_temp_gauge.pos()
            + QPoint(
                int(DIAL_SIZE_MINOR / 3) - SYMBOL_SIZE_EXTRA_SMALL,
                int(DIAL_SIZE_MINOR - SYMBOL_SIZE_EXTRA_SMALL * 4.2),
            )
        )

        self.coolant_temp_indicator_image_cold = Image(
            self,
            IMAGE_PATH + "/coolant-temp-low-high-indicator-light.png",
            SYMBOL_BLUE_COLOR,
        )
        self.coolant_temp_indicator_image_cold.resize(
            self.coolant_temp_indicator_image_normal.size()
        )
        self.coolant_temp_indicator_image_cold.move(
            self.coolant_temp_indicator_image_normal.pos()
        )

        self.coolant_temp_indicator_image_hot = Image(
            self,
            IMAGE_PATH + "/coolant-temp-low-high-indicator-light.png",
            SYMBOL_RED_COLOR,
        )
        self.coolant_temp_indicator_image_hot.resize(
            self.coolant_temp_indicator_image_normal.size()
        )
        self.coolant_temp_indicator_image_hot.move(
            self.coolant_temp_indicator_image_normal.pos()
        )

        self.fuel_image = Image(
            self, IMAGE_PATH + "/lowfuel-warning-light.png", SYMBOL_GRAY_COLOR
        )
        self.fuel_image.resize(SYMBOL_SIZE_EXTRA_SMALL, SYMBOL_SIZE_EXTRA_SMALL)
        self.fuel_image.move(
            self.fuel_level_gauge.pos()
            + QPoint(
                int(DIAL_SIZE_MINOR / 3) - SYMBOL_SIZE_EXTRA_SMALL,
                int(DIAL_SIZE_MINOR - SYMBOL_SIZE_EXTRA_SMALL * 4.2),
            )
        )

        self.low_fuel_warning_image = Image(
            self, IMAGE_PATH + "/lowfuel-warning-light.png", SYMBOL_YELLOW_COLOR
        )
        self.low_fuel_warning_image.resize(
            SYMBOL_SIZE_EXTRA_SMALL, SYMBOL_SIZE_EXTRA_SMALL
        )
        self.low_fuel_warning_image.move(
            self.fuel_level_gauge.pos()
            + QPoint(
                int(DIAL_SIZE_MINOR / 3) - SYMBOL_SIZE_EXTRA_SMALL,
                int(DIAL_SIZE_MINOR - SYMBOL_SIZE_EXTRA_SMALL * 4.2),
            )
        )

        angle_mid = 30
        arc_width = 1.5
        size_scale = 4.25

        self.cruise_control_status_widget = QWidget(self)
        self.cruise_control_status_widget.setStyleSheet("background:transparent")
        self.cruise_control_status_widget.resize(
            QSize(int(DIAL_SIZE_MAJOR / size_scale), int(DIAL_SIZE_MAJOR / size_scale))
        )
        self.cruise_control_status_widget.move(
            self.speedometer.pos()
            + QPoint(DIAL_SIZE_MAJOR // 2, DIAL_SIZE_MAJOR // 2)
            - QPoint(
                self.cruise_control_status_widget.width() // 2,
                self.cruise_control_status_widget.height() // 2,
            )
        )
        self.cruise_control_arc_left = Arc(
            self.cruise_control_status_widget,
            self.cruise_control_status_widget.size(),
            SYMBOL_GRAY_COLOR,
            arc_width,
        )
        self.cruise_control_arc_left.pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.cruise_control_arc_left.set_arc(90 + angle_mid, 180 - angle_mid * 2)

        self.cruise_control_arc_right = Arc(
            self.cruise_control_status_widget,
            self.cruise_control_status_widget.size(),
            SYMBOL_GRAY_COLOR,
            arc_width,
        )
        self.cruise_control_arc_right.pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        self.cruise_control_arc_right.set_arc(270 + angle_mid, 180 - angle_mid * 2)

        label_font = QFont(FONT_GROUP, 22)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, SYMBOL_GRAY_COLOR)

        # todo: add arrow to image instead
        self.fuel_cap_indicator_arrow = QLabel(self)
        self.fuel_cap_indicator_arrow.setStyleSheet("background:transparent")
        self.fuel_cap_indicator_arrow.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.fuel_cap_indicator_arrow.setFont(QFont(FONT_GROUP, 10))
        self.fuel_cap_indicator_arrow.setText(">")
        self.fuel_cap_indicator_arrow.setPalette(palette)
        self.fuel_cap_indicator_arrow.adjustSize()
        self.fuel_cap_indicator_arrow.move(
            self.fuel_image.pos()
            + QPoint(
                self.fuel_image.width() + self.fuel_cap_indicator_arrow.width() - 10,
                self.fuel_cap_indicator_arrow.height() // 2,
            )
        )

        self.cruise_control_speed_label = QLabel(self)
        self.cruise_control_speed_label.setStyleSheet("background:transparent")
        self.cruise_control_speed_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.cruise_control_speed_label.setFont(label_font)
        self.cruise_control_speed_label.setText("0")
        self.cruise_control_speed_label.setPalette(palette)
        self.cruise_control_speed_label.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.cruise_control_speed_label.move(
            self.speedometer.pos()
            + QPoint(
                DIAL_SIZE_MAJOR // 2 - self.cruise_control_speed_label.width() // 2,
                DIAL_SIZE_MAJOR // 2 - self.cruise_control_speed_label.height() // 2,
            )
            + QPoint(0, int(SYMBOL_SIZE * 1.05))
        )

        self.high_beam_image = Image(
            self, IMAGE_PATH + "/highbeam-indicator-light.png", SYMBOL_BLUE_COLOR
        )
        self.high_beam_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.high_beam_image.move(self.tachometer.pos() + QPoint(SYMBOL_SIZE * 2, 0))

        self.low_beam_image = Image(
            self, IMAGE_PATH + "/headlight-indicator-light.png", SYMBOL_GREEN_COLOR
        )
        self.low_beam_image.resize(int(SYMBOL_SIZE * 1.2), int(SYMBOL_SIZE * 1.2))
        self.low_beam_image.move(
            self.speedometer.pos()
            + QPoint(self.tachometer.width() - SYMBOL_SIZE * 3, 0)
        )

        self.fog_light_image = Image(
            self, IMAGE_PATH + "/front-fog-indicator-light.png", SYMBOL_GREEN_COLOR
        )
        self.fog_light_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.fog_light_image.move(
            self.tachometer.pos() + QPoint(int(SYMBOL_SIZE / 1.3), SYMBOL_SIZE)
        )

        self.parking_brake_active_image = Image(
            self,
            IMAGE_PATH + "/brake-warning-indicator-light-letters-only.png",
            SYMBOL_RED_COLOR,
        )
        self.parking_brake_active_image.resize(int(SYMBOL_SIZE * 1.4), int(SYMBOL_SIZE * 1.2))
        self.parking_brake_active_image.move(
            self.speedometer.pos()
            + QPoint(
                DIAL_SIZE_MAJOR // 2 - self.parking_brake_active_image.width() // 2,
                DIAL_SIZE_MAJOR // 2 - self.parking_brake_active_image.height() // 2,
            )
            + QPoint(0, int(SYMBOL_SIZE * 3))
        )

        self.right_turn_signal_image_active = Image(
            self, IMAGE_PATH + "/turn-signal-arrow.png", SYMBOL_GREEN_COLOR
        )
        self.right_turn_signal_image_active.resize(turn_signal_sze, turn_signal_sze)
        self.right_turn_signal_image_active.move(
            self.speedometer.pos() + QPoint(turn_signal_offset_x, turn_signal_offset_y)
        )

        self.left_turn_signal_image_active = Image(
            self,
            IMAGE_PATH + "/turn-signal-arrow.png",
            SYMBOL_GREEN_COLOR,
            vertical_mirror,
        )
        self.left_turn_signal_image_active.resize(turn_signal_sze, turn_signal_sze)
        self.left_turn_signal_image_active.move(
            self.tachometer.pos()
            + QPoint(self.tachometer.width() - SYMBOL_SIZE, 0)
            + QPoint(-turn_signal_offset_x, turn_signal_offset_y)
        )

        label_font = QFont(FONT_GROUP, 34)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))

        self.speed_label = QLabel(self)
        self.speed_label.setStyleSheet("background:transparent")
        self.speed_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.speed_label.setFont(label_font)
        self.speed_label.setPalette(palette)
        self.speed_label.setText("0")
        self.speed_label.resize(DIAL_SIZE_MAJOR, DIAL_SIZE_MAJOR)
        self.speed_label.move(
            int(
                SCREEN_SIZE[0]
                - DIAL_SIZE_MAJOR
                - DIAL_SIZE_MAJOR / 4
                + DIAL_SIZE_MAJOR / 2
                - self.speed_label.width() / 2
            ),
            int(SCREEN_SIZE[1] / 2 - self.speed_label.height() / 2),
        )

        self.gear_indicator_label = QLabel(self)
        self.gear_indicator_label.setStyleSheet("background:transparent")
        self.gear_indicator_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.gear_indicator_label.setFont(label_font)
        self.gear_indicator_label.setPalette(palette)
        self.gear_indicator_label.setText("N")
        self.gear_indicator_label.resize(DIAL_SIZE_MAJOR, DIAL_SIZE_MAJOR)
        self.gear_indicator_label.move(
            int(
                DIAL_SIZE_MAJOR / 4
                + DIAL_SIZE_MAJOR / 2
                - self.gear_indicator_label.width() / 2
            ),
            int(SCREEN_SIZE[1] / 2 - self.gear_indicator_label.height() / 2),
        )

        label_font = QFont(FONT_GROUP, 23)

        self.odometer_label = QLabel(self)
        self.odometer_label.setStyleSheet("background:transparent")
        self.odometer_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
        )
        self.odometer_label.setFont(label_font)
        self.odometer_label.setPalette(palette)
        self.odometer_label.setText("000000")
        self.odometer_label.resize(SCREEN_SIZE[0], SYMBOL_SIZE)
        self.odometer_label.move(
            int(
                SCREEN_SIZE[0] / 2 - self.odometer_label.width() / 2
            ),
            int(SCREEN_SIZE[1] - self.odometer_label.height() - bottom_symbol_y_offset),
        )

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.closed.emit()
        return super().closeEvent(a0)


class Application(QApplication):

    awakened = pyqtSignal()
    init_wait = pyqtSignal()

    def __init__(self) -> None:
        super().__init__([])

        for font_file in listdir(FONT_PATH + "/Montserrat/static"):
            if path.splitext(font_file)[0] in SETTINGS["fonts"].values():
                QFontDatabase.addApplicationFont(f"{FONT_PATH}/Montserrat/static/{font_file}")

        self.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))
        primary_container = MainWindow()
        primary_container.setFixedSize(*SCREEN_SIZE)

        self.start_time = time()
        self.primary_container = primary_container
        self.update_funcs = {}
        self.cluster_vars = {}
        self.cluster_vars_update_ts = {
            i: time() for i in VISUAL_UPDATE_INTERVALS.keys()
        }
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

        self.cruise_dial_left_animation_start = property_animation(
            self,
            self.primary_container.cruise_control_arc_left,
            "arc_start",
            start_left_start,
            end_left_start,
            duration,
        )
        self.cruise_dial_left_animation_end = property_animation(
            self,
            self.primary_container.cruise_control_arc_left,
            "arc_end",
            start_left_end,
            end_left_end,
            duration,
        )
        self.cruise_dial_right_animation_start = property_animation(
            self,
            self.primary_container.cruise_control_arc_right,
            "arc_start",
            start_right_start,
            end_right_start,
            duration,
        )
        self.cruise_dial_right_animation_end = property_animation(
            self,
            self.primary_container.cruise_control_arc_right,
            "arc_end",
            start_right_end,
            end_right_end,
            duration,
        )
        self.cruise_dial_left_animation_start_close = property_animation(
            self,
            primary_container.cruise_control_arc_left,
            "arc_start",
            end_left_start,
            start_left_start,
            duration,
        )
        self.cruise_dial_left_animation_end_close = property_animation(
            self,
            self.primary_container.cruise_control_arc_left,
            "arc_end",
            end_left_end,
            start_left_end,
            duration,
        )
        self.cruise_dial_right_animation_start_close = property_animation(
            self,
            self.primary_container.cruise_control_arc_right,
            "arc_start",
            end_right_start,
            start_right_start,
            duration,
        )
        self.cruise_dial_right_animation_end_close = property_animation(
            self,
            self.primary_container.cruise_control_arc_right,
            "arc_end",
            end_right_end,
            start_right_end,
            duration,
        )

        self.cruise_control_set_last = 1
        self.init_wait.connect(self.awaken_clusters)
        delay(self, self.init_wait.emit, START_WAIT)

    @pyqtSlot()
    def awaken_clusters(self) -> None:
        duration = int((AWAKEN_SEQUENCE_DURATION - AWAKEN_SEQUENCE_DURATION_STALL) / 2)

        def start() -> None:
            property_animation(
                self,
                self.primary_container.tachometer,
                "dial_unit",
                GAUGE_PARAMS["tachometer"]["min_unit"],
                GAUGE_PARAMS["tachometer"]["max_unit"],
                duration,
            ).start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            property_animation(
                self,
                self.primary_container.speedometer,
                "dial_unit",
                GAUGE_PARAMS["speedometer"]["min_unit"],
                GAUGE_PARAMS["speedometer"]["max_unit"],
                duration,
            ).start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        def end() -> None:
            property_animation(
                self,
                self.primary_container.tachometer,
                "dial_unit",
                GAUGE_PARAMS["tachometer"]["max_unit"],
                GAUGE_PARAMS["tachometer"]["min_unit"],
                duration,
            ).start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            property_animation(
                self,
                self.primary_container.speedometer,
                "dial_unit",
                GAUGE_PARAMS["speedometer"]["max_unit"],
                GAUGE_PARAMS["speedometer"]["min_unit"],
                duration,
            ).start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        start()
        delay(self, end, (duration + AWAKEN_SEQUENCE_DURATION_STALL / 2) / 1000)
        delay(self, self.awakened.emit, AWAKEN_SEQUENCE_DURATION / 1000)

    @pyqtSlot(bool)
    def animate_cruise_control(self, opening: bool = True) -> None:
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
    def update_gear_indicator(self) -> None:
        speed = self.cluster_vars.get("vehicle_speed", 1)
        rpm = self.cluster_vars.get("rpm", 0)
        gear = self.cluster_vars.get("gear", 0)
        reverse = self.cluster_vars.get("reverse_switch", 0)
        clutch_switch = self.cluster_vars.get("clutch_switch", 0)

        if reverse:
            gear = "R"
        elif clutch_switch:
            gear = ""
        elif gear == 0:
            gear = "N"
        else:
            gear = str(gear)

        self.primary_container.gear_indicator_label.setText(gear)

    @pyqtSlot(tuple)
    def update_var(self, data: tuple) -> None:
        t = time()
        var, val = data
        self.cluster_vars[var] = val

        if t - self.cluster_vars_update_ts[var] <= VISUAL_UPDATE_INTERVALS[var]:
            return

        if var == "vehicle_speed":
            val *= KPH_TO_MPH_SCALE
            self.primary_container.speed_label.setText(f"{val:.0f}")
            self.primary_container.speedometer.dial_unit = val
        elif var == "rpm":
            self.update_gear_indicator()
            self.primary_container.tachometer.dial_unit = val
        elif var == "turn_signals":
            self.primary_container.left_turn_signal_image_active.setVisible(val[0])
            self.primary_container.right_turn_signal_image_active.setVisible(val[1])
        elif var == "fuel_level":
            self.average_fuel_table.append(val)
            self.average_fuel_table.pop(0)

            avg = reduce(lambda x, y: x + y, self.average_fuel_table) / AVG_FUEL_SAMPLES

            self.primary_container.fuel_level_gauge.dial_unit = avg
            self.primary_container.low_fuel_warning_image.setVisible(
                avg <= LOW_FUEL_THRESHHOLD
            )
        elif var == "coolant_temp":
            converted_val = val * C_TO_F_SCALE + C_TO_F_OFFSET
            self.primary_container.coolant_temp_gauge.dial_unit = converted_val
            if converted_val <= GAUGE_PARAMS["coolant_temp"]["blueline"]:
                self.primary_container.coolant_temp_indicator_image_normal.setVisible(
                    False
                )
                self.primary_container.coolant_temp_indicator_image_cold.setVisible(
                    True
                )
                self.primary_container.coolant_temp_indicator_image_hot.setVisible(
                    False
                )
            elif converted_val >= GAUGE_PARAMS["coolant_temp"]["redline"]:
                self.primary_container.coolant_temp_indicator_image_normal.setVisible(
                    False
                )
                self.primary_container.coolant_temp_indicator_image_cold.setVisible(
                    False
                )
                self.primary_container.coolant_temp_indicator_image_hot.setVisible(True)
            else:
                self.primary_container.coolant_temp_indicator_image_normal.setVisible(
                    True
                )
                self.primary_container.coolant_temp_indicator_image_cold.setVisible(
                    False
                )
                self.primary_container.coolant_temp_indicator_image_hot.setVisible(
                    False
                )
        elif var == "handbrake_switch":
            self.primary_container.brake_warning_image.setVisible(val)
        elif var in ["reverse_switch", "clutch_switch", "gear"]:
            self.update_gear_indicator()
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
            self.primary_container.door_open_warning_image.setVisible("1" in val)
        elif var == "headlights":
            self.primary_container.low_beam_image.setVisible(val[0] or (val[1] == 1))
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
                self.animate_cruise_control(
                    val and self.cluster_vars.get("cruise_control_status", 0)
                )
        elif var == "check_engine_light":
            self.primary_container.check_engine_light_image.setVisible(val)
        elif var == "odometer":
            self.primary_container.odometer_label.setText(f"{val}")

        self.cluster_vars[var] = val
        self.cluster_vars_update_ts[var] = t


if __name__ == "__main__":
    app = Application()
    screens = app.screens()
    USING_CANBUS = False

    if SYSTEM == "Linux":
        screen = screens[0]
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
        app.primary_container.setFocus()

        USING_CANBUS = "nocan" not in sys.argv

        try:
            shutdown_can = subprocess.run(
                ["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True
            )
            setup_can = subprocess.run(
                [
                    "sudo",
                    "/sbin/ip",
                    "link",
                    "set",
                    "can0",
                    "up",
                    "type",
                    "can",
                    "bitrate",
                    "500000",
                ],
                check=True,
            )

            bus = can.interface.Bus(channel="can0", bustype="socketcan", bitrate=500000)
        except (
            can.exceptions.CanInitializationError,
            can.exceptions.CanInterfaceNotImplementedError,
        ):
            print("Could not find PiCan device. Switching to emulation.")
            USING_CANBUS = False
    else:
        app.primary_container.show()
        if len(screens) > 1:
            screen = screens[1]
            app.primary_container.move(screen.geometry().topLeft())
            app.primary_container.showFullScreen()

    if not USING_CANBUS:
        import test_module

        bus_virtual_car = can.interface.Bus(channel="test", bustype="virtual")
        bus = can.interface.Bus(channel="test", bustype="virtual")

        TestController = test_module.TestController(bus_virtual_car)
        TestController.move(
            app.primary_container.pos() - QPoint(test_module.WINDOW_SIZE[0], 0)
        )
        app.setOverrideCursor(Qt.CursorShape.ArrowCursor)

        TestController.closed.connect(app.closeAllWindows)
        app.primary_container.closed.connect(app.closeAllWindows)

        @pyqtSlot()
        def emulate_car() -> None:
            bus_virtual_car.send(test_module.provide_random_message())

        @pyqtSlot()
        def emulate_conversation(msg: can.Message) -> None:
            response = test_module.provide_response_message(msg)
            bus_virtual_car.send(response)

        @pyqtSlot()
        def run() -> None:
            can.Notifier(bus_virtual_car, [emulate_conversation])
            # timed_func(app, emulate_car, 1)

        app.awakened.connect(run)

    can_app = CanApplication(app, bus)
    can_app.updated.connect(app.update_var)

    response_debounce = False
    last_response_time = time()

    @pyqtSlot()
    def run_conversation() -> None:
        global response_debounce, last_response_time
        if response_debounce:
            last_response_time = time()
            response_debounce = False
            # message = can.Message(is_extended_id=False,
            #                       arbitration_id=conversation_ids["send_id"],
            #                       data=[0x02, 0x01, 0x0D, 0, 0, 0, 0, 0])
            # can_app.send(message)
        elif time() - last_response_time >= CONVERSATION_PERIOD_MS:
            print("[WARNING]: No response from ECU during conversation")
            response_debounce = True
            last_response_time = time()

    @pyqtSlot()
    def run() -> None:
        can.Notifier(bus, [can_app.parse_data])

        @pyqtSlot()
        def response_received() -> None:
            global response_debounce
            response_debounce = True

        can_app.response_recieved.connect(response_received)

        @pyqtSlot()
        def attemp_init_conversation() -> None:
            if not response_debounce:
                timed_func(app, run_conversation, CONVERSATION_PERIOD_MS)
            else:
                print("ECU Conversation busy; eavesdropping only.")

        delay(app, attemp_init_conversation, CONVERSATION_WAIT)

    app.awakened.connect(run)
    sys.exit(app.exec())
