import hashlib
import os
import shutil

from CoreFoundation import NSURL, NSData
from Foundation import (
    NSURLBookmarkCreationSuitableForBookmarkFile, NSURLBookmarkResolutionWithoutUI
)
import objc

from . import Argument, Action


class File(Action):
    def validate_args(self, path, source, state, mode, owner, group):
        if source and state == 'absent':
            self.fail("the 'source' argument may not be provided when 'state' is 'absent'")

        if not source and state == 'symlink':
            self.fail("the 'source' argument must be provided when 'state' is 'symlink'")

    def process(self, path, source, state, mode, owner, group):
        # Ensure that home directories are taken into account
        path = os.path.expanduser(path)
        if source:
            source = os.path.expanduser(source)

        if state == 'file':
            if source:
                # The source provided does not exist or is not a file
                if not os.path.isfile(source):
                    self.fail('the source provided could not be found or is not a file')

                # If the destination provided is a path, then we place the file in it
                if os.path.isdir(path):
                    path = os.path.join(path, os.path.basename(source))

                # An existing file at the destination path was found so we compare them
                # and avoid making changes if they're identical
                exists = os.path.isfile(path)
                if exists and self.md5(source) and self.md5(path):
                    self.ok()

                # Copy the source to the destination
                self.copy(source, path)

                # Set mode, owner and group on the path
                self.set_file_attributes(path)

                self.changed(path=path)
            else:
                # An existing file at the destination path was found
                if os.path.isfile(path):
                    self.ok()

                # Create an empty file at the destination path
                self.create_empty(path)

                # Set mode, owner and group on the path
                self.set_file_attributes(path)

                self.changed(path=path)

        elif state == 'directory':
            if source:
                # TODO: implement rsync like functionality here
                self.fail('this feature is not implemented yet')
            else:
                # An existing directory was found
                if os.path.isdir(path):
                    self.ok()

                # Clean any existing item in the path requested
                removed = self.remove(path)

                # Create the directory requested
                try:
                    os.makedirs(path)
                except OSError:
                    self.fail('the requested directory could not be created')

                # Set mode, owner and group on the path
                self.set_file_attributes(path)

                self.changed(path=path)

        elif state == 'alias':
            # If the destination provided is a path, then we place the file in it
            if os.path.isdir(path):
                path = os.path.join(path, os.path.basename(source))

            # When creating an alias, the source must be an absolute path and exist
            source = os.path.abspath(source)
            if not os.path.exists(source):
                self.fail('the source file provided does not exist')

            # An existing alias at the destination path was found so we compare them
            # and avoid making changes if they're identical
            exists = os.path.isfile(path)
            path_url = NSURL.fileURLWithPath_(path)

            if exists:
                bookmark_data, error = NSURL.bookmarkDataWithContentsOfURL_error_(
                    path_url, objc.nil
                )

                if bookmark_data:
                    source_url, is_stale, error = NSURL.URLByResolvingBookmarkData_options_relativeToURL_bookmarkDataIsStale_error_(  # flake8: noqa
                        bookmark_data, NSURLBookmarkResolutionWithoutUI, None, objc.nil, objc.nil
                    )
                    if source_url.path() == source:
                        self.ok()

            # Delete any existing file or symlink at the path
            removed = self.remove(path)

            # Create an NSURL object for the source (absolute paths must be used for aliases)
            source_url = NSURL.fileURLWithPath_(source)

            # Build the bookmark for the alias
            bookmark_data, error = source_url.bookmarkDataWithOptions_includingResourceValuesForKeys_relativeToURL_error_(
                NSURLBookmarkCreationSuitableForBookmarkFile, None, None, objc.nil
            )

            # Write the alias using the bookmark data
            if bookmark_data:
                success, error = NSURL.writeBookmarkData_toURL_options_error_(
                    bookmark_data, path_url, NSURLBookmarkCreationSuitableForBookmarkFile, objc.nil
                )
            else:
                self.fail('unable to create alias')

            # Set mode, owner and group on the path
            self.set_file_attributes(path)

            self.changed(path=path)

        elif state == 'symlink':
            # If the destination provided is a path, then we place the file in it
            if os.path.isdir(path):
                path = os.path.join(path, os.path.basename(source))

            # An existing symlink at the destination path was found so we compare them
            # and avoid making changes if they're identical
            exists = os.path.islink(path)
            if exists and os.readlink(path) == source:
                self.ok()

            # Delete any existing file or symlink at the path
            removed = self.remove(path)

            # Create the symlink requested
            try:
                os.symlink(source, path)
            except OSError:
                self.fail('the requested symlink could not be created')

            # Set mode, owner and group on the path
            self.set_file_attributes(path)

            self.changed(path=path)

        elif state == 'absent':
            removed = self.remove(path)
            self.changed(path=path) if removed else self.ok()

    def copy(self, source, path, buffer_size=1024 * 8):
        try:
            with open(source, 'rb') as fsource:
                with open(path, 'wb') as fpath:
                    for buffer in iter(lambda: fsource.read(buffer_size), b''):
                        fpath.write(buffer)
        except OSError:
            self.fail('unable to copy source file to path requested')

    def create_empty(self, path):
        try:
            with open(path, 'w'):
                pass
        except IsADirectoryError:
            self.fail('the destination path is a directory')
        except OSError:
            self.fail('unable to create an empty file at the path requested')

    def remove(self, path):
        if not os.path.exists(path) and not os.path.islink(path):
            return False

        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                self.fail('existing file could not be removed')

        elif os.path.isdir(path):
            try:
                shutil.rmtree(path)
            except IOError:
                self.fail('existing directory could not be recursively removed')

        elif os.path.islink(path):
            try:
                os.remove(path)
            except OSError:
                self.fail('existing symlink could not be removed')

        return True

    def md5(self, path, block_size=1024 * 8):
        hash = hashlib.md5()

        try:
            with open(path, 'rb') as f:
                for buffer in iter(lambda: f.read(block_size), b''):
                    hash.update(buffer)
        except OSError:
            self.fail('unable to determine checksum of file')

        return hash.hexdigest()


if __name__ == '__main__':
    file = File(
        Argument('path'),
        Argument('source', optional=True),
        Argument(
            'state', choices=['file', 'directory', 'alias', 'symlink', 'absent'], default='file'
        ),
        add_file_attribute_args=True
    )
    file.invoke()
