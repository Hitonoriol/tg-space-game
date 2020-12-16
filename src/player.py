import random
import enum

import strings
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
        self.ready = False


action_lengths = {Action.PLANET_SEARCH: 3}


class Cargo:
    def __init__(self):
        self.cur_weight = 0
        self.max_weight = 25
        self.contents = {}

    def get(self, resource: Resource) -> float:
        return self.contents.get(resource, 0)

    def put(self, resource: Resource, quantity: float) -> float:
        overflow: float = 0
        self.cur_weight += quantity
        if self.cur_weight > self.max_weight:
            overflow = self.max_weight - self.cur_weight
            self.cur_weight = self.max_weight

        self.contents[resource] = self.get(resource) + (quantity - overflow)
        return overflow

    def remove(self, resource: Resource, quantity: float) -> bool:
        if not self.contains(resource, quantity):
            return False

        self.cur_weight -= quantity
        self.contents[resource] = self.get(resource) - quantity
        return True

    def contains(self, resource: Resource, quantity: float) -> bool:
        if self.get(resource) >= quantity:
            return True

        return False

    def is_empty(self) -> bool:
        return not self.contents


class Shuttle:
    def __init__(self):
        self.name = utils.rand_str(3)
        self.lvl = 1
        self.hp = 50
        self.in_use = False
        self.departure_time = -1

    def depart(self, time: int):
        self.in_use = True
        self.departure_time = time

    def return_to_hangar(self):
        self.in_use = False
        self.departure_time = -1


class ShuttleHangar:
    def __init__(self):
        self.shuttles = []

    def get_idle_shuttles(self):
        idle_shuttles = []
        for shuttle in self.shuttles:
            if not shuttle.in_use:
                idle_shuttles.append(shuttle)
        return idle_shuttles

    def next_idle_shuttle(self) -> Shuttle:
        idle_shuttles = self.get_idle_shuttles()
        if not idle_shuttles:
            return
        else:
            return idle_shuttles[0]

    def find_by_departure(self, departure_time: int) -> Shuttle:
        for shuttle in self.shuttles:
            if shuttle.departure_time == departure_time:
                return shuttle

        return None


class Player:
    PROGRESS_NTF_MIN_TIME = 900

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
    shop_icon = "🛍️"
    bulletpoint_icon = "⚫"

    shuttle_price = 50

    extraction_rate = 0.075
    exp_multiplier = 1.195

    send_shuttle_exp = 4

    def __init__(self, id=0, name=""):
        self.name = name
        self.id = id

        self.last_check = utils.now()

        self.money = self.shuttle_price
        self.lvl = 1
        self.exp = 0
        self.required_exp = 50

        self.drill_lvl = 1

        self.pending_actions = []

        self.cargo = Cargo()
        self.planets = []
        self.shuttle_hangar = ShuttleHangar()

    def buy_shuttle(self):
        if self.money < self.shuttle_price:
            self.notify("You don't have enough money to buy a new shuttle!")
            return

        self.money -= self.shuttle_price
        shuttle = Shuttle()
        self.shuttle_hangar.shuttles.append(shuttle)
        self.notify("Bought a new shuttle: " + self.shuttle_icon + " " + shuttle.name + "\n\n" +
                    self.money_icon + " Credits left: " + str(self.money))

    def level_up(self):
        self.exp = 0
        self.required_exp += int(self.required_exp * self.exp_multiplier)
        self.lvl += 1

        msg = self.levelup_icon + " Level Up! You are now a level " + str(self.lvl) + " captain."
        self.notify(msg)

    def add_exp(self, amt: int):
        if amt < 1:
            return

        self.exp += amt

        msg = self.exp_icon + " You get +" + str(amt) + " experience!"
        self.notify(msg)

        if self.exp >= self.required_exp:
            self.level_up()

    def has_more_pending_actions(self):
        return len(self.pending_actions) > 0

    def start_timed_action(self, action: Action):
        global action_lengths
        globals.pending_players.append(str(self.id))
        pending_action = PendingAction(self.id, action, action_lengths[action])
        self.pending_actions.append(pending_action)
        if self.start_action(action):
            pending_action.ready = True
        else:
            self.pending_actions.remove(pending_action)

    def start_planet_search(self):
        shuttle = self.shuttle_hangar.next_idle_shuttle()
        if shuttle is None:
            self.notify("You don't have any shuttles left in your hangar!")
            return

        shuttle.depart(self.pending_actions[-1].start_time)

        self.notify("You send your " + self.shuttle_icon + " " + shuttle.name + " shuttle to search for a new planet...\n\n" +
                    self.time_icon + " It will return in " + utils.time_str(action_lengths[Action.PLANET_SEARCH]) + ".")
        return True

    def start_action(self, action: Action):
        global action_lengths
        if action == Action.PLANET_SEARCH:
            return self.start_planet_search()

    def complete_action(self, pending_action: PendingAction):
        if pending_action.action == Action.PLANET_SEARCH:
            self.find_planet(pending_action)

    def check_pending_action(self, action: PendingAction):
        if utils.now() - action.start_time >= action.length and action.ready:
            self.complete_action(action)
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
            extracted = self.extraction_rate * (planet.time_passed(now) / 60)

            if planet.resource_amount - extracted <= 0:
                extracted = planet.resource_amount
                planet.resource_amount = 0
                self.planets.remove(planet)
            else:
                planet.resource_amount -= extracted

            overflow = self.cargo.put(planet.resource, extracted)
            planet.resource_amount += overflow
            extracted -= overflow
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
            self.notify(msg)

        if len(depleted_msg) > 0:
            self.notify(depleted_msg)

    def add_money(self, quantity: float):
        if quantity <= 0:
            return

        self.money += quantity
        msg = self.money_icon + " You receive +" + utils.round_str(quantity) + " credits."
        self.notify(msg)

    def sell_resource(self, resource: Resource, quantity: int):
        if quantity < 1:
            return False

        if not self.cargo.contains(resource, quantity):
            self.notify("You don't have this quantity of " + resource.name + " in your cargo bay!")
            return False

        self.cargo.remove(resource, quantity)
        self.add_money(resource.value.price * quantity)
        self.notify("Successfuly sold " + str(quantity) + " kg of " + resource.name + ".")

        return True

    def find_planet(self, action: PendingAction):
        planet = Planet(roll_resource())
        self.shuttle_hangar.find_by_departure(action.start_time).return_to_hangar()

        base_resources = self.lvl * resources_per_lvl
        planet.set_resource_amount(random.uniform(base_resources * 0.15, base_resources))
        self.planets.append(planet)

        msg = ("You found a new planet!\n\n" +
               self.planet_icon + " Name: " + planet.name + "\n" +
               self.resource_icon + " Resource type: " + planet.resource.name + "\n" +
               self.box_icon + " Resource amount: " + str(round(planet.resource_amount, 2)) + " kg\n")

        self.notify(msg)
        self.add_exp(int(planet.resource_amount * 0.2))

    def show_profile(self):
        msg = (" Captain " + self.face_icon + " " + self.name + "\n\n" +
               self.exp_icon + " Level " + str(self.lvl) + " [" + str(self.exp) + "/" + str(self.required_exp) + "] " +
               "(" + str(round((self.exp / self.required_exp) * 100)) + "%)\n" +
               self.money_icon + " Credits: " + utils.round_str(self.money) + "\n" +
               self.planet_icon + " Planets found: " + str(len(self.planets))
               )
        self.notify(msg)

    def show_cargo(self):
        self.check_progress()
        msg = (self.box_icon + " Cargo bay " +
               "[" + utils.round_str(self.cargo.cur_weight) + "/" + utils.round_str(self.cargo.max_weight) + " kg]\n\n")

        for resource, quantity in self.cargo.contents.items():
            msg += (self.bulletpoint_icon + " " + resource.name + ": " + utils.round_str(quantity) + " kg" + strings.tab +
                    ("/sell_" + resource.name + "_1 ", "/sell_" + resource.name + "_all")[quantity > 1] + " "
                                                                                                          "(" + self.money_icon + " " + str(resource.value.price) + " per kg)" + "\n"
                    )

        if self.cargo.is_empty():
            msg += "Your cargo bay is completely empty!"
        else:
            msg += "\n" + "/upgrade_cargo"

        self.notify(msg)

    def view_shop(self):
        self.notify(self.shop_icon + " Shop\n" +
                    "Your credits: " + self.money_icon + " " + utils.round_str(self.money) + "\n\n" +
                    self.shuttle_icon + " Buy 1 shuttle for " + str(self.shuttle_price) + " " + self.money_icon + " credits    /buy_shuttle \n")

    def notify(self, msg):
        globals.bot.send_message(self.id, msg)
