# Email Regex Pattern Building

## Local/Username Part

### Basic Vocabulary
The allowed characters in the local part (username before @):
- Alphanumeric: `[a-zA-Z0-9]`
- Special characters: `.` `-` `_`
- Combined: `[a-zA-Z0-9._-]`

**Note on raw strings (`r` prefix):**
- `r''` makes it a raw string in Python
- Treats backslashes `\` as literal characters instead of escape sequences
- Example: `'\n'` = newline, `r'\n'` = literal backslash + 'n'
- Good practice for regex patterns, especially when using `\d`, `\.`, etc.
- Not strictly necessary for `[a-zA-Z0-9._-]` but recommended

### Rules for Local Part
1. Special characters (`._-`) cannot be first or last character
2. Special characters cannot appear consecutively (e.g., `john..doe` is invalid)
3. Username cannot exceed 64 characters

### Pattern Development

**Step 1: Prevent special chars at start/end and consecutive:**
```python
r'[a-zA-Z0-9]([._-]?[a-zA-Z0-9])*'
```

Breaking it down:
- `[a-zA-Z0-9]` - Must start with alphanumeric
- `([._-]?[a-zA-Z0-9])*` - Optionally repeat: special char + alphanumeric
  - `[._-]?` - Optional special character (the `?` means zero or one)
  - `[a-zA-Z0-9]` - Must be followed by alphanumeric
  - `()*` - The `*` makes entire group repeat zero or more times

**Why this works:**
- Always starts/ends with alphanumeric
- Special chars can only appear between alphanumerics
- The `?` makes special chars optional, preventing consecutive ones

**Step 2: Add length constraint (max 64 chars):**
```python
r'[a-zA-Z0-9]([._-]?[a-zA-Z0-9]){0,63}'
```

- `{0,63}` limits the repeated part to 63 occurrences
- Total: 1 (first char) + 63 (repeated) = 64 characters max
- Changed `*` to `{0,63}` to enforce limit

### Regex Quantifiers Reference
- `*` = zero or more times
- `+` = one or more times
- `?` = zero or one time (optional)
- `{n}` = exactly n times
- `{n,}` = n or more times
- `{n,m}` = between n and m times

### Regex Anchors
**Anchors** match positions in the string, not characters:
- `^` = start of string anchor
- `$` = end of string anchor

**Why use anchors:**
Together, `^...$` ensures the pattern matches the **entire string** from start to finish, not just a substring.

**Examples:**
- Without anchors: `[a-zA-Z0-9]+` matches `"abc"` in `"abc@#$"` (partial match)
- With anchors: `^[a-zA-Z0-9]+$` only matches if the **whole string** is alphanumeric (fails on `"abc@#$"`)

**Usage in email validation:**
```python
local_pattern = r'^[a-zA-Z0-9]([._-]?[a-zA-Z0-9])*$'
```
This ensures the entire local part follows the rules, not just a portion of it.

### Caret (^) Symbol: Two Different Meanings

The `^` symbol has **two different meanings** in regex depending on context:

**1. Outside character class `[]` - Anchor (Start of String):**
```python
r'^hello'  # Matches "hello" only at the START of a string
```
- `^` matches a position (start of string), not a character
- Example: `re.match(r'^hello', 'hello world')` matches, but `re.match(r'^hello', 'say hello')` doesn't

**2. Inside character class `[]` - Negation (NOT):**
```python
r'[^a-z]'  # Matches any character that is NOT a lowercase letter
```
- `^` at the start of `[]` means "match anything NOT in this set"
- Example: `re.sub(r'[^a-zA-Z0-9]', '', 'Hello123!')` removes `!` (keeps only letters and digits)

**Common Pattern - Negated Character Class:**
```python
r'[^a-zA-Z0-9+ ]+'  # Match one or more characters that are NOT alphanumeric, plus, or space
```
- Used with `re.sub()` to remove or replace unwanted characters
- Example: `re.sub(r'[^a-zA-Z0-9+ ]+', ' ', '(283)-182-3829')` → `'283 182 3829'`

**Key Takeaway:**
- `^pattern` = anchor, matches at start of string
- `[^chars]` = negation, matches anything NOT in the character class

### Character Classes and Shorthand
**Shorthand character classes:**
- `\s` = whitespace characters (space, tab, newline, etc.)
- `\S` = non-whitespace characters (opposite of `\s`)
- `\d` = digits `[0-9]`
- `\D` = non-digits
- `\w` = word characters `[a-zA-Z0-9_]`
- `\W` = non-word characters

**Finding tokens in text:**
```python
r'\S+'
```
- `\S` = any non-whitespace character
- `+` = one or more times
- Matches sequences of non-whitespace characters (words, punctuation, email addresses, etc.)
- Useful for splitting text into tokens separated by whitespace

**Example:**
```python
text = "Contact me at test@gmail.com for help."
matches = re.finditer(r'\S+', text)
# Finds: ["Contact", "me", "at", "test@gmail.com", "for", "help."]
```

### Final Local Part Pattern
```python
email_address_pattern_username = re.compile(r'[a-zA-Z0-9]([._-]?[a-zA-Z0-9]){0,63}')
```

## Domain Part

### Domain Labels
A domain consists of labels separated by periods (e.g., `mail.google.com` has labels: `mail`, `google`, `com`).

### Basic Vocabulary
The allowed characters in domain labels:
- Alphanumeric: `[a-zA-Z0-9]`
- Hyphen: `-` (but not at start or end of a label)

### Rules for Domain Labels
1. Hyphens are allowed but NOT at the beginning or end of a label
2. Consecutive hyphens ARE allowed (unlike the local part)
3. Domain cannot exceed 255 characters

### Pattern Development

**Single Label Pattern:**
```python
r'[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?'
```

Breaking it down:
- `[a-zA-Z0-9]` - Must start with alphanumeric
- `([a-zA-Z0-9-]*[a-zA-Z0-9])?` - Optional middle and end part
  - `[a-zA-Z0-9-]*` - Zero or more alphanumeric OR hyphens (allows consecutive hyphens like `ex--ample`)
  - `[a-zA-Z0-9]` - Must end with alphanumeric
  - `()?` - Entire group is optional (allows single-char labels like `a.com`)

**Why this works:**
- Always starts and ends with alphanumeric
- Middle can have any mix of alphanumeric and hyphens, including consecutive hyphens
- Different from username pattern: uses `*` instead of `?` after hyphen to allow consecutives

**Key Difference from Local Part:**
- Local part: `([._-]?[a-zA-Z0-9])*` - `?` prevents consecutive special chars
- Domain label: `([a-zA-Z0-9-]*[a-zA-Z0-9])?` - `*` allows consecutive hyphens

### Final Domain Label Pattern
```python
email_address_pattern_label = re.compile(r'[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?')
```

## US Phone Number Masking

### Grouping vs Character Classes

**`()` - Grouping (Capturing Group):**
- Creates a **group** that can be referenced later
- Captures the matched content for later use
- Treats the content inside as a single unit for quantifiers

```python
r'(abc)+'  # Matches "abc", "abcabc", "abcabcabc" (repeats entire group)
r'(\d{3})-(\d{4})'  # Captures area code and number separately
```

**`[]` - Character Class:**
- Matches **one character** from a set of characters
- Each character inside is an option, not a sequence

```python
r'[abc]+'  # Matches "a", "b", "c", "ab", "cba", "aaa" (any combination)
r'[0-9]'   # Matches any single digit
r'[a-zA-Z]'  # Matches any single letter
```

**Key differences:**

| Feature | `()` | `[]` |
|---------|------|------|
| Matches | Sequence of characters | Single character from set |
| Example | `(abc)` matches "abc" | `[abc]` matches "a" OR "b" OR "c" |
| Quantifier | `(abc)+` = "abcabc" | `[abc]+` = "aabbcc" |
| Captures | Yes (can reference later) | No |

**Example:**
```python
r'(ab)+'     # "ab", "abab", "ababab"
r'[ab]+'     # "a", "b", "aa", "ab", "ba", "abb", "baa"
r'(ab){2}'   # "abab" (exactly twice)
r'[ab]{2}'   # "aa", "ab", "ba", "bb" (any two)
```

### Phone Number Pattern Development

**US phone numbers** can appear in various formats:
- `2831823829` (10 digits)
- `(283)-182-3829` (with parentheses and hyphens)
- `(283) 182 3829` (with parentheses and spaces)
- `283-182-3829` (with hyphens)
- `+1-283-182-3829` (with country code)

**Requirements:**
- Optional `+1` country code at the start
- 3-digit area code (optionally in parentheses)
- 3-digit exchange code
- 4-digit subscriber number
- Separators: at most one `-` or `)` between groups, but multiple spaces allowed

### Pattern: `r'(\+1\s*)?\(?\d{3}\)?[\s-]?\s*\d{3}[\s-]?\s*\d{4}'`

Breaking it down:

**`(\+1\s*)?`** - Optional country code group
- `\+` - Literal `+` sign (escaped because `+` is a special regex character)
- `1` - Literal digit `1`
- `\s*` - Zero or more whitespace characters after `+1`
- `()?` - The entire group is optional (the `?` makes the group optional)

**`\(?`** - Optional opening parenthesis
- `\(` - Literal `(` character (escaped)
- `?` - Zero or one (optional)

**`\d{3}`** - Exactly 3 digits (area code)

**`\)?`** - Optional closing parenthesis
- `\)` - Literal `)` character (escaped)
- `?` - Zero or one (optional)

**`[\s-]?`** - At most one separator
- `[\s-]` - Character class: either a space `\s` OR a hyphen `-`
- `?` - Zero or one (at most one separator)

**`\s*`** - Additional spaces allowed
- `\s` - Whitespace
- `*` - Zero or more times

**`\d{3}`** - Exactly 3 digits (exchange code)

**`[\s-]?`** - At most one separator (same as above)

**`\s*`** - Additional spaces allowed (same as above)

**`\d{4}`** - Exactly 4 digits (subscriber number)

**What this pattern matches:**
- `2831823829` ✓ (no separators)
- `(283)-182-3829` ✓ (parentheses and hyphens)
- `(283) 182 3829` ✓ (parentheses and spaces)
- `283-182-3829` ✓ (hyphens only)
- `+1-283-182-3829` ✓ (with country code)
- `283  182   3829` ✓ (multiple spaces)
- `(283)--182-3829` ✗ (two hyphens - violates "at most one" rule)

**Key insight:** The pattern `[\s-]?\s*` allows:
- Zero separators (matches directly)
- One hyphen or one space (from `[\s-]?`)
- Multiple spaces (from `\s*`)

But prevents multiple hyphens or multiple `)` characters, which would be invalid phone number formats.

### Final Phone Number Pattern
```python
phone_pattern = re.compile(r'(\+1\s*)?\(?\d{3}\)?[\s-]?\s*\d{3}[\s-]?\s*\d{4}')

def mask_phone(text: str, mask_str: str = "|||PHONE_NUMBER|||") -> str:
    return re.sub(phone_pattern, mask_str, text)
```

## IP Address Masking

### Word Boundaries (`\b`)

**Word boundaries** (`\b`) match positions between word characters `[a-zA-Z0-9_]` and non-word characters, or at the start/end of a string.

**When to use `\b`:**

1. **Matching whole numbers** (not parts of larger numbers):
```python
r'\b123\b'  # Matches "123" but not "1234" or "5123"
```

2. **Matching complete IP addresses** (not version numbers or partial matches):
```python
r'\b\d+\.\d+\.\d+\.\d+\b'  
# Matches "192.168.1.1" 
# But NOT "1.2.3.4.5" (5 octets) or "version1.2.3.4"
```

3. **Matching whole words**:
```python
r'\bcat\b'  # Matches "cat" but not "category" or "scat"
```

**When NOT to use `\b`:**

1. **When matching within words or allowing adjacent special characters**:
```python
r'@\w+'  # Match @username (no \b needed, @ isn't a word character)
```

2. **When you want partial matches**:
```python
r'test'  # Matches "test" in "testing", "contest", "test"
```

3. **When pattern already has specific delimiters**:
```python
r'\(\d{3}\)'  # Parentheses already act as boundaries
```

**What counts as a word boundary:**
- Between word character `[a-zA-Z0-9_]` and non-word character
- Examples: space, punctuation, start/end of string

**Examples:**
```python
# WITH \b
re.findall(r'\b\d+\b', 'Room 123 costs $456')  # ['123', '456']
re.findall(r'\btest\b', 'test testing')  # ['test']

# WITHOUT \b  
re.findall(r'\d+', 'Room 123 costs $456')  # ['123', '456'] (same here)
re.findall(r'test', 'test testing')  # ['test', 'test'] (matches both)
```

### IP Address Pattern Development

**IPv4 addresses** consist of four octets (0-255) separated by periods:
- `192.168.1.1`
- `10.0.0.255`
- `172.16.254.1`

**Simple Pattern: Match any `number.number.number.number` format**

```python
r'\b\d+\.\d+\.\d+\.\d+\b'
```

Breaking it down:
- `\b` - Word boundary (ensures we match whole IP addresses)
- `\d+` - One or more digits
- `\.` - Literal period (escaped because `.` is a special regex character meaning "any character")
- `\d+` - One or more digits
- `\.` - Literal period
- `\d+` - One or more digits
- `\.` - Literal period
- `\d+` - One or more digits
- `\b` - Word boundary

**Why use `\b` for IP addresses:**

Without `\b`, the pattern might match:
- `1.2.3.4.5` (5 octets - would match `1.2.3.4` or `2.3.4.5`)
- `version1.2.3.4` (prefix attached)
- `1.2.3.4th` (suffix attached)

With `\b`, we ensure:
- The IP address is a complete standalone pattern
- No digits directly before or after
- Proper separation from surrounding text

**Example:**
```python
pattern = re.compile(r'\b\d+\.\d+\.\d+\.\d+\b')

# Test 1: Standard case
text_1 = "Server IPs: 192.168.1.1 and 10.0.0.255, but not version1.2.3.4"
matches = pattern.findall(text_1)
# Returns: ['192.168.1.1', '10.0.0.255']
# Does NOT match 'version1.2.3.4' due to word boundary before the first digit

# Test 2: IP with letter suffix
text_2 = "Server IPs: 192.168.1.1 and 10.0.0.255s, but not version1.2.3.4"
matches = pattern.findall(text_2)
# Returns: ['192.168.1.1'] only
# Does NOT match '10.0.0.255s' because 's' is a word character (no boundary after '5')
# Does NOT match 'version1.2.3.4' (no boundary before '1')
```

**Validation:**

This simple pattern matches any four numbers separated by periods. To ensure each octet is 0-255 (valid IPv4), you can:

1. **Use complex regex** (matches only valid ranges):
```python
r'\b(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\b'
```

2. **Use simple pattern + Python validation** (recommended for readability):
```python
def is_valid_ip(text: str) -> bool:
    try:
        return all(0 <= int(x) <= 255 for x in text.split("."))
    except:
        return False
```

### Final IP Address Pattern
```python
ip_pattern = re.compile(r'\b\d+\.\d+\.\d+\.\d+\b')

def is_valid_ip(text: str) -> bool:
    """Validate that each octet is 0-255"""
    try:
        return all(0 <= int(x) <= 255 for x in text.split("."))
    except:
        return False

def mask_ip(text: str, mask_str: str = "|||IP_ADDRESS|||") -> str:
    """Find valid IP addresses in text and replace with mask string"""
    def replace_if_valid(match):
        ip = match.group()
        return mask_str if is_valid_ip(ip) else ip
    
    return re.sub(ip_pattern, replace_if_valid, text)
```

**Example usage:**
```python
text = "Server at 192.168.1.1 or contact 999.999.999.999"
result = mask_ip(text)
# Result: "Server at |||IP_ADDRESS||| or contact 999.999.999.999"
# (999.999.999.999 not masked because octets exceed 255)
```
