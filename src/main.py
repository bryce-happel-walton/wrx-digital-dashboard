import sys
from math import cos, pi, sin, atan
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QFrame, QWidget
from PySide6.QtGui import QCursor, QTransform, QPainter, QFont
from PySide6.QtCore import Qt

screen_size = [1920, 720]
rpm_params = {
	"min": 0,
	"max": 8,
	"redline": 6.7,
	"sections": 10
}


class Line(QWidget):

	def __init__(self, parent, rect, translation, rotation, color):
		super().__init__(parent)
		self.resize(parent.frameGeometry().width(), parent.frameGeometry().height())
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


class main_window(QMainWindow):

	def __init__(self):
		super().__init__()

		self.setWindowTitle("Digital Cluster")
		self.setFixedSize(screen_size[0], screen_size[1])
		#self.showFullScreen()
		self.show()
		self.setFocus()

		self.rpm_labels = []
		self.make_left_guage(
			rpm_params["min"], rpm_params["max"], rpm_params["redline"], rpm_params["sections"])

	def make_left_guage(self, min, max, redline, sections):
		frame = QFrame(self)
		frame.setStyleSheet("background-color: black")
		frame.resize(500, 500)
		frame.show()

		label_size = [15, 15]
		rad_range = 2 * pi - pi / 2
		rad_offset = pi / 2 + (2 * pi - rad_range) / 2
		rad_step = rad_range / (max)
		rad_section_step = rad_step / sections

		buffer_radius = 50
		num_radius = 50
		section_radius = 20

		num_x_radius = frame.frameGeometry().width() / 2 - label_size[0] / 2 - buffer_radius - num_radius
		num_y_radius = frame.frameGeometry().height() / 2 - label_size[1] / 2 - buffer_radius - num_radius

		section_x_radius = frame.frameGeometry().width() / 2 - label_size[0] / 2 - buffer_radius - section_radius
		section_y_radius = frame.frameGeometry().height() / 2 - label_size[1] / 2 - buffer_radius - section_radius

		x_rad_offset = frame.frameGeometry().width() / 2 - label_size[0] / 2
		y_rad_offset = frame.frameGeometry().height() / 2 - label_size[1] / 2

		color = "white"

		for i in range(min, max + 1):
			label = QLabel(frame, text=f"{i}")
			label.resize(*label_size)
			label.setAutoFillBackground(False)
			label.setStyleSheet(f"color: {color}; background: transparent")
			label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
			label.move(
						cos(i * rad_step + rad_offset) * num_x_radius + x_rad_offset,
						sin(i * rad_step + rad_offset) * num_y_radius + y_rad_offset
					)
			label.show()

			for z in range(0, sections):
				x_radius = section_x_radius
				y_radius = section_y_radius
				if z == 0:
					x_radius -= 10
					y_radius -= 10

				line = Line(frame,
								(
									cos(i * rad_step + rad_offset + z * rad_section_step) * x_radius + x_rad_offset,
									sin(i * rad_step + rad_offset + z * rad_section_step) * y_radius + y_rad_offset,
									cos(i * rad_step + rad_offset + z * rad_section_step) * x_radius + x_rad_offset,
									sin(i * rad_step + rad_offset + z * rad_section_step) * y_radius + y_rad_offset
								),
								(0, 0), 0, color)

				line.show()

				if i == max:
					break

				if (i + (z+1)/sections) >= redline:
					color = "red"

				label.show()

if __name__ == "__main__":
	app = QApplication([])
	app.setOverrideCursor(QCursor(Qt.BlankCursor))
	window = main_window()
	sys.exit(app.exec())
