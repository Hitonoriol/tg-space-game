import random
import enum

import strings
import globals
from planet import *
from entity import *


class Action(Enum):
    PLANET_SEARCH = enum.auto()


class PendingAction:
    def __init__(self, uid: int, action: Action, length: int):
        self.uid = uid
        self.action = action
        self.start_time = utils.now()
        self.length = length
        self.ready = False


action_lengths = {Action.PLANET_SEARCH: 5}


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
        if idle_shuttles:
            return idle_shuttles[0]

    def find_by_departure(self, departure_time: int) -> Shuttle:
        for shuttle in self.shuttles:
            if shuttle.departure_time == departure_time:
                return shuttle


class PlanetContainer:
    upgrade_amount = 3
    upgrade_multiplier = 0.25

    def __init__(self):
        self.max_planets = 5
        self.planet_count = 0
        self.planets = []
        self.upgrade_cost = 10

    def add_planet(self, planet: Planet):
        if self.planet_count + 1 > self.max_planets:
            return
        self.planet_count += 1
        self.planets.append(planet)

    def remove_planet(self, planet: Planet):
        self.planet_count -= 1
        self.planets.remove(planet)

    def get_resource_reserves(self):
        resources = {}
        for planet in self.planets:
            resources[planet.resource] = resources.get(planet.resource, 0) + planet.resource_amount
        return resources

    def get_extraction_rate(self, resource: Resource):
        rate = 0
        for planet in self.planets:
            if planet.resource == resource:
                rate += 1
        return rate

    def upgrade(self):
        self.max_planets += self.upgrade_amount
        self.upgrade_cost += self.upgrade_cost * self.upgrade_multiplier

    def get_pcount_str(self):
        return str(self.planet_count) + "/" + str(self.max_planets)

    def is_full(self):
        return self.planet_count == self.max_planets


class Player(Entity):
    PROGRESS_NTF_MIN_TIME = 900

    shuttle_price = 50

    extraction_rate = 0.085
    exp_multiplier = 1.195

    send_shuttle_exp = 4

    def __init__(self, id=0, name=""):
        super().__init__()
        self.name = name
        self.id = id

        self.last_check = utils.now()

        self.money = self.shuttle_price
        self.lvl = 1
        self.exp = 0
        self.required_exp = 50

        self.drill_lvl = 1

        self.pending_actions = []

        self.planet_container = PlanetContainer()
        self.shuttle_hangar = ShuttleHangar()

    def buy_shuttle(self):
        if self.money < self.shuttle_price:
            self.notify("You don't have enough money to buy a new shuttle!")
            return

        self.pay_money(self.shuttle_price)
        shuttle = Shuttle()
        self.shuttle_hangar.shuttles.append(shuttle)
        self.notify("Bought a new shuttle: " + icons.shuttle + " " + shuttle.name)

    def level_up(self):
        self.exp = 0
        self.required_exp += int(self.required_exp * self.exp_multiplier)
        self.lvl += 1

        msg = icons.levelup + " Level Up! You are now a level " + str(self.lvl) + " captain."
        self.notify(msg)

    def add_exp(self, amt: int):
        if amt < 1:
            return

        self.exp += amt

        msg = icons.exp + " You get +" + str(amt) + " experience!"
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

        if self.planet_container.is_full():
            self.notify("Your celestial database is full!")
            return

        shuttle.depart(self.pending_actions[-1].start_time)

        self.notify("You send your " + icons.shuttle + " " + shuttle.name + " shuttle to search for a new planet...\n\n" +
                    icons.time + " It will return in " + utils.time_str(action_lengths[Action.PLANET_SEARCH]) + ".")
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
        msg = (icons.progress + " Progress\n" +
               "[" + utils.time_str(time_passed) + " since last check]\n\n")

        resources_extracted = {}
        resources_remain = {}
        for planet in self.planet_container.planets[:]:
            if self.cargo.is_full():
                break
            extracted = self.extraction_rate * (planet.time_passed(now) / 60)

            if planet.resource_amount - extracted <= 0:
                extracted = planet.resource_amount
                planet.resource_amount = 0
            else:
                planet.resource_amount -= extracted

            overflow = self.cargo.put(planet.resource, extracted)
            planet.resource_amount += overflow
            extracted -= overflow

            if extracted <= 0:
                extracted = 0

            resources_extracted[planet.resource] = resources_extracted.get(planet.resource, 0) + extracted
            resources_remain[planet.resource] = resources_remain.get(planet.resource, 0) + planet.resource_amount

            if planet.resource_amount == 0:
                self.planet_container.remove_planet(planet)
                depleted_msg += icons.planet + " " + planet.name + " is out of " + planet.resource.name + "!\n"

        if resources_extracted:
            msg += "Your drills have extracted:\n"
        elif self.cargo.is_full():
            msg += "Your cargo bay is full!"
        else:
            msg += "You don't have any planets in your celestial body database."

        for resource, amount in resources_extracted.items():
            msg += (icons.bulletpoint + " " + str(round(amount, 2)) + " kg of " + resource.name + "" +
                    " (" + str(round(resources_remain[resource], 2)) + " kg left)" + "\n")

        if time_passed >= self.PROGRESS_NTF_MIN_TIME or verbose:
            self.notify(msg)

        if len(depleted_msg) > 0:
            self.notify(depleted_msg)

    def add_money(self, quantity: float):
        if quantity <= 0:
            return

        self.money += quantity
        msg = icons.money + " You receive +" + utils.round_str(quantity) + " credits."
        self.notify(msg)

    def pay_money(self, quantity: float):
        if self.money - quantity < 0:
            return
        self.money -= quantity
        self.notify("You paid " + icons.money + utils.round_str(quantity) + "\n" +
                    "Current balance: " + icons.money + utils.round_str(self.money))

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
        self.planet_container.add_planet(planet)

        self.notify("You found a new planet!\n\n" +
                    icons.planet + " Name: " + planet.name + "\n" +
                    icons.resource + " Resource type: " + planet.resource.name + "\n" +
                    icons.box + " Resource amount: " + str(round(planet.resource_amount, 2)) + " kg\n"
        )
        self.add_exp(int(planet.resource_amount * 0.2))

    def show_profile(self):
        self.check_progress()
        self.notify(" Captain " + icons.face + " " + self.name + "\n" +
                    icons.exp + " Level " + str(self.lvl) + " [" + str(self.exp) + "/" + str(self.required_exp) + "] " +
                    "(" + str(round((self.exp / self.required_exp) * 100)) + "%)\n" +
                    icons.money + " Credits: " + utils.round_str(self.money) + "\n\n" +
                    "Stats:\n" +
                    self.get_stat_str() + "\n" +
                    "Ship:\n" +
                    self.cargo.get_cargo_header_str() + strings.tab + "/show_cargo\n" +
                    icons.planet + " Planets found: " + str(self.planet_container.planet_count) + strings.tab + "/celestial_database\n" +
                    icons.shuttle + " Shuttles: " + str(len(self.shuttle_hangar.shuttles))
        )

    def show_cargo(self):
        self.check_progress()
        msg = self.cargo.get_cargo_header_str() + "\n\n"

        for resource, quantity in self.cargo.contents.items():
            msg += (icons.bulletpoint + " " + resource.name + ": " + utils.round_str(quantity) + " kg" + strings.tab +
                    ("/sell_" + resource.name + "_1 ", "/sell_" + resource.name + "_all")[quantity > 1] + " " +
                    "(" + icons.money + str(resource.value.price) + " per kg)" + "\n"
                    )

        if self.cargo.is_empty():
            msg += "Your cargo bay is completely empty!"
        else:
            msg += "\n" + "/upgrade_cargo " + icons.money + utils.round_str(self.cargo.upgrade_cost)

        self.notify(msg)

    def view_shop(self):
        self.notify(icons.shop + " Shop\n" +
                    "Your credits: " + icons.money + " " + utils.round_str(self.money) + "\n\n" +
                    icons.shuttle + " Buy 1 shuttle for " + str(self.shuttle_price) + " " + icons.money + strings.tab + "/buy_shuttle \n")

    def view_planet_list(self):
        self.check_progress()
        msg = (icons.planet_list + " Celestial Body Database " +
               "[" + self.planet_container.get_pcount_str() + "]\n\n"
               )

        if self.planet_container.planet_count == 0:
            msg += "Your database is empty!\n"
        else:
            msg += "Planets by resource:\n"

        resources = self.planet_container.get_resource_reserves()
        for resource, quantity in resources.items():
            msg += (icons.bulletpoint + " " + resource.name + ": " + utils.round_str(quantity) + " kg" + strings.tab +
                    icons.resource_extraction +
                    utils.round_str(self.planet_container.get_extraction_rate(resource) * self.extraction_rate) + " kg/min\n"
                    )
        msg += "\n" + "/upgrade_celestial_database " + icons.money + utils.round_str(self.planet_container.upgrade_cost)

        self.notify(msg)

    def upgrade(self, thing):
        if self.money < thing.upgrade_cost:
            self.notify("You don't have enough credits for this upgrade!")
            return
        self.pay_money(thing.upgrade_cost)
        thing.upgrade()

    def notify(self, msg):
        globals.bot.send_message(self.id, msg)
