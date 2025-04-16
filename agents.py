from searching_framework import Problem, astar_search
import pygame
from gameMap import Map
from random import randint


class Agent:
   def __init__(self):
      self.age = 0
      self.energy = 20
      self.speed = 0.5
      self.hitDamage = randint(10, 50)
      self.profession = []

#Hider agent
class Hider:
   def __init__(self):
      ...

   
#Seeker agent
class Seeker(Problem, Map, Agent):
   def __init__(self, initial, goal=None):
      super().__init__(initial, goal)
      super(Agent).__init__()
   
   def successor(self, state):
      successors = dict()

      return successors
   
   def actions(self, state):
      return self.successor(state).keys() 

   def result(self, state, action):
      return self.successor(state)[action]
   
   def h(self, node):
      ...

   def goal_test(self, state):
      ...