import json
import sys
import os

n = 0

os.mkdir("fetcher_inbox")

for line in open(sys.argv[-1]):
    name = "fetcher_inbox/0-seed_0_0_{}".format(n)

    with open(name, 'w') as f:
        f.write(json.dumps({"url": line.strip()}))

    n += 1
