from dataclasses import dataclass, field

CONFIG_PATH = "config"
LOCAL_DATA_PATH = "local/data.toml"


@dataclass(order=True)
class LocalData:
    odometer: float = 0
    fuel_level_avg: float = 0


@dataclass(order=True)
class CanDeviceConfig:
    channel: str = "can0"
    bustype: str = "socketcan"
    bitrate: int = 500000


@dataclass(order=True)
class Settings:
    units: str = "UIC"
    fonts: dict[str, str] = field(default_factory=lambda: {"main": "Montserrat-Bold"})


@dataclass
class TachometerDialConfig:
    min_unit: float = 0
    max_unit: float = 8000
    redline: int = 6700
    mid_sections: int = 4
    denomination: int = 1000
    visual_num_gap: int = 1000


@dataclass
class SpeedometerDialConfig:
    min_unit: float = 0
    max_unit: float = 180
    redline: int = max_unit + 1
    mid_sections: int = 2
    visual_num_gap: int = 20


@dataclass
class CoolantTempDialConfig:
    min_unit: float = 0
    max_unit: float = 400
    visual_num_gap: int = 50
    mid_sections: int = 2
    redline: float = 350
    blueline: float = 80


@dataclass
class FuelLevelDialConfig:
    min_unit: float = 0
    max_unit: float = 100
    visual_num_gap: int = 20
    redline: float = 101
    mid_sections: int = 3


@dataclass
class OilTempDialConfig:
    min_unit: float = 0
    max_unit: float = 250
    mid_sections: int = 3
    redline: float = 220
    blueline: float = 80


@dataclass(order=True)
class CarData:
    vehicle_speed: float = 0
    traction_control: bool = True
    traction_control_mode: bool = True
    hill_assist: bool = True
    wheel_speeds: list[float] = field(default_factory=lambda: [0, 0, 0, 0])
    throttle_pedal_position: float = 0
    throttle_plate_position: float = 0
    clutch_switch: bool = False
    rpm: int = 0
    gear: int = 0
    headlights: list[bool] = field(default_factory=lambda: [True, True, True, True])
    handbrake_switch: bool = True
    reverse_switch: bool = False
    brake_switch: bool = False
    fuel_level: float = 0
    turn_signals: list[bool] = field(default_factory=lambda: [True, True])
    seatbelt_driver: bool = False
    coolant_temp: int = 0
    oil_temp: int = 0
    cruise_control_speed: int = 0
    cruise_control_status: bool = False
    cruise_control_set: bool = False
    boost_pressure: float = 0
    fuel_consumption: float = 0
    oil_pressure_warning: bool = True
    check_engine_light: bool = True
    srs_airbag_system_warning_light: bool = True
    fog_lights: bool = True
    tpms_warning: bool = True
    door_states: list[bool] = field(default_factory=lambda: [True, True, True, True])
    dimmer_dial: int = 0
    odometer: float = 0
