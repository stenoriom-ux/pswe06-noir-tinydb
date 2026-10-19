"""NOIR acceptance tests for atomic JSONStorage writes."""

import json

import pytest

from tinydb.storages import JSONStorage


def test_hu1_fsync_failure_preserves_original(tmp_path, monkeypatch):
    """A synchronization failure must not overwrite the committed JSON."""
    path = tmp_path / 'db.json'
    old = {'_default': {'1': {'value': 'previous committed value'}}}
    path.write_text(json.dumps(old), encoding='utf-8')
    before = path.read_bytes()
    storage = JSONStorage(path, encoding='utf-8')

    def fail_sync(_fd):
        raise OSError('injected synchronization failure')

    monkeypatch.setattr('tinydb.storages.os.fsync', fail_sync)
    try:
        with pytest.raises(OSError, match='injected synchronization failure'):
            storage.write({'_default': {'1': {'value': 'new'}}})
    finally:
        storage.close()

    assert path.read_bytes() == before
    reopened = JSONStorage(path, encoding='utf-8')
    try:
        assert reopened.read() == old
    finally:
        reopened.close()
