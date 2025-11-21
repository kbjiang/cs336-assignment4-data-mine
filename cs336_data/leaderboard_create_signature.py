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
        for line in f.readlines():
            doc = json.loads(line)['text']
            doc_words = normalize_text(doc)
            
            signature = [float("inf")] * len(seeds)
            for i in range(len(doc_words) - ngrams):
                ngram_str = " ".join(doc_words[i:i+ngrams])
                for j, seed in enumerate(seeds):
                    hash_val = mmh3.hash(ngram_str, seed)
                    signature[j] = min(signature[j], hash_val)
            
            signatures.append(signature)
    return file_idx, signatures

def get_signatures_parallel_incremental(
    input_files: list[str | PathLike], 
    num_hashes: int, 
    ngrams: int,
    output_file: str,
    checkpoint_interval: int = 100
) -> None:
    """Parallel processing with incremental saving"""
    seeds = [random.randint(0, 2**32-1) for _ in range(num_hashes)]
    n_workers = len(os.sched_getaffinity(0))
    
    output_path = Path(output_file)
    checkpoint_file = output_path.with_suffix('.checkpoint')
    metadata_file = output_path.with_suffix('.metadata.pkl')
    
    # Resume from checkpoint if exists
    start_idx = 0
    if checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            start_idx = int(f.read().strip())
        print(f"Resuming from file {start_idx}")
    else:
        # Save metadata on first run
        with open(metadata_file, 'wb') as meta_f:
            pickle.dump({
                'input_files': [str(f) for f in input_files],
                'num_hashes': num_hashes,
                'ngrams': ngrams,
                'seeds': seeds
            }, meta_f)
    
    # Open output file in append mode
    mode = 'ab' if start_idx > 0 else 'wb'
    
    with open(output_path, mode) as out_f:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            # Process in batches
            for batch_start in range(start_idx, len(input_files), checkpoint_interval):
                batch_end = min(batch_start + checkpoint_interval, len(input_files))
                batch = input_files[batch_start:batch_end]
                
                futures = {executor.submit(get_signatures_single_file, fp, batch_start + i, seeds, ngrams): batch_start + i
                           for i, fp in enumerate(batch)}
                
                # Collect results in order
                results = {}
                for future in tqdm(as_completed(futures), desc=f"Batch {batch_start}-{batch_end}", total=len(futures)):
                    file_idx, signatures = future.result()
                    results[file_idx] = signatures

                # TODO: better mapping between file path/line number with output signatures, this is important for clustering
                # Save in order
                for idx in sorted(results.keys()):
                    pickle.dump((idx, results[idx]), out_f)
                    out_f.flush()
                
                # Update checkpoint
                with open(checkpoint_file, 'w') as cf:
                    cf.write(str(batch_end))
    
    # Clean up checkpoint on completion
    checkpoint_file.unlink()
    print(f"Saved signatures to {output_path}")

if __name__ == "__main__":
    input_dir = Path("/home/azureuser/mount/CC-filtered-50")
    input_files = sorted(input_dir.glob("*.jsonl"))
    print(f"Total input files: {len(input_files)}.")
    # Usage
    get_signatures_parallel_incremental(
        input_files, 
        num_hashes=2400, 
        ngrams=5,
        output_file="signatures.pkl",
        checkpoint_interval=100
    )