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
TOR_CON_RENEW = 150
DRIVER_RESTART_TIMEOUT = 120 #10min
driver = []

#Configura Proxy Tor
profile = webdriver.FirefoxProfile()
profile.set_preference("network.proxy.type", 1)
profile.set_preference("network.proxy.http", "127.0.0.1")
profile.set_preference("network.proxy.http_port", 9050)
profile.set_preference("network.proxy.ssl", "127.0.0.1")
profile.set_preference("network.proxy.ssl_port", 9050)
profile.set_preference("network.proxy.socks", "127.0.0.1")
profile.set_preference("network.proxy.socks_port", 9050)

driver.append(webdriver.Firefox(firefox_profile=profile))

#Abre o arquivo de restauracao, se houve erro na execucao passada
restore_file = '.'+SCRIPT_NAME+"_"+team_id+".json"
if os.path.isfile(restore_file):
	with open(restore_file) as infile:
		restore_data = json.load(infile)
else:
	restore_data = None

url='https://www.whoscored.com/Teams/'+team_id+'/Archive'
driver[-1].get(url)

##############################################################
## Preparacao da tabela 'Squad Archive' de cada Torneio-Ano ##
##############################################################
if restore_data != None:
	select_year_tournaments = restore_data["select_year_tournaments"]
	table_squad_category = restore_data["table_squad_category"]
	table_squad_subcategories = restore_data["table_squad_subcategories"]
	_funcoes.log("(*) Restore Carregado", LOG, True, LOG_FILE)
else:
	select_year_tournaments = []
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
	_funcoes.log("(*) Restore nao encontrado", LOG, True, LOG_FILE)

#################################
## Captura os torneios do time ##
#################################
if len(select_year_tournaments) == 0:
	tournament_options_qtd = len(driver[-1].find_element_by_id("stageId").find_elements_by_tag_name("option"))
	tournament_index = 1
	while tournament_index <= tournament_options_qtd:
		tournament_data = _funcoes.no_stale_data('driver.find_element_by_id("stageId").find_element_by_xpath("./option['+str(tournament_index)+']").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE).split("-")
		tournament_name = _funcoes.filter_data(tournament_data[0])
		tournament_id = _funcoes.db_exec(conn, "SELECT id FROM torneio WHERE nome=%s", (tournament_name,), "[Verifica ID Torneio]", LOG, LOG_FILE, True)
		if len(tournament_id) == 1:
			select_year_tournaments.append({
				"path": './option['+str(tournament_index)+']',
				"name": tournament_name,
				"year": _funcoes.filter_data(tournament_data[1].split("/")[0]),
				"id": tournament_id[0][0],
				"visited": False,
				"loaded": True if tournament_index == 1 else False
			})
		tournament_index += 1

#--------------------------------Para cada torneio do ano-----------------------------#
tournament_index = 0
#Enquanto todos os tournaments nao forem carregados, continue tentando
while not _funcoes.check_all_visited(select_year_tournaments):
	players_basic = []
	_funcoes.log("Tournament  : "+str(select_year_tournaments[tournament_index]["name"]+" ("+select_year_tournaments[tournament_index]["year"]+")"), LOG, False, LOG_FILE)
	if select_year_tournaments[tournament_index]["visited"]:
		_funcoes.log(" ->  [Ja visto]", LOG, True, LOG_FILE)
		tournament_index = (tournament_index+1) % len(select_year_tournaments)
		continue
	_funcoes.log(" -> [Visitando..]", LOG, False, LOG_FILE)
	#Carrega o torneio
	if not select_year_tournaments[tournament_index]["loaded"]:
		#Verifica se deu o tempo limite do driver[-1]
		#if (datetime.now()-SCRIPT_BEGIN).total_seconds() > DRIVER_RESTART_TIMEOUT:
		#	_funcoes.restart(driver, profile, url, 0, LOG, LOG_FILE)
		#else:
		_funcoes.log(" -> [Carregando..]", LOG, False, LOG_FILE)
		_funcoes.im_human()
		try:
			driver[-1].find_element_by_id("stageId").find_element_by_xpath(select_year_tournaments[tournament_index]["path"]).click()
		except NoSuchElementException:
			_funcoes.log(" -> [Erro Critico]", LOG, False, LOG_FILE)
			_funcoes.restart(driver, profile, url, TOR_CON_RENEW, LOG, LOG_FILE)
			#driver[-1].find_element_by_id("stageId").find_element_by_xpath(select_year_tournaments[tournament_index]["path"]).click()
		try:
			WebDriverWait(driver[-1], 10).until(EC.presence_of_element_located((By.ID, "team-squad-archive-stats-detailed")))
			_funcoes.log(" -> [Carregado]", LOG, False, LOG_FILE)
		except TimeoutException:
			_funcoes.log(" -> [Timeout]", LOG, True, LOG_FILE)
			tournament_index = (tournament_index+1) % len(select_year_tournaments)
			continue
	else:
		_funcoes.log(" -> [Carregado]", LOG, False, LOG_FILE)
	#Na tabela, muda para detalhes
	driver[-1].find_element_by_xpath('//*[@id="team-squad-archive-stats-options"]/li[5]/a').click()
	try:
		accumulation_select = WebDriverWait(driver[-1], 10).until(EC.presence_of_element_located((By.ID, "statsAccumulationType")))
		_funcoes.log(" -> [Mudou 'Detalhes']", LOG, False, LOG_FILE)
	except TimeoutException:
		_funcoes.log(" -> [Timeout - 'Detalhes']", LOG, True, LOG_FILE)
		tournament_index = (tournament_index+1) % len(select_year_tournaments)
		continue
	#Seleciona os dados para quantidade 'Total'
	accumulation_select.find_element_by_xpath(".//option[4]").click()
	try:
		WebDriverWait(driver[-1].find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed"), 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
		_funcoes.log(" -> [Mudou 'Total']", LOG, True, LOG_FILE)
	except TimeoutException:
		_funcoes.log(" -> [Timeout - 'Total']", LOG, True, LOG_FILE)
		tournament_index = (tournament_index+1) % len(select_year_tournaments)
		continue
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
			_funcoes.log(" -> [Carregando..]", LOG, False, LOG_FILE)
			_funcoes.im_human()
			driver[-1].find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_xpath(table_squad_category[category_index]["path"]).click()
			try:
				WebDriverWait(driver[-1].find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed"), 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
				_funcoes.log(" -> [Carregado]", LOG, True, LOG_FILE)
			except TimeoutException:
				_funcoes.log(" -> [Timeout]", LOG, True, LOG_FILE)
				category_index = (category_index+1) % len(table_squad_category)
				continue
		else:
			_funcoes.log(" -> [Carregado]", LOG, True, LOG_FILE)
		#----------------Captura as subcategorias da categoria--------------------#
		if len(table_squad_subcategories) == 0:
			subcategory_index = 1
			subcategory_options_qtd = len(driver[-1].find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("subcategory").find_elements_by_tag_name("option"))
			while subcategory_index <= subcategory_options_qtd:
				table_squad_subcategories.append({"path": './option['+str(subcategory_index)+']', "visited": False, "loaded": True if subcategory_index == 1 else False})
				subcategory_index += 1
		#------------------------Para cada subcategorias--------------------------#
		subcategory_index = 0
		while not _funcoes.check_all_visited(table_squad_subcategories):
			_funcoes.log("Sub-Category: "+str(subcategory_index), LOG, False, LOG_FILE)
			if table_squad_subcategories[subcategory_index]["visited"]:
				_funcoes.log(" -> [Ja visto]", LOG, True, LOG_FILE)
				subcategory_index = (subcategory_index+1) % len(table_squad_subcategories)
				continue
			_funcoes.log(" -> [Visitando..]", LOG, False, LOG_FILE)
			if not table_squad_subcategories[subcategory_index]["loaded"]:
				_funcoes.log(" -> [Carregando..]", LOG, False, LOG_FILE)
				_funcoes.im_human()
				driver[-1].find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("subcategory").find_element_by_xpath(table_squad_subcategories[subcategory_index]["path"]).click()
				try:
					WebDriverWait(driver[-1].find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed"), 10).until(EC.invisibility_of_element_located((By.ID, "statistics-table-detailed-loading")))
					_funcoes.log(" -> [Carregado]", LOG, True, LOG_FILE)
				except TimeoutException:
					_funcoes.log(" -> [Timeout]", LOG, True, LOG_FILE)
					subcategory_index = (subcategory_index+1) % len(table_squad_subcategories)
					continue
			else:
				_funcoes.log(" -> [Carregado]", LOG, True, LOG_FILE)
			#--------------------------Para cada jogador-----------------------------#
			_funcoes.log("Players     : ", LOG, True, LOG_FILE)
			player_tr_index = 1
			player_trs_qtd = len(driver[-1].find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_elements_by_tag_name("tr"))
			while player_tr_index <= player_trs_qtd:
				player_id = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./a[1]").get_attribute("href")', driver[-1], LOG, LOG_FILE).split("/")[4])
				#Pega os dados basicos apenas na primeira vez
				_funcoes.log("["+str(player_id)+"]", LOG, False, LOG_FILE)
				if player_id not in players_basic:
					players_basic.append(player_id)
					_funcoes.db_insert(conn, "jogador", {
						'id': player_id,
						'nome': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./a[1]").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE)),
						'idade': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./span[1]").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE)),
						'posicoes': _funcoes.break_player_positions(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_class_name("pn").find_element_by_xpath("./span[2]").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE)),
						'altura': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[4]").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE)),
						'peso': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[5]").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE))
					}, " -> [+ _jogador_]", LOG, LOG_FILE, False)
					_funcoes.db_insert(conn, "jogador_time", {
						'id_jogador': player_id,
						'id_time': team_id,
						'ano': select_year_tournaments[tournament_index]["year"],
						'ativo': "0" if "not-current-player" in _funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").get_attribute("class")', driver[-1], LOG, LOG_FILE) else "1"
					}, " -> [+ _jogador_time_]", LOG, LOG_FILE, False)
				#Captura os dados da categoria, subcategoria do jogador
				player_tds_qtd = len(driver[-1].find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr["+str(player_tr_index)+"]").find_elements_by_tag_name("td"))
				_funcoes.db_insert(conn, "jogador_attr", {
					'id_jogador': player_id,
					'id_torneio': select_year_tournaments[tournament_index]["id"],
					'ano': select_year_tournaments[tournament_index]["year"],
					'jogos_jogados': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[6]").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE)),
					'tempo_em_campo': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td[7]").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE)),
					'rating': _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_tds_qtd)+']").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE))
				}, " -> [+ _jogador_attr_]", LOG, LOG_FILE, False)
				#Pode comecar do 8 td, pois os anteriores nao mudam
				player_td_index = 8 if 8 <= player_tds_qtd else 1
				player_data_adv = {}
				while player_td_index <= player_tds_qtd:
					player_td_class = _funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_td_index)+']").get_attribute("class")', driver[-1], LOG, LOG_FILE).strip("\t\n ").split(" ")[0]
					if player_td_class != "" and player_td_class != "pn" and player_td_class != "minsPlayed" and player_td_class != "rating" and player_td_class not in player_data_adv:
						player_data_adv[player_td_class] = _funcoes.filter_data(_funcoes.no_stale_data('driver.find_element_by_id("team-squad-archive-stats").find_element_by_id("team-squad-archive-stats-detailed").find_element_by_id("player-table-statistics-body").find_element_by_xpath("./tr['+str(player_tr_index)+']").find_element_by_xpath("./td['+str(player_td_index)+']").get_attribute("innerHTML")', driver[-1], LOG, LOG_FILE))
					player_td_index += 1
				_funcoes.db_insert(conn, "jogador_attr", {'id_jogador': player_id,'id_torneio': select_year_tournaments[tournament_index]["id"],'ano': select_year_tournaments[tournament_index]["year"]}, " -> [... _jogador_attr_]", LOG, LOG_FILE, False, player_data_adv)
				player_tr_index += 1
				_funcoes.log("", LOG, True, LOG_FILE)
			table_squad_subcategories[subcategory_index]["visited"] = True
			subcategory_index = (subcategory_index+1) % len(table_squad_subcategories)
			#Salva o estado do crawler
			_funcoes.write_restore_file(restore_file, {'select_year_tournaments': select_year_tournaments, 'table_squad_category': table_squad_category, 'table_squad_subcategories': table_squad_subcategories})
		_funcoes.log("", LOG, True, LOG_FILE)
		table_squad_subcategories = []
		table_squad_category[category_index]["visited"] = True
		category_index = (category_index+1) % len(table_squad_category)
	_funcoes.log("", LOG, True, LOG_FILE)
	#Reseta as categorias
	for categoria in table_squad_category:
		categoria["visited"] = False
	select_year_tournaments[tournament_index]["visited"] = True
	tournament_index = (tournament_index+1) % len(select_year_tournaments)

driver[-1].quit()
conn.close()
os.remove(restore_file)