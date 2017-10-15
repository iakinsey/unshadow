import urllib
import lxml.html
import os
import string
import math
import json


from unshadow.dispatch import Stage
from lxml.html.clean import clean_html
from nltk.corpus import stopwords
from nltk import word_tokenize
from collections import Counter
from heapq import nlargest
from urllib.parse import urlparse
from operator import itemgetter
from unshadow.db import DatabaseClass
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException


PUNCTUATION_MAP = str.maketrans({i: ' ' for i in string.punctuation})
STOPWORDS = stopwords.words('english')
BAD_TAGS = ['script', 'style']


class LanguageAnalyzer(Stage, DatabaseClass):
    '''
    Computes term frequency and language of web content.
    '''

    SCHEMA = """
        CREATE TABLE fingerprint (
            url VARCHAR NOT NULL,
            domain VARCHAR NOT NULL,
            language VARCHAR,
            term_frequency VARCHAR
        );
    """

    INSERT_ID_QUERY = """
        INSERT INTO fingerprint (domain, url, language, term_frequency)
        VALUES (%s, %s, %s, %s)
    """

    def init(
        self,
        tf_limit=50,
        db_name=None,
        db_user=None,
        db_pass=None,
        db_host=None,
        db_port=None
    ):
        self.tf_limit = tf_limit
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_host = db_host
        self.db_port = db_port

        self.setup_database('fingerprint')

    def on_message(self, message):
        origin_url = message['origin']
        content_path = message.get('content_path', None)
        language = None
        term_frequency = None
 
        if content_path:
            descriptor = open(content_path, 'rb')
            words = self.get_words(descriptor)

            if words:
                language = self.get_language(words)

                if language == "en":
                    term_frequency = self.find_tf(words)

                if language:
                    self.insert_fingerprint(origin_url, term_frequency, language)
                
            os.remove(content_path)

    def insert_fingerprint(self, url, tf, language):
        domain = urlparse(url).netloc

        with self.get_cursor() as cursor:
            args = (domain, url, language, json.dumps(tf))
            cursor.execute(self.INSERT_ID_QUERY, args)

            self.db.commit()


    def get_document(self, html_content):
        document = None

        try:
            document = lxml.html.document_fromstring(html_content)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass

        return document

    def replace_escapes(self, text):
        return text.replace("\n", "").replace("\t", "").replace("\r", "")

    def get_words(self, descriptor):
        content = descriptor.read().decode("utf-8", "ignore")
        document = self.get_document(content)

        if document is not None:
            document = clean_html(document)
            extracted_text = document.text_content()
            without_escapes = self.replace_escapes(extracted_text)
            as_lower_case = without_escapes.lower()
            without_punctuation = as_lower_case.translate(PUNCTUATION_MAP)

            return without_punctuation

    def find_tf(self, words):
        tokens = word_tokenize(words)
        words = [w for w in tokens if w not in STOPWORDS]

        return self.limit_tf(Counter(words))

    def limit_tf(self, counter):
        return nlargest(self.tf_limit, counter.items(), key=itemgetter(1))

    def get_language(self, words):
        try:
            return detect(words)
        except LangDetectException:
            return None
