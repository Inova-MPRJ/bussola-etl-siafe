import time
from typing import List

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
)
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select


class Filter:
    """A single filter to control information shown in a SIAFE Basic table."""

    _property_select_sel = "[id*='cbx_col_sel_rtfFilter::content']"
    """CSS selector for the <select> element that sets the property the
    filter applies to."""

    _negate_checkbox_sel = "[id*='chk_neg_rtfFilter::content']"
    """CSS selector for the checkbox that negates the value of the operation.
    """

    _operation_select_sel = "[name*='cbx_op_sel_rtfFilter']"
    """CSS selector for the <select> element that sets the filter operation."""

    _value_select_sel = "[id*='select_value_rtfFilter::content']"
    """CSS selector for a <select> field with the filter value."""

    _value_input_sel = "[id*='in_value_rtfFilter::content']"
    """CSS selector for an <input> field with the filter value."""

    @classmethod
    def from_element(cls, filter_elem: WebElement):
        """Initialize a Filter instance from a `WebElement`.

        Parameters:
            filter_elem: A `WebElement` instance
        """

        # get the table property that the filter is applied to
        property_elem = filter_elem.find_element_by_css_selector(
            cls._property_select_sel
        )
        filtered_property = property_elem.get_attribute('title')
        if filtered_property is None or filtered_property == "Selecione":
            # the row is reserved for adding new a filter; skip it
            return None

        # get whether the operation is to be negated
        negate_elem = filter_elem.find_element_by_css_selector(
            cls._property_select_sel
        )
        if negate_elem.get_attribute('checked'):
            negate = True
        else:
            negate = False

        # get the filter operation
        operation_elem = filter_elem.find_element_by_css_selector(
            cls._operation_select_sel
        )
        operation = operation_elem.get_attribute('title')

        # get filter value
        value_elem = filter_elem.find_element_by_css_selector(
            ", ".join([cls._value_select_sel, cls._value_input_sel])
        )
        value = value_elem.get_attribute('title')
        if not value:
            value = value_elem.get_attribute('value')

        # instantiate filter
        return Filter(filtered_property, operation, value, negate)

    def __init__(
        self,
        filtered_property: str,
        operation: str,
        value: str,
        negate: bool = False,
    ):
        self.filtered_property = filtered_property
        self.operation = operation
        self.value = str(value)
        self.negate = negate

    def __eq__(self, other):
        """Determines whether an object is identical to the Filter instance."""
        print("Checking equality")
        try:
            print(
                f"Properties: {self.filtered_property} X {other.filtered_property}"
            )
            print(f"Operation: {self.operation} X {other.operation}")
            print(f"Values: {self.value} X {other.value}")
            print(f"Negate: {self.negate} X {other.negate}")
            is_equal: bool = all(
                [
                    self.filtered_property == other.filtered_property,
                    self.operation == other.operation,
                    self.value == other.value,
                    self.negate == other.negate,
                ]
            )
        except AttributeError:
            print("Something is missing")
            is_equal = False

        return is_equal


class FilterMenu:
    """Component with a collection of filters applied to a SIAFE Basic table."""

    _reset_button_sel = "[id*='btnClearFilter::icon']"
    """CSS selector for the button that clears all filters."""

    _filters_body_sel: str = "[id*='sdtFilter::body']"
    """CSS selector for <div> in which the "filter menu" body is contained.
    """

    _toggle_button_sel: str = "[id*='sdtFilter::btn']"
    """CSS selector used for the button that toggles/collapses the filter menu.
    """

    _filters_header_sel: str = "[id*='sdtFilter::head']"
    """CSS selector for the filter menu headers"""

    def __init__(self, page: WebElement):
        self._page: WebElement = page

    @property
    def _header(self) -> WebElement:
        return self._page.driver.find_element_by_css_selector(
            FilterMenu._filters_header_sel
        )

    @property
    def _body(self) -> WebElement:
        return self._page.driver.find_element_by_css_selector(
            FilterMenu._filters_body_sel
        )

    @property
    def visible(self) -> bool:
        """Whether filter collection body is visible."""

        visible: bool

        try:
            assert self._header.find_elements_by_class_name("x16b")
            visible = True
        except (AssertionError, StaleElementReferenceException):
            visible = False

        return visible

    @visible.setter
    def visible(self, value: bool) -> None:
        if self.visible != value:
            self.toggle()

    def toggle(self) -> None:
        """Switch visibility of the filter collection body in page."""

        initial_state = self.visible
        counter = 0

        while self.visible == initial_state:
            if counter % 5 == 0:
                toggle_button = self._header.find_element_by_css_selector(
                    self._toggle_button_sel
                )
                toggle_button.click()
            else:
                time.sleep(1)
            counter += 1

    @property
    def filters(self) -> List[Filter]:
        """List all filters currently in the filter collection."""

        self.visible = True

        filters: List[Filter] = list()
        for filter_elem in self._body.find_elements_by_class_name("xzy"):
            filter_ = Filter.from_element(filter_elem)
            if filter_:
                filters.append(filter_)

        return filters

    @filters.setter
    def filters(self, new_filter: Filter) -> None:
        """Add a new filter."""

        # TODO: use custom list methods instead of setter to control elements

        if not isinstance(new_filter, Filter):
            raise TypeError

        self.visible = True

        slot = self._body.find_elements_by_class_name("xzy")[-1]

        # set filter property
        property_elem = slot.find_element_by_css_selector(
            Filter._property_select_sel
        )
        Select(property_elem).select_by_visible_text(
            new_filter.filtered_property
        )

        # set whether filter operation should be negated
        if new_filter.negate:
            slot = self._body.find_elements_by_class_name("xzy")[-1]
            negate_elem = slot.find_element_by_css_selector(
                Filter._negate_checkbox_sel
            )
            negate_elem.click()

        # set the filter operation
        while True:
            slot = self._body.find_elements_by_class_name("xzy")[-1]
            operation_elem = slot.find_element_by_css_selector(
                Filter._operation_select_sel
            )
            if operation_elem.get_attribute("title") == new_filter.operation:
                break
            else:
                Select(operation_elem).select_by_visible_text(
                    new_filter.operation
                )
                time.sleep(2)

        # set the filter value
        try:
            slot = self._body.find_elements_by_class_name("xzy")[-1]
            value_elems = slot.find_elements_by_css_selector(
                Filter._value_select_sel
            )
            Select(value_elems[0]).select_by_visible_text(new_filter.value)
        except (
            StaleElementReferenceException,
            NoSuchElementException,
            IndexError,
        ):
            slot = self._body.find_elements_by_class_name("xzy")[-1]
            value_elem = slot.find_element_by_css_selector(
                Filter._value_input_sel
            )
            value_elem.send_keys(new_filter.value)

    # TODO: single filter delete

    def reset(self) -> None:
        """Clear all existing filters."""

        self.visible = True

        reset_button = self._header.find_element_by_css_selector(
            self._reset_button_sel
        )
        reset_button.click()

    def apply(self):
        """Apply the latest changes in filters and collapse the menu."""
        self._body.click()
        self.visible = False
