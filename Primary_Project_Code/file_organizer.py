import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from .logger import get_logger

logger = get_logger(__name__, 'file_organizer.log')

class FileOrganizer:
    """Organize files by type and clean duplicates"""
    
    FILE_CATEGORIES = {
        'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
        'Documents': ['.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx', '.ppt', '.pptx'],
        'Videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
        'Audio': ['.mp3', '.wav', '.flac', '.aac', '.m4a'],
        'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
        'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.txt']
    }
    
    def __init__(self, folder_path):
        self.folder_path = Path(folder_path)
        self.duplicates = []
        self.organized_count = 0
        self.report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'folder': str(self.folder_path),
            'files_organized': 0,
            'duplicates_found': 0,
            'duplicates_deleted': 0,
            'categories': {}
        }
    
    def get_file_category(self, file_extension):
        """Determine file category based on extension"""
        for category, extensions in self.FILE_CATEGORIES.items():
            if file_extension.lower() in extensions:
                return category
        return 'Others'
    
    def get_file_hash(self, file_path):
        """Calculate MD5 hash of a file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return None
    
    def find_duplicates(self):
        """Find duplicate files"""
        hashes = {}
        duplicates = []
        
        try:
            for file_path in self.folder_path.rglob('*'):
                if file_path.is_file():
                    file_hash = self.get_file_hash(file_path)
                    
                    if file_hash:
                        if file_hash in hashes:
                            duplicates.append({
                                'original': hashes[file_hash],
                                'duplicate': file_path
                            })
                        else:
                            hashes[file_hash] = file_path
            
            self.duplicates = duplicates
            logger.info(f"Found {len(duplicates)} duplicate files")
            return duplicates
        except Exception as e:
            logger.error(f"Error finding duplicates: {e}")
            return []
    
    def delete_duplicates(self):
        """Delete duplicate files"""
        deleted_count = 0
        try:
            for dup in self.duplicates:
                dup_path = dup['duplicate']
                try:
                    dup_path.unlink()
                    logger.info(f"Deleted duplicate: {dup_path}")
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete {dup_path}: {e}")
            
            self.report['duplicates_deleted'] = deleted_count
            return deleted_count
        except Exception as e:
            logger.error(f"Error deleting duplicates: {e}")
            return 0
    
    def clean_filename(self, filename):
        """Clean and standardize filename"""
        # Remove special characters, keep only alphanumeric, spaces, dashes, underscores
        name, ext = os.path.splitext(filename)
        clean_name = ''.join(c if c.isalnum() or c in ' -_' else '' for c in name)
        clean_name = clean_name.strip()
        if not clean_name:
            clean_name = 'file'
        return clean_name + ext
    
    def organize_files(self, rename=True, delete_dups=True):
        """Main function to organize files"""
        try:
            logger.info(f"Starting file organization in {self.folder_path}")
            
            if not self.folder_path.exists():
                logger.error(f"Folder not found: {self.folder_path}")
                return False
            
            # Find and delete duplicates
            if delete_dups:
                self.find_duplicates()
                self.report['duplicates_found'] = len(self.duplicates)
                self.delete_duplicates()
            
            # Create category folders and organize files
            for file_path in list(self.folder_path.glob('*')):
                if file_path.is_file():
                    # Get category
                    category = self.get_file_category(file_path.suffix)
                    
                    # Create category folder
                    category_folder = self.folder_path / category
                    category_folder.mkdir(exist_ok=True)
                    
                    # Clean filename if needed
                    new_filename = self.clean_filename(file_path.name) if rename else file_path.name
                    new_path = category_folder / new_filename
                    
                    # Handle name conflicts
                    counter = 1
                    original_stem = Path(new_filename).stem
                    original_suffix = Path(new_filename).suffix
                    
                    while new_path.exists():
                        new_filename = f"{original_stem}_{counter}{original_suffix}"
                        new_path = category_folder / new_filename
                        counter += 1
                    
                    # Move file
                    try:
                        shutil.move(str(file_path), str(new_path))
                        logger.info(f"Organized: {file_path.name} -> {category}/{new_filename}")
                        self.organized_count += 1
                        
                        if category not in self.report['categories']:
                            self.report['categories'][category] = 0
                        self.report['categories'][category] += 1
                    except Exception as e:
                        logger.error(f"Failed to move {file_path}: {e}")
            
            self.report['files_organized'] = self.organized_count
            logger.info(f"File organization completed. {self.organized_count} files organized")
            return True
        
        except Exception as e:
            logger.error(f"Error organizing files: {e}")
            return False
    
    def generate_report(self):
        """Generate and save organization report"""
        try:
            report_path = Path('reports') / f"organization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(report_path, 'w') as f:
                f.write("="*60 + "\n")
                f.write("FILE ORGANIZATION REPORT\n")
                f.write("="*60 + "\n\n")
                f.write(f"Timestamp: {self.report['timestamp']}\n")
                f.write(f"Folder: {self.report['folder']}\n\n")
                f.write(f"Files Organized: {self.report['files_organized']}\n")
                f.write(f"Duplicates Found: {self.report['duplicates_found']}\n")
                f.write(f"Duplicates Deleted: {self.report['duplicates_deleted']}\n\n")
                
                f.write("Files by Category:\n")
                f.write("-"*60 + "\n")
                for category, count in self.report['categories'].items():
                    f.write(f"  {category}: {count} files\n")
                
                f.write("\n" + "="*60 + "\n")
            
            logger.info(f"Report saved to {report_path}")
            print(f"📄 Report saved to: {report_path}")
            return report_path
        
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return None
    
    def display_summary(self):
        """Display organization summary"""
        print("\n" + "="*50)
        print("    FILE ORGANIZATION COMPLETE")
        print("="*50)
        print(f"Files Organized: {self.organized_count}")
        print(f"Duplicates Found: {len(self.duplicates)}")
        print(f"\nFiles by Category:")
        for category, count in self.report['categories'].items():
            print(f"  • {category}: {count}")
        print("="*50 + "\n")
