import PyQt5.QtGui as QtGui
from math import ceil
from time import time
from typing import Any, Callable
from PyQt5.QtGui import QImage, QPixmap, QTransform, QColor, QPainter, QPen, QPaintEvent, QGradient
from PyQt5.QtWidgets import QLabel, QWidget, QApplication
from PyQt5.QtCore import QRectF, QSize, QLineF, QLine, Qt, pyqtProperty, QTimer, QPropertyAnimation, QObject

Q_DEGREE_MULT = 16


def change_image_color(image: QImage, color: QColor) -> None:
    for x in range(image.width()):
        for y in range(image.height()):
            pcolor = image.pixelColor(x, y)
            if pcolor.alpha() > 0:
                n_color = QColor(color)
                n_color.setAlpha(pcolor.alpha())
                image.setPixelColor(x, y, n_color)


class Image(QLabel):

    def __init__(self, parent: QWidget, image_path: str, color: QColor = None, transform: QTransform = None):
        super().__init__(parent)

        self.transform = transform

        self.image = QImage(image_path)
        if color:
            change_image_color(self.image, color)

        self.setStyleSheet("background:transparent")
        self.setScaledContents(True)
        self.update()

    def set_color(self, color: QColor) -> None:
        change_image_color(self.image, color)
        self.update()

    def update(self) -> None:
        self.pixmap = QPixmap.fromImage(self.image)
        if self.transform:
            self.pixmap = self.pixmap.transformed(self.transform)
        self.setPixmap(self.pixmap)


class Line(QWidget):

    painter = QPainter()

    def __init__(self, parent: QWidget, line: QLineF | QLine, color: QColor | QGradient, width: float = 1) -> None:
        super().__init__(parent)
        self.resize(parent.width(), parent.height())
        self.line = line
        self.color = color
        self.pen = QPen(color, width)
        self.pen.setCapStyle(Qt.RoundCap)

    def set_line(self, line: QLineF | QLine) -> None:
        self.line = line
        self.update()

    def set_color(self, color: QColor | QGradient) -> None:
        self.pen.setColor(color)
        self.update()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        painter = self.painter
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.pen)
        painter.drawLine(self.line)
        painter.end()


class Arc(QWidget):

    painter = QPainter()

    def __init__(self, parent: QWidget, size: QSize, color: QColor = QColor(0, 255, 0), width: float = 15) -> None:
        super().__init__(parent)
        self.resize(size)
        self.pen = QPen(color, width)
        self.pen.setCapStyle(Qt.FlatCap)
        self.arc_edge_offest = ceil(width / 2)
        self.size_x = size.width() - width

    @pyqtProperty(float)
    def arc_start(self) -> float:
        return self._arc_start

    @pyqtProperty(float)
    def arc_end(self) -> float:
        return self._arc_end

    @arc_start.setter
    def arc_start(self, val: float) -> None:
        self._arc_start = int(val * Q_DEGREE_MULT)

    @arc_end.setter
    def arc_end(self, val: float) -> None:
        self._arc_end = int(val * Q_DEGREE_MULT)

    def set_color(self, color: QColor | QGradient) -> None:
        self.pen.setColor(color)

    def set_arc(self, start: float, end: float) -> None:
        self._arc_start = int(start * Q_DEGREE_MULT)
        self._arc_end = int(end * Q_DEGREE_MULT)
        self.update()

    def paintEvent(self, a0: QPaintEvent) -> None:
        painter = self.painter
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.pen)
        painter.drawArc(QRectF(self.arc_edge_offest, self.arc_edge_offest, self.size_x, self.size_x), self._arc_start,
                        self._arc_end)
        painter.end()


def delay(app: QApplication, f: Callable, delay_s: float) -> QTimer:
    start_time = time()
    t = QTimer(app)

    def timed_func():
        if time() - start_time >= delay_s:
            t.stop()
            t.deleteLater()
            f()

    t.timeout.connect(timed_func)
    t.start(1)


def timed_func(app: QApplication, f: Callable, delay_ms: int) -> QTimer:
    t = QTimer(app)
    t.timeout.connect(f)
    t.start(delay_ms)


def property_animation(app: QApplication, target_object: QObject, property_name: str, start_val: Any, end_val: Any,
                       duration_ms: int) -> QPropertyAnimation:
    property_animation_obj = QPropertyAnimation(app)
    property_animation_obj.setTargetObject(target_object)
    property_animation_obj.setPropertyName(property_name.encode("utf-8"))
    property_animation_obj.setStartValue(start_val)
    property_animation_obj.setEndValue(end_val)
    property_animation_obj.setDuration(duration_ms)
    return property_animation_obj
