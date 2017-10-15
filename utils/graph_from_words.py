import psycopg2
import sys


DB_CONFIG = {
    "database": "unshadow",
    "user": "unshadow",
    "password": "",
    "port": 5432,
    "host": "localhost"
}


db = psycopg2.connect(**DB_CONFIG)
cursor = db.cursor()
word = sys.argv[-1]


QUERY = """
    SELECT distinct graph.src, graph.dst
    FROM graph
    JOIN fingerprint f_dst ON f_dst.domain = graph.dst
    JOIN fingerprint f_src ON f_src.domain = graph.src
    WHERE f_dst.term_frequency ilike '%["{word}",%'
    AND f_src.term_frequency ilike '%["{word}",%'
""".format(word=word)

cursor.execute(QUERY)


with open("tor-{}-graph.csv".format(word), "w") as f:
    f.write("Source,Target\n")

    for index, row in enumerate(cursor):
        src = row[0]
        tgt = row[1]
        f.write("{},{}\n".format(src, tgt))
