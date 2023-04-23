import cv2 as cv
from env import Enviornment
from agent import Agent
from agentNaive import Agent as AgentNaive
from supporting_classes import Team
from agentBharath import Agent as AgentBharath
from macroAgent import Agent as MacroAgent

env = Enviornment()
env.init_random_game(2)
# env.init_2player_game()

agent2 = AgentNaive(team=Team.RIGHT)
agent1 = MacroAgent(team=Team.LEFT)

while(env.gameRunning):

    actions1 = agent1.act(env)
    actions2 = agent2.act(env)

    for action, playerid, args in actions1:
        env.execute(action, playerid, args)
    for action, playerid, args in actions2:
        env.execute(action, playerid, args)

    env.drawEnviornment(1) # ms update rate
    break