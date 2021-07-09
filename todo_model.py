from dataclasses import dataclass, asdict

import utilities


@dataclass
class TodoDC:
    rowid: int = None
    title: str = None
    tg_chat_id: int = None
    creat__tg_user_id: int = None
    creat_on: str = utilities.now_for_sql()
    assig__tg_user_id: int = None
    closed: int = 0
    closed_on: str = None
    creat__uname: str = None
    assig__uname: str = None

    def as_dict_sql_mod(self) -> dict:
        new_dict = self.as_dict_ext()
        if 'rowid' in new_dict:
            new_dict.pop('rowid')
        return new_dict

    def as_dict_ext(self) -> dict:
        values = asdict(self)
        new_dict = dict()
        for item in values.keys():
            if values[item]:
                new_dict[item] = values[item]
        return new_dict


def main():
    todo = TodoDC(1, 'test')
    print(asdict(todo))
    todo = TodoDC(title='test',creat__tg_user_id=1)
    print(asdict(todo))
    print(todo.as_dict_sql_mod())


if __name__ == '__main__':
    main()
