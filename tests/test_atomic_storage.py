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


@pytest.mark.parametrize('new', [{}, {'_default': {'1': {'value': 'x' * 500}}}])
def test_hu2_success_reopens_new_state(tmp_path, new):
    path = tmp_path / 'db.json'
    storage = JSONStorage(path, encoding='utf-8')
    storage.write({'_default': {'1': {'value': 'old'}}})
    storage.write(new)
    assert storage.read() == new
    storage.close()
    reopened = JSONStorage(path, encoding='utf-8')
    try:
        assert reopened.read() == new
    finally:
        reopened.close()
    assert list(tmp_path.iterdir()) == [path]


def test_hu3_replace_failure_cleans_temp_and_allows_retry(tmp_path, monkeypatch):
    path = tmp_path / 'db.json'
    old = {'_default': {'1': {'value': 'old'}}}
    path.write_text(json.dumps(old), encoding='utf-8')
    before = path.read_bytes()
    storage = JSONStorage(path, encoding='utf-8')

    def fail_replace(source, destination):
        assert source != destination
        assert json.loads(open(source, encoding='utf-8').read()) != old
        raise OSError('injected replacement failure')

    with monkeypatch.context() as patch:
        patch.setattr('tinydb.storages.os.replace', fail_replace)
        try:
            with pytest.raises(OSError, match='injected replacement failure'):
                storage.write({'_default': {'1': {'value': 'new'}}})
            assert path.read_bytes() == before
            assert storage.read() == old
            assert list(tmp_path.iterdir()) == [path]
        finally:
            if path.read_bytes() != before:
                storage.close()

    storage.write({'_default': {}})
    storage.close()
    assert json.loads(path.read_text(encoding='utf-8')) == {'_default': {}}
    assert list(tmp_path.iterdir()) == [path]


def test_hu3_sync_failure_cleans_temp(tmp_path, monkeypatch):
    path = tmp_path / 'db.json'
    path.write_text('{}', encoding='utf-8')
    storage = JSONStorage(path)

    def fail_sync(_fd):
        raise OSError('injected synchronization failure')

    monkeypatch.setattr('tinydb.storages.os.fsync', fail_sync)
    try:
        with pytest.raises(OSError, match='injected synchronization failure'):
            storage.write({'_default': {}})
        assert list(tmp_path.iterdir()) == [path]
    finally:
        storage.close()


def test_atomic_serialization_error_preserves_original(tmp_path):
    path = tmp_path / 'db.json'
    path.write_text('{}', encoding='utf-8')
    storage = JSONStorage(path)
    try:
        with pytest.raises(TypeError):
            storage.write({'not_json': object()})
        assert path.read_bytes() == b'{}'
        assert list(tmp_path.iterdir()) == [path]
    finally:
        storage.close()


def test_atomic_preserves_permissions(tmp_path):
    path = tmp_path / 'db.json'
    path.write_text('{}', encoding='utf-8')
    path.chmod(0o640)
    storage = JSONStorage(path)
    try:
        storage.write({'_default': {}})
    finally:
        storage.close()
    assert path.stat().st_mode & 0o777 == 0o640
