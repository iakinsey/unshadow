from wordcloud import WordCloud
import collections
import json
import math
import psycopg2


DB_CONFIG = {
    "database": "unshadow",
    "user": "unshadow",
    "password": "",
    "port": 5432,
    "host": "localhost"
}


QUERY = """
SELECT term_frequency from fingerprint
where term_frequency is not null and term_frequency != 'null'
"""

db = psycopg2.connect(**DB_CONFIG)
cursor = db.cursor()
blacklist = open("blacklist").read().split()

cursor.execute(QUERY)
document_count = 0
term_occurence_count = collections.defaultdict(int)


for row in cursor:
    document_count += 1
    tf = json.loads(row[0])

    for term, count in tf:
        if term not in blacklist:
            term_occurence_count[term] += 1


#with open("idf.csv", "w") as f:
#    for term, count in term_occurence_count.items():
#        if count != 0:
#            idf = math.log(document_count / count)
#            f.write("{},{}\n".format(term, idf))


with open("counter", "w") as f:
    for term, count in term_occurence_count.items():
        if count != 0:
            kind_of_idf = int(math.log(document_count / count) * 1000)

            try:
                for n in range(kind_of_idf):
                    f.write(term + "\n")
            except UnicodeEncodeError:
                pass


with open("counter", "r") as f:
    wordcloud = WordCloud(
        font_path="/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
        width=4000,
        height=4000
    )

    wordcloud.generate(f.read())
    #plt.show(wordcloud)
    #plt.axis("off")
    wordcloud.to_file("./idf-cloud.png")
