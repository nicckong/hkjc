import pandas as pd
import numpy as np
import urllib
from bs4 import BeautifulSoup
import re
import requests
from urllib.parse import urljoin
import warnings
from time import time
from math import cos, pi, floor

warnings.filterwarnings("ignore")

from math import cos, pi, floor
import requests

class hkjc:
  def __init__(self):
    self.url = 'https://racing.hkjc.com/racing/information/chinese/Racing/JKCScheduledRides.aspx'
    self.race_url = 'https://racing.hkjc.com/racing/information/chinese/Racing/RaceCard.aspx'
    self.start_url = "https://racing.hkjc.com"
    self.current_loc_dict = {}
    self.origin_age_dict = {}

  def parse_challenge(self, page):
      """
      Parse a challenge given by mmi and mavat's web servers, forcing us to solve
      some math stuff and send the result as a header to actually get the page.
      This logic is pretty much copied from https://github.com/R3dy/jigsaw-rails/blob/master/lib/breakbot.rb
      """
      top = page.split('<script>')[1].split('\n')
      challenge = top[1].split(';')[0].split('=')[1]
      challenge_id = top[2].split(';')[0].split('=')[1]
      return {'challenge': challenge, 'challenge_id': challenge_id, 'challenge_result': self.get_challenge_answer(challenge)}

  def get_challenge_answer(self, challenge):
      """
      Solve the math part of the challenge and get the result
      """
      arr = list(challenge)
      last_digit = int(arr[-1])
      arr.sort()
      min_digit = int(arr[0])
      subvar1 = (2 * int(arr[2])) + int(arr[1])
      subvar2 = str(2 * int(arr[2])) + arr[1]
      power = ((int(arr[0]) * 1) + 2) ** int(arr[1])
      x = (int(challenge) * 3 + subvar1)
      y = cos(pi * subvar1)
      answer = x * y
      answer -= power
      answer += (min_digit - last_digit)
      answer = str(int(floor(answer))) + subvar2
      return answer

  def getPage(self, url):
    s = requests.Session()
    r = s.get(url)

    if 'X-AA-Challenge' in r.text:
        challenge = self.parse_challenge(r.text)
        r = s.get(url, headers={
            'X-AA-Challenge': challenge['challenge'],
            'X-AA-Challenge-ID': challenge['challenge_id'],
            'X-AA-Challenge-Result': challenge['challenge_result']
        })

        yum = r.cookies
        r = s.get(url, cookies=yum)
    return r

  def horse_links(self):
    horse_info_links = []
    page = self.getPage(self.url)
    soup = BeautifulSoup(page.text, 'html.parser')
    try:
      table = soup.find('table', attrs= {'class': 'margin_top10 table_bd f_tac fon13'} )
      links = table.find_all('a', href=re.compile("HorseId="))
      for item in links:
          horse_info_links.append(urljoin(self.start_url, item['href']))
    except:
      table = soup.find('table', attrs = {'class': 'table_bd f_tac fon13'})
      links = table.find_all('a', href=re.compile("HorseId="))
      for item in links:
          horse_info_links.append(urljoin(self.start_url, item['href']))
    return horse_info_links

  def horse_df(self, url):
    page = self.getPage(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    name = soup.find('b').text.split('-')[-1].strip(' ')

    temp = soup.find('table', attrs = {'class':"table_top_right table_eng_text"}).find_all('td')
    for i in range(len(temp)):
      if temp[i].text == "現在位置(到達日期)":
        current_loc = temp[i+2].text
        break

    temp_table = soup.find('table', attrs={'class': "table_top_right table_eng_text"})
    origin_age = temp_table.find('tr').text.split('\n')[-2]

    table = soup.find_all(class_='bigborder')
    df = pd.read_html(str(table))

    df=df[0]
    df.columns=df.iloc[0]
    df=df.drop(0)
    # df=df.drop(columns='VideoReplay')
    df.drop('賽事 重播', axis = 1, inplace=True)
    df['馬名']=name
    df['season']=0
    for ind in range(len(df)):
      ind=ind+1
      # if (df['G'][ind] == df['Dist.'][ind]):
      #   c = df['G'][ind][:5]
      if (df['場地 狀況'][ind] == df['途程'][ind]):
        c = df['場地 狀況'][ind][:5]
      df['season'][ind]=c
    df['N_RaceIndex']=df['season']+"_"+df['場次']

    self.current_loc_dict[name] = current_loc
    self.origin_age_dict[name] = origin_age

    for ind in range(len(df)):
      ind=ind+1
      if (df['場地 狀況'][ind] == df['途程'][ind]):
        df['場地 狀況'][ind]="NaN"
    indexNames = df[ df['場地 狀況'] == "NaN" ].index
    df.drop(indexNames , inplace=True)
    return df

  def race_horse_df(self):
    df_list = []
    start_time = time()
    horse_info_links = self.horse_links()

    for link in horse_info_links:
        try:
            df = self.horse_df(link)
            df_list.append(df)
        except:
            continue

    result = pd.concat(df_list)
    result = result.reset_index(drop=True)
    result.columns = result.columns.str.replace(' ', '')
    result['日期'] = pd.to_datetime(result['日期'], format='%d/%m/%y')
    result['race_recency'] = result.groupby(['馬名'])['日期'].rank(ascending = False)
    result['日期'] = result['日期'].dt.strftime('%m-%d')
    return result

  def get_race_info(self):
    page = self.getPage(self.race_url)
    soup = BeautifulSoup(page.text, 'html.parser')
    races = soup.find('table' ,attrs={'class':'f_fs12 js_racecard'})
    race_info_links = []
    race_cards = []
    for i in races.find_all('a'):
      race_cards.append(urljoin('https://racing.hkjc.com/racing/information/Chinese/racing/RaceCard.aspx?', i['href']))
      race_info_links.append('https://bet.hkjc.com/racing/pages/odds_wp.aspx?lang=ch&'+i['href'].lower())

    race_info_links =  [i for i in race_info_links if 'hv' in i or 'st' in i]
    race_info_links.append(race_info_links[0][:-1]+ '1')

    race_cards =  [i for i in race_cards if 'HV' in i or 'ST' in i]
    race_cards.append(race_cards[0][:-1]+ '1')

    race_info_links = [i.replace('racecourse', 'venue') for i in race_info_links]
    old_date_format = re.search(r'(\d+/\d+/\d+)', race_info_links[0])[0]
    new_date_format = re.search(r'(\d+/\d+/\d+)', race_info_links[0])[0].replace('/', '-')
    race_info_links = [i.replace(old_date_format, new_date_format) for i in race_info_links]
    race_info_links = [i.replace('?racedate', 'date') for i in race_info_links]

    race_dict = {}

    for i in race_info_links:
      if 'st' in i:
        rc = '沙田'
      else:
        rc = '跑馬地'
      print (i)
      page = self.getPage(i)
      soup = BeautifulSoup(page.text, 'html.parser')
      s = soup.find('span', attrs = {'class' : "content"}).text
      race_dict[re.findall('\d+', i)[-1]] = re.findall('\d+', i)[-1] + '_'+ s.split(', ')[3].strip(' ')\
      + '_'+ s.split(', ')[-1].strip(' ') + '_'+ rc + ''.join(s.split(', ')[4:-1]).strip(' ')

    races = []
    for u in race_cards:
      page = self.getPage(u)
      soup = BeautifulSoup(page.text, 'html.parser')

      table = soup.find('table', attrs= {'class': 'starter f_tac f_fs13 draggable hiddenable'} )
      df_temp = pd.concat(pd.read_html(str(table)))
      df_temp['upcoming_race'] = race_dict[re.findall('\d+', u)[-1]]
      races.append(df_temp)

    df_race = pd.concat(races)
    df_race.drop(['綵衣', '配備', '排位體重'], axis = 1, inplace = True)

    df_race.upcoming_race = df_race.upcoming_race.str.replace('沙田全天候跑道', '沙田全天候')
    
    result = self.race_horse_df()

    df_race['current_loc'] = df_race["馬名"].map(self.current_loc_dict)
    df_race['origin_age'] = df_race["馬名"].map(self.origin_age_dict)
    return df_race, result

