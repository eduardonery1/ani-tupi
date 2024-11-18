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

if __name__=="__main__":
    url = "https://animefire.plus/pesquisar/" + "-".join(input("Pesquisar anime: ").split())
    print("Buscando...")
    # Your HTML content
    html_content = requests.get(url)
    # Parse the HTML with BeautifulSoup
    soup = BeautifulSoup(html_content.text, 'html.parser')
    # Find all the titles
    titles_link = [div.article.a["href"] for div in soup.find_all('div', class_='col-6 col-sm-4 col-md-3 col-lg-2 mb-1 minWDanime divCardUltimosEps') if 'title' in div.attrs]
    titles = [h3.get_text() for h3 in soup.find_all("h3", class_="animeTitle")]
    selected = menu(titles)
    if selected == "EXIT":
        exit()

    url_episodes = titles_link[titles.index(selected)]
    html_episodes_page = requests.get(url_episodes)
    soup = BeautifulSoup(html_episodes_page.text, "html.parser")
    episode_links = [a["href"] for a in soup.find_all('a', class_="lEp epT divNumEp smallbox px-2 mx-1 text-left d-flex")]
    opts = [str(i) for i in range(1, len(episode_links)+1)]
    selected = menu(opts)
    if selected == "EXIT":
        exit()

    url_episode = episode_links[int(selected) - 1]
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
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located(params)
        )
    except:
        try:
            params = (By.XPATH, "/html/body/div[2]/div[2]/div/div[1]/div[1]/div/div/div[2]/div[4]/iframe")
            element = WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located(params)
            )
        except:
            print("AnimeFire não tem mais esse video ou foi hospedado no YouTube.")
            driver.quit()
            exit()

    product = driver.find_element(params[0], params[1])
    link = product.get_property("src")
    driver.quit()

    try:
        subprocess.run(["mpv", link])
    except:
        print("mpv não encontrado ou houveram problemas na sua execução.")
