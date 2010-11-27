import logging
from copy import copy

from planetwars.planet import Planet, Planets
from planetwars import player

import cache

log = logging.getLogger(__name__)


class MyPlanet(Planet):

	def __repr__(self):
		return "<P(%d) #%d +%d %s>" % (self.id, self.ship_count, self.growth_rate, self.owner)
	
	def get_ship_count(self):
		queued_ships_count = sum([ qfleet['ship_count'] for qfleet in self.universe.fleet_queue if qfleet['source'] == self ])
		return self._ship_count - queued_ships_count
	
	def set_ship_count(self, value):
		self._ship_count = value
	
	ship_count = property(get_ship_count, set_ship_count)
		
#	@property
#	def min_ship_count(self):
#		#TODO: works only for my ships, change it? if not my planet return 0?
#		return max(1, len(self.universe.enemy_planets) * 2 - self.growth_rate)
	
	def available_ship_count(self, turns=0):
		"""The number of ships the planet can send without risk."""
		if self.owner != player.ME:
			raise Exception("Should be run only on my planets!")
		
		value = max(0, self.ship_count - self.safe_ship_count(turns) - self.danger_coefficient())
		
		assert value >= 0
		return value
	
	@cache.memoize
	def needed_ship_count(self, turns=0, attacker=player.EVERYBODY):
		"""The number ships needed so that the planet stays or becomes mine."""
		fleets = sorted(
			self.universe.find_fleets(destination=self, owner=attacker),
			reverse=True,
			key=lambda fleet: fleet.turns_remaining
		)
		
		qfleets = sorted(
			[ qfleet for qfleet in self.universe.fleet_queue if qfleet['destination'] == self ],
			reverse=True,
			key=lambda qfleet: qfleet['turns_remaining']
		)
		
		# when defending we want to counter one fleet at time, when attacking,
		# we want to know about all the fleets going to the target
		if turns == 0 or self.owner != player.ME:
			if len(fleets) != 0:
				turns = max(turns, fleets[0].turns_remaining)
			if len(qfleets) != 0:
				turns = max(turns, qfleets[0]['turns_remaining'])
		
		in_future = self.in_future(turns)
		if in_future.owner == player.ME:
			return -in_future.ship_count
		else:
			return in_future.ship_count + 1
			
			
	@cache.memoize
	def safe_ship_count(self, turns=0):
		"""The number of additional (to ship_count) ships needed so that the planet stays mine."""
		fleets = sorted(
			self.universe.find_fleets(destination=self),
			reverse=True,
			key=lambda fleet: fleet.turns_remaining
		)
		
		qfleets = sorted(
			[ qfleet for qfleet in self.universe.fleet_queue if qfleet['destination'] == self ],
			reverse=True,
			key=lambda qfleet: qfleet['turns_remaining']
		)
		
		if len(fleets) != 0:
			turns = max(turns, fleets[0].turns_remaining)
		if len(qfleets) != 0:
			turns = max(turns, qfleets[0]['turns_remaining'])
		
		value = 0
		total = 0
		
		for i in range(1, turns+1):
			arriving_fleets = [ x for x in fleets if x.turns_remaining == i ]
			
			# this is probably wrong, we cannot assume that this state will be true if we send some ships
			in_future = self.in_future(i)
			
			if in_future.owner == player.ME:
				current = 0#-self.growth_rate
			elif in_future.owner == player.NOBODY:
				current = 0
			else:
				current = self.growth_rate
				
			for fleet in arriving_fleets:
				if fleet.owner == player.ME:
					current -= fleet.ship_count
				else:
					current += fleet.ship_count
			
			current -= sum([ qfleet['ship_count'] for qfleet in qfleets if qfleet['turns_remaining'] == i ])
			
			total += current
			value = max(value, total)
		
#		log.debug(self)
#		log.debug(value)
		return value
		

	@cache.memoize
	def in_future(self, turns=1):
		"""Calculates state of planet in `turns' turns."""
		planet = copy(self)

		arriving_fleets = self.universe.find_fleets(destination=self)
		arriving_qfleets = [ qfleet for qfleet in self.universe.fleet_queue if qfleet['destination'] == self ]
		leaving_qfleets = [ qfleet for qfleet in self.universe.fleet_queue if qfleet['source'] == self ]

		for i in range(1, turns+1):
			# account planet growth
			if planet.owner != player.NOBODY:
				planet.ship_count = planet.ship_count + self.growth_rate

			# get fleets which will arrive in that turn
			fleets = [ x for x in arriving_fleets if x.turns_remaining == i ]

			# assuming 2-player scenario!
			ships = []
			for id in [1,2]:
				count = sum( [ x.ship_count for x in fleets if x.owner == player.PLAYER_MAP.get(int(id)) ] )
				if id == 1:
					count += sum([ qfleet['ship_count'] for qfleet in arriving_qfleets if qfleet['turns_remaining'] == i ])
					count -= sum([ qfleet['ship_count'] for qfleet in leaving_qfleets ])
				if player.PLAYER_MAP[id] == planet.owner:
					count += planet.ship_count

#                if count > 0:
				ships.append({'player':player.PLAYER_MAP.get(id), 'ships':count})

			# neutral planet has own fleet
			if planet.owner == player.NOBODY:
				ships.append({'player':player.NOBODY,'ships':planet.ship_count})

			# calculate outcome
			if len(ships) > 1:
				s = sorted(ships, key=lambda s : s['ships'], reverse=True)

				winner = s[0]
				second = s[1]

				if winner['ships'] == second['ships']:
					planet.ship_count=0
				else:
					planet.owner=winner['player']
					planet.ship_count=winner['ships'] - second['ships']

		return planet
	
	def best_sources(self, owner=player.ME, max_distance=9999):
		planets = [ planet for planet in self.universe.find_planets(owner=owner) if (
			planet.id != self.id and
			#(owner != player.ME or planet.available_ship_count() > 0) and
			planet.distance(self) <= max_distance
		) ]
		
		return sorted(
			planets,
			key=lambda source: float(source.distance(self))
		)
	
	def source_coefficient(self, owner=player.ME):
		value = 0.0
		best_sources = self.best_sources(owner=owner)[0:3]
		for source in best_sources:
			value += source.distance(self)
		value /= float(max(1, len(best_sources)))
		
		return value
	
	def danger_coefficient(self, attacker=player.ENEMIES):
		"""Number of ships that in case of attack can't be countered by help of nearby allied planets."""
		defender = player.ME if attacker == player.ENEMIES else player.ENEMIES
	
		value = 0
		attacker_ship_count = 0
		attacker_sources = self.best_sources(owner=attacker)
		last_distance = 0
		
		for source in attacker_sources:
			defender_sources = self.best_sources(owner=defender, max_distance=self.distance(source)+1)
			value += source.ship_count - (sum([ planet.ship_count for planet in defender_sources ]) - attacker_ship_count)
			
			if self.owner != player.NOBODY:
				value -= self.growth_rate * (self.distance(source) - last_distance)
			
			attacker_ship_count += source.ship_count
			last_distance = self.distance(source)
		
		value = max(0, value)
			
		#log.debug('danger_coefficient: %s %d %s' % (self, value, attacker))
		
		assert value >= 0
		return value
	
	def target_coefficient(self):
		value = 1.0
		log.debug('target_coefficient: %s' % self)
		
		value /= self.source_coefficient() + 1.0
		log.debug('sc ME = %f' % (self.source_coefficient() + 1.0))
		log.debug(value)
		value *= self.source_coefficient(owner=player.ENEMIES) + 1.0
		log.debug('sc ENEMY = %f' % (self.source_coefficient(owner=player.ENEMIES) + 1.0))
		log.debug(value)
		
		value *= self.danger_coefficient(attacker=player.ME) + 1.0
		log.debug('dc ME = %f' % (self.danger_coefficient(attacker=player.ME) + 1.0))
		log.debug(value)
		value /= self.danger_coefficient(attacker=player.ENEMIES) + 1.0
		log.debug('dc ENEMY = %f' % (self.danger_coefficient(attacker=player.ENEMIES) + 1.0))
		log.debug(value)
		
		value /= max(1, self.needed_ship_count(int(self.source_coefficient()))) ** 2
		log.debug('needed_ship_count = %d' % max(1, self.needed_ship_count(int(self.source_coefficient()))))
		log.debug(value)
		
		value *= self.growth_rate
		log.debug('growth_rate = %d' % self.growth_rate)
		log.debug(value)
		
		#value /= float(self.ship_count + 1.0)

		if self.owner != player.NOBODY:
			value *= (self.universe.my_ship_count(with_fleets=True) / float(self.universe.enemy_ship_count(with_fleets=True))) ** 2
			log.debug('ship_count ratio = %f' % (self.universe.my_ship_count(with_fleets=True) / float(self.universe.enemy_ship_count(with_fleets=True))))
			log.debug(value)
			value *= (self.universe.my_growth_rate() / float(self.universe.enemy_growth_rate())) ** 2
			log.debug('growth_rate ratio = %f' % (self.universe.my_growth_rate() / float(self.universe.enemy_growth_rate())))
			log.debug(value)
		
		return value
	
	@property
	def enemy_nearest_planet_distance(self):
		distance = 9999
		for planet in self.universe.enemy_planets:
			if planet.distance(self) < distance:
				distance = planet.distance(self)
				#nearest_planet = planet
		
		return distance
	
	@property
	def my_nearest_planet_distance(self):
		distance = 9999
		for planet in self.universe.my_planets:
			if planet.id != self.id and planet.distance(self) < distance:
				distance = planet.distance(self)
				#nearest_planet = planet
		
		return distance
	
	@property
	def my_frontier_planet(self):
		closest_planets = sorted(
			self.universe.my_planets,
			key=lambda planet: planet.distance(self)
		)
		
		for planet in closest_planets:
			if planet.enemy_nearest_planet_distance < self.enemy_nearest_planet_distance and \
			   planet.danger_coefficient() >= self.danger_coefficient():
				log.debug("%s frontier planet: %s (%d vs %d)" % (self, planet, self.enemy_nearest_planet_distance, planet.enemy_nearest_planet_distance))
				return planet
		
		return None
	
	@property
	def is_front(self):
		# add some or
		return self.enemy_nearest_planet_distance <= 2*self.my_nearest_planet_distance
	
	def queue_fleet(self, target, ship_count):
		if isinstance(target, set):
			if self.ship_count >= ship_count * len(target):
				return self.universe.queue_fleet(self, target, ship_count)
		else:
			if self.ship_count >= ship_count:
				return self.universe.queue_fleet(self, target, ship_count)
		return False
