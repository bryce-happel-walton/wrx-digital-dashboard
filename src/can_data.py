speed_mult = 0.05625

gear_ratios = {
    '1': 3.454,
    '2': 1.947,
    '3': 1.296,
    '4': 0.972,
    '5': 0.78,
    '6': 0.666,
    'r': 3.636,
    'final_drive': 4.111,
    'tire': 26
}


def rpm(data: bytearray) -> int:
    b4 = f"{data[4]:08b}"
    b5 = f"{data[5]:08b}"[-4:]
    return int(b5 + b4, base=2)


def vehicle_speed(data: bytearray) -> int:
    b0 = f"{data[0]:08b}"
    b1 = f"{data[1]:08b}"
    return int(int(b1 + b0, base=2) * speed_mult)


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


def neutral_switch(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"  #! No neutral switch activity observed here. Need to find correct address and bits
    return b6


def handbrake(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"
    return int(b6[4], 2)


def reverse_switch(data: bytearray) -> int:
    b6 = f"{data[6]:08b}"
    return int(b6[5], 2)


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
