import pygame
import random

from map_generator import Map
from agents import Villager, Seeker
from animals import Cow

pygame.init()
pygame.font.init()

DEBUGING_FONT = pygame.font.SysFont(None, 18)

class Game():
   def __init__(self):
      self.width = 1280
      self.height = 640
      self.debug_mode = False

      flags = pygame.HWSURFACE | pygame.DOUBLEBUF # If hardware acceleration is possible use it
      self.screen = pygame.display.set_mode((self.width, self.height), flags)
      pygame.display.set_caption('Hide&Seek')

      # WORLD
      self.gameMap = Map(self.width, self.height)
      self.gameMap.generate_map()

      self.camera_offset = self.gameMap.camera_offset
      self.zoom = self.gameMap.zoom_factor

   # Debugging info logic for the agents
   def debugging(self, agents):
      """Draw debug paths and info for all agents if debug mode is enabled."""
      if not self.debug_mode:
         return  # Skip entirely if debug mode is off

      tile_size = self.gameMap.tile_size
      zoom = self.gameMap.zoom_factor
      cam = self.gameMap.camera_offset

      offset_y = 10  # Where the first agent info block starts

      for agent in agents:
         # === 1. Draw path lines ===
         if getattr(agent, 'path', None):
            world_points = [(tx * tile_size, ty * tile_size) for tx, ty in agent.path]
            screen_points = [
               (int(x * zoom - cam.x), int(y * zoom - cam.y))
               for x, y in world_points
            ]
            if len(screen_points) > 1:
               pygame.draw.lines(self.screen, (0, 255, 0), False, screen_points, 2)

         # === 2. Draw debug text ===
         tile_pos = agent.get_tile_pos() if hasattr(agent, 'get_tile_pos') else ('N/A', 'N/A')
         lines = [
               f"Type: {'Seeker' if isinstance(agent, Seeker) else 'Hider'}",
               f"Mode: {getattr(agent, 'mode', 'N/A')}",
               f"Energy: {getattr(agent, 'energy', 0):.2f}",
               f"Speed: {getattr(agent, 'speed', 0):.2f}",
               f"Hunger: {getattr(agent, 'hunger', 0):.2f}",
               f"Tile: {tile_pos}",
               f"WorldPos: ({int(agent.x)},{int(agent.y)})",
         ]

         if isinstance(agent, Seeker):
            lines.append(f"Vision: {getattr(agent, 'vision', 'N/A')}")
         elif isinstance(agent, Villager):
            lines.append(f"Caught: {getattr(agent, 'caught', False)}")

         for i, line in enumerate(lines):
            text = DEBUGING_FONT.render(line, True, (0,0,0), (255,255,255))
            self.screen.blit(text, (10, offset_y + i * 16))

         offset_y += len(lines) * 16 + 10  # Space before next agent’s block

   # The main game loop
   def main(self):
      running = True
      dragging = False
      last_mouse_poss = None

      #fps in the game
      clock = pygame.time.Clock()

      while running:
         #Locked for 60 fps
         clock.tick(60)

         #Game events logic for drag and drop, quit and etc...
         for event in pygame.event.get():
            if event.type == pygame.QUIT:
               running = False

            elif event.type == pygame.KEYDOWN:
               if event.key == pygame.K_d:
                  #On/Off the debbug mode
                  self.debug_mode = not self.debug_mode
            
            elif event.type == pygame.MOUSEWHEEL:
               mouse_pos = pygame.mouse.get_pos()

               # Zoom
               self.gameMap.zoom_at(mouse_pos, event.y, self.width, self.height)

            elif event.type == pygame.MOUSEBUTTONDOWN:
               if event.button == 1:
                  dragging = True
                  last_mouse_poss = pygame.mouse.get_pos()
                  print(self.gameMap.get_tile(last_mouse_poss))
            
            elif event.type == pygame.MOUSEBUTTONUP:
               if event.button == 1:
                  dragging = False
            
            elif event.type == pygame.MOUSEMOTION and dragging:
               mouse_pos = pygame.mouse.get_pos() 
               dx = mouse_pos[0] - last_mouse_poss[0] 
               dy = mouse_pos[1] - last_mouse_poss[1] 

               self.gameMap.camera_offset -= pygame.Vector2(dx, dy) 
               self.gameMap.clamp_camera(self.width, self.height) 
               
               last_mouse_poss = mouse_pos

                  
         # -------------------------
         # UPDATE WORLD
         # -------------------------
         #self.update_entities()

         # -------------------------
         # RENDER WORLD
         # -------------------------
         self.screen.fill((255, 255, 255))
         self.gameMap.draw(self.screen)

         #self.draw_entities()

         # -------------------------
         # DEBUG
         # -------------------------
         if self.debug_mode:
            self.gameMap.paint_explored_tiles(self.screen, self.camera_offset, self.zoom)

         pygame.display.flip()
      
      pygame.quit()

if __name__ == "__main__":
   instance = Game()
   instance.main()