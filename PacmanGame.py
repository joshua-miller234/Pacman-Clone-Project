import copy
import math
from queue import PriorityQueue
import pygame
import Levels


class Pacman:
    """Template for a pacman object (the player). Contains member variables for tracking position and state, and
    functions for determining valid paths, and moving and drawing pacman on the screen"""

    def __init__(self):
        # 'actual' is the top-left corner of the cell pacman is considered to be (despite visual appearance)
        self.actual_x = (750 // 30) * 15
        self.actual_y = ((875 - 50) // 33) * 24
        # pacman coordinate points (in pixels)
        # Top left corner of where pacman is rendered (not necessarily the cell center of pacman is in)
        self.visual_x = self.actual_x - 10
        self.visual_y = self.actual_y - 10
        # Center is the center-most point of pacman
        self.center_x = self.actual_x + 13
        self.center_y = self.actual_y + 13
        # count of lives left
        self.lives = 3
        # direction variables, used to track which direction pacman is currently facing,
        # valid directions that can be faced, and current direction being input by the user
        # directions = [right, left, up, down]
        #                0       1   2    3
        self.direction = 0
        self.valid_directions = [False, False, False, False]
        self.direction_command = 0
        # power up controls
        self.eaten_ghosts = 0

    # Displays the player/pacman, different rotation of image based on the direction moving
    def draw(self, settings):
        # direction = [right, left, up, down]
        if self.direction == 0:
            settings.screen.blit(player_images[(settings.counter % 20) // 5],
                                 (self.visual_x, self.visual_y))
        if self.direction == 1:
            settings.screen.blit(pygame.transform.flip(player_images[(settings.counter % 20) // 5], True, False),
                                 (self.visual_x, self.visual_y))
        if self.direction == 2:
            settings.screen.blit(pygame.transform.rotate(player_images[(settings.counter % 20) // 5], 90),
                                 (self.visual_x, self.visual_y))
        if self.direction == 3:
            settings.screen.blit(pygame.transform.rotate(player_images[(settings.counter % 20) // 5], 270),
                                 (self.visual_x, self.visual_y))

    # updates which adjacent cells are currently valid for pacman to move to based on his location on the grid
    def update_valid_directions(self, settings):
        # directions = [right, left, up, down]
        valid_directions = [False, False, False, False]
        i = self.actual_y // 25
        j = self.actual_x // 25

        # if out of bounds, player can only move right and left
        # otherwise check surrounding tiles to determine valid paths
        if j < 1 or j > 28:
            valid_directions[0] = True
            valid_directions[1] = True
        else:
            # if grid square below current position isn't a wall and pacman is properly aligned - moving down is ok
            if settings.level[i + 1][j] < 3 and self.actual_x % 25 == 0:
                valid_directions[3] = True

            # if grid above current position isn't a wall and pacman is properly aligned - moving up is ok
            # else handles case where above cell is a wall, but pacman still has space in his own square to move closer
            # or rather, there is a wall in the next cell up but pacman isn't touching the top of his current cell
            if settings.level[i - 1][j] < 3 and self.actual_x % 25 == 0:
                valid_directions[2] = True
            else:
                if self.direction == 2 and self.actual_y > (i * 25):
                    valid_directions[2] = True

            # if cell to the right of the current position isn't a wall and pacman is properly aligned,
            # then moving right is ok
            if settings.level[i][j + 1] < 3 and self.actual_y % 25 == 0:
                valid_directions[0] = True

            # if cell to the left of the current position isn't a wall and pacman is properly aligned,
            # then moving left is ok
            # else handles case where left cell is a wall, but pacman still has space in his own square to move close
            if settings.level[i][j - 1] < 3 and self.actual_y % 25 == 0:
                valid_directions[1] = True
            else:
                if self.direction == 1 and (self.actual_x > (j * 25)):
                    valid_directions[1] = True

        return valid_directions

    # moves pacman if moving forward in the direction pacman is facing is valid (not a wall)
    def move_player(self):
        # direction = [right, left, up, down]
        if self.direction == 0 and self.valid_directions[0]:
            self.visual_x += 1
            self.center_x += 1
            self.actual_x += 1
        elif self.direction == 1 and self.valid_directions[1]:
            self.visual_x -= 1
            self.center_x -= 1
            self.actual_x -= 1
        elif self.direction == 2 and self.valid_directions[2]:
            self.visual_y -= 1
            self.center_y -= 1
            self.actual_y -= 1
        elif self.direction == 3 and self.valid_directions[3]:
            self.visual_y += 1
            self.center_y += 1
            self.actual_y += 1


class Ghost:
    """Template for a ghost object (blinky, inky, pinky, and clyde). Contains member variables for tracking position
    and state, and functions for determining valid paths / pathfinding. It is intended for blinky, inky, and pinky to
    use the A* algorithm with different heuristic options, while clyde has his own (suboptimal) greedy pathfinding
    algorithm - Intention is to demonstrate the effectiveness/differences in different pathfinding algorithms
    behavior"""

    def __init__(self, x_visual, y_visual, x_actual, y_actual, x_center, y_center,
                 target, speed, img, dead, been_eaten, settings):
        self.x_visual = x_visual
        self.y_visual = y_visual
        self.x_actual = x_actual
        self.y_actual = y_actual
        self.x_center = x_center
        self.y_center = y_center
        self.target = target
        self.speed = speed
        self.img = img
        self.dead = dead
        self.been_eaten = been_eaten
        self.valid_directions = [False, False, False, False]
        self.path = None
        self.settings = settings

    def draw(self):
        if (not self.settings.power_up and not self.dead) or (
                self.been_eaten and self.settings.power_up and not self.dead):
            self.settings.screen.blit(self.img, (self.x_visual, self.y_visual))
        elif self.settings.power_up and not self.dead and not self.been_eaten:
            self.settings.screen.blit(spooked_img, (self.x_visual, self.y_visual))
        else:
            self.settings.screen.blit(dead_img, (self.x_visual, self.y_visual))

    # Calculates a list of path (x,y) values using A* algorithm. There is an option between two heuristics that can be
    # used. 'use_heuristic_one' is a boolean to choose which to use.
    def a_star_algorithm(self, use_heuristic_one):
        start = (self.x_center // 25, self.y_center // 25)
        goal = (self.target[0] // 25, self.target[1] // 25)
        frontier = PriorityQueue()
        frontier.put((0, start))
        came_from = dict()
        cost_so_far = dict()
        came_from[start] = None
        cost_so_far[start] = 0

        while not frontier.empty():
            current = frontier.get()
            if current == goal:
                break

            for next_tile in self.find_neighbors(current):
                new_cost = cost_so_far[(current[1])] + 1
                if next_tile not in cost_so_far or new_cost < cost_so_far[next_tile]:
                    cost_so_far[next_tile] = new_cost
                    priority = new_cost + self.heuristic(goal, next_tile, use_heuristic_one)
                    frontier.put((priority, next_tile))
                    came_from[next_tile] = current[1]

        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from[current]
        path.reverse()

        self.path = path

    # Returns result of one of two heuristics, first is distance formula from current position to target (diagonally)
    # second is Manhattan distance - (vertical distance difference + horizontal distance difference)
    def heuristic(self, a, b, use_heuristic_one):
        if use_heuristic_one:
            return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2).__round__()
        else:
            return abs(a[0] - b[0]) + abs(a[1] - b[1])

    # knowing the valid possible directions, creates a list of adjacent tiles that are traversable
    def find_neighbors(self, current):
        # directions = [right, left, up, down]
        self.update_valid_directions_astar(current[1][0], current[1][1])
        neighbors = []
        for i, neighbor in enumerate(self.valid_directions):
            if neighbor:
                if i == 0:
                    neighbors.append((current[1][0] + 1, current[1][1]))
                elif i == 1:
                    neighbors.append((current[1][0] - 1, current[1][1]))
                elif i == 2:
                    neighbors.append((current[1][0], current[1][1] - 1))
                elif i == 3:
                    neighbors.append((current[1][0], current[1][1] + 1))

        return neighbors

    # given a current tile, determines which adjacent tiles are valid/traversable
    def update_valid_directions_astar(self, actual_x, actual_y):
        # directions = [right, left, up, down]
        valid_directions = [False, False, False, False]
        i = actual_y
        j = actual_x

        if j < 1 or j > 28:
            pass
        else:
            if self.settings.level[i + 1][j] < 4:
                valid_directions[3] = True
            if self.settings.level[i - 1][j] < 4:
                valid_directions[2] = True
            if self.settings.level[i][j + 1] < 4:
                valid_directions[0] = True
            if self.settings.level[i][j - 1] < 4:
                valid_directions[1] = True

        self.valid_directions = valid_directions

    # Move ghosts position on board based on A* path
    def a_star_move(self):
        # direction = [right, left, up, down]
        if len(self.path) == 0:
            return
        if self.path[0][0] * 25 + 13 > self.x_center:
            self.x_visual += 1
            self.x_center += 1
            self.x_actual += 1
        elif self.path[0][0] * 25 + 13 < self.x_center:
            self.x_visual -= 1
            self.x_center -= 1
            self.x_actual -= 1
        elif self.path[0][1] * 25 + 13 < self.y_center:
            self.y_visual -= 1
            self.y_center -= 1
            self.y_actual -= 1
        elif self.path[0][1] * 25 + 13 > self.y_center:
            self.y_visual += 1
            self.y_center += 1
            self.y_actual += 1

    def move_clyde(self):
        if self.target[1] < self.y_center and self.valid_directions[2]:
            self.y_center -= 1
            self.y_visual -= 1
            self.y_actual -= 1
        elif self.target[0] > self.x_center and self.valid_directions[0]:
            self.x_center += 1
            self.x_visual += 1
            self.x_actual += 1
        elif self.target[0] < self.x_center and self.valid_directions[1]:
            self.x_center -= 1
            self.x_visual -= 1
            self.x_actual -= 1
        elif self.target[1] > self.y_center and self.valid_directions[3]:
            self.y_center += 1
            self.y_visual += 1
            self.y_actual += 1

    # determines valid directions similar to the player, only used for clyde
    def update_valid_clyde_directions(self):
        # directions = [right, left, up, down]
        valid_directions = [False, False, False, False]
        i = self.y_actual // 25
        j = self.x_actual // 25

        # if out of bounds, can only move right and left - otherwise check surrounding tiles to determine valid paths
        if j < 1 or j > 28:
            valid_directions[0] = True
            valid_directions[1] = True
        else:
            # if grid square below current position isn't a wall and properly aligned - moving down is ok
            if self.settings.level[i + 1][j] < 4 and (0 <= self.x_actual % 25 <= 0):
                valid_directions[3] = True

            # if grid above current position isn't a wall and properly aligned - moving up is ok
            # else handles case where above cell is a wall, but there is space to move closer
            if self.settings.level[i - 1][j] < 4 and (0 <= self.x_actual % 25 <= 0):
                valid_directions[2] = True
            else:
                if self.y_actual > (i * 25):
                    valid_directions[2] = True

            # if cell to the right of the current position isn't a wall and properly aligned - moving right is ok
            if self.settings.level[i][j + 1] < 4 and (0 <= self.y_actual % 25 <= 0):
                valid_directions[0] = True

            # if cell to the left of the current position isn't a wall and properly aligned - moving left is ok
            # else handles case where left cell is a wall, but there is space to move closer
            if self.settings.level[i][j - 1] < 4 and (0 <= self.y_actual % 25 <= 0):
                valid_directions[1] = True
            else:
                if self.x_actual > (j * 25):
                    valid_directions[1] = True

            self.valid_directions = valid_directions


class GameSettings:
    """Wrapper class for misc config options and game settings"""

    def __init__(self):
        # Height and width of game window
        self.width = 750
        self.height = 875
        # fps should be multiple of 20
        self.fps = 60
        # Pygame Settings
        self.channel = pygame.mixer.find_channel()
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font("freesansbold.ttf", 20)
        # Level / Board settings
        self.level_id = 0
        self.level = copy.deepcopy(Levels.level_layouts[0])
        self.level_color = Levels.level_colors[0]
        self.line_width = 3
        # movement speed settings - player speed should be at least 2
        self.player_speed = 4
        self.ghost_speed = self.player_speed - 1
        # Power-up settings
        self.power_up_duration = 8
        self.power_counter = 0
        self.power_up = False
        self.score = 0
        # Triggers for game state
        self.game_lost = False
        self.game_won = False
        # Number of dots left on map that need to be eaten
        self.dots_left = 0
        for row in self.level:
            for index in row:
                if index == 1 or index == 2:
                    self.dots_left += 1
        # Counters used to toggle events based on FPS, such as the pause at the start of game while intro sound plays
        self.counter = 0
        self.startup_counter = 0


# Initialize pygame module
pygame.init()

# Game Assets
# Loading entity images
player_images = []
for g in range(1, 5):
    player_images.append(pygame.transform.scale(pygame.image.load(f"assets/player_images/{g}.png"), (45, 45)))
blinky_img = pygame.transform.scale(pygame.image.load(f"assets/ghost_images/blinky.png"), (45, 45))
pinky_img = pygame.transform.scale(pygame.image.load(f"assets/ghost_images/pinky.png"), (45, 45))
inky_img = pygame.transform.scale(pygame.image.load(f"assets/ghost_images/inky.png"), (45, 45))
clyde_img = pygame.transform.scale(pygame.image.load(f"assets/ghost_images/clyde.png"), (45, 45))
spooked_img = pygame.transform.scale(pygame.image.load(f"assets/ghost_images/scared.png"), (45, 45))
dead_img = pygame.transform.scale(pygame.image.load(f"assets/ghost_images/dead.png"), (45, 45))

# Sounds
beginning_intro = "./assets/Sounds/pacman_beginning.wav"
intermission_sound = "./assets/Sounds/pacman_intermission.wav"
pacman_chomp = "./assets/Sounds/pacman_chomp.mp3"
pacman_death = "./assets/Sounds/pacman_death.wav"
eat_ghost_sound = "./assets/Sounds/pacman_eatghost.wav"
power_pellet_sound = "./assets/Sounds/power_pellet_eaten.wav"
power_up_active_sound = "./assets/Sounds/ghosts_ambient_scared2.wav"


# Sets ghosts back to default settings / positions
def reset_ghosts(blinky, inky, pinky, clyde, settings):
    blinky.x_visual = (settings.width // 30) * 14 - 10
    blinky.y_visual = ((settings.height - 50) // 33) * 12 - 10
    blinky.x_actual = (settings.width // 30) * 14
    blinky.y_actual = ((settings.height - 50) // 33) * 12
    blinky.x_center = (settings.width // 30) * 14 + 13
    blinky.y_center = ((settings.height - 50) // 33) * 12 + 13
    blinky.speed = settings.ghost_speed
    blinky.dead = False
    blinky.been_eaten = False

    inky.x_visual = (settings.width // 30) * 12 - 10
    inky.y_visual = ((settings.height - 50) // 33) * 15 - 10
    inky.x_actual = (settings.width // 30) * 12
    inky.y_actual = ((settings.height - 50) // 33) * 15
    inky.x_center = (settings.width // 30) * 12 + 13
    inky.y_center = ((settings.height - 50) // 33) * 15 + 13
    inky.speed = settings.ghost_speed
    inky.dead = False
    inky.been_eaten = False

    pinky.x_visual = (settings.width // 30) * 14 - 10
    pinky.y_visual = ((settings.height - 50) // 33) * 15 - 10
    pinky.x_actual = (settings.width // 30) * 14
    pinky.y_actual = ((settings.height - 50) // 33) * 15
    pinky.x_center = (settings.width // 30) * 14 + 13
    pinky.y_center = ((settings.height - 50) // 33) * 15 + 13
    pinky.speed = settings.ghost_speed
    pinky.dead = False
    pinky.been_eaten = False

    clyde.x_visual = (settings.width // 30) * 16 - 10
    clyde.y_visual = ((settings.height - 50) // 33) * 15 - 10
    clyde.x_actual = (settings.width // 30) * 16
    clyde.y_actual = ((settings.height - 50) // 33) * 15
    clyde.x_center = (settings.width // 30) * 16 + 13
    clyde.y_center = ((settings.height - 50) // 33) * 15 + 13
    clyde.speed = settings.ghost_speed
    clyde.dead = False
    clyde.been_eaten = False


# Main game loop
def main():
    # Initialize game settings
    settings = GameSettings()

    # Initialize player
    player = Pacman()

    # initialize ghosts
    blinky = Ghost((settings.width // 30) * 14 - 10, ((settings.height - 50) // 33) * 12 - 10,
                   (settings.width // 30) * 14, ((settings.height - 50) // 33) * 12, (settings.width // 30) * 14 + 13,
                   ((settings.height - 50) // 33) * 12 + 13, (player.center_x, player.center_y),
                   settings.ghost_speed, blinky_img, False, False, settings)

    inky = Ghost((settings.width // 30) * 12 - 10, ((settings.height - 50) // 33) * 15 - 10,
                 (settings.width // 30) * 12, ((settings.height - 50) // 33) * 15, (settings.width // 30) * 12 + 13,
                 ((settings.height - 50) // 33) * 15 + 13, (player.center_x, player.center_y),
                 settings.ghost_speed, inky_img, False, False, settings)

    pinky = Ghost((settings.width // 30) * 14 - 10, ((settings.height - 50) // 33) * 15 - 10,
                  (settings.width // 30) * 14, ((settings.height - 50) // 33) * 15, (settings.width // 30) * 14 + 13,
                  ((settings.height - 50) // 33) * 15 + 13, (player.center_x, player.center_y),
                  settings.ghost_speed, pinky_img, False, False, settings)

    clyde = Ghost((settings.width // 30) * 16 - 10, ((settings.height - 50) // 33) * 15 - 10,
                  (settings.width // 30) * 16, ((settings.height - 50) // 33) * 15, (settings.width // 30) * 16 + 13,
                  ((settings.height - 50) // 33) * 15 + 13, (player.center_x, player.center_y),
                  settings.ghost_speed, clyde_img, False, False, settings)

    running = True
    pygame.mixer.Sound(beginning_intro).play()

    while running:

        # player controls - wasd or arrow keys - should function like joystick controls
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    player.direction_command = 0
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    player.direction_command = 1
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    player.direction_command = 2
                if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    player.direction_command = 3
                if event.key == pygame.K_RETURN:
                    # Loading next level on game win/loss
                    if settings.game_lost:
                        settings.level_id = -1
                        player.lives = 3
                        settings.score = 0
                        load_next_level(player, blinky, inky, pinky, clyde, settings)
                    elif settings.game_won:
                        if settings.level_id >= len(Levels.level_layouts) - 1:
                            settings.level_id = -1
                            load_next_level(player, blinky, inky, pinky, clyde, settings)
                        else:
                            load_next_level(player, blinky, inky, pinky, clyde, settings)
            if event.type == pygame.KEYUP:
                if (event.key == pygame.K_RIGHT or event.key == pygame.K_d) and player.direction_command == 0:
                    player.direction_command = player.direction
                if (event.key == pygame.K_LEFT or event.key == pygame.K_a) and player.direction_command == 1:
                    player.direction_command = player.direction
                if (event.key == pygame.K_UP or event.key == pygame.K_w) and player.direction_command == 2:
                    player.direction_command = player.direction
                if (event.key == pygame.K_DOWN or event.key == pygame.K_s) and player.direction_command == 3:
                    player.direction_command = player.direction

        settings.clock.tick(settings.fps)

        # moving player to other side when they go off-screen through the side hallways
        if player.visual_x > settings.width:
            player.visual_x = -47
            player.actual_x = player.visual_x + 10
            player.center_x = player.visual_x + 23
        elif player.visual_x < -50:
            player.visual_x = settings.width - 3
            player.actual_x = player.visual_x + 10
            player.center_x = player.visual_x + 23

        # start-up pause timer for beginning/end of the game
        if settings.startup_counter < settings.fps * 5 and not settings.game_lost and not settings.game_won:
            beginning_of_game = True
            settings.startup_counter += 1
        elif settings.game_lost or settings.game_won:
            beginning_of_game = True
        else:
            beginning_of_game = False

        # counter for animations / flicker
        if settings.counter < settings.fps:
            settings.counter += 1
        else:
            settings.counter = 0

        # timer for when a powerup is picked up - else-if resets settings when power-up ends
        if settings.power_up and settings.power_counter < settings.fps * settings.power_up_duration:
            settings.power_counter += 1
        elif settings.power_up and settings.power_counter >= settings.fps * settings.power_up_duration:
            settings.power_counter = 0
            settings.power_up = False
            player.eaten_ghosts = 0
            blinky.been_eaten = False
            inky.been_eaten = False
            pinky.been_eaten = False
            clyde.been_eaten = False
            blinky.speed = settings.ghost_speed
            inky.speed = settings.ghost_speed
            pinky.speed = settings.ghost_speed
            clyde.speed = settings.ghost_speed

        # Drawing game objects onto the screen
        settings.screen.fill("black")
        draw_level(settings)
        player.draw(settings)
        blinky.draw()
        inky.draw()
        pinky.draw()
        clyde.draw()
        draw_misc(player, settings)

        # Player movement
        if not beginning_of_game:
            # Move the player once for each count of player speed
            for j in range(settings.player_speed):
                # Check what directions pacman is able to move too (which adjacent tiles are not walls)
                player.valid_directions = player.update_valid_directions(settings)

                # Check if the users movement input matches a valid direction - if so adjust Pacman's visual direction
                for i in range(4):
                    if player.direction_command == i and player.valid_directions[i]:
                        player.direction = i

                # if not special case of game won/lost, move the player and check resulting collisions
                if not settings.game_lost and not settings.game_won:
                    player.move_player()
                    check_collisions(player, blinky, inky, pinky, clyde, settings)

        # Ghost movement
        # update ghost targets
        update_ghost_targets(player, blinky, inky, pinky, clyde, settings)

        if not beginning_of_game:
            # Move blinky once per value of his current speed
            for j in range(blinky.speed):
                # if blinky changing directions is possible (he is in the middle of a tile)
                # and player is not out of bounds (using the hallways) - update blinky's path to pacman
                # using A* algorithm with heuristic 1
                if blinky.y_center % 25 == 13 and blinky.x_center % 25 == 13 and (0 <= player.center_x // 25 < 30):
                    blinky.a_star_algorithm(True)
                blinky.a_star_move()

            # Using heuristic 2 for inky and pinky, repeating pathfinding logic for inky and pinky
            for j in range(inky.speed):
                if inky.y_center % 25 == 13 and inky.x_center % 25 == 13 and (0 <= player.center_x // 25 < 30):
                    inky.a_star_algorithm(False)
                inky.a_star_move()
            for j in range(pinky.speed):
                if pinky.y_center % 25 == 13 and pinky.x_center % 25 == 13 and (0 <= player.center_x // 25 < 30):
                    pinky.a_star_algorithm(False)
                pinky.a_star_move()

            # Repeat for clyde with his own pathfinding - he simply attempts to increase/decrease his
            # position relative to pacman, if his x-coord is lower, then increase by 1, if higher than decrease etc.
            # Clyde uses his normal (poor) pathfinding unless he's been eaten and needs to return to the ghost box
            # Clyde uses A* to return to box (heuristic 2), otherwise he would probably never make it to the box
            for j in range(clyde.speed):
                if not clyde.dead:
                    clyde.update_valid_clyde_directions()
                    clyde.move_clyde()
                else:
                    clyde.a_star_algorithm(False)
                    clyde.a_star_move()

        # display everything onto screen
        pygame.display.flip()


# resets the game board to the next appropriate level on a game win/loss
def load_next_level(player, blinky, inky, pinky, clyde, settings):
    # reset stage
    settings.level_id += 1
    settings.level = copy.deepcopy(Levels.level_layouts[settings.level_id])
    settings.level_color = Levels.level_colors[settings.level_id]

    settings.dots_left = 0
    for r in settings.level:
        for i in r:
            if i == 1 or i == 2:
                settings.dots_left += 1

    # play intro or intermission sound
    if settings.game_lost:
        pygame.mixer.Sound(beginning_intro).play()
    else:
        pygame.mixer.Sound(intermission_sound).play()

    # Reset game won/lost
    settings.game_lost = False
    settings.game_won = False

    # Reset Player
    player.actual_x = (settings.width // 30) * 15
    player.actual_y = ((settings.height - 50) // 33) * 24
    player.visual_x = player.actual_x - 10
    player.visual_y = player.actual_y - 10
    player.center_x = player.actual_x + 13
    player.center_y = player.actual_y + 13
    player.direction = 0
    settings.power_up = False
    settings.power_counter = settings.fps * settings.power_up_duration
    settings.startup_counter = 0

    # Reset Ghosts
    reset_ghosts(blinky, inky, pinky, clyde, settings)


# Updates the ghosts targeting, whether they should be targeting pacman, the ghost box, fleeing to a corner, etc.
def update_ghost_targets(player, blinky, inky, pinky, clyde, settings):
    # Blinky always targets the player - (A* , heuristic 1)
    blinky.target = (player.center_x, player.center_y)

    # inky attempts to target in-between blinky and pacman (A* , heuristic 2),
    # but if that targets something unreachable, such as a wall tile, target defaults to pacman
    if ((blinky.x_center + player.center_x) // 2 // 25 > 28 or
            (blinky.y_center + player.center_y) // 2 // 25 > 28 or
            settings.level[(blinky.y_center + player.center_y) // 2 // 25 > 28][
                (blinky.x_center + player.center_x) // 2 // 25 > 28] > 3):
        inky.target = (player.center_x, player.center_y)
    else:
        inky.target = (((blinky.x_center + player.center_x) // 2), ((player.center_y + blinky.y_center) // 2))

    # Pinky tries to target 4 spaces ahead of pacman (A* , heuristic 2),
    # but if that target is out of bounds or a wall/unreachable, it will default to targeting pacman
    if player.direction == 0:
        if (player.center_x + 100) // 25 > 28 or settings.level[player.center_y // 25][(player.center_x + 100) // 25] > 3:
            pinky.target = (player.center_x, player.center_y)
        else:
            pinky.target = (player.center_x + 100, player.center_y)
    elif player.direction == 1:
        if (player.center_x - 100) // 25 < 1 or settings.level[player.center_y // 25][(player.center_x - 100) // 25] > 3:
            pinky.target = (player.center_x, player.center_y)
        else:
            pinky.target = (player.center_x - 100, player.center_y)
    elif player.direction == 2:
        if (player.center_y - 100) // 25 < 1 or settings.level[(player.center_y - 100) // 25][player.center_x // 25] > 3:
            pinky.target = (player.center_x, player.center_y)
        else:
            pinky.target = (player.center_x, player.center_y - 100)
    elif player.direction == 3:
        if (player.center_y + 100) // 25 > 28 or settings.level[(player.center_y + 100) // 25][player.center_x // 25] > 3:
            pinky.target = (player.center_x, player.center_y)
        else:
            pinky.target = (player.center_x, player.center_y + 100)

    # Clyde does not use his target value when moving towards pacman,
    # but changes his x,y position based on his relative position to pacman instead
    clyde.target = (player.center_x, player.center_y)

    # if pacman currently has a power-up, and the ghost hasn't been eaten yet, their target is to flee to one
    # of the four corners of the grid
    if settings.power_up and not blinky.been_eaten:
        blinky.target = ((settings.width // 30) * 27 + 13, ((settings.height - 50) // 33) * 30 + 13)
    if settings.power_up and not inky.been_eaten:
        inky.target = ((settings.width // 30) * 2 + 13, ((settings.height - 50) // 33) * 30 + 13)
    if settings.power_up and not pinky.been_eaten:
        pinky.target = ((settings.width // 30) * 27 + 13, ((settings.height - 50) // 33) * 2 + 13)
    if settings.power_up and not clyde.been_eaten:
        clyde.target = ((settings.width // 30) * 2 + 13, ((settings.height - 50) // 33) * 2 + 13)

    # If the ghost is dead it's target is to return to the ghost box to respawn
    if blinky.dead:
        blinky.target = ((settings.width // 30) * 16 + 13, ((settings.height - 50) // 33) * 15 + 13)
    if inky.dead:
        inky.target = ((settings.width // 30) * 16 + 13, ((settings.height - 50) // 33) * 15 + 13)
    if pinky.dead:
        pinky.target = ((settings.width // 30) * 16 + 13, ((settings.height - 50) // 33) * 15 + 13)
    if clyde.dead:
        clyde.target = ((settings.width // 30) * 16 + 13, ((settings.height - 50) // 33) * 15 + 13)


# Draws the game board by using the values in the grid imported from 'Levels.py'
def draw_level(settings):
    num1 = ((settings.height - 50) // 33)
    num2 = (settings.width // 30)
    for i, row1 in enumerate(settings.level):
        for j, value in enumerate(row1):

            # Draw a small circle if a 1 (small dot)
            if value == 1:
                pygame.draw.circle(settings.screen, "white", (j * num2 + (.5 * num2), i * num1 + (.5 * num1)), 4)

            # Draw a larger circle if a 2 (power-up)
            if value == 2 and settings.counter > settings.fps // 2:
                pygame.draw.circle(settings.screen, "white", (j * num2 + (.5 * num2), i * num1 + (.5 * num1)), 10)

            # Draw a white horizontal line if a 3 (Ghost door)
            if value == 3:
                pygame.draw.line(settings.screen, "white", (j * num2, i * num1 + (.5 * num1)),
                                 (j * num2 + num2, i * num1 + (.5 * num1)), settings.line_width)

            # Draw vertical line if a 4 (wall)
            if value == 4:
                pygame.draw.line(settings.screen, settings.level_color, (j * num2 + (.5 * num2), i * num1),
                                 (j * num2 + (.5 * num2), i * num1 + num1), settings.line_width)

            # Draw a horizontal line if a 5 (wall)
            if value == 5:
                pygame.draw.line(settings.screen, settings.level_color, (j * num2, i * num1 + (.5 * num1)),
                                 (j * num2 + num2, i * num1 + (.5 * num1)), settings.line_width)

            # Draw the top right of a circle if a 6 (wall corner)
            if value == 6:
                pygame.draw.arc(settings.screen, settings.level_color,
                                ((j * num2 - (num2 * .5)), (i * num1 + (.5 * num1)), num2 + 2, num1),
                                0, math.pi / 2.0, settings.line_width)

            # Draw the top left of a circle if a 7 (wall corner)
            if value == 7:
                pygame.draw.arc(settings.screen, settings.level_color,
                                ((j * num2 + (num2 * .5)), (i * num1 + (.5 * num1)), num2, num1),
                                math.pi / 2, math.pi, settings.line_width)

            # Draw the bottom left of a circle if an 8 (wall corner)
            if value == 8:
                pygame.draw.arc(settings.screen, settings.level_color,
                                ((j * num2 + (num2 * .5)), (i * num1 - (.5 * num1)), num2, num1 + 2),
                                math.pi, 3 * math.pi / 2.0, settings.line_width)

            # Draw the bottom right of a circle (wall corner)
            if value == 9:
                pygame.draw.arc(settings.screen, settings.level_color,
                                ((j * num2 - (num2 * .5)), (i * num1 - (.5 * num1)), num2 + 2, num1 + 2),
                                3 * math.pi / 2.0, 2 * math.pi, settings.line_width - 1)


# Draws misc items on the screen, such as game over/won pop-ups, lives remaining, and the current score
def draw_misc(player, settings):
    # Display the score
    score_text = settings.font.render(f"Score: {settings.score}", True, "white")
    settings.screen.blit(score_text, (10, 845))

    # Display the amount of remaining lives
    for i in range(player.lives):
        settings.screen.blit(pygame.transform.scale(player_images[0], (30, 30)), (625 + i * 40, 835))

    if settings.game_lost:
        pygame.draw.rect(settings.screen, settings.level_color, [50, 225, 650, 250], 0, 10)
        pygame.draw.rect(settings.screen, "black", [75, 250, 600, 200], 0, 10)
        game_lost_text = settings.font.render("Game Over! Press Enter to play again!", True, "white")
        settings.screen.blit(game_lost_text, (175, 325))

    if settings.game_won:
        pygame.draw.rect(settings.screen, settings.level_color, [50, 225, 650, 250], 0, 10)
        pygame.draw.rect(settings.screen, "black", [75, 250, 600, 200], 0, 10)
        game_won_text = settings.font.render("You Won! Press Enter to go to next level!", True, "white")
        settings.screen.blit(game_won_text, (175, 325))


# Performs all collision checks, such as getting a dot or power-up, or colliding with a ghost, etc.
def check_collisions(player, blinky, inky, pinky, clyde, settings):
    # players (x,y) coordinates on the grid (tiles are 25x25 in pixels)
    j = player.center_x // 25
    i = player.center_y // 25

    # Player Collisions
    # if player is not out of bounds
    if 0 < player.center_x < settings.width:

        # check if players center position is a small dot. if so, remove dot from level and increase score by 10
        if settings.level[i][j] == 1:
            settings.channel.queue(pygame.mixer.Sound(pacman_chomp))
            settings.level[i][j] = 0
            settings.score += 10
            settings.dots_left -= 1

        # check if players center position is a large dot. if so, remove dot from level and increase score by 50
        # also updates game setting to reflect that a power-up was just picked up
        if settings.level[i][j] == 2:
            pygame.mixer.Sound(power_pellet_sound).play()
            settings.level[i][j] = 0
            settings.score += 50
            settings.dots_left -= 1
            settings.power_up = True
            settings.power_counter = 0
            player.eaten_ghosts = 0
            blinky.been_eaten = False
            inky.been_eaten = False
            pinky.been_eaten = False
            clyde.been_eaten = False
            # Tries to slow the ghosts down by a value of 2, but if their speed would be reduced to <= 0 sets them to 1
            if settings.ghost_speed - 2 > 1:
                if not blinky.dead:
                    blinky.speed = settings.ghost_speed - 2
                if not inky.dead:
                    inky.speed = settings.ghost_speed - 2
                if not pinky.dead:
                    pinky.speed = settings.ghost_speed - 2
                if not clyde.dead:
                    clyde.speed = settings.ghost_speed - 2
            else:
                if not blinky.dead:
                    blinky.speed = 1
                if not inky.dead:
                    inky.speed = 1
                if not pinky.dead:
                    pinky.speed = 1
                if not clyde.dead:
                    clyde.speed = 1

        # Check if all dots are gone
        if settings.dots_left <= 0:
            settings.game_won = True

        # Check if collided with blinky
        if i == blinky.y_center // 25 and j == blinky.x_center // 25:
            if settings.power_up:
                if not blinky.been_eaten:
                    pygame.mixer.Sound(eat_ghost_sound).play()
                    player.eaten_ghosts += 1
                    # increase score by 200, 400, 800, 1600
                    settings.score += 200 * (2 ** player.eaten_ghosts)
                    blinky.been_eaten = True
                    blinky.dead = True
                    blinky.speed = settings.ghost_speed
                elif not blinky.dead:
                    player_death(player, blinky, inky, pinky, clyde, settings)
            elif not blinky.dead:
                player_death(player, blinky, inky, pinky, clyde, settings)

        # Check if collided with inky
        if i == inky.y_center // 25 and j == inky.x_center // 25:
            if settings.power_up:
                if not inky.been_eaten:
                    pygame.mixer.Sound(eat_ghost_sound).play()
                    player.eaten_ghosts += 1
                    settings.score += 200 * (2 ** player.eaten_ghosts)
                    inky.been_eaten = True
                    inky.dead = True
                    inky.speed = settings.ghost_speed
                elif not inky.dead:
                    player_death(player, blinky, inky, pinky, clyde, settings)
            elif not inky.dead:
                player_death(player, blinky, inky, pinky, clyde, settings)

        # Check if collided with pinky
        if i == pinky.y_center // 25 and j == pinky.x_center // 25:
            if settings.power_up:
                if not pinky.been_eaten:
                    pygame.mixer.Sound(eat_ghost_sound).play()
                    player.eaten_ghosts += 1
                    settings.score += 200 * (2 ** player.eaten_ghosts)
                    pinky.been_eaten = True
                    pinky.dead = True
                    pinky.speed = settings.ghost_speed
                elif not pinky.dead:
                    player_death(player, blinky, inky, pinky, clyde, settings)
            elif not pinky.dead:
                player_death(player, blinky, inky, pinky, clyde, settings)

        # Check if collided with clyde
        if i == clyde.y_center // 25 and j == clyde.x_center // 25:
            if settings.power_up:
                if not clyde.been_eaten:
                    pygame.mixer.Sound(eat_ghost_sound).play()
                    player.eaten_ghosts += 1
                    settings.score += 200 * (2 ** player.eaten_ghosts)
                    clyde.been_eaten = True
                    clyde.dead = True
                    clyde.speed = settings.ghost_speed
                    # switch to a* to return to box
                    update_ghost_targets(player, blinky, inky, pinky, clyde, settings)
                    clyde.a_star_algorithm(False)
                elif not clyde.dead:
                    player_death(player, blinky, inky, pinky, clyde, settings)
            elif not clyde.dead:
                player_death(player, blinky, inky, pinky, clyde, settings)

    # Ghost collisions
    # Check if ghosts have made it back to their target in the box
    # only possible if ghost is dead, they are at their target path, and they aren't currently colliding with pacman
    if blinky.dead and len(blinky.path) == 0 and not (i == blinky.y_center // 25 and j == blinky.x_center // 25):
        blinky.dead = False
    if inky.dead and len(inky.path) == 0 and not (i == inky.y_center // 25 and j == inky.x_center // 25):
        inky.dead = False
    if pinky.dead and len(pinky.path) == 0 and not (i == pinky.y_center // 25 and j == pinky.x_center // 25):
        pinky.dead = False
    if clyde.dead and len(clyde.path) == 0 and not (i == clyde.y_center // 25 and j == clyde.x_center // 25):
        clyde.dead = False


# Repositions the level when player dies - triggers game loss if no extra lives remaining
def player_death(player, blinky, inky, pinky, clyde, settings):
    # play pacman death sound effect - pause game until it's finished
    # playsound(pacman_death)
    pygame.mixer.Sound(pacman_death).play()
    while pygame.mixer.get_busy():
        pygame.time.wait(500)

    # reduce lives by 1
    player.lives -= 1

    # End game if out of lives
    if player.lives < 0:
        settings.game_lost = True
        settings.startup_counter = 0
        return

    # reset timers
    settings.startup_counter = 0
    settings.power_up = False

    # reset player back to original positions
    player.actual_x = (settings.width // 30) * 15
    player.actual_y = ((settings.height - 50) // 33) * 24
    player.visual_x = player.actual_x - 10
    player.visual_y = player.actual_y - 10
    player.center_x = player.actual_x + 13
    player.center_y = player.actual_y + 13
    player.direction = 0

    # Reset Ghosts
    reset_ghosts(blinky, inky, pinky, clyde, settings)

    pygame.mixer.Sound(beginning_intro).play()


# Initial call to main game loop
main()

# Closing pygame module
pygame.quit()
