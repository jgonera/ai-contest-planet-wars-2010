require File.expand_path("../MyBot.rb", File.dirname(__FILE__))

RSpec.configure do |config|
  config.mock_framework = :rspec
end

def create_planet(planet_id, options = {})
  Planet.new(planet_id, 
    options[:owner] || 0, 
    options[:num_ships] || 100,
    options[:growth_rate] || 5,
    options[:x] || 10,
    options[:y] || 10)
end

def create_fleet(options = {})
  Fleet.new(options[:owner] || 0,
    options[:num_ships] || 6,
    options[:source_planet] || 1,
    options[:destination_planet] || 2,
    options[:total_trip_length] || 20,
    options[:turns_remaining] || 1)
end