import can_handle
import can
from random import choice, randrange

# todo: make testing UI with controls for everything

turn_signal_data = [
    0x30,  # hazards
    0x20,  # right turn
    0x10,  # left turn
    0x00,  # everything off
]


def provide_random_message() -> can.Message:
    key, val = choice(list(can_handle.CAN_IDS.items()))
    data = [0, 0, 0, 0, 0, 0, 0, 0]
    if key in ["turn_signals", "fuel_level", "seatbelt_driver"]:
        data = [
            randrange(0x25, 0xFF),
            int(f"{choice([0x01, 0x02]):8b}0000", 2),  # todo: fix fuel level
            0,
            0,
            0,
            int(f"00{randrange(0, 2)}{randrange(0, 2)}000{randrange(0, 2)}", 2),
            0,
            0,
        ]
    elif key in [
        "oil_temp",
        "coolant_temp",
        "cruise_control_speed",
        "cruise_control_status",
        "cruise_control_set",
    ]:
        data = [
            0,
            0,
            randrange(0, int((0xFA - 32) / 1.8)),
            randrange(0, int((0xFA - 32) / 1.8)),
            0,
            int(f"00{randrange(0,2)}{randrange(0,2)}0000", 2),
            0,
            randrange(0, 256),
        ]
    elif key in ["headlights", "handbrake_switch", "reverse_switch", "brake_switch"]:
        data = [
            0,
            0,
            0,
            0,
            0,
            0,
            int(f"00{randrange(0,2)}0{randrange(0,2)}000", 2),
            int(
                f"000{randrange(0,2)}{randrange(0,2)}{randrange(0,2)}{randrange(0,2)}0",
                2,
            ),
        ]
    elif key == "door_states":
        data = [
            0,
            int(
                f"00{randrange(0,2)}0{randrange(0,2)}{randrange(0,2)}{randrange(0,2)}{randrange(0,2)}",
                2,
            ),
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    elif key in ["rpm", "gear"]:
        rpm = f"{randrange(0, 8001):016b}"
        data = [0, 0, 0, 0, int(rpm[8:], 2), int(rpm[:8], 2), randrange(0, 8), 0]
    elif key in ["vehicle_speed", "brake_pedal_position"]:
        data = [0, randrange(0, 180 // 14 + 1), 0, 0, 0, 0, 0, 0]
    elif key in ["throttle_pedal_position", "throttle_plate_position", "clutch_switch"]:
        data = [0, int(f"{randrange(0,2)}0000000", 2), 0, 0, 0, 0, 0, 0]
    elif key in ["traction_control", "traction_control_mode"]:
        data = [
            int(f"0000{randrange(0,2)}000", 2),
            int(f"0000{randrange(0,2)}000", 2),
            0,
            0,
            0,
            0,
            0,
            0,
        ]
    elif key == "fog_lights":
        data = [0, int(f"0{randrange(0,2)}000000", 2), 0, 0, 0, 0, 0, 0]
    elif key in ["check_engine_light", "oil_pressure_warning"]:
        data = [0, 0, 0, 0, int(f"{randrange(0,2)}0000000", 2), 0, 0, 0]
    elif key == "odometer":
        num = randrange(0, 1000000) * 10
        num = f"{num:032b}"

        data = [
            int(num[-8:], 2),
            int(num[-16:-8], 2),
            int(num[-24:-16], 2),
            int(num[-32:-24], 2),
            0,
            0,
            0,
            0,
        ]

    return can.Message(is_extended_id=False, arbitration_id=val, data=data)


def get_response_data(pid) -> list:
    for i, v in can_handle.CURRENT_DATA_DEFINITION_ITEMS:
        if v["pid"] == pid:
            if i == "engine_load":
                return [randrange(0, 256)]
            elif i == "fuel_pressure":
                return [randrange(0, 766) // 3]
            elif i == "intake_manifold_absolute_pressure":
                return [randrange(0, 256)]
        return []


def provide_response_message(recv_msg: can.Message) -> can.Message | list[can.Message]:
    if recv_msg.arbitration_id == can_handle.CONVERSATION_IDS["send_id"]:
        data = recv_msg.data

        response_data = get_response_data(data[2])

        new_data = [0x55 for _ in range(8)]
        new_data[0] = 0x03
        new_data[1] = data[1] + 0x40
        new_data[2] = data[2]
        new_data[3 : 3 + len(response_data)] = response_data
        new_data = new_data[:8]

        return can.Message(
            is_extended_id=False,
            arbitration_id=can_handle.CONVERSATION_IDS["ecu_response_id"],
            data=new_data,
        )
