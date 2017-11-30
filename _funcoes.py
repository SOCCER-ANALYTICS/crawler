from random import randint
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
import psycopg2
import translitcodec
import time
import json

#Decodifica string para ASCII
def decode_str(s):
	return s.encode('translit/one/ascii', 'replace')

#Limpa a string de lixos, e converte alguns tipo de dados
def filter_data(s):
	remove_t_n = decode_str(s.strip('\t\n '))
	if remove_t_n == '-':
		result = '0'
	else:
		result = remove_t_n
	return decode_str(result)

#Tenta capturar dados, resolvendo excecoes de Stale
def no_stale_data(code, driver, log_on, log_file):
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
			quit()
		retries += 1

#Retorna o array de posicoes que o jogador ocupa no time
def break_player_positions(s):
	return ", ".join([position.strip('\t\n ') for position in s.split(",") if position])

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
	if table_name == "jogador_attr":
		conflict_var = "id_jogador,id_torneio,ano"
	elif table_name == "jogador_time":
		conflict_var = "id_jogador,id_time,ano"
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

#Tenta restartar o driver ate 5 vezes
def restart(driver, profile, url, delay, LOG, LOG_FILE):
	retries = 0
	log(" ->  [Desligando]", LOG, False, LOG_FILE)
	driver[-1].quit()
	if delay > 0:
		log(" ->  [Dormindo]", LOG, False, LOG_FILE)
		time.sleep(delay)
	log(" ->  [Iniciando]", LOG, False, LOG_FILE)
	while True:
		try:
			driver.append(webdriver.Firefox(firefox_profile=profile))
			driver[-1].get(url)
			break
		except Exception as e:
			if retries > 4:
				log(" ->  [Erro Critico ao reiniciar o driver]", LOG, True, LOG_FILE)
				quit()
			log(" ->  [Re-tentando]", LOG, False, LOG_FILE)
			time.sleep(4)
			retries += 1