''' 
Use this file to create your custom agent!
'''

from env import Enviornment
from supporting_classes import Actions, Movement, Team
import numpy as np

def getActionMinimizingDistanceToBall(player, ball):
    '''
    Returns the action that minimizes the distance to the ball
    '''
    playerPos_x = player.pos_x
    playerPos_y = player.pos_y

    ballPos_x = ball.pos_x
    ballPos_y = ball.pos_y

    distanceCurr = np.linalg.norm([ballPos_x - playerPos_x, ballPos_y - playerPos_y], 2)

    # test all actions
    actions = [Movement.UP, Movement.DOWN, Movement.LEFT, Movement.RIGHT]
    distances = []

    for action in actions:
        new_x, new_y = playerPos_x, playerPos_y
        if action == Movement.UP:
            new_y -= 1
        elif action == Movement.DOWN:
            new_y += 1
        elif action == Movement.LEFT:
            new_x -= 1
        elif action == Movement.RIGHT:
            new_x += 1
        
        distance = np.linalg.norm([ballPos_x - new_x, ballPos_y - new_y], 2)
        distances.append(distance)
    
    bestAction = actions[np.argmin(distances)]

    return bestAction

def getActionToDest(player, dest):
    '''
    Returns the action that minimizes the distance to the ball
    '''
    playerPos_x = player.pos_x
    playerPos_y = player.pos_y

    dest_x = dest[0]
    dest_y = dest[1]

    distanceCurr = np.linalg.norm([dest_x - playerPos_x, dest_y - playerPos_y], 2)

    # test all actions
    actions = [Movement.UP, Movement.DOWN, Movement.LEFT, Movement.RIGHT]
    distances = []

    for action in actions:
        new_x, new_y = playerPos_x, playerPos_y
        if action == Movement.UP:
            new_y -= 1
        elif action == Movement.DOWN:
            new_y += 1
        elif action == Movement.LEFT:
            new_x -= 1
        elif action == Movement.RIGHT:
            new_x += 1
        
        distance = np.linalg.norm([dest_x - new_x, dest_y - new_y], 2)
        distances.append(distance)
    
    bestAction = actions[np.argmin(distances)]

    return bestAction

def distanceToDefend(player, ball, goal):
    resolution = 1000
    interpolate_x = np.linspace(ball.pos_x, goal[0], resolution)
    interpolate_y = np.linspace(ball.pos_y, goal[1], resolution)
    min_dist = float('inf')
    closest_pt = None
    for i in range(resolution):
        distance = np.linalg.norm([interpolate_x[i] - player.pos_x, interpolate_y[i] - player.pos_y], 2)
        if distance < min_dist:
            min_dist = distance
            closest_pt = (interpolate_x[i], interpolate_y[i])
    return distance, closest_pt

class Agent():
    def __init__(self, team, opp) -> None:
        self.team = team
        self.opponent = opp
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
        * env.testTackle(playerId, team) -> returns True if the tackle is possible
        '''
        actions = []

        posession = env.getBallOwnerTeam()
        opponents = env.getPlayers(self.opponent)

        if posession == self.team:
            players = env.getPlayers(self.team)
            for player in players:
                if player.dribble == True:
                    # try to shoot, otherwise see if you can pass, otherwise move
                    if False:
                        pass
                    if env.testShoot(player.playerId, self.team) == None:
                        actions.append([Actions.SHOOT_BALL, player.playerId, []])
                    else:
                        # try to pass
                        distBetweenPlayers = float('inf')
                        for targetPlayer in players:
                            if targetPlayer.playerId != player.playerId:
                                distBetweenPlayers = np.linalg.norm([player.pos_x - targetPlayer.pos_x, player.pos_y - targetPlayer.pos_y], 2)
                        if distBetweenPlayers > 20:
                            for targetPlayer in players:
                                if targetPlayer.playerId != player.playerId and env.testPass(player.playerId, targetPlayer.playerId) == None:
                                    actions.append([Actions.PASS_BALL, player.playerId, [targetPlayer.playerId]])
                                    break
                        else:
                            dir = getActionToDest(player, env.getGoal(self.team).get_mid())
                            actions.append([Actions.MOVE, player.playerId, [dir]])
                else:

                    dir = getActionToDest(player, env.getGoal(self.team).get_mid())
                    actions.append([Actions.MOVE, player.playerId, [dir]])


        elif posession == None:
            # dash to ball
            players = env.getPlayers(self.team)
            for player in players:
                bestAction = getActionMinimizingDistanceToBall(player, env.ball)
                actions.append([Actions.MOVE, player.playerId, [bestAction]])

        elif posession != self.team:
            """
            1. tackle ball if possible
            2. find agent closest to ball
            3. find agent outside of (2) closest to line between ball and goal
            4. all other agents go towards opponent 
            """
            players = env.getPlayers(self.team)
            ball = env.getBallPosition()
            minDistToBall = float('inf')
            playerClosestToBall = None
            for player in players:
                distToBall = np.linalg.norm([ball[0] - player.pos_x, ball[1] - player.pos_y], 2)
                if distToBall < minDistToBall:
                    minDistToBall = distToBall
                    playerClosestToBall = player
            if env.testTackle(playerClosestToBall.playerId, self.team):
                actions.append([Actions.TACKLE_BALL, playerClosestToBall.playerId, []])
            else:
                moveToBallAction = getActionMinimizingDistanceToBall(playerClosestToBall, env.ball)
                actions.append([Actions.MOVE, playerClosestToBall.playerId, [moveToBallAction]])

            minDistToDefend = float('inf')
            defenseBot = None
            defenseSpot = None
            for player in players:
                if player == playerClosestToBall:
                    continue
                distToDefend, closestDefenseSpot = distanceToDefend(player, env.ball, env.getGoal(self.opponent).get_mid())
                if distToDefend < minDistToDefend:
                    distToDefend = minDistToDefend
                    defenseBot = player
                    defenseSpot = closestDefenseSpot
            defendAction = getActionToDest(defenseBot, defenseSpot)
            actions.append([Actions.MOVE, defenseBot.playerId, [defendAction]])
            
            for player in players:
                if player == playerClosestToBall or player == defenseBot:
                    continue
                minDistToOpp = float('inf')
                oppToFind = None
                for opponent in opponents:
                    distToOpp = np.linalg.norm([opponent.pos_x - player.pos_x, opponent.pos_y - player.pos_y], 2)
                    if distToOpp < minDistToOpp:
                        minDistToOpp = distToOpp
                        oppToFind = opponent
                moveToOppAction = getActionToDest(player, (oppToFind.curr_x, oppToFind.curr_y))
                actions.append([Actions.MOVE, player.playerId, [moveToOppAction]])


        # print(actions)
        # print("\n")
        return actions