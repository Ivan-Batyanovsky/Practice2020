import time
import re
import emoji
import pymysql
from bs4 import BeautifulSoup
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


# MySQL can't properly read quotes from Meduza
def extract_glitches(s):
    # print("s from glitch", s)
    forbid = '''»?«!()-[]{};:'"\,<>./?@#$%^&*_~1234567890'''
    return ''.join(c for c in s if c not in forbid)


# Emojis which representation needs more than 3 bytes crash MySQL
def extract_emojis(s):
    # print("s from emojis", s)
    return extract_glitches(''.join(c for c in s if c not in emoji.UNICODE_EMOJI))


# Function for storing title, genre and content to MySQL server
def storeText(title="NULL", genre="NULL", content="NULL"):
    cur.execute("INSERT INTO protNews (title, genre, content) VALUES (\"%s\", \"%s\", \"%s\")",
                (extract_emojis(title),
                 extract_emojis(genre),
                 extract_emojis(content)))
    cur.connection.commit()


def parser(url, rubric):
    newUrl = "https://lenta.ru" + url
    driver.get(newUrl)
    # print("Parser approaching", newUrl)

    bsObj = BeautifulSoup(driver.page_source, "html.parser")
    title = bsObj.find("h1", {"class": "b-topic__title"})
    if title is not None:
        title = title.get_text()
        # print(title)
    #     print("Rubric and Title:", rubric, bsObj.find("h1", {"class": "b-topic__title"}).get_text())
    #     print("*"*100)

    textContainer = bsObj.find("div", {"class": "b-text clearfix js-topic__text"})
    if textContainer is not None:
        if textContainer.find("div", {"class": "b-box"}) is not None:
            content = [p.get_text() for p in textContainer
                .find("div", {"class": "b-box"}).previous_siblings][::-1]
        else:
            content = [p.get_text() for p in textContainer.findAll("p")]
        # print(content)
        # print("-"*100)
        storeText(title, rubric, " ".join(content))
    # time.sleep(3)


def crawler(url="", rubric="NULL", date=date.today(), depth=0, limit=3, main=False):
    global pages
    if main is True:
        newUrl = "https://lenta.ru" + url + str(date)[:4] + "/" + str(date)[5:7] + "/" + str(date)[8:] + "/"
    else:
        newUrl = "https://lenta.ru" + url
    driver.get(newUrl)
    print(newUrl, rubric)
    # time.sleep(3)
    try:
        # Waiting for block of news to appear
        element = WebDriverWait(driver, 10) \
            .until(EC.presence_of_element_located((By.CLASS_NAME, "b-layout.js-layout.b-layout_archive")))
    except:
        print("Can't locate news block")
        return
    finally:
        bsObj = BeautifulSoup(driver.page_source, "html.parser")

    # print("before span4")
    span4s = bsObj.find("section", {"class": "b-layout js-layout b-layout_archive"}).findAll("div", {"class": "span4"})
    for span4 in span4s:
        items = span4.findAll("div", {"class": "item news b-tabloid__topic_news"})
        for item in items:
            if items is not None:
                newLink = item.find("a", {"href": re.compile("^(\/.*\/).*")}).attrs["href"]
                if newLink not in pages:
                    pages.add(newLink)
                    parser(newLink, rubric)
    # print("before crawler")
    if depth < limit:
        print("Push some buttons sometimes(dep, lim):", depth + 1, limit)
        crawler(url=bsObj.find("a", {"class": "control_mini"}).attrs["href"], rubric=rubric, depth=depth + 1, limit=limit, date=date)



chromePath = "chromedriver.exe"

# Launching Selenium
driver = webdriver.Chrome(executable_path=chromePath)
driver.get("https://lenta.ru")

# List of visited pages
pages = set()
# ui-arrow-block_up ----> button
# b-layout js-layout b-layout_archive ---> news block
# -span 4

""" SELECT id, title, genre, GROUP_CONCAT(content SEPARATOR'. ') as concatenatedContent FROM news GROUP BY title;
                        command to see grouped up content from one page"""

# Initializing connection and cursor from MySQL Server
conn = pymysql.connect(host="127.0.0.1", user="root", passwd="Eszqsc1234", db="mysql", use_unicode=True, charset="utf8")
cur = conn.cursor()
cur.execute("USE scraping")
serverAbsolutePath = r"""'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe' -u root -p"""


# # rubricsLinks
# rl = ["/rubrics/russia/", "/rubrics/world/", "/rubrics/ussr/",
#       "/rubrics/economics/", "/rubrics/forces/", "/rubrics/science/",
#       "/rubrics/culture/", "/rubrics/sport/", "/rubrics/media/", "/rubrics/style/",
rl = ["/rubrics/sport/"]

try:
    try:
        # Waiting Side-rubrics to appear
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "b-sidebar-menu__wrap")))
    except:
        # Well... That's unfortunate
        print("quiting...")
        exit(0)

    finally:
        bsObj = BeautifulSoup(driver.page_source, "html.parser")

        # List of rubrics links
        rubricsLinks = [l.find("a", {"href": re.compile("^(\/rubrics\/).+")}).attrs["href"] for l in bsObj.find("ul", {"class": "b-sidebar-menu__list"}) \
            .findAll("li", {"class": "b-sidebar-menu__list-item"})
            if l.find("a", {"href": re.compile("^(\/rubrics\/).+")}) is not None]

    for rubricLink in rl:
        # if rubricLink == "/rubrics/sport/":
        #     continue
        print("Deep in", rubricLink, "I go")

        # Saving rubric to label data
        rubric = rubricLink[9:-1]
        crawler(url=rubricLink, rubric=rubric, depth=0, limit=30, main=True)
finally:
    # Closing connection to MySQL Server
    cur.close()
    conn.close()

    # Closing driver
    # driver.close()
