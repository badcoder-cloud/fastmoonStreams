import asyncio
import re
from .utilis import *
from .clientpoints_.binance import binance_instType_help
from typing import Callable, Any
import sys
from logging.handlers import RotatingFileHandler
import backoff
from .errors import aiohttp_recoverable_errors 
from pathlib import Path
import time
from functools import wraps, partial
base_path = Path(__file__).parent.parent
log_file_bytes = 10*1024*1024,
log_file_backup_count = 5,


class CommonFunctionality:
    
    def __init__(self):
        self.max_reconnect_retries = "its a reference"

    
    def wrapper_create_tasks(self, func):
        """ wrapper for aiohttp tasks"""
        @wraps(func)
        async def inner_wrapper_create_tasks(self, connection_data, lag, *args, **kwargs):
            try:
                connection_start_time = time.time()
                id_api = connection_data.get("id_api")
                await func(self, lag, *args, **kwargs)
            except aiohttp_recoverable_errors as e:
                self.logger.exception("Error from %s: %s", id_api, e, exc_info=True)
                if "CONNECTION_DURATION" in self.producer_metrics:
                    duration = time.time() - connection_start_time
                    self.CONNECTION_DURATION.labels(websocket_id=id_api).set(duration)
                if "ERRORS_DISCONNECTS" in self.producer_metrics:
                    self.ERRORS_DISCONNECTS.labels(websocket_id=id_api).inc()
                raise
            except Exception as e:
                self.logger.exception("Error from %s: %s. The coroutine was completely closed or broken", id_api, e, exc_info=True)
                if "ERRORS_DISCONNECTS" in self.producer_metrics:
                    self.ERRORS_DISCONNECTS.labels(websocket_id=id_api).inc()
        return backoff.on_exception(
                backoff.expo,
                aiohttp_recoverable_errors,
                max_tries=self.max_reconnect_retries,
                max_time=300
            )(inner_wrapper_create_tasks)
        
    def wrapper_update_symbols(func):
        """ patter for method of updating symbols"""
        async def inner_wrapper_update_symbols(self, list_of_functions, lag=0, update_interval=60*24, *args, **kwargs):
            await asyncio.sleep(lag)
            while self.running:
                task = asyncio.create_task(self.get_binance_instruments())
                await task
                await asyncio.sleep(update_interval)
                
        
    @staticmethod
    def log_exceptions(func):
        """ exception wrapper for datainput"""
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except ValueError as e:
                self.logger.exception(f"ValueError in {func.__name__}: {e}")
            except KeyError as e:
                self.logger.exception(f"KeyError in {func.__name__}: {e}")
            except asyncio.TimeoutError as e:
                self.logger.exception(f"TimeoutError in {func.__name__}: {e}")
            except ConnectionError as e:
                self.logger.exception(f"ConnectionError in {func.__name__}: {e}")
            except IndexError as e:
                self.logger.exception(f"IndexError in {func.__name__}: {e}")
            except TypeError as e:
                self.logger.exception(f"TypeError in {func.__name__}: {e}")
            except AttributeError as e:
                self.logger.exception(f"AttributeError in {func.__name__}: {e}")
            except RuntimeError as e:
                self.logger.exception(f"RuntimeError in {func.__name__}: {e}")
            except Exception as e:
                self.logger.exception(f"Unexpected error in {func.__name__}: {e}")
                raise
            
        return wrapper
            


class binance_aoihttp_oioption_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, binance_get_option_expiries_method:callable, aiohttpfetch:callable):
        super().__init__()
        self.underlying_asset = underlying_asset
        self.expiries = []
        self.get_expiries = binance_get_option_expiries_method
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1



    async def get_binance_instruments(self):
        expiries = await self.get_expiries(self.underlying_asset)
        self.expiries = expiries
        
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(update_interval)
            
        # await asyncio.sleep(lag)
        # id_api = self.connection_data.get("id_api")
        # connection_start_time = time.time()
        # try:
        #     while self.running:
        #         task = asyncio.create_task(self.aiomethod())
        #         await task
        #         for message in self.data.values():
        #             await self.send_message_to_topic(self.topic_name, message)
        #             message_encoded = message.encode("utf-8")
        #             print(sys.getsizeof(message_encoded))
        #         await asyncio.sleep(self.pullTimeout)

    async def create_task_helper(self, symbol, expiration, special_method):
        while 
        data = await self.fetcher("option", "oi", symbol=symbol, specialParam=expiration,  special_method=special_method)
        self.data[expiration] = data
        

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        """
            BTC, ETH ...
            latency : seconds to wait before api call
        """
        tasks = []
        for expiration in self.expiries:
            tasks.append(self.helper(self.underlying_asset, expiration, "oioption"))
                    
        for expiry in self.expiries:
            if expiry not in self.data.copy():
                self.expiries.remove(expiry)
        
        return tasks

class binance_aoihttp_posfutureperp_manager():
    """
        I after examining instruments related to BTC, ETHBTC instrument was present but its not suppoused to be. 
        So info API has some mistakes on binance side and it was fixed by filtering all of the symbols that doesnt contain USD
    """

    def __init__ (self, underlying_asset, info_linear:callable, aiohttpfetch:callable):
        super().__init__()
        self.running = True
        self.underlying_asset = underlying_asset
        self.linear_symbols = []
        self.inverse_symbol = underlying_asset + "USD"
        self.info_linear_method = info_linear
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""
        
    async def get_binance_instruments(self):
        self.linear_symbols = await self.info_linear_method(self.underlying_asset)
        self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x]
    
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def helper_1(self, instType, objective, symbol):
        data = await self.fetcher(instType, objective, symbol=symbol, special_method="posfutureperp")
        if data == "[]" and symbol in self.linear_symbols:
            self.linear_symbols.remove(symbol)
        self.data[f"{symbol}_{objective}"] = data


    async def helper_2(self, instType, objective, coinm_symbol):
        data = await self.fetcher(instType, objective, symbol=coinm_symbol, special_method="posfutureperp")
        self.data[coinm_symbol+f"coinmAgg_{objective}"] = data

    # @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for symbol in self.linear_symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            for objective in ["tta", "ttp", "gta"]:
                marginType = binance_instType_help(symbol)
                symbol = symbol if marginType == "Linear" else symbol.replace("_", "").replace("PERP", "")
                tasks.append(self.helper_1(instType, objective, symbol))
        for objective in ["tta", "ttp", "gta"]:
            tasks.append(self.helper_2("perpetual", objective, self.inverse_symbol))
            
        await asyncio.gather(*tasks)

        keys = [f"{x}_{o}" for x in self.linear_symbols for o in ["tta", "ttp", "gta"]] + [self.inverse_symbol+f"coinmAgg_{o}" for o in ["tta", "ttp", "gta"]]
        for key in self.data.copy():
            if key not in keys:
                del self.data[key]
                
                
                

class binance_aoihttp_oifutureperp_manager():

    def __init__ (self, underlying_asset, info_linear_method:callable, info_inverse_method:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.info_linear_method = info_linear_method
        self.info_inverse_method = info_inverse_method
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.linear_symbols = []
        self.inverse_symbols = []
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""
        
    # @with_backoff
    async def fetch_data_2(self, lag):
        await asyncio.sleep(lag)
        id_api = self.connection_data.get("id_api")
        connection_start_time = time.time()
        try:
            while self.running:
                task = asyncio.create_task(self.aiomethod_2())
                await task
                for message in self.data.values():
                    await self.send_message_to_topic(self.topic_name, message)
                    message_encoded = message.encode("utf-8")
                    print(sys.getsizeof(message_encoded))
                await asyncio.sleep(self.pullTimeout)
        except aiohttp_recoverable_errors as e:
            self.logger.exception("Error from %s: %s", id_api, e, exc_info=True)
            if "CONNECTION_DURATION" in self.producer_metrics:
                duration = time.time() - connection_start_time
                self.CONNECTION_DURATION.labels(websocket_id=id_api).set(duration)
            if "ERRORS_DISCONNECTS" in self.producer_metrics:
                self.ERRORS_DISCONNECTS.labels(websocket_id=id_api).inc()
            raise
        except Exception as e:
            self.logger.exception("Error from %s: %s. The coroutine was completely closed or broken", self.connection_data.get('id_api'), e, exc_info=True)
            if "ERRORS_DISCONNECTS" in self.producer_metrics:
                self.ERRORS_DISCONNECTS.labels(websocket_id=id_api).inc()

    async def get_binance_instruments(self):
        self.linear_symbols = await self.info_linear_method(self.underlying_asset)
        self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x]
        self.inverse_symbols = await self.info_inverse_method(self.underlying_asset)
        self.inverse_symbols = [x for x in self.inverse_symbols if self.underlying_asset in x and "USD" in  x]  
    
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def helper(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        if "code" not in data:
            self.data[f"{symbol}_{instType}"] = data
        else:
            if "USD" in symbol:
                self.inverse_symbols.remove(symbol)
            else:
                self.linear_symbols.remove(symbol)

    # @CommonFunctionality.log_exceptions
    async def aiomethod_2(self):
        tasks = []
        for symbol in self.linear_symbols + self.inverse_symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            tasks.append(self.helper(instType, symbol))    
        await asyncio.gather(*tasks)

        all_symbols = self.linear_symbols + self.inverse_symbols

        for key in self.data.copy():
            if len([x for x in all_symbols if x in key]) == 0:
                del self.data[key]
        
class binance_aoihttp_fundperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info_linear_method:callable, info_inverse_method:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.info_linear_method = info_linear_method
        self.info_inverse_method = info_inverse_method
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.linear_symbols = []
        self.inverse_symbols = []
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""

    async def get_binance_instruments(self):
        self.linear_symbols = await self.info_linear_method(self.underlying_asset)
        self.linear_symbols = [x for x in self.linear_symbols if self.underlying_asset in x and "USD" in  x and bool(re.search(r'\d', x.split("_")[-1])) is False]
        self.inverse_symbols = await self.info_inverse_method(self.underlying_asset)
        self.inverse_symbols = [x for x in self.inverse_symbols if self.underlying_asset in x and "USD" in  x and bool(re.search(r'\d', x.split("_")[-1])) is False]  

    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_binance_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def fetch_fund_binance_yeye(self, instType, symbol):
        data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
        self.data[f"{symbol}_{instType}"] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for symbol in self.linear_symbols + self.inverse_symbols:
            instType = "future" if bool(re.search(r'\d', symbol.split("_")[-1])) else "perpetual"
            if not bool(re.search(r'\d', symbol.split("_")[-1])):
                tasks.append(self.fetch_fund_binance_yeye(instType, symbol))
        await asyncio.gather(*tasks)    

class bybit_aoihttp_oifutureperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info_linear:callable, info_inverse:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info_linear = info_linear
        self.info_inverse = info_inverse
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""

    async def get_bybit_instruments(self):
        self.symbols_inverse = await self.info_inverse(self.underlying_asset)
        self.symbols_linear = await self.info_linear(self.underlying_asset)
    
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def h1(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        self.data[symbol] = data

    async def h2(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol=symbol, special_method="oifutureperp")
        self.data[symbol] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_linear:
            instType = "future" if "-" in symbol else "perpetual"
            tasks.append(self.h1(instType, symbol))
        for symbol in self.symbols_inverse:
            instType = "future" if "-" in symbol else "perpetual"
            tasks.append(self.h2(instType, symbol))
        await asyncio.gather(*tasks)

        all_symbols = self.symbols_inverse + self.symbols_linear

        for key in self.data.copy():
            if len([x for x in all_symbols if x in key]) == 0:
                del self.data[key]
        
class bybit_aoihttp_posfutureperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info_linear, info_inverse, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info_linear = info_linear
        self.info_inverse = info_inverse
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""

    async def get_bybit_instruments(self):
        self.symbols_inverse = await self.info_inverse(self.underlying_asset)
        self.symbols_linear = await self.info_linear(self.underlying_asset)
        self.symbols_inverse = [s for s in self.symbols_inverse if len(s.split("-")) == 1]
        self.symbols_linear = [s for s in self.symbols_linear if len(s.split("-")) == 1]
    
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments())
            await task
            await asyncio.sleep(update_interval) 

    async def h1(self, symbol, instType):
        data = await self.fetcher(instType, "gta", symbol=symbol, special_method="posfutureperp")
        self.data["Linear_"+symbol] = data

    async def h2(self, instType, symbol):
        data = await self.fetcher(instType, "gta", symbol=symbol, special_method="posfutureperp")
        self.data["Inverse_"+symbol] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_linear:
            symbol = symbol.replace("PERP", "USD") if "PERP" in symbol else symbol
            instType = "future" if "-" in symbol else "perpetual"
            tasks.append(self.h1(symbol, instType))
        for symbol in self.symbols_inverse:
            symbol = symbol.replace("PERP", "USD") if "PERP" in symbol else symbol
            instType = "future" if "-" in symbol else "perpetual"
            tasks.append(self.h2(instType, symbol))
        await asyncio.gather(*tasks)

        all_symbols = self.symbols_inverse + self.symbols_linear

        for key in self.data.copy():
            if len([x for x in all_symbols if x in key]) == 0:
                del self.data[key]
    
class bybit_aoihttp_fundperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info_linear, info_inverse, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_linear = []
        self.symbols_inverse = []
        self.info_linear = info_linear
        self.info_inverse = info_inverse
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""


    async def get_bybit_instruments(self):
        self.symbols_inverse = await self.info_inverse(self.underlying_asset)
        self.symbols_linear = await self.info_linear(self.underlying_asset)
        self.symbols_inverse = [s for s in self.symbols_inverse if len(s.split("-")) == 1]
        self.symbols_linear = [s for s in self.symbols_linear if len(s.split("-")) == 1]
    
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bybit_instruments())
            await task
            await asyncio.sleep(update_interval) 

    async def h1(self, instType, symbol):
        data = await self.fetcher(instType, "funding", symbol=symbol, special_method="fundperp")
        self.data[symbol] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_linear + self.symbols_inverse:
            instType = "future" if "-" in symbol else "perpetual"
            if instType == "perpetual":
                tasks.append(self.h1(instType, symbol))
        await asyncio.gather(*tasks)

        for k, d in self.data.copy().items():
            if len(d) < 140:
                del self.data[k]
                self.symbols_linear = [item for item in self.symbols_linear if item != k]
                self.symbols_inverse = [item for item in self.symbols_inverse if item != k]
        
class okx_aoihttp_oifutureperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info_perpetual:callable, info_future:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_future = []
        self.symbols_perpetual = []
        self.info_perpetual = info_perpetual
        self.info_future = info_future
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.symbols_perpetual = []
        self.symbols_future = []
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""

    async def get_okx_instruments(self):
        self.symbols_future = await self.info_future(self.underlying_asset)
        self.symbols_perpetual = await self.info_perpetual(self.underlying_asset)
    
    async def update_symbols(self, lag=0, update_time=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_okx_instruments())
            await task
            await asyncio.sleep(update_time)  

    async def h1(self, instType, symbol):
        data = await self.fetcher(instType, "oi", symbol)
        self.data[symbol] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for s in self.symbols_perpetual:
            tasks.append(self.h1("perpetual", s))
        for s in self.symbols_future:
            tasks.append(self.h1("future", s))
        await asyncio.gather(*tasks)

        all_symbols = self.symbols_perpetual + self.symbols_future

        for key in self.data.copy():
            if len([x for x in all_symbols if x == key]) == 0:
                del self.data[key]

class okx_aoihttp_fundperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info_perpetual:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_future = []
        self.symbols_perpetual = []
        self.info_perpetual = info_perpetual
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.symbols_perpetual = []
        self.symbols_future = []
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""


    async def get_okx_instruments(self):
        self.symbols_perpetual = await self.info_perpetual(self.underlying_asset)
    
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_okx_instruments())
            await task
            await asyncio.sleep(update_interval)  

    async def h1(self, symbol):
        response = await self.fetcher("perpetual", "funding", symbol)
        self.data[symbol] = response

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for symbol in self.symbols_perpetual:
            tasks.append(self.h1(symbol))
        await asyncio.gather(*tasks)

        for key in self.data.copy():
            if len([x for x in self.symbols_perpetual if x == key]) == 0:
                del self.data[key]

class bitget_aoihttp_oifutureperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_perpetual = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""

    async def get_bitget_perpetual_symbols(self):
        self.symbols_perpetual = await self.info(self.underlying_asset)
    
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bitget_perpetual_symbols())
            await task
            await asyncio.sleep(update_interval)  

    async def h1(self, symbol):
        data = await self.fetcher("perpetual", "oi", symbol=symbol, special_method="oifutureperp")
        self.data[symbol] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for margin in self.symbols_perpetual:
            for symbol in self.symbols_perpetual[margin]:
                tasks.append(self.h1(symbol))
        await asyncio.gather(*tasks)

class bitget_aoihttp_fundperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.symbols_perpetual = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""

    async def get_bitget_perpetual_symbols(self):
        self.symbols_perpetual = await self.info(self.underlying_asset)
    
    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_bitget_perpetual_symbols())
            await task
            await asyncio.sleep(update_interval)  

    async def h1(self, symbol):
        data = await self.fetcher("perpetual", "funding", symbol=symbol, special_method="fundperp")
        self.data[symbol] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for margin in self.symbols_perpetual:
            for symbol in self.symbols_perpetual[margin]:
                tasks.append(self.h1(symbol))
        await asyncio.gather(*tasks)

        for key, funddata in self.data.copy().items():
            if "fundingRate" not in funddata:
                for symbol, perpsymb in self.symbols_perpetual.copy().items():
                    if key in perpsymb:
                        self.symbols_perpetual[symbol].remove(key)
                del self.data[key]

class gateio_aoihttp_fundperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.linear_symbols = []
        self.inverse_symbols = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""


    async def get_symbols(self):
        linear_perpetual, inverse_perpetual, futures = await self.info(self.underlying_asset)
        self.linear_symbols = linear_perpetual
        self.inverse_symbols = inverse_perpetual

    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_symbols())
            await task
            await asyncio.sleep(update_interval)  

    async def h1(self, symbol):
        data = await self.fetcher("perpetual", "funding", symbol)
        self.data[f"{symbol}"] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for s in self.inverse_symbols:
            tasks.append(self.h1(s))
        for s in self.linear_symbols:
            tasks.append(self.h1(s))
        await asyncio.gather(*tasks)

class gateio_aoihttp_oifutureperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.linear_symbols = []
        self.inverse_symbols = []
        self.future_symbols = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""


    async def get_symbols(self):
        linear_perpetual, inverse_perpetual, futures = await self.info(self.underlying_asset)
        self.linear_symbols = linear_perpetual
        self.inverse_symbols = inverse_perpetual
        self.future_symbols = futures

    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_symbols())
            await task
            await asyncio.sleep(update_interval)  

    async def helper(self, symbol, objective, didi, instType):
        data = await self.fetcher(instType, objective, symbol)
        self.data[f"{symbol}"] = data
    
    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        d = {}
        tasks = []
        for sa in self.linear_symbols:
            tasks.append(self.helper(sa, "oi", d, "perpetual"))
        for saa in self.inverse_symbols:
            tasks.append(self.helper(saa, "oi", d, "perpetual"))
        for saaa in self.future_symbols:
            tasks.append(self.helper(saaa, "oi", d, "future"))
        await asyncio.gather(*tasks)        
        
        for key, value in self.data.copy().items():
            if "total_size" not in value and "open_interest" not in value:
                del self.data[key]
                if key.split("_")[-1].isdigit():
                    self.future_symbols.remove(key)
                if "USD" in key and "USDT" in key: 
                    self.linear_symbols.remove(key)
                if "USD" in key and "USDT" not in key: 
                    self.inverse_symbols.remove(key)

class gateio_aoihttp_posfutureperp_manager(CommonFunctionality):

    def __init__ (self, underlying_asset, info:callable, aiohttpfetch:callable):
        self.running = True
        self.underlying_asset = underlying_asset
        self.linear_symbols = []
        self.inverse_symbols = []
        self.future_symbols = []
        self.info = info
        self.fetcher = aiohttpfetch
        self.symbol_update_task = True
        self.data = {}
        self.pullTimeout = 1
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""


    async def get_symbols(self):
        linear_perpetual, inverse_perpetual, futures = await self.info(self.underlying_asset)
        self.linear_symbols = linear_perpetual
        self.inverse_symbols = inverse_perpetual
        self.future_symbols = futures

    async def update_symbols(self, lag=0, update_interval=60*24):
        await asyncio.sleep(lag)
        while self.running:
            task = asyncio.create_task(self.get_symbols())
            await task
            await asyncio.sleep(update_interval)  

    async def gateio_positioning_useless_or_not(self, symbol, objective, didi):
        data = await self.fetcher("perpetual", objective, symbol)
        self.data[f"{symbol}"] = data

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        d = {}
        tasks = []
        for s in self.linear_symbols:
            tasks.append(self.gateio_positioning_useless_or_not(s, "tta", d))
        for s in self.inverse_symbols:
            tasks.append(self.gateio_positioning_useless_or_not(s, "tta", d))
        await asyncio.gather(*tasks)
        
class htx_aiohttp_oifutureperp_manager(CommonFunctionality):

    def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.htx_aiohttpFetch = htx_aiohttpFetch
        self.data = {}
        self.running = True
        self.pullTimeout = 1
        self.underlying_asset = underlying_asset
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""

    async def htx_fetch_oi_helper(self, instType, objective, underlying_asset, asset_specification, state_dictionary):
        response = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}")      
        state_dictionary[f"{underlying_asset}{asset_specification}"] = response

    async def htx_fetch_oi_helper_2(self, instType, objective, underlying_asset, asset_specification, state_dictionary, ctype):
        response = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}", contract_type=ctype)

        state_dictionary[f"{underlying_asset}{asset_specification}"] = response

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        tasks.append(self.htx_fetch_oi_helper("perpetual", "oiall", self.underlying_asset, "-USDT.LinearPerpetual", self.data))
        tasks.append(self.htx_fetch_oi_helper("perpetual", "oi", self.underlying_asset, "-USD", self.data))
        for ctype in self.inverse_future_contract_types_htx:
            tasks.append(self.htx_fetch_oi_helper_2("future", "oi", self.underlying_asset, ".InverseFuture", self.data, ctype))
        await asyncio.gather(*tasks)

class htx_aiohttp_fundperp_manager(CommonFunctionality):

    def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.htx_aiohttpFetch = htx_aiohttpFetch
        self.data = {}
        self.running = True
        self.pullTimeout = 1
        self.underlying_asset = underlying_asset
        self.send_message_to_topic = lambda x,y : print("This function will be changed dynamically")
        self.topic_name = ""

    async def htx_fetch_fundperp_helper(self, instType, objective, underlying_asset, asset_specification, state_dictionary, marginCoinCoinCoin):
        l = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}{asset_specification}")
        state_dictionary[marginCoinCoinCoin] = l

    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        tasks.append(self.htx_fetch_fundperp_helper("perpetual", "funding", self.underlying_asset, "-USDT", self.data, "usdt"))
        tasks.append(self.htx_fetch_fundperp_helper("perpetual", "funding", self.underlying_asset, "-USD", self.data, "usd"))
        await asyncio.gather(*tasks)
    
class htx_aiohttp_posfutureperp_manager(CommonFunctionality):

    def __init__(self, underlying_asset, inverse_future_contract_types_htx, htx_aiohttpFetch):
        self.inverse_future_contract_types_htx = inverse_future_contract_types_htx
        self.htx_aiohttpFetch = htx_aiohttpFetch
        self.data = {}
        self.running = True
        self.pullTimeout = 1
        self.underlying_asset = underlying_asset
        self.send_message_to_topic:Callable[[Any, str, bytes], Any] = None
        self.topic_name = ""

    async def htx_fetch_pos_helper(self, instType, objective, underlying_asset, ltype, state_dictionary):
        tta = await self.htx_aiohttpFetch(instType, objective, f"{underlying_asset}-{ltype}")
        state_dictionary[f"{underlying_asset}_{ltype}_{objective}"] = tta

    async def htx_fetch_pos_helper_2(self, instType, underlying_asset, obj, state_dictionary):
        tta = await self.htx_aiohttpFetch(instType, obj, f"{underlying_asset}.InverseFuture")

        state_dictionary[f"{underlying_asset}_InverseFuture_tta"] = tta
    
    @CommonFunctionality.log_exceptions
    async def aiomethod(self):
        tasks = []
        for ltype in ["USDT", "USD", "USDT-FUTURES"]:
            for obj in ["tta", "ttp"]:
                tasks.append(self.htx_fetch_pos_helper("perpetual", obj, self.underlying_asset, ltype, self.data))
        for obj in ["tta", "ttp"]:
            tasks.append(self.htx_fetch_pos_helper_2("future", self.underlying_asset, obj, self.data))
        await asyncio.gather(*tasks)

