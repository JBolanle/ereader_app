"""Custom exceptions for the e-reader application.

This module defines the exception hierarchy for all e-reader errors. All custom
exceptions inherit from EReaderError, allowing users to catch all application
errors with a single except clause.

Example:
    >>> try:
    ...     book = EPUBBook("invalid.epub")
    ... except EReaderError as e:
    ...     print(f"Error opening book: {e}")
"""


class EReaderError(Exception):
    """Base exception for all e-reader application errors.

    All custom exceptions in the e-reader application inherit from this class.
    This allows users to catch any application-specific error with a single
    except clause.

    The error message can be accessed via str(exception) or exception.args[0].
    """

    pass


class InvalidEPUBError(EReaderError):
    """Raised when a file is not a valid EPUB.

    This exception is raised when attempting to open a file that does not
    conform to the EPUB specification. Common causes include:
    - File is not a ZIP archive
    - Missing required files (META-INF/container.xml)
    - File extension is .epub but content is not EPUB format

    Example:
        >>> if not zipfile.is_zipfile(filepath):
        ...     raise InvalidEPUBError(f"{filepath} is not a valid ZIP archive")
    """

    pass


class CorruptedEPUBError(EReaderError):
    """Raised when an EPUB file is damaged or incomplete.

    This exception is raised when an EPUB file exists and appears to be in
    the correct format, but is corrupted or incomplete. Common causes include:
    - Incomplete download (truncated file)
    - Disk corruption
    - Missing entries in the ZIP archive
    - Malformed XML that cannot be parsed

    Example:
        >>> try:
        ...     tree = ET.fromstring(xml_content)
        ... except ET.ParseError as e:
        ...     raise CorruptedEPUBError(f"Malformed XML in {filename}: {e}")
    """

    pass


class UnsupportedEPUBError(EReaderError):
    """Raised when an EPUB format or feature is not supported.

    This exception is raised when an EPUB file is valid but uses features or
    formats that are not yet supported by the application. Common causes include:
    - DRM-protected EPUB files
    - Unsupported EPUB version (e.g., EPUB 1.0)
    - Required features not yet implemented

    Example:
        >>> if has_drm(epub_file):
        ...     raise UnsupportedEPUBError("DRM-protected EPUBs are not supported")
    """

    pass
