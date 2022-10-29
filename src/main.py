# formatted with yapf
# Bryce Happel Walton

from random import random, randrange
import sys
from math import ceil, cos, floor, pi, sin, atan, degrees
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QFrame, QWidget
from PySide6.QtGui import QCursor, QPainter, QFont
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from time import time

screen_size = [1920, 720]
rpm_params = {"min": 0, "max": 8000, "redline": 6700, "sections": 14}
speed_params = {
    "min": 0,
    "max": 180,
    "units": 1,  # 1: mph, 2: kph
    "sections": 4
}

cluster_size = 600


def clamp(low, n, high):
    return min(max(n, low), high)


class Line(QWidget):

    def __init__(self, parent, rect, translation, rotation, color):
        super().__init__(parent)
        self.resize(parent.frameGeometry().width(),
                    parent.frameGeometry().height())
        self.rect = rect
        self.parent = parent
        self.translation = translation
        self.rotation = rotation
        self.color = color

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setBackgroundMode(Qt.TransparentMode)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.color)
        painter.drawLine(*self.rect)
        painter.translate(*self.translation)
        painter.rotate(self.rotation)
        painter.end()


class Label(QWidget):

    def __init__(self, parent, text, position, rotation, color, font=None):
        super().__init__(parent)
        self.resize(parent.frameGeometry().width(),
                    parent.frameGeometry().height())
        self.position = position
        self.rotation = rotation
        self.text = text
        self.color = color
        self.fontObj = font
        self.painter = QPainter()

    def paintEvent(self, event):
        painter = self.painter
        painter.begin(self)
        painter.setBackgroundMode(Qt.TransparentMode)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.color)

        if self.fontObj != None:
            painter.setFont(self.fontObj)

        painter.drawText(*self.position, self.text)

        painter.rotate(self.rotation)
        painter.end()


class Tachometer(QWidget):

    def __init__(self, parent, min_rpm, max_rpm, redline, sections):
        super().__init__(parent)

        self.rpm = 0
        self.min_rpm = min_rpm
        self.max_rpm = max_rpm
        self.redline = redline
        self.rpm_range = max_rpm - min_rpm

        self.dial_opacity = "30%"
        self.border_opacity = "60%"

        self.dial_color = f"rgba(255, 255, 255, {self.dial_opacity})"
        self.dial_top_color = f"rgba(255, 255, 255, {self.border_opacity})"
        self.dial_redline_color = f"rgba(255, 0, 0, {self.dial_opacity})"
        self.dial_top_redline_color = f"rgba(255, 0, 0, {self.border_opacity})"

        visual_min_rpm = floor(min_rpm / 1000)
        visual_max_rpm = ceil(max_rpm / 1000)

        self.resize(cluster_size, cluster_size)

        frame = QFrame(self)
        frame.setStyleSheet("background-color: black; border-radius: 300px")
        frame.resize(self.frameGeometry().size())
        frame.show()

        rad_range = 2 * pi - pi / 2
        self.rad_range_a = rad_range / (2 * pi)
        rad_offset = pi / 2 + (2 * pi - rad_range) / 2
        self.dial_offset_angle = rad_offset
        rad_step = rad_range / visual_max_rpm
        rad_section_step = rad_step / sections

        buffer_radius = 20
        num_radius = 43
        section_radius = 20
        minor_section_rad_offset = 3
        middle_section_rad_offset = 36
        major_section_rad_offset = 33
        dial_mask_rad = 300
        dial_inner_border_rad = dial_mask_rad + 8

        num_x_radius = frame.frameGeometry().width(
        ) / 2 - buffer_radius - num_radius
        num_y_radius = frame.frameGeometry().height(
        ) / 2 - buffer_radius - num_radius

        section_x_radius = frame.frameGeometry().width(
        ) / 2 - buffer_radius - section_radius
        section_y_radius = frame.frameGeometry().height(
        ) / 2 - buffer_radius - section_radius

        x_rad_offset = frame.frameGeometry().width() / 2
        y_rad_offset = frame.frameGeometry().height() / 2

        color = "white"
        label_font = QFont("Sans-serif", 17)

        rpm_dial = QFrame(self)
        rpm_dial.resize(section_x_radius + x_rad_offset - section_radius * 2,
                        section_y_radius + y_rad_offset - section_radius * 2)
        rpm_dial.move(x_rad_offset - rpm_dial.frameGeometry().width() / 2,
                      y_rad_offset - rpm_dial.frameGeometry().height() / 2)
        rpm_dial.show()

        rpm_dial_top = QFrame(self)
        rpm_dial_top.resize(rpm_dial.frameGeometry().size())
        rpm_dial_top.move(
            x_rad_offset - rpm_dial_top.frameGeometry().width() / 2,
            y_rad_offset - rpm_dial_top.frameGeometry().height() / 2)
        rpm_dial_top.show()

        rpm_dial_inner_border = QFrame(self)
        rpm_dial_inner_border.resize(dial_inner_border_rad,
                                     dial_inner_border_rad)
        rpm_dial_inner_border.move(
            x_rad_offset - rpm_dial_inner_border.frameGeometry().width() / 2,
            y_rad_offset - rpm_dial_inner_border.frameGeometry().height() / 2)
        rpm_dial_inner_border.show()

        self.rpm_dial_inner_border = rpm_dial_inner_border
        rpm_dial_mask = QFrame(self)
        rpm_dial_mask.resize(dial_mask_rad, dial_mask_rad)
        rpm_dial_mask.move(
            x_rad_offset - rpm_dial_mask.frameGeometry().width() / 2,
            y_rad_offset - rpm_dial_mask.frameGeometry().height() / 2)
        rpm_dial_mask.setStyleSheet(
            f"background-color: rgb(0, 0, 0); border-radius: {int(rpm_dial_mask.geometry().width()/2)}px"
        )
        rpm_dial_mask.show()

        self.rpm_dial = rpm_dial
        self.rpm_dial_top = rpm_dial_top

        self.dial_corner_radius = int(self.rpm_dial.geometry().width() / 2)
        self.rpm_dial_inner_border_radius = int(
            self.rpm_dial_inner_border.geometry().width() / 2)

        for i in range(visual_min_rpm, visual_max_rpm + 1):
            label = Label(
                frame,
                f"{i}",
                (cos(i * rad_step + rad_offset) * num_x_radius + x_rad_offset -
                 4, sin(i * rad_step + rad_offset) * num_y_radius +
                 y_rad_offset + 7),
                0,
                color,
                font=label_font)
            label.show()

            for z in range(0, sections):
                x_radius = section_x_radius
                y_radius = section_y_radius
                x_inner_radius = x_radius
                y_inner_radius = y_radius

                if z == 0:
                    x_inner_radius -= num_radius - major_section_rad_offset
                    y_inner_radius -= num_radius - major_section_rad_offset
                elif (sections % 2 == 0) and (z == sections / 2):
                    x_inner_radius -= num_radius - middle_section_rad_offset
                    y_inner_radius -= num_radius - middle_section_rad_offset
                else:
                    x_inner_radius -= minor_section_rad_offset
                    y_inner_radius -= minor_section_rad_offset

                x_inner_radius = min(x_inner_radius,
                                     x_radius - minor_section_rad_offset)
                y_inner_radius = min(y_inner_radius,
                                     y_radius - minor_section_rad_offset)

                line = Line(
                    frame,
                    (cos(i * rad_step + rad_offset + z * rad_section_step) *
                     x_radius + x_rad_offset,
                     sin(i * rad_step + rad_offset + z * rad_section_step) *
                     y_radius + y_rad_offset,
                     cos(i * rad_step + rad_offset + z * rad_section_step) *
                     x_inner_radius + x_rad_offset,
                     sin(i * rad_step + rad_offset + z * rad_section_step) *
                     y_inner_radius + y_rad_offset), (0, 0), 0, color)

                line.show()

                if i == visual_max_rpm:
                    break

                if (i + (z + 1) / sections) >= redline / 1000:
                    color = "red"

                label.show()

    def setDial(self, alpha):
        alpha = clamp(0, alpha, 1)
        self.setRPM(ceil(alpha * (self.max_rpm - self.min_rpm)))

    def setRPM(self, value):
        self.rpm = value
        self.updateRPM()

    def updateRPM(self):
        rpm = self.rpm

        offset_deg = degrees(self.dial_offset_angle)

        angle_step = offset_deg / self.max_rpm
        angle2 = offset_deg + 90 - rpm * angle_step * 2

        color = self.dial_color
        color2 = self.dial_top_color

        if rpm >= self.redline:
            color = self.dial_redline_color
            color2 = self.dial_top_redline_color

        rpm = self.max_rpm - rpm * self.rad_range_a

        if rpm > 0:
            rpm_a = rpm / self.rpm_range
        else:
            rpm_a = self.max_rpm

        stop_1 = max(rpm_a - 0.001, 0)
        stop_2 = rpm_a
        angle = offset_deg + 90

        if rpm_a == 1:
            stop_1 = 1 - 0.001
            stop_2 = 1

        self.rpm_dial.setStyleSheet(
            f"border-radius: {self.dial_corner_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle}, stop:{stop_1} rgba(255, 255, 255, 0%), stop:{stop_2} {color});"
        )

        self.rpm_dial_inner_border.setStyleSheet(
            f"border-radius: {self.rpm_dial_inner_border_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle}, stop:{stop_1} rgba(255, 255, 255, 0%), stop:{stop_2} {color2});"
        )

        self.rpm_dial_top.setStyleSheet(
            f"border-radius: {self.dial_corner_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle2}, stop:0.995 rgba(255, 255, 255, 0%), stop:1 {color2});"
        )


# todo: update speedometer to new tach spec
class Speedometer(QWidget):

    def __init__(self, parent, min_speed, max_speed, sections, units=1):
        super().__init__(parent)

        self.speed = 0
        self.min_speed = floor(min_speed)
        self.max_speed = ceil(max_speed)
        self.units = 1

        visual_min_speed = floor(min_speed / 10)
        visual_max_speed = ceil(max_speed / 10)

        self.resize(cluster_size, cluster_size)

        frame = QFrame(self)
        frame.setStyleSheet("background-color: black")
        frame.resize(self.frameGeometry().width(),
                     self.frameGeometry().height())
        frame.show()

        rad_range = 2 * pi - pi / 2
        rad_offset = pi / 2 + (2 * pi - rad_range) / 2
        rad_step = rad_range / visual_max_speed
        rad_section_step = rad_step / sections

        buffer_radius = 20
        num_radius = 55
        section_radius = 20
        minor_section_rad_offset = 3
        middle_section_rad_offset = 50
        major_section_rad_offset = 44
        dial_inner_rad = 60

        num_x_radius = frame.frameGeometry().width(
        ) / 2 - buffer_radius - num_radius
        num_y_radius = frame.frameGeometry().height(
        ) / 2 - buffer_radius - num_radius

        section_x_radius = frame.frameGeometry().width(
        ) / 2 - buffer_radius - section_radius
        section_y_radius = frame.frameGeometry().height(
        ) / 2 - buffer_radius - section_radius

        x_rad_offset = frame.frameGeometry().width() / 2
        y_rad_offset = frame.frameGeometry().height() / 2

        color = "white"
        label_font = QFont("Sans-serif", 14)

        rpm_label = QLabel(f"{self.speed}", frame)
        rpm_label.resize(200, 50)
        rpm_label.move(x_rad_offset - 200 / 2, y_rad_offset - 50 / 2)
        rpm_label.setStyleSheet("color: white")
        rpm_label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        rpm_label.setFont(label_font)
        rpm_label.show()
        self.speed_label = rpm_label

        rpm_dial = Line(
            frame,
            (cos(0 * rad_step + rad_offset) * section_x_radius + x_rad_offset,
             sin(0 * rad_step + rad_offset) * section_y_radius + y_rad_offset,
             cos(0 * rad_step + rad_offset) * dial_inner_rad + x_rad_offset,
             sin(0 * rad_step + rad_offset) * dial_inner_rad + y_rad_offset),
            (0, 0), 0, color)

        rpm_dial.show()

        for i in range(visual_min_speed, visual_max_speed + 1):
            label = Label(
                frame,
                f"{i * 10}",
                (cos(i * rad_step + rad_offset) * num_x_radius + x_rad_offset -
                 16, sin(i * rad_step + rad_offset) * num_y_radius +
                 y_rad_offset + 3),
                0,
                color,
                font=label_font)
            label.show()

            for z in range(0, sections):
                x_radius = section_x_radius
                y_radius = section_y_radius
                x_inner_radius = x_radius
                y_inner_radius = y_radius

                if z == 0:
                    x_inner_radius -= num_radius - major_section_rad_offset
                    y_inner_radius -= num_radius - major_section_rad_offset
                elif (sections % 2 == 0) and (z == sections / 2):
                    x_inner_radius -= num_radius - middle_section_rad_offset
                    y_inner_radius -= num_radius - middle_section_rad_offset
                else:
                    x_inner_radius -= minor_section_rad_offset
                    y_inner_radius -= minor_section_rad_offset

                x_inner_radius = min(x_inner_radius,
                                     x_radius - minor_section_rad_offset)
                y_inner_radius = min(y_inner_radius,
                                     y_radius - minor_section_rad_offset)

                line = Line(
                    frame,
                    (cos(i * rad_step + rad_offset + z * rad_section_step) *
                     x_radius + x_rad_offset,
                     sin(i * rad_step + rad_offset + z * rad_section_step) *
                     y_radius + y_rad_offset,
                     cos(i * rad_step + rad_offset + z * rad_section_step) *
                     x_inner_radius + x_rad_offset,
                     sin(i * rad_step + rad_offset + z * rad_section_step) *
                     y_inner_radius + y_rad_offset), (0, 0), 0, color)

                line.show()

                if i == visual_max_speed:
                    break

                label.show()

    def setDial(self, alpha):
        alpha = clamp(0, alpha, 1)
        self.setSpeed(alpha * (self.max_speed - self.min_speed))

    def setSpeed(self, value):
        self.speed = value
        self.updateSpeed()

    def updateSpeed(self):
        self.speed_label.setText(f"{self.speed:.0f}")


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Digital Cluster")

        rpm_gauge = Tachometer(self, rpm_params["min"], rpm_params["max"],
                               rpm_params["redline"], rpm_params["sections"])
        rpm_gauge.move(0 + cluster_size / 4,
                       screen_size[1] / 2 - cluster_size / 2)
        rpm_gauge.show()
        self.tachometer = rpm_gauge

        speed_gauge = Speedometer(self, speed_params["min"],
                                  speed_params["max"],
                                  speed_params["sections"],
                                  speed_params["units"])
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
    if len(screens) > 1: # If I have the dashboard display connected to my PC then this will automatically switch for me
        screen = screens[1]
        app.primary_container.setScreen(screen)
        app.primary_container.move(screen.geometry().topLeft())
        app.primary_container.showFullScreen()
    else:
        app.primary_container.setFixedSize(screen_size[0], screen_size[1])

    app.primary_container.show()
    app.primary_container.setFocus()
    sys.exit(app.exec())
