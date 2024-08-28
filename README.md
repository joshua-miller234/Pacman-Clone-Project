
Purpose: 

The purpose of this project was to make as faithful as possible clone of the Pacman arcade game as a practice project for python, and as a practice / demonstration project for different pathfinding algorithms used by the ghosts – such as breadth first search / A* algorithms with different heuristic functions vs more suboptimal greedy algorithms. 


Running the Project:

The game was made in Pycharm IDE, using the pygame import. If Pycharm is installed, the files/folders “assets”, “PacmanGame.py”, and “Levels.py” can be dragged/dropped into a new Pycharm project. Pycharm should prompt/handle missing imports (if there are any). The game can then be ran by running the “PacmanGame.py” file.

Alternatively, any other method to run the PacmanGame.py file should work. So long as the three files/folders are in the same directory, and the needed imports at the top of PacmanGame.py are installed.


A* Algorithm:

The main pathfinding algorithm used by the ghosts is the A* algorithm, which is used with two different heuristics, that can path around obstacles directly to the player, and then a simple greedy algorithm that tried to move in the players direction regardless of obstacles. An illustration of which ghosts use which algorithm / heuristic is in the included PowerPoint presentation file. There is also a video demonstration of a level of the game being played included as the last slide of the PowerPoint.

Heuristics:

There two heuristics used by the A* algorithm. The first is used by Blinky (red ghost) and is the distance formula, the direct diagonal distance from current position to target. The second heuristic is used by Inky (teal ghost) and Pinky (pink ghost) and is a calculation of the Manhattan distance from current position to target. Clyde (orange ghost) uses the greedy algorithm.


[Pacman Project Presentation.pptx](https://github.com/user-attachments/files/16789961/Pacman.Project.Presentation.pptx)
