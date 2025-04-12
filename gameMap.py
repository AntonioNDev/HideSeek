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
      ...
            
   def draw(self, surface):
      surface.blit(self.map_surface, (0, 0))

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
      return (0 <= targetX <= self.width) and (0 <= targetY <= self.height) and position not in self.obstacles

   # Resets the old map with generating a new map
   def reset_map(self):
      self.map_data = self.generate_random_map()

   def draw_grid(self, surface):
      ...

   def save_map(self):
      ...

   def load_map(self):
      ...