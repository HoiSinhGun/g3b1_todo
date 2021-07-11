import logging
from dataclasses import asdict

from sqlalchemy import MetaData, create_engine, select, text
from sqlalchemy import Table
from sqlalchemy.dialects import sqlite
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.sql import Update, ColumnElement
from sqlalchemy.sql.elements import TextClause
from telegram import Message, Chat, User  # noqa

import subscribe_main
from log.g3b1_log import cfg_logger
# create console handler and set level to debug
from todo_model import TodoDC

BOT_BKEY_TODO = "TODO"
BOT_BKEY_TODO_LC = BOT_BKEY_TODO.lower()

DB_FILE_TODO = rf'C:\Users\IFLRGU\Documents\dev\g3b1_{BOT_BKEY_TODO_LC}.db'
MetaData_TODO = MetaData()
Engine_TODO = create_engine(f"sqlite:///{DB_FILE_TODO}")
MetaData_TODO.reflect(bind=Engine_TODO)

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)


def filters() -> dict:
    sql_default = ' closed=:closed AND tg_chat_id=:tg_chat_id '
    return dict(
        me_assignee=
        f" assig__tg_user_id=:tg_user_id AND {sql_default} ",
        me_creator=
        f"creat__tg_user_id=:tg_user_id AND {sql_default} ",
        me_stake=
        f" (assig__tg_user_id=:tg_user_id OR creat__tg_user_id=:tg_user_id) AND {sql_default} ",
        all=
        f"  {sql_default} "
    )


def table() -> Table:
    return MetaData_TODO.tables["todo"]


def by_rowid(rowid: int) -> TodoDC:
    with Engine_TODO.connect() as con:
        return i_fetch_todo(con, rowid)


def todo_insert(todo: TodoDC) -> TodoDC:
    with Engine_TODO.connect() as con:
        values = todo.as_dict_sql_mod()
        insert_stmt = table().insert().values(values)
        logger.debug(insert_stmt)
        con.execute(insert_stmt)
        rs = con.execute("SELECT last_insert_rowid()")
        rowid: int = rs.fetchone()[0]
        return i_fetch_todo(con, rowid)


def todo_list(filter_sql: str, param_dict: dict) -> dict:
    rs_dict = dict()
    where_str: str = f"WHERE {filter_sql} "
    stmt: TextClause = text("SELECT todo.ROWID, todo.* FROM todo " + where_str)
    #  print(f'param_dict: {param_dict} ')
    stmt = stmt.bindparams(**param_dict)
    with Engine_TODO.connect() as con:
        rs = con.execute(stmt)
        # print(rs)
        count: int = 0
        for row in rs:
            count += 1
            d = dict(row)
            rs_dict.update({count: d})
            #  print(f'added to lod: {d}')
    rs_dict = subscribe_main.map_id_uname(rs_dict, {'creat__tg_user_id': 'creat__uname',
                                            'assig__tg_user_id': 'assig__uname'})
    return rs_dict


def i_fetch_todo(con: MockConnection, rowid: int) -> TodoDC:
    rs = con.execute("SELECT ROWID, * FROM todo WHERE ROWID=:rowid", rowid=rowid)
    todo_dict = dict(rs.mappings().all()[0])
    if not todo_dict:
        return
    todo_upd = TodoDC(**todo_dict)
    return todo_upd


def todo_update(todo: TodoDC) -> TodoDC:
    with Engine_TODO.connect() as con:
        values = todo.as_dict_sql_mod()

        stmt: Update = table().update().values(values)
        stmt_str: str = stmt.compile(
            dialect=sqlite.dialect(), compile_kwargs={"literal_binds": True}
        ).string
        stmt_str = stmt_str + r' WHERE ROWID=:rowid'
        # print(stmt_str)
        logger.debug(stmt_str)
        con.execute(stmt_str, rowid=todo.rowid)  # update

        return i_fetch_todo(con, todo.rowid)


def read_filter_default(tg_chat_id: int, tg_user_id: int) -> str:
    with Engine_TODO.connect() as con:
        result_one = i_read_default_value(
            con, tg_chat_id, tg_user_id,
            MetaData_TODO.tables["user_chat_settings"].c.filter)

        if not result_one:
            return
        filter_key: str = result_one[0]
        return filter_key


def set_filter_default(tg_chat_id: int, tg_user_id: int, filter_key: str) -> str:
    with Engine_TODO.connect() as con:
        i_set_default_value(con, tg_chat_id, tg_user_id, 'filter', filter_key)


def i_read_default_value(con: MockConnection,
                         tg_chat_id: int,
                         tg_user_id: int,
                         column: ColumnElement):
    tbl_settings: Table = MetaData_TODO.tables["user_chat_settings"]
    select_stmt = select(column)
    # logger.debug(select_stmt)
    select_stmt = select_stmt. \
        where(tbl_settings.c.tg_chat_id == tg_chat_id, tbl_settings.c.tg_user_id == tg_user_id)
    # logger.debug(f'SELECT: {select_stmt}')
    logger.debug(f'Reading default for user-chat {column.key}')
    result = con.execute(select_stmt)
    return result.fetchone()


def i_set_default_value(con: MockConnection,
                        tg_chat_id: int,
                        tg_user_id: int,
                        column_name: str,
                        new_value):
    tbl_settings: Table = MetaData_TODO.tables["user_chat_settings"]
    values = dict(
        tg_user_id=tg_user_id, tg_chat_id=tg_chat_id
    )
    values[column_name] = new_value
    insert_stmnt: insert = insert(tbl_settings).values(values).on_conflict_do_update(
        index_elements=['tg_user_id', 'tg_chat_id'],
        set_=values
    )
    logger.debug(f"Insert statement: {insert_stmnt}")
    con.execute(insert_stmnt)


def read_default(tg_chat_id: int, tg_user_id: int) -> TodoDC:
    with Engine_TODO.connect() as con:
        result_one = i_read_default_value(
            con, tg_chat_id, tg_user_id,
            MetaData_TODO.tables["user_chat_settings"].c.todo_id)
        if not result_one:
            return
        todo_id: int = result_one[0]
        return i_fetch_todo(con, todo_id)


def default(tg_chat_id: int, tg_user_id: int, todo_id: int) -> TodoDC:
    with Engine_TODO.connect() as con:
        i_set_default_value(con, tg_chat_id, tg_user_id, 'todo_id', todo_id)
        return i_fetch_todo(con, todo_id)


def main():
    todo_dc = todo_insert(TodoDC(title="test", tg_chat_id=1, creat__tg_user_id=1, assig__tg_user_id=2))
    print(f"todo_dc: {todo_dc}")
    todo_dict = asdict(todo_dc)
    print(f"todo_dict: {todo_dict}")
    todo_dc = by_rowid(todo_dict['rowid'])
    print(f"new todo dc: {todo_dc}")
    todo_dc.assig__tg_user_id = 1
    todo_dc = todo_update(todo_dc)
    print(f"new todo dc with modified assig tg user: {todo_dc}")
    default_todo = read_default(1, 1)
    print("todo default: ", default_todo)
    print(f"set todo {todo_dc.rowid} as default")
    default(
        1, 1, todo_dc.rowid
    )
    default_todo = read_default(1, 1)
    print("todo default: ", default_todo)
    print("filter me_assignee for id=2")
    filter_sql = filters()['me_assignee']
    param_dict = dict(
        tg_chat_id=1, tg_user_id=1, closed=0)
    todo_list(filter_sql, param_dict)
    set_filter_default(1, 2, "all")
    filter_default = read_filter_default(1, 2)
    todo_list(filters()[filter_default], dict(tg_chat_id=1, closed=0))


if __name__ == '__main__':
    main()
