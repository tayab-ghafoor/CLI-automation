"""
Custom exceptions for System Manager CLI
"""


class CliException(Exception):
    """Base exception for CLI application"""
    pass


class ConfigurationError(CliException):
    """Raised when configuration is invalid or missing"""
    pass


class PathError(CliException):
    """Raised when there are issues with file paths"""
    pass


class PermissionError(CliException):
    """Raised when there are permission issues"""
    pass


class BackupError(CliException):
    """Raised when backup operations fail"""
    pass


class FileOrganizationError(CliException):
    """Raised when file organization fails"""
    pass


class DiskSpaceError(CliException):
    """Raised when there's insufficient disk space"""
    pass


class LogAnalysisError(CliException):
    """Raised when log analysis fails"""
    pass


class HealthMonitorError(CliException):
    """Raised when health monitoring fails"""
    pass
