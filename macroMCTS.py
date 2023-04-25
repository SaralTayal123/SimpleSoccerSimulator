from mctsCopy import mcts
from supporting_classes import Team
import math
from macroAgentHelper import State

class MCTSAction():
    def __init__(self, game_action):
        self.game_action = game_action # game_action should be a deep copy

    def __eq__(self, other):
        return self.game_action == other.game_action

    def __hash__(self):
        return hash(str(self.game_action))

    def to_string(self):
        return str(self.game_action)

class MCTSState():
    def __init__(self, game_state : State):
        self.game_state = game_state # game_state should be a deep copy

    def getCurrentPlayer(self):
        # 1 for maximiser, -1 for minimiser
        if (self.game_state.team == Team.LEFT):
            # team left is always the maximiser
            return 1
        else:
            return -1

    def getPossibleActions(self):
        game_action_list = self.game_state.getPossibleActions()
        # print("Pre ")
        # print(game_action_list)
        mcts_action_list = []
        for action in game_action_list:
            mcts_action_list.append(MCTSAction(action))
        # print([action.to_string() for action in mcts_action_list])
        # print("post")
        return mcts_action_list

    def takeAction(self, action : MCTSAction):
        return MCTSState(self.game_state.getNextState([action.game_action]))

    def isTerminal(self):
        return self.game_state.terminal

    def getReward(self):
        # only needed for terminal states
        return self.game_state.value

    def __eq__(self, other):
        return self.game_state == other.game_state

def heuristicPolicy(state : MCTSState):
    # print("START OF ROLLOUT")
    while not state.isTerminal():
        action = MCTSAction(state.game_state.getHeuristicAction())
        state = state.takeAction(action)
        # print("taking action: " + action.to_string())
        # state.game_state.print_state()
    # print("END OF ROLLOUT")
    return state.getReward()

class MCTSSearcher:
    def __init__(self, time_limit_ms, exploration_constant=(1 / math.sqrt(2))):
        self.searcher = mcts(timeLimit=time_limit_ms, explorationConstant=exploration_constant, \
                             rolloutPolicy=heuristicPolicy)

    def search(self, initial_game_state, debug_print=True):
        mcts_state = MCTSState(initial_game_state)
        action = self.searcher.search(initialState=mcts_state, needDetails=debug_print)
        return action['action']
