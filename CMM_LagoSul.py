#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# CMM Oficial com placa de expansão da BRAVAS Technololgy  , criar classes para os outros modulos expansores.
# Desenvolvido por Leandro Leal  rev. 18/07/2019

import biblioteca_CMM as cmm

import time
from datetime import timedelta
import datetime
import os     # Executa comandos do sistema operacional Ex.: os.system('sudo reboot now'))
import threading # Modulo superior Para executar as threads
import sys
import socket
import json
import mysql.connector

os.system("mpg123 /home/pi/CMM/mp3/reiniciando_sistema.mp3")

socket.setdefaulttimeout(2) # limite de 2 segundos para enviar o socket

hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
h = int(time.strftime('%H'))
data = time.strftime('%d/%m/%y')


def log(texto): # Metodo para registro dos eventos no log.txt (exibido na interface grafica)

    hs = time.strftime("%H:%M:%S") 
    data = time.strftime('%d/%m/%y')

    texto = str(texto)

    if texto == "*":

        l = open("/var/www/html/log/log.txt","a")
        l.write("\n")
        l.close()

    else:              

        escrita = ("{} - {}  Evento:  {}\n").format(data, hs, texto)
        escrita = str(escrita)

        l = open("/var/www/html/log/log.txt","a")
        l.write(escrita)
        l.close()
    
l = open("/var/www/html/log_qrcode.txt","a") # Pula uma linha no registro de log
l.write("\n")
l.close()

log("*")
log("Reiniciou o sistema")
log("*")

nome = os.popen('hostname').readline()
nome = str(nome)
nome = nome.replace("\n","")

ip = os.popen('hostname -I').readline()
ip = str(ip)
ip = ip.replace("\n","")

txt = ("Nome desta maquina",nome) #,"com IP",ip)
txt = str(txt)
txt = txt.replace("'","")
txt = txt.replace(",","")
txt = txt.replace("(","")
txt = txt.replace(")","")
txt = txt.replace("\n","")
log(txt)

txt = ("Horario atual",time.strftime("%H:%M:%S"))
txt = str(txt)
txt = txt.replace("'","")
txt = txt.replace(",","")
txt = txt.replace("(","")
txt = txt.replace(")","")
txt = txt.replace("\n","")
log(txt)

############################ INICIA AS CLASSES DA Biblioteca_CMM_Bravas  ########################################

rele = cmm.Rele() # inicia a classe rele com port A em 0
##rele.liga(1)    # Liga rele 1 (podendo ser de 1 a 8)
##rele.desliga(1)  # Desliga rele 1 (podendo ser de 1 a 8)
##rele.pulsa(8,2)  # rele.pulso(rele,tempo)  Pulsa o rele pelo tempo indicado em segundos

entradas = cmm.Entradas()
# Classes para leituras das entradas definidas no arq. config.txt
# Ex. ctw2 = entradas.ctw2
#     qde = entradas.qde                       
#     pm1 = entradas.pm1

saidas = cmm.Saidas()
# Classes para acionamento das saidas definidas no arq. config.txt

narrador = cmm.Narrador()
##narrador.falar("Teste do narrador") # fala o texto enviado - depende de internet
##narrador.gravar("Qrcode não cadastrado","semCadastro") # Grava o texto enviado em nome.mp3

temperatura = cmm.Temperatura()
##print ("\nTemperatura",temperatura.cpu(),"°C\n")  # obter temperatura

email = cmm.Email()
##email.enviar("O Programa acabou de reiniciar\nPosso enviar qualquer mensagem aqui...") # Não usar nenhum caracter especial na mensagem

clima = cmm.Clima()
##tempo = clima.clima_atual()
##print(tempo)

evento = cmm.Evento("0054")
# Inicia a classe para envio de eventos para o Moni com o codigo do cliente

banco = cmm.Banco()
# banco.consulta("tabela","coluna") / banco.atualiza("tabela","coluna","valor")

notifica = cmm.Notifica()
# Condfy - Aviso de QR Code utilizado Ex. notifica.qr_utilizado("2019","83587161") cliete,id do qr utilizado

qr1_garagem = cmm.Qrcode("172.19.1.244","0001",4,"garagem_entrada","1") # IP,Cliente,rele,portao,notificar o condfy) - "172.18.34.247","5987",4,"social" ou "eclusa", "1" notificar o condfy do qrcode usado
qr2_garagem = cmm.Qrcode("172.19.1.243","0001",5,"garagem_saida","0") # IP,Cliente,rele,portao) - "172.18.34.247","5987",4,"social" ou "eclusa"
#qr3 = cmm.Qrcode("172.18.34.249","5987",4,"garagem_entrada") # IP,Cliente,rele,portao) - "172.18.34.247","5987",4,"garagem_entrada" ou "garagem_saida"
#qr4 = cmm.Qrcode("172.18.34.250","5987",5,"garagem_saida") # IP,Cliente,rele,portao) - "172.18.34.247","5987",4,"garagem_entrada" ou "garagem_saida"

################################### Escreve no log da interface grafica #########################



##############################################  Threads dos programas  ##########################################################

def thread_qrcode_garagem_1(): # Programa que mantem a conexão com o QR Code

    log("Programa QR Code Garagem entrada em execução")

    qr1_garagem.start() # Conecta com o leitor dentro da classe do QR Code

qr_garagem_entrada = threading.Thread(target=thread_qrcode_garagem_1)
qr_garagem_entrada.start()

def thread_qrcode_garagem_2(): # Programa que mantem a conexão com o QR Code

    log("Programa QR Code Garagem saida em execução")

    qr2_garagem.start() # Conecta com o leitor dentro da classe do QR Code

qr_garagem_saida = threading.Thread(target=thread_qrcode_garagem_2)
qr_garagem_saida.start()
    

############################################################################################

def Servidor_qr(): ######### Thread servidor Cadastro QR Code ###################

    time.sleep(1)

    deletar = 0
    cadastrar = 0

    host_servidor = '172.19.1.251'  # Host servidor 
    port_gerenciador = 5511# porta para receber dados do gerenciador
    

##    log("Ouvindo Gerenciador na porta",port_gerenciador)
    
    while(1):

        socket.setdefaulttimeout(9999)

        hs = time.strftime("%H:%M:%S") # MANTEM ATUALIZADO O HORARIO DO REGISTRO DE LOG        
              
        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            
            try:
                s.bind((host_servidor, port_gerenciador))
            except socket.error as msg:
                txt = ("Erro servidor gerenciador",msg)
                log(txt)
                
            return s

        def setupConnection():
            
            s.listen(10)
            conn, address = s.accept()
            
##            txt = ("Conectado com: " + address[0] + ":" + str(address[1]))
##            txt = str(txt)
##            txt = txt.replace("'","")
##            txt = txt.replace(",","")
##            txt = txt.replace("(","")
##            txt = txt.replace(")","")            
##            log(txt)
            
            return conn

        def dataTransfer(conn):  # Loop de transferencia e recepção de dados
            
            while True:

                try:
           
                    data = conn.recv(1024)  # Recebe o dado
                    data = data.decode('utf-8')

##                    log("dados recebidos")
##                    log(data)
                    

                    comando = (data.split("&")[0])
                    corpo = (data.split("&")[1])                   

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
                    conn.close()

                except Exception as err:

##                    txt = ("Dados recebidos estao fora do formato",err)
##                    log(txt)
                    
                    break

                
    
                if comando == "deletar_qr":

                    log("Reconheceu deletar")

                    
                    ID = corpo.split(":")[0]

                    txt = ("ID", ID)
                    log(txt)
                    
                    cliente = corpo.split(":")[1]

                    txt =("cliente",cliente)
                    log(txt)
                    

                    try:  # Tenta conectar com o banco de dados
                
                        log('Conectando banco de dados...')  
                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()
                        log('Conectado\n')
                      
                    except mysql.connector.Error as err:
                        
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                          
                            log("Alguma coisa esta errada com o nome de usuario ou a senha!")
                        
                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                          
                            log("Esta base de dados nao existe")
                        
                        else:
                          
                            log(err)

                    else:

                        log("Vai tentar selecionar na tabela qrcode")

                        query = ("SELECT * FROM qrcode")  # Seleciona a tabela qrcode
                        cursor.execute(query)

                        encontrou = 0
                
                    for i in cursor:

                        if encontrou == 0:
                               
                            ID_recebido = str(i[0]) # Seleciona o primeiro item da lista recebida do banco (ID)
                                                            
                            if (ID_recebido == ID): # Compara se o ID vindo do request e igual ao do banco   

                                log("Achou o id no banco...")
                                encontrou = 1                            

                    if encontrou == 0:

                        log("id inexistente")

                    if encontrou == 1:
                                
                        try:                            
                        
                            query = ("DELETE FROM qrcode WHERE ID = %s")%ID
                            cursor.execute(query)
                            cnx.commit()                               
                            
                        except Exception as err:  # mysql.connector.Error as err:

                            txt = ("Id inexistente",ID,err)
                            log(txt)
                            
                            cnx.close()                            

                        else:

                            txt = ("ID",ID,"deletado do banco")
                            log(txt)
                            
                            break

                    break
                    
                if comando == "cadastrar_qr":

                    try:
                       
                        dados = data.replace("cadastrar_qr&","")
                        dados = dados.replace("'",'"')

                    except Exception as err:

                        txt =("Erro ao formatar os dados para converter em json", err)
                        log(txt)

                
            #########  Faz o cadastro dos dados recebidos no banco do CMM #######

                    try:

                        try:
                            
                            dados_json = json.loads(dados)  # Tranforma a string para formato json (dicionario)

                        except:

                            dados.update({'nome':'Nome com emoticons'})                            
                            print(dados)
                            dados_json = json.loads(dados)
                            
                           
                        ID = str(dados_json["ID"])
                        
                        nome = (dados_json["nome"])
                        nome = nome.encode('utf-8')
                        
                        ap = str(dados_json["apartamento"])
                        bloco = str(dados_json["bloco"])
                        cond = str(dados_json["condominio"])
                        di = str(dados_json["data_inicio"])
                        df = str(dados_json["data_final"])
                        hi = str(dados_json["hora_inicio"])
                        hf = str(dados_json["hora_final"])
                        ds = str(dados_json["dias_semana"])

                        l = open("/var/www/html/log_qrcode.txt","a") # Pula uma linha no registro de log
                        l.write("\n")
                        l.close()

                        nome_editado = (dados_json["nome"])
                        nome_editado = str(nome_editado)
                        nome_editado = nome_editado.replace("b","")
                        
                        txt =("Cadastrar:",nome_editado,"Condominio",cond,"Apartamento",ap,"bloco",bloco,"Inicio em",di,"até",df,"das",hi,"até as",hf)
                        txt = str(txt)
                        txt = txt.replace("'","")
                        txt = txt.replace(",","")
                        txt = txt.replace("(","")
                        txt = txt.replace(")","")
                        log(txt)

                    except Exception as err:

                        txt =("Erro na conversao json",err)
                        log(txt)
                                       
                    try:                 
  
                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()
                      
                    except mysql.connector.Error as err:
                        
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                          
                            log("Alguma coisa esta errada com o nome de usuario ou a senha!")
                        
                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                          
                            log("Esta base de dados nao existe")
                        
                        else:
                          
                            log(err)
                    try:                        
                    
                        query = ("INSERT INTO qrcode (ID, nome, apartamento, bloco, cond, hora_inicio, hora_final, data_inicio, data_final, dias_semana) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                        query_data = (ID,nome,ap,bloco,cond,hi,hf,di,df,ds)
                        cursor.execute(query, query_data)
                        cnx.commit()
                        
                    except mysql.connector.Error as err:

                        if err.errno == 1062:

                            log("ID duplicado")

                            cnx.close()
                            break                            
                            
                        else:

                            txt = ("Erro na inclusão do banco",err)
                            log(txt)
                            
                    else:

                        txt = ("Cadastrado com sucesso ID",ID)
                        txt = str(txt)
                        txt = txt.replace("'","")
                        txt = txt.replace(",","")
                        txt = txt.replace("(","")
                        txt = txt.replace(")","")
                        log(txt)

                        cnx.close()
                        break                
                 
        s = setupServer()

        while True:
          
##          txt = ("Escutando Gerenciador na porta",port_gerenciador)
          txt = ("Aguardando novos cadastros de QRCODE...")
          txt = str(txt)
          txt = txt.replace("'","")
          txt = txt.replace(",","")
          txt = txt.replace("(","")
          txt = txt.replace(")","")
          log(txt)
          
                    
          try:

              conn = setupConnection()
              dataTransfer(conn)                                         
                
          except:
            
              log("Encerrou conexão com Gerenciador")

        

####################  Declara as threads dos programas disponiveis  ####################

servidor = threading.Thread(target=Servidor_qr)

######################################### Start dos Programas  #############################################################

servidor.start() 

time.sleep(0.2) # Tempo para colocar as linhas impressas após as linhas de inicio de programa

#########################################   INSTRUCOES   ################################################

##rele_qr.pulsa() # Pusa por 2 segundos o rele do QR Code
##rele_qr.liga()
##rele_qr.desliga()

##narrador.falar("Teste do narrador") # fala o texto enviado - depende de internet
##narrador.gravar("Qrcode não cadastrado","semCadastro") # Grava o texto enviado em nome.mp3

##rele.liga(1)    # Liga rele 1 (podendo ser de 1 a 8)
##rele.desliga(1)  # Desliga rele 1 (podendo ser de 1 a 8)
##rele.pulsa(8,2)  # rele.pulso(rele,tempo)  Pulsa o rele pelo tempo indicado em segundos

##os.system("mpg123 nome.mp3") # Reproduz um arquivo mp3 , necessario instalar mpg123 (sudo apt-get install mpg123)

##log ("\nTemperatura",temperatura.cpu(),"°C\n")  # obter temperatura

##email.enviar("O Programa acabou de reiniciar\nPosso enviar qualquer mensagem aqui...") # Não usar nenhum caracter especial na mensagem

##tempo = clima.clima_atual()
##log(tempo)

##evento.enviar_contact_id('E','132','001') # Evento ou Restauração / Evento / Setor

###################################################################################################

txt = ("Temperatura do processador " + str(temperatura.cpu()) + "°C")  # obter temperatura
log(txt)



