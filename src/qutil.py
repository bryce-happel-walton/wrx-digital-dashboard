from math import ceil
from PyQt5.QtGui import QColor, QImage, QPixmap, QColor, QTransform
from PyQt5.QtWidgets import QLabel, QWidget
import PyQt5.QtGui as QtGui
from PyQt5.QtCore import QRectF, QSize, QLineF, QLine, Qt, pyqtProperty
from PyQt5.QtGui import QColor, QPainter, QPen, QPaintEvent, QGradient
from PyQt5.QtWidgets import QLabel, QWidget

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

        image = QImage(image_path)
        if color:
            change_image_color(image, color)

        pixmap = QPixmap.fromImage(image)
        if transform:
            pixmap = pixmap.transformed(transform)

        self.setPixmap(pixmap)
        self.setStyleSheet("background:transparent")
        self.setScaledContents(True)


class Line(QWidget):

    painter = QPainter()

    def __init__(self, parent: QWidget, line: QLineF | QLine, color: QColor | QGradient, width: float = 1) -> None:
        super().__init__(parent)
        self.resize(parent.size().width(), parent.size().height())
        self.line = line
        self.color = color
        self.pen = QPen(color, width)
        self.pen.setCapStyle(Qt.RoundCap)

    def setLine(self, line: QLineF | QLine) -> None:
        self.line = line
        self.update()

    def setColor(self, color: QColor | QGradient) -> None:
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
        self._arc_start = self._arc_end = 0

    @pyqtProperty(float)
    def arc_start(self):
        return self._arc_start

    @pyqtProperty(float)
    def arc_end(self):
        return self._arc_end

    @arc_start.setter
    def arc_start(self, val: float):
        self._arc_start = int(val * Q_DEGREE_MULT)

    @arc_end.setter
    def arc_end(self, val: float):
        self._arc_end = int(val * Q_DEGREE_MULT)

    def setColor(self, color: QColor | QGradient) -> None:
        self.pen.setColor(color)

    def setArc(self, start: float, end: float) -> None:
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
