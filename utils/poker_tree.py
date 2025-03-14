from typing import List, Union
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
    def __init__(self, rank: Rank, suit: Suit):
        self.rank = rank
        self.suit = suit

    def same_rank(self, other: "Card"):
        return self.rank == other.rank

    def same_suit(self, other: "Card"):
        return self.suit == other.suit

    def __repr__(self):
        return f"{self.rank.value}{self.suit.value}"


class ActionType(Enum):
    FOLD = "fold"
    CALL = "call"
    RAISE = "raise"
    CHECK = "check"
    DEAL = "deal"


class Stage(Enum):
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"


class Action:
    """
    Represents an action in the game.
    - action_type: the type of action
    - amount: the amount of the action
    - all_in: whether the action is an all-in
    """

    def __init__(
        self, action_type: ActionType, amount: Union[int, float], all_in: bool = False
    ):
        self.action_type = action_type
        self.amount = amount
        self.all_in = all_in


class History:
    def __init__(self, history: List[tuple["GameNode", Action]]):
        self.history = history

    def append(self, game_node: "GameNode", action: Action):
        self.history.append((game_node, action))

    def get_history(self):
        return self.history


class Player:
    def __init__(self, dealer: bool = False, stack: int = 0):
        self.stack: int = stack
        self.cards: List[Card] = None
        self.pos: int = 0
        self.dealer: bool = dealer
        self.on_board: bool = False
        self.last_action_amount: int = 0
        self.has_acted: bool = False

    def strategy(self, history: History):
        raise NotImplementedError("Subclass must implement this method")

    def set_cards(self, cards: List[Card]):
        self.cards = cards

    def set_pos(self, pos: int):
        self.pos = pos

    def set_on_board(self, on_board: bool):
        self.on_board = on_board

    def set_has_acted(self, has_acted: bool):
        self.has_acted = has_acted

    def set_last_action_amount(self, last_action_amount: int):
        self.last_action_amount = last_action_amount

    def get_last_action_amount(self):
        return self.last_action_amount

    def get_has_acted(self):
        return self.has_acted

    def get_on_board(self):
        return self.on_board

    def get_cards(self):
        return self.cards

    def get_valid_actions(self):
        raise NotImplementedError("Subclass must implement this method")

    def get_actions(self, history: History):
        return self.strategy(history)

    def make_actions(self, action: Action) -> int:
        if action.action_type == ActionType.FOLD:
            self.on_board = False
            return 0
        elif action.action_type == ActionType.CHECK:
            self.last_action_amount = 0
            return 0
        else:  # RAISE or CALL
            self.stack = self.stack - action.amount + self.last_action_amount
            change = action.amount - self.last_action_amount
            self.last_action_amount = action.amount
            return change


class GameNode:
    """
    Represents a node (history) h in the game tree.
    - player_to_act: which player is acting now, or 'chance' if it's a chance node
    - pot_size: the size of the pot
    - call_amount: the amount of the call
    """

    def __init__(
        self,
        player_to_act: Player,
        player_pos: int,
        pot_size: int = 0,
        call_amount: int = 0,
        stage: Stage = None,
        community_cards: List[Card] = None,
        onboard_players: List[int] = [],
    ):
        self.player_to_act: Player = player_to_act
        self.player_pos: int = player_pos
        self.onboard_players: List[int] = onboard_players
        self.pot_size: int = pot_size
        self.call_amount: int = call_amount
        self.stage: Stage = stage
        self.community_cards: List[Card] = community_cards

    def __repr__(self):
        return f"<GameNode player={self.player_to_act}, actions={self.actions}>"

    def get_player_to_act(self):
        return self.player_to_act

    def get_onboard_players(self):
        return self.onboard_players

    def check_if_terminal(self) -> bool:
        return self.stage == Stage.SHOWDOWN

    def get_pot_size(self):
        return self.pot_size

    def get_call_amount(self):
        return self.call_amount

    def get_stage(self):
        return self.stage

    def get_player_pos(self):
        return self.player_pos

    def get_community_cards(self):
        return self.community_cards


class GameTree:
    """
    Represents the game tree G.
    players: start with UTG
    small_blind: the small blind
    big_blind: the big blind
    """

    def __init__(
        self,
        small_blind: int,
        big_blind: int,
        players: List[Player],
    ):
        self.small_blind: int = small_blind
        self.big_blind: int = big_blind
        self.players: List[Player] = players

        self.dealer: Player = None
        self.history: History = None
        self.deck: List[Card] = [Card(rank, suit) for rank in Rank for suit in Suit]

    def start_game(self):
        if self.history is not None:
            raise ValueError("Game already started")
        self.history = History([])
        self.dealer = Player(dealer=True)
        current_stage = Stage.PRE_FLOP
        self.history.append(
            tuple(
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
        )
        random.shuffle(self.deck)
        for i in range(len(self.players)):
            self.players[i].set_pos(i)
            # Deal 2 cards to each player
            self.players[i].set_cards([self.deck.pop(), self.deck.pop()])
            self.players[i].set_on_board(True)
            self.players[i].set_has_acted(False)
            self.players[i].set_last_action_amount(0)
        small_blind = Action(ActionType.RAISE, self.small_blind)
        big_blind = Action(ActionType.RAISE, self.big_blind)
        # check if players have enough stack to call
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

    def get_action_from_player(self, player: Player) -> Action:
        return player.get_actions(self.history)

    def next_node(self) -> bool:
        """
        Returns the successor node h·a after taking 'action' at node 'current_node'.
        This is a placeholder. In a real system, you'd update:
        - who acts next
        - pot size, bets
        - cards if it's a chance node
        - check if terminal, etc.
        """
        cur_node = self.history.get_history()[-1][0]
        current_pos = cur_node.get_player_pos()
        onboard_players = cur_node.get_onboard_players()
        if cur_node.check_if_terminal():
            return False
        # check if all players reached the call amount, if so, go to dealer move

        flag = False
        for player_pos in onboard_players:
            player = self.players[player_pos]
            if not player.get_has_acted():
                flag = True
                break
            elif player.get_last_action_amount() < cur_node.get_call_amount():
                flag = True
                break

        if flag:
            # player move

            # skip players who have folded
            current_pos = (current_pos + 1) % len(self.players)
            player = self.players[current_pos]
            while not player.get_on_board():
                current_pos = (current_pos + 1) % len(self.players)
                player = self.players[current_pos]

            # get action from player
            player.set_has_acted(True)
            action = self.get_action_from_player(player)
            amount = player.make_actions(action)
            pot_size = cur_node.get_pot_size()
            call_amount = cur_node.get_call_amount()
            if action.action_type == ActionType.RAISE:
                pot_size += amount
                call_amount = amount
            elif action.action_type == ActionType.CALL:
                pot_size += amount
            elif action.action_type == ActionType.FOLD:
                onboard_players.remove(player_pos)
            if len(onboard_players) == 1:
                new_node = GameNode(
                    player_to_act=None,
                    player_pos=-1,
                    pot_size=pot_size,
                    call_amount=0,
                    stage=Stage.SHOWDOWN,
                )
            else:
                new_node = GameNode(
                    player_to_act=player,
                    player_pos=current_pos,
                    pot_size=pot_size,
                    call_amount=call_amount,
                    stage=cur_node.get_stage(),
                    community_cards=cur_node.get_community_cards(),
                    onboard_players=onboard_players,
                )
            self.history.append(new_node, action)
            return True
        else:
            # dealer move
            # Dealer deals community cards based on stage
            stage = cur_node.get_stage()
            community_cards = cur_node.community_cards
            for player_pos in onboard_players:
                player = self.players[player_pos]
                player.set_last_action_amount(0)
                player.set_has_acted(False)
            if stage == Stage.PRE_FLOP:
                community_cards = [self.deck.pop() for _ in range(3)]
                new_node = GameNode(
                    player_to_act=self.dealer,
                    player_pos=-1,
                    pot_size=cur_node.get_pot_size(),
                    call_amount=0,
                    stage=Stage.FLOP,
                    community_cards=community_cards,
                    onboard_players=onboard_players,
                )
            elif stage == Stage.FLOP:
                community_cards = community_cards + [self.deck.pop()]
                new_node = GameNode(
                    player_to_act=self.dealer,
                    player_pos=-1,
                    pot_size=cur_node.get_pot_size(),
                    call_amount=0,
                    stage=Stage.TURN,
                    community_cards=community_cards,
                    onboard_players=onboard_players,
                )
            elif stage == Stage.TURN:
                community_cards = community_cards + [self.deck.pop()]
                new_node = GameNode(
                    player_to_act=self.dealer,
                    player_pos=-1,
                    pot_size=cur_node.get_pot_size(),
                    call_amount=0,
                    stage=Stage.RIVER,
                    community_cards=community_cards,
                    onboard_players=onboard_players,
                )
            elif stage == Stage.RIVER:
                new_node = GameNode(
                    player_to_act=None,
                    player_pos=-1,
                    pot_size=cur_node.get_pot_size(),
                    call_amount=0,
                    community_cards=community_cards,
                    stage=Stage.SHOWDOWN,
                    onboard_players=onboard_players,
                )
            self.history.append(new_node, Action(ActionType.DEAL, 0))
            return True
