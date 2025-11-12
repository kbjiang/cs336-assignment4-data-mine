import re 

###########################################
# mask email

# Pattern:
# Length: The total length of an email address is capped at 320 characters, with 64 for the username and 255 for the domain.
# Spaces: Spaces are not allowed.
# Case sensitivity: Email addresses are generally not case-sensitive, meaning User@Example.com is the same as user@example.com.

# Special characters:
#   - Periods (.), hyphens (-), and underscores (_) are often allowed in the local part.
#   - They cannot be the first or last character of the local part and cannot appear consecutively (e.g., john..doe@example.com is invalid).
#   - In the domain, hyphens are allowed but not at the beginning or end of a label (a part between periods). 
def is_valid_username(username: str) -> bool:
    # 1. allowed special char: [._-]
    # 2. cannot start or end with special chars
    # 3. length cannot exceed 64
    username_pattern = re.compile(r'[a-zA-Z0-9]([._-]?[a-zA-Z0-9]){0,63}')
    return re.match(username_pattern, username)

def is_valid_domain(domain: str) -> bool:
    # Cannot exceed 255 characters
    if len(domain) > 255:
        return False

    # Split domain into labels
    labels = domain.split('.')
    if len(labels) < 2: # at least two labels
        return False

    # 1. allowed special char: -
    # 2. cannot start or end with special chars
    # 3. length cannot exceed 64
    label_pattern = re.compile(r'[a-zA-Z0-9](-?[a-zA-Z0-9]){0,63}')
    for label in labels:
        if not re.match(label_pattern, label):
            return False

    # Last label (TLD) should be at least 2 letters
    if len(labels[-1]) < 2 or not labels[-1].isalpha():
        return False

    return True

def is_valid_email(candidate: str) -> bool:
    # Quick checks before detailed validation
    if not candidate or len(candidate) > 320:
        return False
    
    if candidate.count('@') != 1:  # Must have exactly one "@"
        return False
    
    if candidate.count('.') < 1:  # Must have at least one "."
        return False

    username, domain = candidate.split("@")
    
    # Check for empty parts
    if not username or not domain:
        return False
    
    return is_valid_username(username) and is_valid_domain(domain)

def mask_email(text: str, mask_str: str = "|||EMAIL_ADDRESS|||") -> str:
    """Find potential email addresses in text and replace it with mask string"""
    result = []
    num_masked = 0
    last_end  = 0

    for match in re.finditer(r'\S+', text):
        # Add text between last match and current match (preserves spaces)
        result.append(text[last_end:match.start()])
        
        # Check if current match is email
        candidate = match.group()
        if is_valid_email(candidate):
            result.append(mask_str)
            num_masked += 1
        else:
            result.append(candidate)
        
        last_end = match.end()
    
    # Add any remaining text after last match
    result.append(text[last_end:])
    
    return ''.join(result), num_masked

###########################################
# mask US phone number

# pattern explanation:
# (\+1\s*)? - optional +1 followed by optional spaces
# \(? - optional opening parenthesis
# \d{3} - 3 digits
# \)? - optional closing parenthesis
# [\s-]? - at most one space or hyphen (the ? means zero or one)
# \s* - zero or more additional spaces
# \d{3} - 3 digits
# [\s-]? - at most one space or hyphen
# \s* - zero or more additional spaces
# \d{4} - 4 digits

# Why two patterns
# need the 1st `\b` to not partially match long digits like "1213141515517"
# however, country code `+1` do not like leading `\b`, for e.g. "\n+12259790721\n"

# Pattern 1: Phone numbers WITHOUT country code
# Use (?<!\d) instead of \b to allow matching after '(' or other non-digit characters
pattern_without_country_code = re.compile(r'(?<!\d)\(?\d{3}\)?[\s-]?\s*\d{3}[\s-]?\s*\d{4}\b')

# Pattern 2: Phone numbers WITH country code (+1)
pattern_with_country_code = re.compile(r'\+1\s*\(?\d{3}\)?[\s-]?\s*\d{3}[\s-]?\s*\d{4}\b')

def mask_phone(text: str, mask_str: str = "|||PHONE_NUMBER|||") -> str:
    """Mask phone numbers in text using two-pattern approach"""
    # First mask numbers with +1 (no leading boundary needed - + creates natural separation)
    text, count1 = re.subn(pattern_with_country_code, mask_str, text)
    # Then mask numbers without +1 (uses (?<!\d) to avoid matching in long digit sequences)
    text, count2 = re.subn(pattern_without_country_code, mask_str, text)
    return text, count1 + count2


def mask_phone(text: str, mask_str: str = "|||PHONE_NUMBER|||") -> str:
    # First mask numbers with +1
    text, count1 = re.subn(pattern_with_country_code, mask_str, text)
    # Then mask numbers without +1
    text, count2 = re.subn(pattern_without_country_code, mask_str, text)
    return text, count1 + count2
    
###########################################
# mask IPv4 address
# notice the usage of `\b`.
pattern_ip = re.compile(r'\b\d+\.\d+\.\d+\.\d+\b')

def mask_ip(text: str, mask_str: str = "|||IP_ADDRESS|||") -> str:
    text, n_sub = re.subn(pattern_ip, mask_str, text)
    return text, n_sub