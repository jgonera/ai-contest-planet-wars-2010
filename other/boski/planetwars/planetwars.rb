require File.expand_path("fleet", File.dirname(__FILE__))
require File.expand_path("planet", File.dirname(__FILE__))
require File.expand_path("future", File.dirname(__FILE__))


class PlanetWars
  attr_reader :planets, :fleets, :pending_fleets, :approved_fleets

  def initialize()
    @planets = []
    @pending_fleets = []
    @approved_fleets = []
  end

  def num_planets
    @planets.length
  end

  def get_planet(id)
    @planets[id]
  end

  def num_fleets
    @fleets.length
  end

  def get_fleet(id)
    @fleets[id]
  end

  def my_planets
    @planets.select {|planet| planet.owner == 1 }
  end

  def neutral_planets
    @planets.select {|planet| planet.owner == 0 }
  end

  def enemy_planets
    @planets.select {|planet| planet.owner > 1 }
  end

  def not_my_planets
    @planets.reject {|planet| planet.owner == 1 }
  end

  def my_fleets
    @fleets.select {|fleet| fleet.owner == 1 }
  end

  def enemy_fleets
    @fleets.select {|fleet| fleet.owner > 1 }
  end
  
  def clear_pending_fleets
    @pending_fleets.clear
  end
  
  def approve_pending_fleets
    @approved_fleets += @pending_fleets
    @pending_fleets.clear
  end
  
  def add_pending_fleet(source, destination, num_ships)
    dist = distance(source.planet_id, destination.planet_id)
    @pending_fleets << Fleet.new(1, num_ships, source.planet_id, destination.planet_id, dist, dist)
  end
  
  def send_approved_fleets
    $LOG.info("Sending #{approved_fleets.count} approved fleets")
    @approved_fleets.each do |fleet|
      issue_order(fleet.source_planet, fleet.destination_planet, fleet.num_ships)
    end
    @approved_fleets.clear
  end
  
  def enemy_center
    enemy_planets = Planet.enemies
    x, y, ship_count = 0, 0, 0
    enemy_planets.each do |planet|
      x += planet.x * planet.num_ships;
      y += planet.y * planet.num_ships;
      ship_count += planet.num_ships
    end
    x /= ship_count
    y /= ship_count
    return x, y
  end

  def to_s
    s = []
    @planets.each do |p|
      s << "P #{p.x} #{p.y} #{p.owner} #{p.num_ships} #{p.growth_rate}"
    end
    @fleets.each do |f|
      s << "F #{f.owner} #{f.num_ships} #{f.source_planet} #{f.destination_planet} #{f.total_trip_length} #{f.turns_remaining}"
    end
    return s.join("\n")
  end

  def distance(source_id, destination_id)
    source = get_planet(source_id)
    destination = get_planet(destination_id)
    return Math::sqrt( (source.x - destination.x)**2 + (source.y - destination.y)**2 ).ceil
  end

  def issue_order(source, destination, num_ships)
    puts "#{source} #{destination} #{num_ships}"
    STDOUT.flush
  end

  def is_alive(player_id)
    if (@planets.select{|p| p.owner == player_id }).length > 0
      return true
    elsif (@fleets.select{|p| p.owner == player_id }).length > 0
      return true
    else
      return false
    end
  end

  def parse_game_state(s)
    @fleets = []
    lines = s.split("\n")
    planet_id = 0

    lines.each do |line|
      line = line.split("#")[0]
      tokens = line.split(" ")
      next if tokens.length == 1
      if tokens[0] == "P"
        return 0 if tokens.length != 6
        p = get_planet(planet_id)
        if p
          p.update_state(tokens[3].to_i, tokens[4].to_i)
        else
          p = Planet.new(planet_id,
                         tokens[3].to_i, # owner
                         tokens[4].to_i, # num_ships
                         tokens[5].to_i, # growth_rate
                         tokens[1].to_f, # x
                         tokens[2].to_f) # y
          @planets << p
        end          
        planet_id += 1
      elsif tokens[0] == "F"
        return 0 if tokens.length != 7
        f = Fleet.new(tokens[1].to_i, # owner
                      tokens[2].to_i, # num_ships
                      tokens[3].to_i, # source
                      tokens[4].to_i, # destination
                      tokens[5].to_i, # total_trip_length
                      tokens[6].to_i) # turns_remaining
        @fleets << f
      else
        return 0
      end
    end
    return 1
  end

  def finish_turn
    puts "go"
    STDOUT.flush
  end
end
