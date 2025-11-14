from __future__ import annotations

import os
from typing import Any



def run_extract_text_from_html_bytes(html_bytes: bytes) -> str | None:
    # raise NotImplementedError
    from cs336_data.extract_text import extract_text
    return extract_text(html_bytes)


def run_identify_language(text: str) -> tuple[Any, float]:
    # raise NotImplementedError
    from cs336_data.language_identification import identify_language
    return identify_language(text)


def run_mask_emails(text: str) -> tuple[str, int]:
    # raise NotImplementedError
    from cs336_data.mask_pii import mask_email
    return mask_email(text)


def run_mask_phone_numbers(text: str) -> tuple[str, int]:
    # raise NotImplementedError
    from cs336_data.mask_pii import mask_phone
    return mask_phone(text)


def run_mask_ips(text: str) -> tuple[str, int]:
    # raise NotImplementedError
    from cs336_data.mask_pii import mask_ip
    return mask_ip(text)


def run_classify_nsfw(text: str) -> tuple[Any, float]:
    # raise NotImplementedError
    from cs336_data.harmful_content import classify_nsfw
    return classify_nsfw(text)


def run_classify_toxic_speech(text: str) -> tuple[Any, float]:
    # raise NotImplementedError
    from cs336_data.harmful_content import classify_toxic_speech
    return classify_toxic_speech(text)


def run_classify_quality(text: str) -> tuple[Any, float]:
    raise NotImplementedError


def run_gopher_quality_filter(text: str) -> bool:
    # raise NotImplementedError
    from cs336_data.gopher_quality_filter import gopher_quality_filter
    return gopher_quality_filter(text)


def run_exact_line_deduplication(
    input_files: list[os.PathLike], output_directory: os.PathLike
):
    # raise NotImplementedError
    from cs336_data.exact_deduplication import exact_line_deduplication
    return exact_line_deduplication(input_files, output_directory)


def run_minhash_deduplication(
    input_files: list[os.PathLike],
    num_hashes: int,
    num_bands: int,
    ngrams: int,
    jaccard_threshold: float,
    output_directory: os.PathLike,
):
    raise NotImplementedError
