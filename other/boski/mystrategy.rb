class MyStrategy 
  def initialize()
    @turn = 0
  end
  
  def initialize_world
    @world = PlanetWars.new
    Planet.world = @world
    Fleet.world = @world
  end
  
  def parse_game_state(state)
    @world.parse_game_state(state)
  end
  
  def finish_turn
    @world.send_approved_fleets
    puts "go"
    STDOUT.flush
  end
  
  def do_turn
    @turn += 1
    $LOG.info("Starting turn #{@turn}")
    defend
    attack
    transfer
    $LOG.info("End of turn #{@turn}")
  end
  
  def defend
    $LOG.info("--------Defending----------")
    my_planets = Planet.mine
    my_planets.sort_by!{ |a| a.growth_rate }
    
    
    my_planets.each do |planet|
      if planet.is_attacked?
        $LOG.info("Trying to defend #{planet}")
        planet.attacking_fleets.each do |fleet|
          $LOG.info("Attacked by: #{fleet}")
          future = planet.in_future(fleet.turns_remaining)
          
          unless future.owner == 1            
            ships_needed = future.num_ships
            $LOG.info("Need to defend against: #{fleet}, needed_ships: #{ships_needed}")
            
            @world.clear_pending_fleets
            planet.neighbouring_allies(fleet.turns_remaining-1).each do |ally|
              available = ally.no_risk_ships
              
              if available > 0
                to_send = [available, ships_needed].min
                ships_needed -= to_send
                $LOG.info("Sending rescue fleet #{to_send} from #{ally}")
                @world.add_pending_fleet(ally, planet, to_send)
              end
              
              if ships_needed <= 0
                $LOG.info("Successfully defended")
                
                @world.approve_pending_fleets
                break
              end
            end  
            
            if ships_needed > 0
              break;
            end
          end
        end
      end
    end
  end
  
  def attack
    $LOG.info("--------Attack----------")
    attack_enemies
    attack_neutrals
  end
  
  def attack_enemies
    @world.clear_pending_fleets
    my_planets = Planet.mine
    my_planets.each do |planet|
      closest_enemy = Planet.enemies.sort_by!{ |e| e.distance_to(planet) }.first
      available_ships = planet.no_risk_ships
      unless closest_enemy.nil?
        distance = planet.distance_to(closest_enemy)
        $LOG.info("Distance: #{distance}")
        future_enemy = closest_enemy.in_future(distance)
        if future_enemy.owner > 1 && available_ships >future_enemy.num_ships
          $LOG.info("Attacking with #{future_enemy.num_ships+1} planet #{closest_enemy}, in future #{future_enemy}")
          
          @world.add_pending_fleet(planet, closest_enemy, future_enemy.num_ships+1)
          @world.approve_pending_fleets
        end
      end
    end
  end
  
  def attack_neutrals
    @world.clear_pending_fleets
    my_planets = Planet.mine
    my_planets.each do |planet|
      neutral_planets = Planet.neutral
      neutral_planets.sort_by!{ |n| n.attractive_for(planet)}
      
      neutral_planets.each do |neutral|
        future_neutral = neutral.in_future(planet.distance_to(neutral))
        to_conquer = future_neutral.num_ships+1
        if to_conquer < planet.no_risk_ships
          $LOG.info("Attacking #{neutral} with #{to_conquer} ships from planet #{planet}")
          @world.add_pending_fleet(planet, neutral, to_conquer)
          @world.approve_pending_fleets
        end
      end
    end
  end
  
  def transfer
    $LOG.info("--------Transfer----------")
    @world.clear_pending_fleets
    # x, y  = @world.enemy_center
    # my_planets = Planet.mine.sort_by!{ |planet| planet.distance_to_point(x, y)}
    # my_planets.each_with_index do |planet, i|
    #   available = planet.no_risk_ships
    #   to_transfer = (available/2).ceil
    #   where = (i/2).floor
    #   if to_transfer > 0 && i > 0
    #     $LOG.info("Transfering #{to_transfer} from #{planet} to #{my_planets[where]}")   
    #     @world.add_pending_fleet(planet, my_planets[where], to_transfer)
    #     @world.approve_pending_fleets
    #   end
    # end
    
    my_planets = Planet.mine
    my_planets.each do |planet|
      available = planet.no_risk_ships
      to_transfer = (available/2).ceil
      if to_transfer > 0
        closest_enemy = Planet.enemies.sort_by{ |e| e.distance_to(planet) }.first
        unless closest_enemy.nil?
          my_closest = my_planets.sort_by{ |p| p.distance_to(closest_enemy) }.first
          if my_closest != planet
            $LOG.info("Transfering #{to_transfer} from #{planet} to #{my_closest}")   
            @world.add_pending_fleet(planet, my_closest, to_transfer)
            @world.approve_pending_fleets
          end
        end
      end
    end
  end
end