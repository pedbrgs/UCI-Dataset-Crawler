import argparse
import pandas as pd
from engine.downloader import download_datasets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download UCI datasets based on metadata CSV.")
    parser.add_argument(
        "--metadata_csv",
        type=str,
        required=True,
        help="Path to the CSV file containing UCI dataset metadata."
    )
    parser.add_argument(
        "--download_dir",
        type=str,
        default="./datasets/",
        help="Directory to save downloaded datasets."
    )

    args = parser.parse_args()

    print("Starting UCI Dataset Downloader...")
    metadata = pd.read_csv(args.metadata_csv)
    download_datasets(metadata, args.download_dir)
