from cs336_data.minhash_dedpulication import normalize_text
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
from os import PathLike
import random
import json
import mmh3
from tqdm import tqdm
import pickle
from pathlib import Path

def get_signatures_single_file(file_path, file_idx, seeds, ngrams):
    """Process a single file's signatures"""
    signatures = []
    with open(file_path) as f:
        for line_id, line in enumerate(f.readlines()):
            doc = json.loads(line)['text']
            doc_words = normalize_text(doc)
            
            signature = [float("inf")] * len(seeds)
            for i in range(len(doc_words) - ngrams):
                ngram_str = " ".join(doc_words[i:i+ngrams])
                for j, seed in enumerate(seeds):
                    hash_val = mmh3.hash(ngram_str, seed)
                    signature[j] = min(signature[j], hash_val)
            
            signatures.append({
                'jsonl_file': Path(file_path).name,
                'line_id': line_id,
                'signatures': signature
            })
    return file_idx, signatures

def get_signatures_parallel_incremental(
    input_files: list[str | PathLike], 
    num_hashes: int, 
    ngrams: int,
    output_dir: str,
    batch_size: int = 100
) -> None:
    """Parallel processing with batch-wise saving"""
    seeds = [random.randint(0, 2**32-1) for _ in range(num_hashes)]
    n_workers = len(os.sched_getaffinity(0))

    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        # Process in batches
        for batch_start in range(0, len(input_files), batch_size):
            batch_end = min(batch_start + batch_size, len(input_files))
            batch = input_files[batch_start:batch_end]
            
            # Check if this batch file already exists
            batch_output_file = Path(output_dir) / f"signatures_batch_{batch_start:04d}.pkl"
            if batch_output_file.exists():
                print(f"Skipping batch {batch_start}-{batch_end}, file already exists")
                continue
            
            futures = {executor.submit(get_signatures_single_file, fp, batch_start + i, seeds, ngrams): batch_start + i
                       for i, fp in enumerate(batch)}
            
            # Collect results in order
            results = {}
            for future in tqdm(as_completed(futures), desc=f"Batch {batch_start}-{batch_end}", total=len(futures)):
                file_idx, signatures = future.result()
                results[file_idx] = signatures

            # Save batch to separate file
            with open(batch_output_file, 'wb') as batch_f:
                for idx in sorted(results.keys()):
                    # results[idx] is a list of dicts, save each document's metadata
                    for doc_data in results[idx]:
                        pickle.dump(doc_data, batch_f)
            
            print(f"Saved batch {batch_start}-{batch_end} to {batch_output_file}")

if __name__ == "__main__":
    input_dir = Path("/home/azureuser/mount/CC-filtered")
    input_files = sorted(input_dir.glob("*.jsonl"))
    print(f"Total input files: {len(input_files)}.")
    # Usage
    get_signatures_parallel_incremental(
        input_files, 
        num_hashes=2400, 
        ngrams=5,
        output_dir="/home/azureuser/mount/",
        batch_size=512
    )