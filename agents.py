import pygame
import random
import math
from heapq import heappush, heappop

# AGENTS AND MAP CONFIGURATIONS
MAX_ENERGY = 5
ENERGY_REGEN_RATE = 0.010
ENERGY_DRAIN_RATE = 0.002
SPEED = 1
MAX_SPEED = 1.3

# Parent Agents class
class Agent:
   def __init__(self, x, y, image, map_ref):
      self.x = x
      self.y = y
      self.image = image
      self.map = map_ref
      self.path = list()

      self.speed = SPEED
      self.max_energy = MAX_ENERGY
      self.energy = MAX_ENERGY
      self.recovery_mode = False

      self.tile_size = map_ref.tile_size
      self.rect = pygame.Rect(x, y, self.tile_size, self.tile_size)
      self.mode = None
      self._last_regen_time = pygame.time.get_ticks()

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

   def _handle_energy(self):
      """ Logic to handle energy drain/regain/speed """
      if self.recovery_mode:
         self.mode = "resting"
         self.energy = min(self.max_energy, self.energy + ENERGY_REGEN_RATE)

         if self.energy >= self.max_energy:
            self.recovery_mode = False

            if isinstance(self, Seeker):
               self.mode = "exploring"

         return

      if self.energy <= 0.5 and not self.recovery_mode:
         self.recovery_mode = True
         self.speed = 0
         return

      if not self.path:
         # Not moving = regenerate
         self.energy = min(self.max_energy, self.energy + ENERGY_REGEN_RATE)
      else:
         # Moving = drain
         self.energy = max(0, self.energy - ENERGY_DRAIN_RATE)

      # Adjust speed based on energy
      if self.energy >= 4.5:
         self.speed = MAX_SPEED # Sprint if it's on full energy
      elif self.energy < 2:
         self.speed = 0.8
      else:
         self.speed = SPEED
   
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
   
class Hider(Agent):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)
      self.caught = False
      self.mode = "hiding"
   
   def find_spot(self, hider_poss, seeker_poss):
      if self.mode == "hiding":
         for _ in range(10):  # retry loop to avoid endless fails
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
      # FIX: THIS SHIT
      elif self.mode == "panic":
         hx, hy = hider_poss
         sx, sy = seeker_poss

         # Vector pointing away from seeker
         dx = hx - sx
         dy = hy - sy

         # Normalize direction
         length = (dx ** 2 + dy ** 2) ** 0.5
         if length == 0:
            dx, dy = 1, 0  # Arbitrary direction if on same tile
         else:
            dx /= length
            dy /= length

         # Step away in that direction until we find a good tile
         step_size = 1
         best_tile = None

         for step in range(1, max(self.map.cols, self.map.rows)):
            tx = int(hx + dx * step)
            ty = int(hy + dy * step)

            # Break if out of bounds
            if tx < 0 or ty < 0 or tx >= self.map.cols or ty >= self.map.rows:
                  break

            tile = self.map.map_data[tx][ty]
            if not tile.walkable:
                  break
            if tile.obstacle not in ["tree", None]:
                  break

            best_tile = (tx, ty)  # Update as we find further valid tiles

         # If we found somewhere to go, path there
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

      if hider_poss == seeker_poss:
         self.caught = True
         return
      
      distance = self.heuristic(hider_poss, seeker_poss)

      if self.mode == "hiding":
         self.find_spot(hider_poss, seeker_poss)
      
      if distance <= 5:
         self.mode = "panic"
         self.find_spot(hider_poss, seeker_poss)
      
      elif distance > 10 and not self.path:
         self.mode = "hidden"
      

class Seeker(Agent):
   def __init__(self, x, y, image, map_ref):
      super().__init__(x, y, image, map_ref)
      self.vision = random.randrange(5, 9)
      self.mode = "exploring"
      self.explored_tiles = set()
      self.offsets = [(-2,0), (2,0), (0,-2), (0,2), (-1,-1), (1,1), (-2,2), (2,-2)] 
      self.attempts = 0 # How many attempts the Seeker tried to find the Hider

   def explore(self, seeker_poss, hider_poss):
      self.attempts += 1

      # Here the Seeker if he tried to find the hider
      # for more than 5 times, it goes into agresive mode
      # and uses the a_star to go close to the hider position but not the exact position
      if self.attempts >= 10:
         random.shuffle(self.offsets)

         for dx, dy in self.offsets:
            # Go to a position close to the Hider
            tx, ty = hider_poss[0] + dx, hider_poss[1] + dy

            if self.map.is_walkable(tx, ty) and (tx, ty) not in self.explored_tiles:
               path = self.a_star(seeker_poss, (tx, ty))

               if path:
                  self.set_path(path)
                  self.explored_tiles.add((tx, ty))
                  self.attempts = 0
                  return
         return
      
      else:
         # Here the Seeker searches randomly for a tail
         for _ in range(3):
            tx = random.randint(0, self.map.cols - 1)
            ty = random.randint(0, self.map.rows - 1)

            if self.map.is_walkable(tx, ty) and (tx, ty) not in self.explored_tiles:
               path = self.a_star(seeker_poss, (tx, ty))
               if path:
                  self.set_path(path)
                  self.explored_tiles.add((tx, ty))
                  break
    
   def search(self, hider_poss):
      if self.recovery_mode:
         return

      if self.path:
         return
      
      seeker_poss = self.get_tile_pos()
      
      if self.mode == "exploring" and not self.path:
         self.explore(seeker_poss, hider_poss)
   
   def update(self, hider_poss):
      if not self.path:
         return
      
      seeker_poss = self.get_tile_pos()
      distance = self.heuristic(seeker_poss, hider_poss)

      current_time = pygame.time.get_ticks()

      if distance <= self.vision:
         if seeker_poss != hider_poss:
            # Only recalc path if cooldown passed (e.g. 1000ms = 1s)
            if current_time - getattr(self, "last_calc_time", 0) >= 1000:
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
