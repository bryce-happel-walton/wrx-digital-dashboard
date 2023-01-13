from math import ceil, cos, degrees, floor, pi, sin
from qutil import Line, Arc
from PyQt5.QtCore import QSize, QLineF, Qt
from PyQt5.QtCore import pyqtProperty
from PyQt5.QtGui import QColor, QFont, QPalette, QGradient, QRadialGradient
from PyQt5.QtWidgets import QFrame, QLabel, QWidget


# TODO: allow dynamic changing of dial variable. Ex: changing unit, max, min, etc


class Dial(QWidget):
    def __init__(
        self,
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
        needle_width_deg: float = 0.8,
        no_font: bool = False,
        label_font: QFont = QFont(),
        default_color: QColor = QColor(255, 255, 255),
        redline_color: QColor = QColor(255, 0, 0),
        blueline_color: QColor = QColor(0, 0, 255),
        background_color: QColor = QColor(0, 0, 0),
        needle_color: QColor = QColor(255, 255, 255),
        dial_opacity: float = 0.3,
        visual_num_gap: float = 1,
        buffer_radius: int = 20,
        num_radius: int = 54,
        section_radius: int = 20,
        minor_section_rad_offset: int = 3,
        middle_section_rad_offset: int = 43,
        major_section_rad_offset: int = 40,
        angle_range: float = 2 * pi - pi / 2,
        angle_offset: float = pi - pi / 4,
        gradient: bool = True,
        border_width: int = 1,
    ) -> None:
        super().__init__(parent)
        self.resize(size)

        visual_min_unit = floor(min_unit / visual_num_gap)
        visual_max_unit = ceil(max_unit / visual_num_gap)

        self._unit = 0
        self.min_unit = min_unit
        self.max_unit = max_unit
        self.redline = redline
        self.blueline = blueline
        self.needle_width_deg = needle_width_deg
        self.default_color = default_color
        self.redline_color = redline_color
        self.blueline_color = blueline_color
        self.default_color_dial = QColor(default_color)
        self.redline_color_dial = QColor(redline_color)
        self.blueline_color_dial = QColor(blueline_color)
        self.default_color_needle = QColor(needle_color)

        self.default_color_dial.setAlphaF(dial_opacity)
        self.redline_color_dial.setAlphaF(dial_opacity)
        self.blueline_color_dial.setAlphaF(dial_opacity)

        self.frame = QFrame(self)
        frame_color_palette = QPalette()
        frame_color_palette.setColor(QPalette.ColorRole.Background, background_color)
        self.frame.setPalette(frame_color_palette)
        self.frame.setStyleSheet(f"border-radius: {size.width() // 2}px")
        self.frame.resize(size)

        rad_step = angle_range / visual_max_unit
        rad_section_step = rad_step / mid_sections
        half_width = size.width() / 2
        num_x_radius = half_width - buffer_radius - num_radius
        section_x_radius = half_width - buffer_radius - section_radius
        arc_size_offset = (buffer_radius + section_radius) * 2
        arc_size: QSize = size - QSize(arc_size_offset, arc_size_offset)
        self.dial_offset_angle_deg = 360 - degrees(angle_offset)
        self.dial_angle_step = degrees(angle_range) / (max_unit - min_unit)

        if gradient:
            self.default_color_gradient = QRadialGradient(
                arc_size.width() / 2, arc_size.height() / 2, arc_size.width() / 2
            )
            self.redline_color_gradient = QRadialGradient(
                arc_size.width() / 2, arc_size.height() / 2, arc_size.width() / 2
            )
            self.blueline_color_gradient = QRadialGradient(
                arc_size.width() / 2, arc_size.height() / 2, arc_size.width() / 2
            )
            self.default_color_needle_gradient = QRadialGradient(
                arc_size.width() / 2, arc_size.height() / 2, arc_size.width() / 2
            )

            self.default_color_gradient.setSpread(QGradient.Spread.PadSpread)
            self.redline_color_gradient.setSpread(QGradient.Spread.PadSpread)
            self.blueline_color_gradient.setSpread(QGradient.Spread.PadSpread)
            self.default_color_needle_gradient.setSpread(QGradient.Spread.PadSpread)

            self.default_color_gradient.setColorAt(1, self.default_color_dial)
            self.redline_color_gradient.setColorAt(1, self.redline_color_dial)
            self.blueline_color_gradient.setColorAt(1, self.blueline_color_dial)
            self.default_color_needle_gradient.setColorAt(1, self.default_color_needle)
            self.default_color_needle_gradient.setColorAt(0, QColor(0, 0, 0, 0))
            self.default_color_needle_gradient.setColorAt(
                1 - dial_width / arc_size.width() * 3, QColor(0, 0, 0, 0)
            )

            gradient_colors = [
                (0, QColor(0, 0, 0, 0)),
                (1 - dial_width / arc_size.width() * 2, QColor(0, 0, 0, 0)),
            ]
            for i in gradient_colors:
                self.default_color_gradient.setColorAt(*i)
                self.redline_color_gradient.setColorAt(*i)
                self.blueline_color_gradient.setColorAt(*i)

            self.default_color_dial = self.default_color_gradient
            self.redline_color_dial = self.redline_color_gradient
            self.blueline_color_dial = self.blueline_color_gradient
            self.default_color_needle = self.default_color_needle_gradient

        self.arc = Arc(self, arc_size, self.default_color_dial, dial_width)
        self.arc.move(
            int(half_width - self.arc.width() / 2),
            int(half_width - self.arc.height() / 2),
        )
        self.arc.set_arc(self.dial_offset_angle_deg, 0)

        self.needle = Arc(
            self, arc_size, self.default_color_needle, dial_width + dial_width / 8
        )
        self.needle.move(
            int(half_width - self.arc.width() / 2),
            int(half_width - self.arc.height() / 2),
        )
        self.needle.set_arc(
            self.dial_offset_angle_deg - self.needle_width_deg / 2,
            self.needle_width_deg / 2,
        )

        # TODO: use line width to extend border and eliminate overhang
        if border_width != 0:
            self.outline_arc = Arc(
                self,
                arc_size + QSize(border_width * 2, border_width * 2),
                default_color,
                border_width,
            )
            self.outline_arc.move(
                int(half_width - self.outline_arc.width() // 2),
                int(half_width - self.outline_arc.height() // 2),
            )
            self.outline_arc.set_arc(
                self.dial_offset_angle_deg,
                -min(max_unit, redline) * self.dial_angle_step,
            )

            if redline < max_unit:
                self.outline_arc_redline = Arc(
                    self,
                    arc_size + QSize(border_width * 2, border_width * 2),
                    redline_color,
                    border_width,
                )
                self.outline_arc_redline.move(
                    int(half_width) - self.outline_arc_redline.width() // 2,
                    int(half_width) - self.outline_arc_redline.height() // 2,
                )
                self.outline_arc_redline.set_arc(
                    self.dial_offset_angle_deg + -redline * self.dial_angle_step,
                    -(max_unit - redline) * self.dial_angle_step,
                )

        palette = QPalette()

        for i in range(visual_min_unit, visual_max_unit + 1):
            if i >= redline / visual_num_gap:
                color = redline_color
            elif i <= blueline / visual_num_gap:
                color = blueline_color
            else:
                color = default_color

            palette.setColor(QPalette.ColorRole.WindowText, color)

            if not no_font:
                label = QLabel(self.frame)
                label.setStyleSheet("background:transparent")
                label.setPalette(palette)
                label.setFont(label_font)
                label.setAlignment(
                    Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter
                )
                label.setText(f"{int(i * visual_num_gap / denomination)}")
                label.adjustSize()
                label.move(
                    int(
                        cos(i * rad_step + angle_offset)
                        * (num_x_radius - label.width() / 4)
                        + half_width
                        - label.width() / 2
                    ),
                    int(
                        sin(i * rad_step + angle_offset)
                        * (num_x_radius - label.height() / 3)
                        + half_width
                        - label.height() / 2
                    ),
                )

            for z in range(mid_sections):
                if i + z / mid_sections >= redline / visual_num_gap:
                    color = redline_color
                elif i + z / mid_sections <= blueline / visual_num_gap:
                    color = blueline_color
                else:
                    color = default_color

                if z == 0:
                    x_inner_radius = (
                        section_x_radius - num_radius + major_section_rad_offset
                    )
                elif (mid_sections % 2 == 0) and (z == mid_sections / 2):
                    x_inner_radius = (
                        section_x_radius - num_radius + middle_section_rad_offset
                    )
                else:
                    x_inner_radius = section_x_radius - minor_section_rad_offset

                x_inner_radius = min(
                    x_inner_radius, section_x_radius - minor_section_rad_offset
                )

                Line(
                    self.frame,
                    QLineF(
                        cos(i * rad_step + angle_offset + z * rad_section_step)
                        * section_x_radius
                        + half_width,
                        sin(i * rad_step + angle_offset + z * rad_section_step)
                        * section_x_radius
                        + half_width,
                        cos(i * rad_step + angle_offset + z * rad_section_step)
                        * x_inner_radius
                        + half_width,
                        sin(i * rad_step + angle_offset + z * rad_section_step)
                        * x_inner_radius
                        + half_width,
                    ),
                    color,
                    line_width,
                )

                if i == visual_max_unit:
                    break

    def update_unit(self) -> None:
        angle = -self._unit * self.dial_angle_step
        if self._unit >= self.redline:
            self.arc.set_color(self.redline_color_dial)
        elif self._unit <= self.blueline:
            self.arc.set_color(self.blueline_color_dial)
        else:
            self.arc.set_color(self.default_color_dial)
        self.arc.set_arc(self.dial_offset_angle_deg, angle)
        self.needle.set_arc(
            self.dial_offset_angle_deg + angle - self.needle_width_deg / 2,
            self.needle_width_deg / 2,
        )

    @pyqtProperty(float)
    def dial_unit(self) -> float:
        return self._unit

    @dial_unit.setter
    def dial_unit(self, value: float) -> None:
        self._unit = value
        self.update_unit()
