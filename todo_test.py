from telegram.ext import Dispatcher

import test_utils
import todo_main
import utilities


def main():
    dispatcher: Dispatcher = test_utils.setup(todo_main.__file__)

    ts: test_utils.TestSuite = test_utils.TestSuite(
        todo_main.__file__, dispatcher, []
    )

    ts.tc_li.extend(
        [
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                todo_main.hdl_cmd_filter),
                {'todo_filter': 'all'}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                todo_main.hdl_cmd_list),
                {}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                todo_main.hdl_cmd_default),
                {}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                todo_main.hdl_cmd_pick),
                {'li_pos': '1'}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                todo_main.hdl_cmd_title),
                {'title': utilities.now_for_sql()}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                todo_main.hdl_cmd_default),
                {}
            ),
            test_utils.TestCaseHdl(utilities.g3_cmd_by_func(
                todo_main.hdl_cmd_assign),
                {'uname': 'uname_2'}
            )
        ]
    )

    for tc in ts.tc_li:
        ts.tc_exec(tc)


if __name__ == '__main__':
    main()
