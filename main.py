import pygame
from gameMap import Map
from agents import Hider, Seeker

pygame.init()

class Game():
   #initialize game
   def __init__(self):
      self.width = 1280
      self.height = 640

      self.screen = pygame.display.set_mode((self.width, self.height))

      #Set the title
      pygame.display.set_caption('Hide and Seek', icontitle='icon')

      self.gameMap = Map(self.width, self.height)
      self.map_surface = self.gameMap.mapGenerator()
      print(self.gameMap.loadAssets())

      #self.gameMap.draw_grid(self.map_surface)
   
   def mainLoop(self):
      running = True
      dragging = False
      last_mouse_pos = None

      while running:
         for event in pygame.event.get():
            if event.type == pygame.QUIT:
               running = False
               break

            elif event.type == pygame.MOUSEWHEEL:
               mouse_pos = pygame.mouse.get_pos()
               self.gameMap.zoom_at(mouse_pos, event.y, self.width, self.height)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
               if event.button == 1:
                     dragging = True
                     last_mouse_pos = pygame.mouse.get_pos()
                     
            elif event.type == pygame.MOUSEBUTTONUP:
               if event.button == 1:
                     dragging = False


            elif event.type == pygame.MOUSEMOTION:
               if dragging:
                  mouse_pos = pygame.mouse.get_pos()
                  dx = mouse_pos[0] - last_mouse_pos[0]
                  dy = mouse_pos[1] - last_mouse_pos[1]

                  self.gameMap.camera_offset -= pygame.Vector2(dx, dy)
                  self.gameMap.clamp_camera(self.width, self.height)

                  last_mouse_pos = mouse_pos
         
         self.screen.fill((255, 255, 255))
         self.gameMap.draw(self.screen)

         pygame.display.flip()

      pygame.quit()        

if __name__ == "__main__":
   instance = Game()
   instance.mainLoop()