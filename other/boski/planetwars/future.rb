class Future
  class << self
    def get_future_planet(planet, turns)
      fleets = Fleet.approaching_planet(planet)
      leaving_fleets = Fleet.leaving_planet(planet)
      
      future_planet = planet.clone
      
      unless leaving_fleets.empty?
        future_planet.remove_ships(leaving_fleets.map(&:num_ships).inject(:+))
      end
      
      turns.times do |turn|
        unless future_planet.neutral?
          future_planet.add_ships(future_planet.growth_rate)
        end
        
        turn_fleets = fleets.select{ |fleet| fleet.turns_remaining == turn + 1 }
      
        unless turn_fleets.empty?
          forces = turn_fleets.map(&:owner)
          forces << future_planet.owner
          forces.uniq!
        
          if forces.size > 1
            battle(future_planet, turn_fleets, forces)
          else
            future_planet.add_ships(turn_fleets.map(&:num_ships).inject(:+))
          end
        end  
      end
    
      return future_planet
    end
  
    def battle(future_planet, fleets, forces)
      ships = Hash.new(0)
      fleets.each do |fleet|
        ships[fleet.owner] += fleet.num_ships
      end
      
      ships[future_planet.owner] += future_planet.num_ships
      
      max_ships = ships.values.max
      winners = ships.select{ |key, value| value == max_ships}.count
      
      if winners > 1
        future_planet.num_ships = 0
      else
        runner_up = ships.values.sort[-2]
        remaining_ships = max_ships - runner_up
        future_planet.num_ships = remaining_ships
        future_planet.owner = ships.key(max_ships)
      end
    end
  end
end