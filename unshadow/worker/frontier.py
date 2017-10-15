from urllib.parse import urlparse
from time import time

from unshadow.dispatch import Stage
from unshadow.db import DatabaseClass


class Frontier(Stage, DatabaseClass):
    '''
    Extracts links from urls.
    '''

    ignore_outbox = True
    check_delay = 10
    domain_delay = 60

    SCHEMA = """
        CREATE TABLE domain (
            id SERIAL NOT NULL PRIMARY KEY,
            location VARCHAR NOT NULL,
            found INTEGER NOT NULL,
            accessible BOOLEAN,
            last_emit INTEGER,
            last_seen INTEGER
        );

        CREATE TABLE url (
            domain_id INTEGER NOT NULL,
            url VARCHAR NOT NULL,
            last_visited INTEGER,
            last_emit INTEGER,
            description VARCHAR,
            title VARCHAR,
            http_code INTEGER,
            partial BOOLEAN,
            rejected BOOLEAN,
            http_server VARCHAR,
            CONSTRAINT domain_id_fk FOREIGN KEY (domain_id)
                REFERENCES domain (id) MATCH SIMPLE
        );

        CREATE TABLE graph (
            src VARCHAR NOT NULL,
            dst VARCHAR NOT NULL
        );

        CREATE INDEX domain_id_idx ON domain (id);
        CREATE INDEX url_last_emit_idx ON url (last_emit);
        CREATE INDEX domain_location_trgm_idx ON domain
            USING gin (location gin_trgm_ops);

        CREATE INDEX url_url_trgm_idx ON url
            USING gin (url gin_trgm_ops);

    """

    def init(
        self,
        db_name=None,
        db_user=None,
        db_pass=None,
        db_host=None,
        db_port=None
    ):
        self.db_name = db_name
        self.db_user = db_user
        self.db_pass = db_pass
        self.db_host = db_host
        self.db_port = db_port

        self.setup_database('domain')

    def on_message(self, message):
        urls = message.get('urls', [])
        title = message.get('title', None)
        error = message.get('error', None)
        server = message.get('server', None)
        redirect = message.get('redirect', None)
        rejected = message.get('rejected', None)
        partial = message.get('partial', None)
        http_code = message.get('http_code', None)
        has_header = message.get('header', None) is not None
        description = message.get('description', None)
        origin = message['origin']
        origin_location = urlparse(origin).netloc

        # Update origin
        self.update_origin(
            origin,
            origin_location,
            title,
            description,
            has_header,
            http_code,
            error,
            server,
            rejected,
            partial
        )

        for url in urls:
            location = urlparse(url).netloc

            if location.endswith(".onion"):
                # Update Domain
                domain_id = self.set_or_update_domain(location)

                # Update URL
                self.set_or_update_url(url, domain_id)

                # Update graph
                self.update_graph(origin_location, location)

    def update_origin(
        self,
        origin,
        location,
        title,
        description,
        has_header,
        http_code,
        error,
        server,
        rejected,
        partial
    ):
        accessible = has_header and not error
        # Set or update domain
        domain_id = self.set_or_update_domain(location, accessible=accessible)

        # Set or update url
        self.set_or_update_url(
            origin,
            domain_id,
            visited=True,
            title=title,
            description=description,
            http_code=http_code,
            server=server,
            rejected=rejected,
            partial=partial
        )

    GET_DOMAIN_QUERY = """
        SELECT id FROM domain WHERE location = %s
    """

    UPDATE_DOMAIN_QUERY = """
        UPDATE domain SET last_seen = %s WHERE id = %s
    """

    UPDATE_DOMAIN_WITH_ACCESSIBLE_QUERY = """
        UPDATE domain SET last_seen = %s, accessible = %s WHERE id = %s
    """

    CREATE_DOMAIN_QUERY = """
        INSERT INTO domain (location, found, last_seen, accessible)
        VALUES (%s, %s, %s, %s)
    """

    def set_or_update_domain(self, location, accessible=None):
        with self.get_cursor() as cursor:
            cursor.execute(self.GET_DOMAIN_QUERY, (location,))

            result = cursor.fetchall()

            if result:
                _id = result[0][0]

                if accessible is not None:
                    update_query = self.UPDATE_DOMAIN_WITH_ACCESSIBLE_QUERY
                    update_args = (int(time()), accessible, _id)
                else:
                    update_query = self.UPDATE_DOMAIN_QUERY
                    update_args = (int(time()), _id)

                cursor.execute(update_query, update_args)
                self.db.commit()
            else:
                now = int(time())
                params = (location, now, now, accessible)
                cursor.execute(self.CREATE_DOMAIN_QUERY, params)
                self.db.commit()

                cursor.execute(self.GET_DOMAIN_QUERY, (location,))
                result = cursor.fetchall()
                _id = result[0][0]

        return _id

    GET_URL_QUERY = """
        SELECT 1 FROM url WHERE url = %s
    """

    UPDATE_URL_QUERY = """
        UPDATE url SET
        last_visited = %s,
        http_code = %s,
        http_server = %s,
        rejected = %s,
        partial = %s
        WHERE url = %s
    """

    CREATE_URL_QUERY = """
        INSERT INTO url (domain_id, url, title, description, http_code, http_server, rejected, partial)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    def set_or_update_url(
        self,
        url,
        domain_id,
        visited=False,
        title=None,
        description=None,
        http_code=None,
        server=None,
        rejected=None,
        partial=None
    ):
        with self.get_cursor() as cursor:
            cursor.execute(self.GET_URL_QUERY, (url,))

            result = cursor.fetchall()
            now = int(time())

            if not result:
                create_args = (domain_id, url, title, description, http_code, server, rejected, partial)
                cursor.execute(self.CREATE_URL_QUERY, create_args)
                self.db.commit()

            if visited:
                # TODO, this does not display history
                update_args = (now, http_code, server, rejected, partial, url)
                cursor.execute(self.UPDATE_URL_QUERY, update_args)

                self.db.commit()

    UPDATE_GRAPH_QUERY = """
        INSERT INTO graph (src, dst) VALUES (%s, %s)
    """

    def update_graph(self, src, dst):
        with self.get_cursor() as cursor:
            cursor.execute(self.UPDATE_GRAPH_QUERY, (src, dst))

    GET_NEXT_DOMAINS_QUERY = """
        SELECT
            DISTINCT ON (domain.id)
            domain.id,
            url.url
        FROM domain
        JOIN url ON url.domain_id = domain.id
        WHERE
            (domain.last_emit < %s  OR domain.last_emit IS NULL) AND
            (domain.accessible IS NULL OR domain.accessible = TRUE) AND
            url.last_emit IS NULL
        LIMIT %s
    """

    def on_check(self):
        with self.get_cursor() as cursor:
            now = int(time())
            delay_threshold = now - self.domain_delay
            params = (delay_threshold, self.outbox_space)

            cursor.execute(self.GET_NEXT_DOMAINS_QUERY, params)
            domains = cursor.fetchall()

            if domains:
                self.emit_domains(cursor, now, domains)

    URL_EMIT_QUERY = """
        UPDATE url SET last_emit = %s
        WHERE url = %s
    """

    DOMAIN_EMIT_QUERY = """
        UPDATE domain SET last_emit = %s
        WHERE id = %s
    """

    def emit_domains(self, cursor, now, domains):
        # TODO mogrify instead of doing executemany
        # Set last emit for urls.
        url_emit_params = [(now, i[1]) for i in domains]
        domain_emit_params = [(now, i[0]) for i in domains]

        cursor.executemany(self.URL_EMIT_QUERY, url_emit_params)
        cursor.executemany(self.DOMAIN_EMIT_QUERY, domain_emit_params)

        self.db.commit()
        # Push a set number of them out, depending on the outbox size.

        for domain_id, url in domains:
            self.write_result({
                "url": url
            }, prefix="0-")
