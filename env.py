import numpy as np
import cv2 as cv
from supporting_classes import *

class Enviornment:
    def __init__(self) -> None:
        self.numPlayers = 0
        self.listOfPlayers = []
        self.listOfGoals = []
        self.ball = None
        self.gameRunning = True

        self.dim_x = 1000
        self.dim_y = 500

    def _init_ballAndGoals(self):
        # create goals
        mid_y = int(self.dim_y/2)
        top_y = mid_y + 100
        bottom_y = mid_y - 100
        goal1 = Goal(bottom_y, top_y, 0, Team.RIGHT)
        goal2 = Goal(bottom_y, top_y, self.dim_x - 10, Team.LEFT)

        self.listOfGoals.append(goal1)
        self.listOfGoals.append(goal2)

        self.ball = Ball(int(self.dim_x/2), int(self.dim_y/2))

    def init_random_game(self, numPlayers):
        self.numPlayers = numPlayers

        # create players
        for i in range(numPlayers):
            rand_x_1 = np.random.randint(0, self.dim_x/2)
            rand_y_1 = np.random.randint(0, self.dim_y)
            rand_x_2 = np.random.randint(self.dim_x/2, self.dim_x)
            rand_y_2 = np.random.randint(0, self.dim_y)

            self.listOfPlayers.append(Player(rand_x_1, rand_y_1, 2*i, Team.LEFT))
            self.listOfPlayers.append(Player(rand_x_2, rand_y_2, (2*i) + 1, Team.RIGHT))
        
        self._init_ballAndGoals()

    # a more 'balanced' game
    def init_2player_game(self):
        self.numPlayers = 2

        # create players
        x_1 = int(self.dim_x/2) - 200
        x_2 = int(self.dim_x/2) + 200
        y_1 = int(self.dim_y/2) - 200
        y_2 = int(self.dim_y/2) + 200

        self.listOfPlayers.append(Player(x_1, y_1, 0, Team.LEFT))
        self.listOfPlayers.append(Player(x_1, y_2, 1, Team.LEFT))
        self.listOfPlayers.append(Player(x_2, y_1, 2, Team.RIGHT))
        self.listOfPlayers.append(Player(x_2, y_2, 3, Team.RIGHT))
        
        self._init_ballAndGoals()


    def drawEnviornment(self, time):
        img = np.zeros((self.dim_y, self.dim_x, 3), np.uint8)

        for player in self.listOfPlayers:
            if player.playerTeam == Team.RIGHT:
                cv.circle(img, (player.pos_x, player.pos_y), 5, (0, 0, 255), -1)
            else:
                cv.circle(img, (player.pos_x, player.pos_y), 5, (255, 0, 0), -1)

        for goal in self.listOfGoals:
            cv.rectangle(img, (goal.pos_x, goal.pos_y_top), (goal.pos_x + 10, goal.pos_y_bottom), (0, 255, 0), -1)

        cv.circle(img, (self.ball.pos_x, self.ball.pos_y), 2, (255, 255, 255), -1)
        cv.imshow("game", img)
        cv.waitKey(time)

    ####### Getters for the agent #######

    def getPlayers(self, team):
        players = []
        for player in self.listOfPlayers:
            if player.playerTeam == team:
                players.append(player)
        return players
    
    def getOpponents(self, team):
        players = []
        for player in self.listOfPlayers:
            if player.playerTeam != team:
                players.append(player)
        return players

    def getBallPosition(self):
        return (self.ball.pos_x, self.ball.pos_y)
    
    def getBallOwner(self):
        return self.ball.playerId
    
    def getBallOwnerTeam(self):
        if self.ball.playerId == None:
            return None

        return self.listOfPlayers[self.ball.playerId].playerTeam

    def testPass(self, playerId, targetPlayerId):
        targetPlayer = self.listOfPlayers[targetPlayerId]
        return self.listOfPlayers[playerId].test_passBall(self.ball, targetPlayer, self.listOfPlayers)

    def testShoot(self, playerId, team):
        goal = None
        for g in self.listOfGoals:
            if g.goalTeam != team:
                goal = g
                break
        
        # print("Env test shoot")

        return self.listOfPlayers[playerId].test_shootToGoal(self.ball, goal, self.listOfPlayers)

    def testTackle(self, playerId, team):
        return self.listOfPlayers[playerId].test_tackleBall(self.ball, self.listOfPlayers)

    ####### Player actions #######

    def _movePlayer(self, playerID, dir):
        self.listOfPlayers[playerID].move(dir, self.listOfPlayers, self.ball, self.dim_x, self.dim_y)
    
    def _playerShootBall(self, playerID):
        player = self.listOfPlayers[playerID]
        goal = None
        for g in self.listOfGoals:
            if g.goalTeam != player.playerTeam:
                goal = g
                break
        
        success = player.shootToGoal(self.ball, goal, self.listOfPlayers)

        if success:
            self.gameRunning = False
            print("GOAL, Game over, winning team: ", player.playerTeam)

    def _passBall(self, playerID, targetPlayerID):
        targetPlayer = self.listOfPlayers[targetPlayerID]
        self.listOfPlayers[playerID].passBall(self.ball, targetPlayer, self.listOfPlayers)

    def execute(self, action, playerId, args):
        if action == Actions.MOVE:
            self._movePlayer(playerId, args[0])
        if action == Actions.SHOOT_BALL:
            self._playerShootBall(playerId)
        if action == Actions.PASS_BALL:
            self._passBall(playerId, args[0])
        if action == Actions.TACKLE_BALL:
            self._tackleBall(playerId)
