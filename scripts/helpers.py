# -*- coding: utf-8 -*-
# @Date    : 2018-10-28 12:51:52
# @Author  : Md Nazrul Islam (email2nazrul@gmail.com)
# @Link    : http://nazrul.me/
# @Version : $Id$
# All imports here
from aiohttp.client_exceptions import ClientOSError
from aiohttp.client_exceptions import ClientResponseError
from aiohttp.client_exceptions import ServerDisconnectedError
from collections import OrderedDict
from collections import deque
from zc.buildout import configparser

import aiohttp
import asyncio
import argparse
import datetime
import hashlib
import pathlib
import os
import io
import bs4
import inspect
import sys
import tqdm
import typing

__author__ = 'Md Nazrul Islam (email2nazrul@gmail.com)'

ArgumentParserType = typing.NewType('ArgumentParser', argparse.ArgumentParser)
ArgumentParserNamespaceType = typing.NewType('ArgumentParserNamespaceType',
                                             argparse.Namespace)

BASE_URL = 'http://dist.plone.org/release'
VERSION_CFG = 'versions.cfg'
OUTPUT_DIR = pathlib.Path(__file__).parent.parent / 'dist'
CACHE_DIR = pathlib.Path(__file__).parent / '.cache'


def get_parser() -> ArgumentParserType:
    """"""
    prog = 'python -m cli' if sys.argv[0].endswith('__main__.py') else 'cli'

    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument('distribution',
                        action='store',
                        help='plone released version '
                             'i.e 4.3.16 or 5.1-latest')
    return parser


def setup_parser(parser: ArgumentParserType) -> ArgumentParserNamespaceType:
    """
    :param parser:
    :return:
    """

    parser.add_argument('-D',
                        '--destination-dir',
                        action="store",
                        dest='destination_dir',
                        help="Destination directory, where output files will "
                             "be stored",
                        default=None)

    parser.add_argument('-O',
                        '--output-stream',
                        action="store_true",
                        dest='output_stream',
                        help="Flag for print the output instead of storing on "
                             "filesytem",
                        default=False)

    parser.add_argument('-o',
                        '--offline',
                        action="store_true",
                        dest='offline',
                        help="Flag for looing local cache instead content "
                             "from online",
                        default=False)

    parser.add_argument('-v',
                        '--verbosity-level',
                        dest='verbosity_level',
                        action="count")

    return parser.parse_args()


def cmd(func: typing.Callable[[], typing.Any]) -> typing.Callable:
    """
    :param func:
    :return:
    """

    def new_func(*args, **kwargs):

        new_kwargs = {}
        fn_args = deque()

        for param in inspect.signature(func).parameters.values():

            if param.kind.name in ('POSITIONAL_ONLY',
                                   'POSITIONAL_OR_KEYWORD',
                                   'KEYWORD_ONLY'):
                fn_args.append(param.name)

        for i, a in enumerate(fn_args):
            # should not pass an argument more than once
            if i >= len(args) and a in kwargs:
                new_kwargs[a] = kwargs.get(a)

        return func(*args, **new_kwargs)

    return new_func


async def run_cmd(func: typing.Callable[[], typing.Any], args: []) -> int:
    """
    """
    if isinstance(func, str):

        func = globals().get(func)

        if callable(func) or \
                inspect.isfunction(func) or \
                inspect.ismethod(func):
            out = await func(**args)

    elif isinstance(func, (tuple, list)):
        out = await globals().get(func)(*args.get(func), **args)

    elif callable(func):
        out = await func(**args)

    return out


async def run(parsed_args: typing.Dict) -> int:
    try:
        return await run_cmd(start_generation, parsed_args)

    except LookupError as exc:
        # invalid command provided
        sys.stderr.write(str(exc))
        return 1


async def write_stream(filename, response):
    """ """
    # Progress Bar added
    with tqdm.tqdm(total=int(response.content_length or 100)) as pbar:

        try:
            with open(filename, 'wb') as f:
                while True:
                    chunk = \
                        await response.content.read(io.DEFAULT_BUFFER_SIZE)
                    if not chunk:
                        break
                    pbar.update(len(chunk))
                    f.write(chunk)
        except (ServerDisconnectedError,
                ClientResponseError,
                ClientOSError,
                asyncio.TimeoutError) as exc:
            print(str(exc))
            sys.stderr.write(str(exc))
            os.unlink(filename)


async def download_version_cfg(uri, session, offline):
    """ """
    global CACHE_DIR
    global BASE_URL
    global VERSION_CFG

    cache_id = hashlib.md5(uri.encode('utf-8')).hexdigest()
    cached_file = CACHE_DIR / cache_id
    file_location = None

    if offline:
        if not cached_file.exists():
            sys.stdout.write(
                'No offline file found! at {0!s}, '
                'going to dowanload fresh'.
                format(cached_file))
        else:
            file_location = str(cached_file)

    if file_location is None:
        try:
            async with await session.get(uri, allow_redirects=True) as response:

                if response.status == 200:
                    sys.stdout.write(
                        'Start downloading file from {0}\n'.
                        format(uri))

                    await write_stream(str(cached_file), response)

                    file_location = str(cached_file)
                elif response.status == 404:
                    raise LookupError('The URL {0} cannot access!'.format(uri))

        except (ServerDisconnectedError,
                    ClientResponseError,
                    ClientOSError,
                    asyncio.TimeoutError) as exc:
                print(str(exc))
                sys.stderr.write(str(exc))

    return file_location


async def _parse_versions(cfg, session, offline, container):
    """"""

    with open(cfg, 'r') as f:
        sections = configparser.parse(f, cfg)

    container.append(sections['versions'])

    if 'buildout' in sections and \
            'extends' in sections['buildout']:
        urls = sections['buildout']['extends'].split('\n')

        for uri in urls:
            cfg_l = await download_version_cfg(uri, session, offline)
            await _parse_versions(cfg_l, session, offline, container)


async def generate_requirements_txt(
        locations,
        offline,
        session):
    """ """
    global OUTPUT_DIR

    for dist, location in locations:
        versions_stack = deque()

        await _parse_versions(location, session, offline, versions_stack)

        dist_dir = OUTPUT_DIR / dist
        if not dist_dir.exists():
            dist_dir.mkdir()

        combined_versions = OrderedDict()

        for versions in versions_stack:
            combined_versions.update(versions)

        with open(str(dist_dir / 'requirements.txt'), 'w') as f:
            f.write(
                '# This file has been generated by plone.requirements.txt parser at {0}\n'
                .format(datetime.datetime.now().isoformat('T'))
            )
            # add trusted external links
            f.write(
                '--find-links http://dist.plone.org/thirdparty\n'
                '--find-links http://dist.plone.org/packages\n'
                '--trusted-host dist.plone.org\n'
                '--find-links http://download.zope.org/distribution/\n'
                '--trusted-host download.zope.org\n'
                '--find-links http://effbot.org/downloads\n'
                '--trusted-host effbot.org\n'
            )
            for package, version in combined_versions.items():
                if version.startswith('<') or version.startswith('>'):
                    f.write('{0}{1}\n'.format(package, version))
                else:
                    f.write('{0}=={1}\n'.format(package, version))


async def get_distributions_index(filter_=None):
    """ """
    global BASE_URL

    html = None
    async with aiohttp.ClientSession() as session:

        async with session.get(BASE_URL) as resp:
            if resp.status == 200:
                html = await resp.content.read()

    parsed_html = bs4.BeautifulSoup(html, features='lxml')

    indexes = deque()
    for atag in parsed_html.findAll('a')[1:]:
        dist = atag.text.strip().replace('/', '')

        if filter_ == 'latest-only' and not dist.endswith('latest'):
            continue
        elif filter_ == 'pending-only' and not dist.endswith('pending'):
            continue

        indexes.append(dist)

    return indexes


@cmd
async def start_generation(
        distribution,
        offline):
    """ """
    if distribution in ('all', 'latest-only', 'pending-only'):
        dist_indexes = await get_distributions_index(filter_=distribution)
    else:
        await validate_distribution(distribution)
        dist_indexes = [distribution]

    async with aiohttp.ClientSession() as session:

        for dist in dist_indexes:
            try:
                uri = await download_version_cfg('/'.join([BASE_URL, dist, VERSION_CFG]), session, offline)
            except LookupError as exc:
                sys.stderr.write(str(exc))
            else:
                await generate_requirements_txt([(dist, uri)], offline, session)


async def validate_distribution(distribution):
    """ """
    global BASE_URL
    global VERSION_CFG

    url = '/'.join([BASE_URL, distribution, VERSION_CFG])
    async with aiohttp.ClientSession() as session:

        async with session.get(url) as resp:

            if resp.status == 404:
                raise LookupError('{0} is valid plone distribution!'.format(distribution))