import re 

# mask email
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