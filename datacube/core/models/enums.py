import enum


class RGB(str, enum.Enum):
    RED = 'RED'
    GREEN = 'GREEN'
    BLUE = 'BLUE'


class ChunkingStrategy(str, enum.Enum):
    CARROT = 'carrot'
    POTATO = 'potato'
    SPINACH = 'spinach'


class SensorFamily(str, enum.Enum):
    OPTIC = "OPTIC"
    RADAR = "RADAR"
    MULTI = "MULTI"
    UNKNOWN = "UNKNOWN"
