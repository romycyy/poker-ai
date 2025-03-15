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

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.rank == other.rank and self.suit == other.suit
        return False


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

    def __repr__(self):
        return f"<Action action_type={self.action_type}, amount={self.amount}, all_in={self.all_in}>"


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
        self.is_all_in: bool = False
        self.total_bet: int = 0  # Track total amount bet in the hand

    def __repr__(self):
        return f"<Player stack={self.stack}, cards={self.cards}, pos={self.pos}, last_action_amount={self.last_action_amount}, has_acted={self.has_acted}, is_all_in={self.is_all_in}>"

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

    def add_stack(self, amount: int):
        self.stack += amount    

    def get_stack(self):
        return self.stack

    def get_last_action_amount(self):
        return self.last_action_amount

    def get_has_acted(self):
        return self.has_acted

    def get_on_board(self):
        return self.on_board

    def get_cards(self):
        return self.cards

    # def get_valid_actions(self):
    #     raise NotImplementedError("Subclass must implement this method")

    def get_actions(self, history: History):
        return self.strategy(history)

    def make_actions(self, action: Action) -> int:
        if self.on_board is False:
            raise ValueError("Player is not on board")

        if action.action_type == ActionType.FOLD:
            self.on_board = False
            return 0
        elif action.action_type == ActionType.CHECK:
            return 0
        else:  # RAISE or CALL
            if action.amount < self.last_action_amount:
                raise ValueError("Cannot bet less than the current bet")

            amount_to_pay = action.amount - self.last_action_amount
            if amount_to_pay >= self.stack:
                # All-in case
                amount_to_pay = self.stack
                self.is_all_in = True
                assert action.all_in is True
            elif amount_to_pay < 0:
                raise ValueError("Invalid bet amount")

            self.stack -= amount_to_pay
            self.last_action_amount = action.amount
            self.total_bet += amount_to_pay
            return amount_to_pay

    def get_is_all_in(self):
        return self.is_all_in

    def get_total_bet(self):
        return self.total_bet


class SidePot:
    """Represents a side pot in the game with its eligible players"""

    def __init__(self, amount: int = 0):
        self.amount: int = amount
        self.eligible_players: List[int] = []  # List of player positions

    def __repr__(self):
        return (
            f"<SidePot amount={self.amount}, eligible_players={self.eligible_players}>"
        )

    def add_amount(self, amount: int):
        self.amount += amount

    def add_eligible_player(self, player_pos: int):
        if player_pos not in self.eligible_players:
            self.eligible_players.append(player_pos)


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
        if pot_size < 0:
            raise ValueError("Pot size cannot be negative")
        if call_amount < 0:
            raise ValueError("Call amount cannot be negative")
        if not isinstance(onboard_players, list):
            raise ValueError("onboard_players must be a list")

        self.player_to_act = player_to_act
        self.player_pos = player_pos
        self.onboard_players = (
            onboard_players.copy()
        )  # Make a copy to prevent external modifications
        self.pot_size = pot_size
        self.call_amount = call_amount
        self.stage = stage
        self.community_cards = community_cards
        self.side_pots = [SidePot(pot_size)]  # Main pot is first
        self.current_bet_per_player = {}  # Track bets for side pot calculation

    def __repr__(self):
        return f"<GameNode player={self.player_to_act}, onboard_players={self.onboard_players}, call_amount={self.call_amount}, pot_size={self.pot_size}, stage={self.stage}>"

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

    def calculate_side_pots(self, players: List[Player]):
        """Recalculate side pots when a player goes all-in"""
        # Reset current bets tracking
        self.current_bet_per_player = {
            pos: player.get_total_bet()
            for pos, player in enumerate(players)
            if pos in self.onboard_players
        }

        if not self.current_bet_per_player:
            return  # No players to create pots for

        # Sort players by their total bet amount
        sorted_players = sorted(
            [(pos, players[pos]) for pos in self.onboard_players],
            key=lambda x: x[1].get_total_bet(),
        )

        # Reset side pots
        self.side_pots = []
        previous_bet = 0

        # Calculate each side pot
        for pos, player in sorted_players:
            current_bet = player.get_total_bet()
            if current_bet > previous_bet:
                pot = SidePot()
                contribution = current_bet - previous_bet

                # Add eligible players and their contributions
                eligible_count = 0
                for other_pos in self.onboard_players:
                    if self.current_bet_per_player[other_pos] >= current_bet:
                        pot.add_eligible_player(other_pos)
                        pot.add_amount(contribution)
                        eligible_count += 1

                if (
                    pot.amount > 0
                ):  # Only create pot if pot has money
                    self.side_pots.append(pot)

                previous_bet = current_bet

        # If no side pots were created, create main pot
        if not self.side_pots:
            main_pot = SidePot()
            for pos in self.onboard_players:
                main_pot.add_eligible_player(pos)
                main_pot.add_amount(self.current_bet_per_player[pos])
            self.side_pots.append(main_pot)

    def get_side_pots(self):
        return self.side_pots


class HandRank(Enum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9


class HandEvaluator:
    @staticmethod
    def evaluate_hand(hole_cards: List[Card], community_cards: List[Card]):
        """
        Evaluates the best 5-card hand from hole cards and community cards.
        Returns (HandRank, list of cards making the hand, list of kicker cards)
        """
        all_cards = hole_cards + community_cards

        # Check from highest to lowest possible hands
        evaluators = [
            HandEvaluator._check_royal_flush,
            HandEvaluator._check_straight_flush,
            HandEvaluator._check_four_of_kind,
            HandEvaluator._check_full_house,
            HandEvaluator._check_flush,
            HandEvaluator._check_straight,
            HandEvaluator._check_three_of_kind,
            HandEvaluator._check_two_pair,
            HandEvaluator._check_pair,
            HandEvaluator._check_high_card,
        ]

        for evaluator in evaluators:
            result = evaluator(all_cards)
            if result:
                return result

        return HandRank.HIGH_CARD, [], []

    @staticmethod
    def _get_rank_counts(cards: List[Card]) -> dict:
        """Helper method to count occurrences of each rank"""
        rank_counts = {}
        for card in cards:
            rank_counts[card.rank] = rank_counts.get(card.rank, 0) + 1
        return rank_counts

    @staticmethod
    def _check_royal_flush(cards: List[Card]):
        """Check for royal flush (A, K, Q, J, 10 of same suit)"""
        for suit in Suit:
            suited_cards = [card for card in cards if card.suit == suit]
            if len(suited_cards) >= 5:
                ranks = {card.rank for card in suited_cards}
                royal_ranks = {Rank.TEN, Rank.JACK, Rank.QUEEN, Rank.KING, Rank.ACE}
                if royal_ranks.issubset(ranks):
                    hand = [card for card in suited_cards if card.rank in royal_ranks]
                    return HandRank.ROYAL_FLUSH, hand, []
        return None

    @staticmethod
    def _check_straight_flush(cards: List[Card]):
        """Check for straight flush (five sequential cards of same suit)"""
        for suit in Suit:
            suited_cards = sorted(
                [card for card in cards if card.suit == suit],
                key=lambda x: list(Rank).index(x.rank),
            )
            if len(suited_cards) >= 5:
                # Check regular straight flush
                for i in range(len(suited_cards) - 4):
                    straight = suited_cards[i : i + 5]
                    if all(
                        list(Rank).index(straight[j + 1].rank)
                        - list(Rank).index(straight[j].rank)
                        == 1
                        for j in range(len(straight) - 1)
                    ):
                        return HandRank.STRAIGHT_FLUSH, straight, []

                # Check Ace-low straight flush (A,2,3,4,5)
                if (
                    any(card.rank == Rank.ACE for card in suited_cards)
                    and any(card.rank == Rank.TWO for card in suited_cards)
                    and any(card.rank == Rank.THREE for card in suited_cards)
                    and any(card.rank == Rank.FOUR for card in suited_cards)
                    and any(card.rank == Rank.FIVE for card in suited_cards)
                ):
                    straight = [
                        card
                        for card in suited_cards
                        if card.rank
                        in [Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE]
                    ]
                    return HandRank.STRAIGHT_FLUSH, straight, []
        return None

    @staticmethod
    def _check_four_of_kind(cards: List[Card]):
        """Check for four of a kind"""
        rank_counts = HandEvaluator._get_rank_counts(cards)
        for rank, count in rank_counts.items():
            if count == 4:
                quads = [card for card in cards if card.rank == rank]
                kickers = sorted(
                    [card for card in cards if card.rank != rank],
                    key=lambda x: list(Rank).index(x.rank),
                    reverse=True,
                )
                return HandRank.FOUR_OF_KIND, quads, kickers[:1]
        return None

    @staticmethod
    def _check_full_house(cards: List[Card]):
        """Check for full house (three of a kind plus a pair)"""
        rank_counts = HandEvaluator._get_rank_counts(cards)
        three_of_kind = None
        pair = None

        # Find highest three of a kind
        for rank, count in rank_counts.items():
            if count >= 3 and (
                three_of_kind is None
                or list(Rank).index(rank) > list(Rank).index(three_of_kind)
            ):
                three_of_kind = rank

        if three_of_kind:
            # Find highest pair from remaining cards
            for rank, count in rank_counts.items():
                if (
                    rank != three_of_kind
                    and count >= 2
                    and (
                        pair is None or list(Rank).index(rank) > list(Rank).index(pair)
                    )
                ):
                    pair = rank

            if pair:
                hand = [card for card in cards if card.rank == three_of_kind][:3] + [
                    card for card in cards if card.rank == pair
                ][:2]
                return HandRank.FULL_HOUSE, hand, []
        return None

    @staticmethod
    def _check_pair(cards: List[Card]):
        """Check for a pair"""
        rank_counts = HandEvaluator._get_rank_counts(cards)
        for rank, count in sorted(
            rank_counts.items(), key=lambda x: list(Rank).index(x[0]), reverse=True
        ):  # Check high pairs first
            if count == 2:
                pair = [card for card in cards if card.rank == rank]
                kickers = sorted(
                    [card for card in cards if card.rank != rank],
                    key=lambda x: list(Rank).index(x.rank),
                    reverse=True,
                )
                return HandRank.PAIR, pair, kickers[:3]  # Return top 3 kickers
        return None

    @staticmethod
    def _check_high_card(cards: List[Card]):
        """Return highest card with top 4 kickers"""
        sorted_cards = sorted(
            cards, key=lambda x: list(Rank).index(x.rank), reverse=True
        )
        return HandRank.HIGH_CARD, [sorted_cards[0]], sorted_cards[1:5]

    @staticmethod
    def _check_three_of_kind(cards: List[Card]):
        """Check for three of a kind"""
        rank_counts = HandEvaluator._get_rank_counts(cards)
        for rank, count in sorted(
            rank_counts.items(), key=lambda x: list(Rank).index(x[0]), reverse=True
        ):
            if count >= 3:
                trips = [card for card in cards if card.rank == rank][:3]
                kickers = sorted(
                    [card for card in cards if card.rank != rank],
                    key=lambda x: list(Rank).index(x.rank),
                    reverse=True,
                )
                return HandRank.THREE_OF_KIND, trips, kickers[:2]
        return None

    @staticmethod
    def _check_flush(cards: List[Card]):
        """Check for a flush (five cards of the same suit)"""
        for suit in Suit:
            suited_cards = sorted(
                [card for card in cards if card.suit == suit],
                key=lambda x: list(Rank).index(x.rank),
                reverse=True,
            )
            if len(suited_cards) >= 5:
                return HandRank.FLUSH, suited_cards[:5], []
        return None

    @staticmethod
    def _check_straight(cards: List[Card]):
        """Check for a straight (five sequential cards of any suit)"""
        # Sort cards by rank
        sorted_cards = sorted(cards, key=lambda x: list(Rank).index(x.rank))

        # Remove duplicates while preserving order
        unique_ranks = []
        seen = set()
        for card in sorted_cards:
            if card.rank not in seen:
                unique_ranks.append(card)
                seen.add(card.rank)

        # Check for regular straight
        for i in range(len(unique_ranks) - 4):
            straight = unique_ranks[i : i + 5]
            if all(
                list(Rank).index(straight[j + 1].rank)
                - list(Rank).index(straight[j].rank)
                == 1
                for j in range(len(straight) - 1)
            ):
                return HandRank.STRAIGHT, straight, []

        # Check for Ace-low straight (A,2,3,4,5)
        if (
            any(card.rank == Rank.ACE for card in cards)
            and any(card.rank == Rank.TWO for card in cards)
            and any(card.rank == Rank.THREE for card in cards)
            and any(card.rank == Rank.FOUR for card in cards)
            and any(card.rank == Rank.FIVE for card in cards)
        ):
            straight = [
                next(card for card in cards if card.rank == Rank.ACE),
                next(card for card in cards if card.rank == Rank.TWO),
                next(card for card in cards if card.rank == Rank.THREE),
                next(card for card in cards if card.rank == Rank.FOUR),
                next(card for card in cards if card.rank == Rank.FIVE),
            ]
            return HandRank.STRAIGHT, straight, []

        return None

    @staticmethod
    def _check_two_pair(cards: List[Card]):
        """Check for two pair (two different pairs of same rank)"""
        rank_counts = HandEvaluator._get_rank_counts(cards)
        pairs = [rank for rank, count in rank_counts.items() if count >= 2]

        if len(pairs) >= 2:
            # Sort pairs by rank (highest first)
            pairs.sort(key=lambda x: list(Rank).index(x), reverse=True)
            two_pairs = pairs[:2]

            # Get the cards making up the two pairs
            hand = []
            for pair_rank in two_pairs:
                pair_cards = [card for card in cards if card.rank == pair_rank][:2]
                hand.extend(pair_cards)

            # Get highest remaining card as kicker
            remaining_cards = [card for card in cards if card.rank not in two_pairs]
            kickers = sorted(
                remaining_cards, key=lambda x: list(Rank).index(x.rank), reverse=True
            )[:1]

            return HandRank.TWO_PAIR, hand, kickers

        return None

    @staticmethod
    def compare_hands(hand1, hand2):
        """
        Compares two hands.
        Returns: 1 if hand1 wins, -1 if hand2 wins, 0 if tie
        Each hand is a tuple of (HandRank, main cards, kicker cards)
        """
        if not hand1 or not hand2:
            raise ValueError("Invalid hand comparison")

        rank1, main1, kickers1 = hand1
        rank2, main2, kickers2 = hand2

        # Compare hand ranks first
        if rank1.value > rank2.value:
            return 1
        elif rank1.value < rank2.value:
            return -1

        # If ranks are equal, compare main cards
        for card1, card2 in zip(main1, main2):
            rank_diff = list(Rank).index(card1.rank) - list(Rank).index(card2.rank)
            if rank_diff != 0:
                return 1 if rank_diff > 0 else -1

        # If main cards are equal, compare kickers
        for card1, card2 in zip(kickers1 or [], kickers2 or []):  # Handle None kickers
            rank_diff = list(Rank).index(card1.rank) - list(Rank).index(card2.rank)
            if rank_diff != 0:
                return 1 if rank_diff > 0 else -1

        # If all cards are equal or no more kickers to compare
        return 0


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

    def get_current_history(self):
        return self.history.get_history()[-1]

    def start_game(self):
        # assert all players have enough stack to call
        for player in self.players:
            if player.get_stack() <= 0:
                raise ValueError("Player has insufficient stack")
        if self.history is not None:
            raise ValueError("Game already started")
        self.history = History([])
        self.dealer = Player(dealer=True)
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

        # shuffle deck
        random.shuffle(self.deck)

        # initialize players
        for i in range(len(self.players)):
            self.players[i].set_pos(i)
            # Deal 2 cards to each player
            self.players[i].set_cards([self.deck.pop(), self.deck.pop()])
            self.players[i].set_on_board(True)
            self.players[i].set_has_acted(False)
            self.players[i].set_last_action_amount(0)

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
            elif (
                player.get_last_action_amount() < cur_node.get_call_amount()
                and player.get_stack() > 0
            ):
                # player needs to call and player has not allin
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

            # After player makes action, check if they went all-in
            if action.all_in:
                # Recalculate side pots
                new_node.calculate_side_pots(self.players)

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

    def checkout(self):
        if self.history.get_history()[-1][0].get_stage() == Stage.SHOWDOWN:
            final_node = self.history.get_history()[-1][0]
            side_pots = final_node.get_side_pots()
            community_cards = final_node.get_community_cards()

            # For each side pot, determine the winner
            for pot in side_pots:
                if len(pot.eligible_players) == 1:
                    # Only one player eligible, they win automatically
                    winner_pos = pot.eligible_players[0]
                    self.players[winner_pos].stack += pot.amount
                else:
                    # Compare hands of eligible players
                    best_hand = None
                    winners = []

                    for player_pos in pot.eligible_players:
                        player = self.players[player_pos]
                        if not player.get_on_board():
                            continue

                        hand_result = HandEvaluator.evaluate_hand(
                            player.get_cards(), community_cards
                        )

                        if (
                            best_hand is None
                            or HandEvaluator.compare_hands(hand_result, best_hand) > 0
                        ):
                            best_hand = hand_result
                            winners = [player_pos]
                        elif HandEvaluator.compare_hands(hand_result, best_hand) == 0:
                            winners.append(player_pos)

                    # Split pot among winners
                    split_amount = pot.amount // len(winners)
                    remainder = pot.amount % len(winners)

                    for winner_pos in winners:
                        self.players[winner_pos].stack += split_amount

                    # Give remainder to first player after dealer
                    if remainder > 0:
                        first_winner = min(winners)
                        self.players[first_winner].stack += remainder
        else:
            raise ValueError("Game is not terminal")
