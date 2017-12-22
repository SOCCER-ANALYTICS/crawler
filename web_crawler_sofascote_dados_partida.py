from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import date
import psycopg2
from selenium.common.exceptions import NoSuchElementException        

#Funcao para validar se a xpath é válida
def check_exists_by_xpath(xpath):
    try:
        driver.find_element_by_xpath(xpath)
    except NoSuchElementException:
        return False
    return True

#Abre Browser
driver = webdriver.Firefox()

hoje = date.today()
x = 1
while x <= 1825: #5 anos X 365 dias = 1825  
    #Abre pagina principal baseado nos dias
    teste = "https://www.sofascore.com/pt/futebol/"+str(hoje)+""
    driver.get(teste)

    #bloco responsavel por validar xpath e clicar no jogo para entrar no mesmo e pegar informações
    sair = 0 
    while (sair = 0):
        xpath = """//*[@id="pjax-container-main"]/div/div[2]/div/div[2]/div[2]/div[1]/div[1]/div[2]"""
        #valida xpath
        if check_exists_by_xpath(xpath):
            #Clica na Xpath, para abrir informações macro da partida 
            driver.find_element_by_xpath(xpath).click()
            #Abre informações gerais da partida
            gethref = driver.find_element_by_xpath("/html/body/div[4]/div/div[2]/div/div[3]/div/div/div[1]/div[1]/a").get_attribute("href")
            driver.get(gethref)
            #Abre informações do jogador
            driver.find_element_by_xpath("/html/body/div[4]/div/div[2]/div/div[2]/ul/li[2]/a").click()

            #jogador - chutes - desarmes - totpasses- duelos vencidos - min jogados - posicao - avaliacao

            x = 1 
            while x <= 22:  
                varXpath = """//*[@id="player-statistics-tab-summary"]/table/tbody/tr["""+str(x)+"""]"""
                posts = driver.find_elements_by_xpath(varXpath)
                for post in posts:
                    #print(post.text)

                    #Conexão com BD 
                    conn = psycopg2.connect("host='localhost' dbname='sofascore' user='postgres' password='123'")
                    cursor = conn.cursor()

                    splitStats = post.text.split( )
        
                    if len(splitStats) == 11:
	                    print(splitStats[0]+' '+splitStats[1]+','+splitStats[2]+''+splitStats[3]+','+splitStats[4]+','+splitStats[5]+''+splitStats[6]+','+splitStats[7]+','+splitStats[8]+','+splitStats[9]+','+splitStats[10])
                    elif len(splitStats) == 12:
                        print(splitStats[0]+' '+splitStats[1]+' '+splitStats[2]+','+splitStats[3]+''+splitStats[4]+','+splitStats[5]+''+splitStats[6]+','+splitStats[7]+','+splitStats[8]+','+splitStats[9]+','+splitStats[10]+','+splitStats[11])
                    else:
	                    print(splitStats[0]+','+splitStats[1]+''+splitStats[2]+','+splitStats[3]+','+splitStats[4]+','+splitStats[5]+''+splitStats[6]+','+splitStats[7]+','+splitStats[8]+','+splitStats[9])	
                    conn.commit()    
                x = x + 1 
        else:
            #Ao não existir mais jogos no dia, sai do loop e prossegue ao dia anterior
            sair = 1

    #Retira um dia da data atual para abrir uma nova pagina e pegar novos jogos.
    hoje = date.fromordinal(hoje.toordinal()-1)
    x = x+1
    
