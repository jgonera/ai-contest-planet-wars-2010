class Planet
  attr_reader :planet_id, :growth_rate, :x, :y
  attr_accessor :owner, :num_ships

  def initialize(planet_id, owner, num_ships, growth_rate, x, y)
    @planet_id, @owner, @num_ships = planet_id, owner, num_ships
    @growth_rate, @x, @y = growth_rate, x, y
  end
  
  def update_state(owner, num_ships)
     @owner, @num_ships = owner, num_ships
  end

  def add_ships(n)
    @num_ships += n
  end

  def remove_ships(n)
    @num_ships -= n
  end
  
  def distance_to(planet)
    return Math::sqrt( (self.x - planet.x)**2 + (self.y - planet.y)**2 ).ceil
  end
  
  def distance_to_point(x, y)
    return Math::sqrt( (self.x - x)**2 + (self.y - y)**2 ).ceil
  end
  
  def in_future(turns=1)
    Future.get_future_planet(self, turns)
  end
  
  def after_all_enemy_arrivals
    attacking = Fleet.attacking_planet(self)
    max_turns = attacking.empty? ? 0 : attacking[-1].turns_remaining
    in_future(max_turns)
  end
  
  def no_risk_ships
    future = after_all_enemy_arrivals
    now = in_future(0)
    if future.owner == 1
      [future.num_ships, now.num_ships].min - 1
    else 
      0
    end
  end
  
  def is_attacked?
    attacking_fleets.count > 0
  end
  
  def attacking_fleets
    Fleet.attacking_planet(self)
  end
  
  def neighbouring_allies(turns)
    my_planets = Planet.mine
    my_planets.select{ |planet| planet != self && self.distance_to(planet) <= turns}
  end
  
  def attractive_for(planet)
    if growth_rate == 0
      return 1000
    end
    distance_to(planet) + num_ships/growth_rate
  end
  
  def mine?
    owner == 1
  end
  
  def neutral?
    owner == 0
  end
  
  def enemies?
    owner > 0
  end
  
  def to_s
    "Planet id: #{planet_id}, owner: #{owner}, num ships: #{num_ships}, growth_rate: #{growth_rate}"
  end
  
  class << self
    attr_accessor :world
    
    def mine
      world.planets.select {|planet| planet.owner == 1 }
    end
  
    def neutral
      world.planets.select {|planet| planet.owner == 0 }
    end
    
    def enemies
      world.planets.select {|planet| planet.owner > 1 }
    end
  end
end