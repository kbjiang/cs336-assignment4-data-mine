import os
import requests
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from xopen import xopen
from tqdm import tqdm

base_url = "https://data.commoncrawl.org/"
MOUNT_DIR = Path("/home/azureuser/mount/")
N_CPU = len(os.sched_getaffinity(0))

def download_file(url, output_dir):
    filename = Path(url).name
    output_path = output_dir / filename
    
    if output_path.exists():
        return True, f"Skipped: {filename}"
    
    try:
        response = requests.get(url, stream=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True, f"Downloaded: {filename}"
    except Exception as e:
        return False, f"Error {filename}: {e}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Download Common Crawl WET files')
    parser.add_argument('--n-wet', type=int, default=100, help='Number of WET files to download')
    parser.add_argument('--output-dir', type=str, default=str(MOUNT_DIR/"CC"), help='Output directory for downloaded files')
    args = parser.parse_args()
    
    N_WET = args.n_wet
    
    # Read all paths
    with xopen('wet.paths.gz', 'rt') as f:
        all_paths = [line.strip() for line in f]

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    # Download until we have N_WET successful downloads
    successful_downloads = 0
    path_idx = 0
    futures = {}
    
    pbar = tqdm(total=N_WET, desc="Downloading WET files", unit="file")

    with ThreadPoolExecutor(max_workers=N_CPU) as executor:
        # Submit initial batch
        while path_idx < len(all_paths) and len(futures) < N_CPU:
            url = base_url + all_paths[path_idx]
            future = executor.submit(download_file, url, output_dir)
            futures[future] = path_idx
            path_idx += 1
        
        # Process results and submit new jobs as needed
        while successful_downloads < N_WET and futures:
            done, _ = as_completed(futures), None
            
            for future in list(futures.keys()):
                if future.done():
                    success, message = future.result()
                    
                    if success and not message.startswith("Skipped"):
                        successful_downloads += 1
                        pbar.update(1)
                    
                    if not success:
                        pbar.write(message)
                    
                    del futures[future]
                    
                    # Submit new job if we need more downloads
                    if successful_downloads < N_WET and path_idx < len(all_paths):
                        url = base_url + all_paths[path_idx]
                        new_future = executor.submit(download_file, url, output_dir)
                        futures[new_future] = path_idx
                        path_idx += 1
                    
                    break
    
    pbar.close()
    print(f"\nCompleted: {successful_downloads} successful downloads")
