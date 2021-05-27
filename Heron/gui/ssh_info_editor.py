
import os
from pathlib import Path
import json
from dearpygui.core import *
from dearpygui.simple import *


class Table:
    def __init__(self, name: str, header: List[str] = None):
        self.name = name
        self.header = header
        self.row = 0
        self.column = 0
        self.num_of_rows = 0

        ssh_info_file = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent, 'communication',
                                     'ssh_info.json')
        with open(ssh_info_file) as f:
            self.ssh_info = json.load(f)

        if header is not None:
            self.add_header(self.header)

        self.populate_from_json()

    def add_header(self, header: List[str]):
        add_separator(parent=self.name)
        with managed_columns(f"{self.name}_head", len(header)):
            for item in header:
                add_text(item)

    def add_row(self, row_content: List[Any]):
        with managed_columns(f"{self.name}_{self.row}", len(row_content), parent=self.name):
            self.ssh_info[row_content[1]] = {}
            for i, item in enumerate(row_content):
                item_name = f"##{self.name}_{self.row}_{self.column}"
                if i > 1:
                    self.ssh_info[row_content[1]][self.header[i]] = item
                if type(item) is str:
                    add_input_text(item_name, default_value=item, width=-1, callback=self.on_edit)
                if type(item) is int:
                    add_input_int(item_name, default_value=item, width=-1, step=0, callback=self.on_edit)
                if type(item) is float:
                    add_input_float(item_name, default_value=item, width=-1, step=0, allback=self.on_edit)
                if type(item) is bool:
                    add_checkbox(item_name, default_value=False)
                if i == 1:
                    configure_item(item_name, enabled=False)
                self.column += 1
            self.num_of_rows += 1
        add_separator(name=f"##{self.name}_{self.row}_sep", parent=self.name)
        self.column = 0
        self.row += 1

    def delete_selected_rows(self):
        sel_rows = []
        for row in range(self.num_of_rows):
            if get_value(f"##{self.name}_{row}_{0}"):
                sel_rows.append(row)

        for row in sel_rows:
            id = get_value(f"##{self.name}_{row}_{1}")
            del self.ssh_info[id]

        for row in sel_rows:
            delete_item(f"##{self.name}_{row}_sep")
            for col in range(len(self.header)):
                delete_item(f"##{self.name}_{row}_{col}")

        self.save_to_json()

    def get_cell_data(self, row: int, col: int) -> Any:
        return get_value(f"##{self.name}_{row}_{col}")

    def get_row_data(self, row: int) -> dict:
        """
        Return a row as a dict with keys the names of the columns
        :param row: The row to be retrieved
        :return: A dict of the row data
        """
        result = {}
        for col, name in enumerate(self.header):
            result[name] = self.get_cell_data(row, col)

    def populate_from_json(self):
        for id in self.ssh_info:
            self.add_row([False, id, self.ssh_info[id]['Name'], self.ssh_info[id]['IP'], self.ssh_info[id]['Port'],
                                    self.ssh_info[id]['username'], self.ssh_info[id]['password']])

    def save_to_json(self):
        ssh_info_file = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))).parent, 'communication',
                                     'ssh_info.json')
        with open(ssh_info_file, 'w+') as f:
            json.dump(self.ssh_info, f, indent=4)

    def on_edit(self, item, data):
        row = int(item.split('_')[-2])
        col = int(item.split('_')[-1])

        id = get_value(f"##{self.name}_{row}_{1}")
        col_name = self.header[col]
        self.ssh_info[id][col_name] = get_value(f"##{self.name}_{row}_{col}")


def edit_ssh_info():
    global ssh_table

    with window('ssh info editor', width=800, height=500, on_close=on_close):
        add_button('Add ssh server', callback=add_ssh_server_row)
        add_same_line()
        add_button('Remove ssh server', callback=remove_ssh_server_rows)
        ssh_table = Table('ssh info editor', ['', 'ID', 'Name', 'IP', 'Port', 'username', 'password'])


def add_ssh_server_row():
    global ssh_table
    max_id = 0
    for id in ssh_table.ssh_info:
        if int(id) >= max_id:
            max_id = int(id) + 1
    ssh_table.add_row([False, max_id, 'Id name', 'IP', 22, 'user name', 'password'])
    ssh_table.save_to_json()


def remove_ssh_server_rows():
    global ssh_table
    ssh_table.delete_selected_rows()


def on_close():
    global ssh_table
    ssh_table.save_to_json()
    delete_item('ssh info editor')

