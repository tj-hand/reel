"""Reel module configuration"""

from pydantic_settings import BaseSettings


class ReelConfig(BaseSettings):
    """Configuration for Reel module"""

    # Pagination limits
    max_page_size: int = 100
    default_page_size: int = 50

    # Export limits
    max_export_records: int = 10000

    # Retention settings (0 = infinite retention)
    retention_days: int = 0

    # Performance settings
    batch_insert_size: int = 100

    class Config:
        env_prefix = "REEL_"


# Global config instance
reel_config = ReelConfig()
