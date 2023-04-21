''' 
Use this file to create your custom agent!
'''

from env import Enviornment
from supporting_classes import Actions, Movement, Team

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

        players = env.getPlayers(self.team)

        actions = []
        for player in players:
            actions.append((Actions.MOVE, player.playerId, [Movement.UP]))

        return actions