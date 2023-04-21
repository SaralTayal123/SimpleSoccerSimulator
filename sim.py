import cv2 as cv
from env import Enviornment
from agent import Agent
from supporting_classes import Team

env = Enviornment()
env.init_random_game(2)

agent1 = Agent(team=Team.LEFT)
agent2 = Agent(team=Team.RIGHT)

while(True):

    actions1 = agent1.act(env)
    actions2 = agent2.act(env)

    for action, playerid, args in actions1:
        env.execute(action, playerid, args)
    for action, playerid, args in actions2:
        env.execute(action, playerid, args)

    env.drawEnviornment(1) # ms update rate