import contextlib
import psycopg2


class DatabaseClass(object):
    _db = None

    def setup_database(self, table_name):
        """
        Connect to the database and declare the schema if it doesn't already
        exist.
        """

        sql = """
            SELECT EXISTS (
                SELECT *
                FROM information_schema.tables
                WHERE
                    table_catalog = %s AND
                    table_name = %s
            )
        """

        with self.get_cursor() as cursor:
            cursor.execute(sql, (self.db_name, table_name))

            result = cursor.fetchall()
            exists = result[0][0]

            if not exists:
                try:
                    cursor.execute(self.SCHEMA)
                    self.db_connection.commit()
                except psycopg2.IntegrityError:
                    pass

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

        return self._db

    @property
    def db(self):
        return self.db_connection

    @contextlib.contextmanager
    def get_cursor(self):
        cursor = self.db_connection.cursor()

        try:
            yield cursor
        except:
            self.db_connection.rollback()
            raise
        finally:
            cursor.close()
