from selenium import webdriver
import psycopg2
import sys
from datetime import datetime
import _funcoes

try:
    conn = psycopg2.connect("dbname='whoscored' user='postgres' host='localhost' password='12345678'")
except:
    print "Falha ao conectar em BD"
    quit()

#Script Vars
SCRIPT_NAME = sys.argv[0].split(".")[0]
SCRIPT_BEGIN = datetime.now()
LOG = True if "-v" in sys.argv or "-f" in sys.argv else False
LOG_FILE = SCRIPT_NAME+"__"+str(SCRIPT_BEGIN.day)+"_"+str(SCRIPT_BEGIN.month)+"_"+str(SCRIPT_BEGIN.year)+"__LOG.txt" if "-f" in sys.argv else None

#Configura Proxy Tor
profile = webdriver.FirefoxProfile()
profile.set_preference("network.proxy.type", 1)
profile.set_preference("network.proxy.http", "127.0.0.1")
profile.set_preference("network.proxy.http_port", 9050)
profile.set_preference("network.proxy.ssl", "127.0.0.1")
profile.set_preference("network.proxy.ssl_port", 9050)
profile.set_preference("network.proxy.socks", "127.0.0.1")
profile.set_preference("network.proxy.socks_port", 9050)

driver = webdriver.Firefox(firefox_profile=profile)

with open(SCRIPT_NAME+"_INPUT.txt", "r") as infile:
	for line in infile:
		infile_data = line.strip("\n").split(" ")
		url='https://www.whoscored.com/Regions/'+infile_data[0]+'/Tournaments/'+infile_data[1]+'/'
		_funcoes.log("[Regiao: "+infile_data[0]+"; Torneio: "+infile_data[1]+"]", LOG, False, LOG_FILE)
		_funcoes.log(" -> [Carregando..]", LOG, False, LOG_FILE)
		driver.get(url)
		_funcoes.log(" -> [Carregado]", LOG, True, LOG_FILE)
		#Captura a regiao
		regiao_nome = driver.find_element_by_id("breadcrumb-nav").find_element_by_xpath("./span[1]").text
		_funcoes.db_insert(conn, "regiao", {'id': infile_data[0], 'nome': regiao_nome}, "[Regiao] -> [Inserindo..]", LOG, LOG_FILE, True)
		#Captura os torneios
		for option in driver.find_element_by_id("tournaments").find_elements_by_tag_name("option"):
			torneio_data = option.get_attribute("value").split("Tournaments")[1].split("/")
			_funcoes.db_insert(conn, "torneio", {'id': torneio_data[1], 'nome': torneio_data[2], 'id_regiao': infile_data[0]}, "[Torneio] -> [Inserindo..]", LOG, LOG_FILE, True)
		############################################
		## Captura os ids dos times no campeonato ##
		############################################
		for div in driver.find_elements_by_class_name("tournament-standings-table"):
			tr_index = 1
			trs_qtd = len(div.find_element_by_tag_name("tbody").find_elements_by_xpath("./tr[@data-team-id]"))
			while tr_index <= trs_qtd:
				_funcoes.log("[Lendo Time] -> [Id]", LOG, False, LOG_FILE)
				team_id = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_tag_name("tbody").find_element_by_xpath("./tr[@data-team-id]['+str(tr_index)+']").get_attribute("data-team-id")', div, LOG, LOG_FILE))
				_funcoes.log(" -> [Nome]", LOG, False, LOG_FILE)
				team_name = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_tag_name("tbody").find_element_by_xpath("./tr[@data-team-id]['+str(tr_index)+']").find_element_by_xpath("./td[2]/a").get_attribute("innerHTML")', div, LOG, LOG_FILE))
				_funcoes.log(" -> ["+team_id+": "+team_name+"]", LOG, False, LOG_FILE)
				_funcoes.db_insert(conn, "time", {'id': team_id, 'nome': team_name, 'id_regiao': infile_data[0]}, " -> [Inserindo..]", LOG, LOG_FILE, True)
				tr_index += 1

driver.quit()
conn.close()
