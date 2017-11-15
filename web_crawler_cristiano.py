from selenium import webdriver
from selenium.webdriver.common.keys import Keys

driver = webdriver.Firefox()

driver.get("https://www.sofascore.com/pt/londrina-guarani/xOsxP")
  
driver.find_element_by_xpath("/html/body/div[4]/div/div[2]/div/div[2]/ul/li[2]/a").click()
#jogador - chutes - desarmes - totpasses- duelos vencidos - min jogados - posicao - avaliacao

x = 1 
while x <= 22:  
    varXpath = """//*[@id="player-statistics-tab-summary"]/table/tbody/tr["""+str(x)+"""]"""
    posts = driver.find_elements_by_xpath(varXpath)
    for post in posts:
        print(post.text)
    x = x + 1  
