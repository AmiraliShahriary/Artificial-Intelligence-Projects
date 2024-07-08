from cube import Cube
from constants import *
from utility import *

import random
import numpy as np


class Snake:
    def __init__(self, color, pos, file_name=None):
        self.color = color
        self.head = Cube(pos, color=color)
        self.body = [self.head]
        self.turns = {}
        self.dirnx = 0
        self.dirny = 1

        if file_name is not None:
            try:
                self.q_table = np.load(file_name)
                print(f"Loaded Q-table from {file_name}")
            except:
                self.q_table = np.zeros((20, 20, 20, 20, 4))  
                print("Start learning and load to Q-table")

        else:
            self.q_table = np.zeros((20, 20, 20, 20, 4))  
            print("Start learning and load to Q-table")

        self.lr = 0.1  # Learning rate
        self.discount_factor = 0.95  # Discount factor
        self.epsilon = 0  # Epsilon for epsilon-greedy policy 
        # first for learning we put epsilon on 1 so the agent starts with complete exploration 
        # to encourage the agent to explore different strategies and states.
        self.epsilon_decay = 0.995  # Epsilon decay rate
        self.min_epsilon = 0.01  # Minimum epsilon value
        # prevents the agent from becoming overly greedy too

    def get_optimal_policy(self, state, other_snake_pos):
        q_values = self.q_table[state]
        max_q_value = np.max(q_values)
        actions_with_max_q_value = [i for i in range(len(q_values)) if q_values[i] == max_q_value]

        # tie-breaking  based on immediate rewards or small random values
        if len(actions_with_max_q_value) > 1:
            rewards = [self.estimate_immediate_reward(state, action, other_snake_pos) for action in actions_with_max_q_value]
            max_reward = max(rewards)
            best_actions = [actions_with_max_q_value[i] for i in range(len(rewards)) if rewards[i] == max_reward]
            return random.choice(best_actions)

        return actions_with_max_q_value[0]

    def estimate_immediate_reward(self, state, action, other_snake_pos):
        x, y, snack_x, snack_y = state
        if action == 0:  # Left
            x -= 1
        elif action == 1:  # Right
            x += 1
        elif action == 2:  # Up
            y -= 1
        elif action == 3:  # Down
            y += 1

        # Check for out of bounds
        if x < 1 or x >= ROWS - 1 or y < 1 or y >= ROWS - 1:
            return -1000  # High penalty for out of bounds

        # Check for collision with the other snake
        if (x, y) in other_snake_pos:
            return -1000  # High penalty for colliding with the other snake

        # reward for moving closer to the snack
        distance_to_snack = abs(snack_x - x) + abs(snack_y - y)
        immediate_reward = -distance_to_snack  

        return immediate_reward
    
    def make_action(self, state, other_snake_pos):
        if random.random() < self.epsilon:
            action = random.randint(0, 3)  
        else:
            action = self.get_optimal_policy(state, other_snake_pos)  
        return action



    def update_q_table(self, state, action, next_state, reward):
        if all(0 <= x < 20 for x in state) and all(0 <= x < 20 for x in next_state):
            best_next_action = np.argmax(self.q_table[next_state])

            td_target = reward + self.discount_factor * self.q_table[next_state][best_next_action]
            td_error = td_target - self.q_table[state][action]
            self.q_table[state][action] += self.lr * td_error

    def move(self, snack, other_snake):
        state = (self.head.pos[0], self.head.pos[1], snack.pos[0], snack.pos[1])
        other_snake_pos = [cube.pos for cube in other_snake.body]  
        action = self.make_action(state, other_snake_pos)

        if action == 0 and self.dirnx != 1:  # Left
            self.dirnx = -1
            self.dirny = 0
        elif action == 1 and self.dirnx != -1:  # Right
            self.dirnx = 1
            self.dirny = 0
        elif action == 2 and self.dirny != 1:  # Up
            self.dirny = -1
            self.dirnx = 0
        elif action == 3 and self.dirny != -1:  # Down
            self.dirny = 1
            self.dirnx = 0

        self.turns[self.head.pos[:]] = [self.dirnx, self.dirny]

        for i, c in enumerate(self.body):
            p = c.pos[:]
            if p in self.turns:
                turn = self.turns[p]
                c.move(turn[0], turn[1])
                if i == len(self.body) - 1:
                    self.turns.pop(p)
            else:
                c.move(c.dirnx, c.dirny)

        new_state = (self.head.pos[0], self.head.pos[1], snack.pos[0], snack.pos[1])  
        return state, new_state, action

    

    def check_out_of_board(self):
        headPos = self.head.pos
        if headPos[0] >= ROWS - 1 or headPos[0] < 1 or headPos[1] >= ROWS - 1 or headPos[1] < 1:
            return True
        return False
    
    def calc_reward(self, snack, other_snake):
        reward = 0
        win_self, win_other = False, False

        if self.check_out_of_board():
            print("Snake went out of bounds")
            reward = -10000  # Punish the snake for getting out of the board
            win_other = True
            self.reset((random.randint(3, 18), random.randint(3, 18)))
            return snack, reward, win_self, win_other

        if self.head.pos == snack.pos:
            self.addCube()
            snack = Cube(randomSnack(ROWS, self), color=(0, 255, 0))
            reward = 1000  # Reward the snake for eating
            print("Snake ate a snack")

        if self.head.pos in list(map(lambda z: z.pos, self.body[1:])):
            print("Snake collided with itself")
            reward = -6000  # Punish the snake for hitting itself
            win_other = True
            self.reset((random.randint(3, 18), random.randint(3, 18)))

        if self.head.pos in list(map(lambda z: z.pos, other_snake.body)):
            if self.head.pos != other_snake.head.pos:
                print("Snake collided with the other snake's body")
                reward = -8000  # Punish the snake for hitting the other snake
                win_other = True
                self.reset((random.randint(3, 18), random.randint(3, 18)))

            else:
                if len(self.body) > len(other_snake.body):
                    print("Snake won by head collision")
                    reward = 5000  # Reward the snake for hitting the head of the other snake and being longer
                    win_self = True
                elif len(self.body) == len(other_snake.body):
                    print("Head collision with equal length")
                    reward = 0  # No winner
                else:
                    print("Snake lost by head collision")
                    reward = -7000  # Punish the snake for hitting the head of the other snake and being shorter
                    win_other = True
                    self.reset((random.randint(3, 18), random.randint(3, 18)))

        return snack, reward, win_self, win_other

   

    def reset(self, pos):
        self.head = Cube(pos, color=self.color)
        self.body = [self.head] # this way is more efficient
        self.turns = {}
        self.dirnx = 0
        self.dirny = 1

    def addCube(self):
        tail = self.body[-1]
        dx, dy = tail.dirnx, tail.dirny

        if dx == 1 and dy == 0:
            self.body.append(Cube((tail.pos[0] - 1, tail.pos[1]), color=self.color))
        elif dx == -1 and dy == 0:
            self.body.append(Cube((tail.pos[0] + 1, tail.pos[1]), color=self.color))
        elif dx == 0 and dy == 1:
            self.body.append(Cube((tail.pos[0], tail.pos[1] - 1), color=self.color))
        elif dx == 0 and dy == -1:
            self.body.append(Cube((tail.pos[0], tail.pos[1] + 1), color=self.color))

        self.body[-1].dirnx = dx
        self.body[-1].dirny = dy

    def draw(self, surface):
        for i, c in enumerate(self.body):
            if i == 0:
                c.draw(surface, True)
            else:
                c.draw(surface)

    def save_q_table(self, file_name):
        np.save(file_name, self.q_table)

