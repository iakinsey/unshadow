import json
import os
import sys
import shutil

from unshadow import config
from unshadow.dispatch import Manager
from unshadow.worker.fetcher import Fetcher
from unshadow.worker.parser import LinkExtractor
from unshadow.worker.frontier import Frontier
from unshadow.worker.language_analyzer import LanguageAnalyzer
from unshadow.server.metric import MetricServer


def apply_configs(config_file):
    with open(config_file, 'r') as f:
        config_mapper = json.loads(f.read())

    for key, value in config_mapper.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            err = 'No such configuration value "{}"'.format(key)
            raise NameError(err)


def create_data_dir():
    try:
        os.makedirs(config.DATA_DIR)
    except FileExistsError:
        pass


def reclaim_files(*directories):
    for directory in directories:
        if os.path.exists(directory):
            for file_name in os.listdir(directory):
                if file_name.endswith(".claimed"):
                    new_file_name = file_name.replace(".claimed", "")
                    old_file_path = os.path.join(directory, file_name)
                    new_file_path = os.path.join(directory, new_file_name)

                    shutil.move(old_file_path, new_file_path)

def start_metrics():
    manager = Manager(
        config.MANAGER_POLL_DELAY_MS,
        config.PROCESS_DEATH_FOLDER
    )

    manager.add_worker(
        'metric_server',
        MetricServer,
        1,
        config.METRIC_SERVER_HTTP_HOST,
        config.METRIC_SERVER_HTTP_PORT,
        config.METRIC_SERVER_DB_HOST,
        config.METRIC_SERVER_DB_PORT,
        config.METRIC_SERVER_DB_USER,
        config.METRIC_SERVER_DB_NAME,
        config.METRIC_SERVER_DB_PASS
    )

    manager.start()


def start_crawler(config_file=None):
    if config_file:
        apply_configs(config_file)

    create_data_dir()

    reclaim_files(
        config.FETCHER_INBOX,
        config.EXTRACTOR_INBOX,
        config.EXTRACTOR_OUTBOX,
        config.FRONTIER_INBOX,
        config.LANGUAGE_ANALYZER_INBOX
    )

    manager = Manager(
        config.MANAGER_POLL_DELAY_MS,
        config.PROCESS_DEATH_FOLDER
    )

    metric_args = {
        "db_name": config.METRIC_SERVER_DB_NAME,
        "db_user": config.METRIC_SERVER_DB_USER,
        "db_pass": config.METRIC_SERVER_DB_PASS,
        "db_host": config.METRIC_SERVER_DB_HOST,
        "db_port": config.METRIC_SERVER_DB_PORT
    }

    manager.add_worker(
        'fetcher',
        Fetcher,
        config.FETCHER_WORKER_COUNT,
        config.FETCHER_INBOX,
        None,
        config.FETCHER_INBOX_REGEX,
        config.FETCHER_MAX_ITERATIONS,
        config.PROCESS_DEATH_FOLDER,
        config.FETCHER_MAX_POLL_DELAY_MS,
        config.FETCHER_OUTBOX_MAX_SIZE,
        metric_args,
        user_agent=config.FETCHER_USER_AGENT,
        max_size=config.FETCHER_MAX_CONTENT_SIZE,
        enable_proxy=config.FETCHER_SOCKS5_PROXY_ENABLED,
        proxy_host=config.FETCHER_SOCKS5_PROXY_HOST,
        proxy_port=config.FETCHER_SOCKS5_PROXY_PORT,
        content_folder=config.FETCHER_CONTENT_FOLDER,
        outboxes=config.FETCHER_OUTBOXES,
    )

    manager.add_worker(
        'link_extractor',
        LinkExtractor,
        config.EXTRACTOR_WORKER_COUNT,
        config.EXTRACTOR_INBOX,
        config.EXTRACTOR_OUTBOX,
        config.INBOX_REGEX,
        config.EXTRACTOR_MAX_ITERATIONS,
        config.PROCESS_DEATH_FOLDER,
        config.EXTRACTOR_MAX_POLL_DELAY_MS,
        config.EXTRACTOR_OUTBOX_MAX_SIZE,
        metric_args,
    )

    manager.add_worker(
        'frontier',
        Frontier,
        config.FRONTIER_WORKER_COUNT,
        config.FRONTIER_INBOX,
        config.FRONTIER_OUTBOX,
        config.INBOX_REGEX,
        config.FRONTIER_MAX_ITERATIONS,
        config.PROCESS_DEATH_FOLDER,
        config.FRONTIER_MAX_POLL_DELAY_MS,
        config.FRONTIER_OUTBOX_MAX_SIZE,
        metric_args,
        db_name=config.FRONTIER_DB_NAME,
        db_user=config.FRONTIER_DB_USER,
        db_pass=config.FRONTIER_DB_PASS,
        db_host=config.FRONTIER_DB_HOST,
        db_port=config.FRONTIER_DB_PORT
    )

    manager.add_worker(
        'language_analyzer',
        LanguageAnalyzer,
        config.LANGUAGE_ANALYZER_WORKER_COUNT,
        config.LANGUAGE_ANALYZER_INBOX,
        config.LANGUAGE_ANALYZER_OUTBOX,
        config.INBOX_REGEX,
        config.LANGUAGE_ANALYZER_MAX_ITERATIONS,
        config.PROCESS_DEATH_FOLDER,
        config.LANGUAGE_ANALYZER_MAX_POLL_DELAY_MS,
        config.LANGUAGE_ANALYZER_OUTBOX_MAX_SIZE,
        metric_args,
        tf_limit=config.LANGUAGE_ANALYZER_TF_LIMIT,
        db_name=config.LANGUAGE_ANALYZER_DB_NAME,
        db_user=config.LANGUAGE_ANALYZER_DB_USER,
        db_pass=config.LANGUAGE_ANALYZER_DB_PASS,
        db_host=config.LANGUAGE_ANALYZER_DB_HOST,
        db_port=config.LANGUAGE_ANALYZER_DB_PORT
    )

    manager.start()
