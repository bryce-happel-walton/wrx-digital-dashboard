from PyQt5.QtCore import pyqtSlot

LEAST_5_BITS_MASK = (1 << 5) - 1
LEAST_4_BITS_MASK = (1 << 4) - 1
SPEED_SCALE = 0.05625
TEMP_SENSOR_OFFSET = -40
FUEL_LEVEL_MAX = 0xFF
FUEL_LEVEL_MIN = 0x25

# todo: rewrite to allow reading byte, bits, conversions, etc from can.toml


@pyqtSlot(bytearray)
def rpm(data: bytearray) -> int:
    return data[4] + ((data[5] & LEAST_5_BITS_MASK) << 8)


@pyqtSlot(bytearray)
def vehicle_speed(data: bytearray) -> float:
    b0 = f"{data[0]:08b}"
    b1 = f"{data[1]:08b}"
    return int(b1 + b0, base=2) * SPEED_SCALE


@pyqtSlot(bytearray)
def cruise_control_speed(data: bytearray) -> int:
    return data[7]


@pyqtSlot(bytearray)
def turn_signals(data: bytearray) -> list[int]:
    b5 = f"{data[5]:08b}"

    # * left, right
    new_data = [int(b5[3]), int(b5[2])]

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
def handbrake_switch(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"
    return int(b6[4], 2)


@pyqtSlot(bytearray)
def reverse_switch(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"
    return int(b6[5], 2)


@pyqtSlot(bytearray)
def clutch_switch(data: bytearray) -> int:
    b2 = f"{data[1]:08b}"
    return int(b2[0], 2)


@pyqtSlot(bytearray)
def cruise_control_set(data: bytearray) -> int:
    b5 = f"{data[5]:08b}"
    return int(b5[2], 2)


@pyqtSlot(bytearray)
def cruise_control_status(data: bytearray) -> int:
    b5 = f"{data[5]:08b}"
    return int(b5[3], 2)


@pyqtSlot(bytearray)
def seatbelt_driver(data: bytearray) -> int:
    b5 = f"{data[5]:08b}"
    return int(b5[7], 2)


@pyqtSlot(bytearray)
def dimmer_dial(data: bytearray) -> int:
    return data[0]


@pyqtSlot(bytearray)
def traction_control(data: bytearray) -> int:
    b1 = f"{data[1]:08b}"
    return int(b1[4], 2)


@pyqtSlot(bytearray)
def traction_control_mode(data: bytearray) -> int:
    b0 = f"{data[0]:08b}"
    return int(b0[4], 2)


@pyqtSlot(bytearray)
def fog_lights(data: bytearray) -> int:
    b1 = f"{data[1]:08b}"
    return int(b1[1], 2)


@pyqtSlot(bytearray)
def headlights(data: bytearray) -> list[int]:
    b7 = f"{data[7]:08b}"

    new_data = [
        int(b7[4], 2),  # * lowbeams
        int(b7[5], 2),  # * parking lights
        int(b7[3], 2),  # * highbeams
        int(b7[6], 2),  # * running lights
    ]

    return new_data


@pyqtSlot(bytearray)
def door_states(data: bytearray) -> dict[str]:
    b1 = f"{data[1]:08b}"

    # * lf, rf, lr, rr, trunk
    new_data = [b1[7], b1[6], b1[4], b1[5], b1[2]]

    return new_data


@pyqtSlot(bytearray)
def boost_pressure(data: bytearray) -> float:
    return data[4] * 0.3 - 15.1


@pyqtSlot(bytearray)
def check_engine_light(data: bytearray) -> float:
    b4 = f"{data[4]:08b}"

    return int(b4[0], 2)


@pyqtSlot(bytearray)
def gear(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"[4:]
    b6 = int(b6, 2)

    if b6 == 7 or b6 == 0:
        return 0

    return b6


@pyqtSlot(bytearray)
def odometer(data: bytearray) -> float:
    bits = [f"{i:08b}" for i in data[:4]]
    value = "0"

    for i in reversed(bits):
        value += i

    return int(value, 2) / 10
