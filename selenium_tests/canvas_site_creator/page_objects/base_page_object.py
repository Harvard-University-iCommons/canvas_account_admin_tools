from selenium_common.base_page_object import BasePageObject


class BulkCreateBasePageObject(BasePageObject):
    def __init__(self, driver):
        super(BulkCreateBasePageObject, self).__init__(driver)
        self.focus_on_tool_frame()



