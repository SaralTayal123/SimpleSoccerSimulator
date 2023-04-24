''' 
Use this file to create your custom agent!
'''

from env import Enviornment
from supporting_classes import Actions, Movement, Team
from enum import Enum
import copy
import numpy as np
from macroAgentHelper import *
from macroMCTS import *

class Agent():
    def __init__(self, team) -> None:
        self.team = team
        self.curr_action = None
        self.time_taken_for_curr = 0
        pass

    def act(self, env):
        '''
        Return a list of actions, args for each player

        Examples: 
        * Actions.Move, playerId, [Movement.<direction>]
        * Actions.SHOOT_BALL, playerId, []
        * Actions.PASS_BALL, playerId, [targetPlayerId]
        * Actions.TACKLE_BALL, playerId, []


        Available functions in env:
        * env.getPlayers(team) -> returns a list of players in the team
        * env.getOpponents(team) -> returns a list of opponents in the team
        * env.getBallPosition() -> returns the position of the ball
        * env.getBallOwner() -> returns the playerID of the player who owns the ball
        * env.getBallOwnerTeam() -> returns the team of the player who owns the ball
        * env.testPass(playerId, targetPlayerId) -> returns True if the pass is possible
        * env.testShoot(playerId, team) -> returns True if the shoot is possible
        '''
        
        """
        1. Create a state class
            properties: which macro cell each robot is in (your team and opponent)
                value
                team
            generateChilden() -> returns a list of children states
            -> getNextState([actions]) -> returns the next state given this rollout of actions
            -> getValue() -> returns the value of this state via a rollout? 
            
         
        """

        players_home = env.getPlayers(self.team)

        if (self.curr_action == None or self.time_taken_for_curr >= 20):
            oppositeTeam = Team.LEFT
            if self.team == Team.LEFT:
                oppositeTeam = Team.RIGHT
            players_opp = env.getPlayers(oppositeTeam)

            macro_players_home = []
            macro_players_opp = []
            for player in players_home:
                macro_x = int((player.pos_x / env.dim_x) * NUM_ZONES_X)
                macro_y = int((player.pos_y / env.dim_y) * NUM_ZONES_Y)
                macro_player = MacroPlayer(macro_x, macro_y)
                if player.dribble:
                    macro_player.possession = True
                macro_players_home.append(macro_player)
            for player in players_opp:
                macro_x = int((player.pos_x / env.dim_x) * NUM_ZONES_X)
                macro_y = int((player.pos_y / env.dim_y) * NUM_ZONES_Y)
                macro_player = MacroPlayer(macro_x, macro_y)
                if player.dribble:
                    macro_player.possession = True
                macro_players_opp.append(macro_player)


            stateInit = State(depth = 0, agent_team = self.team, team = self.team, players_home = macro_players_home, players_opponent = macro_players_opp, env = env)
            # stateInit.print_state()


            mctsSearcher = MCTSSearcher(500)
            macro_action = mctsSearcher.search(stateInit, debug_print=True)
            # macro_action = MCTSAction(stateInit.getHeuristicAction())
            print("action: ")
            print(macro_action.game_action)
            self.curr_action = macro_action.game_action
            self.time_taken_for_curr = 0

        actions = []
        for i, action in enumerate(self.curr_action):
            curr_player = players_home[i]
            if action == MacroActions.Up:
                actions.append([Actions.MOVE, curr_player.playerId, [Movement.UP]])
            elif action == MacroActions.Down:
                actions.append([Actions.MOVE, curr_player.playerId, [Movement.DOWN]])
            elif action == MacroActions.Left:
                actions.append([Actions.MOVE, curr_player.playerId, [Movement.LEFT]])
            elif action == MacroActions.Right:
                actions.append([Actions.MOVE, curr_player.playerId, [Movement.RIGHT]])
            elif action == MacroActions.Tackle:   
                actions.append([Actions.TACKLE_BALL, curr_player.playerId, []])
            elif action == MacroActions.Shoot:
                actions.append([Actions.SHOOT_BALL, curr_player.playerId, []])
            elif action == MacroActions.Pass:
                actions.append([Actions.PASS_BALL, curr_player.playerId, [players_home[1-i].playerId]])

        self.time_taken_for_curr += 1

        return actions