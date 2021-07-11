import test_utils
import todo_main
from utilities import get_module, print_header_line


def main():
    update, ctx = test_utils.setup(get_module())

    print_header_line('cmd filter %all%')
    ctx.args = ['all']
    todo_main.hdl_cmd_filter(update, ctx)

    print_header_line('cmd list')
    ctx.args = []
    todo_main.hdl_cmd_list(update, ctx)

    print_header_line('cmd default')
    ctx.args = []
    todo_main.hdl_cmd_default(update, ctx)

    print_header_line('cmd pick %1%')
    ctx.args = ['1']
    todo_main.hdl_cmd_pick(update, ctx)

    print_header_line('cmd default')
    ctx.args = []
    todo_main.hdl_cmd_default(update, ctx)

    print_header_line('cmd title new_title')
    ctx.args = ['new title']
    todo_main.hdl_cmd_title(update, ctx)

    print_header_line('cmd default')
    ctx.args = []
    todo_main.hdl_cmd_default(update, ctx)

    print_header_line('cmd assign')
    ctx.args = ['uname_2']
    todo_main.hdl_cmd_assign(update, ctx)


if __name__ == '__main__':
    main()
