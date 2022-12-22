import platform
from math import ceil, cos, degrees, floor, pi, sin
from qutil import Line, Arc
from PyQt5.QtCore import QSize, QLineF, pyqtProperty
from PyQt5.QtGui import QColor, QFont, QPalette, QPaintEvent
from PyQt5.QtWidgets import QFrame, QLabel, QWidget

#todo: make resize event redraw everything
#todo: make updating center label with unit

SYSTEM = platform.system()


class Dial(QWidget):

    def __init__(self,
                 parent: QWidget,
                 min_unit: float = 0,
                 max_unit: float = 1,
                 redline: float = 0.5,
                 blueline: float = -1,
                 mid_sections: int = 2,
                 denomination: int = 1,
                 size: QSize = QSize(500, 500),
                 dial_width: float = 30,
                 line_width: float = 1,
                 no_font: bool = False,
                 label_font: QFont = QFont("Sans-serif", 16),
                 default_color: QColor = QColor(255, 255, 255),
                 redline_color: QColor = QColor(255, 0, 0),
                 blueline_color: QColor = QColor(0, 0, 255),
                 background_color: QColor = QColor(0, 0, 0),
                 dial_opacity: float = 0.3,
                 visual_num_gap: float = 1,
                 buffer_radius: int = 20,
                 num_radius: int = 54,
                 section_radius: int = 20,
                 minor_section_rad_offset: int = 3,
                 middle_section_rad_offset: int = 43,
                 major_section_rad_offset: int = 40,
                 angle_range: float = 2 * pi - pi / 2,
                 angle_offset: float = pi - pi / 4) -> None:
        super().__init__(parent)

        visual_min_unit = floor(min_unit / visual_num_gap)
        visual_max_unit = ceil(max_unit / visual_num_gap)

        self._unit = 0
        self.min_unit = min_unit
        self.max_unit = max_unit
        self.redline = redline
        self.blueline = blueline
        self.unit_range = max_unit - min_unit
        self.dial_opacity = dial_opacity
        self.default_color = default_color
        self.redline_color = redline_color
        self.blueline_color = blueline_color
        self.default_color_dial = QColor(default_color)
        self.redline_color_dial = QColor(redline_color)
        self.blueline_color_dial = QColor(blueline_color)

        self.default_color_dial.setAlphaF(dial_opacity)
        self.redline_color_dial.setAlphaF(dial_opacity)
        self.blueline_color_dial.setAlphaF(dial_opacity)

        self.resize(size)

        frame = QFrame(self)
        frame.setStyleSheet(
            f"background-color: rgb({background_color.red()}, {background_color.green()}, {background_color.blue()}); border-radius: {int(size.width()/2)}px"
        )

        frame.resize(size)
        self.frame = frame

        rad_offset = angle_offset
        rad_step = angle_range / visual_max_unit
        rad_section_step = rad_step / mid_sections
        x_rad_offset = size.width() / 2
        y_rad_offset = size.height() / 2

        self.rad_range = angle_range
        self.rad_range_deg = degrees(angle_range)
        self.dial_offset_angle_deg = 360 - degrees(rad_offset)
        self.dial_angle_step = self.rad_range_deg / self.unit_range

        arc_size_offset = buffer_radius + num_radius
        arc = Arc(self, size - QSize(arc_size_offset, arc_size_offset), self.default_color_dial, dial_width)
        arc.move(int(x_rad_offset) - arc.width() // 2, int(y_rad_offset) - arc.height() // 2)
        arc.set_arc(int(self.dial_offset_angle_deg), 0)
        self.arc = arc

        palette = QPalette()
        num_x_radius = x_rad_offset - buffer_radius - num_radius
        num_y_radius = y_rad_offset - buffer_radius - num_radius
        section_x_radius = x_rad_offset - buffer_radius - section_radius
        section_y_radius = y_rad_offset - buffer_radius - section_radius

        for i in range(visual_min_unit, visual_max_unit + 1):
            redline / visual_num_gap
            if i >= redline / visual_num_gap:
                color = redline_color
            elif i <= blueline / visual_num_gap:
                color = blueline_color
            else:
                color = default_color

            palette.setColor(QPalette.ColorRole.WindowText, color)

            if not no_font:
                label = QLabel(frame)
                label.setStyleSheet("background:transparent")
                label.setPalette(palette)
                label.setFont(label_font)
                label.setText(f"{int(i * visual_num_gap / denomination)}")
                label.show()
                label.move(
                    int(cos(i * rad_step + rad_offset) * num_x_radius + x_rad_offset - label.width() / 2),
                    int(sin(i * rad_step + rad_offset) * num_y_radius + y_rad_offset - label.height() / 2))

            for z in range(mid_sections):
                if i + z / mid_sections >= redline / visual_num_gap:
                    color = redline_color
                elif i + z / mid_sections <= blueline / visual_num_gap:
                    color = blueline_color
                else:
                    color = default_color

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

                x_inner_radius = min(x_inner_radius, x_radius - minor_section_rad_offset)
                y_inner_radius = min(y_inner_radius, y_radius - minor_section_rad_offset)

                Line(
                    frame,
                    QLineF(
                        cos(i * rad_step + rad_offset + z * rad_section_step) * x_radius + x_rad_offset,
                        sin(i * rad_step + rad_offset + z * rad_section_step) * y_radius + y_rad_offset,
                        cos(i * rad_step + rad_offset + z * rad_section_step) * x_inner_radius + x_rad_offset,
                        sin(i * rad_step + rad_offset + z * rad_section_step) * y_inner_radius + y_rad_offset), color,
                    line_width)

                if i == visual_max_unit:
                    break

    def set_dial(self, alpha: float) -> None:
        self.set_unit(ceil(alpha * self.unit_range))

    def update_unit(self) -> None:
        angle = -(self._unit * self.dial_angle_step)
        if self._unit >= self.redline:
            self.arc.set_color(self.redline_color_dial)
        elif self._unit <= self.blueline:
            self.arc.set_color(self.blueline_color_dial)
        else:
            self.arc.set_color(self.default_color_dial)
        self.arc.set_arc(self.dial_offset_angle_deg, angle)

    @pyqtProperty(float)
    def dial_unit(self) -> float:
        return self._unit

    @dial_unit.setter
    def dial_unit(self, value: float) -> None:
        self._unit = value
        self.update_unit()
