from random import randint
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from datetime import datetime, timedelta
import psycopg2
import translitcodec
import time
import json

#Decodifica string para ASCII
def decode_str(s):
	return s.encode('translit/one/ascii', 'replace').upper()

#Limpa a string de lixos, e converte alguns tipo de dados
def filter_data(s):
	remove_t_n = decode_str(s.strip('\t\n '))
	if remove_t_n == '-' or remove_t_n == 'N/A':
		result = '0'
	else:
		result = remove_t_n
	return decode_str(result)

#Tenta capturar dados, resolvendo excecoes de Stale
def no_stale_data(code, driver, conn, log_on, log_file):
	retries = 0
	while True:
		try:
			elem = eval(code)
			return elem
		except StaleElementReferenceException:
			log(" -> [Stale]", log_on, False, log_file)
		except NoSuchElementException:
			log(" -> [Nao achado]", log_on, False, log_file)
			time.sleep(3)
		if retries > 3:
			log(" -> [Erro critico ao ler elemento]", log_on, False, log_file)
			conn.close()
			driver.quit()
			quit()
		retries += 1

#Arruma o horario, que no site eh duas horas a mais
def fix_time_zone(day, hour):
	time_stamp = datetime.strptime(day+" "+hour, "%Y-%m-%d %H:%M")
	time_zoned = time_stamp - timedelta(hours=2)
	return str(time_zoned).split(" ")

#Verifica se value eh uma substring de algum valor no array
def check_substr_array(arr, value):
	if len(arr) == 0:
		return True
	for val in arr:
		if value in val:
			return True
	return False

#Retorna o array de posicoes que o jogador ocupa no time
def break_player_positions(s):
	return ", ".join([position.strip('\t\n ') for position in s.split(",") if position])

#Retorna um array com o dia, mes e ano, quebrados de uma string no formato ex:'Mon, Dec 25 2017'
def break_date_long(s):
	return [str(d).upper() for d in s.split(" ")[1:]]

#Retorna um array com id e nome do time, quebrado da linha href
def break_team_data(s):
	data = s.split("/")
	return [data[4], " ".join(data[6].split("-")[1:]).upper()]

#Verifica se algum 'select' ainda nao foi visitado
def check_all_visited(arr):
	for obj in arr:
		if not obj["visited"]:
			return False
	return True

#Espera um tempo aleatorio entre 1 - 4 seg
def im_human():
	time.sleep(randint(1, 4))

#Escreve a msg no arquivo ou na tela
def log(msg, log, newline, f=None):
	if not log:
		return 0
	if f == None:
		if newline:
			print msg
		else:
			print msg,
	else:
		if newline:
			f.write(msg+"\n")
		else:
			f.write(msg)

#Escreve para os arquivos de restore
def write_restore_file(filename, data):
	with open(filename, "w") as outfile:
		json.dump(data, outfile)

#Cria linha set de update
def prepared_update(data):
	return ",".join([key.lower()+"='"+str(data[key])+"'" for key in data])

def prepared_insert(data):
	result = {'key': "", 'value': ""}
	for key in data:
		result['key'] += ','+key.lower()
		result['value'] += ",'"+str(data[key])+"'"
	result['key'] = result['key'][1:]
	result['value'] = result['value'][1:]
	return result

#Insere dados no bd
def db_insert(conn, table_name, insert_data, LOG_MSG, LOG, LOG_FILE, NEXT_LINE, update_data=None):
	if table_name == "player_attr":
		conflict_var = "player_id,tournament_id,year"
	elif table_name == "player_team":
		conflict_var = "player_id,team_id,year"
	elif table_name == "match_date":
		conflict_var = "team_id,tournament_id,date,time"
	else:
		conflict_var = "id"
	insert_data = prepared_insert(insert_data)
	cur = conn.cursor()
	try:
		if update_data != None:
			cur.execute("INSERT INTO "+table_name+" ("+insert_data["key"]+") VALUES ("+insert_data["value"]+") ON CONFLICT ("+conflict_var+") DO UPDATE SET "+prepared_update(update_data))
			LOG_MSG += " -> [Inserido/Atualizado]" if cur.rowcount > 0 else " -> [Nada feito]"
		else:
			cur.execute("INSERT INTO "+table_name+" ("+insert_data["key"]+") VALUES ("+insert_data["value"]+") ON CONFLICT ("+conflict_var+") DO NOTHING")
			LOG_MSG += " -> [Inserido]" if cur.rowcount > 0 else " -> [Ja inserido]"
		log(LOG_MSG, LOG, NEXT_LINE, LOG_FILE)
		conn.commit()
		query_ok = True
	except psycopg2.Error as e:
		log(LOG_MSG+" -> ["+e.pgerror+"]", LOG, NEXT_LINE, LOG_FILE)
		conn.rollback()
		query_ok = False
	cur.close()
	return query_ok

#Executa uma query no bd
def db_exec(conn, query, query_data, LOG_MSG, LOG, LOG_FILE, NEXT_LINE):
	data = None
	cur = conn.cursor()
	try:
		cur.execute(query, query_data)
		#log(LOG_MSG+" -> ["+(query % query_data)+"]", LOG, NEXT_LINE, LOG_FILE)
		data = cur.fetchall()
	except psycopg2.Error as e:
		log(LOG_MSG+" -> ["+e.pgerror+"]", LOG, NEXT_LINE, LOG_FILE)
	cur.close()
	return data

#Tenta restartar o driver ate 5 vezes
# def restart(driver, profile, url, delay, LOG, LOG_FILE):
# 	retries = 0
# 	log(" ->  [Desligando]", LOG, False, LOG_FILE)
# 	driver[-1].quit()
# 	if delay > 0:
# 		log(" ->  [Dormindo]", LOG, False, LOG_FILE)
# 		time.sleep(delay)
# 	log(" ->  [Iniciando]", LOG, False, LOG_FILE)
# 	while True:
# 		try:
# 			driver.append(webdriver.Firefox(firefox_profile=profile))
# 			driver[-1].get(url)
# 			break
# 		except Exception as e:
# 			print e
# 			if retries > 4:
# 				log(" ->  [Erro Critico ao reiniciar o driver]", LOG, True, LOG_FILE)
# 				quit()
# 			log(" ->  [Re-tentando]", LOG, False, LOG_FILE)
# 			time.sleep(4)
# 			retries += 1