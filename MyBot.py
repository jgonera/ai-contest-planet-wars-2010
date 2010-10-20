import logging
from math import sqrt


from planetwars import BaseBot, Game
from planetwars.universe2 import Universe2
from planetwars.planet2 import Planet2
from planetwars.universe import player

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class MyBot(BaseBot):

	def do_turn(self):
#		for target in self.universe.best_targets():
#			log.debug(target.target_coefficient())
		
		#TODO: DRY!!! check if defense is correct
		# defend
		for target in self.universe.my_planets:
			available_ships = 0
			longest_distance = 0
			best_sources = target.best_sources()
			
			for source in best_sources:
				if source.ship_count > source.safe_ship_count:
					available_ships += source.ship_count - source.safe_ship_count
					if source.distance(target) > longest_distance:
						longest_distance = source.distance(target)
		
			target_in_future = target.in_future(longest_distance)
			if target_in_future.owner == player.ME:
				continue
			if available_ships < target_in_future.ship_count:
				continue
			
			for source in best_sources:
				target_in_future = target.in_future(longest_distance)
				if source.ship_count > source.safe_ship_count and (not target_in_future.owner == player.ME):
#					log.debug(source.id)
#					log.debug(source.safe_ship_count)
					source.send_fleet(target, min(source.ship_count - source.safe_ship_count, target_in_future.ship_count + target_in_future.min_ship_count))
		
		# attack
		for target in self.universe.best_targets():
			available_ships = 0
			longest_distance = 0
			best_sources = target.best_sources()
			
			for source in best_sources:
				if source.ship_count > source.safe_ship_count + source.min_ship_count:
					available_ships += source.ship_count - source.safe_ship_count - source.min_ship_count
					if source.distance(target) > longest_distance:
						longest_distance = source.distance(target)
		
			target_in_future = target.in_future(longest_distance)
			if target_in_future.owner == player.ME:
				continue
			if available_ships < target_in_future.ship_count + target_in_future.min_ship_count:
				break
			
			for source in best_sources:
				target_in_future = target.in_future(longest_distance)
				if source.ship_count > source.safe_ship_count + source.min_ship_count and (not target_in_future.owner == player.ME):
#					log.debug(source.id)
#					log.debug(source.safe_ship_count)
					source.send_fleet(target, min(source.ship_count - source.safe_ship_count - source.min_ship_count, target_in_future.ship_count + target_in_future.min_ship_count))


class MyPlanet(Planet2):
	
	@property
	def min_ship_count(self):
		#TODO: works only for my ships, change it? if not my planet return 0?
		return len(self.universe.enemy_planets) * 2
	
	@property
	def safe_ship_count(self):
		if self.owner == player.ME:
			enemy = player.ENEMIES
		elif self.owner in player.ENEMIES:
			enemy = player.ME
		else:
			raise Exception("This doesn't work for neutral planets!")
#			
#		value = len(self.universe.find_planets(owner=enemy)) * 2
#		
#		#longest is flawed, need to sort fleets and check remaining turns for each fleet
#		longest = 0
#		for fleet in self.universe.find_fleets(owner=enemy):
#			if fleet.destination.id == self.id:
#				value += fleet.ship_count
#				if fleet.turns_remaining > longest:
#					longest = fleet.turns_remaining
#		
#		value -= longest * self.growth_rate
#		
#		return value
		
		enemy_fleets = sorted(
			self.universe.find_fleets(owner=enemy, destination=self),
			reverse=True,
			key=lambda fleet: fleet.turns_remaining
		)
		
		value = 0
		
		if len(enemy_fleets) != 0:
			in_future = self.in_future(enemy_fleets[0].turns_remaining)
		
			value += self.ship_count
			if self.owner == in_future.owner:
				value -= in_future.ship_count
			else:
				value += in_future.ship_count
			value = max(0, value)
		
		return value
	
	def best_sources(self, owner=player.ME):
		planets = []
		for planet in self.universe.find_planets(owner=owner):
			if planet.id != self.id:
				planets.append(planet)
		
		return sorted(
			planets,
			reverse=True,
			key=lambda source: (
				1.0 * (source.ship_count > source.safe_ship_count or owner != player.ME) # lets assume enemy doesn't check this
				* source.ship_count
				/ float(source.distance(self))
			)
		)
	
	def sources_coefficient(self, owner=player.ME):
		value = 0
		for source in self.best_sources(owner=owner)[0:3]:
			value += float(source.ship_count+1.0) / float(source.distance(self)) / float(self.in_future(source.distance(self)).ship_count+1.0)**2
		value /= 3.0
#		log.debug(owner)
#		log.debug(self.best_sources(owner=owner))
#		log.debug(self.id)
#		log.debug(value)
		
		if value == 0: # some player has only 1 planet
			value = 1.0
		
		return value
	
	def target_coefficient(self, attacker=player.ME):
		if attacker == player.ME:
			enemy = player.ENEMIES
		elif attacker in player.ENEMIES:
			enemy = player.ME
		
		value = self.sources_coefficient(owner=attacker)
		value -= self.sources_coefficient(owner=enemy)
		value /= self.ship_count
		value *= float(self.growth_rate)

		#TODO: this works only for player.ME
		if self.owner != player.NOBODY:
			value *= (float(len(self.universe.my_planets)) / float(len(self.universe.enemy_planets))) ** 2
		
		return value


class MyUniverse(Universe2):
	
	def best_targets(self, attacker=player.ME):
		if attacker == player.ME:
			targets = self.not_my_planets
		else:
			targets = self.my_planets
			
		return sorted(
			targets,
			reverse=True,
			key=lambda planet: planet.target_coefficient(attacker=attacker)
		)


Game(MyBot, universe_class=MyUniverse, planet_class=MyPlanet)
