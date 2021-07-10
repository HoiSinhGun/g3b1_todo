import test_utils
import todo_main
from todo_main import BOT_TOKEN_TODO


def main():
    update, ctx = test_utils.setup(BOT_TOKEN_TODO)

    ctx.args = ['all']
    todo_main.hdl_cmd_filter(update, ctx)

    ctx.args = []
    todo_main.hdl_cmd_list(update, ctx)

    ctx.args = []
    todo_main.hdl_cmd_default(update, ctx)

    ctx.args = ['1']
    todo_main.hdl_cmd_pick(update, ctx)

    ctx.args = []
    todo_main.hdl_cmd_default(update, ctx)

    ctx.args = ['new title']
    todo_main.hdl_cmd_title(update, ctx)

    ctx.args = []
    todo_main.hdl_cmd_default(update, ctx)

    ctx.args = ['uname_2']
    todo_main.hdl_cmd_assign(update, ctx)


if __name__ == '__main__':
    main()
