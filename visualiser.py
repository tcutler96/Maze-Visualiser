import pygame as pg
import pygame.freetype as pgf
import sys
import os
import random
import time
import queue

pg.init()

width, height = 101, 51  # height and width and maze
if width % 2 == 0:  # ensures width and height are odd
    width += 1
if height % 2 == 0:
    height += 1
empty = [[1] * width for _ in range(height)]  # initial empty grid layout
menu = [row[:] for row in empty]  # menu screen layout
menu[0], menu[-1] = [0] * width, [0] * width  # first and last row
for row in menu:
    row[0], row[-1] = 0, 0  # first and last column
grid = [row[:] for row in menu]  # initial grid layout
state = 0  # initial state
start_pos = [1, 1]  # start position
end_pos = [width - 2, height - 2]  # end position
keys = {
    'cell': [0, (230, 230, 230)],
    'wall': [1, (25, 25, 25)],
    'start': [2, (150, 0, 0)],
    'end': [3, (0, 150, 0)],
    'queued': [4, (0, 0, 150)],
    'searched': [5, (0, 150, 150)],
    'path': [6, (150, 100, 150)]
}  # cell information dictionary (name: value, colour)
options = {
    0: ['Queue Method: ', ['LIFO', 'FIFO'], 0, 'What order elements are taken out of the queue', 6],
    1: ['Choose Method: ', ['random', 'first', 'last'], 0, 'How new unvisited neighbours are chosen', 7],
    2: ['Algorithm: ', ['bfs', 'dfs'], 0, 'Which path finding algorithm is used', 10]
}  # options information dictionary (index: text, options, current option, tooltip, height)
button_collide = [0] * len(options)
search = 'bfs'  # maze search type
scale = 10  # grid pixel scale
window_width, window_height = len(empty[0]) * scale, len(empty) * scale  # size of window
leg_scale = int((window_width - 2 * scale) / 40)  # legend scale
os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % (int(pg.display.Info().current_w - window_width) / 2,
                                                int(pg.display.Info().current_h - window_height) / 3)  # screen position
screen = pg.display.set_mode((window_width, window_height + int(leg_scale * 1.5)))  # set screen size
pg.display.set_caption('Maze Generator & Solver')  # set screen menu
legend_font = pgf.SysFont('Consolas', leg_scale)  # legend font
menu_font = pg.font.SysFont('Consolas', int(leg_scale * 0.65))  # menu font
clock = pg.time.Clock()
particles = []


def draw_screen(grid, state):
    screen.fill(keys['wall'][1])
    if state == 0:
        draw_menu()  # draws menu
        for _, particle in sorted(enumerate(particles), reverse=True):
            if particle.size <= 0 or (not 0 <= particle.x_pos <= window_width) or (not particle.y_pos <= window_height):
                particles.remove(particle)
            else:
                particle.draw()  # draws particle
    draw_maze(grid)  # draws maze
    draw_legend()  # draws legend
    pg.display.update()  # updates display


def draw_maze(grid):  # draws grid to screen
    for idx_c, col in enumerate(grid):
        for idx_r, row in enumerate(col):
            if row != keys['wall'][0]:
                outline = 0
                rect = pg.Rect(idx_r * scale, idx_c * scale, scale, scale)
                if row == keys['start'][0]:
                    pg.draw.rect(screen, keys['start'][1], rect)
                elif row == keys['end'][0]:
                    pg.draw.rect(screen, keys['end'][1], rect)
                elif row == keys['queued'][0]:
                    pg.draw.rect(screen, keys['queued'][1], rect)
                elif row == keys['searched'][0]:
                    pg.draw.rect(screen, keys['searched'][1], rect)
                elif row == keys['path'][0]:
                    pg.draw.rect(screen, keys['path'][1], rect)
                else:
                    pg.draw.rect(screen, keys['cell'][1], rect)
                pg.draw.rect(screen, keys['wall'][1], rect, 2 - outline)


def draw_menu():  # draws controls and options menu
    global buttons
    legend_font.render_to(screen, (scale * 2, leg_scale), 'Press ESC to quit', (230, 230, 230))
    legend_font.render_to(screen, (scale * 2, leg_scale * 2), 'CLICK to change options', (230, 230, 230))
    legend_font.render_to(screen, (scale * 2, leg_scale * 3), 'Press SPACE to begin', (230, 230, 230))
    legend_font.render_to(screen, (scale * 2, leg_scale * 5), 'Generation options', (230, 230, 230))
    legend_font.render_to(screen, (scale * 2, leg_scale * 9), 'Solving options', (230, 230, 230))
    buttons = []
    for option in range(len(options)):
        temp_text = menu_font.render(options[option][0] + options[option][1][options[option][2]], True, (230, 230, 230))
        temp_button = pg.Rect(scale * 2, leg_scale * options[option][4], temp_text.get_width() + scale,
                              temp_text.get_height() + int(scale / 2))
        temp_tooltip = menu_font.render(options[option][3], True, (230, 230, 230))
        buttons.append([temp_text, temp_button, temp_tooltip])
    for index, button in enumerate(buttons):
        screen.blit(button[0], (button[1][0] + int(scale / 2), button[1][1] + int(scale / 4)))
        pg.draw.rect(screen, (230, 230, 230), button[1], 1 + button_collide[index])
        if button_collide[index]:
            screen.blit(button[2], (button[1][0] + int(scale / 2) + button[1][2], button[1][1] + int(scale / 4)))


def draw_legend():  # draws maze colour legend
    counter = 3
    for legend in keys:
        rect = pg.Rect(scale + leg_scale * counter, window_height, leg_scale, leg_scale)
        if legend == 'wall':
            pg.draw.rect(screen, keys['cell'][1], rect, 1)
        else:
            pg.draw.rect(screen, keys[legend][1], rect)
            pg.draw.rect(screen, keys['wall'][1], rect, 1)
        legend_font.render_to(screen, (int(scale + leg_scale * (counter + 1.5)),
                                       int(window_height + leg_scale * 0.25)), legend, (230, 230, 230))
        counter += 1 + int(len(legend) / 2 + 2)


def visualiser(grid):
    qm = options[0][1][options[0][2]]  # chosen options
    cm = options[1][1][options[1][2]]
    algorithm = options[2][1][options[2][2]]
    create_maze(grid, start_pos, end_pos, q_method=qm, c_method=cm)  # creates maze
    time.sleep(1)
    solve_maze(grid, start_pos, end_pos, method=algorithm)  # solves maze


class Particle:  # particle control
    def __init__(self, x_pos, y_pos, x_vel, y_vel, x_acc, y_acc, size, shrink, colour):
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.x_vel = x_vel
        self.y_vel = y_vel
        self.x_acc = x_acc
        self.y_acc = y_acc
        self.size = size
        self.shrink = shrink
        self.colour = colour

    def draw(self):
        pg.draw.circle(screen, self.colour, (int(self.x_pos), int(self.y_pos)), int(self.size))  # draw particle
        self.x_pos += self.x_vel  # x position + velocity
        self.y_pos += self.y_vel  # y position + velocity
        self.x_vel += self.x_acc  # x velocity + acceleration
        self.y_vel += self.y_acc  # y velocity + acceleration
        self.size -= self.shrink  # adjust particle size


def create_maze(grid, start_pos, end_pos, q_method='dfs', c_method='random'):  # generates random maze layout
    grid[start_pos[1]][start_pos[0]] = 0  # marks starting position as visited
    if q_method == 'LIFO':
        q = queue.LifoQueue()  # initiates queue
    elif q_method == 'FIFO':
        q = queue.Queue()
    q.put([start_pos, start_pos])  # puts starting position onto queue
    grid[start_pos[1]][start_pos[0]] = keys['queued'][0]
    while q.qsize() > 0:  # while there are elements in the queue
        draw_screen(grid, state)  # redraws grid
        pos = q.get()  # gets last position from queue
        neighbours = get_neighbours(grid, pos[1])  # gets unvisited neighbours of current position
        if len(neighbours) > 0:  # if current position has any unvisited neighbours
            q.put(pos)  # puts current position onto queue
            if c_method == 'random':
                pos = random.choice(neighbours)  # randomly chooses one of the unvisited neighbours
            elif c_method == 'first':
                pos = neighbours[0]  # chooses first unvisited neighbour
            elif c_method == 'last':
                pos = neighbours[-1]  # chooses last unvisited neighbour
            grid[pos[0][1]][pos[0][0]] = keys['queued'][0]  # marks new position as visited
            grid[pos[1][1]][pos[1][0]] = keys['queued'][0]
            q.put(pos)  # puts new position onto queue
        else:
            grid[pos[0][1]][pos[0][0]] = keys['cell'][0]  # marks position as dead end
            grid[pos[1][1]][pos[1][0]] = keys['cell'][0]

    grid[start_pos[1]][start_pos[0]] = keys['cell'][0]
    draw_screen(grid, state)  # redraws grid
    time.sleep(0.25)
    grid[start_pos[1]][start_pos[0]] = 2  # adds start position
    draw_screen(grid, state)  # redraws grid
    time.sleep(0.25)
    grid[end_pos[1]][end_pos[0]] = 3  # add end position
    draw_screen(grid, state)  # redraws grid
    return grid


def get_neighbours(grid, pos):  # gets unvisited neighbours of grid element
    neighbours = []
    direcs = [[-1, 0], [1, 0], [0, -1], [0, 1]]  # four cardinal directions
    for direc in direcs:
        new_pos1 = [pos[0] + direc[0], pos[1] + direc[1]]  # new wall position
        new_pos2 = [new_pos1[0] + direc[0], new_pos1[1] + direc[1]]  # new cell position
        # if new position is an unvisited cell within the array boundaries
        if 0 < new_pos2[0] < len(grid[0]) - 1 and 0 < new_pos2[1] < len(grid) - 1 \
                and grid[new_pos2[1]][new_pos2[0]] == 1:
            direcs = [[-1, -1], [-1, 0], [-1, 1], [0, 1], [1, 1], [1, 0], [1, -1], [0, -1]]
            walls = 0  # counts number of walls surrounding cell
            for direc in direcs:
                walls += grid[new_pos2[1] + direc[1]][new_pos2[0] + direc[0]]
            if walls == 8:  # if completely surrounded
                neighbours.append([new_pos1, new_pos2])
    return neighbours


def solve_maze(grid, start_pos, end_pos, method='bfs'):  # finds path through maze
    if method == 'bfs':
        q = queue.Queue()  # initiates queue
    elif method == 'dfs':
        q = queue.LifoQueue()  # initiates queue
    q.put('')
    while q.qsize() > 0:
        path = q.get()  # gets first element in queue
        _, pos = follow_path(grid, start_pos, path)  # gets position of current path
        grid[pos[1]][pos[0]] = keys['searched'][0]  # mark element as searched
        if end_pos == pos:  # checks if end has been found
            draw_screen(grid, state)
            time.sleep(1)
            grid[start_pos[1]][start_pos[0]] = keys['start'][0]  # resets start position
            draw_screen(grid, state)
            follow_path(grid, start_pos, path[:-1], draw=True, key=keys['path'][0])  # draws solution path
            grid[end_pos[1]][end_pos[0]] = keys['end'][0]  # resets end position
            draw_screen(grid, state)
            q.queue.clear()  # clears queue
            break
        for direct in ['L', 'R', 'U', 'D']:
            new_path = path + direct  # checks each direction around element
            _, new_pos = follow_path(grid, start_pos, new_path)
            if valid_pos(grid, start_pos, new_path):  # if valid element
                q.put(new_path)  # put back into queue
                grid[new_pos[1]][new_pos[0]] = keys['queued'][0]  # mark element as queued
                draw_screen(grid, state)  # redraws grid
    return grid


def valid_pos(grid, start_pos, path):  # checks if given path results in a valid position
    _, pos = follow_path(grid, start_pos, path)  # current element
    # checks if element is an un searched cell element within the array boundaries
    if not (0 <= pos[0] <= len(grid[0]) - 1 and 0 <= pos[1] <= len(grid) and
            grid[pos[1]][pos[0]] in [keys['cell'][0], keys['end'][0]]):
        return False
    return True


def follow_path(grid, start_pos, path, draw=False, key=0):  # follows given path through grid
    pos = start_pos.copy()  # begins at start position
    for move in path:  # increments through each move in path
        if move == 'L':
            pos[0] -= 1
        elif move == 'R':
            pos[0] += 1
        elif move == 'U':
            pos[1] -= 1
        elif move == 'D':
            pos[1] += 1
        if draw:  # draws along path
            grid[pos[1]][pos[0]] = key
            draw_screen(grid, state)
    return grid, pos


def main():
    global grid, state, button_collide, particles
    run = True

    while run:
        clock.tick(60)
        draw_screen(grid, state)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                keys_pressed = pg.key.get_pressed()
                if keys_pressed[pg.K_ESCAPE]:
                    if state == 0:
                        pg.quit()
                        sys.exit()
                    elif state == 1:
                        state = 0
                        grid = [row[:] for row in menu]  # menu screen layout
                if keys_pressed[pg.K_SPACE]:
                    if state == 0:
                        state = 1
                        grid = [row[:] for row in empty]  # initial empty maze
                        particles = []  # resets particles
                        visualiser(grid)

            mouse_pos = pg.mouse.get_pos()  # gets mouse position
            if event.type == pg.MOUSEBUTTONDOWN and 0 <= mouse_pos[0] <= window_width \
                    and 0 <= mouse_pos[1] <= window_height and state == 0:
                if event.button == 1 or event.button == 3 or event.button == 4 or \
                        event.button == 5:  # if mouse button pressed
                    for _ in range(100):  # creates 10 particles
                        particles.append(Particle(mouse_pos[0], mouse_pos[1], random.randint(0, 60) / 10 - 3,
                                                  random.randint(0, 60) / 10 - 5, 0, 0.1, random.randint(1, 4), 0.025,
                                                  (random.randint(0, 255), random.randint(0, 255),
                                                   random.randint(0, 255))))  # creates particle object
            button_collide = [int(buttons[index][1].collidepoint(mouse_pos)) for index
                              in range(len(button_collide))]  # checks for collision between mouse and all buttons
            if 1 in button_collide:  # if mouse is colliding with a button
                button = button_collide.index(1)  # gets collided button index
                if event.type == pg.MOUSEMOTION:
                    particles.append(Particle(mouse_pos[0], mouse_pos[1], random.randint(0, 20) / 10 - 1,
                                              0, 0, 0.2, random.randint(1, 3), 0.075,
                                              (230, 230, 230)))  # create new particle
                if event.type == pg.MOUSEBUTTONUP:  # if mouse button depressed
                    if event.button == 1 or event.button == 3:  # if left or right mouse button clicked
                        cur_index = options[button][2]  # current index
                        if event.button == 1:  # increment index with left click
                            new_index = cur_index + 1
                            if new_index > len(options[button][1]) - 1:  # wrap index value
                                new_index = 0
                        elif event.button == 3:  # decrement index with right click
                            new_index = cur_index - 1
                            if new_index < 0:  # wrap index value
                                new_index = len(options[button][1]) - 1
                        options[button][2] = new_index  # new index


main()
