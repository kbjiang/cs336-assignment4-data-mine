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
