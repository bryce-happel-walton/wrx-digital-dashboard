LEAST_5_BITS_MASK = (1 << 5) - 1
LEAST_4_BITS_MASK = (1 << 4) - 1
SPEED_SCALE = 0.05625
TEMP_SENSOR_OFFSET = -40
FUEL_LEVEL_MAX = 0x3FF
FUEL_LEVEL_MIN = 0x25
FUEL_LEVEL_DIFF = FUEL_LEVEL_MAX - FUEL_LEVEL_MIN
FUEL_CONSUMPTION_SCALE = 0.24726

# todo: rewrite to allow reading byte, bits, conversions, etc from can.toml


def is_set(x: int, n: int) -> bool:
    return x & 1 << n != 0


def rpm(data: bytearray) -> int:
    return data[4] + ((data[5] & LEAST_5_BITS_MASK) << 8)


def vehicle_speed(data: bytearray) -> float:
    return (data[0] + (data[1] << 8)) * SPEED_SCALE


def cruise_control_speed(data: bytearray) -> int:
    return data[7]


def turn_signals(data: bytearray) -> list[bool]:
    # * left, right
    new_data = [is_set(data[5], 4), is_set(data[5], 5)]

    return new_data


def fuel_level(data: bytearray) -> float:
    val = data[0] + ((data[1] & LEAST_4_BITS_MASK) << 8) - FUEL_LEVEL_MIN
    val = 1 - val / FUEL_LEVEL_DIFF
    return val * 100


def oil_temp(data: bytearray) -> int:
    return data[2] + TEMP_SENSOR_OFFSET


def oil_pressure_warning(data: bytearray) -> bool:
    return is_set(data[1], 4)


def coolant_temp(data: bytearray) -> int:
    return data[3] + TEMP_SENSOR_OFFSET


def handbrake_switch(data: bytearray) -> bool:
    return is_set(data[6], 3)


def reverse_switch(data: bytearray) -> bool:
    return is_set(data[6], 2)


def clutch_switch(data: bytearray) -> bool:
    return is_set(data[1], 7)


def tpms_warning(data: bytearray) -> bool:
    return is_set(data[4], 4)


def cruise_control_set(data: bytearray) -> bool:
    return is_set(data[5], 5)


def cruise_control_status(data: bytearray) -> bool:
    return is_set(data[5], 4)


def seatbelt_driver(data: bytearray) -> bool:
    return is_set(data[5], 0)


def dimmer_dial(data: bytearray) -> int:
    return data[0]


def traction_control(data: bytearray) -> bool:
    return is_set(data[1], 3)


def traction_control_mode(data: bytearray) -> bool:
    return is_set(data[0], 3)


def hill_assist(data: bytearray) -> bool:
    return is_set(data[1], 7)


def fog_lights(data: bytearray) -> bool:
    return is_set(data[1], 6)


def headlights(data: bytearray) -> list[bool]:
    return [
        is_set(data[7], 3),  # * lowbeams
        is_set(data[7], 2),  # * parking lights
        is_set(data[7], 4),  # * highbeams
        is_set(data[7], 1),  # * running lights
    ]


def door_states(data: bytearray) -> list[bool]:
    return [
        is_set(data[1], 0),  # * lf
        is_set(data[1], 1),  # * rf
        is_set(data[1], 3),  # * lr
        is_set(data[1], 2),  # * rr
        is_set(data[1], 5),  # * trunk
    ]


def boost_pressure(data: bytearray) -> float:
    return data[4] * 0.3 - 15.1


def check_engine_light(data: bytearray) -> bool:
    return is_set(data[4], 7)


def gear(data: bytearray) -> int:
    val = data[6] & LEAST_4_BITS_MASK

    if val == 7 or val == 0:
        return 0

    return val


def odometer(data: bytearray) -> float:
    value = 0

    for i, x in enumerate(data[:4]):
        value += x << (8 * i)

    return value / 10


def fuel_consumption(data: bytearray) -> float:
    return data[1] * FUEL_CONSUMPTION_SCALE


def srs_airbag_system_warning_light(data: bytearray) -> bool:
    return is_set(data[2], 0)


# *
# * CONVERSATION VALUES BELOW
# *


def engine_load(data: bytearray) -> float:
    return data[0] / 0xFF * 100


def intake_manifold_absolute_pressure(data: bytearray) -> int:
    return data[0]


def timing_advance(data: bytearray) -> float:
    return data[0] / 2 - 64


def mass_air_flow(data: bytearray) -> float:
    return (data[0] + (data[1] << 8)) / 100


def throttle_position(data: bytearray) -> float:
    return data[0] / 0xFF * 100


# 0x37A byte 5 off 0x10 on 0x04
# 0x375 byte 6 on 0x22
