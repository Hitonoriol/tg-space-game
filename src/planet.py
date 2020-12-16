import utils

resources_per_lvl = 25


class Planet:
    def __init__(self, resource):
        self.name = utils.rand_str(6)
        self.resource = resource
        self.resource_amount = 0
        self.last_check = utils.now()

    def set_resource_amount(self, amt):
        self.resource_amount = amt

    def time_passed(self, now):
        passed = now - self.last_check
        self.last_check = now
        return passed
