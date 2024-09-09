import json
import urllib.request
from datetime import timedelta, datetime
import urllib.error
import time
from functools import wraps
import os.path
import pickle
import logging
from filelock import FileLock

institution_url = "https://topology-institutions.osg-htc.org/api/institution_ids"
cache_file_path = '/tmp/institutions_cache.pkl'
cache_lock_path = '/tmp/institutions_cache.pkl.lock'
cache_duration = timedelta(days=1)


def check_cache(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self._is_cache_valid():
            self.update_cache()
        return func(self, *args, **kwargs)

    return wrapper


class Institutions:

    def __init__(self):
        self._institutions = {}
        self._cache_timestamp = None
        self.load_cache()

    @property
    def institutions(self):
        if not self._is_cache_valid():
            self.update_cache()
        return self._institutions

    @staticmethod
    def _parse_institutions(institutions: list):
        return {inst['id']: inst for inst in institutions}

    @check_cache
    def __getitem__(self, institution_id):
        return self._institutions[institution_id]

    @check_cache
    def get(self, key, default=None):
        return self._institutions.get(key, default)

    def load_cache(self):
        with FileLock(cache_lock_path):
            if os.path.exists(cache_file_path):
                with open(cache_file_path, 'rb') as cache_file:
                    cache_data = pickle.load(cache_file)
                    cache_timestamp = cache_data['timestamp']
                    if datetime.now() - cache_timestamp < cache_duration:
                        self._institutions = cache_data['data']
                        return

    def update_cache(self):
        try:
            with urllib.request.urlopen(institution_url) as response:
                data = json.loads(response.read().decode())
                parsed_data = self._parse_institutions(data)
                self._institutions = parsed_data
                with FileLock(cache_lock_path):
                    with open(cache_file_path, 'wb') as cache_file:
                        pickle.dump({'timestamp': datetime.now(), 'data': self._institutions}, cache_file)
        except urllib.error.URLError as e:
            logging.error(f"Failed to fetch institution data: {e}")

    def _is_cache_valid(self):

        # Check if cache file time is in memory
        if self._cache_timestamp is not None:
            return datetime.now() - self._cache_timestamp < cache_duration

        with FileLock(cache_lock_path):
            if os.path.exists(cache_file_path):
                with open(cache_file_path, 'rb') as cache_file:
                    cache_data = pickle.load(cache_file)
                    self._cache_timestamp = cache_data['timestamp']
                    return datetime.now() - self._cache_timestamp < cache_duration

        return False
