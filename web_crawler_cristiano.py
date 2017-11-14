#Data: 20171107

#Sofa score
driver = webdriver.Firefox()

driver.get("https://www.sofascore.com/pt/abc-fc-gremio-esportivo-brasil/LOsNLi")
driver.find_element_by_xpath("""/html/body/div[4]/div/div[2]/div/div[2]/ul/li[2]/a""").click()

#jogador - chutes - desarmes - totpasses- duelos vencidos - min jogados - posicao - avaliacao

x = 1 
while x <= 22:  
    varXpath = "/html/body/div[4]/div/div[2]/div/div[2]/div[2]/div[2]/div/div/div[2]/div[1]/table/tbody/tr["+str(x)+"]"
    posts = driver.find_elements_by_xpath(varXpath)
    for post in posts:
        print(post.text)
    x = x + 1   
