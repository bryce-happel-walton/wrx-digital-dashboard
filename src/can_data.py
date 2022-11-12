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

def left_sw_stock(data: bytearray) -> dict[str, int]:
    b7 = f"{data[7]:08b}"

    new_data = {
        "left_turn_signal": int(b7[3]),
        "right_turn_signal": int(b7[2])
    }

    return new_data

if __name__ == "__main__":
    # rpm
    array = [0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00]
    data = bytearray(array)
    print(rpm(data))

    # vehicle speed
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    data = bytearray(array)
    print(vehicle_speed(data))

    # steering wheel left stock
    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] # everything off
    data = bytearray(array)
    print(left_sw_stock(data))

    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10] # left turn signal
    data = bytearray(array)
    print(left_sw_stock(data))

    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20] # right turn signal
    data = bytearray(array)
    print(left_sw_stock(data))
