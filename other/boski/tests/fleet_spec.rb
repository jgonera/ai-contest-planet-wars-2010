require File.expand_path("spec_helper", File.dirname(__FILE__))

describe Fleet do
  describe :approaching_planet do
    it "should return fleet approaching particular planet sorted by turns remaining" do
      planet = create_planet(1)
      planet2 = create_planet(2)
      world = PlanetWars.new
      Fleet.world = world

      fleets = []
      fleets << fleet1 = create_fleet(:destination_planet => 1, :turns_remaining => 4)
      fleets << fleet2 = create_fleet(:destination_planet => 1, :turns_remaining => 8)
      fleets << fleet3 = create_fleet(:destination_planet => 1, :turns_remaining => 6)
      fleets << fleet4 = create_fleet(:destination_planet => 2, :turns_remaining => 6)
      world.stub(:fleets => fleets)
      
      Fleet.approaching_planet(planet).should == [fleet1, fleet3, fleet2]
    end
  end
  
  describe :future_planet do
    it "should return fleet approaching particular planet sorted by turns remaining" do
      planet = create_planet(1)
      planet2 = create_planet(2)
      world = PlanetWars.new
      Fleet.world = world

      fleets = []
      fleets << fleet1 = create_fleet(:destination_planet => 1, :turns_remaining => 4)
      fleets << fleet2 = create_fleet(:destination_planet => 1, :turns_remaining => 8)
      fleets << fleet3 = create_fleet(:destination_planet => 1, :turns_remaining => 6)
      fleets << fleet4 = create_fleet(:destination_planet => 2, :turns_remaining => 6)
      world.stub(:fleets => fleets)
      
      Fleet.approaching_planet(planet).should == [fleet1, fleet3, fleet2]
    end
  end
end