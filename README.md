## UCI Dataset Crawler

**Author:** [Pedro Vinícius A. B. Venâncio](https://www.linkedin.com/in/pedbrgs/)<sup>1</sup> <br />

***

## :book: About

This project uses a modular, two-step process to scrape the UCI Machine Learning Repository, collect detailed metadata, and then download all available files for a local repository.

## :gear: Installation

1. Clone the repository.
```bash
    git clone https://github.com/pedbrgs/UCI-Dataset-Crawler
```
2. Navigate into the project directory.
```bash
    cd UCI-Dataset-Crawler
```
3. Install the dependencies.
```bash
    pip install -r requirements.txt
```

Note: Python 3.x is required.

## :high_brightness: Usage

The project is executed in two simple steps.

### Step 1: Collect metadata

Run the metadata collector script to crawl the UCI index, extract dataset details, and save the results to a CSV file.

```bash
    python collect_metadata.py
```

The output CSV file is saved by default to `./metadata/uci_datasets_metadata.csv`.

### Step 2: Download datasets

Use the downloader script to fetch all datasets listed in the metadata file.
You must provide the path to the CSV file generated in Step 1.

```bash
    python download_datasets.py --metadata_csv ./metadata/uci_datasets_metadata.csv --download_dir ./datasets/
```

## :open_file_folder: Directory structure

After running the full process, your project folder will look like this:

```
UCI-Dataset-Crawler/
├── collect_metadata.py
├── download_datasets.py
├── engine/              # Internal modules (crawler.py, downloader.py)
├── metadata/            # Output folder for metadata
│   └── uci_datasets_metadata.csv
└── datasets/            # Default output folder for downloads
    ├── Arcene.zip
    └── ... (downloaded files)
```

## :pencil: Contact

Please send any bug reports, questions or suggestions directly in the repository.