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
        #splitStats = post.split( )
        #if len(splitStats) == 11:
	    #    print(splitStats[0]+' '+splitStats[1],splitStats[2],splitStats[3],splitStats[4],splitStats[5],splitStats[6],splitStats[7],splitStats[8],splitStats[9],splitStats[10])
        #else:
	    #    print(splitStats[0],splitStats[1],splitStats[2],splitStats[3],splitStats[4],splitStats[5],splitStats[6],splitStats[7],splitStats[8],splitStats[9])	
        print(post.text)
    x = x + 1  
