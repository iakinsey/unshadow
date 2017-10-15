from unshadow.db import DatabaseClass


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


class MetricClient(DatabaseClass):
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

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

        self.setup_database('metric')

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

            try:
                cursor.executemany(self.DECLARE_METRIC_SQL, creates)
            except psycopg2.IntegrityError:
                cursor.rollback()

            self.db.commit()

            cursor.execute(self.GET_STAGE_METRICS_SQL, (stage,))

            return {i[1]: i[0] for i in cursor.fetchall()}

    def send(self, values):
        """
        Add a specified value for a specified metric id.
        """

        with self.get_cursor() as cursor:
            cursor.executemany(self.ADD_DATA_SQL, values)
            self.db.commit()
