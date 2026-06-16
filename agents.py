import random
import pygame

from entity import Entity
from pathFinding import AStar

# CONFIG
MAX_ENERGY = 5
ENERGY_REGEN = 0.01
ENERGY_DRAIN = 0.002

BASE_SPEED = 1
SPRINT_SPEED = 1.2

# Parent Agent class
class Agent(Entity):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)

      self.pathfinder = AStar(map_ref)

      # Needs
      self.energy = random.uniform(2.5, MAX_ENERGY)
      self.hunger = 5

      # Perception
      self.vision = random.randint(5, 7)

      # State
      self.state = "idle"
      self.target = None

      # Flags
      self.recovering = False

   # Core update func
   def update(self, context):
      self._update_needs()

      action = self.decide(context)
      self.execute(action, context)

      self.move_along_path()

   def _update_needs(self):
      # Energy
      if self.recovering:
         self.energy = min(MAX_ENERGY, self.energy + ENERGY_REGEN)

         if self.energy >= MAX_ENERGY:
               self.recovering = False

         return

      if self.path:
         self.energy = max(0, self.energy - ENERGY_DRAIN)
         self.hunger = max(0, self.hunger - 0.001)
      else:
         self.energy = min(MAX_ENERGY, self.energy + ENERGY_REGEN)

      if self.energy <= 0.1:
         self.recovering = True
         self.speed = 0

   # Decision making function
   def decide(self, context):
      # 1. Hard survival priority
      if self.recovering:
         return "rest"

      # 2. Threat overrides everything
      if context.get("enemy_visible"):
         return "react"

      # 3. Hunger
      if self.hunger <= 1:
         return "hunt"

      # 4. Default
      return "explore"

   # Action execution
   def execute(self, action, context):
      if action == "rest":
         self.state = "resting"
         self.speed = 0

      elif action == "hunt":
         self.state = "hunting"
         self.hunt(context)

      elif action == "react":
         self.state = "reacting"
         self.react(context)

      elif action == "explore":
         self.state = "exploring"
         self.explore(context)

   # Agent behaviors (override in children)
   def hunt(self, context):
      pass

   def react(self, context):
      pass

   def explore(self, context):
      if self.path:
         return

      cx, cy = self.get_tile_pos()

      for _ in range(5):
         tx = random.randint(0, self.map.cols - 1)
         ty = random.randint(0, self.map.rows - 1)

         if self.map.is_walkable(tx, ty):
            path = self.pathfinder.find_path((cx, cy), (tx, ty))
            if path:
               self.set_path(path)
               return

   def get_speed(self):
      if self.energy < 1:
         return 0.8
      return BASE_SPEED

# Normal villager tries to survive and hide from the seeker
class Villager(Agent):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)

      self.state = "idle"
      self.caught = False

   def decide(self, context):
      if self.recovering:
         return "rest"

      if context.get("enemy_visible"):
         return "flee"

      if self.hunger <= 1:
         return "hunt"

      return "explore"

   def execute(self, action, context):
      if action == "flee":
         self.state = "fleeing"
         self.flee(context["enemy_pos"])
         self.speed = SPRINT_SPEED

      else:
         super().execute(action, context)

   def flee(self, enemy_pos):
      cx, cy = self.get_tile_pos()

      dx = cx - enemy_pos[0]
      dy = cy - enemy_pos[1]

      tx = cx + int(dx * 3)
      ty = cy + int(dy * 3)

      if self.map.is_walkable(tx, ty):
         path = self.pathfinder.find_path((cx, cy), (tx, ty))
         if path:
               self.set_path(path)

# Seeker tries to survive and hunts villagers
class Seeker(Agent):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)

      self.state = "exploring"

   def decide(self, context):
      if self.recovering:
         return "rest"

      if context.get("enemy_visible"):
         return "chase"

      if self.hunger <= 1:
         return "hunt"

      return "explore"

   def execute(self, action, context):
      if action == "chase":
         self.state = "chasing"
         self.chase(context["enemy_pos"])
         self.speed = SPRINT_SPEED

      else:
         super().execute(action, context)

   def chase(self, target_pos):
      cx, cy = self.get_tile_pos()

      path = self.pathfinder.find_path((cx, cy), target_pos)
      if path:
         self.set_path(path)