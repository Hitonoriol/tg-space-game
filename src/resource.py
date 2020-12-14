from enum import Enum


class ResourceType(Enum):
    Solid = 0
    Liquid = 1
    Metal = 2
    Fuel = 3


class Resource(Enum):
    Iron = (0, ResourceType.Metal)
    Copper = (1, ResourceType.Metal)
    Organics = (2, ResourceType.Solid)
    Peat = (3, ResourceType.Fuel)
    Stone = (4, ResourceType.Solid)
    Sand = (5, ResourceType.Solid)
    Water = (6, ResourceType.Liquid)
    Oil = (7, ResourceType.Fuel)
    Uranium = (8, ResourceType.Fuel)

    def __init__(self, id, type: ResourceType = ResourceType.Solid):
        self.id = id
        self.type = type


resource_list = list(Resource)

resource_prices = {
    Resource.Iron: 0.25,
    Resource.Copper: 0.2,
    Resource.Organics: 0.5,
    Resource.Peat: 0.65,
    Resource.Stone: 0.1,
    Resource.Sand: 0.15,
    Resource.Water: 0.5,
    Resource.Oil: 0.7,
    Resource.Uranium: 0.85
}
