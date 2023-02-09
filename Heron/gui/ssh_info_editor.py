
import os
from pathlib import Path
import json
import dearpygui.dearpygui as dpg
from Heron import general_utils as gu


class Table:
    def __init__(self, name: str, header: list[str] = None, parent_id: int = 0):
        self.name = name
        self.header = header
        self.parent_id = parent_id
        self.row = 0
        self.column = 0
        self.num_of_rows = 0
        self.id = None
        self.column_ids = []
        self.rows_ids = {}

        self.ssh_info = gu.get_ssh_info_file()

        if header is not None:
            self.add_header(self.header)

        self.populate_from_json()

    def add_header(self, header: list[str]):
        dpg.add_separator(parent=self.parent_id)
        with dpg.table(header_row=True) as self.id:
            for item in header:
                self.column_ids.append(dpg.add_table_column(label=item))

    def add_row(self, row_content: list[any]):
        self.ssh_info[row_content[1]] = {}
        with dpg.table_row(parent=self.id):
            for i, item in enumerate(row_content):
                item_name = f"##{self.name}_{self.row}_{self.column}"

                if i > 1:
                    self.ssh_info[row_content[1]][self.header[i]] = item
                if type(item) is str:
                    self.rows_ids[item_name] = dpg.add_input_text(label=item_name, default_value=item,
                                                                  width=-1, callback=self.on_edit)
                if type(item) is int:
                    self.rows_ids[item_name] = dpg.add_input_int(label=item_name, default_value=item, width=-1, step=0,
                                                                 callback=self.on_edit)
                if type(item) is float:
                    self.rows_ids[item_name] = dpg.add_input_float(label=item_name, default_value=item, width=-1, step=0,
                                                                   callback=self.on_edit)
                if type(item) is bool:
                    self.rows_ids[item_name] = dpg.add_checkbox(label=item_name, default_value=False)
                if i == 1:
                    dpg.configure_item(self.rows_ids[item_name], enabled=False)
                if i == 6:
                    with dpg.tooltip(self.rows_ids[item_name]):
                        dpg.add_text("If the password is 'None' for the local machine\'s IP then the \n"
                                     'local machine does not need to run an SSH server and the \n'
                                     'communication between computers happens through normal sockets. \n'
                                     'If there is a password other than "None" then Heron assumes an \n'
                                     'SSH server is running on the local machine and all data and \n'
                                     'parameters are passed through SSH tunnels.\nWARNING! '
                                     'The SSH tunneling is slow and results in constant dropping of\n'
                                     'data packets!')
                self.column += 1

            with dpg.table_row(parent=self.id):
                sep_name = f"##{self.name}_{self.row}_sep"
                self.rows_ids[sep_name] = dpg.add_separator(label=sep_name)

        self.num_of_rows += 1
        self.row += 1
        self.column = 0

    def delete_selected_rows(self):
        sel_rows = []

        for row in range(self.num_of_rows):
            if dpg.get_value(self.rows_ids[f"##{self.name}_{row}_{0}"]):
                sel_rows.append(row)

        for row in sel_rows:
            id = dpg.get_value(self.rows_ids[f"##{self.name}_{row}_{1}"])
            del self.ssh_info[id]

        for row in sel_rows:
            dpg.delete_item(self.rows_ids[f"##{self.name}_{row}_sep"])
            for col in range(len(self.header)):
                dpg.delete_item(self.rows_ids[f"##{self.name}_{row}_{col}"])

        self.save_to_json()

    def get_cell_data(self, row: int, col: int) -> any:
        return dpg.get_value(self.rows_ids[f"##{self.name}_{row}_{col}"])

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
        item_label = dpg.get_item_label(item)

        row = int(item_label.split('_')[-2])
        col = int(item_label.split('_')[-1])

        id = dpg.get_value(self.rows_ids[f"##{self.name}_{row}_{1}"])
        col_name = self.header[col]
        self.ssh_info[id][col_name] = dpg.get_value(self.rows_ids[f"##{self.name}_{row}_{col}"])


ssh_table: Table
parent_id: int


def set_parent_id(_parent_id):
    global parent_id
    parent_id = _parent_id


def edit_ssh_info():
    global ssh_table
    global parent_id

    with dpg.window(label='ssh info editor', width=800, height=500, on_close=on_close):
        with dpg.group(horizontal=True):
            dpg.add_button(label='Add ssh server', callback=add_ssh_server_row)
            dpg.add_button(label='Remove ssh server', callback=remove_ssh_server_rows)
        ssh_table = Table('ssh info editor', ['', 'ID', 'Name', 'IP', 'Port', 'username', 'password'], parent_id)


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
    dpg.delete_item(ssh_table.id)

