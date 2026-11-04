# -*- coding: utf-8 -*-

import uuid
import redis_lock
from decorator import decorator


class MutexException(Exception):
    pass


class NotLockedMutexException(MutexException):
    pass


class LocksBackend(object):
    def get_lock(self, lock_name, expire, holder_id):
        pass

    def check_locks_beginning_with(self, name):
        pass

    def acquire_lock(self, lock, blocking, timeout):
        pass

    def release_lock(self, lock):
        pass

    def refresh_lock(self, lock, expire):
        pass


class RedisLockBackend(LocksBackend):
    def __init__(self, redis_client):
        self.redis_client = redis_client

    def get_lock(self, lock_name, expire, holder_id):
        if holder_id is None:
            holder_id = str(uuid.uuid4())
        holder_id = str(holder_id).encode("utf-8")
        return redis_lock.Lock(self.redis_client, lock_name, expire=expire, id=holder_id)

    def check_locks_beginning_with(self, name):
        found_keys = self.redis_client.keys("lock:" + name + "*")
        return [found_key.replace("lock:", "") for found_key in found_keys]

    def acquire_lock(self, lock, blocking, timeout):
        lock.acquire(blocking=blocking, timeout=timeout)

    def release_lock(self, lock):
        try:
            lock.release()
        except redis_lock.NotAcquired:
            raise NotLockedMutexException("Lock is not acquired or already expired")

    def refresh_lock(self, lock, expire):
        try:
            lock.extend(expire=expire)
        except redis_lock.NotAcquired:
            raise NotLockedMutexException("Lock is not acquired or already expired")


@decorator
def tree_lock(func, locks_backend=None, nodes_names=None, expire=30, holder_id=None, timeout=0, *args, **kwargs):
    with TreeLock(locks_backend, nodes_names, expire, holder_id, timeout):
        return func(*args, **kwargs)


class TreeLock(object):
    def __init__(self, locks_backend, nodes_names, expire=30, holder_id=None, timeout=0):
        if not locks_backend:
            raise ValueError("locks_backend is mandatory")
        self.locks_backend = locks_backend
        if not nodes_names:
            raise ValueError("nodes_names cannot be empty")
        self.nodes_names = nodes_names
        self.expire = expire
        self.holder_id = holder_id
        self.timeout = timeout
        self.real_lock = None

    def acquire(self):
        cumulative_locks_names = self._generate_cumulative_locks_names(self.nodes_names)
        parent_locks_names, lock_name = (
            cumulative_locks_names[:-1],
            cumulative_locks_names[-1],
        )
        parent_locks = self._acquire_parent_locks(parent_locks_names)
        try:
            self._check_no_childs_lock(lock_name)
            self.real_lock = self._acquire_real_lock(lock_name)
            self.holder_id = self.real_lock.id
            return self
        finally:
            for lock in parent_locks:
                lock.release()

    def release(self):
        if self.real_lock:
            self.locks_backend.release_lock(self.real_lock)
        else:
            raise NotLockedMutexException("Lock is not acquired.")

    def refresh(self, expire=None):
        if self.real_lock:
            expire = expire or self.expire
            self.locks_backend.refresh_lock(self.real_lock, expire=expire)
        else:
            raise NotLockedMutexException("Lock is not acquired.")

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

    @staticmethod
    def _generate_cumulative_locks_names(nodes_names):
        cumulative_names = nodes_names[:1]
        for node_name in nodes_names[1:]:
            cumulative_names.append(cumulative_names[-1] + ";" + node_name)
        cumulative_names = [name + ";" for name in cumulative_names]
        return cumulative_names

    def _acquire_parent_locks(self, parent_locks_names):
        try:
            parent_locks = []
            for key in parent_locks_names:
                expire_time = self.timeout + 5
                lock = self.locks_backend.get_lock(key, expire=expire_time, holder_id=self.holder_id)
                if lock.acquire(blocking=False):
                    parent_locks.append(lock)
                else:
                    raise MutexException("Lock not available because '{}' is locked".format(key))
            return parent_locks
        except Exception:
            for lock in parent_locks:
                lock.release()
            raise

    def _check_no_childs_lock(self, lock_name):
        found_keys = self.locks_backend.check_locks_beginning_with(lock_name)
        if found_keys:
            raise MutexException("Lock not available because {} are locked".format(found_keys))

    def _acquire_real_lock(self, lock_name):
        real_lock = self.locks_backend.get_lock(lock_name, expire=self.expire, holder_id=self.holder_id)
        blocking = self.timeout != 0
        timeout = self.timeout or None
        self.locks_backend.acquire_lock(real_lock, blocking=blocking, timeout=timeout)
        return real_lock
