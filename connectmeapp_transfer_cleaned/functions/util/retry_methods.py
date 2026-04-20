import time
from google.cloud.exceptions import NotFound, GoogleCloudError

def delete_blob_with_retry(bucket, image_id, retries=10, delay=0.5):
    blob = bucket.blob(image_id)
    for attempt in range(retries):
        try:
            blob.delete()
            return True
        except NotFound:
            # Blob doesn't exist — can safely ignore or log
            return False
        except GoogleCloudError as e:
            # Retry on transient errors
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise  # Reraise on last attempt