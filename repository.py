import asyncio
from os import cpu_count
from loader import PluginInterface
from typing import Callable
from collections import defaultdict
from threading import Thread, Condition
from concurrent.futures import ThreadPoolExecutor
from multiprocessing.pool import ThreadPool
from fuzzywuzzy import fuzz

class Repository:
    """ SingletonRepository 
        get for methods called by main that return some value
        search for methods called by main that don't return but affects state
        add for methods called by any plugin that affects state
        register should be called by a loader function 
    """

    _instance = None
    
    def __init__(self) -> None:
        self.sources = []
        self.anime_to_urls = defaultdict(list)
        self.anime_episodes_titles = defaultdict(list)
        self.anime_episodes_urls = defaultdict(list)
    
    def __new__(cls):
        if not Repository._instance:
            Repository._instance = super(Repository, cls).__new__(cls)
        return Repository._instance

    def register(self, plugin: PluginInterface) -> None:
        self.sources.append(plugin)
    
    def search_anime(self, query: str) -> None:
        with ThreadPool(min(len(self.sources), cpu_count())) as pool:
            for source in self.sources:
                pool.apply(source.search_anime, args=(query,))

    def add_anime(self, title: str, url: str, F: Callable[[str, str], None], params=None) -> None:
        """
        This method assumes that different seasons are different anime, like MAL, so plugin devs should take scrape that way.
        """
        title_ = title.lower()
        table = {"clássico": "", 
                 "classico":"", 
                 ":":"", 
                 "part":"season", 
                 "temporada":"season",
                 "(":"",
                 ")":"" }

        for key, val in table.items():
            title_ = title_.replace(key, val)

        threshold = 30
        for key in self.anime_to_urls.keys():
            if fuzz.ratio(title_, key) <= threshold:
                self.anime_to_urls[key].append((url, F, params))
                return
        self.anime_to_urls[title_].append((url, F, params))

    def get_anime_titles(self) -> list[str]:
        return sorted([s.capitalize() for s in self.anime_to_urls.keys()])
    
    def search_episodes(self, anime: str) -> list[str]:
        if anime in self.anime_episodes_titles:
            return self.anime_episode_titles[anime]

        urls_and_scrapers = rep.anime_to_urls[anime]
        threads = [Thread(target=search_episode, args=(anime, url, params, )) for url, search_episode, params in urls_and_scrapers]
        
        for th in threads:
            th.start()

        for th in threads:
            th.join()
    
    def add_episode_list(self, anime: str, title_list: list[str], url_list: list[str], F: Callable[[...], None]) -> None:
        self.anime_episodes_titles[anime].append(title_list)
        self.anime_episodes_urls[anime].append((url_list, F))
    
    def get_episode_list(self, anime: str):
        return self.anime_episodes_titles[anime][0]

    def search_player(self, anime: str, episode_num: int) -> None:
        """
        This method assumes all episode lists to be the same size, plugin devs should guarantee that OVA's are not considered.
        """
        selected_urls = []
        for urls, F in self.anime_episodes_urls[anime]:
            selected_urls.append((urls[episode_num - 1], F))

        async def search_all_sources():
            nonlocal selected_urls, self
            event = asyncio.Event()
            container = []
            loop = asyncio.get_running_loop()
            with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
                tasks = [loop.run_in_executor(executor, search_player_src, url, container, event) for url, search_player_src in selected_urls]
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED) 

                for task in pending:
                    task.cancel()
                return container[0]

        return asyncio.run(search_all_sources())
        
rep = Repository()

if __name__=="__main__":
    rep3, rep2 = Repository(), Repository()
    print(rep3 is rep2)
