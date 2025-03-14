# sunday fill in CFR
from utils.poker_tree import GameTree, Player, Action, ActionType, History, Stage


class Pluribus(Player):
    def __init__(self, dealer: bool = False, stack: int = 0):
        super().__init__(dealer, stack)

    def strategy(self, history: History):
        n = len(history.get_history())
        valid_actions = self.get_valid_actions()
        if len(valid_actions) == 0:
            return Action(ActionType.FOLD, 0)
        elif len(valid_actions) == 1:
            return valid_actions[0]
        else:
            return Action(ActionType.RAISE, 100)


P1 = Pluribus()
P2 = Pluribus()
P3 = Pluribus()
P4 = Pluribus()
P5 = Pluribus()


game_tree = GameTree(1, 2, [P1, P2, P3, P4, P5])
game_tree.start_game()

while game_tree.next_node():
    pass

print(game_tree.get_current_history())
