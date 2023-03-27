import enum


class RGB(enum.Enum):
    RED = 'RED'
    GREEN = 'GREEN'
    BLUE = 'BLUE'


class ChunkingStrategy(enum.Enum):
    CARROT = 'carrot'
    POTATO = 'potato'
    SPINACH = 'spinach'
