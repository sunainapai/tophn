#!/usr/bin/env python

# The MIT License (MIT)
#
# Copyright (c) 2017-2020 Sunaina Pai
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


"""Publish TopHN website.

TopHN is a website that aims to recommend exactly one story from
Hacker News (HN) to the user.

The top story on Hacker News is sampled every minute. The story that
occurred most frequently in these samples in the last 24 hours is
recommended to you.
"""


__version__ = '0.0.1'
__author__ = 'Sunaina Pai'
__credits__ = ('Hacker News community for great content and exposing '
               'the content via REST API.')


import logging
import logging.handlers
import json
import time
import configparser
import urllib
import urllib.request
import os
import shutil
import collections

import jinja2


def _get_top_id(config):
    """Return the HN ID of the current top story.

    Arguments:
      config (configparser.ConfigParser): Configuration object.

    Returns:
      int: HN ID of the current top story.
    """
    ids_url = config.get('hn', 'ids_url')

    # Connect to HN REST API and get the list of IDs of top stories.
    data = urllib.request.urlopen(ids_url).read()

    # Return the first item in the list of IDs. The first item is the ID
    # of current top story on HN.
    top_ids = json.loads(data.decode('utf-8'))
    return top_ids[0]


def _get_story(config, hn_id):
    """Return JSON item for the specified ID.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
      hn_id (int): ID of an HN story.

    Returns:
      dict: Response JSON from HN as a dictionary.
    """
    story_base_url = config.get('hn', 'story_base_url')

    # Connect to HN REST API and get the JSON for the story ID.
    hn_url = story_base_url + str(hn_id) + '.json'
    data = urllib.request.urlopen(hn_url).read()

    # Convert the JSON bytes to string and return it.
    story = json.loads(data.decode('utf-8'))
    return story


def _select_top_id(hn_records):
    """Return the selected top ID.

    Sample the IDs present in hn_records. Select the HN ID with the
    highest frequency. If there is a tie between two HN IDs, the one
    that is more recent on HN is selected as the top ID.

    Arguments:
      hn_records (list): Each entry of the list is a tuple of HN ID and
        timestamp.

    Returns:
      int: HN ID selected as the top ID.
    """
    # This ordered dictionary will contain key-value pairs where story
    # ID is the key and frequency of the story ID is the value.
    id_frequency = collections.OrderedDict()

    # Create a dictionary where each key is a story ID and each value is
    # the frequency of that story ID.
    for hn_id, timestamp in hn_records:
        id_frequency[hn_id] = id_frequency.get(hn_id, 0) + 1

    # Select the story ID with the highest frequency. If there is a tie
    # between two story IDs with the same highest frequency, we select
    # the one that is more recent on HN (i.e., more towards the end of
    # our database file and hence more towards the end of id_frequency).
    max_frequency = -1
    most_frequent_id = -1
    for hn_id, frequency in id_frequency.items():
        if frequency >= max_frequency:
            max_frequency = frequency
            most_frequent_id = hn_id

    return most_frequent_id


def _get_24_hour_samples_from_db(config, cur_time, ids_file):
    """Return entries from the past 24 hours.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
      cur_time (int): Current Unix timestamp rounded to seconds.
      cur_file (str): Current database file

    Returns:
      list: Entries in database with timestamps within past 24 hours as
        a list of tuples.
    """
    time_24_hours_ago = cur_time - 24 * 60 * 60

    hn_records = []
    id_list = []

    # Load entries of current day and previous day into a list.
    if os.path.isfile(ids_file):
        with open(ids_file) as f:
            id_list = json.load(f)
    else:
        logger.info('File does not exist: {}'.format(ids_file))

    # Select all entries with timestamps within past 24 hours and store
    # in the result list.
    for hn_id, timestamp in id_list:
        if int(timestamp) > time_24_hours_ago:
            hn_records.append((int(hn_id), int(timestamp)))

    return hn_records


def _render(config, template_name, template_values, output_file):
    """Render the specified template.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
      template_name (str): Name of the template to be rendered.
      template_values (dict): Values to be used for template rendering
        as a dictionary.
      output_file (str): Path of the file where the template is to be
        rendered.
    """
    templates_path = config.get('templates', 'path')
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_path))
    template = env.get_template(template_name)
    with open(output_file, 'w') as f:
        f.write(template.render(template_values))


def _was_published_earlier(archive_list, hn_id):
    """Return whether the specified HN ID was published earlier.

    Arguments:
      archive_list (list): Each entry of the list is a dictionary
        representing an HN story that was once a top story on TopHN.
      hn_id (int): ID of an HN story.

    Returns:
      bool: True iff the specified HN ID was once the top ID.
    """
    return hn_id in [story['id'] for story in archive_list]


def _check_new_top_story(config, archive_list, cur_time):
    """Check if there is a new top story that was not published earlier.

    The top story is defined as the TopHN top story, i.e. the most
    frequent HN top story in the last 24 hours.

    Select the most frequent top ID from the database. If this selected
    top ID was not published earlier (i.e. does not exist in the archive
    database), then return the top ID.

    If the top ID was published earlier (i.e. exists in the archive
    database), then do nothing and return None.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
      archive_list (list): Each entry of the list is a dictionary
        representing an HN story that was once a top story on TopHN.
      cur_time (int): Current Unix timestamp rounded to seconds.

    Returns:
      int: HN ID if a new top story needs to be published, None
        otherwise.
    """
    ids_file = config.get('database', 'ids')
    # Get the ID of the current top story on HN.
    top_id_on_hn = _get_top_id(config)
    logger.info('Top ID on HN: {}'.format(top_id_on_hn))

    # Re-write ids file with only the last 24 hours data + the currently
    # sampled top ID on HN.
    samples = _get_24_hour_samples_from_db(config, cur_time,
                                           ids_file)
    samples.append([top_id_on_hn, cur_time])
    with open(ids_file, 'w') as f:
        json.dump(samples, f, indent=2)

    # Find the most frequent story ID in the samples and select it for
    # publication.
    top_id = _select_top_id(samples)
    logger.info('Most frequent top ID in the past 24 hours: {}'
                .format(top_id))

    # If the top story ID selected for publication was already
    # published, then do nothing.
    if  _was_published_earlier(archive_list, top_id):
        logger.info('Ignoring selected ID {} because it was published '
                    'earlier'.format(top_id))
        return None

    return top_id


def _add_new_top_story_to_archive(config, top_id, archive_list, cur_time):
    """Add the specified story to the archive database.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
      top_id (int): HN ID of the selected story
      archive_list (list): Each entry of the list is a dictionary
        representing an HN story that was once a top story on TopHN.
      cur_time (int): Current Unix timestamp rounded to seconds.
    """
    database_archive = config.get('database', 'archive')

    # Get the HN story for the selected top ID.
    top_story = _get_story(config, top_id)

    top_story_dict = {
        'by':
            top_story.get('by'),

        'type':
            top_story.get('type'),

        'id':
            top_story.get('id'),

        'title':
            top_story.get('title'),

        'url':
            top_story.get('url'),

        'time_hn':
            top_story.get('time'),

        'time_tophn':
            cur_time
    }

    # Add the new story to the archive database.
    archive_list.append(top_story_dict)
    with open(database_archive, 'w') as f:
        json.dump(archive_list, f, indent=2)


def _read_archive(config):
    """Return the list of top stories from archive database.

    Returns:
      list: List of top stories from archive database. Each entry of the
        list is a dictionary representing an HN story that was once a
        top story on TopHN. An empty list if there is no archive
        database.
    """
    database_archive = config.get('database', 'archive')
    if os.path.isfile(database_archive):
        with open(database_archive) as f:
            archive_list = json.load(f)
    else:
        archive_list = []

    return archive_list


def _stage_top_hn(config, archive_list):
    """Stage a new website directory.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
      archive_list (list): Each entry of the list is a dictionary
        representing an HN story that was once a top story on TopHN.
    """
    templates_home = config.get('templates', 'home')
    templates_archive = config.get('templates', 'archive')
    templates_about = config.get('templates', 'about')
    templates_static = config.get('templates', 'static')

    stage_dir = config.get('site', 'stage_dir')
    home_page = config.get('site', 'home')
    archive_page = config.get('site', 'archive')
    about_page = config.get('site', 'about')
    static_content = config.get('site', 'static')

    logger.info('Creating {} directory ...'.format(stage_dir))
    os.makedirs(stage_dir)

    logger.info('Copying static directory to {} ...'.format(stage_dir))
    shutil.copytree(templates_static, static_content)

    # Publish the top story on the home page.
    logger.info('Rendering home page ...')
    _render(config, templates_home, archive_list[-1], home_page)

    # Render the archive page with the new top story.
    archive_dict = {
        'archives': reversed(archive_list),
        'urllib': urllib,
        'time': time
    }
    logger.info('Rendering archive page ...')
    _render(config, templates_archive, archive_dict, archive_page)

    # Render the about page.
    logger.info('Rendering about page ...')
    _render(config, templates_about, {}, about_page)


def _publish_top_hn(config):
    """Publish the staging website as live website.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
    """
    stage_dir = config.get('site', 'stage_dir')
    live_dir = config.get('site', 'live_dir')
    defunct_dir = config.get('site', 'defunct_dir')

    if os.path.isdir(live_dir):
        logger.info('Moving {} to {} ...'.format(live_dir, defunct_dir))
        shutil.move(live_dir, defunct_dir)
    else:
        logger.info('Live site is missing; nothing to backup')

    logger.info('Moving {} to {} ...'.format(stage_dir, live_dir))
    shutil.move(stage_dir, live_dir)
    logger.info('Published live site')

    if os.path.isdir(defunct_dir):
        logger.info('Removing {} ...'.format(defunct_dir))
        shutil.rmtree(defunct_dir)


def _configure_logging(config):
    """Configure logging as specified in configuration.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
    """
    # Retrieve logging configuration properties.
    log_file = config.get('logging', 'file')
    rotation_time = config.get('logging', 'rotation_time')
    backup_count = config.get('logging', 'backup_count')
    level = config.get('logging', 'level')
    msg_format = config.get('logging', 'msg_format')
    date_format = config.get('logging', 'date_format')

    # Create a timed rotating file handler.
    formatter = logging.Formatter(fmt=msg_format, datefmt=date_format)
    handler = logging.handlers.TimedRotatingFileHandler(
                  log_file, when=rotation_time,
                  backupCount=int(backup_count))
    handler.setFormatter(formatter)

    # Configure the root logger.
    logging.getLogger().setLevel(level)
    logging.getLogger().addHandler(handler)


def _main(config):
    """Start this application.

    Arguments:
      config (configparser.ConfigParser): Configuration object.
    """
    poll_interval = config.getint('poll', 'interval')
    live_dir = config.get('site', 'live_dir')
    while True:
        try:
            logger.info('Working ...')

            # Get the current Unix timestamp to be used everywhere when
            # processing a particular event. The HN item has no
            # milliseconds in the Unix timestamp. Use the same format
            # for our timestamp.
            cur_time = int(round(time.time()))
            cur_time_str = time.strftime("%Y-%m-%d %H:%M:%S %Z",
                                         time.gmtime(cur_time))
            logger.info('Current Time: {}: {}'
                        .format(cur_time, cur_time_str))

            archive_list = _read_archive(config)
            new_story_id = _check_new_top_story(config, archive_list,
                                                cur_time)

            if new_story_id is not None:
                _add_new_top_story_to_archive(config, new_story_id,
                                              archive_list, cur_time)
                logger.info('Publishing top story on TopHN: {}: {}'.
                            format(new_story_id, archive_list[-1]))
                _stage_top_hn(config, archive_list)
                _publish_top_hn(config)

            elif not os.path.isdir(live_dir):
                # If live directory is missing but there is no new
                # story, we don't need to update archive database.
                logger.info('Live site is missing; publishing ...')
                _stage_top_hn(config, archive_list)
                _publish_top_hn(config)

            else:
                logger.info('Live site exists; no new top story; '
                            'nothing to publish')

        except Exception as e:
            logger.error('Unexpected error occurred; error: {!r}'.format(e))
            logger.exception('Unexpected error occurred')

        logger.info('Sleeping for {} seconds ...'.format(poll_interval))
        time.sleep(poll_interval)


if __name__ == '__main__':
    # Read configuration.
    config  = configparser.ConfigParser()
    config.read('config.ini')

    # Create runtime directories.
    os.makedirs(config.get('database', 'db_dir'), exist_ok=True)
    os.makedirs(os.path.dirname(config.get('logging', 'file')),
                                exist_ok=True)

    # Configure logging.
    _configure_logging(config)
    logger = logging.getLogger('tophn')
    logger.info('Logging configured')

    # Start the application.
    _main(config)
