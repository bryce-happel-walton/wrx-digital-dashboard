from random import random, randrange
import sys
from math import ceil, cos, floor, pi, sin, atan
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QFrame, QWidget
from PySide6.QtGui import QCursor, QPainter, QFont
from PySide6.QtCore import Qt, QTimer

screen_size = [1920, 720]
rpm_params = {
	"min": 0,
	"max": 8000,
	"redline": 6700,
	"sections": 14
}


def clamp(low, n, high):
	return min(max(n, low), high)


def rotate(origin, point, angle):
    ox, oy = origin
    px, py = point

    qx = ox + cos(angle) * (px - ox) - sin(angle) * (py - oy)
    qy = oy + sin(angle) * (px - ox) + cos(angle) * (py - oy)
    return qx, qy


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


class RPMGauge(QWidget):

	def __init__(self, parent, min_rpm, max_rpm, redline, sections):
		super().__init__(parent)

		self.rpm = 0
		self.min_rpm = min_rpm
		self.max_rpm = max_rpm
		self.redline = redline

		visual_min_rpm = floor(min_rpm / 1000)
		visual_max_rpm = ceil(max_rpm / 1000)

		self.resize(500, 500)

		frame = QFrame(self)
		frame.setStyleSheet("background-color: black")
		frame.resize(self.frameGeometry().width(), self.frameGeometry().height())
		frame.show()

		rad_range = 2 * pi - pi / 2
		rad_offset = pi / 2 + (2 * pi - rad_range) / 2
		rad_step = rad_range / visual_max_rpm
		rad_section_step = rad_step / sections

		buffer_radius = 20
		num_radius = 43
		section_radius = 20
		minor_section_rad_offset = 3
		middle_section_rad_offset = 36
		major_section_rad_offset = 33
		dial_inner_rad = 60

		num_x_radius = frame.frameGeometry().width() / 2 - buffer_radius - num_radius
		num_y_radius = frame.frameGeometry().height() / 2 - buffer_radius - num_radius

		section_x_radius = frame.frameGeometry().width() / 2 - buffer_radius - section_radius
		section_y_radius = frame.frameGeometry().height() / 2 - buffer_radius - section_radius

		x_rad_offset = frame.frameGeometry().width() / 2
		y_rad_offset = frame.frameGeometry().height() / 2


		color = "white"
		label_font = QFont("Sans-serif", 14)

		rpm_label = QLabel(f"{self.rpm}", frame)
		rpm_label.resize(200, 50)
		rpm_label.move(x_rad_offset - 200/2, y_rad_offset - 50/2)
		rpm_label.setStyleSheet("color: white")
		rpm_label.setAlignment(Qt.AlignHCenter| Qt.AlignVCenter)
		rpm_label.setFont(label_font)
		rpm_label.show()
		self.rpm_label = rpm_label

		rpm_dial = Line(frame,
						(
							cos(0 * rad_step + rad_offset) * section_x_radius + x_rad_offset,
							sin(0 * rad_step + rad_offset) * section_y_radius + y_rad_offset,
							cos(0 * rad_step + rad_offset) * dial_inner_rad + x_rad_offset,
							sin(0 * rad_step + rad_offset) * dial_inner_rad + y_rad_offset
						),
						(0, 0),
						0,
						color
					)

		rpm_dial.show()

		for i in range(visual_min_rpm, visual_max_rpm + 1):
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

				x_inner_radius = min(x_inner_radius, x_radius - minor_section_rad_offset)
				y_inner_radius = min(y_inner_radius, y_radius - minor_section_rad_offset)

				line = Line(frame,
								(
									cos(i * rad_step + rad_offset + z * rad_section_step) * x_radius + x_rad_offset,
									sin(i * rad_step + rad_offset + z * rad_section_step) * y_radius + y_rad_offset,
									cos(i * rad_step + rad_offset + z * rad_section_step) * x_inner_radius + x_rad_offset,
									sin(i * rad_step + rad_offset + z * rad_section_step) * y_inner_radius + y_rad_offset
								),
								(0, 0), 0, color)

				line.show()

				if i == visual_max_rpm:
					break

				if (i + (z+1)/sections) >= redline / 1000:
					color = "red"

				label.show()

	def setDial(self, alpha):
		alpha = clamp(0, alpha, 1)
		self.setRPM(alpha * (self.max_rpm - self.min_rpm))

	def setRPM(self, value):
		self.rpm = value
		self.updateRPM()

	def updateRPM(self):
		self.rpm_label.setText(f"{self.rpm:.0f}")


class MainWindow(QMainWindow):

	def __init__(self):
		super().__init__()

		self.setWindowTitle("Digital Cluster")
		#self.setFixedSize(screen_size[0], screen_size[1])
		self.showFullScreen()
		self.show()
		self.setFocus()

		rpm_gauge = RPMGauge(self, rpm_params["min"], rpm_params["max"], rpm_params["redline"], rpm_params["sections"])
		rpm_gauge.move(1920 - 500 - 500/4, 500/4)
		rpm_gauge.show()
		self.rpm_gauge = rpm_gauge

class Application(QApplication):

	def __init__(self):
		super().__init__([])
		self.setOverrideCursor(QCursor(Qt.BlankCursor))
		primary_container =  MainWindow()
		timer = QTimer()

		#timer.timeout.connect(self.clusterUpdate)
		#timer.start(100)

		self.awaken_sequence_duration_ms = 1000
		self.awaken_sequence_step_ms = 1

		self.timer = timer
		self.primary_container = primary_container

		self.awaken_cluster()

	def awaken_cluster(self):
		timer = QTimer()

		self._awaken_a = 0
		a_step = self.awaken_sequence_step_ms / self.awaken_sequence_duration_ms
		self._awaken_t = 0

		def dialMove():
			self._awaken_t += self.awaken_sequence_step_ms
			if self._awaken_t >= self.awaken_sequence_duration_ms:
				timer.stop()
			elif self._awaken_t >= self.awaken_sequence_duration_ms / 2:
				self._awaken_a -= a_step * 2
			else:
				self._awaken_a += a_step * 2

			self.primary_container.rpm_gauge.setDial(self._awaken_a)


		timer.timeout.connect(dialMove)
		timer.start(self.awaken_sequence_step_ms)

	def clusterUpdate(self):
		self.primary_container.rpm_gauge.setRPM(randrange(0, 8000))


if __name__ == "__main__":
	app = Application()
	sys.exit(app.exec())
