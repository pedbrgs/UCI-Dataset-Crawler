import os
from engine.crawler import crawl_metadata


if __name__ == "__main__":
    print("Starting UCI Metadata Crawler...")
    metadata = crawl_metadata()

    if not metadata.empty:
        os.makedirs("./data/", exist_ok=True)
        metadata.to_csv("./data/uci_datasets_metadata.csv", index=False)
        print(f"\nSaved metadata for {len(metadata)} datasets.")
    else:
        print("\nFailed to collect any data.")
