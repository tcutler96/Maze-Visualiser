# Path-Finding-Visualiser
A Python maze generator and sovler, visualised with PyGame.

A Python script that first generates a maze and then solves it. This is visualised with PyGame using a simple but 
effective design. Includes a main menu teaching the controls and offering the user the ability to change a number of 
options that effect maze generation and solving. Once initiated, the current state of each cell is shown using colours, 
which are explained with a handy key.

--- Options ---
-- Maze Generation --
- Queue Method (What order elements are taken out of the queue): LIFO, FIFO
- Choose Method (How new unvisited neighbours are chosen): random, first, last
(Note: choosing LIFO and random yields the recursive back tracker algorithm)

-- Maze Solving --
- Algorithm (Which path finding algorithm is used): breadth-first search, depth-first search
