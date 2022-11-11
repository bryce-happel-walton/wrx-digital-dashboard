speed_mult = 0.05625
to_mph = 0.62137119
speed_mult *= to_mph

def rpm(data: bytearray) -> int:
    b4 = f"{data[4]:08b}"
    b5 = f"{data[5]:08b}"[-4:]
    return int(b5 + b4, base=2)

def vehicle_speed(data: bytearray) -> int:
    b1 = f"{data[0]:08b}"
    b2 = f"{data[1]:08b}"
    return int(int(b2 + b1, base=2) * speed_mult)


if __name__ == "__main__":
    array = [0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0x00, 0x00]
    data = bytearray(array)
    print(rpm(data))

    array = [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    data = bytearray(array)
    print(vehicle_speed(data))
