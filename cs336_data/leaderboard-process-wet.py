import os
import json
import logging
from tqdm import tqdm
from pathlib import Path
from fastwarc.warc import ArchiveIterator, WarcRecordType
from tldextract import TLDExtract
from resiliparse.parse.encoding import detect_encoding
import concurrent.futures

from cs336_data.language_identification import identify_language
from cs336_data.harmful_content import classify_nsfw, classify_toxic_speech
from cs336_data.gopher_quality_filter import gopher_quality_filter


def should_filter_url(url: str) -> bool:
    """
    Return True if URL should be filtered out (removed)
    """
    # Create the extractor instance
    extractor = TLDExtract()
    if not url:
        return True
    try:
        extracted = extractor(url)  # Use the class instance
        domain = extracted.domain.lower()
        suffix = extracted.suffix.lower()
        
        # based on exploration of paloma dataset
        # it has no intersection with `adult` and `social` domains
        allowed_tlds = {'com', 'org', 'edu', 'gov', 'net', 'uk', 'ca', 'au', 'us'}
        adult_domains = {
            'pornhub', 'xvideos', 'redtube', 'youporn', 'xhamster',
            'tube8', 'spankbang', 'chaturbate', 'cam4', 'livejasmin'
        }
        social_domains = {
            'facebook', 'twitter', 'instagram', 'tiktok', 'snapchat',
            'reddit', '4chan', '8chan', 'discord', 'telegram'
        }

        # 1. Filter by top-level domain (keep only certain TLDs)
        if suffix not in allowed_tlds:
            return True
        # 2. Filter out adult/inappropriate domains
        if domain in adult_domains:
            return True
        # 3. Filter out social media/forum content (often low quality)
        if domain in social_domains:
            return True
        return False
    except Exception:
        # Filter out URLs that can't be parsed
        return True

SCORE_LANG = 0.90
SCORE_NSFW = 0.90
SCORE_TOXIC = 0.90

def process_single_wet_file(input_path: str, output_path: str) -> str:
    """
    Process a single WET file with language, toxicity, and NSFW filtering.
    Returns summary statistics.
    """
    contents = []
    try:
        iterator = ArchiveIterator(open(input_path, "rb"))
        filtered_by_type = 0
        filtered_by_url = 0
        filtered_by_quality = 0
        filtered_by_lang = 0
        filtered_by_nsfw = 0
        filtered_by_toxic = 0
        # i = 0
        for record in iterator:
            # if i > 500: break
            # i += 1
            # 0. check record type
            if record.record_type != WarcRecordType.conversion:
                filtered_by_type += 1
                continue
            byte_string = record.reader.read()
            encoding = detect_encoding(byte_string)
            content = byte_string.decode(encoding, errors="ignore")

            # 1. check URL
            if should_filter_url(record.headers.get('WARC-Target-URI', '')):
                filtered_by_url += 1
                continue

            # 2. Identify language
            lang, score = identify_language(content)
            if lang != "en" or score < SCORE_LANG:
                filtered_by_lang += 1
                continue

            # 3. Quality check, rule-based
            if not gopher_quality_filter(content, min_word_cnt=50, max_word_cnt=2e5):
                filtered_by_quality += 1
                continue

            # 4. Classify NSFW
            nsfw, score = classify_nsfw(content)
            if (not nsfw.startswith("non-")) or score < SCORE_NSFW:
                filtered_by_nsfw += 1
                continue
            
            # 5. Classify Toxic
            toxic, score = classify_toxic_speech(content)
            if (not toxic.startswith("non-")) or score < SCORE_TOXIC:
                filtered_by_toxic += 1
                continue

            contents.append(content)

        filtered_dict = {
                "by_type": filtered_by_type,
                "by_url": filtered_by_url,
                "by_lang": filtered_by_lang,
                "by_quality": filtered_by_quality,
                "by_nsfw": filtered_by_nsfw,
                "by_toxic": filtered_by_toxic
            }
        # 1. Write filtered content to JSONL
        # `utf-8` for writing to JSON; this does not have to match with reading encoding.
        with open(output_path, 'w', encoding='utf-8') as f:
            for content in contents:
                json.dump({'text': content}, f)
                f.write('\n')    
        # 2. Write stats to separate JSON file
        stats_path = output_path.replace('.jsonl', '_stats.json')
        with open(stats_path, 'w') as f:
            json.dump(filtered_dict, f, indent=2)
        return output_path
    except Exception as e:
        logging.error(f"Error processing {input_path}: {e}")
        return None

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        filename='processing_errors.log',
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Set up the executor
    num_cpus = len(os.sched_getaffinity(0))
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=num_cpus)

    # Set up file paths
    input_directory_path = Path("/home/azureuser/mount/CC3")
    wet_filepaths = list(input_directory_path.glob("*.wet.gz"))
    output_directory_path = Path("/home/azureuser/mount/CC3-filtered")
    output_directory_path.mkdir(parents=True, exist_ok=True)

    futures = []

    for wet_filepath in wet_filepaths:
        # For each warc.wet.gz filepath, submit a job to the executor and get a future back
        output_filename = wet_filepath.name.replace(".warc.wet.gz", ".jsonl")
        output_filepath = output_directory_path / output_filename
        
        future = executor.submit(
            process_single_wet_file,
            str(wet_filepath),
            str(output_filepath)
        )
        # Store the futures
        futures.append(future)

    # Iterate over the completed futures as they finish, using a progress bar
    # to keep track of progress.
    for future in tqdm(
        concurrent.futures.as_completed(futures),
        total=len(wet_filepaths),
    ):
        output_file = future.result()