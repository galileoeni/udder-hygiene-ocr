#!/usr/bin/env python3
"""
Automated Udder Hygiene Data Processing Pipeline
This script can be scheduled to run automatically using cron (Linux/Mac) or Task Scheduler (Windows)
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Import our OCR processor
from ocr_automation_backend import UdderHygieneOCR, DataExporter

# Configuration
CONFIG = {
    'WATCH_FOLDER': '/path/to/scanned/documents',  # Folder where scanned docs are saved
    'PROCESSED_FOLDER': '/path/to/processed',       # Archive folder
    'OUTPUT_FOLDER': '/path/to/output',             # Excel output folder
    'ERROR_FOLDER': '/path/to/errors',              # Failed files
    'EMAIL_SETTINGS': {
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'sender': 'automation@farm.com',
        'password': 'your_app_password',
        'recipients': ['manager@farm.com', 'data_analyst@farm.com']
    },
    'SCHEDULE_TIME': '08:00',  # Daily report time
    'ENABLE_REALTIME': True     # Enable real-time file monitoring
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FileWatcher(FileSystemEventHandler):
    """Watch for new files in the scanned documents folder"""
    
    def __init__(self, processor):
        self.processor = processor
        
    def on_created(self, event):
        if not event.is_directory:
            # Wait a bit to ensure file is completely written
            time.sleep(2)
            self.process_new_file(event.src_path)
    
    def process_new_file(self, filepath):
        """Process newly detected file"""
        logger.info(f"New file detected: {filepath}")
        
        try:
            # Process with OCR
            processor = UdderHygieneOCR()
            data = processor.process_file(filepath)
            
            if data:
                # Generate timestamp for unique filenames
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                # Export to Excel
                excel_path = Path(CONFIG['OUTPUT_FOLDER']) / f"udder_hygiene_{timestamp}.xlsx"
                DataExporter.to_excel(data, excel_path)
                
                # Move processed file to archive
                archive_path = Path(CONFIG['PROCESSED_FOLDER']) / Path(filepath).name
                shutil.move(filepath, archive_path)
                
                logger.info(f"Successfully processed {filepath}")
                
                # Send notification
                self.send_notification(Path(filepath).name, len(data), excel_path)
            else:
                # No data extracted, move to error folder
                error_path = Path(CONFIG['ERROR_FOLDER']) / Path(filepath).name
                shutil.move(filepath, error_path)
                logger.warning(f"No data extracted from {filepath}")
                
        except Exception as e:
            logger.error(f"Error processing {filepath}: {str(e)}")
            # Move to error folder
            error_path = Path(CONFIG['ERROR_FOLDER']) / Path(filepath).name
            shutil.move(filepath, error_path)
    
    def send_notification(self, filename, record_count, output_path):
        """Send email notification when file is processed"""
        subject = f"Udder Hygiene Data Processed: {filename}"
        body = f"""
        File Processing Complete
        
        Original File: {filename}
        Records Extracted: {record_count}
        Output File: {output_path.name}
        Processing Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        The Excel file has been saved to the output folder.
        """
        
        send_email(subject, body, attachment_path=output_path)


class AutomationPipeline:
    """Main automation pipeline"""
    
    def __init__(self):
        self.ocr_processor = UdderHygieneOCR()
        self.exporter = DataExporter()
        self.ensure_folders_exist()
    
    def ensure_folders_exist(self):
        """Create necessary folders if they don't exist"""
        for folder_key in ['WATCH_FOLDER', 'PROCESSED_FOLDER', 'OUTPUT_FOLDER', 'ERROR_FOLDER']:
            Path(CONFIG[folder_key]).mkdir(parents=True, exist_ok=True)
    
    def process_batch(self):
        """Process all files in watch folder"""
        watch_folder = Path(CONFIG['WATCH_FOLDER'])
        files_processed = 0
        all_data = []
        
        for file_path in watch_folder.iterdir():
            if file_path.suffix.lower() in self.ocr_processor.supported_formats:
                try:
                    logger.info(f"Processing {file_path.name}")
                    data = self.ocr_processor.process_file(file_path)
                    
                    if data:
                        all_data.extend(data)
                        # Archive processed file
                        archive_path = Path(CONFIG['PROCESSED_FOLDER']) / file_path.name
                        shutil.move(str(file_path), str(archive_path))
                        files_processed += 1
                    else:
                        # Move to error folder
                        error_path = Path(CONFIG['ERROR_FOLDER']) / file_path.name
                        shutil.move(str(file_path), str(error_path))
                        
                except Exception as e:
                    logger.error(f"Error processing {file_path.name}: {str(e)}")
                    error_path = Path(CONFIG['ERROR_FOLDER']) / file_path.name
                    shutil.move(str(file_path), str(error_path))
        
        # Generate consolidated report
        if all_data:
            self.generate_daily_report(all_data, files_processed)
        
        return files_processed, len(all_data)
    
    def generate_daily_report(self, data, files_count):
        """Generate daily consolidated report"""
        timestamp = datetime.now().strftime("%Y%m%d")
        
        # Excel report
        excel_path = Path(CONFIG['OUTPUT_FOLDER']) / f"daily_report_{timestamp}.xlsx"
        self.exporter.to_excel(data, excel_path)
        
        # CSV backup
        csv_path = Path(CONFIG['OUTPUT_FOLDER']) / f"daily_report_{timestamp}.csv"
        self.exporter.to_csv(data, csv_path)
        
        # Calculate statistics
        import pandas as pd
        df = pd.DataFrame(data)
        
        stats = {
            'total_records': len(df),
            'files_processed': files_count,
            'average_score': round(df['average'].mean(), 2),
            'groups_processed': df['group'].nunique(),
            'date_range': f"{df['date'].min()} to {df['date'].max()}"
        }
        
        # Send daily report email
        self.send_daily_report(stats, excel_path)
    
    def send_daily_report(self, stats, report_path):
        """Send daily summary email"""
        subject = f"Daily Udder Hygiene Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
        Daily Udder Hygiene Data Processing Summary
        
        Processing Statistics:
        - Files Processed: {stats['files_processed']}
        - Total Records: {stats['total_records']}
        - Average Score: {stats['average_score']}
        - Groups Processed: {stats['groups_processed']}
        - Date Range: {stats['date_range']}
        
        The detailed Excel report is attached.
        
        This is an automated message from the Udder Hygiene Data Processing System.
        """
        
        send_email(subject, body, attachment_path=report_path)
    
    def run_scheduled_job(self):
        """Run the scheduled batch processing"""
        logger.info("Starting scheduled batch processing...")
        files_processed, records_extracted = self.process_batch()
        logger.info(f"Batch processing complete. Files: {files_processed}, Records: {records_extracted}")


def send_email(subject, body, attachment_path=None):
    """Send email notification"""
    try:
        msg = MIMEMultipart()
        msg['From'] = CONFIG['EMAIL_SETTINGS']['sender']
        msg['To'] = ', '.join(CONFIG['EMAIL_SETTINGS']['recipients'])
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment_path and Path(attachment_path).exists():
            with open(attachment_path, 'rb') as file:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {Path(attachment_path).name}'
                )
                msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(
            CONFIG['EMAIL_SETTINGS']['smtp_server'],
            CONFIG['EMAIL_SETTINGS']['smtp_port']
        )
        server.starttls()
        server.login(
            CONFIG['EMAIL_SETTINGS']['sender'],
            CONFIG['EMAIL_SETTINGS']['password']
        )
        
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully: {subject}")
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")


def main():
    """Main execution function"""
    pipeline = AutomationPipeline()
    
    # Schedule daily batch processing
    schedule.every().day.at(CONFIG['SCHEDULE_TIME']).do(pipeline.run_scheduled_job)
    
    # Setup real-time file monitoring if enabled
    if CONFIG['ENABLE_REALTIME']:
        event_handler = FileWatcher(pipeline.ocr_processor)
        observer = Observer()
        observer.schedule(event_handler, CONFIG['WATCH_FOLDER'], recursive=False)
        observer.start()
        logger.info(f"Real-time monitoring started for {CONFIG['WATCH_FOLDER']}")
    
    logger.info(f"Automation pipeline started. Daily processing scheduled at {CONFIG['SCHEDULE_TIME']}")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        if CONFIG['ENABLE_REALTIME']:
            observer.stop()
            observer.join()
        logger.info("Automation pipeline stopped")


if __name__ == "__main__":
    main()