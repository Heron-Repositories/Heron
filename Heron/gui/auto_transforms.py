from dearpygui import dearpygui as dpg

def auto_align(item, alignment_type: int, x_align: float = 0.5, y_align: float = 0.5):
    def _center_h(_s, _d, data):
        parent = dpg.get_item_parent(data[0])
        while dpg.get_item_info(parent)['type'] != "mvAppItemType::mvWindowAppItem":
            parent = dpg.get_item_parent(parent)
        parent_width = dpg.get_item_rect_size(parent)[0]
        width = dpg.get_item_rect_size(data[0])[0]
        new_x = (parent_width // 2 - width // 2) * data[1] * 2
        dpg.set_item_pos(data[0], [new_x, dpg.get_item_pos(data[0])[1]])

    def _center_v(_s, _d, data):
        parent = dpg.get_item_parent(data[0])
        while dpg.get_item_info(parent)['type'] != "mvAppItemType::mvWindowAppItem":
            parent = dpg.get_item_parent(parent)
        parent_width = dpg.get_item_rect_size(parent)[1]
        height = dpg.get_item_rect_size(data[0])[1]
        new_y = (parent_width // 2 - height // 2) * data[1] * 2
        dpg.set_item_pos(data[0], [dpg.get_item_pos(data[0])[0], new_y])

    if 0 <= alignment_type <= 2:
        with dpg.item_handler_registry():
            if alignment_type == 0:
                # horizontal only alignment
                dpg.add_item_visible_handler(callback=_center_h, user_data=[item, x_align])
            elif alignment_type == 1:
                # vertical only alignment
                dpg.add_item_visible_handler(callback=_center_v, user_data=[item, y_align])
            elif alignment_type == 2:
                # both horizontal and vertical alignment
                dpg.add_item_visible_handler(callback=_center_h, user_data=[item, x_align])
                dpg.add_item_visible_handler(callback=_center_v, user_data=[item, y_align])

        dpg.bind_item_handler_registry(item, dpg.last_container())


def auto_resize(item, resize_direction: int, x_offset: int = 10, y_offset: int = 10,
                min_x: int = 50, min_y: int = 50):
    def _resize_h(_s, _d, data):
        parent = dpg.get_item_parent(data[0])
        while dpg.get_item_info(parent)['type'] != "mvAppItemType::mvWindowAppItem":
            parent = dpg.get_item_parent(parent)
        parent_width = dpg.get_item_rect_size(parent)[0]
        new_width = parent_width - data[1] if parent_width - data[1] > min_x else min_x

        dpg.set_item_width(data[0], new_width)

    def _resize_v(_s, _d, data):
        parent = dpg.get_item_parent(data[0])
        while dpg.get_item_info(parent)['type'] != "mvAppItemType::mvWindowAppItem":
            parent = dpg.get_item_parent(parent)
        parent_height = dpg.get_item_rect_size(parent)[1]
        #height = dpg.get_item_rect_size(data[0])[1]
        new_height = parent_height - data[1] if parent_height - data[1] > min_y else min_y
        dpg.set_item_height(data[0], new_height)

    if 0 <= resize_direction <= 2:
        with dpg.item_handler_registry():
            if resize_direction == 0:
                # x only
                dpg.add_item_visible_handler(callback=_resize_h, user_data=[item, x_offset])
            elif resize_direction == 1:
                # y only
                dpg.add_item_visible_handler(callback=_resize_v, user_data=[item, y_offset])
            elif resize_direction == 2:
                # both x and y
                dpg.add_item_visible_handler(callback=_resize_h, user_data=[item, x_offset])
                dpg.add_item_visible_handler(callback=_resize_v, user_data=[item, y_offset])

        dpg.bind_item_handler_registry(item, dpg.last_container())