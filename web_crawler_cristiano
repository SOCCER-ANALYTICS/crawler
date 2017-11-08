#Data: 20171107

from selenium import webdriver

driver = webdriver.Firefox()

driver.get("https://www.academiadasapostasbrasil.com/stats/match/brasil-stats/brasileirao-serie-a/atletico-pr/corinthians/2419291")

posts = driver.find_elements_by_class_name("stat-lose")

for post in posts:
    print(post.text)
