"""
Ant Design Component Library Definition

Provides selectors and interaction patterns for Ant Design v5+ components.
"""

from app.frameworks.registry import Component, ComponentLibrary


def get_library() -> ComponentLibrary:
    """Get the Ant Design component library definition."""
    library = ComponentLibrary(
        name="antd",
        base_framework="react",
        prefix="ant"
    )

    # Button component
    library.components["button"] = Component(
        name="Button",
        selectors=[
            ".ant-btn",
            "[class*='ant-btn']",
            "button.ant-btn",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "hover": "hover",
            "focus": "focus",
        },
        child_selectors={
            "icon": ".anticon",
            "loading": ".ant-btn-loading-icon",
        }
    )

    # Input component
    library.components["input"] = Component(
        name="Input",
        selectors=[
            ".ant-input",
            "[class*='ant-input']",
            "input.ant-input",
        ],
        attributes=["data-testid", "aria-label", "placeholder"],
        actions={
            "fill": "fill",
            "clear": "clear",
            "type": "type",
        },
        child_selectors={
            "prefix": ".ant-input-prefix",
            "suffix": ".ant-input-suffix",
            "clear_button": ".ant-input-clear-icon",
        }
    )

    # Input with wrapper
    library.components["inputwrapper"] = Component(
        name="InputWrapper",
        selectors=[
            ".ant-input-affix-wrapper",
            ".ant-form-item-control-input",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "input": ".ant-input",
            "prefix": ".ant-input-prefix",
            "suffix": ".ant-input-suffix",
        }
    )

    # Select component
    library.components["select"] = Component(
        name="Select",
        selectors=[
            ".ant-select",
            "[class*='ant-select']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "select": "select_option",
        },
        child_selectors={
            "selector": ".ant-select-selector",
            "arrow": ".ant-select-arrow",
            "clear": ".ant-select-clear",
            "dropdown": ".ant-select-dropdown",
            "option": ".ant-select-item-option",
        }
    )

    # Checkbox component
    library.components["checkbox"] = Component(
        name="Checkbox",
        selectors=[
            ".ant-checkbox-wrapper",
            "[class*='ant-checkbox']",
            ".ant-checkbox",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "check": "check",
            "uncheck": "uncheck",
            "click": "click",
        },
        child_selectors={
            "input": ".ant-checkbox-input",
            "inner": ".ant-checkbox-inner",
        }
    )

    # Radio component
    library.components["radio"] = Component(
        name="Radio",
        selectors=[
            ".ant-radio-wrapper",
            "[class*='ant-radio']",
            ".ant-radio",
        ],
        attributes=["data-testid", "aria-label", "value"],
        actions={
            "check": "check",
            "click": "click",
        },
        child_selectors={
            "input": ".ant-radio-input",
            "inner": ".ant-radio-inner",
        }
    )

    # Switch component
    library.components["switch"] = Component(
        name="Switch",
        selectors=[
            ".ant-switch",
            "[class*='ant-switch']",
            "button.ant-switch",
        ],
        attributes=["data-testid", "aria-label", "aria-checked"],
        actions={
            "click": "click",
            "check": "check",
            "uncheck": "uncheck",
        },
        child_selectors={
            "handle": ".ant-switch-handle",
            "inner": ".ant-switch-inner",
        }
    )

    # DatePicker component
    library.components["datepicker"] = Component(
        name="DatePicker",
        selectors=[
            ".ant-picker",
            "[class*='ant-picker']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "fill": "fill",
        },
        child_selectors={
            "input": ".ant-picker-input input",
            "clear": ".ant-picker-clear",
            "suffix": ".ant-picker-suffix",
            "dropdown": ".ant-picker-dropdown",
            "cell": ".ant-picker-cell",
        }
    )

    # Table component
    library.components["table"] = Component(
        name="Table",
        selectors=[
            ".ant-table",
            "[class*='ant-table']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "scroll": "scroll_into_view",
        },
        child_selectors={
            "header": ".ant-table-thead",
            "body": ".ant-table-tbody",
            "row": ".ant-table-row",
            "cell": ".ant-table-cell",
            "pagination": ".ant-pagination",
            "sorter": ".ant-table-column-sorter",
            "filter": ".ant-table-filter-trigger",
        }
    )

    # Modal component
    library.components["modal"] = Component(
        name="Modal",
        selectors=[
            ".ant-modal",
            "[class*='ant-modal']",
            ".ant-modal-wrap",
        ],
        attributes=["data-testid", "aria-labelledby"],
        actions={
            "close": "click",
        },
        child_selectors={
            "content": ".ant-modal-content",
            "header": ".ant-modal-header",
            "title": ".ant-modal-title",
            "body": ".ant-modal-body",
            "footer": ".ant-modal-footer",
            "close_button": ".ant-modal-close",
        }
    )

    # Drawer component
    library.components["drawer"] = Component(
        name="Drawer",
        selectors=[
            ".ant-drawer",
            "[class*='ant-drawer']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "click",
        },
        child_selectors={
            "content": ".ant-drawer-content",
            "header": ".ant-drawer-header",
            "title": ".ant-drawer-title",
            "body": ".ant-drawer-body",
            "close_button": ".ant-drawer-close",
            "mask": ".ant-drawer-mask",
        }
    )

    # Tabs component
    library.components["tabs"] = Component(
        name="Tabs",
        selectors=[
            ".ant-tabs",
            "[class*='ant-tabs']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
        },
        child_selectors={
            "nav": ".ant-tabs-nav",
            "tab": ".ant-tabs-tab",
            "content": ".ant-tabs-content",
            "pane": ".ant-tabs-tabpane",
        }
    )

    # Menu component
    library.components["menu"] = Component(
        name="Menu",
        selectors=[
            ".ant-menu",
            "[class*='ant-menu']",
        ],
        attributes=["data-testid", "role"],
        actions={
            "click": "click",
        },
        child_selectors={
            "item": ".ant-menu-item",
            "submenu": ".ant-menu-submenu",
            "submenu_title": ".ant-menu-submenu-title",
        }
    )

    # Dropdown component
    library.components["dropdown"] = Component(
        name="Dropdown",
        selectors=[
            ".ant-dropdown",
            "[class*='ant-dropdown']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "menu": ".ant-dropdown-menu",
            "item": ".ant-dropdown-menu-item",
        }
    )

    # Form component
    library.components["form"] = Component(
        name="Form",
        selectors=[
            ".ant-form",
            "[class*='ant-form']",
            "form.ant-form",
        ],
        attributes=["data-testid"],
        actions={
            "submit": "submit",
        },
        child_selectors={
            "item": ".ant-form-item",
            "label": ".ant-form-item-label",
            "control": ".ant-form-item-control",
            "error": ".ant-form-item-explain-error",
        }
    )

    # Message/Notification component
    library.components["message"] = Component(
        name="Message",
        selectors=[
            ".ant-message",
            "[class*='ant-message']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "click",
        },
        child_selectors={
            "notice": ".ant-message-notice",
            "content": ".ant-message-notice-content",
        }
    )

    # Alert component
    library.components["alert"] = Component(
        name="Alert",
        selectors=[
            ".ant-alert",
            "[class*='ant-alert']",
        ],
        attributes=["data-testid", "role"],
        actions={
            "close": "click",
        },
        child_selectors={
            "icon": ".ant-alert-icon",
            "message": ".ant-alert-message",
            "description": ".ant-alert-description",
            "close_button": ".ant-alert-close-icon",
        }
    )

    # Card component
    library.components["card"] = Component(
        name="Card",
        selectors=[
            ".ant-card",
            "[class*='ant-card']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "head": ".ant-card-head",
            "title": ".ant-card-head-title",
            "body": ".ant-card-body",
            "actions": ".ant-card-actions",
        }
    )

    # Collapse/Accordion component
    library.components["collapse"] = Component(
        name="Collapse",
        selectors=[
            ".ant-collapse",
            "[class*='ant-collapse']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "item": ".ant-collapse-item",
            "header": ".ant-collapse-header",
            "content": ".ant-collapse-content",
            "arrow": ".ant-collapse-arrow",
        }
    )

    # Pagination component
    library.components["pagination"] = Component(
        name="Pagination",
        selectors=[
            ".ant-pagination",
            "[class*='ant-pagination']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "item": ".ant-pagination-item",
            "prev": ".ant-pagination-prev",
            "next": ".ant-pagination-next",
            "jump_prev": ".ant-pagination-jump-prev",
            "jump_next": ".ant-pagination-jump-next",
        }
    )

    # Upload component
    library.components["upload"] = Component(
        name="Upload",
        selectors=[
            ".ant-upload",
            "[class*='ant-upload']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "input": "input[type='file']",
            "button": ".ant-upload-select",
            "list": ".ant-upload-list",
            "item": ".ant-upload-list-item",
        }
    )

    # Tree component
    library.components["tree"] = Component(
        name="Tree",
        selectors=[
            ".ant-tree",
            "[class*='ant-tree']",
        ],
        attributes=["data-testid", "role"],
        actions={
            "click": "click",
        },
        child_selectors={
            "node": ".ant-tree-treenode",
            "switcher": ".ant-tree-switcher",
            "checkbox": ".ant-tree-checkbox",
            "title": ".ant-tree-node-content-wrapper",
        }
    )

    return library
