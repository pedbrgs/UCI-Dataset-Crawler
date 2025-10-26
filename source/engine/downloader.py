import os
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup


# Define the base URL for UCI Machine Learning Repository
BASE_URL = "https://archive.ics.uci.edu"
# Define a robust, browser-like User-Agent
COMMON_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}


def get_direct_download_link(metadata_url: str) -> str:
    """Scrape the direct ZIP download link from the dataset's metadata page.

    Parameters
    ----------
    metadata_url : str
        The URL of the dataset's metadata page.
    Returns
    -------
    str
        The direct download link for the dataset ZIP file, or None if not found.
    """
    try:
        r = requests.get(metadata_url, headers=COMMON_HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # 1. NEW PRIMARY SELECTOR: Target the direct static public file link
        # This selector matches the pattern: href="/static/public/..."
        download_link_element = soup.select_one('a[href*="/static/public/"]')
        
        # 2. FALLBACK SELECTOR: Target the API endpoint link
        if not download_link_element:
            download_link_element = soup.select_one('a[href*="/api/v1/datasets/"]')
        
        if download_link_element:
            relative_link = download_link_element.get('href')
            # The link might be relative (starting with /), so we make it absolute
            if relative_link.startswith('/'):
                return BASE_URL + relative_link
            return relative_link

        return None

    except requests.RequestException as e:
        print(f"    -> Error fetching page for download link: {e}")
        return None


def download_datasets(metadata: pd.DataFrame, download_dir: str) -> None:
    """Download datasets from UCI based on the provided metadata.

    Parameters
    ----------
    metadata : pd.DataFrame
        DataFrame containing at least 'name' and 'url' columns for datasets.
    download_dir : str
        Directory to save downloaded datasets.
    """
    print(f"\nStarting dataset download to: {download_dir}")
    
    # Create the target directory if it doesn't exist
    os.makedirs(download_dir, exist_ok=True)
    
    successful_downloads = 0
    total_datasets = len(metadata)

    for index, row in metadata.iterrows():
        name = row['name']
        metadata_url = row['url']
        
        # Clean the name to create a safe base filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        
        print(f"[{index + 1}/{total_datasets}] Processing '{name}'")

        # Get the direct download link
        direct_link = get_direct_download_link(metadata_url)
        
        if not direct_link:
            print(f"    -> WARNING: Could not find direct download link for {name}. Skipping.")
            continue
        
        # Use the name of the dataset plus the file extension (usually .zip or .csv)
        file_extension = direct_link.split('.')[-1].split('?')[0].lower()
        if len(file_extension) > 5 or file_extension not in ['zip', 'csv', 'rar', 'tgz', 'txt']:
            # Default to zip if the extension is ambiguous
            file_extension = 'zip'
        
        output_filename = os.path.join(download_dir, f"{safe_name}.{file_extension}")
        
        # Skip if the file already exists (optional optimization)
        if os.path.exists(output_filename):
            print(f"    -> File already exists at {output_filename}. Skipping download.")
            successful_downloads += 1
            time.sleep(0.1) # Shorter wait time if skipping
            continue


        # Download the file
        try:
            print(f"    -> Downloading from: {direct_link}")
            
            # Streaming download to handle large files
            with requests.get(direct_link, stream=True, headers=COMMON_HEADERS, timeout=60) as r:
                r.raise_for_status()
                with open(output_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            print(f"    -> SUCCESS: Saved to {output_filename}")
            successful_downloads += 1
            
        except requests.RequestException as e:
            print(f"    -> ERROR: Failed to download {name}. Reason: {e}")
        except Exception as e:
            print(f"    -> ERROR: An unexpected error occurred: {e}")

        # Wait between requests
        time.sleep(1)

    print(f"\n Download process complete. {successful_downloads} of {total_datasets} datasets downloaded.")
