import platform
import subprocess
import sys
from typing import Any
import tomlkit
import can
from data import *
from numpy import average
from os import listdir
from pathlib import Path
from math import pi
from time import perf_counter
from qutil import Image, Arc, delay, timed_func, property_animation, TextLabel
from PyQt5.QtCore import (
    Qt,
    pyqtSignal,
    QSize,
    pyqtSlot,
    QPoint,
    QAbstractAnimation,
    QTimer,
)
from PyQt5.QtGui import (
    QColor,
    QCursor,
    QFontDatabase,
    QFont,
    QPalette,
    QTransform,
    QCloseEvent,
)
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from can_handler import (
    CanHandler,
    CAN_IDS,
    CURRENT_DATA_DEFINITIONS,
)
from dial import Dial

PLATFORM = platform.system()
RPI = "pi" in sys.argv
CONFIG_PATH = "config"

# TODO: lazy load
with open(CONFIG_PATH + "/settings.toml", "rb") as f:
    settings_toml = tomlkit.load(f)
    SETTINGS = settings_toml.unwrap()
    CAN_DEVICE_SETTINGS = SETTINGS["can_device"]

local_data = LocalData()
can_device_config = CanDeviceConfig()
settings = Settings()
tachomenter_dial_config = TachometerDialConfig()
speedometer_dial_config = SpeedometerDialConfig()
coolant_temp_dial_config = CoolantTempDialConfig()
fuel_level_dial_config = FuelLevelDialConfig()


START_WAIT = 1

RESOURCE_PATH = "resources"
IMAGE_PATH = RESOURCE_PATH + "/images"
FONT_PATH = RESOURCE_PATH + "/fonts"
FONT_GROUP = SETTINGS["fonts"]["main"]

SCREEN_SIZE = [1920, 720]
SCREEN_REFRESH_RATE = 75
DIAL_SIZE_MAJOR_INT = 660
DIAL_SIZE_MINOR_INT = 525
SYMBOL_SIZE = 63
SYMBOL_BUFFER = 5
SYMBOL_SIZE_SMALL = 50
SYMBOL_SIZE_EXTRA_SMALL = 28
AWAKEN_SEQUENCE_DURATION = 1750
AWAKEN_SEQUENCE_DURATION_STALL = 250
VISUAL_UPDATE_INTERVALS = {}

VISUAL_UPDATE_INVERVAL = 1 / (SCREEN_REFRESH_RATE * 2)

C_TO_F_SCALE = 1.8
C_TO_F_OFFSET = 32
KPH_TO_MPH_SCALE = 0.62137119
KPA_TO_PSI_SCALE = 6.895

AVG_FUEL_SAMPLES = 200
LOW_FUEL_THRESHHOLD = 15
NUM_SEATBELT_BLINKS = 15
SEATBELT_BLINK_INTERVAL_S = 1
SEATBELT_BLINK_WAIT_S = 15

BACKGROUND_COLOR = QColor(0, 0, 0)
SYMBOL_BLUE_COLOR = QColor(0, 0, 255)
SYMBOL_GREEN_COLOR = QColor(0, 230, 0)
SYMBOL_WHITE_COLOR = QColor(255, 255, 255)
SYMBOL_GRAY_COLOR = QColor(125, 125, 125)
SYMBOL_DARK_GRAY_COLOR = QColor(75, 75, 75)
SYMBOL_YELLOW_COLOR = QColor(255, 179, 0)
SYMBOL_RED_COLOR = QColor(255, 0, 0)
BLUELINE_COLOR = QColor(175, 150, 255)
PRIMARY_TEXT_COLOR = QColor(255, 255, 255)
SECONDARY_TEXT_COLOR = QColor(100, 100, 100)

MAJOR_DIAL_ANGLE_RANGE = 2 * pi - pi / 2 - pi / 5 - pi / 32

DIAL_SIZE_MAJOR = QSize(DIAL_SIZE_MAJOR_INT, DIAL_SIZE_MAJOR_INT)
DIAL_SIZE_MINOR = QSize(DIAL_SIZE_MINOR_INT, DIAL_SIZE_MINOR_INT)

ALL_DIAL_PARAMS = {
    "blueline_color": BLUELINE_COLOR,
    "gradient": True,
    "border_width": 2,
    "line_width": 1.5,
    "dial_opacity": 0.55,
    "needle_width_deg": 0.9,
}
DIAL_PARAMS_MAJOR = {
    "buffer_radius": 22,
    "num_radius": 54,
    "section_radius": 20,
    "minor_section_rad_offset": 5,
    "middle_section_rad_offset": 43,
    "major_section_rad_offset": 40,
    "angle_offset": pi,
    "dial_width": 140,
    "angle_range": MAJOR_DIAL_ANGLE_RANGE,
    "size": DIAL_SIZE_MAJOR,
}
DIAL_PARAMS_MINOR = {
    "buffer_radius": 22,
    "num_radius": 50,
    "section_radius": 15,
    "minor_section_rad_offset": 5,
    "middle_section_rad_offset": 58,
    "major_section_rad_offset": 40,
    "no_font": True,
    "dial_width": 50,
    "angle_range": 2 * pi - MAJOR_DIAL_ANGLE_RANGE - pi / 4 * 2,
    "size": DIAL_SIZE_MINOR,
    "angle_offset": MAJOR_DIAL_ANGLE_RANGE - pi + pi / 2.5,
}

local_path = Path("local")
local_data_path = local_path.joinpath("data.toml")


def save_local_data():
    with open(LOCAL_DATA_PATH, "w", encoding="UTF-8") as local_data_file:
        tomlkit.dump(local_data.__dict__, local_data_file)


def read_local_data():
    local_path.mkdir(parents=True, exist_ok=True)
    local_data_path.touch(exist_ok=True)

    with open(local_data_path, "rb") as f:
        for k, v in tomlkit.load(f).items():
            setattr(local_data, k, v)


def update_visual_update_intervals(keys: list[str] | Any):
    for i in keys:
        if i not in VISUAL_UPDATE_INTERVALS:
            VISUAL_UPDATE_INTERVALS[i] = VISUAL_UPDATE_INVERVAL


update_visual_update_intervals(CAN_IDS.keys())
update_visual_update_intervals(CURRENT_DATA_DEFINITIONS.keys())

turn_signal_offset_x = 70
turn_signal_offset_y = 40
bottom_symbol_y_offset = 10


class UI(QMainWindow):

    closed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        background_palette = QPalette()
        background_palette.setColor(QPalette.ColorRole.Background, BACKGROUND_COLOR)
        self.setPalette(background_palette)

        self.build_dials()
        self.built_images()

        angle_mid = 30
        arc_width = 1.5
        size_scale = 4.25

        self.cruise_control_status_widget = QWidget(self)
        self.cruise_control_status_widget.setStyleSheet("background:transparent")
        self.cruise_control_status_widget.resize(
            QSize(
                int(DIAL_SIZE_MAJOR_INT / size_scale),
                int(DIAL_SIZE_MAJOR_INT / size_scale),
            )
        )
        self.cruise_control_status_widget.move(
            self.speedometer.pos()
            + QPoint(DIAL_SIZE_MAJOR_INT // 2, DIAL_SIZE_MAJOR_INT // 2)
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

        # TODO: add arrow to fuel image instead
        self.fuel_cap_indicator_arrow = TextLabel(self, ">")
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

        self.cruise_control_speed_label = TextLabel(self, "0")
        self.cruise_control_speed_label.setFont(label_font)
        self.cruise_control_speed_label.setPalette(palette)
        self.cruise_control_speed_label.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.cruise_control_speed_label.move(
            self.speedometer.pos()
            + QPoint(
                DIAL_SIZE_MAJOR_INT // 2 - self.cruise_control_speed_label.width() // 2,
                DIAL_SIZE_MAJOR_INT // 2
                - self.cruise_control_speed_label.height() // 2,
            )
            + QPoint(0, int(SYMBOL_SIZE * 1.05))
        )

        label_font = QFont(FONT_GROUP, 34)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, PRIMARY_TEXT_COLOR)

        self.speed_label = TextLabel(self, "0")
        self.speed_label.setFont(label_font)
        self.speed_label.setPalette(palette)
        self.speed_label.resize(DIAL_SIZE_MAJOR)
        self.speed_label.move(
            int(
                SCREEN_SIZE[0]
                - DIAL_SIZE_MAJOR_INT
                - DIAL_SIZE_MAJOR_INT / 4
                + DIAL_SIZE_MAJOR_INT / 2
                - self.speed_label.width() / 2
            ),
            int(SCREEN_SIZE[1] / 2 - self.speed_label.height() / 2),
        )

        self.gear_indicator_label = TextLabel(self, "N")
        self.gear_indicator_label.setFont(label_font)
        self.gear_indicator_label.setPalette(palette)
        self.gear_indicator_label.resize(DIAL_SIZE_MAJOR)
        self.gear_indicator_label.move(
            int(
                DIAL_SIZE_MAJOR_INT / 4
                + DIAL_SIZE_MAJOR_INT / 2
                - self.gear_indicator_label.width() / 2
            ),
            int(SCREEN_SIZE[1] / 2 - self.gear_indicator_label.height() / 2),
        )

        label_font = QFont(FONT_GROUP, 20)
        self.odometer_label = TextLabel(self, "000000")
        self.odometer_label.setAlignment(
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom
        )
        self.odometer_label.setFont(label_font)
        self.odometer_label.text_color = PRIMARY_TEXT_COLOR
        self.odometer_label.resize(SCREEN_SIZE[0], SYMBOL_SIZE)
        self.odometer_label.move(
            int(SCREEN_SIZE[0] / 2 - self.odometer_label.width() / 2),
            int(SCREEN_SIZE[1] - self.odometer_label.height() - bottom_symbol_y_offset),
        )

    def build_dials(self) -> None:

        self.tachometer = Dial(
            self,
            label_font=QFont(FONT_GROUP, 20),
            **tachomenter_dial_config.__dict__,
            **DIAL_PARAMS_MAJOR,
            **ALL_DIAL_PARAMS,
        )
        self.tachometer.move(
            int(DIAL_SIZE_MAJOR_INT / 4),
            int(SCREEN_SIZE[1] / 2 - DIAL_SIZE_MAJOR_INT / 2),
        )

        self.speedometer = Dial(
            self,
            label_font=QFont(FONT_GROUP, 18),
            **speedometer_dial_config.__dict__,
            **DIAL_PARAMS_MAJOR,
            **ALL_DIAL_PARAMS,
        )
        self.speedometer.move(
            int(SCREEN_SIZE[0] - DIAL_SIZE_MAJOR_INT - DIAL_SIZE_MAJOR_INT / 4),
            int(SCREEN_SIZE[1] / 2 - DIAL_SIZE_MAJOR_INT / 2),
        )

        self.coolant_temp_gauge = Dial(
            self,
            **coolant_temp_dial_config.__dict__,
            **DIAL_PARAMS_MINOR,
            **ALL_DIAL_PARAMS,
        )
        self.coolant_temp_gauge.move(
            self.tachometer.pos() + QPoint(0, DIAL_SIZE_MAJOR_INT // 7)
        )
        self.coolant_temp_gauge.frame.setStyleSheet("background:transparent")

        self.fuel_level_gauge = Dial(
            self,
            **fuel_level_dial_config.__dict__,
            **DIAL_PARAMS_MINOR,
            **ALL_DIAL_PARAMS,
        )
        self.fuel_level_gauge.move(
            self.speedometer.pos() + QPoint(0, DIAL_SIZE_MAJOR_INT // 7)
        )
        self.fuel_level_gauge.frame.setStyleSheet("background:transparent")

    def built_images(self) -> None:

        """Depends on dials to be built first: `self.build_dials`"""
        vertical_mirror = QTransform().rotate(180)

        self.traction_control_mode_image = Image(
            self, IMAGE_PATH + "/traction-mode-indicator-light.png", SYMBOL_GREEN_COLOR
        )
        self.traction_control_mode_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.traction_control_mode_image.move(
            int(
                SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + 3 * (SYMBOL_SIZE + SYMBOL_BUFFER)
            ),
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

        self.srs_airbag_system_warning_light = Image(
            self,
            IMAGE_PATH + "/srs-airbag-system-warning-light.png",
            SYMBOL_RED_COLOR,
        )
        self.srs_airbag_system_warning_light.resize(
            int(SYMBOL_SIZE * 0.90), int(SYMBOL_SIZE * 0.90)
        )
        self.srs_airbag_system_warning_light.move(
            int(
                SCREEN_SIZE[0] / 2
                - self.srs_airbag_system_warning_light.width() / 2
                - 3 * (SYMBOL_SIZE + SYMBOL_BUFFER)
            ),
            int(
                SCREEN_SIZE[1]
                - self.srs_airbag_system_warning_light.height()
                - bottom_symbol_y_offset
            ),
        )

        self.oil_pressure_warning_light_image = Image(
            self,
            IMAGE_PATH + "/oil-pressure-warning-light.png",
            SYMBOL_RED_COLOR,
        )
        self.oil_pressure_warning_light_image.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.oil_pressure_warning_light_image.move(
            int(
                SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 - 6 * (SYMBOL_SIZE + SYMBOL_BUFFER)
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
            int(
                SCREEN_SIZE[0] / 2 - SYMBOL_SIZE / 2 + 4 * (SYMBOL_SIZE + SYMBOL_BUFFER)
            ),
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

        self.hill_assist_disabled_warning_light = Image(
            self, IMAGE_PATH + "/hillstartassist-warning-light.png", SYMBOL_YELLOW_COLOR
        )
        self.hill_assist_disabled_warning_light.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.hill_assist_disabled_warning_light.move(
            int(
                SCREEN_SIZE[0] / 2
                - SYMBOL_SIZE / 2
                + 11 * (SYMBOL_SIZE + SYMBOL_BUFFER)
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
                DIAL_SIZE_MAJOR_INT // 2 - SYMBOL_SIZE // 2 - 3,
                DIAL_SIZE_MAJOR_INT // 2
                - self.cruise_control_status_image.height() // 2,
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
                int(DIAL_SIZE_MINOR_INT / 3) - SYMBOL_SIZE_EXTRA_SMALL,
                int(DIAL_SIZE_MINOR_INT - SYMBOL_SIZE_EXTRA_SMALL * 4.2),
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
                int(DIAL_SIZE_MINOR_INT / 3) - SYMBOL_SIZE_EXTRA_SMALL,
                int(DIAL_SIZE_MINOR_INT - SYMBOL_SIZE_EXTRA_SMALL * 4.2),
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
                int(DIAL_SIZE_MINOR_INT / 3) - SYMBOL_SIZE_EXTRA_SMALL,
                int(DIAL_SIZE_MINOR_INT - SYMBOL_SIZE_EXTRA_SMALL * 4.2),
            )
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
        self.parking_brake_active_image.resize(
            int(SYMBOL_SIZE * 1.4), int(SYMBOL_SIZE * 1.2)
        )
        self.parking_brake_active_image.move(
            self.speedometer.pos()
            + QPoint(
                DIAL_SIZE_MAJOR_INT // 2 - self.parking_brake_active_image.width() // 2,
                DIAL_SIZE_MAJOR_INT // 2
                - self.parking_brake_active_image.height() // 2,
            )
            + QPoint(0, int(SYMBOL_SIZE * 3))
        )

        self.right_turn_signal_image_active = Image(
            self, IMAGE_PATH + "/turn-signal-arrow.png", SYMBOL_GREEN_COLOR
        )
        self.right_turn_signal_image_active.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.right_turn_signal_image_active.move(
            self.speedometer.pos() + QPoint(turn_signal_offset_x, turn_signal_offset_y)
        )

        self.left_turn_signal_image_active = Image(
            self,
            IMAGE_PATH + "/turn-signal-arrow.png",
            SYMBOL_GREEN_COLOR,
            vertical_mirror,
        )
        self.left_turn_signal_image_active.resize(SYMBOL_SIZE, SYMBOL_SIZE)
        self.left_turn_signal_image_active.move(
            self.tachometer.pos()
            + QPoint(self.tachometer.width() - SYMBOL_SIZE, 0)
            + QPoint(-turn_signal_offset_x, turn_signal_offset_y)
        )

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.closed.emit()
        return super().closeEvent(a0)


class Application(QApplication):

    awakened = pyqtSignal()
    init_wait = pyqtSignal()
    seatbelt_blink_timer = QTimer()

    def __init__(self) -> None:
        super().__init__([])

        read_local_data()

        # todo: fix this to use config value
        for font_file in listdir(FONT_PATH + "/Montserrat/static"):
            if Path(font_file).stem in SETTINGS["fonts"].values():
                QFontDatabase.addApplicationFont(
                    f"{FONT_PATH}/Montserrat/static/{font_file}"
                )

        self.setOverrideCursor(QCursor(Qt.CursorShape.BlankCursor))
        primary_container = UI()
        primary_container.setFixedSize(*SCREEN_SIZE)

        self._last_seatbelt_long_blink_time = 0
        self._last_seatbelt_rapid_blink_time = 0

        self.primary_container = primary_container
        self.cluster_vars: dict[str, Any] = {}
        self.cluster_vars_update_ts: dict[str, float] = {
            i: perf_counter() for i in VISUAL_UPDATE_INTERVALS.keys()
        }

        avg_fuel_stored_val = local_data.fuel_level_avg
        self.average_fuel_table: list[float] = [
            avg_fuel_stored_val for _ in range(AVG_FUEL_SAMPLES)
        ]

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
        self.odometer_text_color_animation_dim = property_animation(
            self,
            self.primary_container.odometer_label,
            "text_color",
            PRIMARY_TEXT_COLOR,
            SECONDARY_TEXT_COLOR,
            duration,
        )
        self.odometer_text_color_animation_bright = property_animation(
            self,
            self.primary_container.odometer_label,
            "text_color",
            SECONDARY_TEXT_COLOR,
            PRIMARY_TEXT_COLOR,
            duration,
        )

        self.cruise_control_set_last = 1
        self.seatbelt_blink_last_state = False

        odo_text = "000000"
        odo_value = local_data.odometer

        if odo_value > 0:
            odo_text = f"{odo_value:.0f}"

        self.primary_container.odometer_label.setText(odo_text)

        self.init_wait.connect(self.awaken_clusters)
        self.awakened.connect(lambda: timed_func(self, self.save_local_data, 1000))
        self.awakened.connect(self.odometer_text_color_animation_dim.start)

        delay(self, self.init_wait.emit, START_WAIT)

    def save_local_data(self) -> None:
        odometer = self.cluster_vars.get("odometer", 0)
        fuel_level_avg = float(average(self.average_fuel_table))

        local_data.odometer = odometer
        local_data.fuel_level_avg = fuel_level_avg

        save_local_data()

    @pyqtSlot()
    def awaken_clusters(self) -> None:
        duration = int((AWAKEN_SEQUENCE_DURATION - AWAKEN_SEQUENCE_DURATION_STALL) / 2)

        def start() -> None:
            property_animation(
                self,
                self.primary_container.tachometer,
                "dial_unit",
                tachomenter_dial_config.min_unit,
                tachomenter_dial_config.max_unit,
                duration,
            ).start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            property_animation(
                self,
                self.primary_container.speedometer,
                "dial_unit",
                speedometer_dial_config.min_unit,
                speedometer_dial_config.max_unit,
                duration,
            ).start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            property_animation(
                self,
                self.primary_container.fuel_level_gauge,
                "dial_unit",
                0,
                int(self.average_fuel_table[0]),
                duration,
            ).start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        def end() -> None:
            property_animation(
                self,
                self.primary_container.tachometer,
                "dial_unit",
                tachomenter_dial_config.max_unit,
                tachomenter_dial_config.min_unit,
                duration,
            ).start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
            property_animation(
                self,
                self.primary_container.speedometer,
                "dial_unit",
                speedometer_dial_config.max_unit,
                speedometer_dial_config.min_unit,
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

    @pyqtSlot(bool)
    def set_seatbelt_indicator(self, enabled: bool) -> None:
        if enabled and enabled != self.seatbelt_blink_last_state:
            self._last_seatbelt_long_blink_time = perf_counter()
            self._last_seatbelt_rapid_blink_time = (
                self._last_seatbelt_long_blink_time + SEATBELT_BLINK_WAIT_S
            )

            @pyqtSlot()
            def blink():
                current_time = perf_counter()

                if (
                    current_time - self._last_seatbelt_long_blink_time
                    >= SEATBELT_BLINK_WAIT_S
                    + SEATBELT_BLINK_INTERVAL_S * (NUM_SEATBELT_BLINKS + 1)
                ):
                    self._last_seatbelt_long_blink_time = (
                        self._last_seatbelt_rapid_blink_time
                    ) = (current_time + SEATBELT_BLINK_WAIT_S)
                elif (
                    current_time - self._last_seatbelt_rapid_blink_time
                    >= SEATBELT_BLINK_INTERVAL_S
                ):
                    self._last_seatbelt_rapid_blink_time = current_time
                    self.primary_container.seatbelt_driver_warning_image.setVisible(
                        False
                    )
                    delay(
                        self,
                        self.primary_container.seatbelt_driver_warning_image.setVisible,
                        SEATBELT_BLINK_INTERVAL_S / 2,
                        True,
                    )

            self.primary_container.seatbelt_driver_warning_image.setVisible(enabled)
            self.seatbelt_blink_timer.timeout.connect(blink)
            self.seatbelt_blink_timer.start(1)
        elif not enabled:
            if self.seatbelt_blink_timer.isActive():
                self.seatbelt_blink_timer.stop()

            self.primary_container.seatbelt_driver_warning_image.setVisible(enabled)

        self.seatbelt_blink_last_state = enabled

    @pyqtSlot(tuple)
    def update_var(self, data: tuple[str, Any]) -> None:
        t = perf_counter()
        var, val = data
        self.cluster_vars[var] = val

        if t - self.cluster_vars_update_ts[var] <= VISUAL_UPDATE_INTERVALS[var]:
            return

        match var:
            case "vehicle_speed":
                val *= KPH_TO_MPH_SCALE
                self.primary_container.speed_label.setText(f"{val:.0f}")
                self.primary_container.speedometer.dial_unit = val
            case "rpm":
                self.update_gear_indicator()
                self.primary_container.tachometer.dial_unit = val
            case "turn_signals":
                self.primary_container.left_turn_signal_image_active.setVisible(val[0])
                self.primary_container.right_turn_signal_image_active.setVisible(val[1])
            case "fuel_level":
                self.average_fuel_table.pop(0)
                self.average_fuel_table.append(val)

                avg = float(average(self.average_fuel_table))

                self.primary_container.fuel_level_gauge.dial_unit = avg
                self.primary_container.low_fuel_warning_image.setVisible(
                    avg <= LOW_FUEL_THRESHHOLD
                )
            case "coolant_temp":
                converted_val = val * C_TO_F_SCALE + C_TO_F_OFFSET
                self.primary_container.coolant_temp_gauge.dial_unit = converted_val
                if converted_val <= coolant_temp_dial_config.redline:
                    self.primary_container.coolant_temp_indicator_image_normal.setVisible(
                        False
                    )
                    self.primary_container.coolant_temp_indicator_image_cold.setVisible(
                        True
                    )
                    self.primary_container.coolant_temp_indicator_image_hot.setVisible(
                        False
                    )
                elif converted_val >= coolant_temp_dial_config.redline:
                    self.primary_container.coolant_temp_indicator_image_normal.setVisible(
                        False
                    )
                    self.primary_container.coolant_temp_indicator_image_cold.setVisible(
                        False
                    )
                    self.primary_container.coolant_temp_indicator_image_hot.setVisible(
                        True
                    )
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
            case "handbrake_switch":
                self.primary_container.parking_brake_active_image.setVisible(val)
            case "reverse_switch" | "clutch_switch" | "gear":
                self.update_gear_indicator()
            case "traction_control":
                self.primary_container.traction_control_off_image.setVisible(val)
            case "traction_control_mode":
                self.primary_container.traction_control_mode_image.setVisible(val)
            case "seatbelt_driver":
                self.set_seatbelt_indicator(val)
            case "cruise_control_status":
                self.primary_container.cruise_control_status_image.setVisible(val)
            case "fog_lights":
                self.primary_container.fog_light_image.setVisible(val)
            case "door_states":
                self.primary_container.door_open_warning_image.setVisible(True in val)
            case "headlights":
                self.primary_container.low_beam_image.setVisible(val[0] or val[1])
                self.primary_container.high_beam_image.setVisible(val[2])
            case "cruise_control_speed":
                if val > 0 and self.cluster_vars.get("cruise_control_status", 0):
                    self.primary_container.cruise_control_speed_label.setVisible(True)
                    self.primary_container.cruise_control_speed_label.setText(f"{val}")
                else:
                    self.primary_container.cruise_control_speed_label.setVisible(False)
            case "cruise_control_set":
                if val != self.cruise_control_set_last:
                    self.cruise_control_set_last = val
                    self.animate_cruise_control(
                        val and self.cluster_vars.get("cruise_control_status", 0)
                    )
            case "check_engine_light":
                self.primary_container.check_engine_light_image.setVisible(val)
            case "odometer":
                if val > 0:
                    self.primary_container.odometer_label.setText(f"{int(val)}")
            case "oil_pressure_warning":
                self.primary_container.oil_pressure_warning_light_image.setVisible(val)
            case "fuel_consumption":
                pass
            case "engine_load":
                pass
            case "intake_manifold_absolute_pressure":
                pass
            case "timing_advance":
                pass
            case "mass_air_flow":
                pass
            case "throttle_position":
                pass
            case "hill_assist":
                self.primary_container.hill_assist_disabled_warning_light.setVisible(
                    val
                )
            case "srs_airbag_system_warning_light":
                self.primary_container.srs_airbag_system_warning_light.setVisible(val)

        self.cluster_vars[var] = val
        self.cluster_vars_update_ts[var] = t


def main() -> None:
    app = Application()
    screens = app.screens()
    using_canbus = "nocan" not in sys.argv
    bus = None

    def post_can_init(bus: can.interface.Bus) -> None:
        can_app = CanHandler(app, bus)

        def run() -> None:
            can_app.updated.connect(app.update_var)

        def stop() -> None:
            can_app.close()
            app.closeAllWindows()

        app.aboutToQuit.connect(stop)
        app.setQuitOnLastWindowClosed(True)
        app.awakened.connect(run)

        sys.exit(app.exec())

    if RPI and using_canbus:
        screen = screens[0]
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
        app.primary_container.setFocus()

        try:
            if PLATFORM == "Linux":
                subprocess.run(
                    ["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True
                )
                subprocess.run(
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

            with can.thread_safe_bus.ThreadSafeBus(**CAN_DEVICE_SETTINGS) as bus:
                post_can_init(bus)
        except (
            can.exceptions.CanInitializationError,
            can.exceptions.CanInterfaceNotImplementedError,
        ):
            print("Could not find can interface device. ENTER to quit")
            input()
        except OSError:
            pass  # python-can has its own print
    else:
        import test_module

        app.primary_container.show()
        if len(screens) > 1:
            screen = screens[1]
            app.primary_container.move(screen.geometry().topLeft())

        with can.thread_safe_bus.ThreadSafeBus(
            channel="test", bustype="virtual"
        ) as bus, can.thread_safe_bus.ThreadSafeBus(
            channel="test", bustype="virtual"
        ) as bus_virtual_car:

            def emulate_car() -> None:
                bus_virtual_car.send(test_module.provide_random_message())

            def emulate_conversation(msg: can.message.Message) -> None:
                response = test_module.provide_response_message(msg)
                bus_virtual_car.send(response)

            def run() -> None:
                can.notifier.Notifier(bus_virtual_car, [emulate_conversation])
                timed_func(app, emulate_car, 0)

            app.awakened.connect(run)

            post_can_init(bus)


if __name__ == "__main__":
    main()
