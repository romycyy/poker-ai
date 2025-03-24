from utils.poker_tree import (
    History,
    Action,
    Card,
    GameNode,
    Stage,
    ActionType,
    Rank,
    Suit,
    Player,
)
from typing import List, Dict, Set
import random


class info_element:
    def __init__(self, actions: List[Action]):
        self.actions = actions


infoset: Set[tuple[tuple[Card, Card], History]] = set()
actions_i: Dict[tuple[tuple[Card, Card], History], info_element] = {}


class PluribusDCFR:
    def __init__(self, infosets, alpha=1.5, beta=0, gamma=2):
        """
        :param infosets: A list of infoset objects or IDs in the game.
        :param alpha: Exponent for discounting positive regrets.
        :param beta:  Exponent for discounting negative regrets.
        :param gamma: Exponent for discounting average-strategy contributions.
        """
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        # Initialize data structures for each infoset I
        self.regrets = {}
        self.average_strategy = {}
        self.strategy = {}

        self.small_blind: int = 5
        self.big_blind: int = 10

        self.root: GameNode = None
        self.players: List[Player] = []
        for I in infosets:
            self.regrets[I] = {a: 0.0 for a in actions_i[I]}
            self.average_strategy[I] = {a: 0.0 for a in actions_i[I]}
            # Initialize current strategy to uniform
            self.strategy[I] = {a: 1.0 / len(actions_i[I]) for a in actions_i[I]}

    def initialize_game(self):
        # assert all players have enough stack to call
        for player in self.players:
            if player.get_stack() <= 0:
                raise ValueError(f"Player {player.get_pos()} has insufficient stack")
        self.history = History([])
        current_stage = Stage.PRE_FLOP
        self.history.append(
            GameNode(
                player_to_act=self.dealer,
                stage=current_stage,
                player_pos=-1,
                pot_size=self.small_blind + self.big_blind,
                call_amount=self.big_blind,
                community_cards=[],
                onboard_players=[i for i in range(len(self.players))],
            ),
            Action(ActionType.DEAL, 0),
        )
        self.root = self.history.get_history()[-1][0]
        self.deck: List[Card] = [Card(rank, suit) for rank in Rank for suit in Suit]
        # shuffle deck
        random.shuffle(self.deck)

        # initialize players
        for i in range(len(self.players)):
            self.players[i].set_pos(i)
            # Deal 2 cards to each player
            self.players[i].set_cards([self.deck.pop(), self.deck.pop()])
            self.players[i].initialized()

        # make small blind and big blind
        small_blind = Action(ActionType.RAISE, self.small_blind)
        big_blind = Action(ActionType.RAISE, self.big_blind)

        # check if small blind and big blind have enough stack to call/ all in
        if self.players[-2].get_stack() < self.small_blind:
            small_blind = Action(
                ActionType.CALL, self.players[-2].get_stack(), all_in=True
            )
        if self.players[-1].get_stack() < self.big_blind:
            big_blind = Action(
                ActionType.CALL, self.players[-1].get_stack(), all_in=True
            )
        self.players[-2].make_actions(small_blind)
        self.players[-1].make_actions(big_blind)

    def compute_blueprint_strategy(self, T):
        """
        Run DCFR for T iterations, discounting at *every iteration* using alpha, beta, gamma.
        :param T: Number of iterations.
        :param players: List of players in the game (including self).
        """
        for t in range(1, T + 1):
            # ---- Perform CFR updates (one iteration per player) ----

            for p in self.players:
                self.initialize_game()
                self.dcfr_traversal(self.root, p, 1.0, 1.0)

            # ---- Apply DCFR discounting to regrets and average strategy ----
            #   Based on the formulas from the slide:
            #     positive regrets *= t^alpha / (t^alpha + 1)
            #     negative regrets *= t^beta / (t^beta + 1)
            #     average-strategy contribution *= (t / (t + 1))^gamma
            pos_factor = (t**self.alpha) / (t**self.alpha + 1.0)
            neg_factor = (t**self.beta) / (t**self.beta + 1.0)
            avg_factor = (t / (t + 1.0)) ** self.gamma

            for I in self.regrets:
                for a in self.regrets[I]:
                    if self.regrets[I][a] > 0:
                        self.regrets[I][a] *= pos_factor
                    else:
                        self.regrets[I][a] *= neg_factor
                    self.average_strategy[I][a] *= avg_factor

        # ---- Build the final blueprint strategy by normalizing the average strategy ----
        final_strategy = {}
        for I in self.average_strategy:
            total = sum(self.average_strategy[I][a] for a in self.average_strategy[I])
            if total > 0:
                final_strategy[I] = {
                    a: self.average_strategy[I][a] / total
                    for a in self.average_strategy[I]
                }
            else:
                # If no positive mass, fall back to uniform
                num_actions = len(self.average_strategy[I])
                final_strategy[I] = {
                    a: 1.0 / num_actions for a in self.average_strategy[I]
                }
        return final_strategy

    def dcfr_traversal(self, h: GameNode, p: Player, reach_p, reach_opp):
        """
        Recursively traverse the game tree to update regrets and average strategy.
        :param h: Current node (history state).
        :param p: The player for whom we are computing the iteration.
        :param reach_p: Probability contribution of player p reaching this node.
        :param reach_opp: Probability contribution of all other players reaching this node.
        :return: The expected payoff for player p at this node.
        """
        if h.check_if_terminal():
            # implement payoff p
            return h.payoff(p)

        if h.is_chance_node():
            a = h.sample_action()
            return self.dcfr_traversal(h.next_state(a), p, reach_p, reach_opp)

        I = h.infoset(p)  # get the infoset for player p
        # Regret matching to compute the current strategy
        sum_positive_regrets = sum(max(self.regrets[I][a], 0) for a in self.regrets[I])
        if sum_positive_regrets > 0:
            for a in self.regrets[I]:
                self.strategy[I][a] = max(self.regrets[I][a], 0) / sum_positive_regrets
        else:
            # If all regrets ≤ 0, use uniform strategy
            for a in self.regrets[I]:
                self.strategy[I][a] = 1.0 / len(self.regrets[I])

        current_player = h.current_player()
        if current_player == p:
            # Player p's decision node
            value = 0.0
            action_values = {}
            for a in self.strategy[I]:
                # Recurse
                action_values[a] = self.dcfr_traversal(
                    h.next_state(a), p, reach_p * self.strategy[I][a], reach_opp
                )
                value += self.strategy[I][a] * action_values[a]

            # Update regrets & average strategy
            for a in self.regrets[I]:
                regret = action_values[a] - value
                self.regrets[I][a] += reach_opp * regret
                self.average_strategy[I][a] += reach_p * self.strategy[I][a]
            return value

        else:
            # Opponent node: sample an action from the strategy
            opp_infoset = h.infoset(current_player)
            sum_positive_opp = sum(
                max(self.regrets[opp_infoset][a], 0) for a in self.regrets[opp_infoset]
            )
            if sum_positive_opp > 0:
                for a in self.regrets[opp_infoset]:
                    self.strategy[opp_infoset][a] = (
                        max(self.regrets[opp_infoset][a], 0) / sum_positive_opp
                    )
            else:
                for a in self.regrets[opp_infoset]:
                    self.strategy[opp_infoset][a] = 1.0 / len(self.regrets[opp_infoset])

            # Sample an action for the opponent
            import random

            actions = list(self.strategy[opp_infoset].keys())
            probs = [self.strategy[opp_infoset][a] for a in actions]
            chosen_a = random.choices(actions, weights=probs, k=1)[0]
            return self.dcfr_traversal(
                h.next_state(chosen_a),
                p,
                reach_p,
                reach_opp * self.strategy[opp_infoset][chosen_a],
            )
