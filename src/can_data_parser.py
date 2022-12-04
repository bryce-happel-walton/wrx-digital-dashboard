speed_mult = 0.05625


def rpm(data: bytearray) -> int:
    b4 = f"{data[4]:08b}"
    b5 = f"{data[5]:08b}"[-5:]
    return int(b5 + b4, base=2)


def vehicle_speed(data: bytearray) -> float:
    b0 = f"{data[0]:08b}"
    b1 = f"{data[1]:08b}"
    return int(b1 + b0, base=2) * speed_mult


def cruise_control_speed(data: bytearray) -> int:
    print(f"{data[6]:08b} {data[7]:08b}", end='\r')
    return data[7]


def turn_signals(data: bytearray) -> dict[str, int]:
    b5 = f"{data[5]:08b}"

    new_data = {
        "left_turn_signal": int(b5[3]),
        "right_turn_signal": int(b5[2])
    }

    return new_data


temp_sensor_offset = -40


def oil_temp(data: bytearray) -> int:
    b2 = f"{data[2]:08b}"
    return (int(b2, 2) + temp_sensor_offset)


def coolant_temp(data: bytearray) -> int:
    b3 = f"{data[3]:08b}"
    return (int(b3, 2) + temp_sensor_offset)


def neutral_switch(data: bytearray) -> bool:
    return data[6] == 39


def handbrake(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"
    return int(b6[4], 2)


def reverse_switch(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"
    return int(b6[5], 2)


def clutch_switch(data: bytearray) -> int:
    b2 = f"{data[2]:08b}"
    return int(b2[0], 2)


def cruise_control_status(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"
    return int(b6[7], 2)


def seatbelt_driver(data: bytearray) -> int:
    b5 = f"{data[5]:08b}"
    return int(b5[7], 2)


def dimmer_dial(data: bytearray) -> int:
    return data[0]


def traction_control(data: bytearray) -> int:
    b1 = f"{data[1]:08b}"
    return int(b1[4], 2)


def trac_mode(data: bytearray) -> int:
    b0 = f"{data[0]:08b}"
    return int(b0[4], 2)


def fog_lights(data: bytearray) -> int:
    b1 = f"{data[1]:08b}"
    return int(b1[1], 2)


def headlights(data: bytearray) -> dict[str, int]:
    # b7b = f"{data[7]:08b}"
    b7 = data[7]

    low = 0x8C
    nothing = 0x80
    pull_high = 0x98
    high = 0x9C
    drl_and_dim = 0x84
    drl_day = 0x82

    new_data = {
        "lowbeams": b7 == low,
        "drls": 1 if b7 == drl_and_dim else 2 if b7 == drl_day else 0,
        "highbeams": b7 in [pull_high, high]
    }

    return new_data


def door_states(data: bytearray) -> dict[str, int]:
    b1 = f"{data[1]:08b}"

    new_data = {
        "lf": b1[7],
        "rf": b1[6],
        "lr": b1[4],
        "rr": b1[5],
        "trunk": b1[2]
    }

    return new_data


if __name__ == "__main__":
    from time import time
    # rpm
    start = time()
    array = [0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00]
    data = bytearray(array)
    rpm(data)
    print(time() - start)

    # vehicle speed
    start = time()
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    data = bytearray(array)
    vehicle_speed(data)
    print(time() - start)

    # steering wheel left stock
    start = time()
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]  # everything off
    data = bytearray(array)
    turn_signals(data)
    print(time() - start)

    start = time()
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x10, 0x00,
             0x00]  # left turn signal
    data = bytearray(array)
    turn_signals(data)
    print(time() - start)

    start = time()
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x20, 0x00,
             0x00]  # right turn signal
    data = bytearray(array)
    turn_signals(data)
    print(time() - start)
