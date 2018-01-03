from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException    
from selenium.common.exceptions import TimeoutException 
from selenium.webdriver.common.by import By
import psycopg2
import sys
import os.path
import json
from datetime import datetime
import _funcoes

######################################################################
# Exec: python whoscored_get_dates.py [-v: Bash log | -f: File log] #
######################################################################

#Script Vars
SCRIPT_NAME = sys.argv[0].split(".")[0]
SCRIPT_BEGIN = datetime.now()
LOG = True if "-v" in sys.argv or "-f" in sys.argv else False
LOG_FILE = open("logs/"+str(SCRIPT_BEGIN.hour)+"_"+str(SCRIPT_BEGIN.minute)+"_"+str(SCRIPT_BEGIN.second)+"__"+str(SCRIPT_BEGIN.day)+"_"+str(SCRIPT_BEGIN.month)+"_"+str(SCRIPT_BEGIN.year)+"__"+SCRIPT_NAME+".txt", "w") if "-f" in sys.argv else None
MONTH_DIC = {'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6, 'JUL': 7, 'AGO': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12}
VALID_TOURNAMENTS = ['Premier League', 'League 1', 'UEFA Champions League', 'UEFA Europa League']

_funcoes.log("[Iniciando Spyder]", LOG, False, LOG_FILE)
try:
	conn = psycopg2.connect("dbname='whoscored' user='postgres' host='localhost' password='12345678'")
	_funcoes.log("-> [Postgresql Ok]", LOG, False, LOG_FILE)
except:
	_funcoes.log("-> [Postgresql Error]", LOG, True, LOG_FILE)
	quit()

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

# driver = webdriver.PhantomJS(service_args=['--proxy=127.0.0.1:9050', '--proxy-type=socks5'])
# driver.set_window_size(1920, 1080)
_funcoes.log("-> [Phantomjs Ok]", LOG, False, LOG_FILE)

#Abre o arquivo de restauracao, se houve erro na execucao passada
restore_file = 'restores/.'+SCRIPT_NAME+".json"
if os.path.isfile(restore_file):
	with open(restore_file) as infile:
		restore_data = json.load(infile)
		_funcoes.log("-> [Restaurando..]", LOG, False, LOG_FILE)
else:
	restore_data = None

_funcoes.log("-> [Carregando URL...]", LOG, False, LOG_FILE)
url = 'https://www.whoscored.com/LiveScores'
driver.get(url)
_funcoes.log("-> [Carregado]", LOG, True, LOG_FILE)

if restore_data != None:
	date = restore_data["date"]
	driver.find_element_by_id("date-config-toggle-button").click()
	WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "date-config")))
	days = driver.find_element_by_xpath('//*[@id="date-config"]/div[1]/div/table/tbody/tr/td[3]/div/table/tbody').find_elements_by_css_selector("td[class$='selectable']")
	for d in days:
		if str(d.get_attribute("innerHTML")) == date[1]:
			d.click()
			break
	try:
		WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="livescores"]/table')))
	except TimeoutException:
		_funcoes.log("(*) Timeout ao achar o ultimo dia", LOG, True, LOG_FILE)
		driver.quit()
		conn.close()
		quit()
else:
	#Captura as hora das partidas, times e regioes
	date = _funcoes.break_date_long(_funcoes.filter_data(driver.find_element_by_xpath('//*[@id="date-config-toggle-button"]/span[1]').text))

while MONTH_DIC[date[0]] == SCRIPT_BEGIN.month:
	_funcoes.log("["+" ".join(date)+"] -> [Carregando..]", LOG, False, LOG_FILE)
	table_tr_index = 1
	table_tr_qtd = len(driver.find_element_by_id("livescores").find_elements_by_tag_name("tr"))
	_funcoes.log("-> ["+str(table_tr_qtd)+" achados]", LOG, False, LOG_FILE)
	tournament_id = None
	check_teams = True
	_funcoes.log("-> [Ok]", LOG, True, LOG_FILE)
	while table_tr_index <= table_tr_qtd:
		_funcoes.log("[Lendo <tr><"+str(table_tr_index)+":"+str(table_tr_qtd)+">]", LOG, False, LOG_FILE)
		tr_class = _funcoes.no_stale_data('driver.find_element_by_id("livescores").find_element_by_tag_name("tbody").find_element_by_xpath("./tr['+str(table_tr_index)+']").get_attribute("class")', driver, conn, LOG, LOG_FILE)
		_funcoes.log("", LOG, True, LOG_FILE)
		#Captura a regiao e torneio
		if "group" in tr_class:
			data_ids = _funcoes.no_stale_data('driver.find_element_by_id("livescores").find_element_by_tag_name("tbody").find_element_by_xpath("./tr['+str(table_tr_index)+']").find_element_by_class_name("tournament-link").get_attribute("href")', driver, conn, LOG, LOG_FILE).split("/")
			tournament_id = data_ids[6]
			data_names = _funcoes.no_stale_data('driver.find_element_by_id("livescores").find_element_by_tag_name("tbody").find_element_by_xpath("./tr['+str(table_tr_index)+']").find_element_by_class_name("tournament-link").find_element_by_xpath("./span[1]").text', driver, conn, LOG, LOG_FILE).split(" - ")
			check_teams = _funcoes.check_substr_array(VALID_TOURNAMENTS, data_names[1])
			if check_teams:
				_funcoes.db_insert(conn, "region", {'id': data_ids[4], 'name': data_names[0].upper()}, "["+data_names[0]+"] -> [Inserindo..]", LOG, LOG_FILE, True)
				_funcoes.db_insert(conn, "tournament", {'id': tournament_id, 'name': data_names[1].upper(), 'region_id': data_ids[4]}, "["+data_names[1]+"] -> [Inserindo..]", LOG, LOG_FILE, True)
			else:
				_funcoes.log("["+"/".join(data_names)+"] -> [Pula]", LOG, True, LOG_FILE)
		#Captura partida e times
		elif "item" in tr_class and check_teams:
			time = _funcoes.fix_time_zone(date[2]+"-"+str(MONTH_DIC[date[0]])+"-"+date[1], _funcoes.no_stale_data('driver.find_element_by_id("livescores").find_element_by_tag_name("tbody").find_element_by_xpath("./tr['+str(table_tr_index)+']").find_element_by_class_name("time").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE))
			_funcoes.log("["+time[0]+" | "+time[1]+"]", LOG, False, LOG_FILE)
			team_home = _funcoes.break_team_data(_funcoes.no_stale_data('driver.find_element_by_id("livescores").find_element_by_tag_name("tbody").find_element_by_xpath("./tr['+str(table_tr_index)+']").find_element_by_class_name("home").find_element_by_xpath("./a[1]").get_attribute("href")', driver, conn, LOG, LOG_FILE))
			_funcoes.db_insert(conn, "team", {'id': team_home[0], 'name': team_home[1]}, "["+team_home[1]+"] -> [Inserindo..]", LOG, LOG_FILE, False)
			team_away = _funcoes.break_team_data(_funcoes.no_stale_data('driver.find_element_by_id("livescores").find_element_by_tag_name("tbody").find_element_by_xpath("./tr['+str(table_tr_index)+']").find_element_by_class_name("away").find_element_by_xpath("./a[1]").get_attribute("href")', driver, conn, LOG, LOG_FILE))
			_funcoes.db_insert(conn, "team", {'id': team_away[0], 'name': team_away[1]}, "["+team_away[1]+"] -> [Inserindo..]", LOG, LOG_FILE, False)
			_funcoes.db_insert(conn, "match_date", {'team_id': team_home[0], 'tournament_id': tournament_id, 'date': time[0], 'time': time[1]}, "[Match Date Home] -> [Inserindo..]", LOG, LOG_FILE, False)
			_funcoes.db_insert(conn, "match_date", {'team_id': team_away[0], 'tournament_id': tournament_id, 'date': time[0], 'time': time[1]}, "[Match Date Away] -> [Inserindo..]", LOG, LOG_FILE, True)
		table_tr_index += 1
	#Muda para o proximo dia
	driver.find_element_by_xpath('//*[@id="date-controller"]/dd[1]/div/a[3]').click()
	_funcoes.log("[Proxima dia] -> [Carregando..]", LOG, False, LOG_FILE)
	try:
		WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="livescores"]/table')))
		date = _funcoes.break_date_long(driver.find_element_by_xpath('//*[@id="date-config-toggle-button"]/span[1]').text)
		_funcoes.log("["+" ".join(date)+"]", LOG, True, LOG_FILE)
		#Salva o estado do crawler
		_funcoes.write_restore_file(restore_file, {'date': date})
	except TimeoutException:
		_funcoes.log("(*) Timeout ir para o proximo dia", LOG, True, LOG_FILE)
		driver.quit()
		conn.close()
		quit()

_funcoes.log("[Nada mais a fazer]", LOG, False, LOG_FILE)
driver.quit()
_funcoes.log("-> [Fechando PhantomJS]", LOG, False, LOG_FILE)
conn.close()
_funcoes.log("-> [Fechando DB]", LOG, False, LOG_FILE)
os.remove(restore_file)
_funcoes.log("-> [Removendo Restore_File]", LOG, True, LOG_FILE)
