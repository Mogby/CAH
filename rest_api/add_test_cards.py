from game.models import Card


NUM_BLACK_CARDS = 50
NUM_WHITE_CARDS = 200
for i in range(NUM_BLACK_CARDS):
    Card.create_card('_ #{}'.format(i+1), True)
for i in range(NUM_WHITE_CARDS):
    Card.create_card('White card #{}'.format(i+1), False)
