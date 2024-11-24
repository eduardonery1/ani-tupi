import requests
import subprocess
from sys import exit
from menu import menu
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def is_firefox_installed_as_snap():
    try:
        result = subprocess.run(
            ["snap", "list", "firefox"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return result.returncode == 0  # Return code 0 means Firefox is installed as a snap
    except FileNotFoundError:
        print("Snap is not installed on this system.")
        return False

def search_anime():
    url = "https://animefire.plus/pesquisar/" + "-".join(input("Pesquisar anime: ").split())
    print("Buscando...")
    html_content = requests.get(url)
    soup = BeautifulSoup(html_content.text, 'html.parser')
    titles_link = [div.article.a["href"] for div in soup.find_all('div', class_='col-6 col-sm-4 col-md-3 col-lg-2 mb-1 minWDanime divCardUltimosEps') if 'title' in div.attrs]
    titles = [h3.get_text() for h3 in soup.find_all("h3", class_="animeTitle")]
    selected = menu(titles)
    url_episodes = titles_link[titles.index(selected)]
    return url_episodes

def search_episode(url_episodes):
    html_episodes_page = requests.get(url_episodes)
    soup = BeautifulSoup(html_episodes_page.text, "html.parser")
    episode_links = [a["href"] for a in soup.find_all('a', class_="lEp epT divNumEp smallbox px-2 mx-1 text-left d-flex")]
    opts = [str(i) for i in range(1, len(episode_links)+1)]
    selected = menu(opts)
    return int(selected) - 1, episode_links 

def find_player_link(url_episode):
    print("Procurando video em:", url_episode)
    options = webdriver.FirefoxOptions()
    options.add_argument("--headless")
    if is_firefox_installed_as_snap():
        service = webdriver.FirefoxService(executable_path="/snap/bin/geckodriver")
        driver = webdriver.Firefox(options=options, service = service)
    else:
        driver = webdriver.Firefox(options=options)
    driver.get(url_episode)

    try:
        params = (By.ID, "my-video_html5_api")
        element = WebDriverWait(driver, 7).until(
            EC.visibility_of_all_elements_located(params)
        )
    except:
        try:
            params = (By.XPATH, "/html/body/div[2]/div[2]/div/div[1]/div[1]/div/div/div[2]/div[4]/iframe")
            element = WebDriverWait(driver, 7).until(
                EC.visibility_of_all_elements_located(params)
            )
        except:
            print("AnimeFire não tem mais esse video ou foi hospedado no YouTube.")
            driver.quit()
            exit()

    product = driver.find_element(params[0], params[1])
    link = product.get_property("src")
    driver.quit()
    return link

def play_episode(link, idx):
    try:
        subprocess.run(["mpv", link])
    except:
        print("mpv não encontrado ou houveram problemas na sua execução.")
        exit()

    opts = ["Proximo episodio"]
    opt = menu(opts)
    if opt == "Proximo episodio":
        idx += 1
        return idx
    else:
        return -1

if __name__=="__main__":
    url_episodes = search_anime()
    idx, episode_links = search_episode(url_episodes)
    link = find_player_link(episode_links[idx])
    idx = play_episode(link, idx)
    
    while idx != -1 and idx < len(episode_links):
        link = find_player_link(episode_links[idx])
        idx = play_episode(link, idx)

    if idx >= len(episode_links):
        print("Sem mais episodios!")
    
