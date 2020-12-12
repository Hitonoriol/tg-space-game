from enum import Enum, auto


class Resources(Enum):
    Iron = auto()
    Copper = auto()
    Organics = auto()
    Stone = auto()
    Sand = auto()
    Water = auto()
    Oil = auto()
    Uranium = auto()


resource_list = list(Resources)
