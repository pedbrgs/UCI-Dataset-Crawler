import time
import requests
import pandas as pd
from typing import List, Dict
from bs4 import BeautifulSoup


# Define the base URL for UCI Machine Learning Repository
BASE_URL = "https://archive.ics.uci.edu"
# Define the base path for the datasets listing page
DATASETS_BASE_PATH = "/datasets" 
# Define a robust, browser-like User-Agent
COMMON_HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}


def get_dataset_links() -> List[str]:
    """Scrape all dataset names and URLs from the UCI dataset listing using pagination.

    Returns
    -------
    list
        A list of dataset page URLs.
    """
    print("Fetching dataset list using pagination...")
    
    all_links = set()
    skip = 0
    take = 20 # Number of datasets to fetch per page
    # Default query parameters to ensure we get the complete, sorted list
    base_query = "sort=desc&view=list&orderBy=NumHits&search="
    
    while True:
        # Construct the URL with skip and take for pagination
        paginated_url = f"{BASE_URL}{DATASETS_BASE_PATH}?skip={skip}&take={take}&{base_query}"
        print(f"  -> Fetching page: skip={skip}")
        
        try:
            # Use the robust headers
            response = requests.get(paginated_url, headers=COMMON_HEADERS, timeout=20)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Error fetching dataset page at skip={skip}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # Target all anchor tags whose href attribute starts with '/dataset/' (singular)
        dataset_cards = soup.select("a[href^='/dataset/']")
        page_links = []
        for card in dataset_cards:
            href = card.get("href")
            
            if href:
                # Split the relative path (e.g., '/dataset/53/iris') by '/' and filter out empty strings
                path_segments = [segment for segment in href.split('/') if segment]
                # Check for the new structure: ['dataset', ID, SLUG] (3 segments)
                if len(path_segments) == 3 and path_segments[0] == 'dataset':
                    page_links.append(BASE_URL + href)

        # Add new links to the master set
        all_links.update(page_links)
        
        # Check if the number of unique links found on this page is less than 'take'
        if not page_links or len(page_links) < take:
            # If the number of links found is less than the page size, we've reached the end
            break
        
        # Move to the next page
        skip += take
        
        # Wait to be polite
        time.sleep(0.3)

    links = list(all_links)
    print(f"Found a total of {len(links)} unique dataset links.")
    return links


def parse_dataset_page(url: str) -> Dict[str, str]:
    """Extract dataset metadata from its detail page.

    Parameters
    ----------
    url : str
        The URL of the dataset detail page.
    Returns
    -------
    dict
        A dictionary containing the dataset metadata.
    """
    name = "N/A"
    try:
        # Use the robust headers
        r = requests.get(url, headers=COMMON_HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Dataset name
        name_element = soup.select_one('h1')
        name = name_element.text.strip() if name_element else "N/A"
        
        # Description
        description = "N/A"
        if name_element:
            parent = name_element.find_parent('div')
            if parent:
                # Look for the immediate next sibling <p> or a common description class
                description_element = parent.find_next_sibling('p') or parent.find('p', class_=lambda c: c and 'pb-6' in c)
                if description_element:
                    description = description_element.text.strip()

        metadata = {"name": name, "url": url, "description": description}

        # Extract metadata fields (handling multiple known layouts)
        dts = []
        dds = []
        
        # Attempt to find the standard <dl><dt><dd> structure (Modern/Older)
        metadata_container = soup.select_one('dl') 
        if metadata_container:
            dts = metadata_container.select('dt')
            dds = metadata_container.select('dd')
        else:
            # Fallback to the specific class-based <dt>/<dd> selectors (Previous attempt)
            dts = soup.select('dl dt.text-sm.font-medium, div dt.text-sm.font-medium')
            dds = soup.select('dl dd.mt-1.text-sm, div dd.mt-1.text-sm')
            
        # Check for the new <h1>/<p> structure if no metadata was found via A
        if not dts:
            # Target all h1 elements that are likely headers for the characteristic fields
            # We look for h1 inside a col-span div (as provided in the user's HTML snippet)
            metadata_divs = soup.select('div.grid > div.col-span-4')
            
            for div in metadata_divs:
                header = div.select_one('h1.text-lg.font-semibold')
                value_p = div.select_one('p.text-md')
                
                if header and value_p:
                    dts.append(header)
                    dds.append(value_p)

        # Process the collected keys and values
        for dt, dd in zip(dts, dds):
            # Extract key and value, stripping whitespace
            key = dt.text.strip()
            value = dd.text.strip()
            
            # Use cleaner key names where necessary (e.g., remove hash symbol)
            if key.startswith('# '):
                key = key[2:]
            
            if key and value and value != '-': # Ignore fields with '-' placeholder
                metadata[key] = value

        return metadata
    except requests.exceptions.RequestException as e:
        print(f" Error fetching {url}: {e}")
        return {"name": name, "url": url}
    except Exception as e:
        # Catch parsing errors
        print(f" Error parsing {url}: {e}")
        return {"name": name, "url": url, "description": "Error during parsing."}


def crawl_metadata() -> pd.DataFrame:
    """Crawl the UCI Machine Learning Repository to extract metadata for all datasets.

    Returns
    -------
    pd.DataFrame
        A DataFrame containing metadata for all datasets.
    """
    links = get_dataset_links()
    if not links:
        print("No dataset links found. Stopping crawl.")
        return pd.DataFrame()

    print("\nCrawling dataset details...")
    all_data = []
    # Use a faster iteration for demonstration, but keep a cap in mind if the total count is huge
    for i, link in enumerate(links, start=1):
        print(f"[{i}/{len(links)}] Scraping: {link}")
        data = parse_dataset_page(link)
        all_data.append(data)
        # Be polite, wait between requests
        time.sleep(0.3)

    df = pd.DataFrame(all_data)
    # Reorder columns for readability (if possible, since keys can vary)
    if not df.empty:
        # These are the keys extracted directly from the page
        common_cols = [
            'name',
            'url',
            'description',
            'Dataset Characteristics',
            'Subject Area',
            'Associated Tasks',
            'Feature Type',
            'Instances',
            'Features'
        ]
        # Map some keys for better DataFrame column names
        key_map = {
            '# Instances': 'Instances',
            '# Features': 'Features'
        }
        # Apply mapping
        df.rename(columns=key_map, inplace=True)
        
        # Place common columns first, then others
        new_cols = common_cols + [col for col in df.columns if col not in common_cols]
        # Reindex, filling missing metadata fields for some datasets with an empty string
        df = df.reindex(columns=new_cols, fill_value='')

    return df
