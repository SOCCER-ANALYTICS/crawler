from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementNotInteractableException
from selenium.webdriver.common.by import By
import psycopg2
import sys
import os.path
import json
from datetime import datetime
import _funcoes

######################################################################
# Exec: python whoscored_time_geral.py [-v: Bash log | -f: File log] #
######################################################################

#Script Vars
SCRIPT_NAME = sys.argv[0].split(".")[0]
SCRIPT_BEGIN = datetime.now()
LOG = True if "-v" in sys.argv or "-f" in sys.argv else False
LOG_FILE = open("logs/"+str(SCRIPT_BEGIN.day)+"_"+str(SCRIPT_BEGIN.month)+"_"+str(SCRIPT_BEGIN.year)+"__"+str(SCRIPT_BEGIN.hour)+"_"+str(SCRIPT_BEGIN.minute)+"_"+str(SCRIPT_BEGIN.second)+"__"+SCRIPT_NAME+".txt", "w") if "-f" in sys.argv else None
players_basic = []
tournament_year = None

_funcoes.log("[Iniciando Spyder]", LOG, False, LOG_FILE)
try:
	conn = psycopg2.connect("dbname='whoscored' user='postgres' host='localhost' password='12345678'")
	_funcoes.log(" -> [Postgresql Ok]", LOG, False, LOG_FILE)
except:
	_funcoes.kill_script(" -> [Postgresql Error]", None, None, LOG, LOG_FILE)

###########################
## Captura dados do time ##
###########################
team_id = _funcoes.db_exec(conn, "SELECT t.id,t.name FROM team t INNER JOIN match_date md ON t.id=md.team_id WHERE t.current_seen_date IS NULL OR (t.current_seen_date<md.date AND ((CURRENT_DATE>md.date) OR (CURRENT_DATE=md.date AND CURRENT_TIME>=md.time + interval '3 hours'))) LIMIT 1", (), "[Verifica Time]", LOG, LOG_FILE, False)
if len(team_id) == 1:
	_funcoes.log(" -> [Achado "+str(team_id[0][0])+" | "+team_id[0][1]+"]", LOG, False, LOG_FILE)
	team_id = str(team_id[0][0])
else:
	_funcoes.kill_script(" -> [Nenhum Time p/ Atualizar]", None, conn, LOG, LOG_FILE)

#Configura Proxy Tor
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1366x768')
options.add_argument('--proxy-server=127.0.0.1:9050')
options.add_argument('--log-level=3')
driver = webdriver.Chrome(chrome_options=options)

_funcoes.log(" -> [ChromeDriver Ok]", LOG, False, LOG_FILE)

#Abre o arquivo de restauracao, se houve erro na execucao passada
restore_file = 'restores/.'+SCRIPT_NAME+"_"+team_id+".json"
if os.path.isfile(restore_file):
	with open(restore_file) as infile:
		restore_data = json.load(infile)
		_funcoes.log(" -> [Restaurando..]", LOG, False, LOG_FILE)
else:
	restore_data = None

_funcoes.log(" -> [Carregando URL...]", LOG, False, LOG_FILE)
url = 'https://www.whoscored.com/Teams/'+team_id
driver.get(url)
_funcoes.log(" -> [Carregado]", LOG, True, LOG_FILE)

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

#Captura o ano do torneio do time e a regiao do torneio
try:
	tournament_year = driver.find_element_by_xpath('//*[@id="layout-content-wrapper"]/div[3]/div[3]/div/div[3]/dl/dd[2]').text.split("/")[1]
	region_id = driver.find_element_by_xpath('//*[@id="breadcrumb-nav"]/a').get_attribute("href").split("/")[4]
except NoSuchElementException:
	_funcoes.kill_script("(*) Painel lateral direito nao carregou", driver, conn, LOG, LOG_FILE)

#Na tabela, muda para detalhes
try:
	driver.find_element_by_id("team-squad-stats").find_element_by_xpath('//*[@id="team-squad-stats-options"]/li[5]/a').click()
except ElementNotInteractableException:
	_funcoes.db_insert(conn, "team", {'id': team_id}, "[Atualizando data_seen do team] -> [Inserindo..]", LOG, LOG_FILE, True, {'current_seen_date': str(SCRIPT_BEGIN.year)+"-"+str(SCRIPT_BEGIN.month)+"-"+str(SCRIPT_BEGIN.day)})
	_funcoes.kill_script("(*)(*) O time nao possui dados o suficiente", driver, conn, LOG, LOG_FILE)
except NoSuchElementException:
	_funcoes.db_insert(conn, "team", {'id': team_id}, "[Atualizando data_seen do team] -> [Inserindo..]", LOG, LOG_FILE, True, {'current_seen_date': str(SCRIPT_BEGIN.year)+"-"+str(SCRIPT_BEGIN.month)+"-"+str(SCRIPT_BEGIN.day)})
	_funcoes.kill_script("(*)(*) O time nao possui nenhum dado", driver, conn, LOG, LOG_FILE)

try:
	accumulation_select = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "statsAccumulationType")))
except TimeoutException:
	_funcoes.kill_script("(*) Timeout ao mudar para a aba 'Detalhes'", driver, conn, LOG, LOG_FILE)

#Seleciona os dados para quantidade 'Total'
accumulation_select.find_element_by_xpath(".//option[4]").click()
try:
	WebDriverWait(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed"), 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
except TimeoutException:
	_funcoes.kill_script("(*) Timeout ao alterar tipo dos dados para 'Total'", driver, conn, LOG, LOG_FILE)

#-------------------------Captura os torneios do time--------------------------#
if len(table_squad_tournaments) == 0:
	tournament_options_qtd = len(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("tournamentOptions").find_elements_by_tag_name("option"))
	tournament_index = 1
	while tournament_index <= tournament_options_qtd:
		table_squad_tournaments.append({
			"path": './option['+str(tournament_index)+']',
			"id": _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("tournamentOptions").find_element_by_xpath("./option['+str(tournament_index)+']").get_attribute("value")', driver, conn, LOG, LOG_FILE)),
			"name": _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("tournamentOptions").find_element_by_xpath("./option['+str(tournament_index)+']").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE)),
			"visited": False,
			"loaded": True if tournament_index == 1 else False
		})
		_funcoes.log("[Verifica "+table_squad_tournaments[-1]["id"]+" | "+table_squad_tournaments[-1]["name"]+"]", LOG, False, LOG_FILE)
		#Verifica se o torneio ja existe no bd
		tournament_check = _funcoes.db_exec(conn, "SELECT id FROM tournament WHERE id=%s", (table_squad_tournaments[-1]["id"],), "", LOG, LOG_FILE, False)
		if len(tournament_check) == 0:
			_funcoes.db_insert(conn, "tournament", {
				'id': table_squad_tournaments[-1]["id"],
				'region_id': region_id,
				'name': table_squad_tournaments[-1]["name"],
			}, " -> [+ _tournament_]", LOG, LOG_FILE, True)
		else:
			_funcoes.log("-> [Achado]", LOG, True, LOG_FILE)
		tournament_index += 1

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
				player_id = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./a[1]").get_attribute("href")', driver, conn, LOG, LOG_FILE).split("/")[4])
				#Pega os dados basicos apenas na primeira vez
				_funcoes.log("["+str(player_id)+"]", LOG, False, LOG_FILE)
				if player_id not in players_basic:
					players_basic.append(player_id)
					_funcoes.db_insert(conn, "player", {
						'id': player_id,
						'name': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./a[1]").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE)),
						'age': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./span[1]").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE)),
						'positions': _funcoes.break_player_positions(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./span[2]").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE)),
						'height': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[4]").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE)),
						'weight': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[5]").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE)),
					}, " -> [+ _jogador_]", LOG, LOG_FILE, False)
					_funcoes.db_insert(conn, "player_team", {
						'player_id': player_id,
						'team_id': team_id,
						'year': tournament_year,
						'active': "0" if "not-current-player" in _funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").get_attribute("class")', driver, conn, LOG, LOG_FILE) else "1"
					}, " -> [+ _jogador_time_]", LOG, LOG_FILE, False)
				#Captura os dados da categoria, subcategoria do jogador
				player_tds_qtd = len(driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr["+str(player_tr_index)+"]").find_elements_by_tag_name("td"))
				_funcoes.db_insert(conn, "player_attr", {
					'player_id': player_id,
					'tournament_id': table_squad_tournaments[tournament_index]["id"],
					'year': tournament_year,
					'matchesplayed': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[6]").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE)),
					'fieldtime': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[7]").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE)),
					'rating': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_tds_qtd)+']").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE))
				}, " -> [+ _jogador_attr_]", LOG, LOG_FILE, False)
				#Pode comecar do 8 td, pois os anteriores nao mudam
				player_td_index = 8 if 8 <= player_tds_qtd else 1
				player_data_adv = {}
				while player_td_index <= player_tds_qtd:
					player_td_class = str(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_td_index)+']").get_attribute("class")', driver, conn, LOG, LOG_FILE).strip("\t\n ").split(" ")[0])
					if player_td_class != "" and player_td_class != "pn" and player_td_class != "minsPlayed" and player_td_class != "rating" and player_td_class not in player_data_adv:
						player_data_adv[player_td_class] = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-stats").find_element_by_id("team-squad-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_td_index)+']").get_attribute("innerHTML")', driver, conn, LOG, LOG_FILE))
					player_td_index += 1
				_funcoes.db_insert(conn, "player_attr", {'player_id': player_id,'tournament_id': table_squad_tournaments[tournament_index]["id"],'year': tournament_year}, " -> [... _jogador_attr_]", LOG, LOG_FILE, False, player_data_adv)
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

_funcoes.db_insert(conn, "team", {'id': team_id}, "[Atualizando data_seen do team] -> [Inserindo..]", LOG, LOG_FILE, True, {'current_seen_date': str(SCRIPT_BEGIN.year)+"-"+str(SCRIPT_BEGIN.month)+"-"+str(SCRIPT_BEGIN.day)})
_funcoes.log("[Nada mais a fazer]", LOG, False, LOG_FILE)
driver.quit()
_funcoes.log("-> [Fechando ChromeDriver]", LOG, False, LOG_FILE)
conn.close()
_funcoes.log("-> [Fechando DB]", LOG, False, LOG_FILE)
os.remove(restore_file)
_funcoes.log("-> [Removendo Restore_File]", LOG, True, LOG_FILE)