# S3 Bucket Zipper

A simple AWS Lambda utility for zipping and unzipping files stored in Amazon S3 using Python.

## Description

This project includes two Lambda functions:

- `zip-s3-bucket.py`: Compresses all files in a specified S3 bucket into a single ZIP archive and uploads it to another S3 bucket.
- `s3-unzip-file.py`: Extracts a (password-protected) ZIP file stored in S3 and uploads the extracted contents back to the bucket.

Both functions operate entirely in memory and are optimized for serverless environments.

## Features

### 🔹 Zip Function (`zip-s3-bucket.py`)
- Scans and compresses all objects in a source S3 bucket into a single ZIP file
- Performs in-memory compression (no disk I/O)
- Uploads the ZIP archive to a target S3 bucket
- Returns metadata on the operation (e.g., file count, duration)

### 🔹 Unzip Function (`s3-unzip-file.py`)
- Extracts contents of a ZIP file (with optional password) stored in S3
- Uploads each extracted file directly to the target S3 location
- Handles large ZIP files gracefully by tracking Lambda time limits and stopping safely before timeout
- Logs detailed statistics (successes, failures, skipped files, etc.)

> **Note:**  
> To use the unzip tool effectively, ensure you increase the Lambda function’s **memory allocation** and set the **execution timeout** to the maximum (up to 15 minutes).  
> If you're already using the maximum timeout and only part of the ZIP file is extracted, consider using **AWS Step Functions** to break the extraction into smaller, more manageable steps.

## Requirements

- AWS Lambda runtime (Python 3.x)
- IAM role with permissions:
  - `s3:ListObjects`
  - `s3:GetObject`
  - `s3:PutObject`
- Two S3 buckets (source and target)
- Adequate Lambda configuration:
  - **Memory**: At least 512 MB (1–2 GB recommended for large files)
  - **Timeout**: Up to 15 minutes

## Setup

### 1. Zipping Files (zip-s3-bucket.py)

1. Create a new Lambda function
2. Copy `zip-s3-bucket.py` into the function code
3. Configure the variables:
    ```python
    source_bucket = 'your-source-bucket'
    target_bucket = 'your-target-bucket'
    zip_filename = 'all_files.zip'
    ```
4. Adjust Lambda memory and timeout settings
5. Grant S3 access via IAM

### 2. Unzipping Files (s3-unzip-file.py)

1. Create a new Lambda function
2. Copy `s3-unzip-file.py` into the function code
3. Configure these variables:
    ```python
    bucket_name = 'YOUR-S3-BUCKET'
    key = 'YOUR-FILE.zip'
    zip_password = 'ADD-ZIP-PASSWORD'
    ```
4. Adjust memory/timeout as needed
5. Ensure the bucket allows `upload` and `download` permissions

## Usage

You can invoke the functions via:

- AWS Console (manual test)
- CloudWatch scheduled events
- S3 triggers (e.g., on file upload)
- AWS SDK / CLI

## Limitations

- Currently processes up to **1000 objects** due to no pagination in the zipping function
- Unzip function will stop early if **approaching timeout**, ensuring partial work is not lost
- No filter or file-type inclusion/exclusion logic
- Both functions operate entirely in memory — not ideal for extremely large files

## License

GNU General Public License v3.0

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation.

See https://www.gnu.org/licenses/ for full details.

## Contributing

Contributions are welcome! Please submit a pull request if you'd like to improve or extend this project.
