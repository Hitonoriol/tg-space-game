import random
import enum

import globals
from planet import *
from resource import *


class Action(Enum):
    PLANET_SEARCH = enum.auto()


class PendingAction:
    def __init__(self, uid: int, action: Action, length: int):
        self.uid = uid
        self.action = action
        self.start_time = utils.now()
        self.length = length


action_lengths = {Action.PLANET_SEARCH: 3}


class Cargo:
    def __init__(self):
        self.cur_weight = 0
        self.max_weight = 25
        self.contents = {}

    def get(self, resource: Resource):
        return self.contents.get(resource, 0)

    def put(self, resource: Resource, quantity: float):
        res = 0
        self.cur_weight += quantity
        if self.cur_weight > self.max_weight:
            res = self.max_weight - self.cur_weight
            self.cur_weight = self.max_weight

        self.contents[resource] = self.get(resource) + (quantity - res)
        return res

    def remove(self, resource: Resource, quantity: float):
        if not self.contains(resource, quantity):
            return False

        self.cur_weight -= quantity
        self.contents[resource] = self.get(resource) - quantity

    def contains(self, resource: Resource, quantity: float):
        if self.get(resource) >= quantity:
            return True

        return False

    def is_empty(self):
        return not self.contents


class Player:
    PROGRESS_NTF_MIN_TIME = 600

    face_icon = "👦"
    money_icon = "💵"
    exp_icon = "✨"
    planet_icon = "🪐"
    box_icon = "📦"
    resource_icon = "💎"
    levelup_icon = "🎉"
    time_icon = "🕛"
    progress_icon = "⌛"
    shuttle_icon = "🚀"
    bulletpoint_icon = "⚫"

    extraction_rate = 0.075
    exp_multiplier = 1.195

    send_shuttle_exp = 4

    def __init__(self, id=0, name=""):
        self.name = name
        self.id = id

        self.last_check = utils.now()

        self.money = 100
        self.lvl = 1
        self.exp = 0
        self.required_exp = 50

        self.drill_lvl = 1

        self.pending_actions = []

        self.cargo = Cargo()
        self.planets = []
        self.shuttles = []

    def level_up(self):
        self.exp = 0
        self.required_exp += int(self.required_exp * self.exp_multiplier)
        self.lvl += 1

        msg = self.levelup_icon + " Level Up! You are now a level " + str(self.lvl) + " captain."
        globals.bot.send_message(self.id, msg)

    def add_exp(self, amt: int):
        if amt < 1:
            return

        self.exp += amt

        msg = self.exp_icon + " You get +" + str(amt) + " experience!"
        globals.bot.send_message(self.id, msg)

        if self.exp >= self.required_exp:
            self.level_up()

    def has_more_pending_actions(self):
        return len(self.pending_actions) > 0

    def start_timed_action(self, action: Action):
        global action_lengths
        globals.pending_players.append(str(self.id))
        self.pending_actions.append(PendingAction(self.id, action, action_lengths[action]))
        self.start_action(action)

    def start_action(self, action: Action):
        global action_lengths
        if action == Action.PLANET_SEARCH:
            msg = (self.shuttle_icon + " You send one of your shuttles to search for a new planet...\n\n" +
                   "" + self.time_icon + " It will return in " + utils.time_str(action_lengths[Action.PLANET_SEARCH]) + ".")
            globals.bot.send_message(self.id, msg)

    def complete_action(self, action: Action):
        if action == Action.PLANET_SEARCH:
            self.find_planet()

    def check_pending_action(self, action: PendingAction):
        if utils.now() - action.start_time >= action.length:
            self.complete_action(action.action)
            return True
        else:
            return False

    def check_pending_actions(self):
        for action in self.pending_actions[:]:
            if self.check_pending_action(action):
                self.pending_actions.remove(action)

    def check_progress(self, verbose: bool = False):
        now = utils.now()
        time_passed = now - self.last_check
        minutes_passed = time_passed / 60
        self.last_check = now
        depleted_msg = ""
        msg = (self.progress_icon + " Progress\n" +
               "[" + utils.time_str(time_passed) + " since last check]\n\n")

        resources_extracted = {}
        resources_remain = {}
        for planet in self.planets[:]:
            extracted = self.extraction_rate * minutes_passed

            if planet.resource_amount - extracted <= 0:
                extracted = planet.resource_amount
                planet.resource_amount = 0
                self.planets.remove(planet)
            else:
                planet.resource_amount -= extracted

            self.cargo.put(planet.resource, extracted)
            resources_extracted[planet.resource] = resources_extracted.get(planet.resource, 0) + extracted
            resources_remain[planet.resource] = resources_remain.get(planet.resource, 0) + planet.resource_amount

            if planet.resource_amount == 0:
                depleted_msg += self.planet_icon + " " + planet.name + " is out of " + planet.resource.name + "!\n"

        if resources_extracted:
            msg += "Your drills have extracted:\n"
        else:
            msg += "You don't have any planets in your celestial body database."

        for resource, amount in resources_extracted.items():
            msg += (self.bulletpoint_icon + " " + str(round(amount, 2)) + " kg of " + resource.name + "" +
                    " (" + str(round(resources_remain[resource], 2)) + " kg left)" + "\n")

        if time_passed >= self.PROGRESS_NTF_MIN_TIME or verbose:
            globals.bot.send_message(self.id, msg)

        if len(depleted_msg) > 0:
            globals.bot.send_message(self.id, depleted_msg)

    def add_money(self, quantity: float):
        if quantity <= 0:
            return

        self.money += quantity
        msg = self.money_icon + " You receive +" + utils.round_str(quantity) + " credits."
        globals.bot.send_message(self.id, msg)

    def sell_resource(self, resource: Resource, quantity: int):
        if quantity < 1:
            return False

        if not self.cargo.contains(resource, quantity):
            globals.bot.send_message(self.id, "You don't have this quantity of " + resource.name + " in your cargo bay!")
            return False

        self.cargo.remove(resource, quantity)
        self.add_money(resource_prices.get(resource, 0))
        globals.bot.send_message(self.id, "Successfuly sold " + str(quantity) + " kg of " + resource.name + ".")

        return True

    def find_planet(self):
        planet = Planet(random.choice(resource_list))

        base_resources = self.lvl * resources_per_lvl
        planet.set_resource_amount(random.uniform(base_resources * 0.15, base_resources))
        self.planets.append(planet)

        msg = ("You found a new planet!\n\n" +
               self.planet_icon + " Name: " + planet.name + "\n" +
               self.resource_icon + " Resource type: " + planet.resource.name + "\n" +
               self.box_icon + " Resource amount: " + str(round(planet.resource_amount, 2)) + " kg\n")

        globals.bot.send_message(self.id, msg)
        self.add_exp(int(planet.resource_amount * 0.2))

    def show_profile(self):
        msg = (" Captain " + self.face_icon + " " + self.name + "\n\n" +
               self.exp_icon + " Level " + str(self.lvl) + " [" + str(self.exp) + "/" + str(self.required_exp) + "] " +
               "(" + str(round((self.exp / self.required_exp) * 100)) + "%)\n" +
               self.money_icon + " Credits: " + str(self.money) + "\n" +
               self.planet_icon + " Planets found: " + str(len(self.planets))
               )
        globals.bot.send_message(self.id, msg)

    def show_cargo(self):
        self.check_progress()
        msg = (self.box_icon + " Cargo bay " +
               "[" + utils.round_str(self.cargo.cur_weight) + "/" + utils.round_str(self.cargo.max_weight) + " kg]\n\n")

        for resource, quantity in self.cargo.contents.items():
            msg += (self.bulletpoint_icon + " " + resource.name + ": " + utils.round_str(quantity) + " kg    " +
                    "/sell_" + resource.name + "_1" + "\n"
                    )

        if self.cargo.is_empty():
            msg += "Your cargo bay is completely empty!"

        globals.bot.send_message(self.id, msg)
