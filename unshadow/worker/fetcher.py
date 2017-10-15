import base64
import functools
import hashlib
import http.client
import io
import pycurl
import os
import shutil
import time
import urllib.parse


from unshadow.dispatch import Stage


class MockSocket:
    def __init__(self, raw):
        self._file = io.BytesIO(raw)

    def makefile(self, *args, **kwargs):
        return self._file


class Fetcher(Stage):
    def init(
        self,
        max_http_retries=5,
        max_size=None,
        user_agent='',
        enable_proxy=False,
        proxy_host=None,
        proxy_port=None,
        content_folder='',
        outboxes=[]
    ):
        self.max_http_retries = max_http_retries
        self.max_size = max_size
        self.content_folder = content_folder
        self.user_agent = user_agent
        self.enable_proxy = enable_proxy
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.content_folder = content_folder
        self.outboxes = outboxes

        self.generate_content_folders()

    def claim_file(self):
        if self.outbox_has_space:
            all_files = os.listdir(self.inbox)
            self.report_metric("inbox_size",  len(all_files))
            paths = filter(self.inbox_regex.match, all_files)

            for file_name in sorted(paths, key=lambda i: int(i.split('-')[0])):
                old_path = os.path.join(self.inbox, file_name)
                new_path = os.path.join(self.inbox,
                                        "{}.claimed".format(file_name))

                try:
                    shutil.move(old_path, new_path)
                except (KeyboardInterrupt, SystemExit):
                    self.kill_process()
                except:
                    pass
                else:
                    return new_path

    @property
    def outbox_has_space(self):
        if self.ignore_outbox:
            return True

        for outbox in self.outboxes:
            inbox = outbox['inbox']

            if len(os.listdir(inbox)) > self.outbox_max_size:
                return False
        
        return True

    def generate_content_folders(self):
        self.create_directory(self.content_folder)

        for outbox in self.outboxes:
            content_folder = outbox['content']
            self.create_directory(content_folder)

    def create_directory(self, path):
        try:
            os.makedirs(path)
        except OSError:
            pass

    def create_content_buffer(self):
        name = "{}_{}_{}".format(
            self.pid,
            int(time.time()),
            self.sequence
        )

        path = os.path.join(self.content_folder, name)
        f = open(path, 'wb')

        return f, path

    def write_data(self, md5_buffer, content_buffer, data):
        md5_buffer.update(data)
        content_buffer.write(data)

        if self.max_size and content_buffer.tell() >= self.max_size:
            return -1

    def write_header(self, buffer, data):
        if data.find(b'Content-Type') == 0:
            # Content type message part
            if not (b'html' in data or b'plain' in data):
                buffer.seek(0)
                return -1

        buffer.write(data)

    def get_url(self, url):
        metadata = urllib.parse.urlparse(url)
        header_buffer = io.BytesIO()
        content_buffer, path = self.create_content_buffer()
        md5_buffer = hashlib.md5()
        write_fn = functools.partial(
            self.write_data,
            md5_buffer,
            content_buffer
        )

        header_fn = functools.partial(self.write_header, header_buffer)

        curl = pycurl.Curl()
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEFUNCTION, write_fn)
        curl.setopt(curl.HEADERFUNCTION, header_fn)
        curl.setopt(curl.USERAGENT, self.user_agent)

        if self.enable_proxy:
            curl.setopt(curl.PROXY, self.proxy_host)
            curl.setopt(curl.PROXYPORT, self.proxy_port)
            curl.setopt(curl.PROXYTYPE, 7)

        self.log.debug("GET: {}".format(url))

        start = time.time()
        success = self.perform_get(
            curl,
            metadata.scheme,
            self.max_http_retries
        )
        end = time.time()

        if success and success != -1:
            http_code = curl.getinfo(curl.HTTP_CODE)

            if 300 <= http_code < 400:
                redirect_url = curl.getinfo(curl.REDIRECT_URL)
            else:
                redirect_url = None

            result = self.generate_http_result(
                metadata,
                path,
                header_buffer,
                int(end - start),
                http_code,
                start,
                md5_buffer.hexdigest(),
                redirect=redirect_url
            )
        else:
            rejected = header_buffer.tell() == 0
            partial = success == -1 and not rejected

            result = self.generate_http_result(
                metadata,
                None,
                None,
                int(end - start),
                None,
                start,
                None,
                error=True,
                partial=partial,
                rejected=True
            )
            
        curl.close()
        content_buffer.close()
        header_buffer.close()
       
        return result

    def generate_http_result(
        self,
        metadata,
        path,
        header_buffer,
        elapsed_time,
        http_code,
        timestamp,
        content_md5,
        error=False,
        redirect=None,
        partial=False,
        rejected=None
    ):
        url = metadata.geturl()
        
        result = {
            'content_path': path,
            'origin': url,
            'http_code': http_code,
            'elapsed_time': elapsed_time,
            'timestamp': timestamp,
            'content_md5': content_md5
        }

        self.parse_header(header_buffer, result)

        if rejected is not None:
            result['rejected'] = rejected

        if partial:
            result['partial'] = partial

        if error:
            result['error'] = True

        if redirect:
            result['redirect'] = redirect

        return result

    def parse_header(self, header_buffer, result):
        header = header_buffer.getvalue() if header_buffer else None

        if header:
            result['header'] = str(base64.b64encode(header), encoding="utf-8")
            header_map = self.get_headers(header)
            result['server'] = header_map.get('server', None)

    def get_headers(self, header_content):
        socket = MockSocket(header_content)
        mock_response = http.client.HTTPResponse(socket)
        mock_response.begin()
        
        return mock_response.headers

    def perform_get(self, curl, scheme, retries):
        try:
            if scheme == 'http':
                self.get_http(curl)
            elif scheme == 'https':
                self.get_https(curl)

            return True
        except (KeyboardInterrupt, SystemExit):
            self.kill_process()
        except pycurl.error as e:
            if e.args[0] == curl.E_WRITE_ERROR:
                return -1
        except Exception as e:
            self.log.warning(e)

            return False

    def get_http(self, curl):
        curl.perform()

    def get_https(self, curl):
        try:
            curl.perform()
        except pycurl.error as e:
            if e.args[0] == curl.E_SSL_PEER_CERTIFICATE:
                curl.setopt(curl.SSL_VERIFYHOST, 0)
                curl.perform()
            else:
                raise e

    def on_message(self, message):
        url = message['url']
        message.update(self.get_url(url))
        
        return message

    def process_work(self, message):
        result = None

        try:
            result = self.on_message(message)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as e:
            self.log.exception(e)
        finally:
            self.export_fetcher_result(message, result)

        return True

    def export_fetcher_result(self, message, result):
        origin_content_path = message.get('content_path', None)
        content_exists = origin_content_path is not None
        content_name = None

        if content_exists:
            content_name = os.path.basename(origin_content_path)


        # TODO pass in dictionary
        if result is not None:
            name = self.generate_unique_name()

            for outbox in self.outboxes:
                inbox = outbox['inbox']
                content_folder = outbox['content']

                if content_exists:
                    destination = os.path.join(content_folder, content_name)
                    message['content_path'] = destination
                    os.link(origin_content_path, destination)

                inbox_destination = os.path.join(inbox, name)

                self.write_result(result, path=inbox_destination)

            if content_exists:
                os.remove(origin_content_path)
