from wheezy.http import HTTPResponse
from wheezy.http import WSGIApplication
from wheezy.routing import url
from wheezy.web.handlers import BaseHandler
from wheezy.web.middleware import bootstrap_defaults
from wheezy.web.middleware import path_routing_middleware_factory
from wsgiref.simple_server import make_server
from time import mktime
from unshadow.encode import RPCEncoder
from unshadow.db import DatabaseClass


import logging
import psycopg2



class AccessDenied(Exception):
    """
    Access unauthorized.
    """

    pass


class InvalidRequest(Exception):
    """
    Request is invalid
    """

    pass


class DoesntExist(Exception):
    """
    Method does not exist.
    """

    pass


# TODO use middleware instead.
GLOBALS = {}


def exposed(fn):
    fn.__exposed = True

    return fn


class GeneralizedHandler(BaseHandler):
    encoder = RPCEncoder()

    # TODO use middleware instead.
    @property
    def db(self):
        return GLOBALS["db"]

    def post(self):
        """
        Handle HTTP POST.
        """

        method = self.get_method()
        body = self.get_body()

        # TODO handle method exception.
        result = method(**body)
        payload = self.encoder.encode(result)

        response = HTTPResponse(content_type="application/json")
        response.status_code = 200
        response.write(payload)

        return response

    def get_method(self):
        method_name = self.request.path.split('/')[3]

        method = getattr(self, method_name, None)

        if not method or not getattr(method, "__exposed", None) == True:
            raise DoesntExist("Method does not exist.")

        return method

    def get_body(self):
        try:
            body, files = self.request.load_body()
        except ValueError:
            return {}
        else:
            return body

    def get_cursor(self):
        return self.db.cursor()


class MetricHandler(GeneralizedHandler):
    DECLARE_METRIC_SQL = """
        INSERT INTO metric (stage, metric) VALUES (%s, %s)
    """

    ADD_DATA_SQL = """
        INSERT INTO metric_data (metric_id, timestamp, value) VALUES (%s, %s, %s)
    """

    GET_DATA_SQL = """
        SELECT timestamp, value FROM metric_data
        WHERE
            metric_id = %s AND
            timestamp <= %s AND
            timestamp >= %s
        ORDER BY timestamp ASC
    """

    LIST_METRIC_SQL = """
        SELECT id, stage, metric FROM metric
    """

    GET_STAGE_METRICS_SQL = """
        SELECT id, metric FROM metric
        WHERE stage = %s
    """

    @exposed
    def declare(self, stage, metrics):
        """
        Get/Create metrics
        """

        metrics = set(metrics)
        persist_metrics = set()

        with self.get_cursor() as cursor:
            cursor.execute(self.GET_STAGE_METRICS_SQL, (stage,))

            for id, metric in cursor.fetchall():
                persist_metrics.add(metric)

            creates = [(stage, m) for m in metrics.difference(persist_metrics)]

            cursor.executemany(self.DECLARE_METRIC_SQL, creates)
            self.db.commit()

            cursor.execute(self.GET_STAGE_METRICS_SQL, (stage,))

            return {i[1]: i[0] for i in cursor.fetchall()}

    @exposed
    def add_data(self, values):
        """
        Add a specified value for a specified metric id.
        """

        with self.get_cursor() as cursor:
            cursor.executemany(self.ADD_DATA_SQL, values)
            self.db.commit()

    @exposed
    def get_data(self, metric_id, start, end):
        """
        Get the metric timeseries between start and end for the specified
        metric id.
        """

        with self.get_cursor() as cursor:
            cursor.execute(self.GET_DATA_SQL, (metric_id, start, end))

            result = cursor.fetchall()

        return [(mktime(i[0].timetuple()) * 1000, i[1]) for i in result]

    @exposed
    def list_metrics(self):
        """
        List all metrics.
        """

        with self.get_cursor() as cursor:
            cursor.execute(self.LIST_METRIC_SQL)

            result = cursor.fetchall()

        return [{
            "id": i[0],
            "stage": i[1],
            "metric": i[2]
        } for i in result]

    @exposed
    def get_stage_metric(self, stage):
        """
        Get metrics for a specific stage.
        """

        with self.get_cursor() as cursor:
            cursor.execute(self.GET_STAGE_METRICS_SQL, (stage,))

            return cursor.fetchall()


class MetricServer(DatabaseClass):
    SCHEMA = """
        CREATE TABLE metric (
            id SERIAL NOT NULL PRIMARY KEY,
            stage CHARACTER VARYING NOT NULL,
            metric CHARACTER VARYING NOT NULL,
            UNIQUE (stage, metric)
        );

        CREATE TABLE metric_data (
            metric_id INT NOT NULL,
            timestamp timestamp with time zone NOT NULL,
            value INT NOT NULL,
            CONSTRAINT metric_fk FOREIGN KEY (metric_id)
                REFERENCES metric (id) MATCH SIMPLE
        );

        CREATE INDEX metric_id_idx ON metric_data (metric_id);
        CREATE INDEX timestamp_idx ON metric_data (timestamp ASC);
    """

    URLS = [
        url("unshadow/metric/{any}", MetricHandler, name="Metrics")
    ]

    _db = None

    def __init__(
        self,
        http_host,
        http_port,
        db_host,
        db_port,
        db_user,
        db_name,
        db_pass
    ):
        self.http_host = http_host
        self.http_port = http_port
        self.db_host = db_host
        self.db_port = db_port
        self.db_user = db_user
        self.db_name = db_name
        self.db_pass = db_pass

    def start(self):
        """
        Start service.
        """

        self.setup_database('metric')

        # TODO use middleware instead.
        GLOBALS["db"] = self._db

        self.start_http_server()

    def setup_http_server(self):
        """
        Configure and start the http server.
        """

        self.start_http_server()

    def start_http_server(self):
        """
        Start the HTTP server.
        """

        self.wsgi_app = WSGIApplication(
            middleware=[
                bootstrap_defaults(url_mapping=self.URLS),
                path_routing_middleware_factory
            ],
            options={}
        )

        socket_pair = (self.http_host, self.http_port)
        self.wsgi_server = make_server(self.http_host, self.http_port, self.wsgi_app)
        message = "HTTP Server running on http://{}:{}"

        logging.info(message.format(self.http_host, self.http_port))

        self.wsgi_server.serve_forever()
