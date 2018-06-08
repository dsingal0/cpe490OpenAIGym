import gym
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from collections import deque
from matplotlib import pyplot as plt
plt.switch_backend('agg')
# Create the Cart-Pole game environment
env = gym.make('CartPole-v0')


class DQNetwork:
    def __init__(self, learning_rate=0.01):
        # state inputs to the Q-network
        self.model = Sequential()

        self.model.add(Dense(10, activation='relu', input_dim=4))
        self.model.add(Dense(10, activation='relu'))
        self.model.add(Dense(2, activation='linear'))
        self.optimizer = 'adagrad'
        self.model.compile(loss='mse', optimizer=self.optimizer)


class Memory():
    def __init__(self, max_size=1000):
        self.b = deque(maxlen=max_size)

    def learn(self, exp):
        self.b.append(exp)

    def sample(self, batch_size):
        idx = np.random.choice(
            np.arange(len(self.b)), size=batch_size, replace=False)
        return [self.b[i] for i in idx]


train_episodes = 4  # max number of episodes to learn from
max_steps = 200  # max steps in an episode
gamma = 0.99  # future reward discount
batch_size = 32  # experience mini-batch size
pretrain_length = batch_size  # number experiences to pretrain the memory

mainQN = DQNetwork()
#resest environment before starting to build memory
env.reset()
# do something random to start environment
state, reward, done, _ = env.step(env.action_space.sample())
state = np.reshape(state, [1, 4])
memory = Memory()

for ii in range(pretrain_length):
    # env.render()
    action = env.action_space.sample()
    next_state, reward, done, _ = env.step(action)
    next_state = np.reshape(next_state, [1, 4])

    if done:
        next_state = np.zeros(state.shape)
        memory.learn((state, action, reward, next_state))

        env.reset()
        state, reward, done, _ = env.step(env.action_space.sample())
        state = np.reshape(state, [1, 4])
    else:
        memory.learn((state, action, reward, next_state))
        state = next_state
step = 0
# starting episodes from 1
for ep in range(1, train_episodes):
    total_reward = 0
    t = 0
    steps_per_sample = []
    while t < max_steps:
        step += 1
        # env.render()

        action = env.action_space.sample()
        next_state, reward, done, _ = env.step(action)
        next_state = np.reshape(next_state, [1, 4])
        total_reward += reward

        if done:
            # the episode ends so no next state
            next_state = np.zeros(state.shape)
            steps_per_sample.append(total_reward)
            t = max_steps
            print('Episode: {}'.format(ep),
                  'Total reward: {}'.format(total_reward))
            # Add experience to memory
            memory.learn((state, action, reward, next_state))
            # Start new episode
            env.reset()
            # Take one random step to get the pole and cart moving
            state, reward, done, _ = env.step(env.action_space.sample())
            state = np.reshape(state, [1, 4])
        else:
            # Add experience to memory
            memory.learn((state, action, reward, next_state))
            state = next_state
            t += 1

        # Replay
        inputs = np.zeros((batch_size, 4))
        targets = np.zeros((batch_size, 2))

        minibatch = memory.sample(batch_size)
        for i, (state_b, action_b, reward_b,
                next_state_b) in enumerate(minibatch):
            inputs[i:i + 1] = state_b
            target = reward_b
            if not (next_state_b == np.zeros(state_b.shape)).all(axis=1):
                target_Q = mainQN.model.predict(next_state_b)[0]
                target = reward_b + gamma * np.amax(
                    mainQN.model.predict(next_state_b)[0])
            targets[i] = mainQN.model.predict(state_b)
            targets[i][action_b] = target
        mainQN.model.fit(inputs, targets, epochs=1, verbose=0)
plt.hist(steps_per_sample)
plt.title('DQN Algorithm')
plt.xlabel('Episodes')
plt.ylabel('Frequency')
plt.savefig('dqn.png')