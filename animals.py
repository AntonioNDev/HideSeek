import pygame
import random
import math
from heapq import heappush, heappop

SPEED = 1

class Animal:
   def __init__(self, x, y, image, map_ref):
      self.y = y
      self.x = x
      self.image = image
      self.map = map_ref
      self.path = tuple()

      self.speed = SPEED
      self.health = 100
      self.tile_size = map_ref.tile_size
      self.rect = pygame.Rect(x, y, self.tile_size, self.tile_size)

   def draw(self, screen):
      """ Draw the animals on the map each frame """
      zoomed_x = (self.x * self.map.zoom_factor) - self.map.camera_offset.x
      zoomed_y = (self.y * self.map.zoom_factor) - self.map.camera_offset.y
      zoomed_image = pygame.transform.scale(
         self.image, 
         (int(self.tile_size * self.map.zoom_factor), int(self.tile_size * self.map.zoom_factor))
      )

      screen.blit(zoomed_image, (zoomed_x, zoomed_y))
   
   def update(self):
      """ Logic for the agents movment it updates their position each frame while handling the energy and movement"""
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
   
class Cow(Animal):
    def __init__(self, x, y, image, map_ref):
        super().__init__(x, y, image, map_ref)
        self.attacked = False
        self.last_wander_time = 0
        self.wander_interval = random.randint(10000, 15000)  # 10–15 seconds