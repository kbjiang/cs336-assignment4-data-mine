import string
from os import PathLike
import unicodedata
import re
import mmh3
import random
import shutil

# `normalize_text`: punctuation removed, text lowercased, NFD unicode normalization applied, accents removed, whitespace is normalized.
# `minhashing` and `get_signature`: requires arguments `num_hashes`, `ngrams`.
# `get_candidates` and `get_clusters`: requires arguments `num_bands` and `jaccard_threshold`.
# `minhash_deduplication`: put all together

# see ``NFD` unicode normalization` in my note for this lecture
def strip_accents(text):
    return "".join(c for c in unicodedata.normalize("NFD", text)
                   if not unicodedata.combining(c))

def normalize_text(text: str) -> list[str]:
    """normalize text and split into a list of words"""
    # remove punctuation
    text = "".join([" " if t in string.punctuation else t for t in text])
    # lowercase
    text = text.lower()
    # NFD normalization and remove accents
    text = strip_accents(text)
    # `\s` matches any whitespace character (space, tab, newline, etc.).
    words = re.split(r"\s+", text)
    return words

def minhashing(doc_words: list[str], ngrams: int, seed: int) -> int:
    """each seed corresponds to one hash func"""
    minhash = float("inf")

    # no need to get set of ngrams because we are taking the min of hash values
    for i in range(len(doc_words) - ngrams): 
        ngram_str = " ".join(doc_words[i:i+ngrams])
        # Hashing a string to a 32-bit integer
        hash_32bit = mmh3.hash(ngram_str, seed)
        minhash = min(hash_32bit, minhash)
    return minhash

def get_signatures(input_files: list[str | PathLike], num_hashes: int, ngrams: int) -> list[list[int]]:
    """num_hashes minhashing of each doc"""
    signatures = []
    seeds = [random.randint(0, 2**32-1) for _ in range(num_hashes)]

    for file_path in input_files:
        with open(file_path) as f:
            doc = f.read()
        doc_words = normalize_text(doc)

        signature = [minhashing(doc_words, ngrams, seed) for seed in seeds]
        signatures.append(signature)
    return signatures

def get_candidates(signatures: list[list[int]], num_bands: int) -> list[tuple[int]]:
    sig_size = len(signatures[0])
    assert sig_size % num_bands == 0, "num of hashes need to be divisible by num of bands"
    row_size = sig_size // num_bands
    candidates = []
    for i in range(num_bands):
        sid = i * row_size
        eid = (i+1) * row_size
        for j in range(len(signatures)):
            for k in range(j+1, len(signatures)):
                if signatures[j][sid:eid] == signatures[k][sid:eid]:
                    # print(signatures[j][sid:eid])
                    # print(signatures[k][sid:eid])
                    candidates.append((j, k))

    return set(candidates)

def get_jaccard_similarity(doc_words_0: list[int], doc_words_1: list[int]) -> float:
    return len(set(doc_words_0).intersection(set(doc_words_1))) / len(set(doc_words_0).union(set(doc_words_1)))

def get_clusters(input_files: list[str | PathLike], candidates: list[tuple[int]], jaccard_threshold: float) -> list[list[int]]:
    # can be improved to aovid repeated loading and normalization
    clusters = []
    for fid_0, fid_1 in candidates:
        with open(input_files[fid_0]) as f:
            doc_0 = f.read()
            doc_words_0 = normalize_text(doc_0)
        with open(input_files[fid_1]) as f:
            doc_1 = f.read()
            doc_words_1 = normalize_text(doc_1)

        if get_jaccard_similarity(doc_words_0, doc_words_1) > jaccard_threshold:
            clusters.append((fid_0, fid_1))
    return clusters

def minhash_deduplication(input_files: list[str | PathLike], output_directory: str | PathLike, num_hashes: str, ngrams: str, num_bands: str, jaccard_threshold: float = 0.8):
    signatures = get_signatures(input_files, num_hashes, ngrams)
    candidates = get_candidates(signatures, num_bands)
    clusters = get_clusters(input_files, candidates, jaccard_threshold)

    # keep one in cluster
    retained_clusters = [random.choice(cluster) for cluster in clusters]
    # print(retained_clusters)

    # non candiates
    non_candidates = [i for i in range(len(input_files)) if i not in set([e for c in candidates for e in c])]
    # print(non_candidates)

    # copying
    output_directory.mkdir(parents=True, exist_ok=True)
    for i in sorted(retained_clusters + non_candidates):
        shutil.copy2(input_files[i], output_directory)