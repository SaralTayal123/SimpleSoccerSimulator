''' 
Use this file to create your custom agent!
'''

from env import Enviornment
from supporting_classes import Actions, Movement, Team
from enum import Enum
import copy
import numpy as np

NUM_ZONES_X = 10
NUM_ZONES_Y = 5


class MacroActions(Enum):
    Up = 1
    Down = 2
    Left = 3
    Right = 4
    Tackle = 5
    Shoot = 6
    Pass = 7

class MacroPlayer():
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y
        self.possession = False
        
    def moveUp(self, max_x, max_y):
        self.y -= 1
        if self.y < 0:
            self.y = 0
            
    def moveDown(self, max_x, max_y):
        self.y += 1
        if self.y > max_y:
            self.y = max_y

    def moveLeft(self, max_x, max_y):
        self.x -= 1
        if self.x < 0:
            self.x = 0

    def moveRight(self, max_x, max_y):
        self.x += 1
        if self.x > max_x:
            self.x = max_x

class State():
    def __init__(self, depth, team : Team, players_home : list[MacroPlayer], players_opponent : list[MacroPlayer], env : Enviornment) -> None:
        self.depth = depth
        self.team = team
        self.players_home = players_home
        self.players_opponent = players_opponent
        self.value = None
        self.children = None
        self.parent = None
        self.env = env

    def getNextState(self, actions : list[MacroActions]):
        
        # create a duplicate state
        oppositeTeam = Team.LEFT
        if self.team == Team.LEFT:
            oppositeTeam = Team.RIGHT
            
        new_state = State(self.depth + 1, oppositeTeam, players_home = copy.deepcopy(self.players_opponent), players_opponent = copy.deepcopy(self.players_home), env = self.env)

        for i, action in enumerate(actions):
            player = new_state.players_home[i]
            if action == MacroActions.Up:
                player.moveUp(NUM_ZONES_X, NUM_ZONES_Y)
            elif action == MacroActions.Down:
                player.moveDown(NUM_ZONES_X, NUM_ZONES_Y)
            elif action == MacroActions.Left:
                player.moveLeft(NUM_ZONES_X, NUM_ZONES_Y)
            elif action == MacroActions.Right:
                player.moveRight(NUM_ZONES_X, NUM_ZONES_Y)
            elif action == MacroActions.Tackle:
                # eq to staying in place
                if player.possession == True:
                    # break out if we already have posession
                    continue
                
                # otherwise
                # confirm that there's another opponent player in the same position with possession
                for opponent in new_state.players_opponent:
                    if opponent.x == player.x and opponent.y == player.y and opponent.possession:
                        # 50% chance of getting possession
                        tackleSuccess = np.random.getrandbits(1)
                        if tackleSuccess:
                            player.possession = False
                            opponent.possession = True
            elif action == MacroActions.Shoot:
                if player.possession == True:
                    source_x = player.x
                    source_y = player.y
                    goal_x = self.env.getGoal(oppositeTeam).pos_x
                    goal_y = self.env.getGoal(oppositeTeam).get_mid()

                    xCheck = range(source_x + 1, goal_x)
                    yCheck = range(source_y + 1, goal_y)

                    shotFailed = False

                    for opponent_player in new_state.players_opponent:
                        dest_x = opponent_player.pos_x
                        dest_y = opponent_player.pos_y


                        if dest_x in xCheck and dest_y in yCheck:
                            # shot fails
                            player.possession = False
                            opponent_player.possession = True
                            shotFailed = True
                            break
                    if shotFailed == False:
                        print("GOAL!")
                        new_state.value = 1
                    break # continue top loop since pass involves both players


            elif action == MacroActions.Pass:
                if i != 0:
                    continue # player 2 can't accept a pass if the player gets possesion this turn

                if player.possession == True:
                    source_x = player.x
                    source_y = player.y
                    pass_x = new_state.players_home[1].x
                    pass_y = new_state.players_home[1].y

                    xCheck = range(source_x + 1, pass_x)
                    yCheck = range(source_y + 1, pass_y)

                    passFailed = False

                    for opponent_player in new_state.players_opponent:
                        dest_x = opponent_player.pos_x
                        dest_y = opponent_player.pos_y


                        if dest_x in xCheck and dest_y in yCheck:
                            # pass fails
                            player.possession = False
                            opponent_player.possession = True
                            passFailed = True
                            break
                    if passFailed == False:
                        new_state.players_home[1].possession = True
                        player.possession = False

                    break # continue top loop since pass involves both players

            else:
                # SHOULD NOT BE HERE
                pass
                
        return new_state

    def print_state(self):
        print("PRINTING STATE")
        print("team: " + str(self.team))
        print("depth: " + str(self.depth)) 
        for i, player in enumerate(self.players_home):
            print("Home player: " + str(i) + " x: " + str(player.x) + " y: " + str(player.y) + " possession: " + str(player.possession))
        for i, player in enumerate(self.players_opponent):
            print("Opponent player: " + str(i) + " x: " + str(player.x) + " y: " + str(player.y) + " possession: " + str(player.possession))


class Agent():
    def __init__(self, team) -> None:
        self.team = team
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
            macro_players_home.append(macro_player)
        for player in players_opp:
            macro_x = int((player.pos_x / env.dim_x) * NUM_ZONES_X)
            macro_y = int((player.pos_y / env.dim_y) * NUM_ZONES_Y)
            macro_player = MacroPlayer(macro_x, macro_y)
            macro_players_opp.append(macro_player)


        stateInit = State(depth = 0, team = self.team, players_home = macro_players_home, players_opponent = macro_players_opp, env = env)
        stateInit.print_state()

        actions = [MacroActions.Up, MacroActions.Up]
        
        newState = stateInit.getNextState(actions)
        newState.print_state()

        actions = []

        return actions