# sunday fill in CFR
from utils.poker_tree import (
    GameTree,
    Player,
    Action,
    ActionType,
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

    # Test side pots
    side_pots = node.calculate_side_pots([player1, player2, player3])
    print(side_pots)
    assert len(side_pots) == 2
    assert side_pots[0].amount == 1500
    assert side_pots[0].eligible_players == [0, 1, 2]
    assert side_pots[1].amount == 600
    print(side_pots[1].eligible_players)
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
    side_pots = node.calculate_side_pots([player1, player2])
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
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.HIGH_CARD
    assert hand_cards == [Card(Rank.ACE, Suit.CLUBS)]
    assert kickers == [
        Card(Rank.KING, Suit.HEARTS),
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.SIX, Suit.HEARTS),
    ]

    # Test pair
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.TEN, Suit.CLUBS)]
    community_cards = [
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.FOUR, Suit.DIAMONDS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.PAIR
    assert hand_cards == [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    assert kickers == [
        Card(Rank.TEN, Suit.CLUBS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.SIX, Suit.HEARTS),
    ]

    # Test two pair
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.ACE, Suit.HEARTS)]
    community_cards = [
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.TWO, Suit.DIAMONDS),
        Card(Rank.SIX, Suit.HEARTS),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.TEN, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.TWO_PAIR
    assert hand_cards == [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.TWO, Suit.CLUBS),
        Card(Rank.TWO, Suit.DIAMONDS),
    ]
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
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.THREE_OF_KIND
    assert hand_cards == [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
    ]
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
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )

    assert (
        HandEvaluator.compare_hands(
            (hand_rank, hand_cards, kickers),
            (
                HandRank.STRAIGHT,
                [
                    Card(Rank.JACK, Suit.CLUBS),
                    Card(Rank.TEN, Suit.SPADES),
                    Card(Rank.NINE, Suit.HEARTS),
                    Card(Rank.EIGHT, Suit.DIAMONDS),
                    Card(Rank.SEVEN, Suit.CLUBS),
                ],
                [],
            ),
        )
        == 0
    )

    # Test flush
    hole_cards = [Card(Rank.ACE, Suit.SPADES), Card(Rank.KING, Suit.SPADES)]
    community_cards = [
        Card(Rank.TWO, Suit.SPADES),
        Card(Rank.FOUR, Suit.SPADES),
        Card(Rank.SIX, Suit.SPADES),
        Card(Rank.EIGHT, Suit.HEARTS),
        Card(Rank.TEN, Suit.CLUBS),
    ]
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.FLUSH
    # print(hand_cards)
    assert hand_cards == [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.SIX, Suit.SPADES),
        Card(Rank.FOUR, Suit.SPADES),
        Card(Rank.TWO, Suit.SPADES),
    ]
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
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.FULL_HOUSE
    assert hand_cards == [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.FOUR, Suit.DIAMONDS),
        Card(Rank.FOUR, Suit.HEARTS),
    ]
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
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.FOUR_OF_KIND
    assert hand_cards == [
        Card(Rank.ACE, Suit.SPADES),
        Card(Rank.ACE, Suit.HEARTS),
        Card(Rank.ACE, Suit.CLUBS),
        Card(Rank.ACE, Suit.DIAMONDS),
    ]
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
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.STRAIGHT_FLUSH
    assert hand_cards == [
        Card(Rank.FIVE, Suit.SPADES),
        Card(Rank.SIX, Suit.SPADES),
        Card(Rank.SEVEN, Suit.SPADES),
        Card(Rank.EIGHT, Suit.SPADES),
        Card(Rank.NINE, Suit.SPADES),
    ]
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
    hand_rank, hand_cards, kickers = HandEvaluator.evaluate_hand(
        hole_cards, community_cards
    )
    assert hand_rank == HandRank.ROYAL_FLUSH
    assert hand_cards == [
        Card(Rank.TEN, Suit.SPADES),
        Card(Rank.JACK, Suit.SPADES),
        Card(Rank.QUEEN, Suit.SPADES),
        Card(Rank.KING, Suit.SPADES),
        Card(Rank.ACE, Suit.SPADES),
    ]
    assert kickers == []


def test_handevaluator_compare_hands():
    # Test high card vs high card
    hand1 = (
        HandRank.HIGH_CARD,
        [Card(Rank.ACE, Suit.SPADES)],
        [
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.CLUBS),
            Card(Rank.JACK, Suit.DIAMONDS),
            Card(Rank.TEN, Suit.SPADES),
        ],
    )
    hand2 = (
        HandRank.HIGH_CARD,
        [Card(Rank.KING, Suit.SPADES)],
        [
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.CLUBS),
            Card(Rank.TEN, Suit.DIAMONDS),
            Card(Rank.NINE, Suit.SPADES),
        ],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == 1

    # Test pair vs pair
    hand1 = (
        HandRank.PAIR,
        [Card(Rank.TWO, Suit.CLUBS), Card(Rank.TWO, Suit.DIAMONDS)],
        [
            Card(Rank.THREE, Suit.HEARTS),
            Card(Rank.FOUR, Suit.SPADES),
            Card(Rank.FIVE, Suit.CLUBS),
        ],
    )
    hand2 = (
        HandRank.PAIR,
        [Card(Rank.THREE, Suit.CLUBS), Card(Rank.THREE, Suit.DIAMONDS)],
        [
            Card(Rank.FOUR, Suit.HEARTS),
            Card(Rank.FIVE, Suit.SPADES),
            Card(Rank.SIX, Suit.CLUBS),
        ],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == -1

    # Test two pair vs two pair
    hand1 = (
        HandRank.TWO_PAIR,
        [
            Card(Rank.THREE, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS),
            Card(Rank.FOUR, Suit.HEARTS),
            Card(Rank.FOUR, Suit.SPADES),
        ],
        [Card(Rank.FIVE, Suit.CLUBS)],
    )
    hand2 = (
        HandRank.TWO_PAIR,
        [
            Card(Rank.FOUR, Suit.CLUBS),
            Card(Rank.FOUR, Suit.DIAMONDS),
            Card(Rank.FIVE, Suit.HEARTS),
            Card(Rank.FIVE, Suit.SPADES),
        ],
        [Card(Rank.SIX, Suit.CLUBS)],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == -1

    # Test three of a kind vs three of a kind
    hand1 = (
        HandRank.THREE_OF_KIND,
        [
            Card(Rank.FIVE, Suit.CLUBS),
            Card(Rank.FIVE, Suit.DIAMONDS),
            Card(Rank.FIVE, Suit.HEARTS),
        ],
        [Card(Rank.SIX, Suit.SPADES), Card(Rank.SEVEN, Suit.CLUBS)],
    )
    hand2 = (
        HandRank.THREE_OF_KIND,
        [
            Card(Rank.SIX, Suit.CLUBS),
            Card(Rank.SIX, Suit.DIAMONDS),
            Card(Rank.SIX, Suit.HEARTS),
        ],
        [Card(Rank.SEVEN, Suit.SPADES), Card(Rank.EIGHT, Suit.CLUBS)],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == -1

    # Test straight vs straight
    hand1 = (
        HandRank.STRAIGHT,
        [
            Card(Rank.SIX, Suit.CLUBS),
            Card(Rank.SEVEN, Suit.DIAMONDS),
            Card(Rank.EIGHT, Suit.HEARTS),
            Card(Rank.NINE, Suit.SPADES),
            Card(Rank.TEN, Suit.CLUBS),
        ],
        [],
    )
    hand2 = (
        HandRank.STRAIGHT,
        [
            Card(Rank.SEVEN, Suit.CLUBS),
            Card(Rank.EIGHT, Suit.DIAMONDS),
            Card(Rank.NINE, Suit.HEARTS),
            Card(Rank.TEN, Suit.SPADES),
            Card(Rank.JACK, Suit.CLUBS),
        ],
        [],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == -1

    # Test flush vs flush
    hand1 = (
        HandRank.FLUSH,
        [
            Card(Rank.TWO, Suit.SPADES),
            Card(Rank.FOUR, Suit.SPADES),
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.EIGHT, Suit.SPADES),
            Card(Rank.TEN, Suit.SPADES),
        ],
        [],
    )
    hand2 = (
        HandRank.FLUSH,
        [
            Card(Rank.THREE, Suit.SPADES),
            Card(Rank.FIVE, Suit.SPADES),
            Card(Rank.SEVEN, Suit.SPADES),
            Card(Rank.NINE, Suit.SPADES),
            Card(Rank.JACK, Suit.SPADES),
        ],
        [],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == -1

    # Test full house vs full house
    hand1 = (
        HandRank.FULL_HOUSE,
        [
            Card(Rank.THREE, Suit.CLUBS),
            Card(Rank.THREE, Suit.DIAMONDS),
            Card(Rank.THREE, Suit.HEARTS),
            Card(Rank.FOUR, Suit.SPADES),
            Card(Rank.FOUR, Suit.CLUBS),
        ],
        [],
    )
    hand2 = (
        HandRank.FULL_HOUSE,
        [
            Card(Rank.FOUR, Suit.CLUBS),
            Card(Rank.FOUR, Suit.DIAMONDS),
            Card(Rank.FOUR, Suit.HEARTS),
            Card(Rank.FIVE, Suit.SPADES),
            Card(Rank.FIVE, Suit.CLUBS),
        ],
        [],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == -1

    # Test four of a kind vs four of a kind
    hand1 = (
        HandRank.FOUR_OF_KIND,
        [
            Card(Rank.FIVE, Suit.CLUBS),
            Card(Rank.FIVE, Suit.DIAMONDS),
            Card(Rank.FIVE, Suit.HEARTS),
            Card(Rank.FIVE, Suit.SPADES),
        ],
        [Card(Rank.SIX, Suit.CLUBS)],
    )
    hand2 = (
        HandRank.FOUR_OF_KIND,
        [
            Card(Rank.SIX, Suit.CLUBS),
            Card(Rank.SIX, Suit.DIAMONDS),
            Card(Rank.SIX, Suit.HEARTS),
            Card(Rank.SIX, Suit.SPADES),
        ],
        [Card(Rank.SEVEN, Suit.CLUBS)],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == -1

    # Test straight flush vs straight flush
    hand1 = (
        HandRank.STRAIGHT_FLUSH,
        [
            Card(Rank.SIX, Suit.SPADES),
            Card(Rank.SEVEN, Suit.SPADES),
            Card(Rank.EIGHT, Suit.SPADES),
            Card(Rank.NINE, Suit.SPADES),
            Card(Rank.TEN, Suit.SPADES),
        ],
        [],
    )
    hand2 = (
        HandRank.STRAIGHT_FLUSH,
        [
            Card(Rank.SEVEN, Suit.SPADES),
            Card(Rank.EIGHT, Suit.SPADES),
            Card(Rank.NINE, Suit.SPADES),
            Card(Rank.TEN, Suit.SPADES),
            Card(Rank.JACK, Suit.SPADES),
        ],
        [],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == -1

    # Test royal flush vs royal flush
    hand1 = (
        HandRank.ROYAL_FLUSH,
        [
            Card(Rank.TEN, Suit.SPADES),
            Card(Rank.JACK, Suit.SPADES),
            Card(Rank.QUEEN, Suit.SPADES),
            Card(Rank.KING, Suit.SPADES),
            Card(Rank.ACE, Suit.SPADES),
        ],
        [],
    )
    hand2 = (
        HandRank.ROYAL_FLUSH,
        [
            Card(Rank.TEN, Suit.HEARTS),
            Card(Rank.JACK, Suit.HEARTS),
            Card(Rank.QUEEN, Suit.HEARTS),
            Card(Rank.KING, Suit.HEARTS),
            Card(Rank.ACE, Suit.HEARTS),
        ],
        [],
    )
    assert HandEvaluator.compare_hands(hand1, hand2) == 0


def test_game_tree_start_game():
    # Create mock players
    player1 = Player(dealer=False, stack=1000)
    player2 = Player(dealer=False, stack=1000)
    player3 = Player(dealer=False, stack=1000)

    # Initialize GameTree
    game_tree = GameTree(
        small_blind=50, big_blind=100, players=[player3, player1, player2]
    )

    # Start the game
    game_tree.start_game()

    # Test initial game state
    assert game_tree.history is not None
    assert len(game_tree.history.get_history()) == 1
    assert game_tree.dealer is not None
    assert player1.get_stack() == 950  # Small blind
    assert player2.get_stack() == 900  # Big blind
    assert player3.get_stack() == 1000
    assert len(player1.get_cards()) == 2
    assert len(player2.get_cards()) == 2
    assert len(player3.get_cards()) == 2


def test_game_tree_get_action_from_player():
    # Create a mock player with a simple strategy
    class MockPlayer(Player):
        def strategy(self, history):
            return Action(ActionType.CALL, 100)

    player = MockPlayer(dealer=False, stack=1000)
    player2 = Player(dealer=False, stack=1000)
    player3 = Player(dealer=False, stack=1000)
    game_tree = GameTree(
        small_blind=50, big_blind=100, players=[player3, player, player2]
    )
    game_tree.start_game()

    # Get action from player
    action = game_tree.get_action_from_player(player)

    # Test action
    assert action.action_type == ActionType.CALL
    assert action.amount == 100


def test_game_tree_next_node():
    class MockPlayer(Player):
        def strategy(self, history):
            return Action(ActionType.CALL, 100)

    # Create mock players
    player1 = MockPlayer(dealer=False, stack=1000)
    player2 = MockPlayer(dealer=False, stack=1000)

    # Initialize GameTree
    game_tree = GameTree(small_blind=50, big_blind=100, players=[player1, player2])
    game_tree.start_game()

    # Advance to the next node
    result = game_tree.next_node()
    print(game_tree.get_current_history()[-1])
    # Test game state after advancing
    assert result is True
    assert len(game_tree.history.get_history()) == 2
    assert game_tree.get_current_history()[-1][0].get_player_to_act() == player1
    assert player1.get_stack() == 900
    assert game_tree.get_current_history()[-1][0].get_stage() == Stage.PRE_FLOP

    result = game_tree.next_node()
    print(game_tree.get_current_history()[-1])
    # Test game state after advancing
    assert result is True
    assert len(game_tree.history.get_history()) == 3
    assert game_tree.get_current_history()[-1][0].get_player_to_act() == player2
    assert player2.get_stack() == 900
    assert game_tree.get_current_history()[-1][0].get_stage() == Stage.PRE_FLOP

    result = game_tree.next_node()
    print(game_tree.get_current_history()[-1])
    # Test game state after advancing
    assert result is True
    assert len(game_tree.history.get_history()) == 4
    assert game_tree.get_current_history()[-1][0].get_stage() == Stage.FLOP
    assert game_tree.get_current_history()[-1][1].action_type == ActionType.DEAL


def test_game_tree_checkout():
    # Create mock players
    class MockPlayer(Player):
        def strategy(self, history):
            return Action(ActionType.CALL, 100)

    player1 = MockPlayer(dealer=False, stack=1000)
    player2 = MockPlayer(dealer=False, stack=1000)

    # Initialize GameTree
    game_tree = GameTree(small_blind=50, big_blind=100, players=[player1, player2])
    game_tree.start_game()

    while game_tree.next_node():
        print(game_tree.get_current_history()[-1])

    # Mock player hands
    player1.set_cards([Card(Rank.ACE, Suit.HEARTS), Card(Rank.KING, Suit.CLUBS)])
    player2.set_cards([Card(Rank.TWO, Suit.HEARTS), Card(Rank.THREE, Suit.CLUBS)])

    # Perform checkout
    game_tree.checkout()

    print(player1.get_stack())
    print(player2.get_stack())

    # Test final player stacks
    assert player1.get_stack() == 1400  # Player 1 wins the pot
    assert player2.get_stack() == 600


if __name__ == "__main__":
    test_player_initialization()
    test_player_betting()
    test_player_cards()
    test_player_fold()
    test_player_reset()
    test_game_node_initialization()
    test_game_node_side_pots()
    test_hand_evaluator()
    test_handevaluator_compare_hands()
    test_game_tree_start_game()
    test_game_tree_get_action_from_player()
    test_game_tree_next_node()
    test_game_tree_checkout()
