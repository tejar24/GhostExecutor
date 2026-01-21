def validate_feature(feature_text: str) -> None:
    """
    Raises ValueError if feature file is invalid.
    """

    if not feature_text.strip():
        raise ValueError("Feature file is empty")

    required_keywords = [
        "Feature:",
        "Scenario",
        "Given",
        "When",
        "Then"
    ]

    for keyword in required_keywords:
        if keyword not in feature_text:
            raise ValueError(f"Missing required keyword: {keyword}")

    # Enforce Given/When/Then order per scenario (basic sanity)
    lines = feature_text.splitlines()
    current_scenario = False
    seen_given = seen_when = seen_then = False

    for line in lines:
        line = line.strip()

        if line.startswith("Scenario"):
            current_scenario = True
            seen_given = seen_when = seen_then = False

        if current_scenario:
            if line.startswith("Given"):
                seen_given = True
            elif line.startswith("When") and seen_given:
                seen_when = True
            elif line.startswith("Then") and seen_when:
                seen_then = True

        if current_scenario and seen_given and seen_when and seen_then:
            current_scenario = False

    # If we exit mid-scenario, structure is broken
    if current_scenario:
        raise ValueError("Scenario does not contain valid Given/When/Then sequence")
