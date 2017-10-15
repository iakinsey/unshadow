from collections import defaultdict, Counter
from wordcloud import WordCloud
import psycopg2
import sys
import json


DB_CONFIG = {
    "database": "unshadow_language",
    "user": "unshadow",
    "password": "",
    "port": 5432,
    "host": "localhost"
}


QUERY = """
SELECT term_frequency from fingerprint
WHERE term_frequency IS NOT NULL
"""


db = psycopg2.connect(**DB_CONFIG)
cursor = db.cursor()

cursor.execute(QUERY)
#counter = defaultdict(int)
counter = Counter()
BLACKLIST = open("blackist").read().split()


for row in cursor:
    data = row[0]
    if data != "null":
        frequency = json.loads(data)
        counter.update(dict(frequency))


final_counter = Counter()


for key, count in dict(counter).items():
    if len(key) > 4 and key not in BLACKLIST:
        final_counter.update({key: count})




with open("counter.json", "w") as f:
    for word, count in final_counter.items():
        try:
            for n in range(count):
                f.write(word + "\n")
        except UnicodeEncodeError:
            pass

with open("counter.json", "r") as f:
    wordcloud = WordCloud(
        font_path="/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        width=4000,
        height=4000
    )

    wordcloud.generate(f.read())
    #plt.show(wordcloud)
    #plt.axis("off")
    wordcloud.to_file("./cloud.png")
