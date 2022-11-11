# formatted with yapf
# Bryce Happel Walton

#todo: This program is far too slow on the RPi

import platform
import subprocess
import sys
from math import pi
from random import random
from time import sleep, time

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QCursor, QFont, QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel

from can_handle import CanApplication
from dial import Dial

screen_size = [1920, 720]
rpm_params = {
    "min": 0,
    "max": 8000,
    "redline": 6700,
    "mid_sections": 10,
    "denomination": 1000
}
speed_params = {"min": 0, "max": 180, "units": "MPH", "mid_sections": 10}

cluster_size = 600


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Digital Cluster")

        font_group = "Sans Serif Collection"
        font_weight = 600
        big_dial_angle_range = 2 * pi - pi / 2 - pi / 5 - pi / 32

        rpm_gauge = Dial(self,
                         size=cluster_size,
                         min_unit=rpm_params["min"],
                         max_unit=rpm_params["max"],
                         redline=rpm_params["redline"],
                         mid_sections=rpm_params["mid_sections"],
                         denomination=rpm_params["denomination"],
                         visual_num_gap=rpm_params["denomination"],
                         label_font=QFont(f"{font_group}", 21, font_weight),
                         angle_offset=pi,
                         angle_range=big_dial_angle_range)

        rpm_gauge.move(int(cluster_size / 4),
                       int(screen_size[1] / 2 - cluster_size / 2))

        rpm_gauge.show()
        self.tachometer = rpm_gauge

        speed_gauge = Dial(self,
                           size=cluster_size,
                           min_unit=speed_params["min"],
                           max_unit=speed_params["max"],
                           redline=speed_params["max"] + 1,
                           mid_sections=speed_params["mid_sections"],
                           units=speed_params["units"],
                           visual_num_gap=20,
                           label_font=QFont(f"{font_group}", 18, font_weight),
                           angle_offset=pi,
                           angle_range=big_dial_angle_range)

        speed_gauge.move(int(screen_size[0] - cluster_size - cluster_size / 4),
                         int(screen_size[1] / 2 - cluster_size / 2))
        speed_gauge.show()

        arrow_image = QPixmap("resources/turn-signal-arrow.png")
        label = QLabel(self)
        label.setPixmap(arrow_image)
        label.resize(arrow_image.width(), arrow_image.height())
        label.move(int(cluster_size / 4 + cluster_size), 10)
        label.show()


        self.speedometer = speed_gauge


class Application(QApplication):

    awakened = pyqtSignal()
    started = pyqtSignal()

    def __init__(self):
        super().__init__([])
        self.setOverrideCursor(QCursor(Qt.BlankCursor))
        primary_container = MainWindow()

        self.start_time = time()

        self.awaken_sequence_duration_ms = 2500
        self.awaken_sequence_steps = 2000
        self.primary_container = primary_container

        label = QLabel(self.primary_container)
        label.setText("Test")
        label.resize(200, 200)
        label.show()
        self.label = label

        self.awaken_clusters()

        self.cluster_vars = {"rpm": 0, "speed": 0}

    def awaken_clusters(self):
        timer = QTimer(self)

        self._awaken_a = 0
        self._awaken_t = 0

        t_step = self.awaken_sequence_duration_ms / self.awaken_sequence_steps
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
        timer.start(int(t_step))

    def clusterUpdate(self):
        self.primary_container.tachometer.setUnit(self.cluster_vars["rpm"])
        #self.primary_container.speedometer.setUnit(self.cluster_vars["speed"])
        rpm = self.cluster_vars["rpm"]
        self.label.setText(f"{rpm}")

    def updateVar(self, var, val):
        self.cluster_vars[var] = val
        self.clusterUpdate()


if __name__ == "__main__":
    system = platform.system()


    if system == "Darwin":
        shrink_rate = 1
        screen_size = [1920/shrink_rate, 720/shrink_rate]
        cluster_size /= shrink_rate

    app = Application()
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

        try:
            shutdown_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "down"], check=True)
            setup_can = subprocess.run(["sudo", "/sbin/ip", "link", "set", "can0", "up", "type", "can", "bitrate", "500000"], check=True)
            can_app = CanApplication()
        except:
            print("Could not find PiCan device! Quitting.")
            del app
            exit()

        can_app.updated.connect(app.updateVar)

        def read_can():
            msg = can_app.get_data()

            if msg is not None:
                can_app.parse_data(msg)

        def run():
            timer = QTimer(app)
            timer.timeout.connect(read_can)
            timer.start(0.01)

        app.awakened.connect(run)

    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
