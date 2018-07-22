import grp
import os
import pwd
from fnmatch import fnmatch

from . import ActionError, FileAction
from ..constants import FLAGS


class Find(FileAction):
    def __init__(
        self, path, min_depth=None, max_depth=None, types=None, patterns=None, aliases=True,
        **kwargs
    ):
        self.path = path
        self.min_depth = min_depth
        self.max_depth = max_depth
        self.types = types
        self.patterns = patterns
        self.aliases = aliases
        super().__init__(**kwargs)

    def process(self):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(self.path)

        # Check that the path exists
        if not os.path.isdir(path):
            raise ActionError('unable to find a directory with the path provided')

        # Find all the paths with the filters provided and return them to the user
        paths = self.walk(
            path, path.count(os.sep), self.mode, self.owner, self.group, self.flags,
            self.min_depth, self.max_depth, self.types, self.patterns, self.aliases
        )
        return self.ok(paths=paths)

    def walk(
        self, path, root_depth, mode=None, owner=None, group=None, flags=None, min_depth=None,
        max_depth=None, types=None, patterns=None, aliases=True
    ):
        # Only import PyObjC libraries if necessary (as they take time)
        if aliases:
            from Foundation import NSURL, NSURLIsAliasFileKey  # pylint: disable=no-name-in-module

        # Create a list to store all the files found
        paths = []

        # Walk through the base path provided using scandir (for speed)
        for item in os.scandir(path):
            # Determine the current depth
            depth = item.path.count(os.sep) - root_depth

            # Impose a maximum depth
            if max_depth and depth > max_depth:
                continue

            # Determine the file type if a type filter is requested
            if types:
                if item.is_dir():
                    file_type = 'directory'
                elif item.is_symlink():
                    file_type = 'symlink'
                elif aliases:
                    # Determine if the file is an alias
                    url = NSURL.fileURLWithPath_(item.path)
                    ok, is_alias, _error = url.getResourceValue_forKey_error_(
                        None, NSURLIsAliasFileKey, None
                    )
                    file_type = 'alias' if ok and is_alias else 'file'
                else:
                    file_type = 'file'

            # Determine the mode, owner, group and flags if requested
            if mode or owner or group or flags:
                if mode:
                    mode_bin = int(mode, 8)

                if owner:
                    try:
                        uid = pwd.getpwnam(owner).pw_uid
                    except KeyError:
                        raise ActionError('the owner requested was not found')

                if group:
                    try:
                        gid = grp.getgrnam(group).gr_gid
                    except KeyError:
                        raise ActionError('the group requested was not found')

                if flags:
                    flags_bin = 0
                    for flag in flags:
                        if flag not in FLAGS:
                            raise ActionError('the specified flag is unsupported')
                        flags_bin |= FLAGS[flag]

                stat = os.stat(item.path, follow_symlinks=False)

            # Determine if the current item should be added to our paths list based on filters
            if (
                (not min_depth or depth >= min_depth) and
                (not types or file_type in types) and
                (not patterns or any(fnmatch(item.path, p) for p in patterns)) and
                (not mode or stat.st_mode == mode_bin) and
                (not owner or stat.st_uid == uid) and
                (not group or stat.st_gid == gid) and
                (not flags or stat.st_flags & flags_bin)
            ):
                paths.append(item.path)

            # Recurse through directories
            if item.is_dir() and not item.is_symlink():
                paths.extend(self.walk(
                    item.path, root_depth, mode, owner, group, flags, min_depth, max_depth,
                    types, patterns, aliases
                ))

        return paths
