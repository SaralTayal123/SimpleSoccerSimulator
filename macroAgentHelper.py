from env import Enviornment
from supporting_classes import Actions, Movement, Team
from enum import Enum
import copy
import numpy as np
import random
from collections import defaultdict

NUM_ZONES_X = 20
NUM_ZONES_Y = 10
MACRO_SHOOT_L1_RANGE = 2

NUM_PLAYERS = 2
MAX_DEPTH = (NUM_ZONES_X + NUM_ZONES_Y) * 2
VALUE_OF_TIME = 100
EXPLORATION_TENDENCY = 0

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
    def __init__(self, depth, agent_team : Team, team : Team, players_home, players_opponent, env : Enviornment) -> None:
        self.depth = depth
        self.team = team
        self.players_home = players_home
        self.players_opponent = players_opponent
        self.value = 0
        self.children = None
        self.parent = None
        self.env = env
        self.agent_team = agent_team
        self.ball_start = env.getBallPosition()
        self.terminal = False
        self.oppositeTeam = Team.LEFT
        if self.team == Team.LEFT:
            self.oppositeTeam = Team.RIGHT

        self.init_ball_grabbed = False
        for player in self.players_home:
            if player.possession:
                self.init_ball_grabbed = True
                break
        if not self.init_ball_grabbed:
            for player in self.players_opponent:
                if player.possession:
                    self.init_ball_grabbed = True
    
    def __eq__(self, other):
        return self.players_home == other.players_home and self.players_opponent == other.players_opponent and self.team == other.team
        
    def testLegality(self, action, player):
        if action == MacroActions.Up:
            if player.y <= 0:
                return False
            for opponent in self.players_opponent:
                if opponent.y == player.y - 1 and player.x == opponent.x:
                    return False
            for teammate in self.players_home:
                if teammate.y == player.y - 1 and player.x == teammate.x:
                    return False
        elif action == MacroActions.Down:
            if player.y >= NUM_ZONES_Y - 1:
                return False
            for opponent in self.players_opponent:
                if opponent.y == player.y + 1 and player.x == opponent.x:
                    return False
            for teammate in self.players_home:
                if teammate.y == player.y + 1 and player.x == teammate.x:
                    return False
        elif action == MacroActions.Left:
            if player.x <= 0:
                return False
            for opponent in self.players_opponent:
                if opponent.y == player.y and player.x - 1 == opponent.x:
                    return False
            for teammate in self.players_home:
                if teammate.y == player.y and player.x - 1 == teammate.x:
                    return False
        elif action == MacroActions.Right:
            if player.x >= NUM_ZONES_X - 1:
                return False
            for opponent in self.players_opponent:
                if opponent.y == player.y and player.x + 1 == opponent.x:
                    return False
            for teammate in self.players_home:
                if teammate.y == player.y and player.x + 1 == teammate.x:
                    return False
        elif action == MacroActions.Tackle:
            ballZoneX = int((self.env.getBallPosition()[0] / self.env.dim_x) * NUM_ZONES_X)
            ballZoneY = int((self.env.getBallPosition()[1] / self.env.dim_y) * NUM_ZONES_Y)

            dist_to_ball = np.linalg.norm([ballZoneY - player.y, ballZoneX - player.x], 2)

            if dist_to_ball > 2:
                return False

            for team_player in self.players_home:
                if team_player.possession:
                    return False
            for opponent_player in self.players_opponent:
                if opponent_player.possession:
                    return True
            return False
        elif action == MacroActions.Shoot:
            if player.possession == True:
                source_x = player.x
                source_y = player.y
                goal_x = self.env.getGoal(self.team).get_mid()[0]
                goal_y = self.env.getGoal(self.team).get_mid()[1]
                goal_zone_x = int((goal_x / self.env.dim_x) * NUM_ZONES_X)
                goal_zone_y = int((goal_y / self.env.dim_y) * NUM_ZONES_Y)

                manhattan_to_goal = np.sum(np.abs(goal_zone_y - source_y) + np.abs(goal_zone_x - source_x))
                if manhattan_to_goal > MACRO_SHOOT_L1_RANGE:
                    return False

                xCheck = range(source_x, goal_zone_x)
                yCheck = range(source_y, goal_zone_y)

                for opponent_player in self.players_opponent:
                    dest_x = opponent_player.x
                    dest_y = opponent_player.y

                    if dest_x in xCheck and dest_y in yCheck:
                        # shot fails
                        return False
                for friend in self.players_home:
                    dest_x = friend.x
                    dest_y = friend.y

                    if dest_x in xCheck and dest_y in yCheck:
                        # shot fails
                        return False
            else:
                return False
        elif action == MacroActions.Pass:
            player1 = self.players_home[0]
            player2 = self.players_home[1]
            if player == player1 and player1.possession == True:
                source_x = player1.x
                source_y = player1.y
                pass_x = player2.x
                pass_y = player2.y
            elif player == player2 and player2.possession == True:
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
                    return False
        else:
            raise Exception("invalid macro action!")

        return True

    def getPossibleActions(self):
        allActions = []
        
        # generate all permutations of actions
        for action in MacroActions:
            if not self.testLegality(action, self.players_home[0]):
                continue
            for action2 in MacroActions:
                if not self.testLegality(action2, self.players_home[1]):
                    continue
                allActions.append([action, action2])

        return allActions

    def getHeuristicAction(self):
        actionList = []
        teamPossession = False
        for agent in self.players_home:
            if agent.possession:
                teamPossession = True

        for agent in self.players_home:
            otherAgent = None
            for test in self.players_home:
                if test != agent:
                    otherAgent = test
                    break
            values = [0 for _ in range(len(MacroActions)+1)]
            if agent.possession:
                values[MacroActions.Tackle.value] = 0
                values[MacroActions.Shoot.value] = 100000
                (_, goal_mid_y) = self.env.getGoal(self.team).get_mid()
                goal_zone_y = int((goal_mid_y / self.env.dim_y) * NUM_ZONES_Y)
                if agent.y < goal_zone_y:
                    values[MacroActions.Up.value] = 0
                    values[MacroActions.Down.value] = 100
                elif agent.y > goal_zone_y:
                    values[MacroActions.Up.value] = 100
                    values[MacroActions.Down.value] = 0
                else:
                    values[MacroActions.Up.value] = 0
                    values[MacroActions.Down.value] = 0

                values[MacroActions.Pass.value] = 10
                if self.team == Team.LEFT:
                    values[MacroActions.Left.value] = 0
                    values[MacroActions.Right.value] = 100

                    for teammate in self.players_home:
                        if teammate.x > agent.x:
                            values[MacroActions.Pass.value] *= 1000
                            break
                else:
                    values[MacroActions.Left.value] = 100
                    values[MacroActions.Right.value] = 0

                    for teammate in self.players_home:
                        if teammate.x < agent.x:
                            values[MacroActions.Pass.value] *= 100
                            break
            else:
                # I don't have the ball
                values[MacroActions.Pass.value] = 0
                values[MacroActions.Shoot.value] = 0

                if teamPossession:
                    # move to goal
                    values[MacroActions.Tackle.value] = 0
                    (_, goal_mid_y) = self.env.getGoal(self.team).get_mid()
                    goal_zone_y = int((goal_mid_y / self.env.dim_y) * NUM_ZONES_Y)
                    if agent.y < goal_zone_y:
                        values[MacroActions.Up.value] = 0
                        values[MacroActions.Down.value] = 10
                    elif agent.y > goal_zone_y:
                        values[MacroActions.Up.value] = 10
                        values[MacroActions.Down.value] = 0
                    else:
                        values[MacroActions.Up.value] = 0
                        values[MacroActions.Down.value] = 0

                    if self.agent_team == Team.LEFT:
                        values[MacroActions.Left.value] = 0
                        values[MacroActions.Right.value] = 10
                    else:
                        values[MacroActions.Left.value] = 10
                        values[MacroActions.Right.value] = 0

                    # move away from teammate
                    # if agent.x < otherAgent.x:
                    #     values[MacroActions.Left.value] *= 5
                    #     values[MacroActions.Left.value] += 10
                    # else:
                    #     values[MacroActions.Right.value] *= 5
                    #     values[MacroActions.Right.value] += 10

                    # if agent.y < otherAgent.y:
                    #     values[MacroActions.Up.value] *= 5
                    #     values[MacroActions.Up.value] += 10
                    # else:
                    #     values[MacroActions.Down.value] *= 5
                    #     values[MacroActions.Down.value] += 10
                else:
                    # move to ball
                    values[MacroActions.Tackle.value] = 100000
                    
                    (ball_x, ball_y) = self.env.getBallPosition()
                    ball_zone_x = int((ball_x / self.env.dim_x) * NUM_ZONES_X)
                    ball_zone_y = int((ball_y / self.env.dim_y) * NUM_ZONES_Y)
                    if agent.x < ball_zone_x:
                        values[MacroActions.Right.value] = 100
                        values[MacroActions.Left.value] = 0
                    elif agent.x > ball_zone_x:
                        values[MacroActions.Right.value] = 0
                        values[MacroActions.Left.value] = 100
                    else:
                        values[MacroActions.Right.value] = 0
                        values[MacroActions.Left.value] = 0

                    if agent.y < ball_zone_y:
                        values[MacroActions.Up.value] = 0
                        values[MacroActions.Down.value] = 100
                    elif agent.y > ball_zone_y:
                        values[MacroActions.Up.value] = 100
                        values[MacroActions.Down.value] = 0
                    else:
                        values[MacroActions.Up.value] = 0
                        values[MacroActions.Down.value] = 0
            for action in MacroActions:
                if self.testLegality(action, agent):
                    values[action.value] += EXPLORATION_TENDENCY
                else:
                    values[action.value] = 0

            actionList.append(random.choices([action for action in MacroActions], \
                                             weights=values[1:], k=1)[0])
        return actionList

    def getNextState(self, actions):
        
        # create a duplicate state

        # for mcts searcher since it wraps actions as a double list
        actions = actions[0]

        # defining constants to put into newState at the end o
        players_home = copy.deepcopy(self.players_home)
        players_opponent = copy.deepcopy(self.players_opponent)
        # new_value = self.value
        new_value = 0
        new_state_terminal = False

        for i, action in enumerate(actions):
            player = players_home[i]
            other_player = players_home[1-i]
            if action == MacroActions.Up:
                player.moveUp(NUM_ZONES_X, NUM_ZONES_Y)
                if not self.init_ball_grabbed and player.x == self.ball_start[0] and player.y == self.ball_start[1]:
                    player.possession = True
                # new_value += -1
            elif action == MacroActions.Down:
                player.moveDown(NUM_ZONES_X, NUM_ZONES_Y)
                if not self.init_ball_grabbed and player.x == self.ball_start[0] and player.y == self.ball_start[1]:
                    player.possession = True
                # new_value += -1
            elif action == MacroActions.Left:
                player.moveLeft(NUM_ZONES_X, NUM_ZONES_Y)
                if not self.init_ball_grabbed and player.x == self.ball_start[0] and player.y == self.ball_start[1]:
                    player.possession = True
                # new_value += -1
            elif action == MacroActions.Right:
                player.moveRight(NUM_ZONES_X, NUM_ZONES_Y)
                if not self.init_ball_grabbed and player.x == self.ball_start[0] and player.y == self.ball_start[1]:
                    player.possession = True
                # new_value += -1
            elif action == MacroActions.Tackle:
                # eq to staying in place
                if player.possession == True:
                    # break out if we already have posession
                    continue
                
                # otherwise
                # confirm that there's another opponent player in the same position with possession
                for opponent in players_opponent:
                    dist_to_opp = np.linalg.norm([opponent.x - player.x, opponent.y - player.y], 2)
                    if dist_to_opp <= 2 and opponent.possession:
                        # 50% chance of getting possession
                        tackleSuccess = np.random.randint(0,10) < 3
                        if tackleSuccess:
                            player.possession = False
                            opponent.possession = True
            elif action == MacroActions.Shoot:
                if player.possession == True:
                    source_x = player.x
                    source_y = player.y
                    goal_x = self.env.getGoal(self.team).get_mid()[0]
                    goal_y = self.env.getGoal(self.team).get_mid()[1]
                    goal_zone_x = int((goal_x / self.env.dim_x) * NUM_ZONES_X)
                    goal_zone_y = int((goal_y / self.env.dim_y) * NUM_ZONES_Y)

                    xCheck = range(source_x + 1, goal_zone_x)
                    yCheck = range(source_y + 1, goal_zone_y)

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
                            new_value = -1 * np.exp(-1 * self.depth / MAX_DEPTH * VALUE_OF_TIME)
                            # new_value += -2 * MAX_DEPTH
                            new_state_terminal = True
                        else:
                            new_value = 1 * np.exp(-1 * self.depth / MAX_DEPTH * VALUE_OF_TIME)
                            # new_value += 2 * MAX_DEPTH
                            new_state_terminal = True
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
                    break

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
                
        
        new_state = State(self.depth + 1, self.agent_team, self.oppositeTeam, players_home = players_opponent, players_opponent = players_home, env = self.env)
        new_state.value = new_value
        new_state.terminal = new_state_terminal
        if new_state.depth > MAX_DEPTH:
            # new_state.value = -4 * MAX_DEPTH
            new_state.value = 0
            new_state.terminal = True
        return new_state

    def print_state(self):
        print("PRINTING STATE")
        print("team: " + str(self.team))
        print("depth: " + str(self.depth)) 
        for i, player in enumerate(self.players_home):
            print("Home player: " + str(i) + " x: " + str(player.x) + " y: " + str(player.y) + " possession: " + str(player.possession))
        for i, player in enumerate(self.players_opponent):
            print("Opponent player: " + str(i) + " x: " + str(player.x) + " y: " + str(player.y) + " possession: " + str(player.possession))

