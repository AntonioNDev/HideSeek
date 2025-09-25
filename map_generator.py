import pygame
import random
import json
from noise import pnoise2
from pathlib import Path

class Tile:
   def __init__(self, x, y, size, surface=None, obstacle=None):
      self.x = x
      self.y = y
      self.size = size
      self.surface = surface
      self.obstacle = obstacle
      self.walkable = True if obstacle is None else False
      self.biom = "grassland"
      self.explored = False
      self.render_offset = pygame.Vector2(0, 0)

   def draw(self, screen):
      if self.surface:
         draw_x = self.x * self.size + self.render_offset.x
         draw_y = self.y * self.size + self.render_offset.y
         screen.blit(self.surface, (draw_x, draw_y))

   def to_dict(self):
      return {
         'x': self.x,
         'y': self.y,
         'obstacle': self.obstacle,
         'biom': self.biom,
         'explored': self.explored,
         'walkable': self.walkable
      }

   @staticmethod
   def from_dict(data):
      return Tile(data['x'], data['y'], 16, None, data['obstacle'])

class Map:
   def __init__(self, width, height, tile_size=16):
      self.width = width
      self.height = height
      self.tile_size = tile_size
      self.cols = self.width // tile_size
      self.rows = self.height // tile_size

      self.zoom_factor = 1.0
      self.min_zoom = 1.0
      self.max_zoom = 2.8
      self.camera_offset = pygame.Vector2(0, 0)

      self.map_data = [[Tile(x, y, tile_size) for y in range(self.rows)] for x in range(self.cols)]
      self.assets = self.load_assets()
      self.map_surface = pygame.Surface((self.width, self.height))

      self.perlin_offset_x = random.uniform(0, 1000)
      self.perlin_offset_y = random.uniform(0, 1000)

   def load_assets(self, asset_dir="assets"):
      data = {"trees": [], "rocks": [], "water": [], "grass": None}
      for f in Path(asset_dir).iterdir():
         if not f.is_file(): continue
         asset = pygame.image.load(str(f)).convert_alpha()
         if "tree" in f.name:
               data["trees"].append(asset)
         elif "rock" in f.name:
               data["rocks"].append(asset)
         elif "water" in f.name:
               data["water"].append(asset)
         elif "grass" in f.name:
               data["grass"] = asset
      return data

   def generate_map(self, scale=5):
      for x in range(self.cols):
         for y in range(self.rows):
            tile = self.map_data[x][y]

            if tile.obstacle:
               continue

            nx = (x / self.cols - 1) * scale + self.perlin_offset_x
            ny = (y / self.rows - 1) * scale + self.perlin_offset_y
            noise_val = (pnoise2(nx, ny) + 1) / 2

            if noise_val < 0.25:
               tile.obstacle = "water"
               tile.surface = random.choice(self.assets["water"])
               tile.walkable = False
               tile.biom = "lake"
               tile.render_offset = pygame.Vector2(0, 0)

            elif noise_val < 0.35:
               tile.obstacle = "rock"
               tile.surface = pygame.transform.scale(
                  random.choice(self.assets["rocks"]),
                  (tile.size, tile.size)
               )
               tile.walkable = False
               tile.biom = "rocky"
               tile.render_offset = pygame.Vector2(0, 0)

            elif noise_val < 0.55:
               tile.obstacle = "tree"
               tree_img = random.choice(self.assets["trees"])
               tile.surface = pygame.transform.scale(tree_img, (tile.size, tile.size * 1.5 ))
               tile.render_offset = pygame.Vector2(0, -tile.size)
               tile.walkable = True
               tile.biom = "forest"

            else:
               tile.surface = None
               tile.walkable = True
               tile.biom = "grassland"
               tile.render_offset = pygame.Vector2(0, 0)

   def draw(self, screen):
      world_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
      for col in self.map_data:
         for tile in col:
            tile.draw(world_surface)
         
      # FOR DEBUGGING
      #self.draw_grid(world_surface)

      zoomed_size = (int(self.width * self.zoom_factor), int(self.height * self.zoom_factor))
      zoomed_surface = pygame.transform.scale(world_surface, zoomed_size)
      screen.blit(zoomed_surface, (-self.camera_offset.x, -self.camera_offset.y))

   def draw_grid(self, surface):
      grid_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
      rows = surface.get_height() // self.tile_size
      cols = surface.get_width() // self.tile_size

      for x in range(cols + 1):
         pygame.draw.line(grid_surface, (0, 0, 0, 100), (x * self.tile_size, 0), (x * self.tile_size, surface.get_height()), 1)
      for y in range(rows + 1):
         pygame.draw.line(grid_surface, (0, 0, 0, 100), (0, y * self.tile_size), (surface.get_width(), y * self.tile_size), 1)

      surface.blit(grid_surface, (0, 0))

   def zoom_at(self, mouse_pos, direction, viewport_width, viewport_height):
      old_zoom = self.zoom_factor
      zoom_change = 0.3 * direction
      new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom_factor + zoom_change))

      if new_zoom != old_zoom:
         mx, my = mouse_pos
         before_zoom = pygame.Vector2(mx, my) + self.camera_offset
         scale = new_zoom / old_zoom
         self.zoom_factor = new_zoom
         after_zoom = before_zoom * scale
         self.camera_offset = after_zoom - pygame.Vector2(mx, my)
         self.clamp_camera(viewport_width, viewport_height)

   def clamp_camera(self, screen_width, screen_height):
      zoomed_width = self.width * self.zoom_factor
      zoomed_height = self.height * self.zoom_factor
      max_x = max(0, zoomed_width - screen_width)
      max_y = max(0, zoomed_height - screen_height)
      self.camera_offset.x = max(0, min(self.camera_offset.x, max_x))
      self.camera_offset.y = max(0, min(self.camera_offset.y, max_y))

   def screen_to_tile_coords(self, mouse_pos: tuple) -> tuple | None:
      mx, my = mouse_pos
      world_x = (mx + self.camera_offset.x) / self.zoom_factor
      world_y = (my + self.camera_offset.y) / self.zoom_factor

      tile_x = int(world_x // self.tile_size)
      tile_y = int(world_y // self.tile_size)

      if 0 <= tile_x < self.cols and 0 <= tile_y < self.rows:
         return (tile_x, tile_y)
      return None

   def get_tile(self, mouse_pos: tuple):
      coords = self.screen_to_tile_coords(mouse_pos)
      if coords is not None:
         x, y = coords
         if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.map_data[x][y].to_dict()
      return None
   
   def get_tile_at(self, x: int, y: int):
      """Returns the Tile object at grid coordinate (x, y)."""
      if 0 <= x < self.cols and 0 <= y < self.rows:
         return self.map_data[x][y]
      return None

   def update_tile(self, cords:tuple, obstacle):
      tile = self.get_tile(cords)

      if obstacle:
         tile.obstacle = obstacle
         tile.walkable = True if obstacle is None else False

   def is_walkable(self, x, y):
      tile = self.get_tile_at(x, y)
      return tile.walkable if tile else False

   def save_map(self, filename="saved_map.json"):
      data = [[tile.to_dict() for tile in col] for col in self.map_data]
      with open(filename, 'w') as f:
         json.dump(data, f)

   def load_map(self, filename="saved_map.json"):
      with open(filename, 'r') as f:
         data = json.load(f)
      for x in range(self.cols):
         for y in range(self.rows):
            self.map_data[x][y] = Tile.from_dict(data[x][y])

   def debug_draw_obstacles(self, screen):
      """Visual debug - draw red dots on obstacle tiles"""
      for x in range(self.cols):
         for y in range(self.rows):
            tile = self.map_data[x][y]
            if tile.obstacle:
               center = (x * self.tile_size + self.tile_size//2, 
               y * self.tile_size + self.tile_size//2)
               pygame.draw.circle(screen, (255, 0, 0), center, 3)
   
   def paint_explored_tiles(self, screen, camera_offset, zoom):
      """Visual debug - change color of the explored tiles"""
      for x in range(self.cols):
         for y in range(self.rows):
            tile = self.map_data[x][y]
            if tile.explored:
               # world coordinates (center of tile)
               world_x = x * self.tile_size + self.tile_size // 2
               world_y = y * self.tile_size + self.tile_size // 2

               # apply camera offset + zoom
               screen_x = (world_x - camera_offset[0]) * zoom
               screen_y = (world_y - camera_offset[1]) * zoom

               # draw red dot (adjust radius to scale with zoom if needed)
               pygame.draw.circle(screen, (255, 0, 0), (int(screen_x), int(screen_y)), max(1, int(3 * zoom)))

   def tile_to_pixel(self, tilepos):
      tx, ty = tilepos
      return tx * self.tile_size, ty * self.tile_size