import mysql.connector
from mysql.connector import errorcode


class Database:
    def __init__(self, db_secrets):
        self.sql_stmt = ''
        self.clause = ''
        self.order = ''
        self.left_join = ''
        self.db_config = {
            'user': db_secrets['db_username'],
            'password': db_secrets['db_password'],
            'host': db_secrets['db_host'],
            'port': db_secrets['db_port'],
            'database': db_secrets['db_name'],
            'raise_on_warnings': True,
            'consume_results': True
        }
        self.cmd = ''
        try:
            self.db_connect = mysql.connector.connect(**self.db_config)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
            exit(1)
        self.db_cursor = self.db_connect.cursor(dictionary=True, buffered=True)

    def select(self, tbl_name: str, column_list: list[str] | None):
        if column_list is None:
            columns = '*'
        else:
            columns = ', '.join(column_list)
        self.sql_stmt = f'SELECT {columns} FROM {tbl_name}'
        self.cmd = 'select'

    def insert(self, tbl_name: str, data_set: dict) -> None:
        name_list = '('
        val_list = '('
        for k, v in data_set.items():
            if v is not None:
                name_list += k + ', '
                if isinstance(v, str):
                    val_list += '"' + v + '", '
                elif isinstance(v, int):
                    val_list += str(v) + ', '
                elif isinstance(v, float):
                    val_list += str(v) + ', '
        name_list = name_list[:-2] + ')'
        val_list = val_list[:-2] + ')'
        self.sql_stmt = f'INSERT INTO {tbl_name} {name_list} VALUES {val_list}'
        self.cmd = 'insert'

    def update(self, tbl_name: str, data_set: dict) -> None:
        set_list = ''
        for k, v in data_set.items():
            if v is not None:
                if isinstance(v, str):
                    if v[0] == '@':
                        set_list += f'{k} = {v[1:]}, '
                    else:
                        set_list += f'{k} = "{v}", '
                elif isinstance(v, int):
                    set_list += f'{k} = {v}, '
                elif isinstance(v, float):
                    set_list += f'{k} = {v}, '
        set_list = set_list[:-2]
        self.sql_stmt = f'UPDATE {tbl_name} SET {set_list}'
        self.cmd = 'update'

    def delete(self, tbl_name: str) -> None:
        self.sql_stmt = f'DELETE FROM {tbl_name}'
        self.cmd = 'delete'

    def close(self) -> None:
        self.db_cursor.close()
        self.db_connect.close()

    def where(self, clause: str) -> None:
        self.clause = clause

    def order_by(self, order: str) -> None:
        self.order = order

    def join_left(self, tbl_name: str, on: str) -> None:
        self.left_join = f'LEFT JOIN {tbl_name} ON ({on})'

    def run(self):
        if self.cmd == 'insert':
            self.clause = ''
            self.left_join = ''
            self.order = ''
        if self.cmd == 'update' or self.cmd == 'delete':
            self.left_join = ''
            self.order = ''
        ex_cmd = f'{self.sql_stmt}'
        if len(self.left_join) > 0:
            ex_cmd += f' {self.left_join}'
        if len(self.clause) > 0:
            ex_cmd += f' WHERE {self.clause}'
        if len(self.order) > 0:
            ex_cmd += f' ORDER BY {self.order}'
        try:
            self.db_cursor.execute(ex_cmd)
            self.db_connect.commit()
        except mysql.connector.Error as err:
            print(ex_cmd)
            raise err
        self.clause = ''
        self.left_join = ''
        self.order = ''
        if self.cmd == 'select':
            rows = self.db_cursor.fetchall()
            return rows
        elif self.cmd == 'insert':
            return self.db_cursor.lastrowid
        elif self.cmd == 'update':
            return True
        elif self.cmd == 'delete':
            return True
        else:
            return False

    def fetch(self):
        ex_cmd = f'{self.sql_stmt}'
        if len(self.left_join) > 0:
            ex_cmd += f' {self.left_join}'
        if len(self.clause) > 0:
            ex_cmd += f' WHERE {self.clause}'
        if len(self.order) > 0:
            ex_cmd += f' ORDER BY {self.order}'
        try:
            self.db_cursor.execute(ex_cmd)
            self.db_connect.commit()
        except mysql.connector.Error as err:
            print(ex_cmd)
            raise err
        else:
            self.clause = ''
            self.left_join = ''
            self.order = ''
            row = self.db_cursor.fetchone()
            return_row = row
            while row is not None:
                row = self.db_cursor.fetchone()
            return return_row

    def last_id(self):
        return self.db_cursor.lastrowid
