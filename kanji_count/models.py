from __future__ import unicode_literals

from collections import defaultdict, Counter

from django.db import models

import requests
from bs4 import BeautifulSoup

# Source: http://www.rikai.com/library/kanjitables/kanji_codes.unicode.shtml
FIRST_COMMON_KANJI = '一'  # \u4e00 - ord=19968
LAST_COMMON_KANJI = '龥'  # \u9fa5 - ord=40869
FIRST_RARE_KANJI = '㐀'  # \u3400 - ord=13312
LAST_RARE_KANJI = '䶵'  # \u4db5 - ord=19893


class Article(models.Model):
    """
    An article that we will be reading the contents of to count the number
    of known kanji.

    :cvar str url: URL of the article
    :cvar str title: Title of the webpage at URL
    :cvar str content: The HTML Content of the webpage at URL.
    """
    url = models.URLField(unique=True, blank=False)
    title = models.CharField(max_length=100)
    content = models.TextField()

    @classmethod
    def from_url(cls, url: str):
        """
        Creates or updates an Article from the given url, doing all of the
        counting of kanji.

        :param url: a string url to an article.
        :return: The newly created Article
        :rtype: Article
        """
        article, _ = cls.objects.get_or_create(url=url)
        article.content = article.get_content(url)
        article.title = article.get_title(article.content)
        article.save()

        # Count the Kanji on the page
        article.count_kanji()

        return article

    def count_kanji(self) -> None:
        """
        Counts the Kanji for this webpage.
        """
        tagless_content = self.remove_tags(self.content)
        counter = Counter((char for char in tagless_content if is_kanji(char)))

        for character, count in counter.items():
            KanjiCount.objects.get_or_create(article=self,
                                             kanji=character,
                                             total=count)

    @staticmethod
    def get_content(url: str) -> str:
        """
        Gets the content of the webpage at url.

        :param url: URL of the webpage we are getting the content of.
        :return: The content of the webpage
        """
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    @staticmethod
    def get_title(content: str) -> str:
        """
        Gets the title of the webpage from the content.

        :param content: HTML content of a webpage
        :return: the title found in that webpage
        """
        soup = BeautifulSoup(content, "html.parser")
        return soup.title.string

    @staticmethod
    def remove_tags(content: str) -> str:
        """
        Removes the html tags from the content.

        :param content: Some HTML content we are removing the tags from.
        :return: content that no longer has tags in it.
        """
        soup = BeautifulSoup(content, "html.parser")
        return soup.body.get_text()


class KanjiCount(models.Model):
    """
    The count of a single Kanji in an article.
    """
    article = models.ForeignKey(Article)
    kanji = models.CharField(max_length=1)
    total = models.PositiveIntegerField()

    def __str__(self):
        return "{kanji}: {total}".format(kanji=self.kanji, total=self.total)

    class Meta:
        unique_together = ('article', 'kanji')


def is_kanji(character: str) -> bool:
    """
    Returns True if the character is a Kanji character, false otherwise.

    :param character: a single character that may or may not be Kanji.
    :return: True if it's kanji, False otherwise.
    """
    if ord(FIRST_COMMON_KANJI) <= ord(character) <= ord(LAST_COMMON_KANJI) \
            or ord(FIRST_RARE_KANJI) <= ord(character) <= ord(LAST_RARE_KANJI):
        return True
    return False
