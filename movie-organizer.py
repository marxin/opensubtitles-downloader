#!/usr/bin/env python3

from pythonopensubtitles.opensubtitles import OpenSubtitles
from pythonopensubtitles.utils import File

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
parser.add_argument('destination',  help='Folder with videos')
args = parser.parse_args()

def is_video_ext(ext):
    return ext in ['.mkv', '.avi', '.mp4']

def get_imdb_info(imdb_id):
    return json.loads(urllib.request.urlopen('http://www.omdbapi.com/?i=' + imdb_id).read().decode('utf-8'))

def process_file(video_path):
    f = File(video_path)
    ext = os.path.splitext(video_path)[1]

    data = opensubtitles.search_subtitles([{'sublanguageid': 'cze', 'moviehash': f.get_hash(), 'moviebytesize': f.size}])

    if len(data) == 0:
        print('No subtitles found')
        return False

    print('Found %d CZE subtitles' % len(data))

    subtitle = data[0]
    url = subtitle['ZipDownloadLink']    
    encoding = subtitle['SubEncoding']
    imdb_id = 'tt' + subtitle['IDMovieImdb'].rjust(7, '0')
    imdb_info = get_imdb_info (imdb_id)
    title = imdb_info['Title']
    year = imdb_info['Year']
    rating = imdb_info['imdbRating']
    print('Title: %s, score: %s, year: %s' % (title, rating, year))

    folder = os.path.join(args.destination, title + ' (%s, %s)' % (year, rating))
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

    return True

    # TODO
    # copy video
    # shutil.copy(video_path, os.path.join(folder, title + ext))

opensubtitles = OpenSubtitles()

token = opensubtitles.login('marxin', 'spartapraha')
assert type(token) == str

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
