from snake import *
from utility import *
from cube import *

import pygame
import numpy as np
from tkinter import messagebox
import matplotlib.pyplot as plt


def main():
    pygame.init()
    win = pygame.display.set_mode((WIDTH, HEIGHT))

    snake_1 = Snake((255, 0, 0), (15, 15), SNAKE_1_Q_TABLE)
    snake_2 = Snake((255, 255, 0), (5, 5), SNAKE_2_Q_TABLE)
    snake_1.addCube()
    snake_2.addCube()

    snack = Cube(randomSnack(ROWS, snake_1), color=(0, 255, 0))

    clock = pygame.time.Clock()
    episodes = 1500  # Number of episodes for training
    epsilon_decay = 0.995  # Epsilon decay rate
    min_epsilon = 0.01  # Minimum epsilon value
    rewards = []  # store reward for plotting

    for episode in range(episodes):
        total_reward_1 = 0
        total_reward_2 = 0
        done = False

        while not done:
            pygame.time.delay(25)
            clock.tick(5)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    if messagebox.askokcancel("Quit", "Do you want to save the Q-tables?"):
                        save(snake_1, snake_2)
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    np.save(SNAKE_1_Q_TABLE, snake_1.q_table)
                    np.save(SNAKE_2_Q_TABLE, snake_2.q_table)
                    pygame.time.delay(100)

            state_1, new_state_1, action_1 = snake_1.move(snack, snake_2)
            state_2, new_state_2, action_2 = snake_2.move(snack, snake_1)

            snack, reward_1, win_1, win_2 = snake_1.calc_reward(snack, snake_2)
            snack, reward_2, win_2, win_1 = snake_2.calc_reward(snack, snake_1)

            snake_1.update_q_table(state_1, action_1, new_state_1, reward_1)
            snake_2.update_q_table(state_2, action_2, new_state_2, reward_2)

            total_reward_1 += reward_1
            total_reward_2 += reward_2

            redrawWindow(snake_1, snake_2, snack, win)

            if win_1 or win_2:
                done = True

        rewards.append((total_reward_1, total_reward_2))

        # Decay epsilon
        if snake_1.epsilon > min_epsilon:
            snake_1.epsilon *= epsilon_decay
        if snake_2.epsilon > min_epsilon:
            snake_2.epsilon *= epsilon_decay

    # Plot rewards
    rewards_1, rewards_2 = zip(*rewards)
    plt.plot(rewards_1, label="Snake 1")
    plt.plot(rewards_2, label="Snake 2")
    plt.xlabel("Episode")
    plt.ylabel("Total Reward")
    plt.legend()
    plt.show()

    save(snake_1, snake_2)


if __name__ == "__main__":
    main()
