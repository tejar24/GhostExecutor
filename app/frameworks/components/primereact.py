"""
PrimeReact Component Library Definition

Provides selectors and interaction patterns for PrimeReact components.
"""

from app.frameworks.registry import Component, ComponentLibrary


def get_library() -> ComponentLibrary:
    """Get the PrimeReact component library definition."""
    library = ComponentLibrary(
        name="primereact",
        base_framework="react",
        prefix="p-"
    )

    # Button component
    library.components["button"] = Component(
        name="Button",
        selectors=[
            ".p-button",
            "[class*='p-button']",
            "button.p-button",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "hover": "hover",
            "focus": "focus",
        },
        child_selectors={
            "label": ".p-button-label",
            "icon": ".p-button-icon",
            "badge": ".p-badge",
        }
    )

    # InputText component
    library.components["inputtext"] = Component(
        name="InputText",
        selectors=[
            ".p-inputtext",
            "input.p-inputtext",
        ],
        attributes=["data-testid", "aria-label", "placeholder"],
        actions={
            "fill": "fill",
            "clear": "clear",
            "type": "type",
        },
        child_selectors={}
    )

    # InputTextarea component
    library.components["inputtextarea"] = Component(
        name="InputTextarea",
        selectors=[
            ".p-inputtextarea",
            "textarea.p-inputtextarea",
        ],
        attributes=["data-testid", "aria-label", "placeholder"],
        actions={
            "fill": "fill",
            "clear": "clear",
            "type": "type",
        },
        child_selectors={}
    )

    # Dropdown component
    library.components["dropdown"] = Component(
        name="Dropdown",
        selectors=[
            ".p-dropdown",
            "[class*='p-dropdown']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "select": "select_option",
        },
        child_selectors={
            "label": ".p-dropdown-label",
            "trigger": ".p-dropdown-trigger",
            "panel": ".p-dropdown-panel",
            "item": ".p-dropdown-item",
            "filter": ".p-dropdown-filter",
        }
    )

    # MultiSelect component
    library.components["multiselect"] = Component(
        name="MultiSelect",
        selectors=[
            ".p-multiselect",
            "[class*='p-multiselect']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
        },
        child_selectors={
            "label": ".p-multiselect-label",
            "trigger": ".p-multiselect-trigger",
            "panel": ".p-multiselect-panel",
            "item": ".p-multiselect-item",
            "checkbox": ".p-checkbox",
            "header": ".p-multiselect-header",
        }
    )

    # Checkbox component
    library.components["checkbox"] = Component(
        name="Checkbox",
        selectors=[
            ".p-checkbox",
            "[class*='p-checkbox']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "check": "check",
            "uncheck": "uncheck",
            "click": "click",
        },
        child_selectors={
            "box": ".p-checkbox-box",
            "icon": ".p-checkbox-icon",
            "input": ".p-checkbox input",
        }
    )

    # RadioButton component
    library.components["radiobutton"] = Component(
        name="RadioButton",
        selectors=[
            ".p-radiobutton",
            "[class*='p-radiobutton']",
        ],
        attributes=["data-testid", "aria-label", "value"],
        actions={
            "check": "check",
            "click": "click",
        },
        child_selectors={
            "box": ".p-radiobutton-box",
            "icon": ".p-radiobutton-icon",
            "input": ".p-radiobutton input",
        }
    )

    # InputSwitch component
    library.components["inputswitch"] = Component(
        name="InputSwitch",
        selectors=[
            ".p-inputswitch",
            "[class*='p-inputswitch']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
        },
        child_selectors={
            "slider": ".p-inputswitch-slider",
            "input": ".p-inputswitch input",
        }
    )

    # Calendar component
    library.components["calendar"] = Component(
        name="Calendar",
        selectors=[
            ".p-calendar",
            "[class*='p-calendar']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
            "fill": "fill",
        },
        child_selectors={
            "input": ".p-inputtext",
            "button": ".p-datepicker-trigger",
            "panel": ".p-datepicker",
            "header": ".p-datepicker-header",
            "table": ".p-datepicker-calendar",
            "day": "td span:not(.p-disabled)",
        }
    )

    # DataTable component
    library.components["datatable"] = Component(
        name="DataTable",
        selectors=[
            ".p-datatable",
            "[class*='p-datatable']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "scroll": "scroll_into_view",
        },
        child_selectors={
            "header": ".p-datatable-header",
            "thead": ".p-datatable-thead",
            "tbody": ".p-datatable-tbody",
            "row": ".p-datatable-tbody tr",
            "cell": "td",
            "header_cell": "th",
            "paginator": ".p-paginator",
            "filter": ".p-column-filter",
            "sortable": ".p-sortable-column",
        }
    )

    # Dialog component
    library.components["dialog"] = Component(
        name="Dialog",
        selectors=[
            ".p-dialog",
            "[class*='p-dialog']",
        ],
        attributes=["data-testid", "aria-labelledby"],
        actions={
            "close": "click",
        },
        child_selectors={
            "header": ".p-dialog-header",
            "title": ".p-dialog-title",
            "content": ".p-dialog-content",
            "footer": ".p-dialog-footer",
            "close_button": ".p-dialog-header-close",
            "mask": ".p-dialog-mask",
        }
    )

    # Sidebar component
    library.components["sidebar"] = Component(
        name="Sidebar",
        selectors=[
            ".p-sidebar",
            "[class*='p-sidebar']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "click",
        },
        child_selectors={
            "header": ".p-sidebar-header",
            "content": ".p-sidebar-content",
            "close_button": ".p-sidebar-close",
            "mask": ".p-sidebar-mask",
        }
    )

    # TabView component
    library.components["tabview"] = Component(
        name="TabView",
        selectors=[
            ".p-tabview",
            "[class*='p-tabview']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "nav": ".p-tabview-nav",
            "header": ".p-tabview-header",
            "panel": ".p-tabview-panel",
            "title": ".p-tabview-title",
        }
    )

    # Menu component
    library.components["menu"] = Component(
        name="Menu",
        selectors=[
            ".p-menu",
            "[class*='p-menu']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "list": ".p-menu-list",
            "item": ".p-menuitem",
            "link": ".p-menuitem-link",
            "text": ".p-menuitem-text",
            "icon": ".p-menuitem-icon",
        }
    )

    # Toast component
    library.components["toast"] = Component(
        name="Toast",
        selectors=[
            ".p-toast",
            "[class*='p-toast']",
        ],
        attributes=["data-testid"],
        actions={
            "close": "click",
        },
        child_selectors={
            "message": ".p-toast-message",
            "content": ".p-toast-message-content",
            "icon": ".p-toast-message-icon",
            "text": ".p-toast-message-text",
            "close_button": ".p-toast-icon-close",
        }
    )

    # ConfirmDialog component
    library.components["confirmdialog"] = Component(
        name="ConfirmDialog",
        selectors=[
            ".p-confirm-dialog",
            "[class*='p-confirm-dialog']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "message": ".p-confirm-dialog-message",
            "icon": ".p-confirm-dialog-icon",
            "accept": ".p-confirm-dialog-accept",
            "reject": ".p-confirm-dialog-reject",
        }
    )

    # Accordion component
    library.components["accordion"] = Component(
        name="Accordion",
        selectors=[
            ".p-accordion",
            "[class*='p-accordion']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "tab": ".p-accordion-tab",
            "header": ".p-accordion-header",
            "content": ".p-accordion-content",
            "toggle_icon": ".p-accordion-toggle-icon",
        }
    )

    # Panel component
    library.components["panel"] = Component(
        name="Panel",
        selectors=[
            ".p-panel",
            "[class*='p-panel']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "header": ".p-panel-header",
            "title": ".p-panel-title",
            "content": ".p-panel-content",
            "toggler": ".p-panel-toggler",
        }
    )

    # Card component
    library.components["card"] = Component(
        name="Card",
        selectors=[
            ".p-card",
            "[class*='p-card']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "header": ".p-card-header",
            "title": ".p-card-title",
            "subtitle": ".p-card-subtitle",
            "body": ".p-card-body",
            "content": ".p-card-content",
            "footer": ".p-card-footer",
        }
    )

    # Paginator component
    library.components["paginator"] = Component(
        name="Paginator",
        selectors=[
            ".p-paginator",
            "[class*='p-paginator']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "first": ".p-paginator-first",
            "prev": ".p-paginator-prev",
            "next": ".p-paginator-next",
            "last": ".p-paginator-last",
            "pages": ".p-paginator-pages",
            "page": ".p-paginator-page",
        }
    )

    # Slider component
    library.components["slider"] = Component(
        name="Slider",
        selectors=[
            ".p-slider",
            "[class*='p-slider']",
        ],
        attributes=["data-testid", "aria-valuemin", "aria-valuemax"],
        actions={
            "click": "click",
        },
        child_selectors={
            "handle": ".p-slider-handle",
            "range": ".p-slider-range",
        }
    )

    # AutoComplete component
    library.components["autocomplete"] = Component(
        name="AutoComplete",
        selectors=[
            ".p-autocomplete",
            "[class*='p-autocomplete']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "fill": "fill",
            "click": "click",
        },
        child_selectors={
            "input": ".p-autocomplete-input",
            "panel": ".p-autocomplete-panel",
            "item": ".p-autocomplete-item",
            "loader": ".p-autocomplete-loader",
        }
    )

    # Tree component
    library.components["tree"] = Component(
        name="Tree",
        selectors=[
            ".p-tree",
            "[class*='p-tree']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "container": ".p-tree-container",
            "node": ".p-treenode",
            "content": ".p-treenode-content",
            "label": ".p-treenode-label",
            "toggler": ".p-tree-toggler",
            "checkbox": ".p-checkbox",
        }
    )

    # FileUpload component
    library.components["fileupload"] = Component(
        name="FileUpload",
        selectors=[
            ".p-fileupload",
            "[class*='p-fileupload']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "buttonbar": ".p-fileupload-buttonbar",
            "content": ".p-fileupload-content",
            "choose": ".p-fileupload-choose",
            "upload": ".p-fileupload-upload",
            "cancel": ".p-fileupload-cancel",
            "files": ".p-fileupload-files",
        }
    )

    return library
