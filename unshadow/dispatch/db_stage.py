import os
import psycopg2


from unshadow.dispatch.worker import Stage


class DBStage(Stage):
    _conn = None
    tables = {}

    @property
    def db_connection(self):
        if not self._db:
            self._db = psycopg2.connect(**{
                "database": self.db_name,
                "user": self.db_user,
                "password": self.db_pass,
                "host": self.db_host,
                "port": self.db_port
            })

            # TODO use middleware instead.
            GLOBALS["db"] = self._db

        return self._db

    def get_cursor(self):
        return self.db_connection.cursor()
