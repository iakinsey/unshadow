from urllib.parse import urlparse
from time import time

from unshadow.dispatch import DBStage


class URLFilter(DBStage):
    '''
    Extracts links from urls.
    '''

    tables = {
        "url": {
            "url": "VARCHAR",
            "location": "VARCHAR",
            "found": "INT",
            "last_seen": "INT",
            "origin": "VARCHAR",
            "title": "VARCHAR",
        }
    }

    def on_message(self, message):
        results = []
        urls = message['urls']
        title = message['title']
        origin = message['origin']

        # Create or update origin
        self.get_or_update_origin(origin, title)

        # Get or create urls
        for url in urls:
            if self.get_or_create_url(url, origin):
                results.append({
                    "url": url,
                    "origin": origin
                })

        self.log.info("{} URLS passed through".format(len(results)))

        return results

    def set_or_update_url(self, mapper):
        """
        Sets or updates URL.
        Returns True if item was updated, False if item is new.
        """

        url = self.get("url", "url", mapper["url"])

        if not url:
            self.set("url", mapper)

            return True
        else:
            update_mapper = {"last_seen": mapper["last_seen"]}
            self.update("url", "url", mapper["url"], update_mapper)

            return False

    def get_or_create_url(self, url, origin_url):
        location = urlparse(origin_url).netloc

        return self.set_or_update_url({
            "location": location,
            "url": url,
            "origin": origin_url,
            "title": None,
            "found": int(time()),
            "last_seen": int(time())
        })

    def get_or_update_origin(self, origin_url, title):
        location = urlparse(origin_url).netloc

        self.set_or_update_url({
            "location": location,
            "url": origin_url,
            "origin": None,
            "title": title,
            "found": int(time()),
            "last_seen": int(time())
        })
