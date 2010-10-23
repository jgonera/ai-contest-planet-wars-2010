import logging
from math import sqrt


from planetwars import BaseBot, Game
from planetwars.universe2 import Universe2
from planetwars.planet2 import Planet2
from planetwars.universe import player

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class MyBot(BaseBot):
	# TODO: catch TimeIsUp exception
	first_turn = True
	
	def do_turn(self):
#		if self.first_turn:
#			self.first_turn = False
#			return
		
		log.debug("DEFEND")
		# TODO: sort planets (probably by growth)
		for planet in self.universe.my_planets:
			attacking_fleets = planet.attacking_fleets
			safe_ship_count = planet.safe_ship_count()
			
			if len(attacking_fleets) != 0 and planet.ship_count < safe_ship_count:
				log.debug("%s attacked by: %s" % (planet, attacking_fleets))
				log.debug("Safe ship count: %s" % safe_ship_count)
			
				defend = True
				
				# TODO: take into account already countered fleets in consecutive fleets				
				for fleet in attacking_fleets:
					needed_ship_count = planet.needed_ship_count(turns=fleet.turns_remaining)
					
					if needed_ship_count > 0:
						best_sources = planet.best_sources(
							max_distance=fleet.turns_remaining
						)
						
						# don't try to defend further fleets if can't counter closer fleets
						if len(best_sources) == 0:
							log.debug("Can't defend anymore!")
							defend = False
							break
						
						for source in best_sources:
							source_sent_ships = min(source.available_ship_count(), needed_ship_count)# TODO: make a method for that (min's 1st arg)?
							source.queue_fleet(planet, source_sent_ships)
							needed_ship_count -= source_sent_ships
							
							if needed_ship_count <= 0:
								break;
							
						if needed_ship_count <= 0:
							self.universe.send_queued_fleets()
						else:
							self.universe.clear_queued_fleets()
				
				# if can't defend this planet anymore, try next
				if defend == False:
					continue
		
		
		log.debug("ATTACK")
		for target in self.universe.best_targets():
			available_ships = 0
			longest_distance = 0
			best_sources = target.best_sources()
			
			for source in best_sources:
				available_ships += source.available_ship_count()
				longest_distance = max(longest_distance, source.distance(target))
		
			target_in_future = target.in_future(longest_distance)
			if target_in_future.owner == player.ME:
				continue
			if available_ships < target.needed_ship_count(longest_distance):
				break
			
			for source in best_sources:
				target_in_future = target.in_future(longest_distance)
				if not target_in_future.owner == player.ME:
					source.send_fleet(target, min(source.available_ship_count(), target.needed_ship_count(longest_distance)))


class MyPlanet(Planet2):
	
	def get_ship_count(self):
		queued_ships = [ qfleet['ship_count'] for qfleet in self.universe.fleet_queue if qfleet['source'] == self ]
		return self._ship_count + sum(queued_ships)
	
	def set_ship_count(self, value):
		self._ship_count = value
	
	ship_count = property(get_ship_count, set_ship_count)
		
	@property
	def min_ship_count(self):
		#TODO: works only for my ships, change it? if not my planet return 0?
		return max(1, len(self.universe.enemy_planets) * 2 - self.growth_rate)
	
	def available_ship_count(self, turns=0):
		"""The number of ships the planet can send without risk."""
		return self.ship_count - self.safe_ship_count(turns)
	
	def needed_ship_count(self, turns=0):
		"""The number of ships needed to defend or conquer the planet."""
		if self.owner == player.ME:
			return self.safe_ship_count(turns) - self.ship_count
		else:
			return self.ship_count + self.safe_ship_count(turns) + 1
	
	def safe_ship_count(self, turns=0):
		"""The number of additional (to ship_count) ships needed so that the planet stays or becomes mine."""
		fleets = sorted(
			self.universe.find_fleets(destination=self),
			reverse=True,
			key=lambda fleet: fleet.turns_remaining
		)
		
		# TODO: include also queued fleets?
		
		if len(fleets) != 0:
			turns = max(turns, fleets[0].turns_remaining)
		
		value = 0
		total = 0
		
		for i in range(1, turns+1):
			arriving_fleets = [ x for x in fleets if x.turns_remaining == i ]
			
			in_future = self.in_future(i)
			
			if in_future.owner == player.ME:
				current = -self.growth_rate
			elif in_future.owner == player.NOBODY:
				current = 0
			else:
				current = self.growth_rate
				
			for fleet in arriving_fleets:
				if fleet.owner == player.ME:
					current -= fleet.ship_count
				else:
					current += fleet.ship_count
		
			total += current
			value = max(value, total)
		
#		log.debug(self)
#		log.debug(value)
		return value
	
	def best_sources(self, owner=player.ME, max_distance=9999.0):
		planets = [ planet for planet in self.universe.find_planets(owner=owner) if (
			planet.id != self.id and
			planet.available_ship_count() > 0 and
			planet.distance(self) <= max_distance
		) ]
		
		return sorted(
			planets,
			key=lambda source: float(source.distance(self)) / float(source.ship_count + 1.0)
		)
	
	def sources_coefficient(self, owner=player.ME):
		value = 0
		best_sources = self.best_sources(owner=owner)[0:3]
		for source in best_sources:
			distance = source.distance(self)
			value += float(source.ship_count) / float(distance + 1.0) #/ float(self.safe_ship_count(distance)+1.0)
		value /= float(max(1, len(best_sources)))
#		log.debug(owner)
#		log.debug(self.best_sources(owner=owner))
#		log.debug(self.id)
#		log.debug(value)
		
		return value
	
	def target_coefficient(self, attacker=player.ME):
		if attacker == player.ME:
			enemy = player.ENEMIES
		elif attacker in player.ENEMIES:
			enemy = player.ME
		
#		log.debug("target coefficient of %s" % self)
#		log.debug(self.sources_coefficient(owner=attacker))
#		log.debug(self.sources_coefficient(owner=enemy))
#		log.debug(self.ship_count)
#		log.debug(self.safe_ship_count())
#		log.debug(self.growth_rate)
		
		value = self.sources_coefficient(owner=attacker) + 1.0
		value /= self.sources_coefficient(owner=enemy) + 1.0
		value /= float(self.ship_count + 1.0)
		value /= float(self.safe_ship_count(10) + 1.0)
		value *= float(self.growth_rate)

		#TODO: this works only for player.ME
		if self.owner != player.NOBODY:
			value *= (float(len(self.universe.my_planets)) / float(len(self.universe.enemy_planets))) ** 2
		
		return value
	
	@property
	def attacking_fleets(self):
		"""Same as in the original kit, but sorted by turns_remaining."""
		fleets = self.universe.find_fleets(destination=self, owner=player.EVERYBODY - self.owner)
		
		return sorted(
			fleets,
			key=lambda fleet: fleet.turns_remaining
		)
	
	def queue_fleet(self, target, ship_count):
		if isinstance(target, set):
			if self.ship_count >= ship_count * len(target):
				return self.universe.queue_fleet(self, target, ship_count)
		else:
			if self.ship_count >= ship_count:
				return self.universe.queue_fleet(self, target, ship_count)
		return None

class MyUniverse(Universe2):
	
	fleet_queue = []
	
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
	
	def max_sources(self, owner=player.ME):
		if owner == player.ME:
			planets_count = len(self.my_planets)
		else:
			planets_count = len(self.not_my_planets)
		
		return max(3, planets_count/2)
	
	def queue_fleet(self, source, destination, ship_count):
		self.fleet_queue.append({
			'source': source,
			'destination': destination,
			'ship_count': ship_count
		})
	
	def clear_queued_fleets(self):
		del self.fleet_queue[:]
	
	def send_queued_fleets(self):
		for qfleet in self.fleet_queue:
			self.send_fleet(qfleet['source'], qfleet['destination'], qfleet['ship_count'])
		self.clear_queued_fleets()


Game(MyBot, universe_class=MyUniverse, planet_class=MyPlanet)
