import urllib
import urllib.parse
import lxml.html
import os


from unshadow.dispatch import Stage


class LinkExtractor(Stage):
    '''
    Extracts links from urls.
    '''

    def on_message(self, message):
        origin_url = message['origin']
        content_path = message['content_path']
 
        if content_path:
            metadata = self.parse_page(content_path, origin_url)

            message.update(metadata)
            os.remove(content_path)
            del message['content_path']

        self.add_additional_urls(message)
        
        self.log.info('{} urls extracted'.format(len(message.get('urls', []))))

        return message

    def add_additional_urls(self, message):
        redirect = message.get("redirect", None)
        origin = message['origin']
        urls = message.get('urls', [])

        if redirect is not None:
            urls.append(redirect)

        metadata = urllib.parse.urlparse(origin)
        urls.append("{}://{}".format(metadata.scheme, metadata.netloc))

        message['urls'] = urls

    def parse_page(self, path, origin_url):
        metadata = {}

        with open(path, 'rb') as f:
            html_content = f.read()

        document = self.get_document(html_content)

        if document is not None:
            metadata.update({
                'urls': self.get_urls(document, origin_url),
                'title': self.get_title(document),
                "description": self.get_description(document)
            })

        return metadata

    def get_title(self, document):
        title_elem = document.find('.//title')

        return title_elem.text if title_elem is not None else None

    def get_description(self, document):
        desc_elem = document.find('.//meta[@name="description"]')

        return desc_elem.get("content") if desc_elem is not None else None

    def get_document(self, html_content):
        document = None

        try:
            document = lxml.html.document_fromstring(html_content)

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            pass

        return document

    def get_urls(self, document, origin_url):
        urls = []

        for document_link in document.iterlinks():
            url = self.clean_url(document_link[2], origin_url)
            if url:
                urls.append(url)
            else:
                self.save_garbage(url, origin_url)

        self.log.info('{} urls extracted'.format(len(urls)))

        return urls

    def save_garbage(self, url, origin_url):
        pass

    def clean_url(self, url, origin_url):
        try:
            origin_url_metadata = urllib.parse.urlparse(origin_url)
            url_metadata = urllib.parse.urlparse(url)

            if url.startswith("//"):
                origin_scheme = origin_url_metadata.scheme
                url = "{}:{}".format(origin_scheme, url)

            if not url_metadata.netloc:
                url = urllib.parse.urljoin(origin_url, url_metadata.path)

            new_metadata = urllib.parse.urlparse(url)
            base = "{}://{}".format(new_metadata.scheme, new_metadata.netloc)
            quoted_url = urllib.parse.quote(new_metadata.path)

            return urllib.parse.urljoin(base, quoted_url)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.log.warning("Parse failed with: {}".format(e))

            return None
