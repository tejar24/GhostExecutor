"""
Material-UI (MUI) Component Library Definition

Provides selectors and interaction patterns for MUI v5+ components.
"""

from app.frameworks.registry import Component, ComponentLibrary


def get_library() -> ComponentLibrary:
    """Get the MUI component library definition."""
    library = ComponentLibrary(
        name="mui",
        base_framework="react",
        prefix="Mui"
    )

    # Button component
    library.components["button"] = Component(
        name="Button",
        selectors=[
            ".MuiButton-root",
            "[class*='MuiButton']",
            "button.MuiButton-root",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "hover": "hover",
            "focus": "focus",
        },
        child_selectors={
            "label": ".MuiButton-label",
            "startIcon": ".MuiButton-startIcon",
            "endIcon": ".MuiButton-endIcon",
        }
    )

    # TextField component
    library.components["textfield"] = Component(
        name="TextField",
        selectors=[
            ".MuiTextField-root",
            ".MuiFormControl-root:has(.MuiInputBase-root)",
            "[class*='MuiTextField']",
        ],
        attributes=["data-testid", "aria-label", "placeholder"],
        actions={
            "fill": "fill",
            "clear": "clear",
            "type": "type",
        },
        child_selectors={
            "input": ".MuiInputBase-input",
            "label": ".MuiInputLabel-root",
            "helper_text": ".MuiFormHelperText-root",
            "error": ".Mui-error",
        }
    )

    # Select component
    library.components["select"] = Component(
        name="Select",
        selectors=[
            ".MuiSelect-root",
            "[class*='MuiSelect']",
            ".MuiFormControl-root:has(.MuiSelect-select)",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "select": "select_option",
        },
        child_selectors={
            "select": ".MuiSelect-select",
            "icon": ".MuiSelect-icon",
            "menu": ".MuiMenu-paper",
            "option": ".MuiMenuItem-root",
        }
    )

    # Checkbox component
    library.components["checkbox"] = Component(
        name="Checkbox",
        selectors=[
            ".MuiCheckbox-root",
            "[class*='MuiCheckbox']",
            "input[type='checkbox'].MuiCheckbox-input",
        ],
        attributes=["data-testid", "aria-label", "name"],
        actions={
            "check": "check",
            "uncheck": "uncheck",
            "click": "click",
        },
        child_selectors={
            "input": "input[type='checkbox']",
            "icon": ".MuiSvgIcon-root",
        }
    )

    # Radio component
    library.components["radio"] = Component(
        name="Radio",
        selectors=[
            ".MuiRadio-root",
            "[class*='MuiRadio']",
            "input[type='radio'].MuiRadio-input",
        ],
        attributes=["data-testid", "aria-label", "name", "value"],
        actions={
            "check": "check",
            "click": "click",
        },
        child_selectors={
            "input": "input[type='radio']",
            "icon": ".MuiSvgIcon-root",
        }
    )

    # Switch component
    library.components["switch"] = Component(
        name="Switch",
        selectors=[
            ".MuiSwitch-root",
            "[class*='MuiSwitch']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "check": "check",
            "uncheck": "uncheck",
            "click": "click",
        },
        child_selectors={
            "input": ".MuiSwitch-input",
            "thumb": ".MuiSwitch-thumb",
            "track": ".MuiSwitch-track",
        }
    )

    # Autocomplete component
    library.components["autocomplete"] = Component(
        name="Autocomplete",
        selectors=[
            ".MuiAutocomplete-root",
            "[class*='MuiAutocomplete']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "fill": "fill",
            "click": "click",
            "clear": "clear",
        },
        child_selectors={
            "input": ".MuiAutocomplete-input",
            "popup": ".MuiAutocomplete-popper",
            "option": ".MuiAutocomplete-option",
            "clear_button": ".MuiAutocomplete-clearIndicator",
        }
    )

    # Dialog component
    library.components["dialog"] = Component(
        name="Dialog",
        selectors=[
            ".MuiDialog-root",
            "[class*='MuiDialog']",
            "[role='dialog']",
        ],
        attributes=["data-testid", "aria-labelledby"],
        actions={
            "close": "press_key('Escape')",
        },
        child_selectors={
            "title": ".MuiDialogTitle-root",
            "content": ".MuiDialogContent-root",
            "actions": ".MuiDialogActions-root",
            "close_button": "button[aria-label='close']",
        }
    )

    # Menu component
    library.components["menu"] = Component(
        name="Menu",
        selectors=[
            ".MuiMenu-root",
            "[class*='MuiMenu']",
            "[role='menu']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "press_key('Escape')",
        },
        child_selectors={
            "paper": ".MuiMenu-paper",
            "list": ".MuiMenu-list",
            "item": ".MuiMenuItem-root",
        }
    )

    # Table component
    library.components["table"] = Component(
        name="Table",
        selectors=[
            ".MuiTable-root",
            "[class*='MuiTable']",
            ".MuiTableContainer-root table",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "scroll": "scroll_into_view",
        },
        child_selectors={
            "header": ".MuiTableHead-root",
            "body": ".MuiTableBody-root",
            "row": ".MuiTableRow-root",
            "cell": ".MuiTableCell-root",
            "header_cell": ".MuiTableCell-head",
            "pagination": ".MuiTablePagination-root",
        }
    )

    # Tabs component
    library.components["tabs"] = Component(
        name="Tabs",
        selectors=[
            ".MuiTabs-root",
            "[class*='MuiTabs']",
            "[role='tablist']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
        },
        child_selectors={
            "tab": ".MuiTab-root",
            "indicator": ".MuiTabs-indicator",
            "scroller": ".MuiTabs-scroller",
        }
    )

    # Snackbar component
    library.components["snackbar"] = Component(
        name="Snackbar",
        selectors=[
            ".MuiSnackbar-root",
            "[class*='MuiSnackbar']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "click",
        },
        child_selectors={
            "content": ".MuiSnackbarContent-root",
            "message": ".MuiSnackbarContent-message",
            "action": ".MuiSnackbarContent-action",
        }
    )

    # Alert component
    library.components["alert"] = Component(
        name="Alert",
        selectors=[
            ".MuiAlert-root",
            "[class*='MuiAlert']",
            "[role='alert']",
        ],
        attributes=["data-testid", "severity"],
        actions={
            "close": "click",
        },
        child_selectors={
            "icon": ".MuiAlert-icon",
            "message": ".MuiAlert-message",
            "action": ".MuiAlert-action",
            "close_button": ".MuiAlert-action button",
        }
    )

    # Chip component
    library.components["chip"] = Component(
        name="Chip",
        selectors=[
            ".MuiChip-root",
            "[class*='MuiChip']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "delete": "click",
        },
        child_selectors={
            "label": ".MuiChip-label",
            "delete_icon": ".MuiChip-deleteIcon",
            "avatar": ".MuiChip-avatar",
        }
    )

    # DatePicker component
    library.components["datepicker"] = Component(
        name="DatePicker",
        selectors=[
            ".MuiDatePicker-root",
            "[class*='MuiPickersDay']",
            ".MuiPickersBasePicker-container",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "fill": "fill",
            "click": "click",
        },
        child_selectors={
            "input": ".MuiInputBase-input",
            "calendar_button": "[aria-label*='calendar']",
            "day": ".MuiPickersDay-root",
            "month": ".MuiPickersMonth-root",
            "year": ".MuiPickersYear-root",
        }
    )

    # Drawer component
    library.components["drawer"] = Component(
        name="Drawer",
        selectors=[
            ".MuiDrawer-root",
            "[class*='MuiDrawer']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "press_key('Escape')",
        },
        child_selectors={
            "paper": ".MuiDrawer-paper",
            "backdrop": ".MuiBackdrop-root",
        }
    )

    # Accordion component
    library.components["accordion"] = Component(
        name="Accordion",
        selectors=[
            ".MuiAccordion-root",
            "[class*='MuiAccordion']",
        ],
        attributes=["data-testid"],
        actions={
            "expand": "click",
            "collapse": "click",
        },
        child_selectors={
            "summary": ".MuiAccordionSummary-root",
            "details": ".MuiAccordionDetails-root",
            "expand_icon": ".MuiAccordionSummary-expandIconWrapper",
        }
    )

    # Slider component
    library.components["slider"] = Component(
        name="Slider",
        selectors=[
            ".MuiSlider-root",
            "[class*='MuiSlider']",
        ],
        attributes=["data-testid", "aria-label", "aria-valuemin", "aria-valuemax"],
        actions={
            "click": "click",
            "drag": "drag",
        },
        child_selectors={
            "thumb": ".MuiSlider-thumb",
            "track": ".MuiSlider-track",
            "rail": ".MuiSlider-rail",
            "mark": ".MuiSlider-mark",
        }
    )

    return library
