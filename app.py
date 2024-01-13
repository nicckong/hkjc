import streamlit as st
import pandas as pd
import numpy as np
import regex as re
from hkjc import hkjc
  
st.header("🐴🏇🏼Giddy Up🏇🏼🐴")
st.caption("-- where horsing around meets the joy of learning and exploration --")

# st.markdown("![Alt Text](https://media.tenor.com/_x9RKnwqMkYAAAAd/kramer-cosmo.gif)")

@st.cache_data
def load_data():
    df_race, result, df_track_stats  = hkjc().get_race_info()
    return df_race, result, df_track_stats 
 
# Create a text element and let the reader know the data is loading.
data_load_state = st.text('Loading data...')
# Load 10,000 rows of data into the dataframe.
df_race, result, df_track_stats = load_data()
# Notify the reader that the data was successfully loaded.
data_load_state.text('Loading data...done!')
 
# if st.checkbox('Show raw data'):
#     st.write(data)

#choose race 
df_race['upcoming_race_no'] = df_race['upcoming_race'].apply(lambda x: x.split('_')[0])
df_race.upcoming_race_no = df_race.upcoming_race_no.astype(int)
race_no = st.radio("Choose Race No.", (range(1, df_race.upcoming_race_no.max()+1)), horizontal = True)

upcoming_race = ' '.join(df_race[df_race.upcoming_race_no == race_no].upcoming_race.unique()[0].split('_')[1:])

st.subheader(upcoming_race)

f = False
 
# condition
if len(upcoming_race.split(' ')) == 4:
    field_condition = upcoming_race.split(' ')[1]
    race = upcoming_race.split(' ')[2]
    dist = upcoming_race.split(' ')[-1][:-1]
    if '黏' in field_condition or '濕' in field_condition:
        f = True
else:
    if "全天候" in upcoming_race:
        race = "全天候"
        dist = upcoming_race.split(' ')[-1][-5:-1]
        if "濕" in upcoming_race or '黏' in upcoming_race:
            f = True

    else:
        race = upcoming_race.split(' ')[-1]
        dist = upcoming_race.split(' ')[1][:-1]
recent_results = result.query('race_recency <= 6')
    
recent_results_agg = recent_results.pivot_table(index=['馬名'],
                        values=['日期', '馬場/跑道/賽道', '途程', '場地狀況', '賽事班次', '檔位', '騎師', '練馬師', '實際負磅'],
                        aggfunc=lambda x: "|".join(str(v) for v in x)).reset_index()
data = df_race.merge(recent_results_agg, on = '馬名', how = 'left') 
data_vet = df_race[['upcoming_race_no', '馬匹編號', '馬名', 'vet_date', 'vet_details', 'vet_pass_date']]
data_vet.dropna(subset=['vet_date'], inplace=True)
data_vet.columns = ['upcoming_race_no', 'horse_no', 'horse_name', 'vet_date', 'vet_details', 'vet_pass_date']
data.drop(['vet_date', 'vet_details', 'vet_pass_date'], axis=1, inplace=True)

if data.shape[1] == 23:
    data.columns = ['horse_no', 'past_pla', 'horse_name', 'weight', 'jockey', 'draw', 'trainer', 'rating', 'rating_change',
                    'priority', 'upcoming_race', 'current_loc', 'origin_age',
                    'upcoming_race_no','going', 'wt', 'past_race_dates', 'past_draws', 'past_trainers','past_race_classes', 'past_dist',
                    'past_races_info', 'past_jockeys']
else: 
    data.columns = ['horse_no', 'past_pla', 'horse_name', 'weight','jockey', 'draw', 'trainer', 'rating', 'rating_change',
                    'priority', 'upcoming_race', 'international_rating', 'current_loc', 'origin_age',
                    'upcoming_race_no','going', 'wt', 'past_race_dates', 'past_draws', 'past_trainers','past_race_classes', 'past_dist',
                    'past_races_info', 'past_jockeys']
data.jockey = data.jockey.str.replace(r'[\(\-\d+)]', '')
data.trainer = data.trainer.str.replace(r'[\(\-\d+)]', '')

def jockey(df):
  try:
    if df.jockey in df.past_jockeys:
      return 'Y'
    else:
      return 'N'
  except:
    return 'N'

def trainer(df):
  try:
    if df.trainer in df.past_trainers:
      return 'Y'
    else:
      return 'N'
  except:
    return 'N'

data["rode_before"] = data.apply(jockey, axis = 1)
data["trained_before"] = data.apply(trainer, axis = 1)

filtered_data = data[data.upcoming_race_no == race_no].drop(['upcoming_race_no', 'upcoming_race'], axis = 1).set_index('horse_no')
filtered_data_vet = data_vet[data_vet.upcoming_race_no == race_no].drop(['upcoming_race_no'], axis=1).set_index('horse_no')
filtered_data_track = df_track_stats[df_track_stats.upcoming_race_no == race_no].drop(['upcoming_race_no'], axis=1).set_index('draw')
  
def color_rode_before(val):
    color = 'red' if val=="N" else 'green'
    # return f'background-color: {color}'
    return f'color: {color}'

def color_trained_before(val):
    color = 'red' if val=="N" else 'green'
    # return f'background-color: {color}'
    return f'color: {color}'

#new race track
df_temp = filtered_data.query('~past_races_info.isnull()')
new_track = df_temp[~df_temp.past_races_info.str.contains(race)].horse_name.unique()

if len(new_track) > 0:
    st.write('New to ', race, ':' , ', '.join(new_track))

#new distance 
df_temp = filtered_data.query('~past_dist.isnull()')
new_dist = df_temp[~df_temp.past_dist.str.contains(dist)].horse_name.unique()

if len(new_dist) > 0:
    st.write('New to ', dist, ':' , ', '.join(new_dist))

#new trainer
new_trainer = filtered_data[(filtered_data.trained_before == "N") & (~filtered_data.past_draws.isnull())].horse_name.unique()

for i in range(len(new_trainer)):
    old_trainer = set(filtered_data[filtered_data.horse_name == new_trainer[i]].past_trainers.values.tolist()[0].split('|'))
    new_trainer[i] = new_trainer[i] + '('+ ','.join(old_trainer)+ ')'

if len(new_trainer) > 0:
    st.write("New Trainer:", ', '.join(new_trainer))
    
if len(filtered_data_vet) > 0:
    st.write('Vet Records')
    st.dataframe(filtered_data_vet)
        
filtered_data = filtered_data.drop(['past_trainers', 'weight', 'priority', 'trained_before', 'current_loc'], 
                                   axis = 1) 

col_order = ['horse_name',  'draw', 'past_pla', 'jockey','rode_before', 'trainer', 'rating',
             'going', 'past_draws', 'past_race_classes', 'past_dist',
             'past_races_info', 'past_race_dates', 'past_jockeys', 'wt',
             'origin_age', 'rating_change']

filtered_data = filtered_data[col_order]

st.write('Data')
st.dataframe(filtered_data.style.applymap(color_rode_before, subset=['rode_before'])
             , height = (filtered_data.shape[0] + 1) * 35 + 5)


st.write('Track Stats')
st.dataframe(filtered_data_track.iloc[:-1, :])
st.write(' '.join(filtered_data_track.iloc[-1, :2].tolist()))

if f == True:
    field_condition = upcoming_race.split(' ')[1]
    df_field = result[(result.場地狀況.str.contains(field_condition[:-1])) & (result.名次 != "WV")]
    df_field_agg = df_field .pivot_table(index=['馬名'],
                values=['名次','日期', '馬場/跑道/賽道', '途程', '場地狀況', '賽事班次', '檔位', '騎師', '練馬師'],
                aggfunc=lambda x: "|".join(str(v) for v in x)).reset_index()
    data_field = df_race.merge(df_field_agg, on = '馬名', how = 'inner') 
    data_field.drop('6次近績', axis =1, inplace=True)
    data_field.columns = ['horse_no', 'horse_name', 'weight','jockey', 'draw', 'trainer', 
                            'rating', 'rating_change','priority', 'upcoming_race', 'current_loc', 'origin_age',
                            'upcoming_race_no', 'past_pla', 'going', 'past_race_dates', 'past_draws', 
                            'past_trainers','past_race_classes', 'past_dist','past_races_info', 'past_jockeys']
    data_field.jockey = data_field.jockey.str.replace(r'[\(\-\d+)]', '')
    data_field.trainer = data_field.trainer.str.replace(r'[\(\-\d+)]', '')
    data_field["rode_before"] = data_field.apply(jockey, axis = 1)
    data_field["trained_before"] = data_field.apply(trainer, axis = 1)
    
    filtered_data_field = data_field[data_field.upcoming_race_no == race_no].drop(['upcoming_race_no', 'upcoming_race'], axis = 1).set_index('horse_no')
    
    if len(filtered_data_field) > 0:
        filtered_data_field = filtered_data_field[col_order]
        st.write(field_condition)
        st.dataframe(filtered_data_field.style.applymap(color_rode_before, subset=['rode_before']))
        
        