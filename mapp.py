import numpy
import pygame

class Map:
   def __init__(self, width, height):
      self.width = width
      self.height = height

      self.map_data = None

      self.assets = self.loadAssets()
   
   def loadAssets(self) -> dict:
      ...
   def scaleImaes(self):
      ...
   def generate_random_map(self):
      ...
   def draw(self):
      ...
   def loadChunk(self):
      ...
   def get_tile(self, x, y):
      ...
   def update_tile(self, x, y, new_tile):
      ...
   def get_chunk(self, chunk_x, chunk_y):
      ...
   def is_walkable(self, x, y):
      ...
   def reset_map(self):
      ...
   def draw_grid(self, surface):
      ...
   def save_map(self):
      ...
   def load_map(self):
      ...