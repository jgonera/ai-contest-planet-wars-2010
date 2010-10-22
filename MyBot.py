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
	first_turn = False
	
	def do_turn(self):
		if self.first_turn:
			self.first_turn = False
			return
		
		log.debug("DEFEND")
		# TODO: sort planets (probably by growth)
		for planet in self.universe.my_planets:
			attacking_fleets = planet.attacking_fleets
			safe_ship_count = planet.safe_ship_count()
			
			log.debug(attacking_fleets)
			log.debug(planet.ship_count)
			log.debug(safe_ship_count)
			if len(attacking_fleets) != 0 and planet.ship_count < safe_ship_count:
				defend = True
				
				# TODO: take into account already countered fleets in consecutive fleets when using defense_plan
				#       (both in ship_counts of sources and in future fleet_safe_ship_counts)
				defense_plan = [] # list of { planet, ship_count } to send for rescue
				
				for fleet in attacking_fleets:
					fleet_safe_ship_count = planet.safe_ship_count(turns=fleet.turns_remaining)
					
					if planet.ship_count < fleet_safe_ship_count:
						needed_ship_count = fleet_safe_ship_count - planet.ship_count
						
						best_sources = planet.best_sources(
							min_ship_count=needed_ship_count,
							max_distance=fleet.turns_remaining
						)
						
						# don't try to defend if can't counter all the fleets
						if len(best_sources) == 0:
							log.debug("can't defend")
							defend = False
							break
						
						# TODO: use defense_plan, don't send until sure that can send
						for source in best_sources:
							source_sent_ships = min(source.ship_count - fleet_safe_ship_count, needed_ship_count)# TODO: make a method for that (min's 1st arg)?
							source.send_fleet(planet, source_sent_ships)
							needed_ship_count -= source_sent_ships
							
							if needed_ship_count <= 0:
								break;
							
#							defense_plan.append({
#								'source': best_sources[0],
#								'ship_count': needed_ship_count
#							})
				
				log.debug(defense_plan)
				# if can't defend this planet, try next
				if defend == False:
					continue
				
#				for defense in defense_plan:
#					defense['source'].send_fleet(planet, defense['ship_count'])
		
		
		log.debug("ATTACK")
		for target in self.universe.best_targets():
			available_ships = 0
			longest_distance = 0
			best_sources = target.best_sources()
			
			for source in best_sources:
				attack_ship_count = source.attack_ship_count()
				if attack_ship_count > source.min_ship_count:
					available_ships += attack_ship_count
					if source.distance(target) > longest_distance:
						longest_distance = source.distance(target)
		
			target_in_future = target.in_future(longest_distance)
			if target_in_future.owner == player.ME:
				continue
			if available_ships < target.defend_ship_count(longest_distance):
				break
			
			for source in best_sources:
				target_in_future = target.in_future(longest_distance)
				attack_ship_count = source.attack_ship_count()
				if attack_ship_count > source.min_ship_count and (not target_in_future.owner == player.ME):
#					log.debug(source.id)
#					log.debug(source.safe_ship_count())
					source.send_fleet(target, min(attack_ship_count - source.min_ship_count, target.defend_ship_count(longest_distance)))


class MyPlanet(Planet2):
	
	@property
	def min_ship_count(self):
		#TODO: works only for my ships, change it? if not my planet return 0?
		return max(1, len(self.universe.enemy_planets) * 2 - self.growth_rate)
	
	def attack_ship_count(self, turns=0):
		return self.ship_count - self.safe_ship_count(turns)
	
	def defend_ship_count(self, turns=0):
		return self.ship_count + self.safe_ship_count(turns) + 1
	
	def safe_ship_count(self, turns=0):
		
		fleets = sorted(
			self.universe.find_fleets(destination=self),
			reverse=True,
			key=lambda fleet: fleet.turns_remaining
		)
		
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
	
	def best_sources(self, owner=player.ME, max_distance=9999.0, min_ship_count=1):
		planets = [ planet for planet in self.universe.find_planets(owner=owner) if (
			planet.id != self.id and
			planet.distance(self) <= max_distance
		) ]
		
		# TODO: make it work for enemy too
		if owner == player.ME:
			available_planets = 0
			for planet in planets:
				available_planets += planet.ship_count - planet.safe_ship_count()
				if available_planets >= min_ship_count:
					break
		
			if available_planets < min_ship_count:
				return []
		
		return sorted(
			planets,
			key=lambda source: float(source.distance(self)) / float(source.ship_count + 1.0)
		)
	
	def sources_coefficient(self, owner=player.ME):
		value = 0
		for source in self.best_sources(owner=owner)[0:3]:
			distance = source.distance(self)
			value += float(source.ship_count) / float(distance) #/ float(self.safe_ship_count(distance)+1.0)
		value /= float(max(1, len(self.best_sources(owner=owner)[0:3])))
#		log.debug(owner)
#		log.debug(self.best_sources(owner=owner))
#		log.debug(self.id)
#		log.debug(value)
		
#		if value == 0: # some player has only 1 planet
#			value = 1.0
		
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
		
		value = self.sources_coefficient(owner=attacker)+1.0
		value /= self.sources_coefficient(owner=enemy)+1.0
		value /= float(self.ship_count + 1.0)
		value /= float(self.safe_ship_count(10) + 1.0)
		value *= float(self.growth_rate)

		#TODO: this works only for player.ME
		if self.owner != player.NOBODY:
			value *= (float(len(self.universe.my_planets)) / float(len(self.universe.enemy_planets))) ** 2
		
		return value
	
	@property
	def attacking_fleets(self):
		fleets = self.universe.find_fleets(destination=self, owner=player.EVERYBODY - self.owner)
		
		return sorted(
			fleets,
			key=lambda fleet: fleet.turns_remaining
		)

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
	
	def max_sources(self, owner=player.ME):
		if owner == player.ME:
			planets_count = len(self.my_planets)
		else:
			planets_count = len(self.not_my_planets)
		
		return max(3, planets_count/2)


Game(MyBot, universe_class=MyUniverse, planet_class=MyPlanet)
