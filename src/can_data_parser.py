from PyQt5.QtCore import pyqtSlot

SPEED_SCALE = 0.05625
TEMP_SENSOR_OFFSET = -40
FUEL_LEVEL_SCALE = 0.004587
FUEL_LEVEL_VALUE_OFFSET = 0x200  # 512
FUEL_LEVEL_MAX = 0xFF
FUEL_LEVEL_MIN = 0x25

# todo: rewrite to allow reading byte, bits, conversions, etc from can.toml


@pyqtSlot(bytearray)
def rpm(data: bytearray) -> int:
    b4 = f"{data[4]:08b}"
    b5 = f"{data[5]:08b}"[-5:]
    return int(b5 + b4, base=2)


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

    # data = {"left_turn_signal": int(b5[3]), "right_turn_signal": int(b5[2])}
    new_data = [int(b5[3]), int(b5[2])]
    # constant = [int(b5[4]), int(b5[5])]

    return new_data


@pyqtSlot(bytearray)
def fuel_level(data: bytearray) -> float:
    return (
        1
        - (
            (data[0] + FUEL_LEVEL_VALUE_OFFSET - FUEL_LEVEL_MIN) / 2 / FUEL_LEVEL_MAX
            - 1
        )
    ) * 100


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


low = 0x8C
pull_high = 0x98
high = 0x9C
rl_and_dim = 0x84
rl_day = 0x82


# todo: change to evaluate individual bits instead of comparing hex values
@pyqtSlot(bytearray)
def headlights(data: bytearray) -> list[int]:
    # d7 = data[7]
    b7 = f"{data[7]:08b}"

    # data = {
    #     "lowbeams": b7 == low,
    #     "drls": 1 if b7 == drl_and_dim else 2 if b7 == drl_day else 0,
    #     "highbeams": b7 in [pull_high, high]
    # }

    new_data = [
        int(b7[3], 2),
        int(b7[2], 2),  # 1 if d7 == rl_and_dim else 2 if d7 == rl_day else 0,
        int(b7[4], 2),
    ]

    return new_data


@pyqtSlot(bytearray)
def door_states(data: bytearray) -> dict[str]:
    b1 = f"{data[1]:08b}"

    # data = {"lf": b1[7], "rf": b1[6], "lr": b1[4], "rr": b1[5], "trunk": b1[2]}
    new_data = [b1[7], b1[6], b1[4], b1[5], b1[2]]

    return new_data


@pyqtSlot(bytearray)
def boost_pressure(data: bytearray) -> float:
    return data[4] * 0.3 - 15.1


@pyqtSlot(bytearray)
def check_engine_light(data: bytearray) -> float:
    b4 = f"{data[4]:08b}"

    return int(b4[7], 2)


@pyqtSlot(bytearray)
def gear(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"[4:]

    b6int = int(b6, 2)

    if b6int == 7 or b6int == 0:
        return 0

    return b6int
