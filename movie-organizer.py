#!/usr/bin/env python3

from pythonopensubtitles.opensubtitles import OpenSubtitles
from pythonopensubtitles.utils import File
from pythonopensubtitles.settings import Settings

import sys
import json
import urllib.request
import zipfile
import io
import os
import argparse
import shutil

parser = argparse.ArgumentParser(description='Video organizer')
parser.add_argument('folder', help='Folder with videos')
parser.add_argument('destination', help='Folder with videos')
parser.add_argument('--move', dest = 'move', help='Move video files', action = 'store_true')
parser.add_argument('--language', help='Language of subtitles', default = 'cze')
args = parser.parse_args()

def is_video_ext(ext):
    return ext in ['.mkv', '.avi', '.mp4']

def pad_with_zero(s):
    if len(s) == 1:
        s = '0' + s
    return s

def get_imdb_info(imdb_id):
    return json.loads(urllib.request.urlopen('http://www.omdbapi.com/?i=' + imdb_id).read().decode('utf-8'))

def process_file(video_path):
    f = File(video_path)
    ext = os.path.splitext(video_path)[1]

    data = opensubtitles.search_subtitles([{'sublanguageid': args.language, 'moviehash': f.get_hash(), 'moviebytesize': f.size}])

    if len(data) == 0:
        print('No subtitles found')
        return False

    print('Found %d %s subtitles' % (len(data), args.language), end = '')

    max_download_count = -1
    subtitle = None
    for s in data:
        d = int(s['SubDownloadsCnt'])
        if d > max_download_count:
            max_download_count = d
            subtitle = s

    print(' with %d downloads' % max_download_count)

    url = subtitle['ZipDownloadLink']
    encoding = subtitle['SubEncoding']
    imdb_id = 'tt' + subtitle['IDMovieImdb'].rjust(7, '0')
    imdb_info = get_imdb_info (imdb_id)

    # series
    series_info = None
    if 'seriesID' in imdb_info:
        series_info = get_imdb_info(imdb_info['seriesID'])
        episode_info = imdb_info
        imdb_info = series_info

    title = imdb_info['Title']
    year = imdb_info['Year']
    if '–' in year:
        year = year[:year.find('–')]

    rating = imdb_info['imdbRating']
    print('Title: %s, score: %s, year: %s' % (title, rating, year))

    folder = os.path.join(args.destination, title + ' (%s, %s)' % (year, rating))
    if series_info != None:
        folder = os.path.join(folder, 'Season_' +pad_with_zero(episode_info['Season']))
        title = pad_with_zero(episode_info['Episode']) + '-' + episode_info['Title']

    if not os.path.exists(folder):
        os.makedirs(folder)

    response = urllib.request.urlopen(url)
    data = response.read()
    zf = zipfile.ZipFile(io.BytesIO(data), 'r')
    for name in zf.namelist():
        if name.endswith('.srt'):
            content = zf.read(name)
            with open(os.path.join(folder, title + '.srt'), 'w') as f:
                f.write(content.decode(encoding))
            break

    if args.move:
        destination = os.path.join(folder, title + ext)
        if os.path.abspath(video_path) != os.path.abspath(destination):
            print('Moving video: ' + title + ext)
            shutil.move(video_path, destination)
        else:
            print('Not moving: same location')

    return True

Settings.USER_AGENT = 'OSTestUserAgentTemp'
opensubtitles = OpenSubtitles()

token = opensubtitles.login('marxin', 'spartapraha')
if not type(token) == str:
    print("Can't login to opensubtitles.org")
    exit(1)

file_list = []

for root, dirs, files in os.walk(args.folder):
    for file in files:
        if is_video_ext(os.path.splitext(file)[1]):
            file_list.append(os.path.join(root, file))

unresolved = 0

for f in file_list:
    print('Processing: %s' % f)
    if not process_file(f):
        unresolved += 1
        
    print('')

print ('UNRESOLVED: %d' % unresolved)
