import can_handle
import can
from random import choice, randrange

turn_signal_data = [
    [0x0F, 0x04, 0x00, 0x00, 0x00, 0x30, 0x00, 0x00],  # hazards
    [0x0F, 0x04, 0x00, 0x00, 0x00, 0x20, 0x00, 0x00],  # right turn
    [0x0F, 0x04, 0x00, 0x00, 0x00, 0x10, 0x00, 0x00],  # left turn
    [0x0F, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]  # everything off
]


def provide_random_message():
    key, val = choice(list(can_handle.can_ids.items()))
    data = [0, 0, 0, 0, 0, 0, 0, 0]
    if key == "turn_signals":
        data = choice(turn_signal_data)
    elif key in ["oil_temp", "coolant_temp"]:
        data = [
            0, 0,
            randrange(0, int((0xfa - 32) / 1.8)),
            randrange(0, int((0xfa - 32) / 1.8)), 0, 0, 0, 0
        ]
    elif key in ["headlights", "handbrake", "reverse_switch", "brake_switch"]:
        data = [0, 0, 0, 0, 0, 0, int(f'0000{randrange(0,2)}000', 2), 0]
    elif key in ["rpm", "neutral_switch"]:
        data = [
            0x00, 0x00, 0x00, 0x00,
            randrange(0, 256),
            randrange(0, 256), 0x00, 0x00
        ]
    elif key in ["vehicle_speed", "brake_pedal_position"]:
        speed_range_2 = 180 // 14
        data = [0, randrange(0, speed_range_2 + 1), 0, 0, 0, 0, 0, 0]
    return can.Message(arbitration_id=val, data=data)
