from enum import Enum, auto


class ResourceType(Enum):
    Solid = auto()
    Liquid = auto()
    Metal = auto()
    Fuel = auto()


class Resource(Enum):
    Iron = (auto(), ResourceType.Metal)
    Copper = (auto(), ResourceType.Metal)
    Organics = auto()
    Peat = (auto(), ResourceType.Fuel)
    Stone = auto()
    Sand = auto()
    Water = (auto(), ResourceType.Liquid)
    Oil = (auto(), ResourceType.Fuel)
    Uranium = (auto(), ResourceType.Fuel)

    def __init__(self, id, type: ResourceType = ResourceType.Solid):
        self.id = id
        self.type = type


resource_list = list(Resource)
