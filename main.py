import pygame
from mapp import Map
from agents import Hider, Seeker

pygame.init()

class Game():
   #initialize game
   def __init__(self):
      self.screen = pygame.display.set_mode((1040, 640))

      #Set the title
      pygame.display.set_caption('Hide and Seek', icontitle='icon')
      
   
   def mainLoop(self):
      running = True

      while running:
         for event in pygame.event.get():
            if event.type == pygame.QUIT:
               running = False
               break
         
         self.screen.fill((0,0,0))

         pygame.display.flip()


      pygame.quit()

         

if __name__ == "__main__":
   instance = Game()
   instance.mainLoop()