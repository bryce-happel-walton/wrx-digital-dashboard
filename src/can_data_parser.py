from PyQt5.QtCore import pyqtSlot

LEAST_5_BITS_MASK = (1 << 5) - 1
LEAST_4_BITS_MASK = (1 << 4) - 1
SPEED_SCALE = 0.05625
TEMP_SENSOR_OFFSET = -40
FUEL_LEVEL_MAX = 0xFF
FUEL_LEVEL_MIN = 0x25
FUEL_CONSUMPTION_SCALE = 0.24726

# todo: rewrite to allow reading byte, bits, conversions, etc from can.toml


def is_set(x: int, n: int) -> bool:
    return x & 1 << n != 0


@pyqtSlot(bytearray)
def rpm(data: bytearray) -> int:
    return data[4] + ((data[5] & LEAST_5_BITS_MASK) << 8)


@pyqtSlot(bytearray)
def vehicle_speed(data: bytearray) -> float:
    return (data[0] + (data[1] << 8)) * SPEED_SCALE


@pyqtSlot(bytearray)
def cruise_control_speed(data: bytearray) -> int:
    return data[7]


@pyqtSlot(bytearray)
def turn_signals(data: bytearray) -> list[bool]:
    # * left, right
    new_data = [is_set(data[5], 4), is_set(data[5], 5)]

    return new_data


@pyqtSlot(bytearray)
def fuel_level(data: bytearray) -> float:
    num = data[0] + ((data[1] & LEAST_4_BITS_MASK) << 8)

    return (1 - (num - FUEL_LEVEL_MIN) / 2 / FUEL_LEVEL_MAX - 1) * 100


@pyqtSlot(bytearray)
def oil_temp(data: bytearray) -> int:
    return data[2] + TEMP_SENSOR_OFFSET


@pyqtSlot(bytearray)
def coolant_temp(data: bytearray) -> int:
    return data[3] + TEMP_SENSOR_OFFSET


@pyqtSlot(bytearray)
def handbrake_switch(data: bytearray) -> bool:
    return is_set(data[6], 5)


@pyqtSlot(bytearray)
def reverse_switch(data: bytearray) -> bool:
    return is_set(data[6], 5)


@pyqtSlot(bytearray)
def clutch_switch(data: bytearray) -> bool:
    return is_set(data[1], 5)


@pyqtSlot(bytearray)
def cruise_control_set(data: bytearray) -> bool:
    return is_set(data[5], 5)


@pyqtSlot(bytearray)
def cruise_control_status(data: bytearray) -> bool:
    return is_set(data[5], 4)


@pyqtSlot(bytearray)
def seatbelt_driver(data: bytearray) -> bool:
    return is_set(data[5], 0)


@pyqtSlot(bytearray)
def dimmer_dial(data: bytearray) -> int:
    return data[0]


@pyqtSlot(bytearray)
def traction_control(data: bytearray) -> bool:
    return is_set(data[1], 3)


@pyqtSlot(bytearray)
def traction_control_mode(data: bytearray) -> bool:
    return is_set(data[0], 3)


@pyqtSlot(bytearray)
def fog_lights(data: bytearray) -> bool:
    return is_set(data[1], 6)


@pyqtSlot(bytearray)
def headlights(data: bytearray) -> list[bool]:
    return [
        is_set(data[7], 3),  # * lowbeams
        is_set(data[7], 2),  # * parking lights
        is_set(data[7], 4),  # * highbeams
        is_set(data[7], 1),  # * running lights
    ]


@pyqtSlot(bytearray)
def door_states(data: bytearray) -> list[bool]:
    return [
        is_set(data[1], 0),  # * lf
        is_set(data[1], 1),  # * rf
        is_set(data[1], 3),  # * lr
        is_set(data[1], 2),  # * rr
        is_set(data[1], 5),  # * trunk
    ]


@pyqtSlot(bytearray)
def boost_pressure(data: bytearray) -> float:
    return data[4] * 0.3 - 15.1


@pyqtSlot(bytearray)
def check_engine_light(data: bytearray) -> float:
    return is_set(data[4], 7)


@pyqtSlot(bytearray)
def gear(data: bytearray) -> int:
    val = data[6] & LEAST_4_BITS_MASK

    if val == 7 or val == 0:
        return 0

    return val


@pyqtSlot(bytearray)
def odometer(data: bytearray) -> float:
    value = 0

    for i, x in enumerate(reversed(data[:4])):
        value += x << (8 * i)

    return value / 10


@pyqtSlot(bytearray)
def fuel_consumption(data: bytearray) -> float:
    return data[1] * FUEL_CONSUMPTION_SCALE
