# Adafruit Arduino Board Package Tool (bpt)
# Swiss Army knife for managing Arduino board packages.  Can check board packages
# against a published board package index and notify when newer versions are
# available, automatically build updated packages for the index, and more.
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
import json
import http.server
import socketserver

from bpt_model import *
import click
from git import Repo
from pkg_resources import parse_version


logger = logging.getLogger(__name__)


class BptContext(object):
    """Context object which holds global state passed between click groups and
    commands.
    """

    def __init__(self):
        self.board_config_file = None
        self.board_index_file = None
        self.board_packages = None
        self.board_config = None
        self.board_index = None

    def load_data(self):
        """Load all the package and package index metadata to prepare for
        processing.  This will read the package config INI file and all grab all
        the packages it mentions, then load the package index JSON and parse it.
        """
        click.echo('Loading current packages from their origin repository/directory...')
        # Load the board configuration file.
        self.board_config = BoardConfig(self.board_config_file)
        # Save the board packages in the context so other commands can read and
        # process them.
        self.board_packages = self.board_config.get_packages()
        # Now read in the board index JSON file and parse it, then save in global context.
        with open(self.board_index_file, 'r') as bi:
            self.board_index = BoardIndex(json.load(bi))


@click.group()
@click.option('--debug', '-d', is_flag=True,
    help='Enable debug output.')
@click.option('--board-config', '-c', default='bpt.ini',
    type=click.Path(dir_okay=False),
    help='Specify a INI config file with list of board packages to use. Default is a bpt.ini in the current directory.')
@click.option('--board-index', '-i', default='package_adafruit_index.json',
    type=click.Path(exists=True, dir_okay=False),
    help='Specify a board index JSON file.  This is the master index that publishes all the packages.')
@click.pass_context
def bpt_command(ctx, debug, board_config, board_index):
    """Adafruit Arduino Board Package Tool (bpt)

    Swiss Army knife for managing Arduino board packages.  Can check board packages
    against a published board package index and notify when newer versions are
    available, automatically build updated packages for the index, and more.
    """
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    ctx.obj.board_config_file = board_config
    ctx.obj.board_index_file = board_index


@bpt_command.command()
@click.pass_context
def check_updates(ctx):
    """Check package index for out of date packages.

    Scan a set of board packages and compare their version against the most
    recent version published in a board index.  Will alert of any board packages
    which have a newer version than is published in the board index.
    """
    ctx.obj.load_data()  # Load all the package config & metadata.
    click.echo('Found the following current packages:')
    for package in ctx.obj.board_packages:
        click.echo('- {0}'.format(package.get_name()))
        click.echo('    version = {0}'.format(package.get_version()))
        click.echo('    origin  = {0}'.format(package.get_origin()))
    # Go through each board package loaded from the board package config INI
    # and check if its version is newer than the related packages in the board
    # index.
    click.echo('Comparing current packages with published versions in board index...')
    for package in ctx.obj.board_packages:
        parent = package.get_parent()
        name = package.get_name()
        version = package.get_version()
        click.echo('- {0}'.format(name))
        # Get all the associated packages in the board index.
        index_packages = list(ctx.obj.board_index.get_platforms(parent, name))
        # Skip to the next package if nothing was found in the board index for this package.
        if len(index_packages) == 0:
            click.echo('    Not found in board index!')
            continue
        # Find the most recent version in the index packages.
        #print(index_packages)
        latest = max(map(lambda x: parse_version(x.get('version', '')), index_packages))
        click.echo('    latest index version = {0}'.format(str(latest)))
        # Warn if the latest published package is older than the current package
        # from its origin source.
        if latest < parse_version(version):
            click.echo('    !!!! BOARD INDEX NOT UP TO DATE !!!!')


@bpt_command.command()
@click.option('--force', '-f', is_flag=True,
              help='Force the specified package to be updated even if the version is older than currently in the index.')
@click.option('--output-board-index', '-o',
    type=click.Path(dir_okay=False, writable=True),
    help='Specify the new board index JSON file to write.  If not specified the input board index (--board-index value or its default) will be used.')
@click.option('--output-board-dir', '-od', default='boards',
    type=click.Path(file_okay=False, writable=True),
    help="Specify the directory to write the board package archive file.  Default is a 'boards' subdirectory in the current location.")
@click.argument('package_name')
@click.pass_context
def update_index(ctx, package_name, force, output_board_index, output_board_dir):
    """Update board package in the published index.

    This command will archive and compress a board package and add it to the
    board index file.  A sanity check will be done to ensure the package has a
    later version than currently in the board index, however this can be disabled
    with the --force option.

    The command takes one argument, the name of the board package to update.
    This should be the name of the package as defined in the board package config
    INI file section name (use the check_updates command to list all the packages
    from the config if unsure).
    """
    ctx.obj.load_data()  # Load all the package config & metadata.
    # Use the input board index as the output if none is specified.
    if output_board_index is None:
        output_board_index = ctx.obj.board_index_file
    # Validate that the specified package exists in the config.
    package = ctx.obj.board_config.get_package(package_name)
    if package is None:
        raise click.BadParameter('Could not find specified package in the board package config INI file! Run check_updates command to list all configured package names.',
            param_hint='package')
    # If not in force mode do a sanity check to make sure the package source
    # has a newer version than in the index.
    if not force:
        # Get all the associated packages in the board index.
        index_packages = list(ctx.obj.board_index.get_platforms(package.get_parent(),
            package.get_name()))
        # Do version check if packages were found in the index.
        if len(index_packages) > 0:
            # Find the most recent version in the index packages.
            latest = max(map(lambda x: parse_version(x.get('version', '')), index_packages))
            # Warn if the latest published package is the same or newer than the
            # current package from its origin source.
            if latest >= parse_version(package.get_version()):
                raise click.UsageError('Specified package is older than the version currently in the index!  Use the --force option to force this update if necessary.')
    # Create the output directory if it doesn't exist.
    if not os.path.exists(output_board_dir):
        os.makedirs(output_board_dir)
    # Build the archive with the board package data and write it to the target
    # directory.
    archive_path = os.path.join(output_board_dir, package.get_archive_name())
    size, sha256 = package.write_archive(archive_path)
    click.echo('Created board package archive: {0}'.format(archive_path))
    # Convert the package template from JSON to a platform metadata dict that
    # can be inserted in the board index.
    template_params = {
        'version': package.get_version(),
        'filename': package.get_archive_name(),
        'sha256': sha256,
        'size': size
    }
    platform = json.loads(package.get_template().format(**template_params))
    # Add the new pacakge metadata to the board index.
    ctx.obj.board_index.add_platform(package.get_parent(), platform)
    # Write out the new board index JSON.
    new_index = ctx.obj.board_index.write_json()
    with open(output_board_index, 'w') as bi:
        bi.write(new_index)
    click.echo('Wrote updated board index JSON: {0}'.format(output_board_index))


@bpt_command.command()
@click.option('--url-transform', '-u', default='adafruit.github.io/arduino-board-index',
              help='URL domain and starting path to replace with the localhost:<port> test server in the index during testing.  Must be set or else the index will reference files on the internet, not local machine!')
@click.option('--port', '-p', type=click.INT, default=8000,
              help='Port number to use for the test server.')
@click.pass_context
def test_server(ctx, url_transform, port):
    """Run a local webserver to test board index.

    Create a local webserver on port 8000 (but can be changed with the --port
    option) that will serve the board package index.  Setup the Arduino IDE to
    use the board package URL:
      http://localhost:8000/package_test_index.json
    """
    # TODO: Don't hard code this file name.  However Arduino _must_ see a file
    # named 'package_<PACKAGE_NAME>_index.json' for the file to work, and we
    # don't want to modify the real index with the transformations below.  for
    # now we just use a test package file.
    test_index = 'package_test_index.json'
    ctx.obj.load_data()  # Load all the package config & metadata.
    # Start the webserver from inside the directory with the index file.
    index_dir, index_filename = os.path.split(ctx.obj.board_index_file)
    if index_dir is not None and index_dir != '':
        os.chdir(index_dir)
    # Transform all package url values in the index to use http instead of https
    # (SSL is unsupported by Python's simple web server), and to replace the
    # domain and root of the URL with the localhost:<port> value so the data
    # is served locally instead of from the remote server.
    ctx.obj.board_index.transform_urls([
        ('https://', 'http://'),  # Replace https:// with http://
        (url_transform, 'localhost:{0}'.format(port))  # Replace remote server URL with local test server.
    ])
    # Write out the test board index JSON.
    with open(test_index, 'w') as bi:
        bi.write(ctx.obj.board_index.write_json())
    try:
        server = socketserver.TCPServer(('', port), http.server.SimpleHTTPRequestHandler)
        click.echo('Source board index file: {0}'.format(ctx.obj.board_index_file))
        click.echo('Test server listening at: http://localhost:{0}'.format(port))
        click.echo('Configure Arduino to use the following board package URL:')
        click.echo('  http://localhost:{0}/{1}'.format(port, test_index))
        server.serve_forever()
    finally:
        # Cleanup the test index file that was created.
        os.remove(test_index)


if __name__ == '__main__':
    try:
        # Create a board package tool context object that will hold all global
        # state passed between command handler functions.
        context = BptContext()
        # Invoke click command processing.
        bpt_command(obj=context)
    finally:
        # Close any board packages that were opened, this will clean up temporary
        # file locations, etc.
        if context.board_packages is not None:
            for package in context.board_packages:
                package.close()
