import pygame
import random
from map_generator import Map
from agents import Hider, Seeker

pygame.init()
pygame.font.init()
DEBUGING_FONT = pygame.font.SysFont(None, 18)

class Game():
   def __init__(self):
      self.width = 1280
      self.height = 640
      self.debug_mode = False

      flags = pygame.HWSURFACE | pygame.DOUBLEBUF
      self.screen = pygame.display.set_mode((self.width, self.height), flags)

      pygame.display.set_caption('Hide and Seek', icontitle='icon')

      self.gameMap = Map(self.width, self.height)

      self.gameMap.generate_map()
      self.hider, self.seeker = self.spawn_agents()

      self.camera_offset = self.gameMap.camera_offset
      self.zoom = self.gameMap.zoom_factor

      #let the hider hide
      self.hider.hide(self.seeker.get_tile_pos())
      self.seeker.search(self.hider.get_tile_pos())
   
   def spawn_agents(self):
      def get_spawn_tile():
         while True:
            x = random.randint(0, self.gameMap.cols - 1)
            y = random.randint(0, self.gameMap.rows - 1)
            tile = self.gameMap.map_data[x][y]

            if tile.walkable:
               return x, y
      
      #Try to load images for the seeker and the hider
      try:
         self.hider_img = pygame.image.load("assets/entity-army-archer1.png").convert_alpha()
         self.seeker_img = pygame.image.load("assets/entity-seeker-man1.png").convert_alpha()
      except Exception as e:
         raise RuntimeError(f"Failed to load one or more asset images: {e}")
      
      #Spawn the Hider
      hider_spawn = get_spawn_tile()

      #Spawn the Seeker far from the Hider
      seeker_spawn = get_spawn_tile()
      while abs(hider_spawn[0] - seeker_spawn[0]) + abs(hider_spawn[1] - seeker_spawn[1]) < 15:
         seeker_spawn = get_spawn_tile()
      
      hider_px = self.gameMap.tile_to_pixel(hider_spawn)
      seeker_px = self.gameMap.tile_to_pixel(seeker_spawn)

      hider = Hider(hider_px[0], hider_px[1], self.hider_img, self.gameMap)
      seeker = Seeker(seeker_px[0], seeker_px[1], self.seeker_img, self.gameMap)

      return hider, seeker

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
               f"Tile: {tile_pos}",
               f"WorldPos: ({int(agent.x)},{int(agent.y)})",
         ]

         if isinstance(agent, Seeker):
            lines.append(f"Vision: {getattr(agent, 'vision', 'N/A')}")
         elif isinstance(agent, Hider):
            lines.append(f"Caught: {getattr(agent, 'caught', False)}")

         for i, line in enumerate(lines):
            text = DEBUGING_FONT.render(line, True, (0, 0, 0))
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
         #Locked for 120 fps
         clock.tick(60)

         #Game events logic for drag and drop, quit and etc...
         for event in pygame.event.get():
            if event.type == pygame.QUIT:
               running = False
               break

            elif event.type == pygame.KEYDOWN:
               if event.key == pygame.K_d:
                  #On/Off the debbug mode
                  self.debug_mode = not self.debug_mode
            
            elif event.type == pygame.MOUSEWHEEL:
               mouse_pos = pygame.mouse.get_pos()
               self.gameMap.zoom_at(mouse_pos, event.y, self.width, self.height)

            elif event.type == pygame.MOUSEBUTTONDOWN:
               if event.button == 1:
                  dragging = True
                  last_mouse_poss = pygame.mouse.get_pos()
            
            elif event.type == pygame.MOUSEBUTTONUP:
               if event.button == 1:
                  dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
               if dragging:
                  mouse_pos = pygame.mouse.get_pos() 
                  dx = mouse_pos[0] - last_mouse_poss[0] 
                  dy = mouse_pos[1] - last_mouse_poss[1] 

                  self.gameMap.camera_offset -= pygame.Vector2(dx, dy) 
                  self.gameMap.clamp_camera(self.width, self.height) 
                  last_mouse_poss = mouse_pos
            
            elif event.type == pygame.MOUSEWHEEL:
               if dragging and last_mouse_poss is not None:
                  mouse_poss = pygame.mouse.get_pos()
                  dx, dy = mouse_poss[0]-last_mouse_poss[0], mouse_poss[1]-last_mouse_poss[1]

                  #update the camera offset
                  self.gameMap.camera_offset -= pygame.Vector2(dx, dy)
                  self.gameMap.clamp_camera(self.width, self.height)

                  last_mouse_poss = mouse_poss
         
         # Update the world
         self.screen.fill((255, 255, 255)) # White background for temporary
         self.gameMap.draw(self.screen)

         # Update the agents positions
         seeker_poss = self.seeker.get_tile_pos()
         hider_poss = self.hider.get_tile_pos()

         # Update the Hider
         self.hider.update()
         self.hider.hide(seeker_poss)

         # Update the Seeker
         self.seeker.update(hider_poss)
         self.seeker.search(hider_poss)

         # Draw agents on the map
         self.hider.draw(self.screen)
         self.seeker.draw(self.screen)

         # debugging mode
         if self.debug_mode:
            self.debugging([self.hider, self.seeker])

         pygame.display.flip()
      
      pygame.quit()

if __name__ == "__main__":
   instance = Game()
   instance.main()