from utils.poker_tree import (
    Player,
    Card,
    History,
    Action,
    Rank,
    Suit,
    GameNode,
    Stage,
    ActionType,
    HandEvaluator,
)
from typing import List, Dict
import random


class info_element:
    def __init__(self, actions: List[Action]):
        self.actions = actions


infoset: Dict[tuple[tuple[Card, Card], History], info_element] = {}

# TODO: need action abstraction and information abstraction for infoset initialization


class Pluribus(Player):
    def __init__(self, alpha=1.5, beta=0, gamma=2, stack=10000):
        super().__init__(stack=stack)
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.regrets = {}
        self.average_strategy = {}
        self.strategy = {}
        for key, value in infoset.items():
            self.regrets[key] = {a: 0.0 for a in value.actions}
            self.average_strategy[key] = {a: 0.0 for a in value.actions}
            # Initialize current strategy to uniform
            self.strategy[key] = {a: 1.0 / len(value.actions) for a in value.actions}

    def strategy(self, history: History):
        return random.choice(
            infoset[(self.cards, history)].actions,
            weights=[
                self.strategy[(self.cards, history)][a]
                for a in infoset[(self.cards, history)].actions
            ],
        )


class PluribusDCFR:
    def __init__(
        self,
        players: List[Pluribus],
        small_blind: int = 5,
        big_blind: int = 10,
    ):
        """
        :param players: A list of Pluribus players.
        """
        self.players = players
        self.small_blind: int = small_blind
        self.big_blind: int = big_blind
        self.history: History = History([])
        self.dealer: Player = Player(dealer=True)
        self.history: History = History([])
        self.deck: List[Card] = []
        self.root: GameNode = GameNode(self.dealer, 0, 0, 0)

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

    # TODO: should move this out of the class
    def compute_blueprint_strategy(self, T):
        """
        Run DCFR for T iterations, discounting at *every iteration* using alpha, beta, gamma.
        :param T: Number of iterations.
        """
        for t in range(1, T + 1):
            # ---- Perform CFR updates (one iteration per player) ----
            for p in self.players:
                self.dcfr_traversal(game_tree.root, p, 1.0, 1.0)

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

    def dcfr_traversal(self, h, p, reach_p, reach_opp):
        """
        Recursively traverse the game tree to update regrets and average strategy.
        :param h: Current node (history state).
        :param p: The player for whom we are computing the iteration.
        :param reach_p: Probability contribution of player p reaching this node.
        :param reach_opp: Probability contribution of all other players reaching this node.
        :return: The expected payoff for player p at this node.
        """
        if h.is_terminal():
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

            actions = list(self.strategy[opp_infoset].keys())
            probs = [self.strategy[opp_infoset][a] for a in actions]
            chosen_a = random.choices(actions, weights=probs, k=1)[0]
            return self.dcfr_traversal(
                h.next_state(chosen_a),
                p,
                reach_p,
                reach_opp * self.strategy[opp_infoset][chosen_a],
            )
