import random

from entity import Entity
from pathFinding import AStar

# CONFIG
BASE_SPEED = 1
SPRINT_SPEED = 1.3

MAX_STAMINA = 5
STAMINA_DRAIN = 0.02
STAMINA_REGEN = 0.01


# Base animal class
class Animal(Entity):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)

      self.pathfinder = AStar(map_ref)

      # Needs
      self.stamina = MAX_STAMINA

      # State
      self.state = "idle"

      # Wander control
      self.last_wander_time = 0
      self.wander_interval = random.randint(2000, 5000)

   # Main update func
   def update(self, context):
      self._update_stamina()

      action = self.decide(context)
      self.execute(action, context)

      self.move_along_path()

   def _update_stamina(self):
      if self.state == "fleeing":
         self.stamina = max(0, self.stamina - STAMINA_DRAIN)
      else:
         self.stamina = min(MAX_STAMINA, self.stamina + STAMINA_REGEN)

   # Decisions
   def decide(self, context):
      # 1. Danger has highest priority
      if context.get("danger"):
         return "flee"

      # 2. Exhaustion
      if self.stamina <= 0.5:
         return "rest"

      # 3. Default behavior
      return "wander"

   # Executions
   def execute(self, action, context):
      if action == "flee":
         self.state = "fleeing"
         self.speed = SPRINT_SPEED
         self.flee(context["danger_pos"])

      elif action == "rest":
         self.state = "resting"
         self.speed = 0
         self.path.clear()

      elif action == "wander":
         self.state = "wandering"
         self.speed = BASE_SPEED
         self.wander()

   # Behaviors
   def wander(self):
      if self.path:
         return

      cx, cy = self.get_tile_pos()

      # Small local movement → clustering behavior
      for _ in range(5):
         tx = cx + random.randint(-3, 3)
         ty = cy + random.randint(-3, 3)

         if self.map.is_walkable(tx, ty):
            path = self.pathfinder.find_path((cx, cy), (tx, ty))
            if path:
               self.set_path(path)
               return

   def flee(self, danger_pos):
      cx, cy = self.get_tile_pos()

      dx = cx - danger_pos[0]
      dy = cy - danger_pos[1]

      # Normalize direction
      length = max(1, abs(dx) + abs(dy))
      dx //= length
      dy //= length

      # Run away multiple tiles
      tx = cx + dx * random.randint(3, 6)
      ty = cy + dy * random.randint(3, 6)

      if self.map.is_walkable(tx, ty):
         path = self.pathfinder.find_path((cx, cy), (tx, ty))
         if path:
               self.set_path(path)

class Cow(Animal):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)

      self.type = "cow"