import subprocess
from collections import UserDict


class ReversibleDict(UserDict):
    """
    A dict which maintains a reverse mapping between values and keys for easy reverse lookups.
    """

    def __init__(self, *args, **kwargs):
        self.reversed_data = {}
        super().__init__(*args, **kwargs)

    def __delitem__(self, key):
        value = self.data[key]
        del self.reversed_data[value]
        super().__delitem__(key)

    def __setitem__(self, key, value):
        if value in self.data.values():
            raise ValueError('all values in this data structure must be unique')

        super().__setitem__(key, value)
        self.reversed_data[value] = key

    def lookup(self, value):
        return self.reversed_data[value]


def deep_equal(source, destination):
    """
    Deeply compares the source dict against the destination ensuring that all items contained
    in the source are also in and equal to the destination.

    :param source: The source master dictionary to be used as a reference in the comparison
    :param destination: The destination dictionary to compare against the source.

    :return: a boolean indicating whether the source is contained in the destination
    """
    if isinstance(source, dict) and isinstance(destination, dict):
        for key, value in source.items():
            if not deep_equal(value, destination.get(key)):
                return False

        return True
    else:
        return source == destination


def deep_merge(source, destination):
    """
    Deep merges the source dict into the destination.

    :param source: The source dict to merge into the destination.
    :param destination: The destination dict to merge the source into.

    :return: the destination dict is returned (required for recursion) but the destination
             dict will be updated too
    """
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            destination[key] = deep_merge(value, node)
        else:
            destination[key] = value

    return destination


def batch(items, batch_size):
    """
    Batches up a list into multiple lists which each are of the requested batch size;

    :param items: the list of items to be batched
    :param batch_size: the size of each batch
    """
    length = len(items)
    for index in range(0, length, batch_size):
        yield items[index:min(index + batch_size, length)]


def generate_uuid():
    """Generate a UUID using uuidgen."""
    return subprocess.check_output('/usr/bin/uuidgen', encoding='utf-8').rstrip()
