from django.db import models
from django.contrib.auth.models import User
from typing import Tuple, List

from django.db.models import Sum, F, FloatField, ExpressionWrapper

from kanji_count.models import Kanji, Article


class UserProfile(models.Model):
    """
    Profile holds non-authentication related fields for the user.
    """
    user = models.OneToOneField(User)
    known_kanji = models.ManyToManyField('kanji_count.Kanji')

    def __str__(self):
        return str(self.user)

    def add_known_kanji(self, char: str) -> None:
        """
        Adds the character to this user's known_kanji list.

        :param char: a Kanji character
        """
        self.known_kanji.add(Kanji.objects.get(char=char))

    def get_articles(self) -> List[Tuple[Article, float]]:
        """
        Gets a list of tuples of the Article, and the ratio of known kanji
            to unknown in the article.
        """
        return Article.objects\
            .filter(kanjicount__kanji__in=self.known_kanji.all())\
            .annotate(known=ExpressionWrapper(
                (Sum('kanjicount__total') * 1.0)/F('kanji_total'),
                output_field=FloatField())).order_by('-known')
