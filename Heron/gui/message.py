from dearpygui import dearpygui as dpg


class Message:
    def __init__(self, message_txt, show_ok_button=True, element_indent=0, loading_indicator=False):

        with dpg.window(label="Error Window", modal=True, show=True, id="modal_error_id",
                        no_title_bar=True, popup=True, pos=[500, 300], on_close=self.__del__):
            if show_ok_button:
                dpg.add_text(message_txt)
                dpg.add_separator()
                dpg.add_button(label="OK", width=75, indent=element_indent, callback=self.__del__)
            elif loading_indicator:
                ind_indent = element_indent if element_indent else 0
                dpg.add_loading_indicator(indent=ind_indent)
                dpg.add_spacer(height=10)
                dpg.add_text(message_txt)
            else:
                dpg.add_text(message_txt)

    def __del__(self):
        if dpg.does_alias_exist('modal_error_id'):
            dpg.delete_item('modal_error_id')
        if dpg.does_alias_exist("modal_id_credentials"):
            dpg.delete_item("modal_id_credentials")
            print('killed creds window')
        if dpg.does_alias_exist("modal_id_folders_not_found"):
            dpg.delete_item("modal_id_folders_not_found")
            print('killed wrong folder window')

        del self



