import utils

resources_per_lvl = 25


class Planet:
    def __init__(self, resource):
        self.name = utils.rand_str(6)
        self.resource = resource
        self.resource_amount = 0

    def set_resource_amount(self, amt):
        self.resource_amount = amt
