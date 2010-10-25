import logging
from copy import copy

from planetwars import BaseBot, Game
from planetwars.universe import Universe
from planetwars.planet import Planet, Planets
from planetwars import player

from mybot import cache

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class MyBot(BaseBot):
	# TODO: catch TimeIsUp exception
	first_turn = True
	
	def do_turn(self):
		# TODO: count how many we can send on the first attack
#		if self.first_turn:
#			self.first_turn = False
#			return

		cache.store.clear()
		
		self.defend()
		self.attack()
		#self.tunnel()
		
		self.universe.send_queued_fleets()
		log.debug(cache.stats)
	
	
	def defend(self):
		log.info("DEFEND")
		# TODO: sort planets (probably by growth)
		for planet in self.universe.my_planets:
			attacking_fleets = sorted(
				planet.attacking_fleets,
				key=lambda fleet: fleet.turns_remaining
			)
			needed_ship_count = planet.needed_ship_count()
			
			if len(attacking_fleets) != 0 and needed_ship_count > 0:
				log.info("%s attacked by: %s" % (planet, attacking_fleets))
				log.info("Needed ship count: %s" % needed_ship_count)
			
				defend = True
								
				for fleet in attacking_fleets:
					needed_ship_count = planet.needed_ship_count(turns=fleet.turns_remaining)
					log.info("Countering {0}.".format(fleet))
					log.info("Needed ship count: {0}".format(needed_ship_count))
					
					if needed_ship_count > 0:
						best_sources = planet.best_sources(max_distance=fleet.turns_remaining)
						
						self.universe.begin_transaction()
						
						for source in best_sources:
							source_sent_ships = min(source.available_ship_count(), needed_ship_count)
							source.queue_fleet(planet, source_sent_ships)
							needed_ship_count -= source_sent_ships
							
							if needed_ship_count <= 0:
								self.universe.commit_transaction()
								break
						
						# don't try to defend further fleets if can't counter closer fleets
						if needed_ship_count > 0:
							log.info("Can't defend anymore!")
							defend = False
							break
							
				
				# if can't defend this planet anymore, try next
				if defend == False:
					continue
	
	
	def attack(self):
		log.info("ATTACK")
		for target in self.universe.best_targets():
			if not (self.universe.my_growth_rate() <= 1.1 * self.universe.enemy_growth_rate() or
			        self.universe.my_ship_count() >= self.universe.enemy_ship_count()):
				break
			   
			log.info("Ships needed for {0}: {1}".format(target, target.needed_ship_count()))
			available_ships = 0
			longest_distance = 0
			best_sources = target.best_sources()

			if target.needed_ship_count() <= 0 or len(best_sources) == 0:
				continue
			
			for source in best_sources:
				available_ships += source.available_ship_count()
				longest_distance = max(longest_distance, source.distance(target))
				needed_ship_count = target.needed_ship_count(longest_distance)
				if available_ships >= needed_ship_count:
					break

			if available_ships < needed_ship_count:
				break
			
			log.info("Attacking %s, %i ships needed." % (target, needed_ship_count))
			self.universe.begin_transaction()
			
			for source in best_sources:
#				target_in_future = target.in_future(longest_distance)
#				if not target_in_future.owner == player.ME:
				source_sent_ships = min(source.available_ship_count(), needed_ship_count)
				source.queue_fleet(target, source_sent_ships)
				needed_ship_count -= source_sent_ships
				
				if needed_ship_count <= 0:
					break
			
			self.universe.commit_transaction()
			target.set_attacked()
	
	
	def tunnel(self):
		front_planets = Planets([ planet for planet in self.universe.my_planets if planet.is_front() ])
		front_planets_count = len(front_planets)
		source_planets = self.universe.my_planets - front_planets
		
		if front_planets_count != 0:
			self.universe.begin_transaction()
			for source in source_planets:
				available_ships = source.available_ship_count()/front_planets_count
				if available_ships > 0:
					for planet in front_planets:
						source.queue_fleet(planet, available_ships)
			self.universe.commit_transaction()


class MyPlanet(Planet):
	
	def get_ship_count(self):
		queued_ships_count = sum([ qfleet['ship_count'] for qfleet in self.universe.fleet_queue if qfleet['source'] == self ])
		return self._ship_count - queued_ships_count
	
	def set_ship_count(self, value):
		self._ship_count = value
	
	ship_count = property(get_ship_count, set_ship_count)
		
	@property
	def min_ship_count(self):
		#TODO: works only for my ships, change it? if not my planet return 0?
		return max(1, len(self.universe.enemy_planets) * 2 - self.growth_rate)
	
	def available_ship_count(self, turns=0):
		"""The number of ships the planet can send without risk."""
		if self.owner != player.ME:
			raise Exception("Should be run only on my planets!")
#		
#		if self.id == 13:
#			log.debug(self)
#			log.debug(self.ship_count)
#			log.debug(-self.needed_ship_count(turns))
		return self.ship_count - self.safe_ship_count(turns)
		
	
	@cache.memoize
	def needed_ship_count(self, turns=0):
		"""The number ships needed so that the planet stays or becomes mine."""
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
			(owner != player.ME or planet.available_ship_count() > 0) and
			planet.distance(self) <= max_distance
		) ]
		
		return sorted(
			planets,
			key=lambda source: float(source.distance(self))
		)
	
	def average_source_distance(self, owner=player.ME):
		value = 0
		best_sources = self.best_sources(owner=owner)[0:3]
		for source in best_sources:
			value += source.distance(self)
		value /= float(max(1, len(best_sources)))
		#log.debug("sc {0} / {1}: {2}".format(self, owner, value))
		
		return value
	
	def target_coefficient(self):
#		log.debug("target coefficient of %s" % self)
#		log.debug(self.average_source_distance() + 1.0)
#		log.debug(self.average_source_distance(owner=player.ENEMIES) + 1.0)
#		log.debug(float(max(1.0, self.needed_ship_count(int(self.average_source_distance())))))
#		log.debug(self.growth_rate)
		
		value = 1.0
		value /= self.average_source_distance() + 1.0
		value *= self.average_source_distance(owner=player.ENEMIES) + 1.0
		value /= float(max(1.0, self.needed_ship_count(int(self.average_source_distance()))))
		
		# TODO: this is probably crap, invent better way to support attacks
		if hasattr(self, 'attacked'):
			value *= 10 - self.attacked
			self.attacked += 1
			if self.attacked > 10:
				del self.attacked
		
		if self.owner == player.NOBODY:
			value *= float(self.growth_rate)
			#value /= float(self.ship_count + 1.0)

		if self.owner != player.NOBODY:
			value *= float(self.universe.my_ship_count()) / float(self.universe.enemy_ship_count())
			value *= float(self.universe.my_growth_rate()) / float(self.universe.enemy_growth_rate())
#			value *= 1.0 * (
#				self.universe.my_ship_count() > self.universe.enemy_ship_count() and \
#				self.universe.my_growth_rate() > self.universe.enemy_growth_rate()
#			)
		
#		log.debug(value)
		return value
	
	def set_attacked(self):
		if not hasattr(self, 'attacked'):
			self.attacked = 0
		
	def is_front(self):
		log.debug(self)
		log.debug(self.universe.front_average())
		log.debug(self.average_source_distance(player.ENEMIES))
		return self.average_source_distance(player.ENEMIES) < self.universe.front_average()
	
	def queue_fleet(self, target, ship_count):
		if isinstance(target, set):
			if self.ship_count >= ship_count * len(target):
				return self.universe.queue_fleet(self, target, ship_count)
		else:
			if self.ship_count >= ship_count:
				return self.universe.queue_fleet(self, target, ship_count)
		return False

class MyUniverse(Universe):
	
	fleet_queue = []
	queue_transaction = []
	
	def my_ship_count(self):
#		fleet_ship_count = sum([ fleet.ship_count for fleet in self.my_fleets ])
#		fleet_ship_count += sum([ qfleet['ship_count'] for qfleet in self.fleet_queue ])
		planet_ship_count = sum([ planet.ship_count for planet in self.my_planets ])
		return planet_ship_count# + fleet_ship_count
	
	def enemy_ship_count(self):
		fleet_ship_count = sum([ fleet.ship_count for fleet in self.enemy_fleets ])
		planet_ship_count = sum([ planet.ship_count for planet in self.enemy_planets ])
		return planet_ship_count + fleet_ship_count
	
	def my_growth_rate(self):
		return sum([ planet.growth_rate for planet in self.my_planets ])
		
	def enemy_growth_rate(self):
		return sum([ planet.growth_rate for planet in self.enemy_planets ])
	
	@cache.memoize
	def front_average(self):
		return sum([ planet.average_source_distance(owner=player.ENEMIES) for planet in self.my_planets ])/len(self.my_planets)
	
	#@cache.memoize
	def best_targets(self):
		return sorted(
			self.not_my_planets,
			reverse=True,
			key=lambda planet: (
				1.0 * (planet.average_source_distance(player.ME) <= planet.average_source_distance(player.ENEMIES)),
				planet.target_coefficient()
			)
		)
	
	def max_sources(self, owner=player.ME):
		if owner == player.ME:
			planets_count = len(self.my_planets)
		else:
			planets_count = len(self.not_my_planets)
		
		return max(3, planets_count/2)
	
	def begin_transaction(self):
		del self.queue_transaction[:]
	
	def queue_fleet(self, source, destination, ship_count):
		log.debug("Queuing fleet of {0} from {1} to {2}.".format(ship_count, source, destination))
		self.queue_transaction.append({
			'source': source,
			'destination': destination,
			'ship_count': ship_count,
			'turns_remaining': source.distance(destination)
		})
		return True
		
	def commit_transaction(self):
		self.fleet_queue.extend(self.queue_transaction)
		cache.store.clear()
	
	def send_queued_fleets(self):
		for qfleet in self.fleet_queue:
			self.send_fleet(qfleet['source'], qfleet['destination'], qfleet['ship_count'])
		
		del self.fleet_queue[:]
				

Game(MyBot, universe_class=MyUniverse, planet_class=MyPlanet)
