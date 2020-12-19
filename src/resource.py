from typing import NamedTuple
from enum import Enum
import utils


class ResourceType(Enum):
    Solid = 0
    Liquid = 1
    Metal = 2
    Fuel = 3
    Precious = 4


class ResourceContainer(NamedTuple):
    type: ResourceType
    price: float
    probability: float = 25


class Resource(Enum):
    Iron = ResourceContainer(type=ResourceType.Metal, price=1.25, probability=30)
    Copper = ResourceContainer(type=ResourceType.Metal, price=1, probability=35)

    Peat = ResourceContainer(type=ResourceType.Fuel, price=3.25, probability=20)
    Oil = ResourceContainer(type=ResourceType.Fuel, price=3.5, probability=10)
    Uranium = ResourceContainer(type=ResourceType.Fuel, price=4.25, probability=5)

    Water = ResourceContainer(type=ResourceType.Liquid, price=2.5, probability=7.5)

    Organics = ResourceContainer(type=ResourceType.Solid, price=2.5, probability=7)
    Stone = ResourceContainer(type=ResourceType.Solid, price=0.5, probability=50)
    Sand = ResourceContainer(type=ResourceType.Solid, price=0.75, probability=45)
    Dust = ResourceContainer(type=ResourceType.Solid, price=0.25)

    Opal = ResourceContainer(type=ResourceType.Precious, price=5, probability=2.5)
    Ruby = ResourceContainer(type=ResourceType.Precious, price=5.75, probability=2)
    Emerald = ResourceContainer(type=ResourceType.Precious, price=6.25, probability=1.75)
    Sapphire = ResourceContainer(type=ResourceType.Precious, price=6.85, probability=1.1)
    Diamond = ResourceContainer(type=ResourceType.Precious, price=7.5, probability=0.75)


resource_list = list(Resource)
resource_list.sort(key=lambda res: res.value.probability)


def roll_resource() -> Resource:
    roll = utils.rand_percent()
    for resource in resource_list:
        if utils.roll_result(roll, resource.value.probability):
            return resource

    return Resource.Dust
