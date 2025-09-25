import pygame
import random
import math
from heapq import heappush, heappop

# ENERGY CONFIG
MAX_ENERGY = 5
ENERGY_REGEN_RATE = 0.010
ENERGY_DRAIN_RATE = 0.002

# SPEED CONFIG
SPEED = 1
MAX_SPEED = 1.2

# Parent Agents class
class Agent:
   def __init__(self, x, y, image, map_ref):
      self.x = x
      self.y = y
      self.image = image
      self.map = map_ref
      self.path = tuple()

      self.speed = SPEED
      self.max_energy = MAX_ENERGY
      self.energy = MAX_ENERGY
      self.vision = random.randint(5, 7)
      self.hunger = 5 # Every agent starts with full bars

      self.recovery_mode = False

      self.tile_size = map_ref.tile_size
      self.rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
      self.mode = None

   def draw(self, screen):
      """ Draw the agents on the map each frame """
      zoomed_x = (self.x * self.map.zoom_factor) - self.map.camera_offset.x
      zoomed_y = (self.y * self.map.zoom_factor) - self.map.camera_offset.y
      zoomed_image = pygame.transform.scale(
         self.image, 
         (int(self.tile_size * self.map.zoom_factor), int(self.tile_size * self.map.zoom_factor))
      )

      screen.blit(zoomed_image, (zoomed_x, zoomed_y))

   def update(self):
      """ Logic for the agents movment it updates their position each frame while handling the energy and movement"""
      self._handle_energy()

      # Hard stop while recovering
      if self.recovery_mode:
         self.rect.topleft = (self.x, self.y)
         return

      if self.path:
         tx, ty = self.path[0]
         px = tx * self.tile_size
         py = ty * self.tile_size
         dx = px - self.x
         dy = py - self.y

         dist = math.hypot(dx, dy)

         if dist < self.speed and dist > 0:
            self.x, self.y = px, py
            self.path.pop(0)

         elif dist > 0:
            self.x += self.speed * dx / dist
            self.y += self.speed * dy / dist
         else:
            # Already exactly at target — just pop it
            self.path.pop(0)

         self.rect.topleft = (self.x, self.y)

   def set_path(self, path):
      self.path = path
   
   def get_tile_pos(self):
      return int(self.x // self.tile_size), int(self.y // self.tile_size)

   def calculate_energy_drain(self, speed, is_sprinting, base_rate=0.0010):
      """
      Returns energy drain per tick/frame.
      - base_rate: idle drain
      - walking ~1x drain
      - sprinting ~0.5x drain
      """

      # Idle or walking slowly
      drain = base_rate  

      # Walking normally (speed around 1.0–1.2)
      if speed > 0.8:
         drain += 0.0001 * speed  # gentle increase

      # Sprint/panic mode = multiplier
      if is_sprinting:
         drain *= 0.001

      return drain
   
   def _handle_energy(self):
      """ Logic to handle energy drain/regain """
      if self.recovery_mode:
         self.mode = "resting"
         self.energy = min(self.max_energy, self.energy + ENERGY_REGEN_RATE)

         if self.energy >= self.max_energy:
            self.recovery_mode = False

            if isinstance(self, Seeker):
               self.mode = "exploring"
         return

      if self.energy <= 0.1 and not self.recovery_mode:
         self.recovery_mode = True
         self.speed = 0
         return

      if not self.path:
         # Not moving = regenerate
         self.energy = min(self.max_energy, self.energy + ENERGY_REGEN_RATE)
      else:
         # Moving = drain
         drain_rate = ENERGY_DRAIN_RATE * (self.speed / SPEED) ** 2
         self.energy = max(0, self.energy - drain_rate)


         is_sprinting = self.speed >= 1.2
         hunger_drain_rate = self.calculate_energy_drain(self.speed, is_sprinting)
         self.hunger = max(0, self.hunger - hunger_drain_rate)

   def heuristic(self, a, b):
      """logic to find the shortest path from point A to point B"""

      return abs(a[0] - b[0]) + abs(a[1] - b[1])
   
   def a_star(self, start, end):
      """ A-star algorithm to find the best path from start to end"""
      if start == end:
         return []

      open_set = []
      came_from = {}
      g_score = {start: 0}
      f_score = {start: self.heuristic(start, end)}
      heappush(open_set, (f_score[start], start))

      while open_set:
         _, current = heappop(open_set)
         if current == end:
            return self.reconstruct_path(came_from, current)

         for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)

            if not self.map.is_walkable(*neighbor):
               continue

            tentative_g = g_score[current] + 1

            if neighbor not in g_score or tentative_g < g_score[neighbor]:
               came_from[neighbor] = current
               g_score[neighbor] = tentative_g
               f_score[neighbor] = tentative_g + self.heuristic(neighbor, end)
               heappush(open_set, (f_score[neighbor], neighbor))
      
      return []

   def reconstruct_path(self, came_from, current):
      path = [current]
      while current in came_from:
         current = came_from[current]
         path.append(current)

      return path[::-1]
   
   def check_overlap(self, current_path: list) -> bool:
      overlap_ratio = len(set(current_path) & set(list(self.explored_tiles)[1:])) / len(current_path)

      if overlap_ratio < 0.39:
         return True
      else:
         return False

   def get_speed(self):
      if self.energy < 1:
         return 0.8
      
      return SPEED

class Hider(Agent):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)
      self.x = x
      self.y = y

      self.energy = random.uniform(2.5, 5)
      
      self.caught = False
      self.mode = "hiding"
      self.cooldown = random.randint(20*1000, 60*1000) # Cooldown for hiding between 20s and 1 minute
   
   def find_spot(self, hider_poss, seeker_poss):
      if self.mode == "hiding":
         for _ in range(5):  # retry loop to avoid endless fails
            tx = random.randint(0, self.map.cols - 1)
            ty = random.randint(0, self.map.rows - 1)
            tile = self.map.map_data[tx][ty]

            if not tile.walkable:
               continue

            if tile.obstacle in ["tree"]:
               path = self.a_star(hider_poss, (tx, ty))
               if path:
                  self.set_path(path)
                  self.failed_panic_attempts = 0
                  self.mode = "I found a place!."
                  return
      
      elif self.mode == "panic":
         hx, hy = hider_poss
         sx, sy = seeker_poss

         # Vector away from seeker
         dx = hx - sx
         dy = hy - sy

         # Normalize
         length = (dx ** 2 + dy ** 2) ** 0.5
         if length == 0:
            dx, dy = 1, 0
         else:
            dx /= length
            dy /= length

         # Candidate directions (away, left, right, random jitter)
         candidate_dirs = [
            (dx, dy),           # directly away
            (-dy, dx),          # perpendicular left
            (dy, -dx),          # perpendicular right
            ((dx+dy)*0.7, (dy-dx)*0.7),  # diagonal variant
            ((dx-dy)*0.7, (dy+dx)*0.7)   # another diagonal
         ]

         best_tile = None
         max_steps = min(5, max(2, int(length)))
         
         for dirx, diry in candidate_dirs:
            for step in range(max_steps, max(self.map.cols, self.map.rows)):
               tx = int(hx + dirx * step)
               ty = int(hy + diry * step)

               # Out of bounds check
               if tx < 0 or ty < 0 or tx >= self.map.cols or ty >= self.map.rows:
                  break

               tile = self.map.map_data[tx][ty]

               # Skip if blocked
               if not tile.walkable:
                  break
               if tile.obstacle not in ["tree", None]:
                  break

               # Don’t run directly into seeker’s tile
               if (tx, ty) == seeker_poss:
                  break

               best_tile = (tx, ty)
               break  # Stop at first valid in this direction

            if best_tile:
               break  # Found a good escape, no need to test other dirs

         if best_tile:
            path = self.a_star(hider_poss, best_tile)
            if path:
               self.set_path(path)
               self.failed_panic_attempts = 0
               return
 
   def hide(self, seeker_poss):
      if self.path:
         return
      
      hider_poss = self.get_tile_pos()
      distance = self.heuristic(hider_poss, seeker_poss)
      
      if distance <= 4:
         self.mode = "panic"
         self.find_spot(hider_poss, seeker_poss)

      if self.mode == "hiding":
         self.find_spot(hider_poss, seeker_poss)
      
      elif distance > 10 and not self.path:
         self.mode = "hidden"
      
   def get_speed(self):
      if self.mode == "panic" and self.energy > 1.1:
         return MAX_SPEED
      return super().get_speed()

   def update(self, seeker_poss):
      self.speed = self.get_speed()

      current_poss = self.get_tile_pos()

      if seeker_poss == current_poss:
         self.path.clear()
         self.caught = True
         self.speed = 0
         self.mode = "I got caught!."
         return
      
      if self.mode == "hidden":
         current_time = pygame.time.get_ticks()

         if not hasattr(self, "last_calc_time_"):
            self.last_calc_time_ = current_time  # set when first entering hidden mode

         if current_time - self.last_calc_time_ >= self.cooldown:
            self.mode = "hiding"
            self.find_spot(current_poss, seeker_poss)

            self.last_calc_time_ = current_time # Reset timer
            self.cooldown = random.randint(20*1000, 60*1000)
            
      x, y = current_poss
      tile = self.map.map_data[x][y].obstacle is None

      if tile and not self.path:
         self.mode = "hiding"
         self.find_spot(current_poss, seeker_poss)

      return super().update()
   
class Seeker(Agent):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)

      self.energy = random.uniform(2.5, 5)
      self.attempts = 0 # How many attempts the Seeker tried to find the Hider
      self.cooldown = 5000

      self.offsets = [(-2,0), (2,0), (0,-2), (0,2), (-1,-1), (1,1), (-2,2), (2,-2)] 
      self.explored_tiles = set()
      
      self.mode = "exploring"

   def explore(self, seeker_poss, hider_poss):
      self.attempts += 1

      # Here the Seeker if he tried to find the hider
      # for more than 5 times, it goes into agresive mode
      # and uses the a_star to go close to the hider position but not the exact position
      if self.attempts >= 3:
         self.explored_tiles.clear()
         random.shuffle(self.offsets)

         for dx, dy in self.offsets:
            # Go to a position close to the Hider
            tx, ty = hider_poss[0] + dx, hider_poss[1] + dy

            if self.map.is_walkable(tx, ty):
               path = self.a_star(seeker_poss, (tx, ty))

               if path and self.check_overlap(path):
                  self.set_path(path)
                  self.attempts = 0
                  break
      else:
         # Here the Seeker searches randomly for a tail
         for _ in range(3):
            tx = random.randint(0, self.map.cols - 1)
            ty = random.randint(0, self.map.rows - 1)

            if self.map.is_walkable(tx, ty):
               path = self.a_star(seeker_poss, (tx, ty))
               if path and self.check_overlap(path):
                  self.set_path(path)
                  break
    
   def search(self, hider_poss):
      if self.recovery_mode:
         return

      if self.path:
         return
      
      seeker_poss = self.get_tile_pos()
      
      if self.mode == "exploring" and not self.path:
         self.explore(seeker_poss, hider_poss)
   
   def get_speed(self):
      if self.mode == "chasing" and self.energy > 1.1:
         return MAX_SPEED
      return super().get_speed()
   
   def update(self, hider_poss):
      self.speed = self.get_speed()

      seeker_poss = self.get_tile_pos()
      distance = self.heuristic(seeker_poss, hider_poss)

      if distance <= self.vision + 1:
         self.cooldown = 1000

      x, y = seeker_poss
      x1, y1 = hider_poss # Cordinates to check if the Hidder is not hidden in a field place
      hider_place = self.map.map_data[x1][y1].biom
      seeker_place = self.map.map_data[x][y].biom 

      if hider_place is None and seeker_place is None: # IF the agent has energy and the hider is not hidden well that makes the Seeker vision better
         self.vision = 8
      elif hider_place == 'forest' and seeker_place == 'forest':
         self.vision = 4
      else:
         self.vision = self.vision

      if (x, y) not in self.explored_tiles:
         self.explored_tiles.add((x,y))
         self.map.map_data[x][y].explored = True

      current_time = pygame.time.get_ticks()

      if distance <= self.vision:
         if seeker_poss != hider_poss:
            # Only recalc path if cooldown passed
            if current_time - getattr(self, 'last_calc_time', 0) >= self.cooldown:
               path = self.a_star(seeker_poss, hider_poss)
               if path:
                  if path[0] == seeker_poss:
                     path = path[1:]
                  self.set_path(path)

               self.last_calc_time = current_time  # reset cooldown

         self.mode = "chasing"

      elif distance > self.vision:
         self.mode = "exploring"

      super().update()

