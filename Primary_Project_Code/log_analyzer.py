import re
import csv
from pathlib import Path
from datetime import datetime
from .logger import get_logger

logger = get_logger(__name__, 'log_analyzer.log')

class LogAnalyzer:
    """Analyze system log files"""
    
    def __init__(self, log_file_path=None):
        self.log_file_path = Path(log_file_path) if log_file_path else None
        self.errors = []
        self.failed_logins = []
        self.warnings = []
        self.info_logs = []
    
    def analyze_log_file(self, log_file_path):
        """Analyze a single log file"""
        try:
            self.log_file_path = Path(log_file_path)
            
            if not self.log_file_path.exists():
                logger.error(f"Log file not found: {log_file_path}")
                return False
            
            logger.info(f"Analyzing log file: {log_file_path}")
            
            with open(self.log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            self._parse_logs(lines)
            logger.info(f"Log analysis completed. Found {len(self.errors)} errors, {len(self.failed_logins)} failed logins")
            
            return True
        
        except Exception as e:
            logger.error(f"Error analyzing log file: {e}")
            return False
    
    def analyze_folder(self, folder_path):
        """Analyze all log files in a folder"""
        try:
            folder = Path(folder_path)
            
            if not folder.exists():
                logger.error(f"Folder not found: {folder_path}")
                return False
            
            logger.info(f"Analyzing logs in folder: {folder_path}")
            
            # Find all log files
            log_files = list(folder.glob('*.log')) + list(folder.glob('*.txt'))
            
            if not log_files:
                logger.warning(f"No log files found in {folder_path}")
                return False
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    self._parse_logs(lines, str(log_file))
                except Exception as e:
                    logger.error(f"Error reading {log_file}: {e}")
            
            logger.info(f"Folder analysis completed. Found {len(self.errors)} errors, {len(self.failed_logins)} failed logins")
            return True
        
        except Exception as e:
            logger.error(f"Error analyzing folder: {e}")
            return False
    
    def _parse_logs(self, lines, source="log"):
        """Parse log lines and extract relevant information"""
        
        error_patterns = [
            r'ERROR',
            r'CRITICAL',
            r'FATAL',
            r'Exception',
            r'Traceback',
            r'Failed',
            r'error'
        ]
        
        failed_login_patterns = [
            r'(?:Authentication failed|Login failed|Invalid credentials|Access denied)',
            r'(?:Failed password|Failed publickey)',
            r'(?:Invalid user|Unknown user)',
            r'(?:Connection closed|Connection reset)',
            r'failed'
        ]
        
        for idx, line in enumerate(lines, 1):
            # Check for errors
            if any(re.search(pattern, line) for pattern in error_patterns):
                self.errors.append({
                    'source': source,
                    'line_number': idx,
                    'message': line.strip()
                })
            
            # Check for failed logins
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in failed_login_patterns):
                self.failed_logins.append({
                    'source': source,
                    'line_number': idx,
                    'message': line.strip()
                })
            
            # Check for warnings
            if re.search(r'WARNING|WARN', line):
                self.warnings.append({
                    'source': source,
                    'line_number': idx,
                    'message': line.strip()
                })
    
    def get_summary(self):
        """Get analysis summary"""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'total_failed_logins': len(self.failed_logins),
            'source_file': str(self.log_file_path) if self.log_file_path else 'Multiple files'
        }
    
    def export_to_csv(self, output_file=None):
        """Export analysis results to CSV"""
        try:
            if output_file is None:
                output_file = f"log_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            output_path = Path('reports') / output_file
            output_path.parent.mkdir(exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['ANALYSIS SUMMARY'])
                writer.writerow(['Timestamp', self.get_summary()['timestamp']])
                writer.writerow(['Total Errors', len(self.errors)])
                writer.writerow(['Total Warnings', len(self.warnings)])
                writer.writerow(['Total Failed Logins', len(self.failed_logins)])
                writer.writerow([])
                
                # Write errors
                if self.errors:
                    writer.writerow(['ERRORS'])
                    writer.writerow(['Source', 'Line Number', 'Message'])
                    for error in self.errors:
                        writer.writerow([error['source'], error['line_number'], error['message']])
                    writer.writerow([])
                
                # Write warnings
                if self.warnings:
                    writer.writerow(['WARNINGS'])
                    writer.writerow(['Source', 'Line Number', 'Message'])
                    for warning in self.warnings:
                        writer.writerow([warning['source'], warning['line_number'], warning['message']])
                    writer.writerow([])
                
                # Write failed logins
                if self.failed_logins:
                    writer.writerow(['FAILED LOGINS'])
                    writer.writerow(['Source', 'Line Number', 'Message'])
                    for login in self.failed_logins:
                        writer.writerow([login['source'], login['line_number'], login['message']])
            
            logger.info(f"CSV report exported to {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return None
    
    def display_summary(self):
        """Display analysis summary"""
        summary = self.get_summary()
        
        print("\n" + "="*50)
        print("    LOG ANALYSIS REPORT")
        print("="*50)
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Source: {summary['source_file']}")
        print(f"\nErrors Found: {summary['total_errors']}")
        print(f"Warnings Found: {summary['total_warnings']}")
        print(f"Failed Logins: {summary['total_failed_logins']}")
        
        if self.errors:
            print("\nTop 5 Errors:")
            for error in self.errors[:5]:
                print(f"  • [{error['source']}:{error['line_number']}] {error['message'][:80]}")
        
        if self.failed_logins:
            print("\nTop 5 Failed Logins:")
            for login in self.failed_logins[:5]:
                print(f"  • [{login['source']}:{login['line_number']}] {login['message'][:80]}")
        
        print("="*50 + "\n")
