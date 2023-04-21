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
        * env.testTackle(playerId, team) -> returns True if the tackle is possible
        '''
        actions = []

        posession = env.getBallOwnerTeam()

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
                        for targetPlayer in players:
                            if targetPlayer.playerId != player.playerId and env.testPass(player.playerId, targetPlayer.playerId) == None:
                                actions.append([Actions.PASS_BALL, player.playerId, [targetPlayer.playerId]])
                                break
                        else:
                            dirOptions = [Movement.UP, Movement.DOWN, Movement.LEFT, Movement.RIGHT]
                            dir = np.random.choice(dirOptions)
                            actions.append([Actions.MOVE, player.playerId, [dir]])
                else:
                    dirOptions = [Movement.UP, Movement.DOWN, Movement.LEFT, Movement.RIGHT]
                    dir = np.random.choice(dirOptions)
                    actions.append([Actions.MOVE, player.playerId, [dir]])


        elif posession == None:
            # dash to ball
            players = env.getPlayers(self.team)
            for player in players:
                bestAction = getActionMinimizingDistanceToBall(player, env.ball)
                actions.append([Actions.MOVE, player.playerId, [bestAction]])

        elif posession != self.team:
            # dash to ball
            players = env.getPlayers(self.team)
            for player in players:
                if env.testTackle(player.playerId, self.team):
                    actions.append([Actions.TACKLE_BALL, player.playerId, []])
                else:
                    bestAction = getActionMinimizingDistanceToBall(player, env.ball)
                    actions.append([Actions.MOVE, player.playerId, [bestAction]])


        # print(actions)
        # print("\n")
        return actions