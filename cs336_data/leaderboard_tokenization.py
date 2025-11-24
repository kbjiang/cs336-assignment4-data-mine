import multiprocessing
import numpy as np
from tqdm import tqdm
from transformers import AutoTokenizer
import pickle
import random
import json
from pathlib import Path
import pandas as pd

INPUT_DIR = Path("/home/azureuser/mount/CC-filtered")
OUTPUT_DIR = Path("/home/azureuser/mount")

tokenizer = AutoTokenizer.from_pretrained("gpt2")

def tokenize_line_and_add_eos(line):
    return tokenizer.encode(line) + [tokenizer.eos_token_id]

def tokenize_incremental(input_file_dict, output_file, batch_size):
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    files_list = list(input_file_dict.items())
    
    for batch_start in range(0, len(files_list), batch_size):
        batch_end = min(batch_start + batch_size, len(files_list))
        batch_files = files_list[batch_start:batch_end]
        
        print(f"Processing files {batch_start}-{batch_end}")
        
        # Load lines from all files in batch
        all_lines = []
        for file, line_ids in batch_files:
            with open(INPUT_DIR/file) as f:
                file_lines = f.readlines()
                texts = [json.loads(file_lines[i])["text"] for i in line_ids]
                all_lines.extend(texts)
        
        # Tokenize batch
        results = []
        for result in tqdm(
            pool.imap(tokenize_line_and_add_eos, all_lines, chunksize=100),
            total=len(all_lines),
            desc=f"Tokenizing batch {batch_start//batch_size + 1}"
        ):
            results.append(result)
        
        # Flatten and save incrementally
        all_ids = [token_id for sublist in results for token_id in sublist]
        ids_array = np.array(all_ids, dtype=np.uint16)
        
        # Append to file
        with open(output_file, 'ab') as f:
            ids_array.tofile(f)
        
        print(f"Saved batch {batch_start//batch_size + 1}, total tokens so far: {(batch_end * len(all_ids)) // len(batch_files)}")
    
    pool.close()
    pool.join()


if __name__ == "__main__":
    # read clusters
    cluster_file = "/home/azureuser/mount/duplicate_clusters.pkl"

    with open(cluster_file, "rb") as f:
        all_clusters = pickle.load(f)

    # choose a random element from each set
    files_2keep = [random.choice(list(c)) for c in all_clusters["clusters"]]
    metadata = all_clusters["metadata"]
    print(f"Total docs: {len(metadata)/1e6}M")
    print(f"Kept docs: {len(files_2keep)/1e6}M")

    # get dict of file name and line ids
    metadata_2keep = [metadata[i] for i in sorted(files_2keep)]
    input_file_dict = pd.DataFrame(metadata_2keep).groupby("jsonl_file")["line_id"].agg(list).to_dict()

    # Tokenization
    tokenize_incremental(input_file_dict, OUTPUT_DIR/"CC_filtered_tokens.bin", 200)

