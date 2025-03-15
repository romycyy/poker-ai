# sunday fill in CFR
from utils.poker_tree import (
    GameTree,
    Player,
    Action,
    ActionType,
    History,
    Stage,
    Card,
    Rank,
    Suit,
    HandRank,
    HandEvaluator,
    GameTree,
    GameNode,
    SidePot,
)


def test_player_initialization():
    # Test basic initialization
    player = Player(dealer=True, stack=1000)
    assert player.get_stack() == 1000


def test_player_betting():
    player = Player(dealer=False, stack=1000)
    player.set_on_board(True)
    action = Action(ActionType.RAISE, 100)

    # Test adding bet
    player.make_actions(action)
    assert player.get_total_bet() == 100
    assert player.get_stack() == 900

    # Test adding multiple bets
    action = Action(ActionType.RAISE, 300)
    player.make_actions(action)
    assert player.get_total_bet() == 300
    assert player.get_stack() == 700

    # Test betting more than stack
    action = Action(ActionType.RAISE, 1100, all_in=True)
    player.make_actions(action)
    assert player.get_stack() == 0
    assert player.is_all_in is True


def test_player_cards():
    player = Player(dealer=False, stack=1000)

    # Test setting cards
    cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
    player.set_cards(cards)
    assert player.get_cards() == cards

    # Test clearing card


def test_player_fold():
    player = Player(dealer=False, stack=1000)
    player.set_on_board(True)
    assert player.get_on_board() is True

    # Test folding
    action = Action(ActionType.FOLD, 0)
    player.make_actions(action)
    assert player.get_on_board() is False

    # Test can't bet after folding
    action = Action(ActionType.RAISE, 100)
    try:
        player.make_actions(action)
        assert False, "Should raise ValueError"
    except ValueError:
        pass


def test_player_reset():
    player = Player(dealer=True, stack=1000)
    player.set_on_board(True)
    # Make some actions
    action = Action(ActionType.RAISE, 200)
    player.make_actions(action)
    player.set_cards([Card(Rank.ACE, Suit.SPADES)])
    action = Action(ActionType.FOLD, 0)
    player.make_actions(action)


def test_game_node_initialization():
    # Create a mock player
    player = Player(dealer=True, stack=1000)

    # Initialize a GameNode
    node = GameNode(
        player_to_act=player,
        player_pos=0,
        pot_size=100,
        call_amount=50,
        stage=Stage.PRE_FLOP,
        community_cards=[Card(Rank.ACE, Suit.SPADES)],
        onboard_players=[0, 1],
    )

    # Test initial values
    assert node.get_player_to_act() == player
    assert node.get_pot_size() == 100
    assert node.get_call_amount() == 50
    assert node.get_stage() == Stage.PRE_FLOP
    assert node.get_community_cards() == [Card(Rank.ACE, Suit.SPADES)]
    assert node.get_onboard_players() == [0, 1]


def test_game_node_side_pots():
    # Create mock players
    player1 = Player(dealer=False, stack=1000)
    player2 = Player(dealer=False, stack=500)
    player3 = Player(dealer=False, stack=1000)
    player1.set_on_board(True)
    player2.set_on_board(True)
    player3.set_on_board(True)
    # Initialize a GameNode
    node = GameNode(
        player_to_act=player1,
        player_pos=0,
        pot_size=0,
        call_amount=0,
        stage=Stage.PRE_FLOP,
        community_cards=[],
        onboard_players=[0, 1, 2],
    )

    # Set total bets for players
    action = Action(ActionType.RAISE, 800)
    player1.make_actions(action)
    action = Action(ActionType.CALL, 500, all_in=True)
    player2.make_actions(action)
    action = Action(ActionType.CALL, 800)
    player3.make_actions(action)

    # Calculate side pots
    node.calculate_side_pots([player1, player2, player3])

    # Test side pots
    side_pots = node.get_side_pots()
    assert len(side_pots) == 2
    assert side_pots[0].amount == 1500
    assert side_pots[0].eligible_players == [0, 1, 2]
    assert side_pots[1].amount == 600
    assert side_pots[1].eligible_players == [0, 2]

    # Test add stack
    player1.last_action_amount = 0
    player2.last_action_amount = 0
    player1.total_bet = 0
    player2.total_bet = 0
    player1.add_stack(800)
    assert player1.get_stack() == 1000
    player2.add_stack(500)
    assert player2.get_stack() == 500
    node = GameNode(
        player_to_act=player1,
        player_pos=0,
        pot_size=0,
        call_amount=0,
        stage=Stage.PRE_FLOP,
        community_cards=[],
        onboard_players=[0, 1],
    )
    action = Action(ActionType.RAISE, 900)
    player1.make_actions(action)
    action = Action(ActionType.CALL, 500, all_in=True)
    player2.make_actions(action)
    node.calculate_side_pots([player1, player2])
    side_pots = node.get_side_pots()
    assert len(side_pots) == 2
    assert side_pots[0].amount == 1000
    assert side_pots[0].eligible_players == [0, 1]
    assert side_pots[1].amount == 400
    assert side_pots[1].eligible_players == [0]
    assert player2.get_stack() == 0


def test_hand_evaluator():
    # Test high card
    hole_cards = [Card(Rank.TEN, Suit.SPADES), Card(Rank.KING, Suit.HEARTS)]
    community_cards = [
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.FOUR, Suit.DIAMONDS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.ACE, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.HIGH_CARD
    assert hand_cards == [Card(Rank.ACE, Suit.CLUBS)]
    assert kickers == [Card(Rank.KING, Suit.HEARTS), Card(Rank.TEN, Suit.SPADES), Card(Rank.EIGHT, Suit.SPADES), Card(Rank.SIX, Suit.HEARTS)]

    # Test pair
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.TEN, Suit.CLUBS)]
    community_cards = [
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.FOUR, Suit.DIAMONDS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.PAIR
    assert hand_cards == [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    assert kickers == [Card(Rank.TEN, Suit.CLUBS), Card(Rank.EIGHT, Suit.SPADES), Card(Rank.SIX, Suit.HEARTS)]

    # Test two pair
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    community_cards = [
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.TEN, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.TWO_PAIR
    assert hand_cards == [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS), Card(Rank.TWO, Suit.CLUBS), Card(Rank.TWO, Suit.DIAMONDS)]
    assert kickers == [Card(Rank.TEN, Suit.CLUBS)]

    # Test three of a kind
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    community_cards = [
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.FOUR, Suit.DIAMONDS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.TEN, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.THREE_OF_KIND
    assert hand_cards == [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS)]
    assert kickers == [Card(Rank.TEN, Suit.CLUBS), Card(Rank.EIGHT, Suit.SPADES)]

    # Test straight
    hole_cards = [Card(Rank.FIVE, Suit.SPADES), Card(Rank.SIX, Suit.HEARTS)]
    community_cards = [
        Card(Rank.SEVEN, Suit.CLUBS),
        Card(Rank.EIGHT, Suit.DIAMONDS),
        Card(Rank.NINE, Suit.HEARTS),
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    print(hand_rank, hand_cards, kickers)
    assert hand_rank == HandRank.STRAIGHT
    assert hand_cards == [Card(Rank.SEVEN, Suit.CLUBS), Card(Rank.EIGHT, Suit.DIAMONDS), Card(Rank.NINE, Suit.HEARTS), Card(Rank.TEN, Suit.SPADES), Card(Rank.JACK, Suit.CLUBS)]
    assert kickers == []

    # Test flush
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.SPADES)]
    community_cards = [
        Card(Rank.TWO, Suit.SPADES),
        Card(Rank.FOUR, Suit.SPADES),
        Card(Rank.SIX, Suit.SPADES),
        Card(Rank.EIGHT, Suit.HEARTS),
        Card(Rank.TEN, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.FLUSH
    assert hand_cards == [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.SPADES), Card(Rank.TWO, Suit.SPADES), Card(Rank.FOUR, Suit.SPADES), Card(Rank.SIX, Suit.SPADES)]
    assert kickers == []

    # Test full house
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    community_cards = [
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.FOUR, Suit.DIAMONDS),
        Card(Rank.FOUR, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.TEN, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.FULL_HOUSE
    assert hand_cards == [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS), Card(Rank.FOUR, Suit.DIAMONDS), Card(Rank.FOUR, Suit.HEARTS)]
    assert kickers == []

    # Test four of a kind
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    community_cards = [
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.TEN, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.FOUR_OF_KIND
    assert hand_cards == [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS), Card(Rank.ACE, Suit.CLUBS), Card(Rank.ACE, Suit.DIAMONDS)]
    assert kickers == [Card(Rank.TEN, Suit.CLUBS)]

    # Test straight flush
    hole_cards = [Card(Rank.FIVE, Suit.SPADES), Card(Rank.SIX, Suit.SPADES)]
    community_cards = [
        Card(Rank.SEVEN, Suit.SPADES),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.NINE, Suit.SPADES),
        Card(Rank.TEN, Suit.HEARTS),
        Card(Rank.JACK, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.STRAIGHT_FLUSH
    assert hand_cards == [Card(Rank.FIVE, Suit.SPADES), Card(Rank.SIX, Suit.SPADES), Card(Rank.SEVEN, Suit.SPADES), Card(Rank.EIGHT, Suit.SPADES), Card(Rank.NINE, Suit.SPADES)]
    assert kickers == []

    # Test royal flush
    hole_cards = [Card(Rank.TEN, Suit.SPADES), Card(Rank.JACK, Suit.SPADES)]
    community_cards = [
        Card(Rank.QUEEN, Suit.SPADES),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.TWO, Suit.HEARTS),
        Card(Rank.THREE, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(hole_cards, community_cards)
    assert hand_rank == HandRank.ROYAL_FLUSH
    assert hand_cards == [Card(Rank.TEN, Suit.SPADES), Card(Rank.JACK, Suit.SPADES), Card(Rank.QUEEN, Suit.SPADES), Card(Rank.KING, Suit.SPADES), Card(Rank.ACE, Suit.SPADES)]
    assert kickers == []


if __name__ == "__main__":
    test_player_initialization()
    test_player_betting()
    test_player_cards()
    test_player_fold()
    test_player_reset()
    test_game_node_initialization()
    test_game_node_side_pots()
    test_hand_evaluator()