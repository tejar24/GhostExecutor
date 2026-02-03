"""
Automatic Test Data Generator

Generates context-aware test data for UI elements using Faker.
"""

import re
from typing import Any, Optional
from faker import Faker
from app.brain.ui_brain import ElementDescriptor

class DataGenerator:
    """
    Generates realistic test data based on element properties.
    """

    def __init__(self, locale: str = "en_US"):
        self.faker = Faker(locale)
        # Seed to ensure we get different values each run, 
        # but you could set a specific seed for reproducibility if needed.
        # self.faker.seed_instance(12345) 

    def generate_value(self, element: ElementDescriptor) -> str:
        """
        Generate a suitable value for the given element.
        """
        # 1. Check element subtype (e.g., input type="email")
        if element.element_subtype == "email":
            return self.faker.email()
        elif element.element_subtype == "tel" or element.element_subtype == "phone":
            return self.faker.phone_number()
        elif element.element_subtype == "url":
            return self.faker.url()
        elif element.element_subtype == "date":
            return self.faker.date()
        elif element.element_subtype == "password":
             return "Test@1234" # Return a standard password for testing predictability 
                                # or self.faker.password() if random is preferred.

        # 2. Check label/name/id for keywords
        label = (element.resolved_label or "").lower()
        name = (element.attributes.get("name") or "").lower()
        el_id = (element.attributes.get("id") or "").lower()
        
        context_str = f"{label} {name} {el_id}"

        if "email" in context_str:
            return self.faker.email()
        if "first" in context_str and "name" in context_str:
            return self.faker.first_name()
        if "last" in context_str and "name" in context_str:
            return self.faker.last_name()
        if "name" in context_str: # Generic name
            return self.faker.name()
        if "phone" in context_str or "mobile" in context_str:
            return self.faker.phone_number()
        if "address" in context_str:
            return self.faker.address().replace("\n", ", ")
        if "city" in context_str:
            return self.faker.city()
        if "zip" in context_str or "postal" in context_str:
            return self.faker.zipcode()
        if "company" in context_str:
            return self.faker.company()
        if "job" in context_str or "title" in context_str:
            return self.faker.job()
        if "desc" in context_str or "comment" in context_str or "message" in context_str:
            return self.faker.sentence()
        
        # 3. Fallback based on element type
        if element.element_type == "input":
             return self.faker.word()
        if element.element_subtype == "multiline": # textarea
             return self.faker.paragraph()

        return "Test Value"
