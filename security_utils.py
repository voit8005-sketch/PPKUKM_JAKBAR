"""
Security utilities for password and email validation
"""
import re
from email_validator import validate_email, EmailNotValidError

# Password requirements
PASSWORD_MIN_LENGTH = 12
PASSWORD_REQUIRES_UPPERCASE = True
PASSWORD_REQUIRES_LOWERCASE = True
PASSWORD_REQUIRES_DIGIT = True
PASSWORD_REQUIRES_SPECIAL = True

SPECIAL_CHARACTERS = r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]'


def validate_email_address(email):
    """
    Validate email address format and structure
    Returns: (is_valid: bool, message: str)
    """
    try:
        # Validate email format - check_deliverability=False to allow local/test domains
        valid = validate_email(email, check_deliverability=False)
        email = valid.email
        return True, f"Email {email} valid ✓"
    except EmailNotValidError as e:
        return False, str(e)


def validate_password_strength(password):
    """
    Validate password strength with detailed feedback
    Returns: (is_valid: bool, feedback: dict)
    """
    feedback = {
        "strength": 0,  # 0-100
        "requirements": {
            "length": len(password) >= PASSWORD_MIN_LENGTH,
            "uppercase": bool(re.search(r'[A-Z]', password)),
            "lowercase": bool(re.search(r'[a-z]', password)),
            "digit": bool(re.search(r'[0-9]', password)),
            "special": bool(re.search(SPECIAL_CHARACTERS, password))
        },
        "messages": []
    }

    # Check minimum length
    if not feedback["requirements"]["length"]:
        feedback["messages"].append(f"Minimal {PASSWORD_MIN_LENGTH} karakter")
    else:
        feedback["strength"] += 20

    # Check uppercase
    if PASSWORD_REQUIRES_UPPERCASE and not feedback["requirements"]["uppercase"]:
        feedback["messages"].append("Minimal 1 huruf BESAR (A-Z)")
    elif feedback["requirements"]["uppercase"]:
        feedback["strength"] += 20

    # Check lowercase
    if PASSWORD_REQUIRES_LOWERCASE and not feedback["requirements"]["lowercase"]:
        feedback["messages"].append("Minimal 1 huruf kecil (a-z)")
    elif feedback["requirements"]["lowercase"]:
        feedback["strength"] += 20

    # Check digit
    if PASSWORD_REQUIRES_DIGIT and not feedback["requirements"]["digit"]:
        feedback["messages"].append("Minimal 1 angka (0-9)")
    elif feedback["requirements"]["digit"]:
        feedback["strength"] += 20

    # Check special characters
    if PASSWORD_REQUIRES_SPECIAL and not feedback["requirements"]["special"]:
        feedback["messages"].append("Minimal 1 simbol unik (!@#$%^&*...)")
    elif feedback["requirements"]["special"]:
        feedback["strength"] += 20

    # Determine strength level
    if feedback["strength"] >= 100:
        feedback["level"] = "Sangat Kuat"
        feedback["color"] = "green"
    elif feedback["strength"] >= 80:
        feedback["level"] = "Kuat"
        feedback["color"] = "blue"
    elif feedback["strength"] >= 60:
        feedback["level"] = "Sedang"
        feedback["color"] = "yellow"
    elif feedback["strength"] >= 40:
        feedback["level"] = "Lemah"
        feedback["color"] = "orange"
    else:
        feedback["level"] = "Sangat Lemah"
        feedback["color"] = "red"

    # Check if password is valid
    is_valid = (
        feedback["requirements"]["length"] and
        feedback["requirements"]["uppercase"] and
        feedback["requirements"]["lowercase"] and
        feedback["requirements"]["digit"] and
        feedback["requirements"]["special"]
    )

    return is_valid, feedback


def check_password_requirements(password):
    """
    Check if password meets all requirements
    Returns: (is_valid: bool, missing_requirements: list)
    """
    is_valid, feedback = validate_password_strength(password)
    return is_valid, feedback["messages"]
