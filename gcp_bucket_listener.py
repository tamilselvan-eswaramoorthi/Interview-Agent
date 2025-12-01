"""
GCP Storage Bucket Listener
Monitors a GCP bucket for new PNG files and tracks them for display in Streamlit UI
"""

import os
import time
import json
import datetime
from google.cloud import storage
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GCPBucketListener:
    def __init__(self, bucket_name, download_dir="downloaded_images", start_time=None):
        """
        Initialize GCP bucket listener
        
        Args:
            bucket_name: Name of the GCP storage bucket to monitor
            download_dir: Local directory to download PNG files
            start_time: Only process images uploaded after this time (datetime object)
        """
        self.bucket_name = bucket_name
        self.download_dir = download_dir
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)
        self.seen_files = set()
        self.metadata_file = "image_metadata.json"
        
        # Make start_time timezone-aware once during initialization
        if start_time:
            if start_time.tzinfo is None:
                self.start_time = start_time.replace(tzinfo=datetime.timezone.utc)
            else:
                self.start_time = start_time
        else:
            self.start_time = None
        
        # Callback for when new image is detected
        self.on_new_image = None
        
        # Create download directory if it doesn't exist
        Path(download_dir).mkdir(parents=True, exist_ok=True)
        
        # Load existing metadata
        self.load_metadata()
        
    def load_metadata(self):
        """Load metadata of previously seen images"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    self.seen_files = set(data.get('seen_files', []))
                    logger.info(f"Loaded {len(self.seen_files)} previously seen files")
            except Exception as e:
                logger.error(f"Error loading metadata: {e}")
                self.seen_files = set()
        else:
            self.seen_files = set()
    
    def check_for_new_pngs(self):
        """Check bucket for the latest PNG file"""
        new_files = []
        
        try:
            # List all PNG blobs and sort by time_created to get the latest
            blobs = list(self.bucket.list_blobs())
            
            # Filter PNG files only
            png_blobs = [blob for blob in blobs if blob.name.lower().endswith('.png')]
            
            if not png_blobs:
                return new_files
            
            # Sort by time_created (most recent first) and get the latest
            png_blobs.sort(key=lambda x: x.time_created if x.time_created else datetime.datetime.min.replace(tzinfo=datetime.timezone.utc), reverse=True)
            latest_blob = png_blobs[0]


            image_name = latest_blob.name
            image_name = image_name.split('/')[-1]

            #created time from name
            created_time  = image_name.split('_')[1] + '_' + image_name.split('_')[2][:6]  #20251201_144858
            created_time = datetime.datetime.strptime(created_time, "%Y%m%d_%H%M%S").replace(tzinfo=datetime.timezone.utc)

            if image_name not in self.seen_files:
                if self.start_time and created_time:
                    if created_time < self.start_time:
                        logger.info(f"Skipping old file: {image_name} uploaded")
                        return new_files
                
                logger.info(f"New PNG file detected: {latest_blob.name}")
                
                # Download the file
                local_path = os.path.join(self.download_dir, os.path.basename(image_name))
                latest_blob.download_to_filename(local_path)
                logger.info(f"Downloaded to: {local_path}")
                
                # Track the file
                self.seen_files.add(image_name)
                file_info = {
                    'name': image_name,
                    'local_path': local_path,
                    'size': latest_blob.size,
                    'created': latest_blob.time_created.isoformat() if latest_blob.time_created else None,
                    'updated': latest_blob.updated.isoformat() if latest_blob.updated else None
                }
                new_files.append(file_info)
                
                # Trigger callback if registered
                if self.on_new_image:
                    self.on_new_image(local_path, file_info)
                
        except Exception as e:
            logger.error(f"Error checking bucket: {e}")
        
        return new_files
    
    def listen(self, interval=5):
        """
        Continuously monitor the bucket for new PNG files
        
        Args:
            interval: Time in seconds between checks
        """
        logger.info(f"Starting to monitor bucket: {self.bucket_name}")
        logger.info(f"Checking every {interval} seconds for new PNG files...")
        
        try:
            while True:
                new_files = self.check_for_new_pngs()
                
                if new_files:
                    logger.info(f"Found {len(new_files)} new PNG file(s)")
                    for file_info in new_files:
                        logger.info(f"  - {file_info['name']} ({file_info['size']} bytes)")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Stopping bucket listener...")
        except Exception as e:
            logger.error(f"Error in listener loop: {e}")
