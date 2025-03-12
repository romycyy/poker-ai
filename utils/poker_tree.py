from typing import List, Union, Any
from enum import Enum
import random

class Suit(Enum):
    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"

class Rank(Enum):
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"
    TEN = "10"
    JACK = "J"
    QUEEN = "Q"
    KING = "K"
    ACE = "A"

class Card:
    def __init__(self,
        rank: Rank,
        suit: Suit):
        self.rank = rank
        self.suit = suit
    
    def same_rank(self, other: Card):
        return self.rank == other.rank
    
    def same_suit(self, other: Card):
        return self.suit == other.suit
    
    def __repr__(self):
        return f"{self.rank.value}{self.suit.value}"

class Player:
    def __init__(self,
        dealer: bool = False,
        stack: int = 0):
        self.stack: int = stack
        self.cards: List[Card] = None
        self.pos: int = 0
        self.dealer: bool = dealer
    
    def set_cards(self, cards: List[Card]):
        self.cards = cards
    
    def set_pos(self, pos: int):
        self.pos = pos

    def get_cards(self):
        return self.cards

    def get_dealer(self):
        return self.dealer

class ActionType(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"
    START = "start"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"

class Action:
    def __init__(self,
        action_type: ActionType,
        amount: Union[int, float],
        all_in: bool = False):
        self.action_type = action_type
        self.amount = amount
        self.all_in = all_in

class GameNode:
    """
    Represents a node (history) h in the game tree.
    - history: all relevant info to define the state (public cards, private cards, bets so far, etc.)
    - player_to_act: which player is acting now, or 'chance' if it's a chance node
    - actions: list of possible actions (A(h))
    - is_terminal: True if this is a terminal node in the game (h ∈ Z)
    """
    def __init__(self,
                 player_to_act: Player,
                 actions: List[Action],
                 is_terminal: bool = False):
        self.player_to_act: Player = player_to_act
        self.actions: List[Action] = actions
        self.is_terminal: bool = is_terminal

    def __repr__(self):
        return f"<GameNode player={self.player_to_act}, terminal={self.is_terminal}, actions={self.actions}>"

    def get_player_to_act(self):
        return self.player_to_act

    def get_action_space(self):
        return NotImplementedError
         
    def check_if_terminal(self) -> bool:
        """
        Determines if the new state is terminal.
        This is just a placeholder. Real logic would check:
        - if only one player remains
        - if all betting rounds are complete and no more actions are possible
        - showdown conditions, etc.
        """
        # Example: if the history has a special "END" action
        if self.is_terminal:
            return True
        else:
            return False

class GameTree:
    """"""
    def __init__(self,
                 small_blind: int,
                 big_blind: int,
                 players: List[Player],
                 dealer_pos: int = 0):
        self.small_blind: int = small_blind
        self.big_blind: int = big_blind
        self.players: List[Player] = players
        self.dealer_pos: int = dealer_pos
        self.current_stage: ActionType = None
        self.dealer: Player = None
        self.nodes: List[GameNode] = []
        self.deck: List[Card] = [Card(rank, suit) for rank in Rank for suit in Suit]

    def start_game(self):
        assert self.current_stage == None
        dealer = Player(dealer=True)
        self.dealer = dealer
        self.nodes.append(GameNode(player_to_act=dealer, actions=[Action(ActionType.START, 0)], is_terminal=False))
        self.current_stage = ActionType.START
        random.shuffle(self.deck)
        for i in range(len(self.players)):
            self.players[i].set_pos((i-self.dealer_pos)%len(self.players))
            # Deal 2 cards to each player
            self.players[i].set_cards([self.deck.pop(), self.deck.pop()])


    def get_root(self):
        return self.root
    
    def get_node(self, node_id: str):
        return self.nodes[node_id]
    
    def get_action_from_player(self, current_node: GameNode) -> Action:
        player = current_node.get_player_to_act()

    
    def next_node(self, current_node: GameNode, action) -> None:
        """
        Returns the successor node h·a after taking 'action' at node 'current_node'.
        This is a placeholder. In a real system, you'd update:
        - who acts next
        - pot size, bets
        - cards if it's a chance node
        - check if terminal, etc.
        """
        new_history = current_node.history + [action]  # simplistic: just append action to 'history'
        new_actions = []

        # 1. If chance node, generate possible deals or outcomes
        if current_node.player_to_act == "chance":
            # For example, if we are dealing a card from a deck:
            new_actions = []  # depends on the deck, next deals, etc.
            next_player = 0   # after chance, player 0 might act
        else:
            # 2. If player node, define next player's turn
            next_player = (current_node.player_to_act + 1) % 6  # example for 6-handed
            new_actions = ["fold", "call", "raise"]  # simplistic placeholder

        # 3. Check if terminal
        # For instance, if everyone but one player folded, or if all betting rounds are done
        is_terminal = check_if_terminal(new_history)

        self.nodes[new_history] = GameNode(history=new_history,
        # Create and return the new node
        return GameNode(history=new_history,
                        player_to_act=next_player,
                        actions=new_actions,
                        is_terminal=is_terminal)
