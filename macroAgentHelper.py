from env import Enviornment
from supporting_classes import Actions, Movement, Team
from enum import Enum
import copy
import numpy as np

NUM_ZONES_X = 10
NUM_ZONES_Y = 5

NUM_PLAYERS = 2
MAX_DEPTH = 200

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
    def __init__(self, depth, agent_team : Team, team : Team, players_home : list[MacroPlayer], players_opponent : list[MacroPlayer], env : Enviornment) -> None:
        self.depth = depth
        self.team = team
        self.players_home = players_home
        self.players_opponent = players_opponent
        self.value = None
        self.children = None
        self.parent = None
        self.env = env
        self.agent_team = agent_team
    
    def __eq__(self, other):
        return self.players_home == other.players_home and self.players_opponent == other.players_opponent and self.team == other.team
        
    def testLegality(self, action, player):
        oppositeTeam = Team.LEFT
        if self.team == Team.LEFT:
            oppositeTeam = Team.RIGHT
        if action == MacroActions.Up:
            if player.y == 0:
                return False
        elif action == MacroActions.Down:
            if player.y == NUM_ZONES_Y - 1:
                return False
        elif action == MacroActions.Left:
            if player.x == 0:
                return False
        elif action == MacroActions.Right:
            if player.x == NUM_ZONES_X - 1:
                return False
        elif action == MacroActions.Tackle:
            ballZoneX = int((self.env.getBallPosition()[0] / self.env.dim_x) * NUM_ZONES_X)
            ballZoneY = int((self.env.getBallPosition()[1] / self.env.dim_y) * NUM_ZONES_Y)

            if not (ballZoneX == player.x and ballZoneY == player.y and player.possession != self.team):
                return False
        elif action == MacroActions.Shoot:
            if player.possession == True:
                source_x = player.x
                source_y = player.y
                goal_x = self.env.getGoal(oppositeTeam).get_mid()[0]
                goal_y = self.env.getGoal(oppositeTeam).get_mid()[1]

                xCheck = range(source_x + 1, goal_x)
                yCheck = range(source_y + 1, goal_y)

                for opponent_player in self.players_opponent:
                    dest_x = opponent_player.x
                    dest_y = opponent_player.y

                    if dest_x in xCheck and dest_y in yCheck:
                        # shot fails
                        player.possession = False
                        opponent_player.possession = True
                        return False
            else:
                return False
        elif action == MacroActions.Pass:
            player1 = self.players_home[0]
            player2 = self.players_home[1]
            if player1.possession == True:
                source_x = player1.x
                source_y = player1.y
                pass_x = player2.x
                pass_y = player2.y
            elif player2.possession == True:
                source_x = player2.x
                source_y = player2.y
                pass_x = player1.x
                pass_y = player1.y
            else:
                return False

            xCheck = range(source_x + 1, pass_x)
            yCheck = range(source_y + 1, pass_y)

            for opponent_player in self.players_opponent:
                dest_x = opponent_player.x
                dest_y = opponent_player.y


                if dest_x in xCheck and dest_y in yCheck:
                    # pass fails
                    player.possession = False
                    opponent_player.possession = True
                    return False

        return True

    def getPossibleActions(self) -> list[list[MacroActions]]:
        allActions = []
        
        # generate all permutations of actions
        for action in MacroActions:
            if not self.testLegality(action, self.players_home[0]):
                continue
            for action2 in MacroActions:
                if not self.testLegality(action2, self.players_home[1]):
                    continue
                if action == MacroActions.Pass and action2 != MacroActions.Pass or action != MacroActions.Pass and action2 == MacroActions.Pass:
                    continue
                allActions.append([action, action2])

        return allActions


    def getNextState(self, actions : list[MacroActions]):
        
        # create a duplicate state
        oppositeTeam = Team.LEFT
        if self.team == Team.LEFT:
            oppositeTeam = Team.RIGHT

        # for mcts searcher since it wraps actions as a double list
        actions = actions[0]

        # defining constants to put into newState at the end o
        players_home = copy.deepcopy(self.players_home)
        players_opponent = copy.deepcopy(self.players_opponent)
        new_value = None

        for i, action in enumerate(actions):
            player = players_home[i]
            other_player = players_home[1-i]
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
                for opponent in players_opponent:
                    if opponent.x == player.x and opponent.y == player.y and opponent.possession:
                        # 50% chance of getting possession
                        tackleSuccess = np.random.randint(0,2)
                        if tackleSuccess:
                            player.possession = False
                            opponent.possession = True
            elif action == MacroActions.Shoot:
                if player.possession == True:
                    source_x = player.x
                    source_y = player.y
                    goal_x = self.env.getGoal(oppositeTeam).get_mid()[0]
                    goal_y = self.env.getGoal(oppositeTeam).get_mid()[1]

                    xCheck = range(source_x + 1, goal_x)
                    yCheck = range(source_y + 1, goal_y)

                    shotFailed = False

                    for opponent_player in players_opponent:
                        dest_x = opponent_player.x
                        dest_y = opponent_player.y


                        if dest_x in xCheck and dest_y in yCheck:
                            # shot fails
                            player.possession = False
                            opponent_player.possession = True
                            shotFailed = True
                            break
                    if shotFailed == False:
                        if (self.team != self.agent_team):
                            new_value = -1 * np.exp(-1 * self.depth)
                        else:
                            new_value = 1 * np.exp(-1 * self.depth)
                    break # continue top loop since pass involves both players


            elif action == MacroActions.Pass:
                if i != 0:
                    continue # player 2 can't accept a pass if the player gets possesion this turn

                passFailed = False
                if player.possession == True:
                    source_x = player.x
                    source_y = player.y
                    pass_x = other_player.x
                    pass_y = other_player.y
                elif other_player.possession == True:
                    source_x = other_player.x
                    source_y = other_player.y
                    pass_x = player.x
                    pass_y = player.y
                else:
                    passFailed = True

                xCheck = range(source_x + 1, pass_x)
                yCheck = range(source_y + 1, pass_y)

                for opponent_player in players_opponent:
                    dest_x = opponent_player.x
                    dest_y = opponent_player.y


                    if dest_x in xCheck and dest_y in yCheck:
                        # pass fails
                        player.possession = False
                        opponent_player.possession = True
                        passFailed = True
                        break
                if passFailed == False:
                    players_home[1].possession = True
                    player.possession = False

                break # continue top loop since pass involves both players

            else:
                raise Exception("Invalid action!", action)
            

            if action == MacroActions.Up or action == MacroActions.Down or action == MacroActions.Left or action == MacroActions.Right:
                if (self.env.getBallOwner() == None):
                    ballZoneX = int((self.env.getBallPosition()[0] / self.env.dim_x) * NUM_ZONES_X)
                    ballZoneY = int((self.env.getBallPosition()[1] / self.env.dim_y) * NUM_ZONES_Y)

                    if (ballZoneX == player.x and ballZoneY == player.y):
                        player.possession = True
                
        
        new_state = State(self.depth + 1, self.agent_team, oppositeTeam, players_home = players_opponent, players_opponent = players_home, env = self.env)
        new_state.value = new_value
        if new_state.depth > MAX_DEPTH:
            new_state.value = 0
        return new_state

    def print_state(self):
        print("PRINTING STATE")
        print("team: " + str(self.team))
        print("depth: " + str(self.depth)) 
        for i, player in enumerate(self.players_home):
            print("Home player: " + str(i) + " x: " + str(player.x) + " y: " + str(player.y) + " possession: " + str(player.possession))
        for i, player in enumerate(self.players_opponent):
            print("Opponent player: " + str(i) + " x: " + str(player.x) + " y: " + str(player.y) + " possession: " + str(player.possession))

