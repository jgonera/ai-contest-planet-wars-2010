import logging

from planetwars.universe import Universe
from planetwars import player
from planetwars.util import Point

import cache

log = logging.getLogger(__name__)


class MyUniverse(Universe):
	
	fleet_queue = []
	queue_transaction = []
	
	def my_center(self):
		if len(self.my_planets) == 0:
			return Point(0.0, 0.0)
			
		x = 0.0
		y = 0.0
		for planet in self.my_planets:
			x += planet.position[0]
			y += planet.position[1]
		
		x /= len(self.my_planets)
		y /= len(self.my_planets)
		
		return Point(x, y)

	def enemy_center(self):
		if len(self.enemy_planets) == 0:
			return Point(0.0, 0.0)
	
		x = 0.0
		y = 0.0
		for planet in self.enemy_planets:
			x += planet.position[0]
			y += planet.position[1]
		
		x /= len(self.enemy_planets)
		y /= len(self.enemy_planets)
		
		return Point(x, y)
	
	def my_ship_count(self, with_fleets=True):
		value = sum([ planet.ship_count for planet in self.my_planets ])
		if with_fleets:
			value += sum([ fleet.ship_count for fleet in self.my_fleets ])
		
		return value
	
	def enemy_ship_count(self, with_fleets=True):
		value = sum([ planet.ship_count for planet in self.enemy_planets ])
		if with_fleets:
			value += sum([ fleet.ship_count for fleet in self.enemy_fleets ])
		
		return value
	
	def my_attacked_neutrals(self):
		attacked_neutrals = []
		for fleet in self.my_fleets:
			if fleet.destination.owner == player.NOBODY and fleet.destination not in attacked_neutrals and \
			fleet.destination.in_future(fleet.turns_remaining).owner == player.ME:
				attacked_neutrals.append(fleet.destination)
				
		for qfleet in self.fleet_queue:
			if qfleet['destination'].owner == player.NOBODY and qfleet['destination'] not in attacked_neutrals and \
			qfleet['destination'].in_future(qfleet['turns_remaining']).owner == player.ME:
				attacked_neutrals.append(qfleet['destination'])
		
		return attacked_neutrals
	
	def enemy_attacked_neutrals(self):
		attacked_neutrals = []
		for fleet in self.enemy_fleets:
			if fleet.destination.owner == player.NOBODY and fleet.destination not in attacked_neutrals and \
			fleet.destination.in_future(fleet.turns_remaining).owner in player.ENEMIES:
				attacked_neutrals.append(fleet.destination)
		
		return attacked_neutrals
	
	def my_growth_rate(self, in_future=False):
		value = sum([ planet.growth_rate for planet in self.my_planets ])
		
		if in_future:
			value += sum([ planet.growth_rate for planet in self.my_attacked_neutrals() ])
		
		return value
		
	def enemy_growth_rate(self, in_future=False):
		value = sum([ planet.growth_rate for planet in self.enemy_planets ])
		
		if in_future:
			value += sum([ planet.growth_rate for planet in self.enemy_attacked_neutrals() ])

		return value
	
#	@cache.memoize
#	def front_average(self):
#		return sum([ planet.source_coefficient(owner=player.ENEMIES) for planet in self.my_planets ])/len(self.my_planets)
	
	#@cache.memoize
	def best_targets(self):
		return sorted(
			self.not_my_planets,
			reverse=True,
			key=lambda planet: (
				1.0 * (hasattr(planet, 'attacked')),
				#1.0 * (planet.owner == player.NOBODY),
				1.0 * (planet.source_coefficient(player.ME) <= planet.source_coefficient(player.ENEMIES) or (
					self.my_ship_count(with_fleets=True) > self.enemy_ship_count(with_fleets=True) and \
					self.my_growth_rate() > self.enemy_growth_rate()
				)),
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
		if ship_count == 0:
			return False
		
		log.debug("Queuing fleet of %d from %s to %s." % (ship_count, source, destination))
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
		# This assignment is to avoid negative ship_count in debug info
		fleet_queue = list(self.fleet_queue)
		del self.fleet_queue[:]
	
		for qfleet in fleet_queue:
			self.send_fleet(qfleet['source'], qfleet['destination'], qfleet['ship_count'])
		
