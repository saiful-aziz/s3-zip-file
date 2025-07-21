# S3 Bucket Zipper

A simple AWS Lambda function that zips all files in an S3 bucket and uploads the resulting zip file to a target bucket.

## Description

This Lambda function scans all files in a specified S3 source bucket, compresses them into a single zip file, and then uploads that zip file to a target S3 bucket. The process happens entirely in memory, making it efficient for serverless environments.

## Features

- Creates a zip file containing all files from a source S3 bucket
- Handles the compression process in-memory without requiring disk space
- Uploads the resulting zip file to a target S3 bucket
- Returns a success message with details about the operation

## Requirements

- AWS Lambda environment
- IAM role with permissions for:
  - s3:ListObjects
  - s3:GetObject
  - s3:PutObject
- Two S3 buckets (source and target)

## Setup

1. Create a new Lambda function in AWS
2. Copy the code from `zip-s3-bucket.py` into the function
3. Set the appropriate values for `source_bucket` and `target_bucket` in the code
4. Configure the Lambda execution role with the necessary S3 permissions
5. Set an appropriate timeout value (depending on the expected size of your bucket contents)

## Usage

The function can be triggered in several ways:

- Manually through the AWS Console
- On a schedule using CloudWatch Events
- In response to S3 events
- Through the AWS SDK or CLI

## Configuration

Modify these variables in the code to customize behavior:

```python
source_bucket = 'your-source-bucket'  # The bucket containing files to zip
target_bucket = 'your-target-bucket'  # The bucket where the zip file will be stored
zip_filename = 'all_files.zip'        # Name of the resulting zip file
```

## Limitations

- The function processes all files in memory, so it may not be suitable for very large buckets
- There is no pagination implemented, so it will only process the first 1000 objects in a bucket
- No filtering mechanism is implemented - all files in the bucket will be included

## License

[Insert your preferred license here]

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
