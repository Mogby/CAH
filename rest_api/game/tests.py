from django.db.models import Max, Sum
from django.test import TestCase

from game.errors import *
from game.models import *
from game.bots import RandomBot


class CAHTestCase(TestCase):

    # Custom assertions

    def assertGameState(self, game, status, host=None, players=None):
        if players is None:
            players = []

        self.assertEqual(game.status, status)
        self.assertEqual(game.host, host)
        self.assertEqual(set(game.player_set.all()), set(players))

    def assertGameFinished(self, game):
        self.assertGameState(
            game,
            Game.Status.FINISHED
        )

    # API wrappers

    def create_new_player(self, name):
        try:
            return Player.create_new_player(name)
        except Exception as e:
            self.fail('create_new_player raised exception: {}'.format(str(e)))

    def get_players_by_ids(self, ids):
        try:
            return Player.get_players_by_ids(ids)
        except Exception as e:
            self.fail('get_players_by_ids raised exception: {}'.format(str(e)))

    def get_player_by_token(self, token):
        try:
            return Player.get_player_by_token(token)
        except Exception as e:
            self.fail('get_player_by_token raised exception: {}'.format(str(e)))

    def create_game(self, host):
        try:
            new_game = Player.create_game(host.auth_token)
        except Exception as e:
            self.fail('create_game raised exception: {}'.format(str(e)))
        host.refresh_from_db()
        return new_game

    def start_game(self, host):
        try:
            Player.start_game(host.auth_token)
        except Exception as e:
            self.fail('start_game raised exception: {}'.format(str(e)))
        host.refresh_from_db()

    def join_game(self, player, game):
        try:
            Player.join_game(player.auth_token, game.id)
        except Exception as e:
            self.fail('join_game raised exception: {}'.format(str(e)))
        player.refresh_from_db()
        game.refresh_from_db()

    def leave_game(self, player):
        try:
            Player.leave_game(player.auth_token)
        except Exception as e:
            self.fail('leave_game raised exception: {}'.format(str(e)))
        player.refresh_from_db()


class ModelsTestCase(CAHTestCase):
    def setUp(self):
        for i in range(50):
            Card.objects.create(
                text='Black card #{}'.format(i),
                is_black=True,
                pick=1,
            )
        for i in range(200):
            Card.objects.create(
                text='White card #{}'.format(i),
                is_black=False,
            )

    def test_create_player(self):
        self.create_new_player('mogbymo')
        self.create_new_player('abgde')

    def test_get_player(self):
        player1 = self.create_new_player('mogbymo')
        player2 = self.create_new_player('abgde')

        player1_by_id = self.get_players_by_ids([player1.id])
        self.assertEqual([player1], list(player1_by_id))

        players_by_ids = self.get_players_by_ids([
            player1.id,
            player2.id
        ])
        self.assertEqual(set([player1, player2]), set(players_by_ids))

        player1_by_token = self.get_player_by_token(player1.auth_token)
        self.assertEqual(player1, player1_by_token)

    def test_create_game(self):
        player = self.create_new_player('mogbymo')

        game1 = self.create_game(player)
        game2 = self.create_game(player)

        game1.refresh_from_db()
        game2.refresh_from_db()
        player.refresh_from_db()

        self.assertGameFinished(game1)
        self.assertGameState(
            game2,
            Game.Status.CREATED,
            player,
            [player]
        )

    def test_join_game(self):
        player1 = self.create_new_player('mogbymo')
        player2 = self.create_new_player('abgde')

        game1 = self.create_game(player1)
        game2 = self.create_game(player2)

        self.join_game(player1, game2)

        game1.refresh_from_db()
        game2.refresh_from_db()

        self.assertGameFinished(game1)
        self.assertGameState(
            game2,
            Game.Status.CREATED,
            player2,
            [player1, player2]
        )

    def test_leave_game(self):
        player1 = self.create_new_player('mogbymo')
        player2 = self.create_new_player('abgde')

        game = self.create_game(player1)

        with self.assertRaises(PlayerNotInGameError):
            Player.leave_game(player2.auth_token)

        self.join_game(player2, game)

        game.refresh_from_db()
        self.assertGameState(
            game,
            Game.Status.CREATED,
            player1,
            [player1, player2]
        )

        self.leave_game(player1)

        game.refresh_from_db()
        self.assertGameState(
            game,
            Game.Status.CREATED,
            player2,
            [player2]
        )

        self.leave_game(player2)

        game.refresh_from_db()
        self.assertGameFinished(game)

    def test_start_game(self):
        self.assertLessEqual(3, Game.MIN_PLAYERS)
        self.assertLessEqual(Game.MIN_PLAYERS, Game.MAX_PLAYERS)

        host = self.create_new_player('host')
        game = self.create_game(host)

        players = [host]
        for i in range(1, Game.MAX_PLAYERS):
            if i < Game.MIN_PLAYERS:
                with self.assertRaises(NotEnoughPlayersError):
                    Player.start_game(host.auth_token)
            players.append(self.create_new_player('player_{}'.format(i)))
            self.join_game(players[-1], game)

        extra_player = self.create_new_player('extra_player')
        with self.assertRaises(GameIsFullError):
            Player.join_game(extra_player.auth_token, game.id)

        with self.assertRaises(PermissionDeniedError):
            game.start_by(extra_player)

        game.refresh_from_db()
        self.assertGameState(
            game,
            Game.Status.CREATED,
            host,
            players
        )

        self.start_game(host)

        game.refresh_from_db()
        self.assertGameState(
            game,
            Game.Status.STARTED,
            host,
            players
        )

        for player in players:
            player.refresh_from_db()
            self.assertEqual(
                player.current_hand.cards.count(),
                Game.HAND_SIZE
            )
            self.assertEqual(player.score, 0)

        Player.leave_game(host.auth_token)

        host.refresh_from_db()
        self.assertEqual(host.current_game, None)
        self.assertEqual(host.current_hand, None)
        self.assertEqual(host.score, None)


class GameplayTest(CAHTestCase):
    def test_game(self):
        Game.FINISH_DELAY_SECONDS = 0
        Game.WINNER_SCORE = 3

        for i in range(2):
            Card.objects.create(
                text='Black card #{}'.format(i),
                is_black=True,
                pick=1,
            )
        for i in range(Game.MAX_PLAYERS * Game.HAND_SIZE):
            Card.objects.create(
                text='White card #{}'.format(i),
                is_black=False,
            )

        players = []
        for i in range(Game.MAX_PLAYERS):
            new_player = self.create_new_player('monkey_{}'.format(i))
            players.append(new_player)

        host = players[0]
        game = self.create_game(host)
        player_bot = {}
        for player in players:
            if player != host:
                self.join_game(player, game)
            player_bot[player] = RandomBot(player, game)


        max_possible_score = \
                Game.WINNER_SCORE \
                + (Game.WINNER_SCORE - 1) * (len(players) - 1)
        score_sum = 0
        self.start_game(host)
        game.refresh_from_db()
        game._update_state()
        while game.status == Game.Status.STARTED:
            self.assertEqual(game.current_round.get_state(), Round.State.PLAY)

            card_czar = game.current_round.card_czar
            for player in players:
                if player != card_czar:
                    player_bot[player].update()

            game.refresh_from_db()
            game._update_state()
            self.assertEqual(game.current_round.get_state(), Round.State.PICK)

            player_bot[card_czar].update()

            game.refresh_from_db()
            new_score_sum = \
                    game.player_set.aggregate(Sum('score'))['score__sum']
            self.assertEqual(score_sum + 1, new_score_sum)
            self.assertLess(new_score_sum, max_possible_score)
            score_sum = new_score_sum

            while game.current_round.get_state() == Round.State.WAITING_FINISH:
                game.refresh_from_db()
                game._update_state()

            game.refresh_from_db()
            game._update_state()

        winner_score = game.player_set.aggregate(Max('score'))['score__max']
        self.assertEqual(winner_score, Game.WINNER_SCORE)


class DequeTestCase(CAHTestCase):
    def test_simple(self):
        deque = Deque.objects.create()
        deque.add_cards([1, 2, 3])
        deque.shuffle()
        picked_cards = deque.draw_cards(2)

        self.assertEqual(deque.get_size(), 1)
        self.assertEqual(deque.cards, deque.deque)
        self.assertEqual(
            set(picked_cards + deque.deque),
            set([1, 2, 3])
        )

        deque.add_cards(picked_cards)

        self.assertEqual(deque.get_size(), 3)
        self.assertEqual(set(deque.cards), set([1, 2, 3]))

        picked_cards = [deque.draw_single_card()]

        self.assertEqual(deque.get_size(), 2)
        self.assertEqual(set(deque.deque), set(deque.deque))
        self.assertEqual(
            set(picked_cards + deque.deque),
            set([1, 2, 3])
        )

    def test_pick_too_many(self):
        deque = Deque.objects.create()
        deque.add_cards([1, 2, 3])
        with self.assertRaises(NotEnoughCardsError):
            deque.draw_cards(4)

    def test_shuffle(self):
        deque = Deque.objects.create()
        cards = [i for i in range(100)]
        deque.add_cards(cards)
        deque.shuffle()

        self.assertNotEqual(deque.deque, cards)
        self.assertEqual(set(deque.deque), set(cards))

    def test_repeated_cards(self):
        deque = Deque.objects.create()
        deque.add_cards([1, 1, 1, 1, 1])
        deque.draw_single_card()

        self.assertEqual(deque.deque, [1, 1, 1, 1])
        self.assertEqual(deque.cards, [1, 1, 1, 1])

    def test_remove(self):
        deque = Deque.objects.create()
        deque.add_cards([1, 1, 2, 3, 3])
        deque._remove_cards([1, 1, 2])

        self.assertEqual(deque.cards, [3, 3])

        with self.assertRaises(CardNotInDequeError):
            deque._remove_cards([1])


class QueueTestCase(CAHTestCase):
    def test_simple(self):
        queue = Queue.objects.create()

        queue.add_item(1)
        queue.add_item(2)
        queue.add_item(3)

        self.assertEqual(queue.pop_item(), 1)
        self.assertEqual(queue.pop_item(), 2)
        self.assertEqual(queue.pop_item(), 3)
        self.assertEqual(queue.pop_item(), None)

    def test_remove_item(self):
        queue = Queue.objects.create()

        queue.add_item(1)
        queue.add_item(2)
        queue.add_item(3)

        queue.remove_item(2)

        self.assertEqual(queue.pop_item(), 1)
        self.assertEqual(queue.pop_item(), 3)
        self.assertEqual(queue.pop_item(), None)

