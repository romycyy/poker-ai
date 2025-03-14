# sunday fill in CFR
from utils.poker_tree import GameTree, Player, Action, ActionType, History, Stage


class test(Player):
    def __init__(self, dealer: bool = False, stack: int = 0):
        super().__init__(dealer, stack)

    def strategy(self, history: History):
        n = len(history.get_history())
        valid_actions = self.
        if len(valid_actions) == 0:
            return Action(ActionType.FOLD, 0)
        elif len(valid_actions) == 1:
            return valid_actions[0]
        else:
            return Action(ActionType.RAISE, 100)


P1 = test(stack=100)
P2 = test(stack=100)


game_tree = GameTree(1, 2, [P1, P2])
game_tree.start_game()

while game_tree.next_node():
    print(game_tree.get_current_history()[0], game_tree.get_current_history()[1])
    pass

print(game_tree.get_current_history())
