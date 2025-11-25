from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class ButtonMaker:
    """
    A utility class for creating and organizing inline keyboard buttons.
    """
    def __init__(self):
        self.__button = []
        self.__header_button = []
        self.__first_body_button = []
        self.__last_body_button = []
        self.__footer_button = []

    def ubutton(self, key, link, position=None):
        """
        Adds a URL button.

        :param key: The text of the button.
        :param link: The URL for the button.
        :param position: The position of the button ('header', 'f_body', 'l_body', 'footer', or None for default).
        """
        button = InlineKeyboardButton(text=key, url=link)
        self.__add_button(button, position)

    def ibutton(self, key, data, position=None):
        """
        Adds a callback button.

        :param key: The text of the button.
        :param data: The callback data for the button.
        :param position: The position of the button ('header', 'f_body', 'l_body', 'footer', or None for default).
        """
        button = InlineKeyboardButton(text=key, callback_data=data)
        self.__add_button(button, position)

    def __add_button(self, button, position):
        if position == 'header':
            self.__header_button.append(button)
        elif position == 'f_body':
            self.__first_body_button.append(button)
        elif position == 'l_body':
            self.__last_body_button.append(button)
        elif position == 'footer':
            self.__footer_button.append(button)
        else:
            self.__button.append(button)

    def build_menu(self, b_cols=1, h_cols=8, fb_cols=2, lb_cols=2, f_cols=8):
        """
        Builds the inline keyboard menu with the added buttons.

        :param b_cols: The number of columns for the main body buttons.
        :param h_cols: The number of columns for the header buttons.
        :param fb_cols: The number of columns for the first body buttons.
        :param lb_cols: The number of columns for the last body buttons.
        :param f_cols: The number of columns for the footer buttons.
        :return: An InlineKeyboardMarkup object.
        """
        menu = [self.__button[i:i+b_cols] for i in range(0, len(self.__button), b_cols)]

        def build_row(buttons, cols):
            return [buttons[i:i+cols] for i in range(0, len(buttons), cols)]

        if self.__header_button:
            menu = build_row(self.__header_button, h_cols) + menu
        if self.__first_body_button:
            menu += build_row(self.__first_body_button, fb_cols)
        if self.__last_body_button:
            menu += build_row(self.__last_body_button, lb_cols)
        if self.__footer_button:
            menu += build_row(self.__footer_button, f_cols)

        return InlineKeyboardMarkup(menu)
