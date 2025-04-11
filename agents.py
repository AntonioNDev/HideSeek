from searching_framework import Problem, astar_search
from mapp import Map

#Hider agent
class Hider(Problem, Map):
   def __init__(self, initial, goal=None):
      super().__init__(initial, goal)

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
   
#Seeker agent
class Seeker(Problem, Map):
   def __init__(self, initial, goal=None):
      super().__init__(initial, goal)
   
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