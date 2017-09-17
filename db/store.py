"""
Handles the creation of tables and storage into tables.
"""

from typing import List
import db.retrieve
import db.utils
import db.config as DB_CONFIG

def store_nba_response(data_name: str, nba_response, primary_keys=(), ignore_keys=set()):
    store_nba_responses(data_name, [nba_response], primary_keys, ignore_keys)

def store_nba_responses(data_name: str, l_nba_response: List, primary_keys=(), ignore_keys=set()):
    """
    Stores a given list of nba responses, creating a table
    if necessary with the given data_name.
    """
    if len(l_nba_response) == 0:
        raise ValueError('List of nba responses was empty.')

    def filter_columns(nba_response, desired_column_headers):
        """
        Removes all columns specified in ignore_keys
        and returns the processed list of rows.
        """
        try:
            desired_column_indicies = [headers.index(header) for header in desired_column_headers]
        except:
            raise ValueError('nba response headers are inconsistent: {} \n\n {}'.format(
                nba_response.headers,
                headers
            ))

        rows = nba_response.rows
        processed_rows = []
        for row in rows:
            processed_rows.append([row[i] for i in desired_column_indicies])
        return processed_rows

    # process the rows to only contain the desired columns
    headers = l_nba_response[0].headers
    desired_column_headers = [header for header in headers if header not in ignore_keys]

    processed_rows = []
    for nba_response in l_nba_response:
        processed_rows.extend(filter_columns(nba_response, desired_column_headers))


    if db.retrieve.exists_table(data_name):
        add_to_table(data_name, desired_column_headers, processed_rows)
    else:
        create_table_with_data(data_name, desired_column_headers, processed_rows, primary_keys)

def create_table_with_data(table_name: str, headers: List[str], rows: List[List], primary_keys=()):
    """
    Creates a table with column names and rows corresponding
    to the provided json responses.
    """
    if len(headers) != len(rows[0]):
        raise ValueError('Length of the headers and rows are not the same.')

    def get_column_types(rows: List[List]):
        """
        Returns a list of sqlite3 types defined by the
        data in the json response rows.
        """
        TYPE_MAPPING = {
            str: 'TEXT',
            int: 'INT',
            float: 'FLOAT',
            bool: 'INT'
        }
        return [TYPE_MAPPING[type(ele)] for ele in rows[0]]

    def format_column_strs():
        """
        Returns the string representing the declaration of columns
         in a sqlite3 table declaration which includes.
        - column name
        - column type (sqlite3)
        - primary key

        Ex. 'PLAYER_ID INT, PLAYER_NAME TEXT, PRIMARY KEY (PLAYER_ID, PLAYER_NAME)'
        """
        column_types = get_column_types(rows)
        column_strs = []
        for i in range(len(headers)):
            column_str = '{} {}'.format(headers[i], column_types[i])
            column_strs.append(column_str)
        column_def_str = ', '.join(column_strs)
        if len(primary_keys) != 0:
            column_def_str += ', PRIMARY KEY ({})'.format(', '.join(primary_keys))
        return column_def_str

    column_sql_str = format_column_strs()
    db.utils.execute_sql("""CREATE TABLE IF NOT EXISTS {} ({});""".format(table_name, column_sql_str))

    add_to_table(table_name, headers, rows)


def add_to_table(table_name: str, headers: List[str], rows: List[List]):
    """
    Adds the rows to the table.
    """
    insert_values_sql_str = '({})'.format(', '.join(['?'] * len(headers)))
    if DB_CONFIG.IGNORE_DUPLICATES:
        sql_statement = """INSERT OR IGNORE INTO {} VALUES {};"""
    else:
        sql_statement = """INSERT INTO {} VALUES {};"""

    db.utils.execute_many_sql(sql_statement.format(table_name, insert_values_sql_str), rows)