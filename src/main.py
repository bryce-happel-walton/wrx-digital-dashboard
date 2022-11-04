# formatted with yapf
# Bryce Happel Walton

import sys
from math import pi
from random import random
from time import time

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCursor, QFont
from PySide6.QtWidgets import QApplication, QMainWindow

from dial import Dial

screen_size = [1920, 720]
rpm_params = {
    "min": 0,
    "max": 8000,
    "redline": 6700,
    "mid_sections": 14,
    "denomination": 1000
}
speed_params = {"min": 0, "max": 180, "units": "MPH", "mid_sections": 10}

cluster_size = 600


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Digital Cluster")

        font_group = "Yu Gothic UI"

        rpm_gauge = Dial(self,
                         size=cluster_size,
                         min_unit=rpm_params["min"],
                         max_unit=rpm_params["max"],
                         redline=rpm_params["redline"],
                         mid_sections=rpm_params["mid_sections"],
                         denomination=rpm_params["denomination"],
                         visual_num_gap=rpm_params["denomination"],
                         label_font=QFont(f"{font_group}", 22, 600),
                         angle_offset=pi,
                         angle_range=2 * pi - pi / 2)

        rpm_gauge.move(0 + cluster_size / 4,
                       screen_size[1] / 2 - cluster_size / 2)

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
                           label_font=QFont(f"{font_group}", 17, 600),
                           angle_offset=pi,
                           angle_range=2 * pi - pi / 2)

        speed_gauge.move(1920 - cluster_size - cluster_size / 4,
                         screen_size[1] / 2 - cluster_size / 2)
        speed_gauge.show()

        self.speedometer = speed_gauge


class Application(QApplication):

    awakened = Signal()
    started = Signal()

    def __init__(self):
        super().__init__([])
        self.setOverrideCursor(QCursor(Qt.BlankCursor))
        primary_container = MainWindow()

        self.start_time = time()

        self.awaken_sequence_duration_ms = 2500
        self.awaken_sequence_steps = 2000
        self.primary_container = primary_container

        self.awaken_clusters()
        self.awakened.connect(self.start)

    @Slot()
    def start(self):
        print(time() - self.start_time)
        self.primary_container.tachometer.setDial(1)
        self.primary_container.speedometer.setDial(1)

        timer = QTimer()

        start = time()

        def clusterHeck():
            if time() - start > 5:
                timer.stop()
                timer.deleteLater()
            self.clusterUpdate()

        timer.timeout.connect(clusterHeck)
        timer.start(100)

    def awaken_clusters(self):
        timer = QTimer()

        self._awaken_a = 0
        self._awaken_t = 0

        t_step = self.awaken_sequence_duration_ms / self.awaken_sequence_steps
        a_step = t_step / self.awaken_sequence_duration_ms

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

    @Slot()
    def clusterUpdate(self):
        self.primary_container.tachometer.setDial(random())
        self.primary_container.speedometer.setDial(random())


if __name__ == "__main__":
    app = Application()

    screens = app.screens()
    # If I have the dashboard display connected to my PC then this will automatically switch for me
    if len(screens) > 1:
        screen = screens[1]
        app.primary_container.setScreen(screen)
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
    else:
        app.primary_container.setFixedSize(screen_size[0], screen_size[1])

    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
