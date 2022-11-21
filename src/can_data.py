speed_mult = 0.05625
to_mph = 0.62137119
speed_mult *= to_mph

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
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] # everything off
    data = bytearray(array)
    turn_signals(data)
    print(time() - start)

    start = time()
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x10, 0x00, 0x10] # left turn signal
    data = bytearray(array)
    turn_signals(data)
    print(time() - start)

    start = time()
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x20, 0x00, 0x20] # right turn signal
    data = bytearray(array)
    turn_signals(data)
    print(time() - start)
