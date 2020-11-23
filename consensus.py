# Number of "satoshis" per Bitcoin
COIN = 100_000_000

# Number of blocks between subsidy halvings
HALVING_INTERVAL = 210_000

# The maximum allowed size for a serialized block, in bytes (only for buffer size limits)
MAX_BLOCK_SERIALIZED_SIZE = 4000000

# The maximum allowed weight for a block, see BIP 141 (network rule)
MAX_BLOCK_WEIGHT = 4000000

DEFAULT_BLOCK_MIN_TX_FEE = 1000

# The maximum allowed number of signature check operations in a block (network rule)
MAX_BLOCK_SIGOPS_COST = 80000

# Coinbase transaction outputs can only be spent after this number of new blocks (network rule) */
COINBASE_MATURITY = 100

WITNESS_SCALE_FACTOR = 4

# 60 is the lower bound for the size of a valid serialized CTransaction
MIN_TRANSACTION_WEIGHT = WITNESS_SCALE_FACTOR * 60

# 10 is the lower bound for the size of a serialized CTransaction
MIN_SERIALIZABLE_TRANSACTION_WEIGHT = WITNESS_SCALE_FACTOR * 10

# Flags for nSequence and nLockTime locks
# Interpret sequence numbers as relative lock-time constraints.
LOCKTIME_VERIFY_SEQUENCE = int(1 << 0)
# Use GetMedianTimePast() instead of nTime for end point timestamp.
LOCKTIME_MEDIAN_TIME_PAST = int(1 << 1)
