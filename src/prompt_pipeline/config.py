"""Model configuration and constants."""

# Model IDs for different pipeline phases
HAIKU_MODEL = "claude-haiku-4-5-20251001"  # classify, expand
SONNET_MODEL = "claude-sonnet-4-5-20250929"  # restyle

# Default token limits
MAX_TOKENS_CLASSIFY = 1024
MAX_TOKENS_EXPAND = 4096
MAX_TOKENS_RESTYLE = 16000
