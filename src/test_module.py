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
    elif key in ["oil_temp", "coolant_temp", "cruise_control_speed", "cruise_control_status", "cruise_control_set"]:
        data = [
            0, 0,
            randrange(0, int((0xfa - 32) / 1.8)),
            randrange(0, int((0xfa - 32) / 1.8)), 0,
            int(f"00{randrange(0,2)}{randrange(0,2)}0000", 2), 0,
            randrange(0, 256)
        ]
    elif key in ["headlights", "handbrake", "reverse_switch", "brake_switch"]:
        data = [
            0, 0, 0, 0, 0, 0,
            int(f'00{randrange(0,2)}0{randrange(0,2)}000', 2),
            choice([0x8C, 0x80, 0x98, 0x9C, 0x84, 0x82])
        ]
    elif key == "door_states":
        data = [
            0,
            int(f"00{randrange(0,2)}0{randrange(0,2)}{randrange(0,2)}{randrange(0,2)}{randrange(0,2)}", 2), 0, 0, 0, 0,
            0, 0
        ]
    elif key in ["rpm", "neutral_switch"]:
        data = [0, 0, 0, 0, randrange(0, 256), randrange(0, 256), choice([27, 20]), 0]
    elif key in ["vehicle_speed", "brake_pedal_position"]:
        data = [0, randrange(0, 180 // 14 + 1), 0, 0, 0, 0, 0, 0]
    elif key == "clutch_switch":
        data = [0, 0, choice([90, 89]), 0, 0, 0, 0, 0]
    elif key == "traction_control":
        data = [0, int(f"0000{randrange(0,2)}000", 2), 0, 0, 0, 0, 0, 0]
    elif key == "traction_control_mode":
        data = [int(f"0000{randrange(0,2)}000", 2), 0, 0, 0, 0, 0, 0, 0]
    elif key == "seatbelt_driver":
        data = [0, 0, 0, 0, 0, int(f"0000000{randrange(0,2)}", 2), 0, 0]
    elif key == "fog_lights":
        data = [0, int(f"0{randrange(0,2)}000000", 2), 0, 0, 0, 0, 0, 0]

    return can.Message(is_extended_id=False, arbitration_id=val, data=data)


def provide_response_message(recv_msg: can.Message) -> can.Message | list[can.Message]:
    if recv_msg.arbitration_id == can_handle.conversation_ids["send_id"]:
        data = [0, 0, 0, 0, 0, 0, 0, 0]
        return can.Message(is_extended_id=False, arbitration_id=can_handle.conversation_ids["response_id"], data=data)
