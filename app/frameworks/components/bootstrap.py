"""
Bootstrap Component Library Definition

Provides selectors and interaction patterns for Bootstrap 5+ components.
"""

from app.frameworks.registry import Component, ComponentLibrary


def get_library() -> ComponentLibrary:
    """Get the Bootstrap component library definition."""
    library = ComponentLibrary(
        name="bootstrap",
        base_framework="vanilla",
        prefix="bs"
    )

    # Button component
    library.components["button"] = Component(
        name="Button",
        selectors=[
            ".btn",
            "[class*='btn-']",
            "button.btn",
            "a.btn",
        ],
        attributes=["data-testid", "aria-label", "data-bs-toggle"],
        actions={
            "click": "click",
            "hover": "hover",
            "focus": "focus",
        },
        child_selectors={
            "spinner": ".spinner-border",
        }
    )

    # Input component
    library.components["input"] = Component(
        name="Input",
        selectors=[
            ".form-control",
            "input.form-control",
            "textarea.form-control",
        ],
        attributes=["data-testid", "aria-label", "placeholder", "name"],
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
            ".form-select",
            "select.form-select",
            "select.form-control",
        ],
        attributes=["data-testid", "aria-label", "name"],
        actions={
            "select": "select_option",
            "click": "click",
        },
        child_selectors={
            "option": "option",
        }
    )

    # Checkbox component
    library.components["checkbox"] = Component(
        name="Checkbox",
        selectors=[
            ".form-check-input[type='checkbox']",
            "input.form-check-input[type='checkbox']",
        ],
        attributes=["data-testid", "aria-label", "name"],
        actions={
            "check": "check",
            "uncheck": "uncheck",
            "click": "click",
        },
        child_selectors={
            "label": ".form-check-label",
        }
    )

    # Radio component
    library.components["radio"] = Component(
        name="Radio",
        selectors=[
            ".form-check-input[type='radio']",
            "input.form-check-input[type='radio']",
        ],
        attributes=["data-testid", "aria-label", "name", "value"],
        actions={
            "check": "check",
            "click": "click",
        },
        child_selectors={
            "label": ".form-check-label",
        }
    )

    # Switch component
    library.components["switch"] = Component(
        name="Switch",
        selectors=[
            ".form-switch .form-check-input",
            ".form-check.form-switch input",
        ],
        attributes=["data-testid", "aria-label", "role"],
        actions={
            "click": "click",
            "check": "check",
            "uncheck": "uncheck",
        },
        child_selectors={
            "label": ".form-check-label",
        }
    )

    # Modal component
    library.components["modal"] = Component(
        name="Modal",
        selectors=[
            ".modal",
            "[class*='modal']",
            ".modal.show",
        ],
        attributes=["data-testid", "aria-labelledby", "data-bs-backdrop"],
        actions={
            "close": "click",
        },
        child_selectors={
            "dialog": ".modal-dialog",
            "content": ".modal-content",
            "header": ".modal-header",
            "title": ".modal-title",
            "body": ".modal-body",
            "footer": ".modal-footer",
            "close_button": ".btn-close",
        }
    )

    # Dropdown component
    library.components["dropdown"] = Component(
        name="Dropdown",
        selectors=[
            ".dropdown",
            "[class*='dropdown']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "toggle": ".dropdown-toggle",
            "menu": ".dropdown-menu",
            "item": ".dropdown-item",
            "divider": ".dropdown-divider",
        }
    )

    # Navbar component
    library.components["navbar"] = Component(
        name="Navbar",
        selectors=[
            ".navbar",
            "[class*='navbar']",
            "nav.navbar",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
        },
        child_selectors={
            "brand": ".navbar-brand",
            "toggler": ".navbar-toggler",
            "collapse": ".navbar-collapse",
            "nav": ".navbar-nav",
            "item": ".nav-item",
            "link": ".nav-link",
        }
    )

    # Nav/Tabs component
    library.components["nav"] = Component(
        name="Nav",
        selectors=[
            ".nav",
            ".nav-tabs",
            ".nav-pills",
        ],
        attributes=["data-testid", "role"],
        actions={
            "click": "click",
        },
        child_selectors={
            "item": ".nav-item",
            "link": ".nav-link",
        }
    )

    # Card component
    library.components["card"] = Component(
        name="Card",
        selectors=[
            ".card",
            "[class*='card']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "header": ".card-header",
            "body": ".card-body",
            "title": ".card-title",
            "text": ".card-text",
            "footer": ".card-footer",
            "img": ".card-img-top",
        }
    )

    # Accordion component
    library.components["accordion"] = Component(
        name="Accordion",
        selectors=[
            ".accordion",
            "[class*='accordion']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "item": ".accordion-item",
            "header": ".accordion-header",
            "button": ".accordion-button",
            "collapse": ".accordion-collapse",
            "body": ".accordion-body",
        }
    )

    # Alert component
    library.components["alert"] = Component(
        name="Alert",
        selectors=[
            ".alert",
            "[class*='alert-']",
            "[role='alert']",
        ],
        attributes=["data-testid", "role"],
        actions={
            "close": "click",
        },
        child_selectors={
            "close_button": ".btn-close",
        }
    )

    # Badge component
    library.components["badge"] = Component(
        name="Badge",
        selectors=[
            ".badge",
            "[class*='badge']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={}
    )

    # Toast component
    library.components["toast"] = Component(
        name="Toast",
        selectors=[
            ".toast",
            "[class*='toast']",
            ".toast.show",
        ],
        attributes=["data-testid", "role", "aria-live"],
        actions={
            "close": "click",
        },
        child_selectors={
            "header": ".toast-header",
            "body": ".toast-body",
            "close_button": ".btn-close",
        }
    )

    # Table component
    library.components["table"] = Component(
        name="Table",
        selectors=[
            ".table",
            "table.table",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "scroll": "scroll_into_view",
        },
        child_selectors={
            "header": "thead",
            "body": "tbody",
            "row": "tr",
            "header_cell": "th",
            "cell": "td",
        }
    )

    # List Group component
    library.components["listgroup"] = Component(
        name="ListGroup",
        selectors=[
            ".list-group",
            "[class*='list-group']",
        ],
        attributes=["data-testid"],
        actions={
            "click": "click",
        },
        child_selectors={
            "item": ".list-group-item",
            "action": ".list-group-item-action",
        }
    )

    # Pagination component
    library.components["pagination"] = Component(
        name="Pagination",
        selectors=[
            ".pagination",
            "[class*='pagination']",
        ],
        attributes=["data-testid", "aria-label"],
        actions={
            "click": "click",
        },
        child_selectors={
            "item": ".page-item",
            "link": ".page-link",
            "prev": ".page-item:first-child",
            "next": ".page-item:last-child",
        }
    )

    # Progress component
    library.components["progress"] = Component(
        name="Progress",
        selectors=[
            ".progress",
            "[class*='progress']",
        ],
        attributes=["data-testid", "aria-valuenow", "aria-valuemin", "aria-valuemax"],
        actions={},
        child_selectors={
            "bar": ".progress-bar",
        }
    )

    # Spinner component
    library.components["spinner"] = Component(
        name="Spinner",
        selectors=[
            ".spinner-border",
            ".spinner-grow",
        ],
        attributes=["data-testid", "role"],
        actions={},
        child_selectors={}
    )

    # Offcanvas component
    library.components["offcanvas"] = Component(
        name="Offcanvas",
        selectors=[
            ".offcanvas",
            "[class*='offcanvas']",
            ".offcanvas.show",
        ],
        attributes=["data-testid", "aria-labelledby"],
        actions={
            "close": "click",
        },
        child_selectors={
            "header": ".offcanvas-header",
            "title": ".offcanvas-title",
            "body": ".offcanvas-body",
            "close_button": ".btn-close",
        }
    )

    # Form Group component
    library.components["formgroup"] = Component(
        name="FormGroup",
        selectors=[
            ".mb-3:has(.form-control)",
            ".form-group",
            ".form-floating",
        ],
        attributes=["data-testid"],
        actions={},
        child_selectors={
            "label": ".form-label",
            "input": ".form-control",
            "feedback": ".invalid-feedback, .valid-feedback",
            "text": ".form-text",
        }
    )

    # Input Group component
    library.components["inputgroup"] = Component(
        name="InputGroup",
        selectors=[
            ".input-group",
        ],
        attributes=["data-testid"],
        actions={},
        child_selectors={
            "input": ".form-control",
            "text": ".input-group-text",
            "button": ".btn",
        }
    )

    # Carousel component
    library.components["carousel"] = Component(
        name="Carousel",
        selectors=[
            ".carousel",
            "[class*='carousel']",
        ],
        attributes=["data-testid", "data-bs-ride"],
        actions={
            "click": "click",
        },
        child_selectors={
            "inner": ".carousel-inner",
            "item": ".carousel-item",
            "prev": ".carousel-control-prev",
            "next": ".carousel-control-next",
            "indicators": ".carousel-indicators",
        }
    )

    return library
