import utils
import icons
from resource import *


class Upgradeable:
    def __init__(self, upgrade_by=1, upgrade_multiplier=0.5, initial_cost=1):
        self.upgrade_lvl = 1
        self.upgrade_amount = upgrade_by
        self.upgrade_multiplier = upgrade_multiplier
        self.upgrade_cost = initial_cost

    def upgrade(self):
        self.upgrade_lvl += 1
        self.upgrade_cost += self.upgrade_cost * self.upgrade_multiplier


class Cargo(Upgradeable):
    def __init__(self):
        super().__init__(upgrade_by=25, upgrade_multiplier=0.20, initial_cost=15)
        self.cur_weight = 0
        self.max_weight = 25
        self.contents = {}

    def get(self, resource: Resource) -> float:
        return self.contents.get(resource, 0)

    def put(self, resource: Resource, quantity: float) -> float:
        overflow: float = 0
        self.cur_weight += quantity
        if self.cur_weight > self.max_weight:
            overflow = self.cur_weight - self.max_weight
            self.cur_weight = self.max_weight

        self.contents[resource] = self.get(resource) + (quantity - overflow)
        return overflow

    def remove(self, resource: Resource, quantity: float) -> bool:
        if not self.contains(resource, quantity):
            return False

        self.cur_weight -= quantity
        self.contents[resource] = self.get(resource) - quantity

        if self.cur_weight < 0:
            self.cur_weight = 0

        return True

    def contains(self, resource: Resource, quantity: float) -> bool:
        if self.get(resource) >= quantity:
            return True

        return False

    def upgrade(self):
        super().upgrade()
        self.max_weight += self.upgrade_amount

    def is_empty(self) -> bool:
        return not self.contents

    def is_full(self) -> bool:
        return self.cur_weight == self.max_weight

    def get_cargo_header_str(self):
        return (icons.box + " Cargo bay " +
                "[" + utils.round_str(self.cur_weight) + "/" + utils.round_str(self.max_weight) + " kg]")


class Entity:
    def __init__(self):
        self.name = utils.rand_str(15)

        self.hp = 25
        self.max_hp = self.hp

        self.shield = 1
        self.shield_max = self.shield

        self.atk = 1
        self.dead = False

        self.cargo = Cargo()

    def check_stats(self):
        self.hp = max(self.hp, 0)
        if self.hp == 0:
            self.dead = True

    def get_shield_percent(self) -> float:
        return self.shield / self.shield_max

    def take_shield_damage(self, amount):
        self.shield -= amount
        dmg_overflow = 0
        if self.shield < 0:
            dmg_overflow = abs(self.shield)
            self.shield = 0
        return dmg_overflow

    def take_damage(self, amount: int):
        self.hp -= amount
        self.check_stats()

    def attack(self, enemy: 'Entity'):
        enemy_shield = enemy.get_shield_percent()
        atk = self.atk - (self.atk * enemy_shield)

        if enemy_shield > 0:
            atk += enemy.take_shield_damage(max(atk, 1))

        enemy.take_damage(int(atk))

    def get_stat_str(self) -> str:
        stats = (icons.hp + " Hull integrity: " + str(self.hp) + "/" + str(self.max_hp) + "\n" +
                 icons.defense + " Shield: " + str(self.shield) + "/" + str(self.shield_max) + "\n" +
                 icons.atk + " Firepower: " + str(self.atk) + "\n"
                 )
        return stats


class Mob(Entity):
    def __init__(self):
        super().__init__()
