import boto3
import zipfile
import io

s3 = boto3.client('s3')

def lambda_handler(event, context):
    source_bucket = 'your-source-bucket'
    target_bucket = 'your-target-bucket'
    zip_filename = 'all_files.zip'
    
    # Create a zip file in-memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # List objects in the source bucket
        response = s3.list_objects_v2(Bucket=source_bucket)
        
        if 'Contents' in response:
            objects = response.get('Contents', [])
            
            for obj in objects:
                key = obj.get('Key')
                if key:
                    # Get object content
                    response = s3.get_object(Bucket=source_bucket, Key=key)
                    content = response['Body'].read()
                    
                    # Add file to zip
                    zipf.writestr(key, content)
        else:
            print("No objects found in the source bucket.")
    
    # Upload the zip file to the target bucket
    zip_buffer.seek(0)
    s3.upload_fileobj(zip_buffer, target_bucket, zip_filename)
    
    return {
        'statusCode': 200,
        'body': f'Created {zip_filename} with all files from {source_bucket}'
    }
