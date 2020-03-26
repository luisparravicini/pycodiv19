from pathlib import Path
from datetime import datetime
import requests
import sys
import re
from bs4 import BeautifulSoup
import json


def name_for(df):
    return df['Countries and territories'].iloc[0].replace('_', ' ')


def find_newest_dataset(download=True):
    date = datetime.today().strftime('%Y-%m-%d')
    fname_prefix = 'covid19-data-'
    fname = Path(f'{fname_prefix}{date}.xlsx')

    if not fname.exists():
        if download:
            print('looking for new data files')
            DOWNLOAD_URL = 'https://www.ecdc.europa.eu/en/publications-data/download-todays-data-geographic-distribution-covid-19-cases-worldwide'
            res = requests.get(DOWNLOAD_URL)
            res.raise_for_status()
            soup = BeautifulSoup(res.content, 'html.parser')
            link = soup.select_one('.download a')
            href = link.get('href')

            fname = Path('.', f'{fname_prefix}{date}.xlsx')
            if not fname.exists():
                print(f'fetching data file')
                res = requests.get(href)
                if res.status_code == 200:
                    with open(fname, 'wb') as f:
                        f.write(res.content)

        data_files = sorted(Path('.').glob(fname_prefix + '*'))
        if len(data_files) == 0:
            print('no data files')
            sys.exit(1)
        fname = data_files[-1]
        match = re.search(r'(\d{4}-\d{2}-\d{2})', str(fname))
        if match is None:
            print('couldn\'t extract date')
            sys.exit(1)
        date = match.group(1)
        print(f'using {fname}')

    return (fname, date)


def countries_population():
    path = Path('population.json')
    if path.exists():
        with open(path) as file:
            return json.load(file)

    print('fetching countries populations')
    res = requests.get('https://www.worldometers.info/world-population/population-by-country/')
    res.raise_for_status()

    population = dict()

    soup = BeautifulSoup(res.content, 'html.parser')
    for row in soup.table.find_all('tr'):
        cols = row.find_all('td')
        if len(cols) > 0:
            name = cols[1].text
            n = int(cols[2].text.replace(',', ''))
            population[name] = n

    with open(path, 'w') as file:
        json.dump(population, file)

    return population
