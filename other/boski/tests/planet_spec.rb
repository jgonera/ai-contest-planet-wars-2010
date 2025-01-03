require File.expand_path("spec_helper", File.dirname(__FILE__))

describe Planet do
  describe :in_future do
    it "should properly handle non battle situations" do
      planet = create_planet(1, :owner => 1, :num_ships => 10, :growth_rate => 1)
      world = PlanetWars.new
      Fleet.world = world

      fleets = []
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 5, :owner => 1)
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 7, :owner => 1)
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 2, :num_ships => 4, :owner => 1)
      world.stub(:fleets => fleets)
      
      f1 = planet.in_future(1)
      f1.owner.should == 1
      f1.num_ships.should == 23
      
      f2 = planet.in_future(2)
      f2.owner.should == 1
      f2.num_ships == 28
    end
    
    it "should properly handle battle situations" do
      planet = create_planet(1, :owner => 1, :num_ships => 10, :growth_rate => 1)
      world = PlanetWars.new
      Fleet.world = world

      fleets = []
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 5, :owner => 2)
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 2, :num_ships => 8, :owner => 2)
      world.stub(:fleets => fleets)
      
      f1 = planet.in_future(1)
      f1.owner.should == 1
      f1.num_ships.should == 6
      
      f2 = planet.in_future(2)
      f2.owner.should == 2
      f2.num_ships == 1
    end
    
    it "should properly handle tie battle situations" do
      planet = create_planet(1, :owner => 1, :num_ships => 10, :growth_rate => 1)
      world = PlanetWars.new
      Fleet.world = world

      fleets = []
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 13, :owner => 2)
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 2, :owner => 1)
      world.stub(:fleets => fleets)

      f1 = planet.in_future(1)
      f1.owner.should == 1
      f1.num_ships.should == 0
    end
    
    it "should properly handle 3 forces battle" do
      planet = create_planet(1, :owner => 0, :num_ships => 10, :growth_rate => 1)
      world = PlanetWars.new
      Fleet.world = world

      fleets = []
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 11, :owner => 2)
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 12, :owner => 1)
      world.stub(:fleets => fleets)

      f1 = planet.in_future(1)
      f1.owner.should == 1
      f1.num_ships.should == 1
    end
    
    it "should properly handle 3 forces tie battle" do
      planet = create_planet(1, :owner => 0, :num_ships => 10, :growth_rate => 1)
      world = PlanetWars.new
      Fleet.world = world

      fleets = []
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 11, :owner => 2)
      fleets << create_fleet(:destination_planet => 1, :turns_remaining => 1, :num_ships => 11, :owner => 1)
      world.stub(:fleets => fleets)

      f1 = planet.in_future(1)
      f1.owner.should == 0
      f1.num_ships.should == 0
    end
  end
end