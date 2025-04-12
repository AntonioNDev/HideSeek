import pygame

class Map:
   def __init__(self, width, height):
      self.width = width
      self.height = height

      self.map_data = []

      self.assets = Map.loadAssets()
      self.obstacles = []

   # Takes assets from the assets folder and stores them into a dictrionary
   # and returns them so further use into the Map generation process
   @staticmethod
   def loadAssets(dir="assets") -> dict:
      from pathlib import Path

      data = {"groundLvlAssets": [], "topLvlAssets": [], "sounds": []}
      for f in Path(dir).iterdir():
         if f.is_file():
            key = {
               "base": "groundLvlAssets",
               "top": "topLvlAssets",
               "sound": "sounds"
            }.get(f.stem.split("-")[0], "")
            if key != "sounds":
               image = pygame.image.load(str(f)).convert_alpha()
               data[key].append(image)
            else:
               data[key].append(str(f))

      return data

   # Takes image, new_width, new_height and returns new 
   # scaled image while maintaining the aspect ratio
   @staticmethod
   def scaleImage(image, new_width, new_height):
      
      #calculate the new scale ratio while preserving aspect ratio
      ratio = min(new_width / image.get_width(), new_height / image.get_height())
      new_size = (int(image.get_width() * ratio), int(image.get_height() * ratio))

      return pygame.transform.smoothscale(image, new_size)

   def generate_map(self):
      """
         Generates the base map layer by randomly selecting ground-level tiles.
         Stores the resulting surface in self.map_surface.

      """

      import random

      TILE_SIZE = 16

      self.map_data = [
         [random.choice(self.assets["groundLvlAssets"])
          for _ in range(self.width)]
         for _ in range(self.height)
      ]

      self.map_surface = pygame.Surface(
         (self.width * TILE_SIZE, self.height * TILE_SIZE)
      )

      for y in range(self.height):
         for x in range(self.width):
               tile_image = self.map_data[y][x]
               tile_pos = (x * TILE_SIZE, y * TILE_SIZE)
               self.map_surface.blit(tile_image, tile_pos)
      
      self.draw_grid(self.map_surface)
      
   def draw(self):
      ...

   def loadChunk(self):
      ...

   # Returns a tile (cell) that's on (x, y) cords
   def get_tile(self, x:int, y:int):
      return self.map_data[x][y]

   # Updates a tile (cell) changes it's value eg: from tree to rock
   def update_tile(self, x: int, y: int, new_tile):
      self.map_data[x][y] = new_tile

   def get_chunk(self, chunk_x, chunk_y):
      ...

   # Checks if the agent position is not outside of the board and also is not in
   # the obstacles
   def is_walkable(self, position: tuple) -> bool:
      targetX, targetY = position
      return (0 <= targetX <= self.width) and (0 <= targetX <= self.height) and position not in self.obstacles

   # Resets the old map with generating a new map
   def reset_map(self):
      self.map_data = self.generate_random_map()

   def draw_grid(self, surface):
      """
         Draws a debugging grid overlay on the given surface.
         - Grid lines are thin and black
         - Background is transparent (doesn't overwrite existing content)
         - Grid size adapts to self.map_data dimensions
      """
      # Temporary surface 
      grid_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

      # Map dimensions
      rows = len(self.map_data)
      cols = len(self.map_data[0]) if rows > 0 else 0

      # Calculate cell size based on surface dimensions
      cell_width = surface.get_width() // cols
      cell_height = surface.get_height() // rows

      # Draw vertical lines
      for x in range(0, surface.get_width(), cell_width):
         pygame.draw.line(
            grid_surface,
            (0, 0, 0, 225),
            (x, 0),
            (x, surface.get_height()),
            1
         )
      
      # Draw horizontal lines
      for y in range(0, surface.get_height(), cell_height):
         pygame.draw.line(
            grid_surface,
            (0, 0, 0, 225),
            (y, 0),
            (surface.get_width(), y),
            1
         )

      surface.blit(grid_surface, (0, 0))

   def save_map(self):
      ...

   def load_map(self):
      ...