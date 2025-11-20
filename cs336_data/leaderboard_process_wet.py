import os
import json
import logging
from tqdm import tqdm
from pathlib import Path
from fastwarc.warc import ArchiveIterator, WarcRecordType
from tldextract import TLDExtract
from resiliparse.parse.encoding import detect_encoding
import concurrent.futures
import fasttext
from cs336_data.gopher_quality_filter import gopher_quality_filter

SCORE_LANG = 0.90
SCORE_NSFW = 0.90
SCORE_TOXIC = 0.90
BATCH_SIZE = 64

model_lang = fasttext.load_model("/home/azureuser/localfiles/cs336-assignment4-data-mine/cs336_data/lid.176.bin")
model_nsfw = fasttext.load_model("/home/azureuser/localfiles/cs336-assignment4-data-mine/cs336_data/jigsaw_fasttext_bigrams_nsfw_final.bin")
model_toxic = fasttext.load_model("/home/azureuser/localfiles/cs336-assignment4-data-mine/cs336_data/jigsaw_fasttext_bigrams_hatespeech_final.bin")


TLD_EXTRACTOR = TLDExtract()
def should_filter_url(url: str) -> bool:
    """
    Return True if URL should be filtered out (removed)
    """
    # Create the extractor instance
    if not url:
        return True
    try:
        extracted = TLD_EXTRACTOR(url)  # Use the class instance
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

def filter_batch(
        batch, model_lang, model_nsfw, model_toxic,
        score_lang, score_nsfw, score_toxic,
        filtered_by_lang, filtered_by_quality, filtered_by_nsfw, filtered_by_toxic,
):
    # major speed up comes from doing language identification on batch of records
    batch_nsfw = []
    batch_toxic = []
    batch_kept = []

    texts = [text.replace("\n", " ") for text in batch]
    preds = model_lang.predict(texts)
    preds = list(zip(*preds))
    for i, (pred, score) in enumerate(preds):
        pred = pred[0].replace("__label__", "")
        if pred == "en" and score.item() > score_lang:
            if gopher_quality_filter(batch[i], min_word_cnt=50, max_word_cnt=2e5):
                batch_nsfw.append(batch[i])
            else:
                filtered_by_quality += 1
                continue
        else:
            filtered_by_lang += 1

    if batch_nsfw: 
        texts = [text.replace("\n", " ") for text in batch_nsfw]
        preds = model_nsfw.predict(texts)
        preds = list(zip(*preds))
        for i, (pred, score) in enumerate(preds):
            pred = pred[0].replace("__label__", "")
            if pred.startswith("non-") and score.item() > score_nsfw:
                batch_toxic.append(batch_nsfw[i])
            else:
                filtered_by_nsfw += 1

    if batch_toxic: 
        texts = [text.replace("\n", " ") for text in batch_toxic]
        preds = model_toxic.predict(texts)
        preds = list(zip(*preds))
        for i, (pred, score) in enumerate(preds):
            pred = pred[0].replace("__label__", "")
            if pred.startswith("non-") and score.item() > score_toxic:
                batch_kept.append(batch_toxic[i])
            else:
                filtered_by_toxic += 1

    return batch_kept, filtered_by_lang, filtered_by_quality, filtered_by_nsfw, filtered_by_toxic

def process_single_wet_file(input_path: str, output_path: str) -> str:
    """
    Process a single WET file with language, toxicity, and NSFW filtering.
    Returns summary statistics.
    
    Speed up effort (see leaderboard.ipynb for more detail):
    1. Doing language identification on batch of records
    2. Write to output file incrementally to release memory
    """
    filtered_by_type = 0
    filtered_by_url = 0
    filtered_by_quality = 0
    filtered_by_lang = 0
    filtered_by_nsfw = 0
    filtered_by_toxic = 0
    try:
        # Write filtered content to JSONL
        # `utf-8` for writing to JSON; this does not have to match with reading encoding.
        with open(output_path, 'w', encoding='utf-8') as f:
            iterator = ArchiveIterator(open(input_path, "rb"))
            batch = []
            for record in iterator:
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

                batch.append(content)
                # 2. Apply filters
                if len(batch) >= BATCH_SIZE:
                    batch_kept, filtered_by_lang, filtered_by_quality, filtered_by_nsfw, filtered_by_toxic = filter_batch(
                        batch, model_lang, model_nsfw, model_toxic, 
                        SCORE_LANG, SCORE_NSFW, SCORE_TOXIC,
                        filtered_by_lang, filtered_by_quality, filtered_by_nsfw, filtered_by_toxic
                    )
                    if batch_kept:
                        for content in batch_kept:
                            json.dump({'text': content}, f)
                            f.write('\n')    
                    batch = []

            # do once for remainder
            if batch:
                batch_kept, filtered_by_lang, filtered_by_quality, filtered_by_nsfw, filtered_by_toxic = filter_batch(
                    batch, model_lang, model_nsfw, model_toxic, 
                    SCORE_LANG, SCORE_NSFW, SCORE_TOXIC,
                    filtered_by_lang, filtered_by_quality, filtered_by_nsfw, filtered_by_toxic
                )
                if batch_kept:
                    for content in batch_kept:
                        json.dump({'text': content}, f)
                        f.write('\n')    

            filtered_dict = {
                    "by_type": filtered_by_type,
                    "by_url": filtered_by_url,
                    "by_lang": filtered_by_lang,
                    "by_quality": filtered_by_quality,
                    "by_nsfw": filtered_by_nsfw,
                    "by_toxic": filtered_by_toxic
                }
            # Write stats to separate JSON file
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
        filename='leaderboard_process_wet.log',
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Set up the executor
    num_cpus = len(os.sched_getaffinity(0))
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=num_cpus)

    # Set up file paths
    input_directory_path = Path("/home/azureuser/mount/CC")
    wet_filepaths = list(input_directory_path.glob("*.wet.gz"))
    output_directory_path = Path("/home/azureuser/mount/CC-filtered")
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