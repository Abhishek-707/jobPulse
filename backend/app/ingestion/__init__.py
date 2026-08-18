# Ingestion module exports
from .base import JobSource, RawJob, SourceAdapter
from .normalizer import JobNormalizer
from .validator import JobValidator
from .deduplicator import JobDeduplicator

__all__ = [
    "JobSource",
    "RawJob",
    "SourceAdapter",
    "JobNormalizer",
    "JobValidator",
    "JobDeduplicator",
]
