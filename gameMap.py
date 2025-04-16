import pygame
import random

class Tile:
   def __init__(self, x, y, size, surface=None, obstacle=None):
      self.x = x
      self.y = y
      self.size = size
      self.surface = surface  # image of the surface like tree rock etc
      self.obstacle = obstacle  # "tree", "rock", etc.
      self.walkable = None
      self.biom = "grassland"

   def draw(self, screen):
      if self.surface:
         screen.blit(self.surface, (self.x * self.size, self.y * self.size))

   def __repr__(self):
      return f"Tile(x={self.x}, y={self.y}, obs={self.obstacle}, surf={self.surface}, walkable={self.walkable}, biom={self.biom})"

class Map:
   def __init__(self, width, height):
      self.width = width
      self.height = height
      self.tile_size = 16

      self.zoom_factor = 1.0
      self.min_zoom = 1.0
      self.max_zoom = 2.5
      self.camera_offset = pygame.Vector2(0, 0)
   

      self.cols = self.width // self.tile_size
      self.rows = self.height // self.tile_size

      self.assets = Map.loadAssets() #Load assets
      self.map_data = [[Tile(x, y, self.tile_size) for y in range(self.rows)] for x in range(self.cols)]

      self.map_surface = None

   @staticmethod
   def loadAssets(dir="assets") -> dict:
      """
         Loads game assets from specified directory and categorizes them into:
         - topLvlAssets: Top-level game objects (e.g., trees, characters)
         - sounds: Audio files
         - background: Background images
         
         Files should be prefixed with:
         - 'top-' for top level assets
         - 'sound-' for audio files
         - 'bg-' for backgrounds
         - 'entity' for entities
         - 'obj' for objects

         Returns: Dictionary containing sorted asset lists
      """
      from pathlib import Path

      data = {
         "topLvlAssets": {"trees": [], "rocks": [], "water": []},
         "entities": {"hidder": [], "seeker": [], "animals": []},
         "sounds": {"walking": [], "backgroundMusic": [], "hit": []},
         "background": [],
         "objects": []
      }
      
      for f in Path(dir).iterdir():
         if not f.is_file() or "-" not in f.stem:
            continue
         
         category, subtype = f.stem.split("-", 1)

         key = {
            "top": "topLvlAssets",
            "sound": "sounds",
            "bg": "background",
            "entity": "entities",
            "obj": "objects"
         }.get(category)

         if not key:
            continue

         if key in ["background", "objects"]:
            # List-type categories
            asset = pygame.image.load(str(f)).convert_alpha()
            data[key].append(asset)

         elif key == "sounds":
            # Audio files
            if subtype in data[key]:
               data[key][subtype].append(str(f))

         else:
            # Dict-type image categories like topLvlAssets, entities
            asset = pygame.image.load(str(f)).convert_alpha()
            if subtype in data[key]:
               data[key][subtype].append(asset)
            else:
               data[key]["water" if key == "topLvlAssets" else "animals"].append(asset)

      return data

   def generate_obstacles(self, cluster_count=25, cluster_size_range=(10, 30)):
      tree_assets = self.assets["topLvlAssets"]["trees"]
      rock_assets = self.assets["topLvlAssets"]["rocks"]

      if not tree_assets and not rock_assets:
         return

      for _ in range(cluster_count):
         cluster_type = random.choices(["tree", "rock", "mixed"], weights=[0.7, 0.2, 0.1])[0]

         if cluster_type == "tree":
            cluster_asset = random.choice(tree_assets)
            obstacle_type = "tree"
            biom = "forest"
            
         elif cluster_type == "rock":
            cluster_asset = random.choice(rock_assets)
            obstacle_type = "rock"
            biom = "rocks"

         else:  #mixed
            cluster_asset = random.choice(tree_assets * 3 + rock_assets)
            obstacle_type = "tree" if cluster_asset in tree_assets else "rock"
            biom = "mixed"

         cx = random.randint(0, self.cols - 1)
         cy = random.randint(0, self.rows - 1)
         cluster_size = random.randint(*cluster_size_range)

         for _ in range(cluster_size):
            dx = random.randint(-2, 2)
            dy = random.randint(-2, 2)
            tx = cx + dx
            ty = cy + dy

            if 0 <= tx < self.cols and 0 <= ty < self.rows:
               tile = self.map_data[tx][ty]
               if tile.obstacle is None:
                  tile.surface = pygame.transform.scale(cluster_asset, (16, 16))
                  tile.obstacle = obstacle_type
                  tile.walkable = True if obstacle_type == "tree" else False
                  tile.biom = biom

                  tile.draw(self.map_surface)

   def generate_perlin_map(self, scale=7, octaves=2, persistence=0.3, lacunarity=1.6):
      """Map generator using tuned Perlin noise for more grass and forest."""

      from noise import pnoise2

      for x in range(self.cols):
        for y in range(self.rows):
            nx = x / self.cols * scale
            ny = y / self.rows * scale

            noise_val = pnoise2(nx, ny, 
                                 octaves=octaves, persistence=persistence, 
                                 lacunarity=lacunarity)

            # Normalize to 0-1
            noise_val = (noise_val + 1) / 2.0

            tile = self.map_data[x][y]

            if noise_val < 0.33:
               tile.obstacle = "water"
               tile.walkable = False
               tile.surface = random.choice(self.assets["topLvlAssets"]["water"])
               tile.biom = "lake"

            elif noise_val < 0.35:
               tile.obstacle = "rock"
               tile.walkable = False
               tile.surface = random.choice(self.assets["topLvlAssets"]["rocks"])
               tile.biom = "rocky"

            elif noise_val < 0.48:
               tile.obstacle = "trees"
               tile.walkable = True
               tile.surface = random.choice(self.assets["topLvlAssets"]["trees"])
               tile.biom = "forest"

            else:
               tile.obstacle = None  # Grassland
               tile.walkable = True
               tile.surface = None  # Or your grass tile

            if tile.surface:
               tile.surface = pygame.transform.scale(tile.surface, (16, 16))

            tile.draw(self.map_surface)

   def spawn_players(self):
      hidder = self.assets["entities"]["hidder"][0]
      seeker = self.assets["entities"]["seeker"][0]

      cord_hidder_x = random.randint(0, self.cols - 1)
      cord_hidder_y = random.randint(0, self.rows - 1)

      #place the agents
      tile = self.map_data[cord_hidder_x][cord_hidder_y]

      tile.surface = pygame.transform.scale(hidder, (16, 16))
      tile.obstacle = "player-hidder"
      tile.walkable = True

      tile.draw(self.map_surface)

      cord_seeker_x = random.randint(0, self.cols - 1)
      cord_seeker_y = random.randint(0, self.rows - 1)

      #place the agents
      tile = self.map_data[cord_seeker_x][cord_seeker_y]

      tile.surface = pygame.transform.scale(seeker, (16, 16))
      tile.obstacle = "player-seeker"
      tile.walkable = True

      tile.draw(self.map_surface)

   def mapGenerator(self):
      """
      Generates a random map by setting the background image from assets.
      Requires self.assets["background"] to contain a pre-loaded Surface.
      """
      self.map_surface = pygame.Surface((self.width, self.height))

      background = self.assets.get("background", [None])[0]

      if background:
         scaled_bg = pygame.transform.scale(background, (self.width, self.height))
         self.map_surface.blit(scaled_bg, (0, 0))

      else:
         self.map_surface.fill((255, 255, 255))

      # Obstacles in clusters
      self.generate_perlin_map()
      #self.spawn_players()
      #self.debug_draw_obstacles(self.map_surface)

      return self.map_surface

   def draw(self, screen):
      # Draw the map onto a world_surface
      world_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
      world_surface.blit(self.map_surface, (0, 0))  # draw background
      for col in self.map_data:
         for tile in col:
            tile.draw(world_surface)

      # Apply zoom
      zoomed_size = (int(self.width * self.zoom_factor), int(self.height * self.zoom_factor))
      zoomed_surface = pygame.transform.scale(world_surface, zoomed_size)

      # camera offset
      screen.blit(zoomed_surface, (-self.camera_offset.x, -self.camera_offset.y))

   def get_tile(self, mouse_poss: tuple):
      """Returns tile object at specific (x, y) grid position."""

      mx, my = mouse_poss

      world_x = (mx + self.camera_offset.x) / self.zoom_factor
      world_y = (my + self.camera_offset.y) / self.zoom_factor

      tile_x = int(world_x // self.tile_size)
      tile_y = int(world_y // self.tile_size)
      
      if 0 <= tile_x < self.cols and 0 <= tile_y < self.rows:
        return self.map_data[tile_x][tile_y]
      else:
         return None

   def update_tile(self, mouse_poss: tuple, new_tile):
      """Updates a tile with new content (tree/rock/None)."""

      mx, my = mouse_poss

      world_x = (mx + self.camera_offset.x) / self.zoom_factor
      world_y = (my + self.camera_offset.y) / self.zoom_factor

      tile_x = int(world_x // self.tile_size)
      tile_y = int(world_y // self.tile_size)

      if 0 <= tile_x < self.cols and 0 <= tile_y < self.rows:
         #update tile
         ...
      else:
         return None

   def is_walkable(self, position: tuple) -> bool:
      """Checks if the tile at position is walkable (not obstacle)."""

      mx, my = position

      world_x = (mx + self.camera_offset.x) / self.zoom_factor
      world_y = (my + self.camera_offset.y) / self.zoom_factor

      tile_x = int(world_x // self.tile_size)
      tile_y = int(world_y // self.tile_size)

      return (0 <= tile_x < self.cols) and (0 <= tile_y < self.rows) and self.map_data[tile_x][tile_y].walkable

   def reset_map(self):
      """ Resets the old map with generating a new map """

      self.map_data = [[Tile(x, y, self.tile_size) for y in range(self.rows)] for x in range(self.cols)]
      self.generate_obstacles()

   def zoom_at(self, mouse_pos, direction, viewport_width, viewport_height):
      """
      Zooms into the point under mouse_pos. Direction: +1 (in), -1 (out)
      """
      old_zoom = self.zoom_factor
      zoom_change = 0.1 * direction
      new_zoom = max(self.min_zoom, min(self.max_zoom, self.zoom_factor + zoom_change))

      if new_zoom != old_zoom:
         mx, my = mouse_pos
         before_zoom = pygame.Vector2(mx, my) + self.camera_offset
         scale = new_zoom / old_zoom
         self.zoom_factor = new_zoom
         after_zoom = before_zoom * scale
         self.camera_offset = after_zoom - pygame.Vector2(mx, my)

         # Clamp after zooming
         self.clamp_camera(viewport_width, viewport_height)

   def draw_grid(self, surface):
      """
      Draws a grid on the given surface with lines spaced at self.tile_size intervals.
      Fixed horizontal line drawing to extend full width.

      used for debugging!

      """

      grid_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)

      rows = surface.get_height() // self.tile_size
      cols = surface.get_width() // self.tile_size

      for x in range(cols + 1):
         pygame.draw.line(
               grid_surface,
               (0, 0, 0, 100),
               (x * self.tile_size, 0),
               (x * self.tile_size, surface.get_height()),
               1
         )

      for y in range(rows + 1):
         pygame.draw.line(
               grid_surface,
               (0, 0, 0, 100),
               (0, y * self.tile_size),
               (surface.get_width(), y * self.tile_size),
               1
         )

      surface.blit(grid_surface, (0, 0))

   def debug_draw_obstacles(self, screen):
      """Visual debug - draw red dots on obstacle tiles"""
      for x in range(self.cols):
         for y in range(self.rows):
            tile = self.map_data[x][y]
            if tile.obstacle:
               center = (x * self.tile_size + self.tile_size//2, 
                        y * self.tile_size + self.tile_size//2)
               pygame.draw.circle(screen, (255, 0, 0), center, 3)

   def clamp_camera(self, screen_width, screen_height):
      zoomed_width = self.width * self.zoom_factor
      zoomed_height = self.height * self.zoom_factor

      max_x = max(0, zoomed_width - screen_width)
      max_y = max(0, zoomed_height - screen_height)

      self.camera_offset.x = max(0, min(self.camera_offset.x, max_x))
      self.camera_offset.y = max(0, min(self.camera_offset.y, max_y))

   def save_map(self):
      ...

   def load_map(self):
      ...
