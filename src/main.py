# formatted with yapf
# Bryce Happel Walton

#! This program may be too slow on the RPi

import platform, sys, subprocess
from math import pi
from random import randrange
from time import time

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCursor, QFont, QPixmap, QPalette, QColor, QImage, QTransform
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

from can_handle import CanApplication, can_ids
from dial import Dial

system = platform.system()

screen_size = [1920, 720]
screen_refresh_rate = 75 if system == "Linux" else 60 if system == "Darwin" else 144

rpm_params = {
    "min": 0,
    "max": 8000,
    "redline": 6700,
    "mid_sections": 10,
    "denomination": 1000
}
speed_params = {"min": 0, "max": 180, "units": "MPH", "mid_sections": 10}
coolant_temp_params = {
    "min": 0,
    "max": 230,
    "units": "F",
    "mid_sections": 3,
    "redline": 230 - 46,
    "blueline": 80
}

visual_update_intervals = {
    "coolant_temp": 0.75,
    "oil_temp": 0.75
}

for i in can_ids.keys():
    if not i in visual_update_intervals:
        visual_update_intervals[i] = 1 / screen_refresh_rate

cluster_size = 660

c_to_f_scale = 9 / 5
c_to_f_offset = 32
kph_to_mph = 0.62137119


def change_image_color(image: QImage, color: QColor):
    for x in range(image.width()):
        for y in range(image.height()):
            pcolor = image.pixelColor(x, y)
            if pcolor.alpha() > 0:
                n_color = QColor(color)
                n_color.setAlpha(pcolor.alpha())
                image.setPixelColor(x, y, n_color)


class MainWindow(QMainWindow):

    def __init__(self, scale=1):
        super().__init__()

        self.setWindowTitle("Digital Cluster")

        font_group = "Sans Serif Collection"
        font_weight = 600
        big_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32

        coolant_temp_gauge = Dial(
            self,
            size=cluster_size,
            min_unit=coolant_temp_params["min"],
            max_unit=coolant_temp_params["max"],
            redline=coolant_temp_params["redline"],
            blueline=coolant_temp_params["blueline"],
            blueline_color=[125, 125, 255],
            dial_opacity="10%",
            mid_sections=coolant_temp_params["mid_sections"],
            no_font=True,
            visual_num_gap=28.75,
            angle_offset=big_dial_angle_range - pi + pi / 5,
            angle_range=2 * pi - big_dial_angle_range - pi / 5 * 2,
            buffer_radius=20 * scale,
            num_radius=50 * scale,
            section_radius=15 * scale,
            minor_section_rad_offset=3 * scale,
            middle_section_rad_offset=58 * scale,
            major_section_rad_offset=40 * scale,
            dial_mask_rad=525 * scale,
            dial_inner_border_rad=3 * scale,
            dymanic_mask=True)
        coolant_temp_gauge.move(int(cluster_size / 4),
                                int(screen_size[1] / 2 - cluster_size / 2))
        coolant_temp_gauge.show()

        rpm_gauge = Dial(self,
                         size=cluster_size,
                         min_unit=rpm_params["min"],
                         max_unit=rpm_params["max"],
                         redline=rpm_params["redline"],
                         mid_sections=rpm_params["mid_sections"],
                         denomination=rpm_params["denomination"],
                         visual_num_gap=rpm_params["denomination"],
                         label_font=QFont(font_group, 19 * scale, font_weight),
                         angle_offset=pi,
                         angle_range=big_dial_angle_range,
                         buffer_radius=20 * scale,
                         num_radius=54 * scale,
                         section_radius=20 * scale,
                         minor_section_rad_offset=3 * scale,
                         middle_section_rad_offset=43 * scale,
                         major_section_rad_offset=40 * scale,
                         dial_mask_rad=360 * scale,
                         dial_inner_border_rad=4 * scale)
        rpm_gauge.frame.setStyleSheet("background:transparent")
        rpm_gauge.move(int(cluster_size / 4),
                       int(screen_size[1] / 2 - cluster_size / 2))
        rpm_gauge.show()

        speed_gauge = Dial(self,
                           size=cluster_size,
                           min_unit=speed_params["min"],
                           max_unit=speed_params["max"],
                           redline=speed_params["max"] + 1,
                           mid_sections=speed_params["mid_sections"],
                           visual_num_gap=20,
                           label_font=QFont(font_group, 18 * scale,
                                            font_weight),
                           angle_offset=pi,
                           angle_range=big_dial_angle_range,
                           buffer_radius=20 * scale,
                           num_radius=54 * scale,
                           section_radius=20 * scale,
                           minor_section_rad_offset=3 * scale,
                           middle_section_rad_offset=43 * scale,
                           major_section_rad_offset=40 * scale,
                           dial_mask_rad=360 * scale,
                           dial_inner_border_rad=4 * scale)
        speed_gauge.move(int(screen_size[0] - cluster_size - cluster_size / 4),
                         int(screen_size[1] / 2 - cluster_size / 2))
        speed_gauge.show()

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

        label_font = QFont("Sans-serif", 22 * scale)
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        turn_signal_offset = -30 * scale
        turn_signal_size = 50 * scale

        right_turn_signal_image = QLabel(self)
        right_turn_signal_image.setPixmap(right_arrow_image_black)
        right_turn_signal_image.move(
            int(screen_size[0] - cluster_size -
                cluster_size / 4 - turn_signal_offset),
            int(screen_size[1] / 2 - cluster_size / 2))
        right_turn_signal_image.setScaledContents(True)
        right_turn_signal_image.resize(turn_signal_size, turn_signal_size)
        right_turn_signal_image.show()

        left_turn_signal_image = QLabel(self)
        left_turn_signal_image.setPixmap(left_arrow_image_black)
        left_turn_signal_image.move(
            int(cluster_size / 4 + cluster_size -
                turn_signal_size + turn_signal_offset),
            int(screen_size[1] / 2 - cluster_size / 2))
        left_turn_signal_image.setScaledContents(True)
        left_turn_signal_image.resize(turn_signal_size, turn_signal_size)
        left_turn_signal_image.show()

        speed_label_size = 200

        speed_label = QLabel(self)
        speed_label.setText(f"{0}")
        speed_label.setStyleSheet("background:transparent")
        speed_label.setFont(label_font)
        speed_label.setPalette(palette)
        speed_label.move(
            int(screen_size[0] - cluster_size - cluster_size / 4 +
                cluster_size / 2 - 25 * scale / 2),
            int(screen_size[1] / 2 - cluster_size / 2 +
                speed_label_size * scale))
        speed_label.resize(speed_label_size * scale, speed_label_size * scale)
        speed_label.show()

        rpm_label_size = speed_label_size

        rpm_label = QLabel(self)
        rpm_label.setStyleSheet("background:transparent")
        rpm_label.setText(f"{0}")
        rpm_label.move(
            int(cluster_size / 4 + cluster_size / 2 - 25 * scale),
            int(screen_size[1] / 2 - cluster_size / 2 +
                rpm_label_size * scale))
        rpm_label.setFont(label_font)
        rpm_label.setPalette(palette)
        rpm_label.resize(rpm_label_size * scale, rpm_label_size * scale)
        rpm_label.show()

        label_font = QFont("Sans-serif", 16 * scale)
        color = QColor(255, 255, 255)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        oil_temp_label = QLabel(self)
        oil_temp_label.setStyleSheet("background:transparent")
        oil_temp_label.setText(f"Oil Temp: {0} F")
        oil_temp_label.setFont(label_font)
        oil_temp_label.setPalette(palette)
        oil_temp_label.resize(150 * scale, rpm_label_size * scale)
        oil_temp_label.show()
        oil_temp_label.move(
            int(screen_size[0] / 2 -
                oil_temp_label.frameGeometry().width() / 2 * scale),
            int(screen_size[1] / 2 -
                oil_temp_label.frameGeometry().height() / 2 * scale))

        label_font = QFont("Sans-serif", 17 * scale)
        color = QColor(255, 0, 0)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        hand_brake_label = QLabel(self)
        hand_brake_label.setStyleSheet("background:transparent")
        hand_brake_label.setText(f"BRAKE")
        hand_brake_label.setFont(label_font)
        hand_brake_label.setPalette(palette)
        hand_brake_label.resize(80 * scale, 75 * scale)
        hand_brake_label.move(
            int(screen_size[0] - cluster_size - cluster_size / 4 +
                cluster_size / 2 -
                hand_brake_label.frameGeometry().width() / 2 * scale),
            int(screen_size[1] / 2 - cluster_size / 2 +
                speed_label_size * scale +
                hand_brake_label.frameGeometry().height() * 4 * scale))
        hand_brake_label.show()

        self.oil_temp_label = oil_temp_label
        self.hand_brake_label = hand_brake_label

        self.rpm_label = rpm_label
        self.speed_label = speed_label

        self.right_turn_signal_image = right_turn_signal_image
        self.left_turn_signal_image = left_turn_signal_image

        self.speedometer = speed_gauge
        self.tachometer = rpm_gauge
        self.coolant_temp_gauge = coolant_temp_gauge


class Application(QApplication):

    awakened = pyqtSignal()
    started = pyqtSignal()

    cluster_vars = {}
    cluster_vars_update_ts = {i: time() for i in visual_update_intervals.keys()}

    awaken_sequence_duration_ms = 2500

    def __init__(self, scale=1):
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

    def awaken_clusters(self):
        timer = QTimer(self)

        self._awaken_a = 0
        self._awaken_t = 0

        t_step = self.awaken_sequence_duration_ms / screen_refresh_rate
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

    def updateVar(self, var, val):
        t = time()
        self.cluster_vars[var] = val

        if t - self.cluster_vars_update_ts[var] <= visual_update_intervals[var]:
            return

        print(f"{(t - self.cluster_vars_update_ts[var]):.5f}",
                visual_update_intervals[var],
                (t - self.cluster_vars_update_ts[var]) >=
                visual_update_intervals[var])

        if var == "vehicle_speed":
            self.primary_container.speed_label.setText(
                f"{val * kph_to_mph:.0f}")
            #self.primary_container.speedometer.setUnit(val)
        elif var == "rpm":
            self.primary_container.rpm_label.setText(f"{val}")
            #self.primary_container.tachometer.setUnit(val)
        elif var == "turn_signals":
            if val["left_turn_signal"]:
                self.primary_container.left_turn_signal_image.setPixmap(
                    self.primary_container.left_arrow_image_green)
            else:
                self.primary_container.left_turn_signal_image.setPixmap(
                    self.primary_container.left_arrow_image_black)

            if val["right_turn_signal"]:
                self.primary_container.right_turn_signal_image.setPixmap(
                    self.primary_container.right_arrow_image_green)
            else:
                self.primary_container.right_turn_signal_image.setPixmap(
                    self.primary_container.right_arrow_image_black)
        elif var == "fuel_level":
            if time(
            ) - self.last_updated_fuel >= self.update_fuel_level_interval:
                self.last_updated_fuel = time()
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
            #print(f"Neutral: {val}")
            pass
        elif var == "reverse_switch":
            #print(f"Reverse: {val}")
            pass

        self.cluster_vars[var] = val
        self.cluster_vars_update_ts[var] = t


if __name__ == "__main__":
    scale = 1

    if system == "Darwin":
        scale = 1 / 1.3325
    elif system == "Windows":
        scale = 1# / 1.25

    screen_size = [1920 * scale, 720 * scale]
    cluster_size *= scale
    app = Application(scale=scale)
    screens = app.screens()

    turn_signal_data = [
        [0x0F, 0x04, 0x00, 0x00, 0x00, 0x30, 0x00, 0x00],  # hazards
        [0x0F, 0x04, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00],  # right turn
        [0x0F, 0x04, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00],  # left turn
        [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]  # everything off
    ]

    import can_data

    def emulate_can():
        app.updateVar("vehicle_speed",
                      randrange(speed_params["min"], speed_params["max"] + 1))
        app.updateVar("rpm", randrange(rpm_params["min"],
                                       rpm_params["max"] + 1))
        app.updateVar(
            "turn_signals",
            can_data.turn_signals(turn_signal_data[randrange(
                0, len(turn_signal_data))]))
        app.updateVar("handbrake", randrange(0, 2))
        app.updateVar("oil_temp", randrange(0, 104 + 1))
        app.updateVar(
            "coolant_temp",
            randrange(coolant_temp_params["min"],
                      104 + 1))

    def run():
        timer = QTimer(app)
        timer.timeout.connect(emulate_can)
        timer.start(1/screen_refresh_rate)

    if system != "Linux":
        if len(screens) > 1:
            screen = screens[1]
            app.primary_container.move(screen.geometry().topLeft())
            app.primary_container.showFullScreen()
        else:
            app.primary_container.setFixedSize(screen_size[0], screen_size[1])

        app.awakened.connect(run)
    else:
        screen = screens[0]
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
        app.primary_container.setFixedSize(screen_size[0], screen_size[1])

        using_pican = True

        try:
            shutdown_can = subprocess.run(
                ["sudo", "/sbin/ip", "link", "set", "can0", "down"],
                check=True)
            setup_can = subprocess.run([
                "sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can",
                "bitrate", "500000"
            ],
                                       check=True)
            can_app = CanApplication()
        except:
            print("Could not find PiCan device. Switching to emulation.")
            using_pican = False

        if using_pican:

            def read_can():
                msg = can_app.get_data()

                if msg:
                    can_app.parse_data(msg)

            def run():
                timer = QTimer(app)
                timer.timeout.connect(read_can)
                timer.start(1 / 500000)

            app.awakened.connect(run)
            can_app.updated.connect(app.updateVar)
        else:
            app.awakened.connect(run)

    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
