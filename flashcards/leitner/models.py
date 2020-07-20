from typing import Optional

from django.conf import settings
from django.db import models

"""
Models for the Leitner System, see  https://en.wikipedia.org/wiki/Leitner_system
"""


class Deck(models.Model):
    description = models.CharField('Deck description', max_length=150)
    created_by = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='decks')

    def create_boxes(self):
        defaults = {'in_session': False, 'last_used': None, 'deck': self}
        Box.objects.create(description='Use this every day', box_type=0, **defaults)
        Box.objects.create(description='Use this every tuesday and thursday', box_type=1, **defaults)
        Box.objects.create(description='Use this every friday', box_type=2, **defaults)

    def __str__(self):
        return self.description


class Box(models.Model):
    description = models.CharField('Box description', max_length=150)
    deck = models.ForeignKey(to=Deck, on_delete=models.CASCADE, related_name='boxes')
    in_session = models.BooleanField('Box currently in session?', default=False)
    box_type = models.IntegerField('0: Everyday, 1: Tue/Thu, 2: Fri')
    last_used = models.DateTimeField(null=True)

    def last_used_text(self):
        return 'Never' if self.last_used is None else self.last_used.strftime('%a %d %b %Y %H:%M')

    def __str__(self):
        return f'Box: {self.description} | Last used: {self.last_used_text()}'


class Card(models.Model):
    front_text = models.CharField('Front text', max_length=150)
    back_text = models.TextField('Back text')
    updated_at = models.DateTimeField('Last modified on', auto_now=True)
    on_deck = models.ForeignKey(to=Deck, on_delete=models.CASCADE, related_name='cards')
    on_box = models.ForeignKey(to=Box, on_delete=models.CASCADE, related_name='cards')

    def correct_answer(self) -> None:
        """
        Moves the card to the next box, given a correct answer. Requires the box to be in a session
        """
        current_box_num = self.on_box.box_type

        if current_box_num < self.on_deck.boxes.count() - 1:  # Nothing happens if the card is on the last box
            self.on_box = self.on_deck.boxes.get(box_type=current_box_num + 1)
            self.save()

        SessionFinishedCards.objects.create(session=self.on_deck.session.get(), card=self)

    def wrong_answer(self) -> None:
        """
        Moves the card to the box type 0, given a wrong answer. Requires the box to be in a session
        """
        self.on_box = self.on_deck.boxes.get(box_type=0)
        self.save()
        SessionFinishedCards.objects.create(session=self.on_deck.session.get(), card=self)


class Session(models.Model):
    deck = models.ForeignKey(Deck, on_delete=models.CASCADE, related_name='session')
    current_box = models.ForeignKey(Box, on_delete=models.CASCADE, related_name='session')
    total_cards_on_box = models.IntegerField('Total cards of the current box')
    is_finished = models.BooleanField('Is the session finished?', default=False)

    def current_card(self) -> Optional[Card]:
        """
        Gets the current card to use in the study session
        """
        qs = Card.objects.filter(on_box=self.current_box).exclude(finished_session__session=self).order_by(
            'updated_at').first()
        return qs


class SessionFinishedCards(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='finished_cards')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='finished_session')
