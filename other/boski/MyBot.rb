#!/usr/bin/env ruby
require File.expand_path("planetwars/planetwars", File.dirname(__FILE__))
require File.expand_path("mystrategy", File.dirname(__FILE__))
require 'logger'

$LOG = Logger.new('mystrategy.log')
$LOG.level = Logger::ERROR

$mystrategy = MyStrategy.new
$mystrategy.initialize_world

def do_turn(game_state)
  begin
    $mystrategy.parse_game_state(game_state)
    $mystrategy.do_turn
    $mystrategy.finish_turn
  rescue Exception => e
    $LOG.error("Exception: #{e.backtrace.join('\n')}")
    exit
  end
end

map_data = ''
loop do
  current_line = gets.strip rescue break
  if current_line.length >= 2 and current_line[0..1] == "go"
    do_turn(map_data)
    map_data = ''
  else
    map_data += current_line + "\n"
  end
end