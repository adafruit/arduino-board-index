# Adafruit Arduino Board Package Tool (bpt) Data Model
# Classes that support bpt's commands.  These classes represent the Arduino
# packages, board index, and configuration of the tool.
# Author: Tony DiCola
#
# Copyright (c) 2016 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import ConfigParser
import hashlib
import json
import logging
import os
import os.path
import posixpath
import re
import shutil
import tarfile
import tempfile

from git import Repo
from pkg_resources import parse_version


logger = logging.getLogger(__name__)


class BoardPackage(object):
    """Board package instance state (name, version, etc.)."""

    def __init__(self, parent, template, name, version, origin, archive_prefix=None):
        """Initialize board package instance with specified state:
          - parent = name of parent package that contains this instance
          - template = JSON string to use as template when writing this instance
                       back to the board index
          - name = name of the board package instance
          - version = version of the board package instance
          - origin = string that describes the source of this board package
          - archive_prefix = prefix to use when constructing the board package
                             archive filename
        """
        self._parent = parent
        self._name = name
        self._version = version
        self._origin = origin
        self._archive_prefix = archive_prefix
        self._template = template

    def get_parent(self):
        """Return the parent package name in the board index that owns this board
        package.
        """
        return self._parent

    def get_template(self):
        """Return a string template that contains a JSON object which will be
        inserted into the board index.
        """
        return self._template

    def get_version(self):
        """Return the version of this board package instance."""
        return self._version

    def get_name(self):
        """Return the name of this board package instance."""
        return self._name

    def get_origin(self):
        """Return a description of the origin for this package, i.e. the
        directory or Git repo that is the source for this package.
        """
        return self._origin

    def get_archive_name(self):
        """Return the name of the archive file for this board package.  This
        name is set as a '<prefix>-<version>.tar.bz2' where <prefix> defaults
        to the name of the package but can be overridden, and <version> is the
        version of the package.
        """
        prefix = self.get_name()
        if self._archive_prefix is not None:
            prefix = self._archive_prefix
        return '{0}-{1}.tar.bz2'.format(prefix, self.get_version())

    def close(self):
        """Close will be called at the termination of the program and gives a
        good place for subclasses to cleanup any temporary data.
        """
        pass

    def write_archive(self, target):
        """Create an archive that is compressed and in the expected format for
        a board package (.tar.bz2).  Will write the contents to the specified
        target file name.  Returns a tuple of (archive size in bytes, archive
        SHA256 hash).
        """
        raise NotImplementedError


class DirectoryBoardPackage(BoardPackage):
    """Board package that lives inside a directory on the machine."""

    def __init__(self, directory, origin=None, **kwargs):
        """Initialize board package instance pointing at the specified local
        directory.
        """
        self._directory = directory
        version = None
        # Check that the directory exists and has a platform.txt that is
        # readable (i.e. is an Arduino board package).
        platform_file = os.path.join(directory, 'platform.txt')
        with open(platform_file, 'r') as platform_txt:
            # Parse out the platform version.
            for line in platform_txt.readlines():
                # Look for 'version=<platform version>' line and grab the version.
                # Grab everything up to the end of line or start of comment (#).
                match = re.match('version=([^#]+)', line, flags=re.IGNORECASE)
                if match:
                    version = match.group(1).strip()
        # Check that a version was found inside the package.
        assert version is not None, 'Expected version for package: {0}'.format(name)
        # Set the origin location if it wasn't provided already.
        if origin is None:
            origin = 'directory: {0}'.format(directory)
        super(DirectoryBoardPackage, self).__init__(version=version, origin=origin,
            **kwargs)

    def write_archive(self, target):
        """Create an archive that is compressed and in the expected format for
        a board package (.tar.bz2).  Will write the contents to the specified
        target file name.  Returns a tuple of (archive size in bytes, archive
        SHA256 hash).
        """
        # Create .tar.bz2 archive of the package directory.
        with tarfile.open(target, 'w:bz2') as archive:
            archive.add(self._directory,
                # Put files inside a folder with same name as archive (minus extension)
                arcname=os.path.basename(target)[:-len('.tar.bz2')],
                exclude=lambda x: x.startswith('.git'))  # Don't add .git folder!
        # Get the size of the archive.
        size = os.stat(target).st_size
        # Generate a SHA256 hash of the archive.
        with open(target, 'rb') as archive:
            sha256 = hashlib.sha256(archive.read()).hexdigest()
        return (size, sha256)


class GitBoardPackage(DirectoryBoardPackage):
    """Board package that lives in a remote Git repository."""

    def __init__(self, repo, repo_dir, **kwargs):
        """Initialize board package using the contents of the specified Git
        repository.  Repo should be a URL that can be cloned with Git and its
        contents will be cloned in a temporary directory.
        """
        # Create a temporary directory to clone the repository.
        self._local_dir = tempfile.mkdtemp()
        # Clone the repo to the temp directory.
        logger.debug('GitBoardPackage cloning repo {0} to directory {1}'.format(repo, self._local_dir))
        Repo.clone_from(repo, self._local_dir)
        # Find path to repo dir inside cloned directory.
        target_dir = self._local_dir
        if repo_dir is not None:
            # Parse the directories from the board config repo_dir value.
            # Note that by convention this is in Unix-style path separators
            # (forward slashes, '/').
            repo_dir = posixpath.normpath(repo_dir)
            dirs = repo_dir.split(posixpath.sep)
            # Now use the current OS path join to point at the repo_dir.
            target_dir = os.path.join(self._local_dir, *dirs)
        # Finish initializing using the cloned repo directory.
        super(GitBoardPackage, self).__init__(target_dir, origin='git: {0}'.format(repo),
            **kwargs)

    def close(self):
        """Clean up temporary location that holds remote Git repository files."""
        if self._local_dir is not None:
            logger.debug('Deleting temporary directory {0}'.format(self._local_dir))
            shutil.rmtree(self._local_dir, ignore_errors=True)


class BoardIndex(object):
    """Board index that is the master list of packages published to Arduino
    clients.
    """

    def __init__(self, index_data):
        """Initialize board index with JSON decoded dict of board index data.
        """
        self._data = index_data
        # Load all the packages and add them to a dict indexed by package name
        # for quick lookup.
        self._packages = {}
        for package in self._data.get('packages', []):
            name = package.get('name')
            assert name is not None and name != '', 'Board index package must specify a name!'
            self._packages[name] = package

    def get_packages(self):
        """Retrieve a list of all the packages."""
        return self._packages.values()

    def get_platforms(self, package, name=None):
        """Retrieve a list of all platforms for the specified package name.
        Can optionally filter by platforms of the specified name (i.e. to get
        all the different versions of that platform).
        """
        platforms = self._packages[package].get('platforms', [])
        if name is None:
            return platforms
        else:
            return filter(lambda x: x.get('name') == name, platforms)

    def add_platform(self, package, platform):
        """Add a platform to the specified package."""
        parent = self._packages[package]
        parent.get('platforms', []).append(platform)

    def write_json(self):
        """Serialize the board index data into JSON so it can be written to a
        file.  Will return the JSON string of the data.
        """
        return json.dumps(self._data, indent=2, separators=(',', ': '))

    def transform_urls(self, transforms):
        """Transform all the urls inside platforms using the specified list
        of string transformations.  Each transform entry should be a 2-tuple
        with target, the string to search for from the beginning, and value,
        the string to replace target with.  For example the tuple ('https://',
        'http://') would convert SSL to non-SSL.  Note that target searching is
        case insensitive!
        """
        # Walk all the packages and platforms inside them.
        for package in self._data.get('packages', []):
            for platform in package.get('platforms', []):
                # Look for any url attribute and apply transformations.
                if 'url' not in platform:
                    continue
                for transform in transforms:
                    target, value = transform
                    # Look for the first instance of target in the string (being
                    # careful to be case insensitive).
                    url = platform['url']
                    start = url.lower().find(target.lower())
                    if start != -1:
                        # Replace target with value.
                        platform['url'] = ''.join([url[:start], value, url[start+len(target):]])

class BoardConfig(object):
    """Represents a board configuration INI file.  This configuration can define
    a list of board package locations, either as directories or Git repositories.
    This is useful for predefining a set of board packages in a configuration
    file that saves having to use a lot of command line parameters to specify
    each pacakge location.
    """

    def __init__(self, board_config):
        """Initialize board package config using the specified board_config
        file path.  If board_config is None or empty then no board pacakges will
        be loaded.  Otherwise board_config should point at an INI file with
        a section for each board package and attributes inside:
          - package = name of parent package inside board index (required)
          - directory = path to a directory on the machine with the board package
          - repo = git repository URL that holds the board package
        """
        self._packages = []
        # Load the INI file and process all the sections.
        self._config = ConfigParser.RawConfigParser()
        self._config.read([board_config])
        for section in self._config.sections():
            logger.debug('Processing config file {0} section {1}'.format(board_config, section))
            # Process required options.
            parent = self._config.get(section, 'index_parent')
            template = self._config.get(section, 'index_template')
            # Process optional options.
            archive_prefix = None
            if self._config.has_option(section, 'archive_prefix'):
                archive_prefix = self._config.get(section, 'archive_prefix')
            # Look for a directory or repo and process accordingly.
            if self._config.has_option(section, 'directory') and \
                self._config.has_option(section, 'repo'):
                # Both options are ambiguous, fail.
                raise RuntimeError('Board package config is ambiguous with both directory and repo!')
            if self._config.has_option(section, 'directory'):
                # Create a local directory-based package source.
                directory = self._config.get(section, 'directory')
                self._packages.append(DirectoryBoardPackage(directory, parent=parent,
                    template=template, name=section, archive_prefix=archive_prefix))
            elif self._config.has_option(section, 'repo'):
                # Create a Git-based package source.
                repo = self._config.get(section, 'repo')
                # Grab optional repo_dir path to platforms.txt.
                repo_dir = None
                if self._config.has_option(section, 'repo_dir'):
                    repo_dir = self._config.get(section, 'repo_dir')
                self._packages.append(GitBoardPackage(repo, repo_dir, parent=parent,
                    template=template, name=section, archive_prefix=archive_prefix))
            else:
                # No known way to read this repo, fail.
                raise RuntimeError('Board package config must specify either directory or repo!')

    def get_packages(self):
        """Return the packages parsed by this configuration file."""
        return self._packages

    def get_package(self, package):
        """Return the specified package (by name), or None if it does not exist
        in the config.
        """
        packages = filter(lambda x: x.get_name() == package, self._packages)
        if len(packages) == 0:
            return None
        elif len(packages) == 1:
            return packages[0]
        else:
            raise RuntimeError('Found multiple packages with same name in config, ambiguous result!')
