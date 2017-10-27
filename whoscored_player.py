from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException     
from selenium.webdriver.common.by import By
import time

#Configura Proxy Tor
#profile = webdriver.FirefoxProfile()
#profile.set_preference("network.proxy.type", 1)
#profile.set_preference("network.proxy.http", "127.0.0.1")
#profile.set_preference("network.proxy.http_port", 9050)
#profile.set_preference("network.proxy.ssl", "127.0.0.1")
#profile.set_preference("network.proxy.ssl_port", 9050)
#profile.set_preference("network.proxy.socks", "127.0.0.1")
#profile.set_preference("network.proxy.socks_port", 9050)

#driver = webdriver.Firefox(firefox_profile=profile)
driver = webdriver.Firefox()

player = {"basic": {}, "detailed": {}}
url='https://www.whoscored.com/Players/13154'
driver.get(url)

####################
## Parte com HTML ##
####################
for line in driver.find_elements_by_class_name("player-info-block"):
	player["basic"][line.find_element_by_tag_name("dt").get_attribute("innerHTML").strip("\t\:").replace(" ", "_").lower()] = line.find_element_by_tag_name("dd").text.strip("\t")

####################
## Parte com Ajax ##
####################
#Na tabela, muda para detalhes
driver.find_element_by_xpath('//*[@id="player-tournament-stats-options"]/li[5]/a').click()
try:
	accumulation_select = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "statsAccumulationType")))
except TimeoutException:
	print "Erro ao mudar para aba 'Detalhes'"
	driver.quit()
	quit()
details_div = driver.find_element_by_id("player-tournament-stats-detailed")
#Seleciona os dados para quantidade 'Total'
accumulation_select.find_element_by_xpath(".//option[4]").click()
#Certifica a mudanca para tipo 'Total'
try:
	WebDriverWait(details_div, 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
except TimeoutException:
	print "Erro ao mudar para tipo de dados 'Total'"
	driver.quit()
	quit()

player_tbody = details_div.find_element_by_id("player-table-statistics-body")
for tr in player_tbody.find_elements_by_tag_name("tr"):
	try:
		tournament = tr.find_element_by_xpath(".//td[1]/a").get_attribute("href").split("/")
		tournament = tournament[len(tournament)-1]
	except NoSuchElementException:
		continue
	if tournament not in player["detailed"]:
		player["detailed"][tournament] = {}
	for td in tr.find_elements_by_tag_name("td"):
		if td.get_attribute("class") == "tournament":
			continue
		player["detailed"][tournament][td.get_attribute("class").split(" ")[0]] = td.get_attribute("innerHTML").strip('\t\n')

print player
driver.quit()