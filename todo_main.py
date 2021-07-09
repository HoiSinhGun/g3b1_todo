#!/usr/bin/env python
# pylint: disable=C0116,W0613
# This program is dedicated to the public domain under the CC0 license.

"""This is a very simple example on how one could implement a custom error handler."""
import json
import logging
import string

from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters
from telegram.utils.helpers import escape_markdown

import subscribe_db
import tg_db
import tg_reply
import tgdata_main
import todo_db
import utilities
from log.g3b1_log import cfg_logger
from todo_model import TodoDC
from utilities import TgCommand

logger = cfg_logger(logging.getLogger(__name__), logging.DEBUG)

# The token you got from @botfather when you created the bot
BOT_TOKEN_TODO = "1811660536:AAECIUTG4--AXz8STwzd_iQjiCmjleHWF98"


def commands() -> dict:
    return dict(
        todo_create=
        TgCommand("create", "todo_create",
                  hdl_cmd_create, hdl_cmd_create.__doc__, ['title']),
        todo_assign=
        TgCommand("assign", "todo_assign",
                  hdl_cmd_assign, hdl_cmd_assign.__doc__, ['assignee_un']),
        todo_close=
        TgCommand("close", "todo_close",
                  hdl_cmd_close, hdl_cmd_close.__doc__, []),
        todo_filter=
        TgCommand("filter", "todo_filter",
                  hdl_cmd_filter, hdl_cmd_filter.__doc__, ['filter']),
        todo_list=
        TgCommand("list", "todo_list",
                  hdl_cmd_list, hdl_cmd_list.__doc__, []),
        todo_pick=
        TgCommand("pick", "todo_pick",
                  hdl_cmd_pick, hdl_cmd_pick.__doc__, ['number']),
        todo_idpick=
        TgCommand("idpick", "todo_idpick",
                  hdl_cmd_idpick, hdl_cmd_idpick.__doc__, ['rowid'])
    )


def start(update: Update, context: CallbackContext) -> None:
    """Displays info."""
    commands_str = utilities.build_commands_str(commands())
    update.effective_message.reply_html(
        commands_str +
        utilities.build_debug_str(update)
    )


def hdl_message(update: Update, context: CallbackContext) -> None:
    """store message to DB"""
    message = update.message
    logger.debug(f"Handle message {message}")
    tg_db.synchronize_from_message(message)


def hdl_cmd_create(update: Update, context: CallbackContext) -> None:
    """Create a new todo"""
    title = " ".join(context.args)
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    todo = TodoDC(title=title, tg_chat_id=chat_id,
                  creat__tg_user_id=user_id, assig__tg_user_id=user_id)
    todo = todo_db.todo_insert(todo)
    todo_db.default(chat_id, user_id, todo.rowid)
    tg_reply.command_successful(update)


def todo_default_r_err(update: Update) -> TodoDC:
    todo = todo_db.read_default(update.effective_chat.id, update.effective_user.id)
    if not todo:
        update.effective_message.reply_html(
            f'Current todo not set! Pick a todo first. Use /list and then /pick.'
        )
    return todo


def filter_default_r_err(update: Update) -> (str, str):
    filter_key = todo_db.read_filter_default(update.effective_chat.id, update.effective_user.id)
    if not filter_key:
        update.effective_message.reply_html(
            f'Current filter for todo not set! Set a filter first. '
            f'Use <code>/todo_filter me_assignee</code>.'
        )
    return filter_key, todo_db.filters()[filter_key]


def hdl_cmd_assign(update: Update, context: CallbackContext) -> None:
    """Assign an user to do it"""
    uname = context.args[0]
    assignee_user_id = subscribe_db.id_by_uname(uname)
    if not assignee_user_id:
        update.effective_message.reply_html(
            f'Assignee by uname={uname} not found!'
        )
        return
    todo: TodoDC = todo_default_r_err(update)
    if not todo:
        return
    todo.assig__tg_user_id = assignee_user_id
    todo_db.todo_update(todo)
    tg_reply.command_successful(update=update)


def hdl_cmd_close(update: Update, context: CallbackContext) -> None:
    """Close a todo"""
    todo: TodoDC = todo_default_r_err(update)
    if not todo:
        return
    if not todo.closed:
        # silently ignore
        todo.closed = 1
        todo.closed_on = utilities.now_for_sql()
    todo_db.todo_update(todo)
    tg_reply.command_successful(update=update)


def hdl_cmd_filter(update: Update, context: CallbackContext) -> None:
    """Set the default filter for the user and chat."""
    """Examples (always excludes closed ones): 
    me = tg_user_id, sender of the command
    me_assignee, me_creator, me_stake (creator or assignee or...), 
    all"""
    tg_user_id = update.effective_user.id
    todo_filter = context.args[0]
    filter_sql: str = todo_db.filters()[todo_filter]
    if not filter_sql:
        update.effective_message.reply_html(
            f'Filter {todo_filter} not found!'
        )
        return
    todo_db.set_filter_default(update.effective_chat.id, tg_user_id, todo_filter)
    tg_reply.command_successful(update)


def i_list_default(update: Update, context: CallbackContext):
    filter_key, filter_sql = filter_default_r_err(update)
    tg_user_id = update.effective_user.id
    tg_chat_id = update.effective_chat.id
    if not filter_key:
        return
    param_dict: dict = dict()
    if filter_sql.find(":tg_chat_id") > 0:
        param_dict.update(tg_chat_id=tg_chat_id)
    if filter_sql.find(":tg_user_id") > 0:
        param_dict.update(tg_user_id=tg_user_id)
    if filter_sql.find(":closed") > 0:
        param_dict.update(closed=0)

    return todo_db.todo_list(filter_sql, param_dict)


def hdl_cmd_list(update: Update, context: CallbackContext) -> None:
    """List todo by todo filter (/todo_filter me_assignee"""
    list_def = i_list_default(update, context)
    reply_str: str = ""
    count: int = 1
    data_as_dic: dict = {}
    for i in list_def:
        data_as_dic.update({count: i})
        reply_str += f'{count}' + " " + json.dumps(i) + "\n"
        count += 1

    tbl_def = utilities.TableDef(cols=['title', 'creat__uname', 'assig__uname'])
    tbl = utilities.dc_dic_to_table(data_as_dic, tbl_def)
    reply_str = utilities.table_print(tbl)
    if not reply_str:  # == reply_str.strip():
        tg_reply.no_data(update)
        return
    if len(reply_str) > 3753:
        reply_str = 'More than 3753 characters. Data will be cut!\n'
    reply_str = "<code>\n" + reply_str[:3753] + "\n</code>"
    update.effective_message.reply_html(reply_str)
#    update.effective_message.reply_markdown_v2(
#        escape_markdown(reply_str, 2)  # .replace('{', r'\{').replace('}', r'\{').replace('-', r'\-')
#    )


def hdl_cmd_pick(update: Update, context: CallbackContext) -> None:
    """Pick a todo by it's position in the list of user's default list filter"""
    list_default = i_list_default(update, context)
    li_idx = int(context.args[0]) - 1
    row: dict = list_default[li_idx]
    i_set_default(update.effective_chat.id, update.effective_user.id, int(row['rowid']))


def i_set_default(update: Update, todo_id: int, chat_id: int = None, user_id: int = None):
    if not chat_id:
        chat_id = update.effective_chat.id
    if not user_id:
        user_id = update.effective_user.id
    todo_dc = todo_db.default(chat_id, user_id, todo_id)
    update.effective_message.reply_html(
        f'Todo Default - {todo_id}: {todo_dc.title}'
    )


def hdl_cmd_idpick(update: Update, context: CallbackContext) -> None:
    """Pick a todo by its id """
    todo_dc = todo_db.by_rowid(int(context.args[0]))
    i_set_default(update.effective_chat.id, update.effective_user.id, todo_dc.rowid)


def main() -> None:
    """Run the bot."""
    tgdata_main.start_bot(BOT_TOKEN_TODO, commands(), start, hdl_message)


if __name__ == '__main__':
    main()