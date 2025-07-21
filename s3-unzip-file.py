#To use this unzip tool effectively: Ensure you increase the function’s memory allocation and set the execution timeout to the maximum (up to 15 minutes).
#If you're already using the maximum timeout and only part of the ZIP file is extracted, consider using AWS Step Functions to break the task into smaller, manageable steps.
import boto3
import zipfile
import os
import tempfile
import logging
import json
import time
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    start_time = time.time()
    # Get the remaining time in milliseconds and convert to seconds
    max_execution_time = context.get_remaining_time_in_millis() / 1000 if hasattr(context, 'get_remaining_time_in_millis') else 840  # Default to 14 minutes (safe margin)
    
    try:
        # Manually specify bucket name and zip file path here
        bucket_name = 'YOUR-S3-BUCKET'
        key = 'YOUR-FILE.zip'
        
        # Specify the password for the zip file
        zip_password = 'ADD-ZIP-PASSWORD'  # Replace with the actual password
        pwd_bytes = zip_password.encode('utf-8') if zip_password else None
        
        logger.info(f"Processing password-protected zip file: {key} from bucket: {bucket_name}")
        logger.info(f"Maximum execution time: {max_execution_time} seconds")
        
        # Check if the file is a zip file
        if not key.lower().endswith('.zip'):
            logger.error(f"File {key} is not a zip file.")
            return {
                'statusCode': 400,
                'body': 'Not a zip file, no action taken'
            }
        
        # Get the directory where the zip file is located
        prefix = os.path.dirname(key)
        if prefix and not prefix.endswith('/'):
            prefix += '/'
        
        with tempfile.TemporaryDirectory() as tmpdir:
            download_path = os.path.join(tmpdir, os.path.basename(key))
            
            # Download the zip file
            logger.info(f"Attempting to download {key} from bucket {bucket_name}")
            download_start = time.time()
            try:
                s3_client.download_file(bucket_name, key, download_path)
                logger.info(f"Successfully downloaded {key} in {time.time() - download_start:.2f} seconds")
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', 'Unknown error')
                logger.error(f"Failed to download file. Error code: {error_code}, Message: {error_message}")
                return {
                    'statusCode': 500,
                    'body': f'Error downloading file: {error_code} - {error_message}'
                }
            
            # Get file size
            file_size = os.path.getsize(download_path)
            logger.info(f"Zip file size: {file_size / (1024 * 1024):.2f} MB")
            
            # Extract the password-protected zip file
            logger.info(f"Extracting password-protected zip file {key}")
            extract_start = time.time()
            
            # Statistics
            total_files = 0
            extracted_files = 0
            failed_files = 0
            uploaded_files = 0
            skipped_files = 0
            
            try:
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    # Get list of files in the zip
                    file_list = zip_ref.namelist()
                    total_files = len(file_list)
                    logger.info(f"Found {total_files} files in the zip archive")
                    
                    # Extract and upload each file with password
                    for i, file_path in enumerate(file_list):
                        # Check for timeout - leave 60 seconds for cleanup
                        elapsed_time = time.time() - start_time
                        if elapsed_time > (max_execution_time - 60):
                            logger.warning(f"Approaching Lambda timeout after processing {i} of {total_files} files. Stopping extraction.")
                            break
                        
                        # Skip directories
                        if file_path.endswith('/'):
                            skipped_files += 1
                            continue
                        
                        try:
                            # Extract file
                            zip_ref.extract(file_path, path=tmpdir, pwd=pwd_bytes)
                            extracted_files += 1
                            
                            # Upload file immediately after extraction to save memory
                            local_path = os.path.join(tmpdir, file_path)
                            
                            # Combine the original prefix with the file path from the zip
                            if prefix:
                                s3_key = prefix + '/' + file_path
                            else:
                                s3_key = file_path
                            
                            # Normalize the path to avoid double slashes
                            s3_key = s3_key.replace('//', '/')
                            
                            # Upload the file
                            s3_client.upload_file(local_path, bucket_name, s3_key)
                            uploaded_files += 1
                            
                            # Remove the file to free up space
                            os.remove(local_path)
                            
                            # Log progress periodically
                            if i % 100 == 0 or i == total_files - 1:
                                logger.info(f"Progress: {i+1}/{total_files} files processed ({(i+1)/total_files*100:.1f}%)")
                                
                        except Exception as extract_error:
                            logger.error(f"Failed to process {file_path}: {str(extract_error)}")
                            failed_files += 1
                    
                    extraction_time = time.time() - extract_start
                    logger.info(f"Extraction and upload completed in {extraction_time:.2f} seconds")
                    
            except zipfile.BadZipFile as e:
                logger.error(f"Invalid zip file: {str(e)}")
                return {
                    'statusCode': 400,
                    'body': f'Invalid zip file: {str(e)}'
                }
            except RuntimeError as e:
                if 'Bad password' in str(e):
                    logger.error(f"Incorrect password for zip file: {str(e)}")
                    return {
                        'statusCode': 401,
                        'body': 'Incorrect password for zip file'
                    }
                else:
                    logger.error(f"Runtime error: {str(e)}")
                    return {
                        'statusCode': 500,
                        'body': f'Runtime error: {str(e)}'
                    }
            
            total_time = time.time() - start_time
            logger.info(f"Operation statistics:")
            logger.info(f"- Total files in zip: {total_files}")
            logger.info(f"- Files extracted: {extracted_files}")
            logger.info(f"- Files uploaded: {uploaded_files}")
            logger.info(f"- Files failed: {failed_files}")
            logger.info(f"- Files skipped: {skipped_files}")
            logger.info(f"- Total execution time: {total_time:.2f} seconds")
            
            # Check if all files were processed
            if extracted_files < total_files - skipped_files:
                logger.warning(f"Not all files were processed. Consider breaking up the zip file or increasing Lambda timeout/memory.")
                return {
                    'statusCode': 206,  # Partial Content
                    'body': json.dumps({
                        'message': 'Partial extraction completed due to Lambda constraints',
                        'total_files': total_files,
                        'extracted_files': extracted_files,
                        'uploaded_files': uploaded_files,
                        'failed_files': failed_files,
                        'skipped_files': skipped_files,
                        'execution_time_seconds': round(total_time, 2)
                    })
                }
            
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully extracted and uploaded all files',
                'total_files': total_files,
                'extracted_files': extracted_files,
                'uploaded_files': uploaded_files,
                'failed_files': failed_files,
                'skipped_files': skipped_files,
                'execution_time_seconds': round(total_time, 2)
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': f'Unexpected error: {str(e)}'
        }
