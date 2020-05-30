import random

from game.models import Player, Round


class BotBase:
    def __init__(self, player, game):
        self._player = player
        self._game = game
        self.init()

    def update(self):
        self._game.refresh_from_db()

        round = self._game.current_round
        if round is None:
            return
        round_state = round.get_state()
        if round_state == Round.State.PLAY and round.card_czar != self._player:
            self._play()
        elif round_state == Round.State.PICK and round.card_czar == self._player:
            self._pick()

    def init(self):
        pass

    def _play(self):
        raise NotImplementedError()

    def _pick(self):
        raise NotImplementedError()


class RandomBot(BotBase):
    def _play(self):
        card = random.choice(self._player.current_hand.cards.all())
        Player.play_card(self._player.auth_token, card.id)

    def _pick(self):
        card = random.choice(self._game.current_round.turn_set.all()).card
        Player.play_card(self._player.auth_token, card.id)

