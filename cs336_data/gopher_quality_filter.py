import nltk
import re

def valid_words(text, min_word_cnt, max_word_cnt):
    # num of words requirement
    words = nltk.word_tokenize(text)
    if len(words) < min_word_cnt or len(words) > max_word_cnt:
        return False

    # word length requirement
    word_lens = [len(word) for word in words]
    mean_len = sum(word_lens)/len(words)
    if mean_len < 3.0 or mean_len > 10.0:
        return False

    # at least one alphabetic character
    n_valid_words = sum(1 for word in words if re.search(r'[a-zA-Z]', word))
    if n_valid_words / len(words) < 0.8:
        return False

    return True

def valid_lines(text):
    lines = re.split(r"\n+", text)    
    n_valid_lines = sum(1 for line in lines if not line.endswith("..."))
    if n_valid_lines / len(lines) > 0.7:
        return True
    return False

def gopher_quality_filter(text, min_word_cnt=50, max_word_cnt=1e5):
    return valid_words(text, min_word_cnt, max_word_cnt) and valid_lines(text)