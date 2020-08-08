import json

from game.models import Card

with open('test.json', 'r') as default_cards:
    card_pack = json.load(default_cards)

for blackCard in card_pack["blackCards"]:
    Card.create_card(blackCard, True)

for whiteCard in card_pack["whiteCards"]:
    Card.create_card(whiteCard, False)
