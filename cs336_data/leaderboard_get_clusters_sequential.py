import os
from pathlib import Path
import pickle
from tqdm import tqdm
import numpy as np
import gc

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_candidates_single_band(sigs, band_idx, band_size=16):
    """Process a single band to find candidate pairs - optimized with numpy"""
    
    start = band_idx * band_size
    sig_band = sigs[:, start:start+band_size]
    
    # Use numpy for faster hashing: convert each row to bytes for hashing
    buckets = defaultdict(set)
    for idx in range(sig_band.shape[0]):
        # Convert row to tuple for hashing (much faster than .tolist() on whole array)
        key = tuple(sig_band[idx])
        buckets[key].add(idx)
    
    # Return only buckets with multiple documents
    # return [v for v in buckets.values() if len(v) > 1]
    return list(buckets.values())

class UnionFind:
    """Efficient union-find data structure with path compression"""
    def __init__(self):
        self.parent = {}
    
    def find(self, x):
        """Find root with iterative path compression (avoids recursion limit)"""
        if x not in self.parent:
            self.parent[x] = x
            return x
        
        # Find root iteratively
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        
        # Path compression: make all nodes point directly to root
        current = x
        while current != root:
            next_node = self.parent[current]
            self.parent[current] = root
            current = next_node
        
        return root
    
    def union(self, x, y):
        """Union two sets"""
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x != root_y:
            self.parent[root_x] = root_y
    
    def get_clusters(self):
        """Get all clusters as dict mapping root -> set of members"""
        clusters = defaultdict(set)
        for x in self.parent:
            clusters[self.find(x)].add(x)
        return list(clusters.values())


def merge_overlapping_sets(sets: list[set[int]], keep_singletons: bool = False) -> list[set[int]]:
    """Merge sets with overlapping elements using Union-Find
    
    Args:
        sets: List of sets to merge
        keep_singletons: If True, include singleton sets in output
    
    Time: O(n × α(n)) where n = total elements across all sets
    Space: O(n)
    """
    uf = UnionFind()
    
    # Union all elements within each set
    for s in sets:
        elements = list(s)
        # Add all elements to union-find (even singletons)
        for elem in elements:
            uf.find(elem)  # Ensure element exists
        # Union pairs within each set
        for i in range(1, len(elements)):
            uf.union(elements[0], elements[i])
    
    clusters = uf.get_clusters()
    
    # Filter out singletons if requested
    if not keep_singletons:
        clusters = [c for c in clusters if len(c) > 1]
    
    return clusters


if __name__ == "__main__":
    sig_dir = "/home/azureuser/mount/"
    batch_files = sorted(Path(sig_dir).glob('signatures_batch_*.pkl'))
    print(f"Found {len(batch_files)} files to load")

    #####################################################

    # load pickle files 
    # Memory-efficient: Load files incrementally without massive temp buffers
    # Signature into numpy array, metadata as list of dicts
    # First pass: count total documents to pre-allocate array
    print("\n# Step 1: loading signature pickle files")
    print("Counting documents...")
    total_docs = 0
    for batch_file in tqdm(batch_files, desc="Counting"):
        with open(batch_file, 'rb') as f:
            while True:
                try:
                    pickle.load(f)
                    total_docs += 1
                except EOFError:
                    break

    print(f"Total documents: {total_docs}")

    # Pre-allocate arrays (much more memory efficient)
    sigs = np.empty((total_docs, 2400), dtype=np.int32)
    all_metadata = []

    # Second pass: fill arrays incrementally
    print("Loading signatures...")
    doc_idx = 0
    for batch_file in tqdm(batch_files, desc="Loading files"):
        with open(batch_file, 'rb') as f:
            while True:
                try:
                    doc_data = pickle.load(f)
                    sigs[doc_idx] = doc_data['signatures']
                    all_metadata.append({
                        'jsonl_file': doc_data.get('jsonl_file'),
                        'line_id': doc_data.get('line_id')
                    })
                    doc_idx += 1
                except EOFError:
                    break
        
        # Force garbage collection after each file
        gc.collect()
        print(f"  Loaded {batch_file.name}, progress: {doc_idx}/{total_docs}")

    print(f"\nFinal shape: {sigs.shape}")
    print(f"Memory usage: {sigs.nbytes / 1024**3:.2f} GB")

    #####################################################

    # Get candidates by band
    print("\n# Step 2: generating duplicate candidates by band")
    band_size = 16
    num_bands = sigs.shape[1] // band_size
    
    candidates = []
    
    # Sequential processing with progress bar - faster startup, no thread overhead
    for band_idx in tqdm(range(num_bands), desc="Processing bands"):
        band_candidates = get_candidates_single_band(sigs, band_idx, band_size)
        candidates.extend(band_candidates)

    print(f"Total candidate sets: {len(candidates)}")

    #####################################################

    # Form clusters
    print("\n# Step 3: form clusters")
    final_clusters = merge_overlapping_sets(candidates, keep_singletons=True)
    print(f"Number of duplicate clusters: {len(final_clusters)}")
    print(f"Total documents in clusters: {sum(len(c) for c in final_clusters)}")

    #####################################################
    
    # Save clusters to disk
    output_file = Path(sig_dir) / "duplicate_clusters.pkl"
    # output_file = Path(".") / "duplicate_clusters.pkl"
    print(f"\nSaving clusters to {output_file}...")
    with open(output_file, 'wb') as f:
        pickle.dump({
            'clusters': final_clusters,
            'metadata': all_metadata,
            'num_documents': total_docs,
            'num_clusters': len(final_clusters)
        }, f)
    print(f"Saved {len(final_clusters)} clusters")