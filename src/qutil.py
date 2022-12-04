from PyQt5.QtGui import QColor, QImage, QPixmap, QColor, QTransform
from PyQt5.QtWidgets import QLabel, QWidget


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

