import numpy as np
from enum import Enum

class Actions(Enum):
    MOVE = 0
    PASS_BALL = 4
    SHOOT_BALL = 5
    TACKLE_BALL = 6

class Movement(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

class Team(Enum):
    RIGHT = 0
    LEFT = 1

class Ball:
    def __init__(self, pos_x, pos_y) -> None:
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.captured = False
        self.playerId = None

    def move(self, pos_x, pos_y):
        self.pos_x = pos_x
        self.pos_y = pos_y

class Goal:
    def __init__(self, pos_y_top, pos_y_bottom, pos_x, goalTeam) -> None:
        self.pos_y_top = pos_y_top
        self.pos_y_bottom = pos_y_bottom
        self.pos_x = pos_x
        self.goalTeam = goalTeam

    def get_mid(self):
        goalMid = int(self.pos_y_bottom + (self.pos_y_top - self.pos_y_bottom) / 2)
        return (self.pos_x, goalMid)


class Player:
    def __init__(self, pos_x, pos_y, playerId, playerTeam) -> None:
        self.playerId = playerId
        self.playerTeam = playerTeam
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.dribble = False

    def captureBall(self, ball):
        distToBall = np.linalg.norm([ball.pos_x - self.pos_x, ball.pos_y - self.pos_y], 2)
        if distToBall < 5 and self.dribble == False and ball.captured == False:
            self.dribble = True
            ball.captured = True
            ball.playerId = self.playerId
        
    def test_tackleBall(self, ball, listOfPlayers):
        if self.dribble == True:
            return False

        distanceToBall = np.linalg.norm([ball.pos_x - self.pos_x, ball.pos_y - self.pos_y], 2)

        if distanceToBall < 5:
            return True
        return False

    def tackleBall(self, ball, listOfPlayers):
        if self.test_tackleBall(ball, listOfPlayers):
            tackleSuccess = np.random.getrandbits(1)
            if tackleSuccess:
                listOfPlayers[ball.playerHost].dribble = False
                ball.playerId = self.playerId
                self.dribble = True

    
    def move(self, dir, listOfPlayers, ball, dim_x, dim_y):
        proposed_x = self.pos_x
        proposed_y = self.pos_y

        if dir == Movement.UP:
            proposed_y -= 1
        elif dir == Movement.DOWN:
            proposed_y += 1
        elif dir == Movement.LEFT:
            proposed_x -= 1
        elif dir == Movement.RIGHT:
            proposed_x += 1


        # check if the proposed move is valid
        valid = True
        for player in listOfPlayers:
            if player != self:
                if proposed_x == player.pos_x and proposed_y == player.pos_y:
                    valid = False
                    break
        
        if proposed_x < 0 or proposed_x >= dim_x or proposed_y < 0 or proposed_y >= dim_y:
            valid = False
        
        if valid:
            self.pos_x = proposed_x
            self.pos_y = proposed_y

            # try to capture the ball
            self.captureBall(ball)
        
            if self.dribble == True:
                ball.pos_x = self.pos_x
                ball.pos_y = self.pos_y

    def test_passBall(self, ball, destPlayer, listOfPlayers):

        source_x = self.pos_x
        source_y = self.pos_y
        dest_x = destPlayer.pos_x
        dest_y = destPlayer.pos_y
        dist_x = dest_x - source_x
        dist_y = dest_y - source_y

        # 8 connected distance between source and destination
        # distance = min(np.abs(dist_x), np.abs(dist_y)) * np.sqrt(2) + max(np.abs(dist_x), np.abs(dist_y)) - min(np.abs(dist_x), np.abs(dist_y))

        # loop through all the players and see how close they are to the ball along the entire path
        for player in listOfPlayers:
            if player != self and player != destPlayer:
                resolution = 100
                interpolate_x = np.linspace(source_x, dest_x, resolution)
                interpolate_y = np.linspace(source_y, dest_y, resolution)
                for i in range(resolution):
                    distance = np.linalg.norm([interpolate_x[i] - player.pos_x, interpolate_y[i] - player.pos_y], 2)
                    if distance < 5:
                        return player
        return None
    
    def passBall(self, ball, destPlayer, listOfPlayers):
        assert(self.dribble == True)
    
        print("passing ball from player " + str(self.playerId) + " to player " + str(destPlayer.playerId))

        playerIntercept = self.test_passBall(ball, destPlayer, listOfPlayers)

        passWorked = False

        # pass failed
        if playerIntercept == None:
            playerIntercept = destPlayer
            passWorked = True

        
        # process new ball ownership
        self.dribble = False
        playerIntercept.dribble = True
        ball.playerId = playerIntercept.playerId
        ball.pos_x = playerIntercept.pos_x
        ball.pos_y = playerIntercept.pos_y

        return passWorked

    def test_shootToGoal(self, ball, goal, listOfPlayers):
        assert(self.dribble == True)

        for player in listOfPlayers:
            if player != self:
                resolution = 1000
                interpolate_x = np.linspace(self.pos_x, goal.pos_x, resolution)
                goalMid = goal.pos_y_bottom + (goal.pos_y_top - goal.pos_y_bottom) / 2
                goalMid = int(goalMid)
                interpolate_y = np.linspace(self.pos_y, goalMid, resolution)
                for i in range(resolution):
                    distance = np.linalg.norm([interpolate_x[i] - player.pos_x, interpolate_y[i] - player.pos_y], 2)
                    if distance < 5:
                        print("Player in the way, shot on goal failed")
                        return player
        
        # pass worked
        return None

    def shootToGoal(self, ball, goal, listOfPlayers):
        assert(self.dribble == True)

        playerIntercept = self.test_shootToGoal(ball, goal, listOfPlayers)

        # pass failed
        if playerIntercept != None:
            playerIntercept.dribble = True
            ball.playerId = playerIntercept.playerId
            self.dribble = False
            return False

        # pass worked, end round
        return True