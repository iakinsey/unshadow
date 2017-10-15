mport sys
import time
import json


domains = set()
counter = 0


with open(sys.argv[-1]) as f:
    for line in f:
        for domain in  line.strip().split(","):
            url = "http://{}".format(domain)

            if url not in domains:
                domains.add(url)
                now = int(time.time())
                name = "0-Export_0_{}_{}".format(now, counter)
                path = "ungraph/{}".format(name)

                print("Exporting {}".format(url))

                with open(path, 'w') as e:
                    e.write(json.dumps({"url": url}))

                counter += 1
