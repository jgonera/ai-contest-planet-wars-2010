import logging
import math

from planetwars import BaseBot, Game
from planetwars import player
from planetwars.planet import Planets

import cache
from myplanet import MyPlanet
from myuniverse import MyUniverse

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

INITIAL_TURNS = 30
MAX_TURNS = 200

class MyBot(BaseBot):
	# TODO: count time
	turn = 0
	attacked_planets = {}
	
	def do_turn(self):
		self.turn += 1
		
		for target in self.attacked_planets.keys():
			self.attacked_planets[target] -= 1
			if self.attacked_planets[target] == 0:
				del self.attacked_planets[target]

		cache.store.clear()
		
		self.defend()
		self.attack()
		self.tunnel()
		
		self.universe.send_queued_fleets()
		log.debug(cache.stats)
	
	
	def defend(self):
		log.info("DEFEND")
		
		planets = sorted(
			self.universe.my_planets,
			reverse=True,
			key=lambda planet: planet.growth_rate
		)
		
		planets.extend(self.attacked_planets.keys())
		
		# experimental crap
#		for fleet in self.universe.my_fleets:
#			if fleet.destination.owner != player.ME:
#				planets.append(fleet.destination)
		
		for planet in planets:
			# don't use Planet.attacking_fleets() here because we will try to
			# counter our own fleets when defending neutral planets which are
			# not yet ours!
			attacking_fleets = sorted(
				self.universe.find_fleets(owner=player.ENEMIES, destination=planet),
				key=lambda fleet: fleet.turns_remaining
			)
			needed_ship_count = planet.needed_ship_count(attacker=player.ENEMIES)
			
			if len(attacking_fleets) != 0 and needed_ship_count > 0:
				log.info("%s attacked by: %s" % (planet, attacking_fleets))
				log.info("Needed ship count: %s" % needed_ship_count)
			
				defend = True
								
				for fleet in attacking_fleets:
					needed_ship_count = planet.needed_ship_count(turns=fleet.turns_remaining)
					log.info("Countering %s" % fleet)
					log.info("Needed ship count: %d" % needed_ship_count)
					
					if needed_ship_count > 0:
						best_sources = planet.best_sources(max_distance=fleet.turns_remaining)
						
						self.universe.begin_transaction()
						
						for source in best_sources:
							source_sent_ships = min(source.available_ship_count(with_danger=False), needed_ship_count)
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
			log.debug("growth rate: %d / %d" % (self.universe.my_growth_rate(in_future=False), self.universe.enemy_growth_rate(in_future=False)))
			log.debug("ship count: %d / %d" % (self.universe.my_ship_count(with_fleets=True), self.universe.enemy_ship_count(with_fleets=True)))
#			if not (self.universe.my_growth_rate(in_future=True) <= self.universe.enemy_growth_rate(in_future=True) or
#			        self.universe.my_ship_count() > self.universe.enemy_ship_count() or
#			        self.turn <= INITIAL_TURNS):
#				break
			if (self.universe.my_ship_count() + self.universe.my_growth_rate(in_future=False) * (MAX_TURNS - self.turn) < self.universe.enemy_ship_count() + self.universe.enemy_growth_rate(in_future=False) * (MAX_TURNS - self.turn) or
				self.universe.my_growth_rate(in_future=True) <= self.universe.enemy_growth_rate(in_future=True) or
				self.universe.my_ship_count(with_fleets=False) > self.universe.enemy_ship_count() or
				self.turn <= INITIAL_TURNS):
		        
				with_danger = (
					self.universe.my_ship_count() + self.universe.my_growth_rate(in_future=False) * (MAX_TURNS - self.turn) < self.universe.enemy_ship_count() + self.universe.enemy_growth_rate(in_future=False) * (MAX_TURNS - self.turn) or
					self.turn <= INITIAL_TURNS
				)
			   
				log.info("Ships needed for %s: %d" % (target, target.needed_ship_count()))
				available_ships = 0
				longest_distance = 0
				best_sources = target.best_sources()

				if target.needed_ship_count() <= 0 or len(best_sources) == 0:
					continue
			
				for source in best_sources:
					available_ships += source.available_ship_count(with_danger)
					longest_distance = max(longest_distance, source.distance(target))
					needed_ship_count = target.needed_ship_count(longest_distance)
					if available_ships >= needed_ship_count:
						break

				if available_ships < needed_ship_count:
					break
			
				log.info("Attacking %s, %i ships needed." % (target, needed_ship_count))
				self.universe.begin_transaction()
			
				for source in best_sources:
	#				if self.turn == 1:
	#					available_ship_count = min(
	#						source.available_ship_count(),
	#						source.distance([ p for p in self.universe.enemy_planets ][0]) * source.growth_rate
	#					)
	#				else:
					available_ship_count = source.available_ship_count(with_danger)
				
					source_sent_ships = min(available_ship_count, needed_ship_count)
					source.queue_fleet(target, source_sent_ships)
					needed_ship_count -= source_sent_ships
				
					if needed_ship_count <= 0:
						break
			
				self.universe.commit_transaction()
				self.attacked_planets[target] = longest_distance
	
	
	def tunnel(self):
		log.info("TUNNEL")
		
#		front_planets = [ planet for planet in self.universe.my_planets if planet.is_front ]
#		front_planets.extend([ planet for planet in self.attacked_planets.keys() if planet.is_front ])
#		
#		if len(front_planets) == 0:
#			return
#		
#		front_planets = sorted(
#			front_planets,
#			reverse=True,
#			key=lambda planet: planet.danger_coefficient()
#		)
#		log.debug('front_planets: %s' % front_planets)
#		sources_per_front = int(math.ceil((len(self.universe.my_planets) - len(front_planets)) / float(len(front_planets))))
#		used_sources = []
#		
#		for front_planet in front_planets:
#			self.universe.begin_transaction()
#			
#			best_sources = Planets(front_planet.best_sources()) - Planets(front_planets)
#			i = 0
#			for source in best_sources:
#				if source not in used_sources:
#					source.queue_fleet(source.my_frontier_planet2(front_planet), source.available_ship_count(with_danger=False))
#					used_sources.append(source)
#					i += 1
#				if i >= sources_per_front:
#					break
#		
#			self.universe.commit_transaction()

		self.universe.begin_transaction()
		
		for planet in self.universe.my_planets:
			frontier_planet = planet.my_frontier_planet
			if frontier_planet and planet.available_ship_count() > 0:
				planet.queue_fleet(frontier_planet, planet.available_ship_count(with_danger=False))
		
		self.universe.commit_transaction()
				

Game(MyBot, universe_class=MyUniverse, planet_class=MyPlanet)
