# python3;failure

from bs4 import BeautifulSoup
URL = "https://realpython.github.io/fake-jobs/"
page = urlreq(url, verb='GET')
soup = BeautifulSoup(page.content, "html.parser")