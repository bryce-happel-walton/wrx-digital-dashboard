import sys
from math import cos, pi, sin, atan
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QFrame, QWidget
from PySide6.QtGui import QCursor, QTransform, QPainter, QFont, QTextOption
from PySide6.QtCore import Qt, QRect

screen_size = [1920, 720]
rpm_params = {
	"min": 0,
	"max": 8,
	"redline": 6.7,
	"sections": 14
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


class Label(QWidget):

	def __init__(self, parent, text, position, rotation, color, font=None):
		super().__init__(parent)
		self.resize(parent.frameGeometry().width(), parent.frameGeometry().height())
		self.position = position
		self.rotation = rotation
		self.text = text
		self.color = color
		self.fontObj = font

	def paintEvent(self, event):
		painter = QPainter()
		painter.begin(self)
		painter.setBackgroundMode(Qt.TransparentMode)
		painter.setRenderHint(QPainter.Antialiasing)
		painter.setPen(self.color)

		if self.fontObj != None:
			painter.setFont(self.fontObj)

		painter.drawText(*self.position, self.text)


		painter.rotate(self.rotation)
		painter.end()


class RPMGuage(QWidget):

	def __init__(self, parent, min, max, redline, sections):
		super().__init__(parent)

		self.resize(500, 500)

		frame = QFrame(self)
		frame.setStyleSheet("background-color: black")
		frame.resize(500, 500)
		frame.show()

		rad_range = 2 * pi - pi / 2
		rad_offset = pi / 2 + (2 * pi - rad_range) / 2
		rad_step = rad_range / (max)
		rad_section_step = rad_step / sections

		buffer_radius = 20
		num_radius = 60
		section_radius = 20
		minor_section_rad_offset = 7
		middle_section_rad_offset = 43
		major_section_rad_offset = 38

		num_x_radius = frame.frameGeometry().width() / 2 - buffer_radius - num_radius
		num_y_radius = frame.frameGeometry().height() / 2 - buffer_radius - num_radius

		section_x_radius = frame.frameGeometry().width() / 2 - buffer_radius - section_radius
		section_y_radius = frame.frameGeometry().height() / 2 - buffer_radius - section_radius

		x_rad_offset = frame.frameGeometry().width() / 2
		y_rad_offset = frame.frameGeometry().height() / 2

		color = "white"

		label_font = QFont("Sans-serif", 14)

		for i in range(min, max + 1):
			label = Label(frame, f"{i}",
					(
						cos(i * rad_step + rad_offset) * num_x_radius + x_rad_offset - 4,
						sin(i * rad_step + rad_offset) * num_y_radius + y_rad_offset + 7
					),
					0,
					color,
					font=label_font
				)
			label.show()

			for z in range(0, sections):
				x_radius = section_x_radius
				y_radius = section_y_radius
				x_inner_radius = x_radius
				y_inner_radius = y_radius

				if z == 0:
					x_inner_radius -= num_radius - major_section_rad_offset
					y_inner_radius -= num_radius - major_section_rad_offset
				elif (sections % 2 == 0) and (z == sections/2):
					x_inner_radius -= num_radius - middle_section_rad_offset
					y_inner_radius -= num_radius - middle_section_rad_offset
				else:
					x_inner_radius -= minor_section_rad_offset
					y_inner_radius -= minor_section_rad_offset

				line = Line(frame,
								(
									cos(i * rad_step + rad_offset + z * rad_section_step) * x_radius + x_rad_offset,
									sin(i * rad_step + rad_offset + z * rad_section_step) * y_radius + y_rad_offset,
									cos(i * rad_step + rad_offset + z * rad_section_step) * x_inner_radius + x_rad_offset,
									sin(i * rad_step + rad_offset + z * rad_section_step) * y_inner_radius + y_rad_offset
								),
								(0, 0), 0, color)

				line.show()

				if i == max:
					break

				if (i + (z+1)/sections) >= redline:
					color = "red"

				label.show()


class MainWindow(QMainWindow):

	def __init__(self):
		super().__init__()

		self.setWindowTitle("Digital Cluster")
		self.setFixedSize(screen_size[0], screen_size[1])
		#self.showFullScreen()
		self.show()
		self.setFocus()

		self.rpm_guage = RPMGuage(self, rpm_params["min"], rpm_params["max"], rpm_params["redline"], rpm_params["sections"])
		self.rpm_guage.show()



class Application(QApplication):

	def __init__(self):
		super().__init__([])
		self.setOverrideCursor(QCursor(Qt.BlankCursor))
		self.primary_container = MainWindow()


if __name__ == "__main__":
	app = Application()
	sys.exit(app.exec())
