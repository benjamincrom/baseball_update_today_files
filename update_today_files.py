from datetime import timedelta, datetime
from os import environ, makedirs
from os.path import exists, dirname
from re import findall
from subprocess import check_output
from urllib.request import urlopen

from boto3 import session


BUCKET = 'spaces-host'
FOLDER = 'livebaseballscorecards-artifacts'
ZIP_TEMPLATE = 'https://spaces-host.nyc3.digitaloceanspaces.com/{}/{}'
FILENAME_TEMPLATE = 'baseball_files_{}.zip'
LINK_TEMPLATE = (
    'http://gd2.mlb.com/components/game/mlb/year_{year}/month_{month}/day_{day}/'
)


this_session = session.Session()
client = this_session.client(
    's3',
    region_name='nyc3',
    endpoint_url='https://nyc3.digitaloceanspaces.com',
    aws_access_key_id=environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=environ.get('AWS_SECRET_ACCESS_KEY')
)


def ensure_folder(filename):
    if not exists(dirname(filename)):
        makedirs(dirname(filename))

def fetch_xml_files_for_datetime(this_datetime):
    year = str(this_datetime.year)
    month = str(this_datetime.month).zfill(2)
    day = str(this_datetime.day).zfill(2)

    filename = FILENAME_TEMPLATE.format(year)
    zip_url = ZIP_TEMPLATE.format(FOLDER, filename)
    link = LINK_TEMPLATE.format(year=year, month=month, day=day)

    content = str(urlopen(link).read())
    game_id_list = findall(r'>\s*(gid\_\w+)/<', content)

    for game_id in game_id_list:
        game_link = link + '{}/'.format(game_id)
        boxscore_link = game_link + 'boxscore.xml'
        players_link = game_link + 'players.xml'
        inning_link = game_link + 'inning/inning_all.xml'

        boxscore_xml = urlopen(boxscore_link).read().decode('utf-8')
        boxscore_key = boxscore_link.split('game/mlb/year_')[1]
        players_xml = urlopen(players_link).read().decode('utf-8')
        players_key = players_link.split('game/mlb/year_')[1]
        inning_xml = urlopen(inning_link).read().decode('utf-8')
        inning_key = inning_link.split('game/mlb/year_')[1]

        ensure_folder(boxscore_key)
        with open(boxscore_key, 'w') as fh:
          fh.write(boxscore_xml)

        ensure_folder(players_key)
        with open(players_key, 'w') as fh:
          fh.write(players_xml)

        ensure_folder(inning_key)
        with open(inning_key, 'w') as fh:
          fh.write(inning_xml)

    if game_id_list:
        check_output(['rm', '-f', zip_url.split('/')[-1]])
        check_output(['wget', '{}'.format(zip_url)])
        check_output(['zip', '-ur', filename, year])

        client.upload_file(Filename=filename,
                           Bucket=BUCKET,
                           Key='{}/{}'.format(FOLDER, filename),
                           ExtraArgs={'ACL': 'public-read'})

        check_output(['rm', '-rf', filename, year])

def main():
    time_shift = timedelta(hours=14)
    today = datetime.utcnow() - time_shift

    fetch_xml_files_for_datetime(today)

if __name__ == '__main__':
    main()
