import pygame
import random
import time

# Constants
WIDTH, HEIGHT = 800, 800
ROWS, COLS = 40, 40  # Larger maze possible now
CELL_SIZE = WIDTH // COLS

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Initialize Pygame with acceleration
pygame.init()
win = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Optimized Maze Generator")

class Cell:
    __slots__ = ['row', 'col', 'visited', 'walls']  # Optimize memory usage
    
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.visited = False
        self.walls = {"top": True, "right": True, "bottom": True, "left": True}

    def draw(self, win):
        x = self.col * CELL_SIZE
        y = self.row * CELL_SIZE

        # Only draw walls if they exist (optimization)
        if self.walls["top"]:
            pygame.draw.line(win, BLACK, (x, y), (x + CELL_SIZE, y), 2)
        if self.walls["right"]:
            pygame.draw.line(win, BLACK, (x + CELL_SIZE, y), (x + CELL_SIZE, y + CELL_SIZE), 2)
        if self.walls["bottom"]:
            pygame.draw.line(win, BLACK, (x, y + CELL_SIZE), (x + CELL_SIZE, y + CELL_SIZE), 2)
        if self.walls["left"]:
            pygame.draw.line(win, BLACK, (x, y), (x, y + CELL_SIZE), 2)

    def get_neighbors(self, grid):
        neighbors = []
        
        # Check neighbors with short-circuit evaluation
        if self.row > 0 and not grid[self.row-1][self.col].visited:
            neighbors.append(("top", self.row-1, self.col))
        if self.col < COLS-1 and not grid[self.row][self.col+1].visited:
            neighbors.append(("right", self.row, self.col+1))
        if self.row < ROWS-1 and not grid[self.row+1][self.col].visited:
            neighbors.append(("bottom", self.row+1, self.col))
        if self.col > 0 and not grid[self.row][self.col-1].visited:
            neighbors.append(("left", self.row, self.col-1))
            
        return neighbors

def remove_walls(current, next_cell, direction):
    # Inline wall removal for speed
    if direction == "top":
        current.walls["top"] = next_cell.walls["bottom"] = False
    elif direction == "right":
        current.walls["right"] = next_cell.walls["left"] = False
    elif direction == "bottom":
        current.walls["bottom"] = next_cell.walls["top"] = False
    elif direction == "left":
        current.walls["left"] = next_cell.walls["right"] = False

def generate_maze():
    # Pre-allocate grid
    grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
    for row in range(ROWS):
        for col in range(COLS):
            grid[row][col] = Cell(row, col)
    
    stack = []
    current = grid[0][0]
    current.visited = True
    stack.append(current)

    # Create a surface for static elements
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill(WHITE)
    win.blit(background, (0, 0))
    pygame.display.flip()

    while stack:
        current = stack[-1]
        neighbors = current.get_neighbors(grid)

        if neighbors:
            direction, next_row, next_col = random.choice(neighbors)
            next_cell = grid[next_row][next_col]
            remove_walls(current, next_cell, direction)
            next_cell.visited = True
            stack.append(next_cell)
            
            # Only draw the changed cells
            current.draw(win)
            next_cell.draw(win)
            pygame.display.update(pygame.Rect(
                min(current.col, next_cell.col) * CELL_SIZE,
                min(current.row, next_cell.row) * CELL_SIZE,
                CELL_SIZE * 2, CELL_SIZE * 2
            ))
        else:
            stack.pop()

    return grid

def main():
    run = True
    clock = pygame.time.Clock()
    
    # Generate maze first without visualization
    start_time = time.time()
    grid = generate_maze()
    print(f"Maze generated in {time.time() - start_time:.2f} seconds")
    
    # Main loop just for display
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

        # Draw everything once
        win.fill(WHITE)
        for row in grid:
            for cell in row:
                cell.draw(win)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()