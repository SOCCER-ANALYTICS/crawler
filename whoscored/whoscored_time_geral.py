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

if len(sys.argv) < 2 or not sys.argv[1].isdigit():
	quit("Exec: python whoscored_time_geral.py ID_TIME [-v: Bash log | -f: File log]")

try:
    conn = psycopg2.connect("dbname='whoscored' user='postgres' host='localhost' password='12345678'")
except:
    print "Falha ao conectar em BD"
    quit()

#Script Vars
SCRIPT_NAME = sys.argv[0].split(".")[0]
LOG = True if "-v" in sys.argv or "-f" in sys.argv else False
SCRIPT_BEGIN = datetime.now()
team_id = sys.argv[1]
LOG_FILE = SCRIPT_NAME+"__"+team_id+"__"+str(SCRIPT_BEGIN.day)+"_"+str(SCRIPT_BEGIN.month)+"_"+str(SCRIPT_BEGIN.year)+"__LOG.txt" if "-f" in sys.argv else None
players_basic = []

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

#Abre o arquivo de restauracao, se houve erro na execucao passada
restore_file = '.'+SCRIPT_NAME+".json"
if os.path.isfile(restore_file):
	with open(restore_file) as infile:
		restore_data = json.load(infile)
else:
	restore_data = None

url = 'https://www.whoscored.com/Teams/'+team_id
driver.get(url)

###########################
## Captura dados do time ##
###########################
team_name = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_class_name("team-profile-side-box").find_element_by_class_name("team-name").find_element_by_class_name("team-link").text', driver, LOG, LOG_FILE))
id_regiao = _funcoes.no_stale_data('driver.find_element_by_id("breadcrumb-nav").find_element_by_tag_name("a").get_attribute("href")', driver, LOG, LOG_FILE).split("/")[4]
_funcoes.db_insert(conn, "time", {'id': team_id, 'nome': team_name, 'id_regiao': id_regiao}, "[Time] -> [Inserindo..]", LOG, LOG_FILE, True)

##################################
## Preparacao da tabela 'Squad' ##
##################################
if restore_data != None:
	table_squad_tournaments = restore_data["table_squad_tournaments"]
	table_squad_category = restore_data["table_squad_category"]
	table_squad_subcategories = restore_data["table_squad_subcategories"]
else:
	table_squad_tournaments = []
	table_squad_category = [
		{"path": '//*[@id="category"]/optgroup[1]/option[1]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[1]/option[2]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[1]/option[3]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[1]/option[4]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[1]/option[5]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[1]/option[6]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[1]/option[7]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[1]/option[8]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[2]/option[1]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[2]/option[2]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[2]/option[3]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[2]/option[4]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[2]/option[5]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[3]/option[1]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[3]/option[2]', "loaded": False, "visited": False},
		{"path": '//*[@id="category"]/optgroup[3]/option[3]', "loaded": False, "visited": False}
	]
	table_squad_subcategories = []

#Na tabela, muda para detalhes
driver.find_element_by_id("team-squad-stats").find_element_by_xpath('//*[@id="team-squad-stats-options"]/li[5]/a').click()
try:
	accumulation_select = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "statsAccumulationType")))
except TimeoutException:
	_funcoes.log("(*) Timeout ao mudar para a aba 'Detalhes'", LOG, True, LOG_FILE)
	driver.quit()
	conn.close()
	quit()

#Seleciona os dados para quantidade 'Total'
accumulation_select.find_element_by_xpath(".//option[4]").click()
try:
	WebDriverWait(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed"), 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
except TimeoutException:
	_funcoes.log("(*) Timeout ao alterar tipo dos dados para 'Total'", LOG, True, LOG_FILE)
	driver.quit()
	conn.close()
	quit()

#-------------------------Captura os torneios do time--------------------------#
if len(table_squad_tournaments) == 0:
	tournament_options_qtd = len(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("tournamentOptions").find_elements_by_tag_name("option"))
	tournament_index = 1
	while tournament_index <= tournament_options_qtd:
		table_squad_tournaments.append({
			"path": './option['+str(tournament_index)+']',
			"id": _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("tournamentOptions").find_element_by_xpath("./option['+str(tournament_index)+']").get_attribute("value")', driver, LOG, LOG_FILE)),
			"name": _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("tournamentOptions").find_element_by_xpath("./option['+str(tournament_index)+']").get_attribute("innerHTML")', driver, LOG, LOG_FILE)),
			"visited": False,
			"loaded": True if tournament_index == 1 else False
		})
		tournament_index += 1
_funcoes.log(table_squad_tournaments, LOG, True, LOG_FILE)

#--------------------------------Para cada torneio-----------------------------#
tournament_index = 0
#Enquanto todos os tournaments nao forem carregados, continue tentando
while not _funcoes.check_all_visited(table_squad_tournaments):
	_funcoes.log("Tournament  : "+str(tournament_index), LOG, False, LOG_FILE)
	if table_squad_tournaments[tournament_index]["visited"]:
		_funcoes.log(" -> [Ja visto]", LOG, True, LOG_FILE)
		tournament_index = (tournament_index+1) % len(table_squad_tournaments)
		continue
	_funcoes.log(" -> [Visitando..]", LOG, False, LOG_FILE)
	#Carrega o torneio
	if not table_squad_tournaments[tournament_index]["loaded"]:
		_funcoes.log(" -> [Carregando..]", LOG, False, LOG_FILE)
		_funcoes.im_human()
		driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("tournamentOptions").find_element_by_xpath(table_squad_tournaments[tournament_index]["path"]).click()
		driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_class_name("search-button").click()
		try:
			WebDriverWait(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed"), 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
			_funcoes.log(" -> [Carregado]", LOG, True, LOG_FILE)
		except TimeoutException:
			_funcoes.log(" -> [Timeout]", LOG, True, LOG_FILE)
			tournament_index = (tournament_index+1) % len(table_squad_tournaments)
			continue
	else:
		_funcoes.log(" -> [Carregado]", LOG, True, LOG_FILE)
	category_index = 0
	while not _funcoes.check_all_visited(table_squad_category):
		_funcoes.log("Category    : "+str(category_index), LOG, False, LOG_FILE)
		if table_squad_category[category_index]["visited"]:
			_funcoes.log(" -> [Ja visto]", LOG, True, LOG_FILE)
			category_index = (category_index+1) % len(table_squad_category)
			continue
		_funcoes.log(" -> [Visitando..]", LOG, False, LOG_FILE)
		#Carrega a categoria
		if not table_squad_category[category_index]["loaded"]:
			_funcoes.log(" ->  [Carregando..]", LOG, False, LOG_FILE)
			_funcoes.im_human()
			driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_xpath(table_squad_category[category_index]["path"]).click()
			try:
				WebDriverWait(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed"), 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
				_funcoes.log(" ->  [Carregado]", LOG, True, LOG_FILE)
			except TimeoutException:
				_funcoes.log(" ->  [Timeout]", LOG, True, LOG_FILE)
				category_index = (category_index+1) % len(table_squad_category)
				continue
		else:
			_funcoes.log(" ->  [Carregado]", LOG, True, LOG_FILE)
		#----------------Captura as subcategorias da categoria--------------------#
		if len(table_squad_subcategories) == 0:
			subcategory_index = 1
			subcategory_options_qtd = len(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("subcategory").find_elements_by_tag_name("option"))
			while subcategory_index <= subcategory_options_qtd:
				table_squad_subcategories.append({"path": './option['+str(subcategory_index)+']', "visited": False, "loaded": True if subcategory_index == 1 else False})
				subcategory_index += 1
		#------------------------Para cada subcategorias--------------------------#
		subcategory_index = 0
		while not _funcoes.check_all_visited(table_squad_subcategories):
			_funcoes.log("Sub-Category: "+str(subcategory_index), LOG, False, LOG_FILE)
			if table_squad_subcategories[subcategory_index]["visited"]:
				_funcoes.log(" ->  [Ja visto]", LOG, True, LOG_FILE)
				subcategory_index = (subcategory_index+1) % len(table_squad_subcategories)
				continue
			_funcoes.log(" ->  [Visitando..]", LOG, False, LOG_FILE)
			if not table_squad_subcategories[subcategory_index]["loaded"]:
				_funcoes.log(" ->  [Carregando..]", LOG, False, LOG_FILE)
				_funcoes.im_human()
				driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("subcategory").find_element_by_xpath(table_squad_subcategories[subcategory_index]["path"]).click()
				try:
					WebDriverWait(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed"), 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
					_funcoes.log(" ->  [Carregado]", LOG, True, LOG_FILE)
				except TimeoutException:
					_funcoes.log(" ->  [Timeout]", LOG, True, LOG_FILE)
					subcategory_index = (subcategory_index+1) % len(table_squad_subcategories)
					continue
			else:
				_funcoes.log(" ->  [Carregado]", LOG, True, LOG_FILE)
			#--------------------------Para cada jogador-----------------------------#
			_funcoes.log("Players     : ", LOG, True, LOG_FILE)
			player_tr_index = 1
			player_trs_qtd = len(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_elements_by_tag_name("tr"))
			while player_tr_index <= player_trs_qtd:
				player_id = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./a[1]").get_attribute("href")', driver, LOG, LOG_FILE).split("/")[4])
				#Pega os dados basicos apenas na primeira vez
				_funcoes.log("["+str(player_id)+"]", LOG, False, LOG_FILE)
				if player_id not in players_basic:
					players_basic.append(player_id)
					_funcoes.db_insert(conn, "jogador", {
						'id': player_id,
						'nome': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./a[1]").get_attribute("innerHTML")', driver, LOG, LOG_FILE)),
						'idade': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./span[1]").get_attribute("innerHTML")', driver, LOG, LOG_FILE)),
						'posicoes': _funcoes.break_player_positions(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./span[2]").get_attribute("innerHTML")', driver, LOG, LOG_FILE)),
						'altura': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[4]").get_attribute("innerHTML")', driver, LOG, LOG_FILE)),
						'peso': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[5]").get_attribute("innerHTML")', driver, LOG, LOG_FILE)),
					}, " -> [+ _jogador_]", LOG, LOG_FILE, False)
					_funcoes.db_insert(conn, "jogador_time", {
						'id_jogador': player_id,
						'id_time': team_id,
						'ano': SCRIPT_BEGIN.year,
						'ativo': "0" if "not-current-player" in _funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").get_attribute("class")', driver, LOG, LOG_FILE) else "1"
					}, " -> [+ _jogador_time_]", LOG, LOG_FILE, False)
				#Captura os dados da categoria, subcategoria do jogador
				player_tds_qtd = len(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr["+str(player_tr_index)+"]").find_elements_by_tag_name("td"))
				_funcoes.db_insert(conn, "jogador_attr", {
					'id_jogador': player_id,
					'id_torneio': table_squad_tournaments[tournament_index]["id"],
					'ano': str(SCRIPT_BEGIN.year),
					'jogos_jogados': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[6]").get_attribute("innerHTML")', driver, LOG, LOG_FILE)),
					'tempo_em_campo': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[7]").get_attribute("innerHTML")', driver, LOG, LOG_FILE)),
					'rating': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_tds_qtd)+']").get_attribute("innerHTML")', driver, LOG, LOG_FILE))
				}, " -> [+ _jogador_attr_]", LOG, LOG_FILE, False)
				#Pode comecar do 8 td, pois os anteriores nao mudam
				player_td_index = 8 if 8 <= player_tds_qtd else 1
				player_data_adv = {}
				while player_td_index <= player_tds_qtd:
					player_td_class = str(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_td_index)+']").get_attribute("class")', driver, LOG, LOG_FILE).strip("\t\n ").split(" ")[0])
					if player_td_class != "" and player_td_class != "pn" and player_td_class != "minsPlayed" and player_td_class != "rating" and player_td_class not in player_data_adv:
						player_data_adv[player_td_class] = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_td_index)+']").get_attribute("innerHTML")', driver, LOG, LOG_FILE))
					player_td_index += 1
				_funcoes.db_insert(conn, "jogador_attr", {'id_jogador': player_id,'id_torneio': table_squad_tournaments[tournament_index]["id"],'ano': SCRIPT_BEGIN.year}, " -> [... _jogador_attr_]", LOG, LOG_FILE, False, player_data_adv)
				player_tr_index += 1
				_funcoes.log("", LOG, True, LOG_FILE)
			table_squad_subcategories[subcategory_index]["visited"] = True
			subcategory_index = (subcategory_index+1) % len(table_squad_subcategories)
			#Salva o estado do crawler
			_funcoes.write_restore_file(restore_file, {'table_squad_tournaments': table_squad_tournaments, 'table_squad_category': table_squad_category, 'table_squad_subcategories': table_squad_subcategories})
		_funcoes.log("", LOG, True, LOG_FILE)
		table_squad_subcategories = []
		table_squad_category[category_index]["visited"] = True
		category_index = (category_index+1) % len(table_squad_category)
	_funcoes.log("", LOG, True, LOG_FILE)
	#Reseta as categorias
	for categoria in table_squad_category:
		categoria["visited"] = False
	table_squad_tournaments[tournament_index]["visited"] = True
	tournament_index = (tournament_index+1) % len(table_squad_tournaments)

driver.quit()
conn.close()
os.remove(restore_file)
