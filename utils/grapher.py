import psycopg2
import sys


DB_CONFIG = {
    "database": "unshadow",
    "user": "unshadow",
    "password": "",
    "port": 5432,
    "host": "localhost"
}


QUERY = """
SELECT distinct src, dst FROM graph
join domain sd on sd.location = src
join domain ld on ld.location = dst
where sd.accessible = true
and ld.accessible = true
"""

mode = sys.argv[-1]

if mode == "complex":
    QUERY = """
        SELECT graph.src, graph.dst FROM graph
        JOIN domain ON domain.location = graph.dst
        WHERE domain.accessible = true
    """

db = psycopg2.connect(**DB_CONFIG)
cursor = db.cursor()

cursor.execute(QUERY)

with open("tor-new.csv", "w") as f:
    f.write("Source,Target\n")

    for index, row in enumerate(cursor):
        src = row[0]
        tgt = row[1]
        f.write("{},{}\n".format(src, tgt))
