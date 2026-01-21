"""
Chakra UI Component Library Definition

Provides selectors and interaction patterns for Chakra UI components.
"""

from app.frameworks.registry import Component, ComponentLibrary


def get_library() -> ComponentLibrary:
    """Get the Chakra UI component library definition."""
    library = ComponentLibrary(
        name="chakra",
        base_framework="react",
        prefix="chakra"
    )

    # Button component
    library.components["button"] = Component(
        name="Button",
        selectors=[
            ".chakra-button",
            "[class*='chakra-button']",
            "button.chakra-button",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "hover": "hover",
            "focus": "focus",
        },
        child_selectors={
            "spinner": ".chakra-spinner",
        }
    )

    # Input component
    library.components["input"] = Component(
        name="Input",
        selectors=[
            ".chakra-input",
            "input.chakra-input",
        ],
        attributes=["data-testid", "aria-label", "placeholder"],
        actions={
            "fill": "fill",
            "clear": "clear",
            "type": "type",
        },
        child_selectors={}
    )

    # InputGroup component
    library.components["inputgroup"] = Component(
        name="InputGroup",
        selectors=[
            ".chakra-input__group",
            "[class*='chakra-input__group']",
        ],
        attributes=["data-testid"],
        actions={},
        child_selectors={
            "input": ".chakra-input",
            "left_element": ".chakra-input__left-element",
            "right_element": ".chakra-input__right-element",
            "left_addon": ".chakra-input__left-addon",
            "right_addon": ".chakra-input__right-addon",
        }
    )

    # Textarea component
    library.components["textarea"] = Component(
        name="Textarea",
        selectors=[
            ".chakra-textarea",
            "textarea.chakra-textarea",
        ],
        attributes=["data-testid", "aria-label", "placeholder"],
        actions={
            "fill": "fill",
            "clear": "clear",
            "type": "type",
        },
        child_selectors={}
    )

    # Select component
    library.components["select"] = Component(
        name="Select",
        selectors=[
            ".chakra-select",
            "select.chakra-select",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "select": "select_option",
            "click": "click",
        },
        child_selectors={
            "option": "option",
            "icon": ".chakra-select__icon-wrapper",
        }
    )

    # Checkbox component
    library.components["checkbox"] = Component(
        name="Checkbox",
        selectors=[
            ".chakra-checkbox",
            "[class*='chakra-checkbox']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "check": "check",
            "uncheck": "uncheck",
            "click": "click",
        },
        child_selectors={
            "input": ".chakra-checkbox__input",
            "control": ".chakra-checkbox__control",
            "label": ".chakra-checkbox__label",
        }
    )

    # Radio component
    library.components["radio"] = Component(
        name="Radio",
        selectors=[
            ".chakra-radio",
            "[class*='chakra-radio']",
        ],
        attributes=["data-testid", "aria-label", "value"],
        actions={
            "check": "check",
            "click": "click",
        },
        child_selectors={
            "input": ".chakra-radio__input",
            "control": ".chakra-radio__control",
            "label": ".chakra-radio__label",
        }
    )

    # Switch component
    library.components["switch"] = Component(
        name="Switch",
        selectors=[
            ".chakra-switch",
            "[class*='chakra-switch']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "check": "check",
            "uncheck": "uncheck",
        },
        child_selectors={
            "input": ".chakra-switch__input",
            "track": ".chakra-switch__track",
            "thumb": ".chakra-switch__thumb",
        }
    )

    # Modal component
    library.components["modal"] = Component(
        name="Modal",
        selectors=[
            ".chakra-modal__content",
            "[class*='chakra-modal']",
            "[role='dialog']",
        ],
        attributes=["data-testid", "aria-labelledby"],
        actions={
            "close": "click",
        },
        child_selectors={
            "overlay": ".chakra-modal__overlay",
            "header": ".chakra-modal__header",
            "body": ".chakra-modal__body",
            "footer": ".chakra-modal__footer",
            "close_button": ".chakra-modal__close-btn",
        }
    )

    # Drawer component
    library.components["drawer"] = Component(
        name="Drawer",
        selectors=[
            ".chakra-modal__content",  # Drawer uses modal content
            "[class*='chakra-slide']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "click",
        },
        child_selectors={
            "overlay": ".chakra-modal__overlay",
            "header": ".chakra-modal__header",
            "body": ".chakra-modal__body",
            "footer": ".chakra-modal__footer",
            "close_button": ".chakra-modal__close-btn",
        }
    )

    # Menu component
    library.components["menu"] = Component(
        name="Menu",
        selectors=[
            ".chakra-menu__menu-list",
            "[class*='chakra-menu']",
        ],
        attributes=["data-testid", "role"],
        actions={
            "click": "click",
        },
        child_selectors={
            "button": ".chakra-menu__menu-button",
            "list": ".chakra-menu__menu-list",
            "item": ".chakra-menu__menuitem",
            "divider": ".chakra-menu__divider",
            "group": ".chakra-menu__group",
        }
    )

    # Tabs component
    library.components["tabs"] = Component(
        name="Tabs",
        selectors=[
            ".chakra-tabs",
            "[class*='chakra-tabs']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "tablist": ".chakra-tabs__tablist",
            "tab": ".chakra-tabs__tab",
            "panels": ".chakra-tabs__tab-panels",
            "panel": ".chakra-tabs__tab-panel",
        }
    )

    # Accordion component
    library.components["accordion"] = Component(
        name="Accordion",
        selectors=[
            ".chakra-accordion",
            "[class*='chakra-accordion']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "item": ".chakra-accordion__item",
            "button": ".chakra-accordion__button",
            "panel": ".chakra-accordion__panel",
            "icon": ".chakra-accordion__icon",
        }
    )

    # Alert component
    library.components["alert"] = Component(
        name="Alert",
        selectors=[
            ".chakra-alert",
            "[class*='chakra-alert']",
            "[role='alert']",
        ],
        attributes=["data-testid", "data-status"],
        actions={
            "close": "click",
        },
        child_selectors={
            "icon": ".chakra-alert__icon",
            "title": ".chakra-alert__title",
            "description": ".chakra-alert__desc",
        }
    )

    # Toast component
    library.components["toast"] = Component(
        name="Toast",
        selectors=[
            ".chakra-toast",
            "[class*='chakra-toast']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "click",
        },
        child_selectors={
            "title": ".chakra-toast__title",
            "description": ".chakra-toast__description",
            "close_button": ".chakra-toast__close-btn",
        }
    )

    # Table component
    library.components["table"] = Component(
        name="Table",
        selectors=[
            ".chakra-table",
            "table.chakra-table",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "scroll": "scroll_into_view",
        },
        child_selectors={
            "container": ".chakra-table__container",
            "header": "thead",
            "body": "tbody",
            "footer": "tfoot",
            "row": "tr",
            "header_cell": "th",
            "cell": "td",
            "caption": "caption",
        }
    )

    # Card component
    library.components["card"] = Component(
        name="Card",
        selectors=[
            ".chakra-card",
            "[class*='chakra-card']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "header": ".chakra-card__header",
            "body": ".chakra-card__body",
            "footer": ".chakra-card__footer",
        }
    )

    # Popover component
    library.components["popover"] = Component(
        name="Popover",
        selectors=[
            ".chakra-popover__content",
            "[class*='chakra-popover']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "click",
        },
        child_selectors={
            "trigger": ".chakra-popover__trigger",
            "content": ".chakra-popover__content",
            "header": ".chakra-popover__header",
            "body": ".chakra-popover__body",
            "footer": ".chakra-popover__footer",
            "close_button": ".chakra-popover__close-btn",
            "arrow": ".chakra-popover__arrow",
        }
    )

    # Tooltip component
    library.components["tooltip"] = Component(
        name="Tooltip",
        selectors=[
            ".chakra-tooltip",
            "[class*='chakra-tooltip']",
            "[role='tooltip']",
        ],
        attributes=["data-testid"],
        actions={},
        child_selectors={
            "arrow": ".chakra-tooltip__arrow",
        }
    )

    # Spinner component
    library.components["spinner"] = Component(
        name="Spinner",
        selectors=[
            ".chakra-spinner",
            "[class*='chakra-spinner']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={},
        child_selectors={}
    )

    # Progress component
    library.components["progress"] = Component(
        name="Progress",
        selectors=[
            ".chakra-progress",
            "[class*='chakra-progress']",
        ],
        attributes=["data-testid", "aria-valuenow", "aria-valuemin", "aria-valuemax"],
        actions={},
        child_selectors={
            "track": ".chakra-progress__track",
            "filled_track": ".chakra-progress__filled-track",
        }
    )

    # Slider component
    library.components["slider"] = Component(
        name="Slider",
        selectors=[
            ".chakra-slider",
            "[class*='chakra-slider']",
        ],
        attributes=["data-testid", "aria-valuemin", "aria-valuemax"],
        actions={
            "click": "click",
        },
        child_selectors={
            "track": ".chakra-slider__track",
            "filled_track": ".chakra-slider__filled-track",
            "thumb": ".chakra-slider__thumb",
            "mark": ".chakra-slider__marker",
        }
    )

    # NumberInput component
    library.components["numberinput"] = Component(
        name="NumberInput",
        selectors=[
            ".chakra-numberinput",
            "[class*='chakra-numberinput']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "fill": "fill",
            "click": "click",
        },
        child_selectors={
            "field": ".chakra-numberinput__field",
            "stepper": ".chakra-numberinput__stepper",
            "increment": ".chakra-numberinput__stepper:first-child",
            "decrement": ".chakra-numberinput__stepper:last-child",
        }
    )

    # PinInput component
    library.components["pininput"] = Component(
        name="PinInput",
        selectors=[
            ".chakra-pin-input",
            "[class*='chakra-pin-input']",
        ],
        attributes=["data-testid"],
        actions={
            "fill": "fill",
            "type": "type",
        },
        child_selectors={
            "field": ".chakra-pin-input__field",
        }
    )

    # Avatar component
    library.components["avatar"] = Component(
        name="Avatar",
        selectors=[
            ".chakra-avatar",
            "[class*='chakra-avatar']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "image": ".chakra-avatar__img",
            "initials": ".chakra-avatar__initials",
            "badge": ".chakra-avatar__badge",
        }
    )

    # Badge component
    library.components["badge"] = Component(
        name="Badge",
        selectors=[
            ".chakra-badge",
            "[class*='chakra-badge']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={}
    )

    # Tag component
    library.components["tag"] = Component(
        name="Tag",
        selectors=[
            ".chakra-tag",
            "[class*='chakra-tag']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "label": ".chakra-tag__label",
            "close_button": ".chakra-tag__close-button",
        }
    )

    # Breadcrumb component
    library.components["breadcrumb"] = Component(
        name="Breadcrumb",
        selectors=[
            ".chakra-breadcrumb",
            "[class*='chakra-breadcrumb']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
        },
        child_selectors={
            "list": ".chakra-breadcrumb__list",
            "item": ".chakra-breadcrumb__list-item",
            "link": ".chakra-breadcrumb__link",
            "separator": ".chakra-breadcrumb__separator",
        }
    )

    # Editable component
    library.components["editable"] = Component(
        name="Editable",
        selectors=[
            ".chakra-editable",
            "[class*='chakra-editable']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
            "fill": "fill",
        },
        child_selectors={
            "preview": ".chakra-editable__preview",
            "input": ".chakra-editable__input",
            "textarea": ".chakra-editable__textarea",
        }
    )

    return library
