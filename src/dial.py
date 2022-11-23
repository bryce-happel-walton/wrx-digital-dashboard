from math import ceil, cos, degrees, floor, pi, sin
from util import clamp

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter, QPalette
from PyQt5.QtWidgets import QFrame, QLabel, QWidget

#todo: make resize event redraw everything
#todo: make updating center label with unit


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
                 label_font=QFont("Sans-serif", 16),
                 default_color=(255, 255, 255),
                 redline_color=(255, 0, 0),
                 blueline_color=(0, 0, 255),
                 background_color=(0, 0, 0),
                 dial_opacity="30%",
                 border_opacity="60%",
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
                 angle_range=2 * pi - pi / 2,
                 angle_offset=pi - pi / 4,
                 blueline=-1,
                 no_font=False,
                 dymanic_mask=False):
        super().__init__(parent)

        visual_min_unit = floor(min_unit / visual_num_gap)
        visual_max_unit = ceil(max_unit / visual_num_gap)

        self.unit = 0
        self.min_unit = min_unit
        self.max_unit = max_unit
        self.redline = redline
        self.blueline = blueline
        self.unit_range = max_unit - min_unit
        self.denomination = denomination
        self.label_font = label_font
        self.dial_opacity = dial_opacity
        self.border_opacity = border_opacity

        self.dial_color = f"rgba({default_color[0]}, {default_color[1]}, {default_color[2]}, {self.dial_opacity})"
        self.dial_top_color = f"rgba({default_color[0]}, {default_color[1]}, {default_color[2]}, {self.border_opacity})"

        self.dial_redline_color = f"rgba({redline_color[0]}, {redline_color[1]}, {redline_color[2]}, {self.dial_opacity})"
        self.dial_top_redline_color = f"rgba({redline_color[0]}, {redline_color[1]}, {redline_color[2]}, {self.border_opacity})"

        self.dial_blueline_color = f"rgba({blueline_color[0]}, {blueline_color[1]}, {blueline_color[2]}, {self.dial_opacity})"
        self.dial_top_blueline_color = f"rgba({blueline_color[0]}, {blueline_color[1]}, {blueline_color[2]}, {self.border_opacity})"

        self.resize(size, size)

        frame = QFrame(self)
        frame.setStyleSheet(
            f"background-color: rgb({background_color[0]}, {background_color[1]}, {background_color[2]}); border-radius: {int(size/2)}px"
        )
        frame.resize(self.geometry().size())
        frame.show()

        rad_offset = angle_offset
        rad_step = angle_range / visual_max_unit
        rad_section_step = rad_step / mid_sections

        self.rad_range = angle_range
        self.rad_range_deg = degrees(angle_range)
        self.rad_range_a = angle_range / (2 * pi)
        self.dial_offset_angle = rad_offset
        self.dial_offset_angle_deg = degrees(rad_offset)
        self.dial_angle_step = self.rad_range_deg / self.unit_range

        dial_inner_border_rad += dial_mask_rad

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
        self.dial_corner_radius = int(unit_dial.geometry().width() / 2)
        unit_dial.setStyleSheet(f"border-radius: {self.dial_corner_radius}")
        unit_dial.show()
        unit_dial.move(
            int(x_rad_offset - unit_dial.frameGeometry().width() / 2),
            int(y_rad_offset - unit_dial.frameGeometry().height() / 2))

        unit_dial_top = QFrame(frame)
        unit_dial_top.resize(unit_dial.frameGeometry().size())
        unit_dial_top.show()
        unit_dial_top.setStyleSheet(f"border-radius: {self.dial_corner_radius}")
        unit_dial_top.move(
            int(x_rad_offset - unit_dial_top.frameGeometry().width() / 2),
            int(y_rad_offset - unit_dial_top.frameGeometry().height() / 2))

        unit_dial_bottom = QFrame(frame)
        unit_dial_bottom.resize(unit_dial.frameGeometry().size())
        unit_dial_bottom.setStyleSheet(
            f"border-radius: {self.dial_corner_radius}")
        unit_dial_bottom.move(
            x_rad_offset - unit_dial_bottom.frameGeometry().width() / 2,
            y_rad_offset - unit_dial_bottom.frameGeometry().height() / 2)
        unit_dial_bottom.show()

        unit_dial_inner_border = QFrame(frame)
        unit_dial_inner_border.resize(dial_inner_border_rad,
                                      dial_inner_border_rad)
        self.unit_dial_inner_border_radius = int(
            unit_dial_inner_border.geometry().width() / 2)
        unit_dial_inner_border.move(
            int(x_rad_offset -
                unit_dial_inner_border.frameGeometry().width() / 2),
            int(y_rad_offset -
                unit_dial_inner_border.frameGeometry().height() / 2))
        unit_dial_inner_border.setStyleSheet(f"border-radius: {self.unit_dial_inner_border_radius}")
        unit_dial_inner_border.show()

        unit_dial_mask = QFrame(frame)
        unit_dial_mask.resize(dial_mask_rad, dial_mask_rad)
        unit_dial_mask.move(
            x_rad_offset - unit_dial_mask.frameGeometry().width() / 2,
            y_rad_offset - unit_dial_mask.frameGeometry().height() / 2)

        if dymanic_mask:
            gradient_angle = (self.max_unit - self.max_unit * self.rad_range_a
                              - pi) / (self.unit_range)

            unit_dial_mask.setStyleSheet(
                f"border-radius: {int(unit_dial_mask.geometry().width()/2)}px;\
                background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{-(self.dial_offset_angle_deg + (self.rad_range_a - pi) / 2)}, stop:{gradient_angle - 0.001} rgba(255, 255, 255, 0%), stop:{gradient_angle} rgb({background_color[0]}, {background_color[1]}, {background_color[2]}));"
            )
        else:
            unit_dial_mask.setStyleSheet(
                f"border-radius: {int(unit_dial_mask.geometry().width()/2)}px; background-color: rgb({background_color[0]}, {background_color[1]}, {background_color[2]});"
            )
        unit_dial_mask.show()

        self.unit_dial_inner_border = unit_dial_inner_border
        self.unit_dial = unit_dial
        self.unit_dial_top = unit_dial_top
        self.unit_dial_bottom = unit_dial_bottom
        self.frame = frame

        color = QColor(*default_color)
        palette = QPalette()

        for i in range(visual_min_unit, visual_max_unit + 1):
            if i >= redline / visual_num_gap:
                color = QColor(*redline_color)
            elif i <= blueline / visual_num_gap:
                color = QColor(*blueline_color)
            else:
                color = QColor(*default_color)

            palette.setColor(QPalette.ColorRole.WindowText, color)

            if not no_font:
                label = QLabel(f"{int(i * visual_num_gap / denomination)}",
                               frame)
                label.setStyleSheet("background:transparent")
                label.setPalette(palette)
                label.setFont(label_font)
                label.show()
                label.move(
                    cos(i * rad_step + rad_offset) * num_x_radius +
                    x_rad_offset - label.geometry().width() / 2,
                    sin(i * rad_step + rad_offset) * num_y_radius +
                    y_rad_offset - label.geometry().height() / 2)
                label.show()

            for z in range(mid_sections):
                if i + z / mid_sections >= redline / visual_num_gap:
                    color = QColor(*redline_color)
                elif i + z / mid_sections <= blueline / visual_num_gap:
                    color = QColor(*blueline_color)

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

    def setDial(self, alpha):
        alpha = clamp(0, alpha, 1)
        self.setUnit(ceil(alpha * self.unit_range))

    def setUnit(self, value):
        self.unit = value
        self.updateUnit()

    def updateUnit(self):
        current_unit = self.unit

        angle = -self.dial_offset_angle_deg
        angle2 = angle - current_unit * self.dial_angle_step

        color = self.dial_color
        color2 = self.dial_top_color

        if current_unit >= self.redline:
            color = self.dial_redline_color
            color2 = self.dial_top_redline_color
        elif current_unit <= self.blueline:
            color = self.dial_blueline_color
            color2 = self.dial_top_blueline_color

        current_unit = self.max_unit - current_unit * self.rad_range_a

        if current_unit > 0:
            unit_alpha = current_unit / self.unit_range
        else:
            unit_alpha = self.max_unit

        # stop_1 = clamp(0, unit_alpha - 0.001, 0.999)
        # stop_2 = min(unit_alpha, 1)

        stop_1 = unit_alpha - 0.001
        stop_2 = unit_alpha

        #* the style sheets are expensive
        # or the f strings?

        self.unit_dial.setStyleSheet(
            f"border-radius: {self.dial_corner_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle}, stop:{stop_1} rgba(255, 255, 255, 0%), stop:{stop_2} {color});"
        )

        self.unit_dial_inner_border.setStyleSheet(
            f"border-radius: {self.unit_dial_inner_border_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle}, stop:{stop_1} rgba(255, 255, 255, 0%), stop:{stop_2} {color2});"
        )

        self.unit_dial_top.setStyleSheet(
            f"border-radius: {self.dial_corner_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle2}, stop:0.997 rgba(255, 255, 255, 0%), stop:1 {color2});"
        )

        self.unit_dial_bottom.setStyleSheet(
            f"border-radius: {self.dial_corner_radius}px; background-color: qconicalgradient(cx:0.5, cy:0.5, angle:{angle}, stop:0.997 rgba(255, 255, 255, 0%), stop:1 {color2});"
        )
