import numpy as np
import datetime
import pandas as pd
from itertools import chain
import uuid
import os
import aiofiles
import rapidjson as json

def booksflow_find_level(price, level_size):
    return np.ceil(price / level_size) * level_size

def booksflow_compute_percent_variation(new_value, old_value):
    try:
        percentage_difference = ((new_value - old_value) / abs(old_value)) * 100
        return percentage_difference
    except:
        return 9999999999

def booksflow_manipulate_arrays(old_levels, new_levels, new_values):
    """
      helper for dynamically dealing with new columns
    """
    new_isolated_levels = np.setdiff1d(new_levels, old_levels)
    sorted_new_values = np.array([])
    for i in range(len(old_levels)):
        index = np.where(new_levels == old_levels[i])[0]
        if len(index) != 0:
            sorted_new_values = np.append(sorted_new_values, new_values[index])
        else:
            sorted_new_values = np.append(sorted_new_values,0)
    for i in range(len(new_isolated_levels)):
        index = np.where(new_levels == new_isolated_levels[i])[0]
        if len(index) != 0:
            sorted_new_values = np.append(sorted_new_values, new_values[index])    
        else:
            sorted_new_values = np.append(sorted_new_values,0)
    return sorted_new_values

def booksflow_datatrim(current_price, dataDict, side, book_ceil_thresh):
    keys_to_remove = []
    for level in dataDict[side].keys():
        if abs(booksflow_compute_percent_variation(float(level), current_price)) > book_ceil_thresh:
            keys_to_remove.append(level)
    for level in keys_to_remove:
        del dataDict[side][level]

def calculate_option_time_to_expire_deribit(date : str):                                  
    today_day = datetime.datetime.now().timetuple().tm_yday
    today_year = datetime.datetime.now().year
    f = datetime.datetime.strptime(date, "%d%b%y")
    expiration_date = f.timetuple().tm_yday
    expiration_year = f.year
    if today_year == expiration_year:
        r = expiration_date - today_day
    if today_year == expiration_year + 1:
        r = 365 + expiration_date - today_day
    return float(r)

def calculate_option_time_to_expire_okex(date):                                  
    today_day = datetime.datetime.now().timetuple().tm_yday
    today_year = datetime.datetime.now().year
    f = datetime.datetime.strptime(date, "%y%m%d")
    expiration_date = f.timetuple().tm_yday
    expiration_year = f.year
    if today_year == expiration_year:
        r = expiration_date - today_day
    if today_year == expiration_year + 1:
        r = 365 + expiration_date - today_day
    return float(r)

def calculate_option_time_to_expire_bybit(date):
    target_date = datetime.datetime.strptime(date, '%d%b%y')
    current_date = datetime.datetime.now()
    days_left = (target_date - current_date).days
    return int(days_left)


def merge_suffixes(n):
    """
        The maximum amount of datasets to aggregate is the len(alphabet). 
        Modify this function to get more aggregation possibilities
    """
    alphabet = 'xyzabcdefghijklmnopqrstuvw'
    suffixes = [f'_{alphabet[i]}' for i in range(n)]
    return suffixes

def oiflowOption_getcolumns(price_percentage_ranges: np.array):
    price_percentage_ranges = np.unique(np.sort(np.concatenate((price_percentage_ranges, -price_percentage_ranges)), axis=0))
    price_percentage_ranges[price_percentage_ranges == -0] = 0
    price_percentage_ranges[price_percentage_ranges == price_percentage_ranges[0]] = 0
    price_percentage_ranges = np.unique(price_percentage_ranges)
    columns = np.concatenate((np.array(['timestamp']), price_percentage_ranges), axis=0)
    return columns

def build_option_dataframes(expiration_ranges, ppr):
    columns = oiflowOption_getcolumns(ppr)
    df_dic = {}
    for i, exp_range in enumerate(expiration_ranges):
        if i in [0, len(expiration_ranges)-1]:
            df_dic[f'{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
            df_dic[f'{int(exp_range)}']['timestamp'] = pd.to_datetime([])
            df_dic[f'{int(exp_range)}'].set_index('timestamp', inplace=True)
        if i in [len(expiration_ranges)-1]:
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}']['timestamp'] = pd.to_datetime([])
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'].set_index('timestamp', inplace=True)
        else:
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'] = pd.DataFrame(columns=columns, dtype="float64") #.set_index('timestamp')
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}']['timestamp'] = pd.to_datetime([])
            df_dic[f'{int(expiration_ranges[i-1])}_{int(exp_range)}'].set_index('timestamp', inplace=True)
    df_dic.pop(f"{int(np.max(expiration_ranges))}_{int(np.min(expiration_ranges))}")
    return df_dic


def oiflowOption_getranges(price_percentage_ranges: np.array):
    price_percentage_ranges = np.unique(np.sort(np.concatenate((price_percentage_ranges, -price_percentage_ranges)), axis=0))
    price_percentage_ranges[price_percentage_ranges == -0] = 0
    price_percentage_ranges[price_percentage_ranges == price_percentage_ranges[0]] = 0
    price_percentage_ranges = np.unique(price_percentage_ranges)
    return price_percentage_ranges


def oiflowOption_dictionary_helper(dfs, countdowns):
    countdown_ranges = list(dfs.keys())
    countdowns = np.unique(countdowns)
    countdown_ranges_flt = sorted(list(set(([float(item) for sublist in [x.split('_') for x in countdown_ranges] for item in sublist]))))
    mx = max(countdown_ranges_flt)
    mn = min(countdown_ranges_flt)
    l = {key: [] for key in countdown_ranges}
    for index, cf in enumerate(countdown_ranges_flt):
      for v in countdowns.tolist():
          if cf == mn and v <= cf:
              l[str(int(cf))].append(v)
          if cf != mn and v <= cf and v > countdown_ranges_flt[index-1]:
              l[f"{str(int(countdown_ranges_flt[index-1]))}_{str(int(cf))}"].append(v)
          if cf == mx and v > cf:
              l[str(int(cf))].append(v)
    return l

def getpcd(center, value):
    if center == 0 and value > center:
        return float(100)
    if value == 0 and value < center:
        return float(9999999999)
    else:
        diff = value - center
        average = (center + value) / 2
        percentage_diff = (diff / average) * 100
        return percentage_diff

def oiflowOption_choose_range(ppr, value):
    for index, r in enumerate(ppr):
        if index == 0 and value < r:
            return ppr[0]
        if index == len(ppr)-1 and value > r:
            return ppr[-1]
        if value < r and value >= ppr[index-1]:
            return r
        

def oiflow_merge_columns(common_columns_dic, oidf):
    new_data = pd.DataFrame(dtype="float64")
    commoncolumnsDict = {key: value for key, value in common_columns_dic.items() if key not in ["oi", "price", "fundingRate"]}
    for common_columns in commoncolumnsDict.keys():
        for index, column in enumerate(commoncolumnsDict[common_columns]):
            if index == 0:
                new_data[common_columns] = oidf[column]
            else:
                new_data[common_columns] = new_data[common_columns] + oidf[column]
    return new_data


def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if isinstance(item, list):
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list

def synthesis_Trades_mergeDict(dictionaries):
    concatenated_dict = {key : [] for d in dictionaries for key in d.keys()}
    for d in dictionaries:
        for key, value in d.items():
            concatenated_dict[key].append(value)
    return flatten_list(concatenated_dict.values())



def last_non_zero(arr):
    for i in range(-1, -len(arr) - 1, -1):
        if arr[i] != 0:
            return arr[i]
    return None  # Return None if the array is all zeros

def is_valid_dataframe(df):
    return df is not None and isinstance(df, pd.DataFrame)



class MockCouchDB:
    def __init__(self, filename, folder_name="", buffer_size=1024):
        self.file_path =  folder_name + "/" + filename + ".json"
        self.buffer_size = buffer_size

    async def save(self, data, market_state, connection_data, on_message:callable):
        try:
            data = await on_message(data=data, market_state=market_state, connection_data=connection_data)
        except Exception as e:
            print(e)
            return
        data["_doc"] = str(uuid.uuid4())

        if not os.path.exists(self.file_path):
            async with aiofiles.open(self.file_path ,mode='w') as f:
                content = []
                content.insert(0, data)
                await f.seek(0)  
                await f.truncate() 
                await f.write(json.dumps(content, indent=2)) 
        else:
            async with aiofiles.open(self.file_path ,mode='r+') as f: 
                content = await f.read()
                content = json.loads(content)
                content.insert(0, data)
                content = json.dumps(content)
                await f.seek(0)  
                await f.truncate() 
                await f.write(content)

def insert_into_CouchDB(self, data, connection_dict, on_message:callable):
    getattr(self, f"db_{connection_dict.get('id_ws')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=on_message)

def insert_into_CouchDB_2(self, data, connection_dict, on_message:callable):
    getattr(self, f"db_{connection_dict.get('id_api_2')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=on_message)
    
async def insert_into_mockCouchDB(self, data, connection_dict):
    try:
        await getattr(self, f"db_{connection_dict.get('id_ws')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=connection_dict.get("on_message_method_ws"))
    except Exception as e:
        print(f'{connection_dict.get("id_ws")} is not working properly' )
        print(e)

async def insert_into_mockCouchDB_2(self, data, connection_dict):
    try:
        await getattr(self, f"db_{connection_dict.get('id_api_2')}").save(data=data, market_state=self.market_state, connection_data=connection_dict, on_message=connection_dict.get("on_message_method_api_2"))
    except Exception as e:
        print(f'{connection_dict.get("id_api_2")} is not working properly' )
        print(e)

async def insert_into_mockCouchDB_3(self, data, connection_dict):
    try:
        await getattr(self, f"db_{connection_dict.get('id_api')}").save(data=data, market_state=self.market_state, connection_data=connection_dict,  on_message=connection_dict.get("on_message_method_api"))
    except Exception as e:
        print(f'{connection_dict.get("id_api")} is not working properly' )
        print(e) 

async def ws_fetcher_helper(function):
    data = await function()
    return data