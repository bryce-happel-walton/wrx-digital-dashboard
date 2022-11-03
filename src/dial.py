from math import ceil, cos, degrees, floor, pi, sin

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPalette
from PySide6.QtWidgets import QFrame, QLabel, QWidget

#todo: make resize event redraw everything
#todo: make updating center label with unit


def clamp(low, n, high):
    return min(max(n, low), high)


class Line(QWidget):

    def __init__(self, parent, rect, color):
        super().__init__(parent)
        self.resize(parent.frameGeometry().width(),
                    parent.frameGeometry().height())
        self.rect = rect
        self.parent = parent
        self.color = color

    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setBackgroundMode(Qt.TransparentMode)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(self.color)
        painter.drawLine(*self.rect)
        painter.end()


class Dial(QWidget):

    def __init__(self,
                 parent,
                 min_unit=0,
                 max_unit=1,
                 redline=0.5,
                 mid_sections=2,
                 size=500,
                 label_font=QFont("Sans-serif", 17),
                 default_color=(255, 255, 255),
                 redline_color=(255, 0, 0),
                 background_color=(0, 0, 0),
                 dial_opacity="30%",
                 border_opacity="60%",
                 units="",
                 denomination=1,
                 visual_num_gap=1,
                 buffer_radius=20,
                 num_radius=54,
                 section_radius=20,
                 minor_section_rad_offset=3,
                 middle_section_rad_offset=43,
                 major_section_rad_offset=40,
                 dial_mask_rad=290,
                 dial_inner_border_rad=4,
                 angle_offset=0):
        super().__init__(parent)

        visual_min_unit = floor(min_unit / visual_num_gap)
        visual_max_unit = ceil(max_unit / visual_num_gap)

        self.unit = 0
        self.min_unit = min_unit
        self.max_unit = max_unit
        self.redline = redline
        self.unit_range = max_unit - min_unit

        self.dial_opacity = dial_opacity
        self.border_opacity = border_opacity

        self.dial_color = f"rgba({default_color[0]}, {default_color[1]}, {default_color[2]}, {self.dial_opacity})"
        self.dial_top_color = f"rgba({default_color[0]}, {default_color[1]}, {default_color[2]}, {self.border_opacity})"
        self.dial_redline_color = f"rgba({redline_color[0]}, {redline_color[1]}, {redline_color[2]}, {self.dial_opacity})"
        self.dial_top_redline_color = f"rgba({redline_color[0]}, {redline_color[1]}, {redline_color[2]}, {self.border_opacity})"

        self.label_font = label_font

        self.resize(size, size)

        frame = QFrame(self)
        frame.setStyleSheet(
            f"background-color: rgb({background_color[0]}, {background_color[1]}, {background_color[2]}); border-radius: {int(size/2)}px"
        )
        frame.resize(self.geometry().size())
        frame.show()
        self.frame = frame

        rad_range = 2 * pi - pi / 2
        rad_offset = pi / 2 + (2 * pi - rad_range) / 2 + angle_offset
        rad_step = rad_range / visual_max_unit
        rad_section_step = rad_step / mid_sections

        self.rad_range_a = rad_range / (2 * pi)
        self.dial_offset_angle = rad_offset

        dial_inner_border_rad = dial_mask_rad + dial_inner_border_rad

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

        unit_dial = QFrame(frame)
        unit_dial.resize(section_x_radius + x_rad_offset - section_radius * 2,
                         section_y_radius + y_rad_offset - section_radius * 2)
        unit_dial.move(x_rad_offset - unit_dial.frameGeometry().width() / 2,
                       y_rad_offset - unit_dial.frameGeometry().height() / 2)
        unit_dial.show()

        unit_dial_top = QFrame(frame)
        unit_dial_top.resize(unit_dial.frameGeometry().size())
        unit_dial_top.move(
            x_rad_offset - unit_dial_top.frameGeometry().width() / 2,
            y_rad_offset - unit_dial_top.frameGeometry().height() / 2)
        unit_dial_top.show()

        unit_dial_inner_border = QFrame(frame)
        unit_dial_inner_border.resize(dial_inner_border_rad,
                                      dial_inner_border_rad)
        unit_dial_inner_border.move(
            x_rad_offset - unit_dial_inner_border.frameGeometry().width() / 2,
            y_rad_offset - unit_dial_inner_border.frameGeometry().height() / 2)
        unit_dial_inner_border.show()

        unit_dial_mask = QFrame(frame)
        unit_dial_mask.resize(dial_mask_rad, dial_mask_rad)
        unit_dial_mask.move(
            x_rad_offset - unit_dial_mask.frameGeometry().width() / 2,
            y_rad_offset - unit_dial_mask.frameGeometry().height() / 2)
        unit_dial_mask.setStyleSheet(
            f"background-color: rgb({background_color[0]}, {background_color[1]}, {background_color[2]}); border-radius: {int(unit_dial_mask.geometry().width()/2)}px"
        )
        unit_dial_mask.show()

        self.unit_dial_inner_border = unit_dial_inner_border
        self.unit_dial = unit_dial
        self.unit_dial_top = unit_dial_top

        self.dial_corner_radius = int(self.unit_dial.geometry().width() / 2)
        self.unit_dial_inner_border_radius = int(
            self.unit_dial_inner_border.geometry().width() / 2)

        color = QColor(*default_color)
        readline_drawn = False

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.WindowText, color)

        for i in range(visual_min_unit, visual_max_unit + 1):
            label = QLabel(f"{int(i * visual_num_gap / denomination)}", frame)
            label.setStyleSheet("background:transparent")
            label.setPalette(palette)
            label.setFont(label_font)
            label.show()
            label.move(
                cos(i * rad_step + rad_offset) * num_x_radius + x_rad_offset -
                label.geometry().width() / 2,
                sin(i * rad_step + rad_offset) * num_y_radius + y_rad_offset -
                label.geometry().height() / 2)


            for z in range(0, mid_sections):
                x_radius = x_inner_radius = section_x_radius
                y_radius = y_inner_radius = section_y_radius

                if z == 0:
                    x_inner_radius -= num_radius - major_section_rad_offset
                    y_inner_radius -= num_radius - major_section_rad_offset
                elif (mid_sections % 2 == 0) and (z == mid_sections / 2):
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
                     y_inner_radius + y_rad_offset), color)

                line.show()

                if i == visual_max_unit:
                    break

                if not readline_drawn and (
                        i + (z + 1) / mid_sections) >= redline / denomination:
                    readline_drawn = True
                    color = QColor(*redline_color)
                    palette.setColor(QPalette.ColorRole.WindowText, color)

                label.show()

    def setDial(self, alpha):
        alpha = clamp(0, alpha, 1)
        self.setRPM(ceil(alpha * (self.max_unit - self.min_unit)))

    def setRPM(self, value):
        self.unit = value
        self.updateRPM()

    def updateRPM(self):
        current_unit = self.unit

        offset_deg = degrees(self.dial_offset_angle)

        angle_step = offset_deg / self.max_unit
        angle2 = offset_deg + 90 - current_unit * angle_step * 2

        color = self.dial_color
        color2 = self.dial_top_color

        if current_unit >= self.redline:
            color = self.dial_redline_color
            color2 = self.dial_top_redline_color

        current_unit = self.max_unit - current_unit * self.rad_range_a

        if current_unit > 0:
            unit_alpha = current_unit / self.unit_range
        else:
            unit_alpha = self.max_unit

        stop_1 = max(unit_alpha - 0.001, 0)
        stop_2 = unit_alpha
        angle = offset_deg + 90

        if unit_alpha == 1:
            stop_1 = 1 - 0.001
            stop_2 = 1

        self.unit_dial.setStyleSheet(
            f"border-radius: {self.dial_corner_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle}, stop:{stop_1} rgba(255, 255, 255, 0%), stop:{stop_2} {color});"
        )

        self.unit_dial_inner_border.setStyleSheet(
            f"border-radius: {self.unit_dial_inner_border_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle}, stop:{stop_1} rgba(255, 255, 255, 0%), stop:{stop_2} {color2});"
        )

        self.unit_dial_top.setStyleSheet(
            f"border-radius: {self.dial_corner_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle2}, stop:0.995 rgba(255, 255, 255, 0%), stop:1 {color2});"
        )
