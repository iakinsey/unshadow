import logging
import multiprocessing
import os
import re


###############################################################################
# Misc
###############################################################################


NUM_CPUS = multiprocessing.cpu_count()
DEFAULT_OUTBOX_MAX_SIZE = 450
DEFAULT_MAX_ITERATIONS = 100
DEFAULT_MAX_POLL_DELAY_MS = 5000


###############################################################################
# Project path configuration
###############################################################################


PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
INBOX_REGEX = re.compile(r'^[A-z]+_[0-9]+_[0-9]+_[0-9]+$')
in_data = lambda *a: os.path.join(DATA_DIR, *a)


###############################################################################
# Logging
###############################################################################


LOG_LEVEL = logging.DEBUG
LOG_PATH = None #  in_data('unshadow.log')


###############################################################################
# Process manager
###############################################################################


MANAGER_POLL_DELAY_MS = 2000
PROCESS_DEATH_FOLDER = in_data('death')


###############################################################################
# Database
###############################################################################


DB_HOST = 'localhost'
DB_PORT = 5432
DB_USER = "unshadow"
DB_PASS = ""



###############################################################################
# HTML Parser
###############################################################################


EXTRACTOR_WORKER_COUNT = NUM_CPUS
EXTRACTOR_MAX_POLL_DELAY_MS = DEFAULT_MAX_POLL_DELAY_MS
EXTRACTOR_INBOX = in_data("extractor_inbox")
EXTRACTOR_OUTBOX = in_data('extractor_outbox')
EXTRACTOR_CONTENT = in_data('extractor_content')
EXTRACTOR_MAX_ITERATIONS = DEFAULT_MAX_ITERATIONS
EXTRACTOR_OUTBOX_MAX_SIZE = DEFAULT_OUTBOX_MAX_SIZE


###############################################################################
# Frontier URL Filter
###############################################################################


ALLOWED_TLDS = [
    "onion"
]


###############################################################################
# Language Analyzer
###############################################################################


LANGUAGE_ANALYZER_WORKER_COUNT = NUM_CPUS
LANGUAGE_ANALYZER_INBOX = in_data('language_inbox')
LANGUAGE_ANALYZER_CONTENT = in_data('language_content')
LANGUAGE_ANALYZER_OUTBOX = None
LANGUAGE_ANALYZER_MAX_ITERATIONS = DEFAULT_MAX_ITERATIONS
LANGUAGE_ANALYZER_OUTBOX_MAX_SIZE = None
LANGUAGE_ANALYZER_MAX_POLL_DELAY_MS = DEFAULT_MAX_POLL_DELAY_MS
LANGUAGE_ANALYZER_TF_LIMIT = 50
LANGUAGE_ANALYZER_DB_HOST = DB_HOST
LANGUAGE_ANALYZER_DB_PORT = DB_PORT
LANGUAGE_ANALYZER_DB_USER = DB_USER
LANGUAGE_ANALYZER_DB_PASS = DB_PASS
LANGUAGE_ANALYZER_DB_NAME = "unshadow"


###############################################################################
# Link Fetcher
###############################################################################


FETCHER_WORKER_COUNT = NUM_CPUS * 32
FETCHER_MAX_POLL_DELAY_MS = DEFAULT_MAX_POLL_DELAY_MS
FETCHER_INBOX = in_data('fetcher_inbox')
FETCHER_OUTBOXES = [
    {
        "inbox": EXTRACTOR_INBOX,
        "content": EXTRACTOR_CONTENT
    },
    {
        "inbox": LANGUAGE_ANALYZER_INBOX,
        "content": LANGUAGE_ANALYZER_CONTENT
    }
]
FETCHER_OUTBOX_MAX_SIZE = DEFAULT_OUTBOX_MAX_SIZE
FETCHER_CONTENT_FOLDER = in_data('fetcher_content')
FETCHER_MAX_ITERATIONS = DEFAULT_MAX_ITERATIONS
FETCHER_USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; rv:31.0) Gecko/20100101 Firefox/31.0'
FETCHER_INBOX_REGEX = re.compile(r'^[0-9]+\-[A-z]+_[0-9]+_[0-9]+_[0-9]+$')
FETCHER_MAX_CONTENT_SIZE = 8000000
FETCHER_SOCKS5_PROXY_ENABLED = True
FETCHER_SOCKS5_PROXY_HOST = 'localhost'
FETCHER_SOCKS5_PROXY_PORT = 9050


###############################################################################
# Frontier
###############################################################################


FRONTIER_WORKER_COUNT = NUM_CPUS
FRONTIER_INBOX = EXTRACTOR_OUTBOX
FRONTIER_OUTBOX = FETCHER_INBOX
FRONTIER_MAX_ITERATIONS = DEFAULT_MAX_ITERATIONS
FRONTIER_OUTBOX_MAX_SIZE = DEFAULT_OUTBOX_MAX_SIZE
FRONTIER_MAX_POLL_DELAY_MS = DEFAULT_MAX_POLL_DELAY_MS
FRONTIER_DB_HOST = DB_HOST
FRONTIER_DB_PORT = DB_PORT
FRONTIER_DB_USER = DB_USER
FRONTIER_DB_PASS = DB_PASS
FRONTIER_DB_NAME = "unshadow"


###############################################################################
# Metrics
###############################################################################


METRIC_SERVER_HTTP_HOST = 'localhost'
METRIC_SERVER_HTTP_PORT = 8080
METRIC_SERVER_DB_HOST = DB_HOST
METRIC_SERVER_DB_PORT = DB_PORT
METRIC_SERVER_DB_USER = DB_USER
METRIC_SERVER_DB_PASS = DB_PASS
METRIC_SERVER_DB_NAME = 'unshadow'
