import logging
import os
from math import sqrt

from planetwars import BaseBot, Game
from planetwars.universe2 import Universe2
from planetwars.planet2 import Planet2
from planetwars.universe import player


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

MAX_ATTACKS = 3
#min_ship_count = 10

class MyBot(BaseBot):
	#enemy_fleets = {}

	def do_turn(self):
		max_sources = min(10, max(3, len(self.universe.my_planets)/2))
		min_ship_count = len(self.universe.enemy_planets)**2
		
		# defend
		remaining_attacks = min(3, len(self.universe.my_planets))
		attacked_planets = []
		attacked_planets_ids = []
		attacked_planets_turns = {}
		
		for fleet in self.universe.enemy_fleets:
			if fleet.destination.owner == player.ME:
				if fleet.destination not in attacked_planets:
					attacked_planets.append(fleet.destination)
					attacked_planets_ids.append(fleet.destination.id)
				if attacked_planets_turns.get(fleet.destination.id, 0) < fleet.turns_remaining:
					attacked_planets_turns[fleet.destination.id] = fleet.turns_remaining
				
		
		attacked_planets = sorted(
			attacked_planets,
			reverse=True,
			key=lambda planet: planet.growth_rate
		)
						
		for target in attacked_planets[0:len(self.universe.my_planets)/2]:
			best_sources = sorted(
				self.universe.my_planets,
				reverse=True,
				key=lambda source: float(source.ship_count)/float(1.0+source.distance(target))
			)
			best_ships = 0
			longest_distance = 0
			for source in best_sources[0:max_sources]:
				if source.id != target.id and (source not in attacked_planets or len(self.universe.my_planets) < 3):
					best_ships += source.ship_count
					if source.distance(target) > longest_distance:
						longest_distance = source.distance(target)
			
			target_in_future = target.in_future(longest_distance+20)
			if best_ships < target_in_future.ship_count + min_ship_count*max_sources:
				continue
			
			for source in best_sources[0:max_sources]:
				target_in_future = target.in_future(longest_distance+20)
				if source.id != target.id and source.ship_count > 0 and not target_in_future.owner == player.ME and (source not in attacked_planets or len(self.universe.my_planets) < 3):
					current_fleet = min(target_in_future.ship_count + target.growth_rate*(max(0, source.distance(target)-attacked_planets_turns[target.id])), source.ship_count)
					source.send_fleet(target, current_fleet)
					remaining_attacks -= 1
						
		
		# attack
		best_sources = {}
		target_coefficient = {}
		
		for target in self.universe.not_my_planets:
			best_sources[target.id] = sorted(
				self.universe.my_planets,
				reverse=True,
				key=lambda source: 1.0*(source.ship_count > min_ship_count and source not in attacked_planets or len(self.universe.my_planets) > 2*len(self.universe.enemy_planets))*source.ship_count/float(source.distance(target))
			)
			target_coefficient[target.id] = 0
			for source in best_sources[target.id][0:3]:
				target_coefficient[target.id] += float(source.ship_count) / float(source.distance(target)**2) / (float(target.in_future(source.distance(target)).ship_count+1.0)**3)
			target_coefficient[target.id] /= 3
			log.debug("sources coefficient: %s" % target_coefficient[target.id])
			target_coefficient[target.id] *= float(target.growth_rate)
			log.debug("+ growth: %s" % target_coefficient[target.id])
			if target.owner in player.ENEMIES:
				target_coefficient[target.id] *= float(len(self.universe.my_planets)) / float(len(self.universe.enemy_planets))**2
			log.debug("+ if enemy: %s" % target_coefficient[target.id])
	
		best_targets = sorted(self.universe.not_my_planets, reverse=True, key=lambda target: target_coefficient[target.id])
		
		# support previous attacks
#		enemy_attacked_planets = []
#		enemy_attacked_planets_turns = {}
#		for fleet in self.universe.my_fleets:
#			if fleet.destination.owner in player.NOT_ME:
#				if fleet.destination not in enemy_attacked_planets:
#					enemy_attacked_planets.append(fleet.destination)
#				if enemy_attacked_planets_turns.get(fleet.destination.id, 0) < fleet.turns_remaining:
#					enemy_attacked_planets_turns[fleet.destination.id] = fleet.turns_remaining
#					
#		for target in enemy_attacked_planets:
#			for source in best_sources[target.id]:
#				target_in_future = target.in_future(enemy_attacked_planets_turns[target.id]+20)
#				if source.ship_count > min_ship_count and (not target_in_future.owner == player.ME or target_in_future.ship_count < min_ship_count) and (source not in attacked_planets or len(self.universe.my_planets) < 3):
#					source.send_fleet(target, min(source.ship_count - min_ship_count, target_in_future.ship_count + min_ship_count))
		
		# new attacks
		for target in best_targets:
			best_ships = 0
			longest_distance = 0
			for source in best_sources[target.id][0:max_sources]:
				if source.ship_count > min_ship_count and (source not in attacked_planets or len(self.universe.my_planets) < 3):
					best_ships += source.ship_count
					if source.distance(target) > longest_distance:
						longest_distance = source.distance(target)
			
			target_in_future = target.in_future(longest_distance+20)
			
			if target_in_future.owner == player.ME:
				continue
			if best_ships < target_in_future.ship_count + min_ship_count*max_sources:
				break
			
			for source in best_sources[target.id]:
				target_in_future = target.in_future(longest_distance+20)
				if source.ship_count > min_ship_count and (not target_in_future.owner == player.ME or target_in_future.ship_count < min_ship_count) and (source not in attacked_planets or len(self.universe.my_planets) < 3):
					source.send_fleet(target, min(source.ship_count - min_ship_count, target_in_future.ship_count + min_ship_count))


Game(MyBot, universe_class=Universe2, planet_class=Planet2)
