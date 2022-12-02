# formatted with yapf
# Bryce Happel Walton

import platform
import subprocess
import sys
import tomllib
import can
from math import pi
from time import time
from qutil import change_image_color
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QSize, QEvent, pyqtSlot
from PyQt5.QtGui import (QColor, QCursor, QFont, QImage, QPalette, QPixmap,
                         QTransform)
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from can_handle import CanApplication, can_ids
from dial import Dial

system = platform.system()

screen_size = [1920, 720]
screen_refresh_rate = 75 if system == "Linux" else 60 if system == "Darwin" else 144

visual_update_intervals = {"coolant_temp": 0.75, "oil_temp": 0.75}

with open("config/gauge_config.toml", "rb") as f:
    gauge_params = tomllib.load(f)

for i in can_ids.keys():
    if not i in visual_update_intervals:
        visual_update_intervals[i] = 1 / screen_refresh_rate

original_cluster_size = 660

c_to_f_scale = 1.8
c_to_f_offset = 32
kph_to_mph = 0.62137119


class MainWindow(QMainWindow):

    def __init__(self, scale: float = 1) -> None:
        super().__init__()

        self.setWindowTitle("Digital Cluster")

        font_group = "Sans Serif"
        if system != "Windows":
            font_group = "Microsoft Sans Serif"
        font_weight = 600
        big_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32

        int_size = int(original_cluster_size * scale)
        cluster_size = QSize(int_size, int_size)

        dial_params_minor = {
            "buffer_radius": 20 * scale,
            "num_radius": 50 * scale,
            "section_radius": 15 * scale,
            "minor_section_rad_offset": 3 * scale,
            "middle_section_rad_offset": 58 * scale,
            "major_section_rad_offset": 40 * scale
        }

        dial_params_major = {
            "buffer_radius": 20 * scale,
            "num_radius": 54 * scale,
            "section_radius": 20 * scale,
            "minor_section_rad_offset": 3 * scale,
            "middle_section_rad_offset": 43 * scale,
            "major_section_rad_offset": 40 * scale
        }

        for i, v in dial_params_minor.items():
            dial_params_minor[i] = int(v)
        for i, v in dial_params_major.items():
            dial_params_major[i] = int(v)

        dial_opacity = 0.375
        dial_width = 110

        coolant_temp_gauge = Dial(
            self,
            size=cluster_size,
            min_unit=gauge_params["coolant_temp"]["min"],
            max_unit=gauge_params["coolant_temp"]["max"],
            redline=gauge_params["coolant_temp"]["redline"],
            blueline=gauge_params["coolant_temp"]["blueline"],
            blueline_color=QColor(125, 125, 255),
            dial_opacity=0.3,
            dial_width=30,
            mid_sections=gauge_params["coolant_temp"]["mid_sections"],
            no_font=True,
            visual_num_gap=28.75,
            angle_offset=big_dial_angle_range - pi + pi / 5,
            angle_range=2 * pi - big_dial_angle_range - pi / 5 * 2,
            **dial_params_minor)
        coolant_temp_gauge.move(int(int_size / 4),
                                int(screen_size[1] / 2 - int_size / 2))

        rpm_gauge = Dial(
            self,
            size=cluster_size,
            min_unit=gauge_params["tachometer"]["min"],
            max_unit=gauge_params["tachometer"]["max"],
            redline=gauge_params["tachometer"]["redline"],
            mid_sections=gauge_params["tachometer"]["mid_sections"],
            denomination=gauge_params["tachometer"]["denomination"],
            visual_num_gap=gauge_params["tachometer"]["denomination"],
            label_font=QFont(font_group, int(19 * scale), font_weight),
            angle_offset=pi,
            dial_opacity=dial_opacity,
            dial_width=dial_width,
            angle_range=big_dial_angle_range,
            **dial_params_major)
        rpm_gauge.frame.setStyleSheet("background:transparent")
        rpm_gauge.move(int(int_size / 4),
                       int(screen_size[1] / 2 - int_size / 2))

        speed_gauge = Dial(
            self,
            size=cluster_size,
            min_unit=gauge_params["speedometer"]["min"],
            max_unit=gauge_params["speedometer"]["max"],
            redline=gauge_params["speedometer"]["max"] + 1,
            mid_sections=gauge_params["speedometer"]["mid_sections"],
            visual_num_gap=20,
            dial_opacity=dial_opacity,
            dial_width=dial_width,
            label_font=QFont(font_group, int(18 * scale), font_weight),
            angle_offset=pi,
            angle_range=big_dial_angle_range,
            **dial_params_major)
        speed_gauge.move(int(screen_size[0] - int_size - int_size / 4),
                         int(screen_size[1] / 2 - int_size / 2))

        color_black = QColor(0, 0, 0)
        color_green = QColor(0, 255, 0)
        vertical_mirror = QTransform().rotate(180)

        right_arrow_image_black = QImage("resources/turn-signal-arrow.png")
        change_image_color(right_arrow_image_black, color_black)
        right_arrow_image_black = QPixmap.fromImage(right_arrow_image_black)

        right_arrow_image_green = QImage("resources/turn-signal-arrow.png")
        change_image_color(right_arrow_image_green, color_green)
        right_arrow_image_green = QPixmap.fromImage(right_arrow_image_green)

        left_arrow_image_black = QImage("resources/turn-signal-arrow.png")
        change_image_color(left_arrow_image_black, color_black)
        left_arrow_image_black = QPixmap.fromImage(left_arrow_image_black)
        left_arrow_image_black = left_arrow_image_black.transformed(
            vertical_mirror)

        left_arrow_image_green = QImage("resources/turn-signal-arrow.png")
        change_image_color(left_arrow_image_green, color_green)
        left_arrow_image_green = QPixmap.fromImage(left_arrow_image_green)
        left_arrow_image_green = left_arrow_image_green.transformed(
            vertical_mirror)

        self.right_arrow_image_black = right_arrow_image_black
        self.right_arrow_image_green = right_arrow_image_green
        self.left_arrow_image_black = left_arrow_image_black
        self.left_arrow_image_green = left_arrow_image_green

        turn_signal_offset = int(-30 * scale)
        turn_signal_size = int(50 * scale)

        right_turn_signal_image = QLabel(self)
        right_turn_signal_image.setPixmap(right_arrow_image_black)
        right_turn_signal_image.move(
            int(screen_size[0] - int_size - int_size / 4 - turn_signal_offset),
            int(screen_size[1] / 2 - int_size / 2))
        right_turn_signal_image.setScaledContents(True)
        right_turn_signal_image.resize(turn_signal_size, turn_signal_size)

        right_turn_signal_image_active = QLabel(self)
        right_turn_signal_image_active.setPixmap(right_arrow_image_green)
        right_turn_signal_image_active.move(
            int(screen_size[0] - int_size - int_size / 4 - turn_signal_offset),
            int(screen_size[1] / 2 - int_size / 2))
        right_turn_signal_image_active.setScaledContents(True)
        right_turn_signal_image_active.resize(turn_signal_size,
                                              turn_signal_size)

        left_turn_signal_image = QLabel(self)
        left_turn_signal_image.setPixmap(left_arrow_image_black)
        left_turn_signal_image.move(
            int(int_size / 4 + int_size - turn_signal_size +
                turn_signal_offset), int(screen_size[1] / 2 - int_size / 2))
        left_turn_signal_image.setScaledContents(True)
        left_turn_signal_image.resize(turn_signal_size, turn_signal_size)

        left_turn_signal_image_active = QLabel(self)
        left_turn_signal_image_active.setPixmap(left_arrow_image_green)
        left_turn_signal_image_active.move(
            int(int_size / 4 + int_size - turn_signal_size +
                turn_signal_offset), int(screen_size[1] / 2 - int_size / 2))
        left_turn_signal_image_active.setScaledContents(True)
        left_turn_signal_image_active.resize(turn_signal_size,
                                             turn_signal_size)

        speed_label_size = 200
        label_font = QFont(font_group, int(22 * scale))
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        speed_label = QLabel(self)
        speed_label.setText(f"{0}")
        speed_label.setStyleSheet("background:transparent")
        speed_label.setFont(label_font)
        speed_label.setPalette(palette)
        speed_label.move(
            int(screen_size[0] - int_size - int_size / 4 + int_size / 2 -
                25 * scale / 2),
            int(screen_size[1] / 2 - int_size / 2 + speed_label_size * scale))
        speed_label.resize(int(speed_label_size * scale),
                           int(speed_label_size * scale))

        rpm_label_size = speed_label_size

        rpm_label = QLabel(self)
        rpm_label.setStyleSheet("background:transparent")
        rpm_label.setText(f"{0}")
        rpm_label.move(
            int(int_size / 4 + int_size / 2 - 25 * scale),
            int(screen_size[1] / 2 - int_size / 2 + rpm_label_size * scale))
        rpm_label.setFont(label_font)
        rpm_label.setPalette(palette)
        rpm_label.resize(int(rpm_label_size * scale),
                         int(rpm_label_size * scale))

        label_font = QFont(font_group, int(16 * scale))
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        oil_temp_label = QLabel(self)
        oil_temp_label.setStyleSheet("background:transparent")
        oil_temp_label.setText(f"Oil Temp: {0} F")
        oil_temp_label.setFont(label_font)
        oil_temp_label.setPalette(palette)
        oil_temp_label.resize(int(150 * scale), int(rpm_label_size * scale))
        oil_temp_label.move(
            int(screen_size[0] / 2 -
                oil_temp_label.frameGeometry().width() / 2 * scale),
            int(screen_size[1] / 2 -
                oil_temp_label.frameGeometry().height() / 2 * scale))

        label_font = QFont(font_group, int(17 * scale))
        color = QColor(255, 0, 0)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        hand_brake_label = QLabel(self)
        hand_brake_label.setStyleSheet("background:transparent")
        hand_brake_label.setText(f"BRAKE")
        hand_brake_label.setFont(label_font)
        hand_brake_label.setPalette(palette)
        hand_brake_label.resize(int(80 * scale), int(75 * scale))
        hand_brake_label.move(
            int(screen_size[0] - int_size - int_size / 4 + int_size / 2 -
                hand_brake_label.frameGeometry().width() / 2 * scale),
            int(screen_size[1] / 2 - int_size / 2 + speed_label_size * scale +
                hand_brake_label.frameGeometry().height() * 4 * scale))

        self.oil_temp_label = oil_temp_label
        self.hand_brake_label = hand_brake_label

        self.rpm_label = rpm_label
        self.speed_label = speed_label

        self.right_turn_signal_image = right_turn_signal_image
        self.left_turn_signal_image = left_turn_signal_image
        self.right_turn_signal_image_active = right_turn_signal_image_active
        self.left_turn_signal_image_active = left_turn_signal_image_active

        self.speedometer = speed_gauge
        self.tachometer = rpm_gauge
        self.coolant_temp_gauge = coolant_temp_gauge


class Application(QApplication):

    awakened = pyqtSignal()

    cluster_vars = {}
    cluster_vars_update_ts = {
        i: time()
        for i in visual_update_intervals.keys()
    }

    awaken_sequence_duration_ms = 1750

    def __init__(self, scale: float = 1) -> None:
        super().__init__([])
        self.setOverrideCursor(QCursor(Qt.BlankCursor))
        primary_container = MainWindow(scale)
        background_color = (100, 100, 100)
        primary_container.setStyleSheet(
            f"background-color: rgb({background_color[0]}, {background_color[1]}, {background_color[2]})"
        )

        self.start_time = time()
        self.primary_container = primary_container

        self.update_funcs = {}

        self.awaken_clusters()

    def awaken_clusters(self) -> None:
        timer = QTimer(self)

        self._awaken_a = 0
        self._awaken_t = 0

        t_step = self.awaken_sequence_duration_ms // 1000
        a_step = t_step / self.awaken_sequence_duration_ms

        self.primary_container.tachometer.setDial(0)
        self.primary_container.speedometer.setDial(0)

        self._last_time = time() * 1000
        start_time = self._last_time

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

    @pyqtSlot(tuple)
    def updateVar(self, new: tuple) -> None:
        t = time()
        var = new[0]
        val = new[1]
        self.cluster_vars[var] = val

        if t - self.cluster_vars_update_ts[var] <= visual_update_intervals[var]:
            return

        if var == "vehicle_speed":
            self.primary_container.speed_label.setText(
                f"{val * kph_to_mph:.0f}")
            self.primary_container.speedometer.setUnit(val)
        elif var == "rpm":
            self.primary_container.rpm_label.setText(f"{val}")
            self.primary_container.tachometer.setUnit(val)
        elif var == "turn_signals":
            left_turn_signal = val["left_turn_signal"]
            right_turn_signal = val["right_turn_signal"]

            self.primary_container.left_turn_signal_image.setHidden(
                not left_turn_signal)
            self.primary_container.left_turn_signal_image_active.setHidden(
                left_turn_signal)
            self.primary_container.right_turn_signal_image.setHidden(
                not right_turn_signal)
            self.primary_container.right_turn_signal_image_active.setHidden(
                right_turn_signal)
        elif var == "fuel_level":
            pass
        #todo: make config file of sorts that has user selected units
        elif var == "oil_temp":
            self.primary_container.oil_temp_label.setText(
                f"Oil Temp: {val * c_to_f_scale + c_to_f_offset:.0f} F")
        elif var == "coolant_temp":
            self.primary_container.coolant_temp_gauge.setUnit(val *
                                                              c_to_f_scale +
                                                              c_to_f_offset)
        elif var == "handbrake":
            if val:
                self.primary_container.hand_brake_label.setText("BRAKE")
            else:
                self.primary_container.hand_brake_label.setText("")
        elif var == "neutral_switch":
            pass
        elif var == "reverse_switch":
            pass

        self.cluster_vars[var] = val
        self.cluster_vars_update_ts[var] = t


if __name__ == "__main__":
    scale = 1
    if system == "Darwin":
        scale = 1 / 1.3325
    elif system == "Windows":
        scale = 1 / 1.25

    screen_size = [int(1920 * scale), int(720 * scale)]
    app = Application(scale=scale)

    screens = app.screens()
    if system != "Linux":
        if len(screens) > 1:
            screen = screens[1]
            app.primary_container.move(screen.geometry().topLeft())
            app.primary_container.showFullScreen()
        else:
            app.primary_container.setFixedSize(screen_size[0], screen_size[1])
    else:
        screen = screens[0]
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
        app.primary_container.setFixedSize(screen_size[0], screen_size[1])

    if system == "Linux" and len(sys.argv) > 1:
        using_canbus = sys.argv[1] != "nocan"
    elif system != "Linux":
        using_canbus = False
    else:
        using_canbus = True

    if system == "Linux":
        try:
            shutdown_can = subprocess.run(
                ["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True)
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

        def emulate_car():
            bus_virtual_car.send(test_provider.provide_random_message())

        def run():
            timer = QTimer(app)
            timer.timeout.connect(emulate_car)
            timer.start(1000 // 500000)

        app.awakened.connect(run)

    can_app = CanApplication(app, bus)
    can_app.updated.connect(app.updateVar)

    def read_can():
        msg = can_app.get_data()
        can_app.parse_data(msg)

    def run():
        timer = QTimer(app)
        timer.timeout.connect(read_can)
        timer.start(1000 // 500000)

    app.awakened.connect(run)
    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
