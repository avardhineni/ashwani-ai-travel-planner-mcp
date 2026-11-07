"""Verify local PostgreSQL connectivity without showing passwords."""
import psycopg
from config import require_database_url


def main():
    with psycopg.connect(require_database_url(), connect_timeout=10) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT current_database()')
            database = cursor.fetchone()[0]
    print('Connected to PostgreSQL database:', database)


if __name__ == '__main__':
    main()
