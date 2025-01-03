class Fleet
  attr_reader :owner, :num_ships, :source_planet, 
    :destination_planet, :total_trip_length, :turns_remaining
 
   def initialize(owner, num_ships, source_planet, 
                 destination_planet, total_trip_length, 
                 turns_remaining)
    @owner, @num_ships = owner, num_ships
    @source_planet = source_planet
    @destination_planet = destination_planet
    @total_trip_length = total_trip_length
    @turns_remaining = turns_remaining
  end
  
  def to_s
    "Fleet owner: #{owner}, num_ships: #{num_ships}, turns_remaining: #{turns_remaining}"
  end
  
  class << self
    attr_accessor :world
    
    def approaching_planet(planet)
      fleets = @world.fleets.select{ |fleet| fleet.destination_planet == planet.planet_id}
      fleets + @world.approved_fleets.select{ |fleet| fleet.destination_planet == planet.planet_id}
      fleets.sort{|a, b| a.turns_remaining <=> b.turns_remaining}
    end
    
    def leaving_planet(planet)
      @world.approved_fleets.select{ |fleet| fleet.source_planet == planet.planet_id}
    end
    
    def against_me
      @world.fleets.select{ |fleet| fleet.owner && @world.get_planet(fleet.destination_planet).owner == 1 }
    end
    
    def attacking_planet(planet)
      fleets = @world.fleets.select{ |fleet| fleet.destination_planet == planet.planet_id && fleet.owner > 1}
      fleets.sort{|a, b| a.turns_remaining <=> b.turns_remaining}
    end  
  end
end