#!/usr/bin/env python3
# coding=UTF-8

# CMM Oficial com placa de expansão da BRAVAS Technololgy
# Desenvolvido por Leandro Leal  rev. 26/09/2019

import RPi.GPIO as GPIO
import time
import biblioteca_CMM as cmm

from datetime import datetime, timedelta
import wiringpi # Biblioteca para usar as GPIO da rasp como saidas ou entradas
import os     # Executa comandos do sistema operacional Ex.: os.system('sudo reboot now'))
import threading # Modulo superior Para executar as threads
import sys
import socket
import _thread as thread
import json
import mysql.connector

socket.setdefaulttimeout(2) # limite de 2 segundos para enviar o socket


def log(texto): # Metodo para registro dos eventos no log.txt (exibido na interface grafica)

    hs = time.strftime("%H:%M:%S") 
    data = time.strftime('%d/%m/%y')

    texto = str(texto)

    if texto == "*":

        l = open("/var/www/html/log/log.txt","a")
        l.write("\n")
        l.close()

    else:        

        texto = texto.replace("'","")
        texto = texto.replace(",","")
        texto = texto.replace("(","")
        texto = texto.replace(")","")

        escrita = ("{} - {}  Evento:  {}\n").format(data, hs, texto)
        escrita = str(escrita)

        l = open("/var/www/html/log/log.txt","a")
        l.write(escrita)
        l.close()
        
# Imprimi o nome e o IP do equipamento no log da interface

nome = os.popen('hostname').readline()
nome = str(nome)
nome = nome.replace("\n","")
ip = os.popen('hostname -I').readline()
ip = str(ip)
ip = ip.replace("\n","")
txt = ("Nome desta maquina",nome) #,"com IP",ip)
txt = str(txt)
log(txt)
log("*") # pula uma linha no log
log("*") # Deixa uma linha em branco no log da interface

log("Reiniciou o sistema")

os.system("mpg123 /home/pi/CMM/mp3/sistema_carregado.mp3") 




############################ INICIA AS CLASSES DA biblioteca_CMM ###############################################

rele = cmm.Rele() # inicia a classe rele com port A em 0
narrador = cmm.Narrador()
temperatura = cmm.Temperatura()
email = cmm.Email()
clima = cmm.Clima()
entradas = cmm.Entradas() # Classe para leitura das entradas digitais do CMM
saidas = cmm.Saidas()  # Classe para acionamento dos reles e saidas transistorizadas do CMM
evento = cmm.Evento("6639") # Inicia a classe evento com o codigo do cliente
banco = cmm.Banco() # Oprerações CRUD no banco CMM

##qr1 = cmm.Qrcode("172.18.36.245","6639",1,"social","1","1","acesso_qr.mp3") # IP,Cliente,rele,portao,notifica,leitor,mensagem) - "172.18.34.247","5987",4,"social" ou "eclusa" 172.18.36.245","6639
##qr2 = cmm.Qrcode("172.18.36.243","6639",1,"social","1","2","acesso_qr.mp3") # IP,Cliente,rele,portao,notifica,leitor,mensagem) - "172.18.34.247","5987",4,"social" ou "eclusa" 172.18.36.243
##qr3 = cmm.Qrcode("172.18.36.247","6639",3,"eclusa","0","3","acesso_qr.mp3") # IP,Cliente,rele,portao,notifica,leitor,mensagem) - "172.18.34.247","5987",4,"social" ou "eclusa"
##qr4 = cmm.Qrcode("172.18.36.248","6639",3,"eclusa","0","4","acesso_qr.mp3") # IP,Cliente,rele,portao,notifica,leitor,mensagem) - "172.18.34.247","5987",4,"social" ou "eclusa" 172.18.36.248

# 172.20.9.5 IP qrcode bancada 172.18.36.247

############################## Intertravamento dos portões sociais #############################################

def Servidor_qr(): ######### Thread servidor Cadastro QR Code ###################

    time.sleep(1)

    deletar = 0
    cadastrar = 0

    host_servidor = '172.18.36.252'  # Host servidor 
    port_gerenciador = 5511# porta para receber dados do gerenciador
    

    print("Ouvindo Gerenciador na porta",port_gerenciador)
    
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

                    txt = ("Dados recebidos estao fora do formato",err)
                    log(txt)                    
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
                      
                    except Exception as err:
                        
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
                
                  #  Faz o cadastro dos dados recebidos no banco do CMM #

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

                        log("*")
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
                      
                    except Exception as err:
                        
                        log(err)
                        
                    try:                        
                    
                        query = ("INSERT INTO qrcode (ID, nome, apartamento, bloco, cond, hora_inicio, hora_final, data_inicio, data_final, dias_semana) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                        query_data = (ID,nome,ap,bloco,cond,hi,hf,di,df,ds)
                        cursor.execute(query, query_data)
                        cnx.commit()
                        
                    except Exception as err:

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
                        log("*")

                        cnx.close()
                        break                
                 
        s = setupServer()

        while True:          

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

##def thread_qrcode1(): # Programa do QR Code 1
##
##    log("Programa QR Code social entrada em execução")
##
##    qr1.start() # Inicia o qr code do portão social    
##
##def thread_qrcode2(): # Programa do QR Code 2
##
##    log("Programa QR Code social saida em execução")
##
##    qr2.start() # Inicia o qrcode do portão da eclusa
##    
##def thread_qrcode3(): # Programa do QR Code 3
##
##    log("Programa QR Code eclusa entrada em execução")
##
##    qr3.start() # Inicia o qrcode do portão da eclusa
##
##def thread_qrcode4(): # Programa do QR Code 4
##
##    log("Programa QR Code eclusa saida em execução")
##
##    qr4.start() # Inicia o qrcode do portão da eclusa


def Intertravamento(comando): # Inicia a thread dos portoes sociais importando a classe Rele
        
        entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        
        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
        
        audio = 0 # Deixa ativo ass mensagens de audio de abertura
        cont = 0

        a = open("/home/pi/CMM/status_social.cmm","r")
        abre_social = a.read()
        a.close()

        b = open("/home/pi/CMM/status_eclusa.cmm","r")
        abre_eclusa = b.read()
        b.close()        

    
        if comando == "abre_social":

            entradas = cmm.Entradas()
            pm1 = entradas.pm1
                                
            if pm1 == 1: # O portão social já esta aberto

                log("O portão social já esta aberto")
                            
                os.system("mpg123 /home/pi/CMM/mp3/social_aberto.mp3")
                time.sleep(1)

            else: # Se o portão Social esta fechado então pode abrir

                entradas = cmm.Entradas()
                pm2 = entradas.pm2
                                
                if pm2 == 0: # Se Ponto magnético Eclusa fechado
                    
##                    s = open("/home/pi/CMM/status_social.cmm","w")
##                    s.write("1")
##                    s.close()

                    rele.liga(5) # Aqui abrimos o contato da eclusa para impedir que ela seja aberta enquanto o social esta aberto
                    
                    log("*")
                    txt = ("Abrindo portão Social")
                    log(txt)
                    abre.social()

                    if audio == 1: # Ativa as mensagens de abertura e fechamento

                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_social.mp3")                   
                    
                    time.sleep(1) # Tempo minimo para o portão abrir

                    entradas = cmm.Entradas()
                    pm1 = entradas.pm1
                                        
##                    if pm1 == 0: # Portão fechado pois não abriu com o comando
##
##                        log("Portão Social emperrado")

##                        os.system("mpg123 /home/pi/CMM/mp3/social_emperrado.mp3")
##                                                
##                        rele.desliga(5) # Fecha o contato e libera a eclusa para ser acionada
##
##                        evento.enviar("E","132","008") # Envia portão emperrado                        

                    if pm1 == 1: # Portão abriu

                        evento.enviar("E","133","001") # Envia abriu portão
                        
                        contador = 200 # Tempo maximo para o social ficar aberto 300 = 30 segundos
                        log("Esperando portão social fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = cmm.Entradas()
                            pm1 = entradas.pm1
                            
                            # Esperando o portão social fechar...
                            
                            if pm1 == 0: # portão fechou

                                log("Portão social fechou")
                                
                                evento.enviar("R","133","001") # Envia fechamento
                                
                                contador = 1
                                                            
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(5) # Fecha o contato e libera a eclusa para ser acionada

                                break

                            if (pm1 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                log("Portão social aberto por muito tempo")
                                
                                evento.enviar("E","132","010") # Envia falha no fechamento social

                                os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                                
##                                status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
##                                status.write("1")
##                                status.close()

                                contador = 0

                                rele.desliga(5) # Fecha o contato e libera a eclusa para ser acionada
                                
                            entradas = cmm.Entradas()    
                            ctw2 = entradas.ctw2
                            btn2 = entradas.qde
                            
                            if (ctw2 == 0 or btn2 == 0):# and pm1 == 1): # Entrada para abrir o portão da eclusa
                                log("Agurade o fechamento do social")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Necessario manter esse audio sempre ativo
                                time.sleep(1)
                                
                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1
                            
                entradas = cmm.Entradas()
                pm2 = entradas.pm2
  
                        
        if comando == "abre_eclusa":

            entradas = cmm.Entradas()
            pm2 = entradas.pm2            

            if pm2 == 1: # O portão Eclusa já esta aberto

                log("O portão Eclusa já esta aberto")

                os.system("mpg123 /home/pi/CMM/mp3/eclusa_aberto.mp3")
                time.sleep(1)

            else: # Se o portão Eclusa esta fechado então pode abrir

                entradas = cmm.Entradas()
                pm2 = entradas.pm2
                pm1 = entradas.pm1

                if pm1 == 0: # Ponto magnético Social fechado, pode abrir a eclusa
                    
##                    s = open("/home/pi/CMM/status_eclusa.cmm","w")
##                    s.write("1")
##                    s.close()

                    rele.liga(6) # Impede o social de abrir enquanto a eclusa esta aberta

                    log("*")                    
                    txt = ("Abrindo portão Eclusa")
                    log(txt)
                    abre.eclusa()
                                        

                    if audio == 1:
                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_eclusa.mp3")
                    
                    time.sleep(1) # Tempo de espera para o portão abrir

                    entradas = cmm.Entradas()
                    pm2 = entradas.pm2
                    
##                    if pm2 == 0: # Portão fechado não abriu após o comando
##
##                       log("Portão eclusa emperrado")
##                       
##                       os.system("mpg123 /home/pi/CMM/mp3/eclusa_emperrado.mp3")
##                            
##                       rele.desliga(6) # Libera o social para abrir mesmo com a eclusa aberta
##
##                       evento.enviar("E","132","009") # Envia portão emperrado

                    if pm2 == 1: # Portão aberto

                        evento.enviar("E","133","003") # Envia abertura
                        
                        contador = 200 # Tempo maximo para eclusa ficar aberta 30 segundos
                        log("Esperando portão Eclusa fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = cmm.Entradas()
                            pm2 = entradas.pm2
                            
                            # Esperando o portão eclusa fechar...

                            if pm2 == 0: # portão fechou

                                log("Portão Eclusa fechou")
                                
                                evento.enviar("R","133","003") # Envia fechamento
                                
                                contador = 1
                                
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(6) # Libera o social para abrir

                                break

                            if (pm2 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                log("Portão Eclusa aberto por muito tempo")
                                
                                evento.enviar("E","132","011") # Envia falha no fechamento
                                
                                os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                                
                                status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
                                status.write("1")
                                status.close()                                

                                rele.desliga(6) # Libera o social para abrir mesmo com a eclusa aberta

                                contador = 0

                            entradas = cmm.Entradas()
                            ctw1 = entradas.ctw1
                            

                            if ctw1 == 0 : # Alguem esta tentando abrir o social com a eclusa aberta

                                log("Aguarde o fechamento do portão")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Manter esse audio sempre ativo
                                time.sleep(1)
                                

                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1


def Portoes_sociais(Rele): # Programa
    
    log("Programa Sociais em execução ")

    saida = 0
    banco = cmm.Banco()

    entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        
    pm1 = entradas.pm1
    pm2 = entradas.pm2

    print("pm1 =",pm1)
    print("pm2 =", pm2)

    qbv = wiringpi.digitalRead(306) # leitura direta IN7     
        
    ctw1 = entradas.ctw1
    ctw2 = entradas.ctw2

    ar1 = 0
    ar2 = 0
    reset_ar1 = 0
    reset_ar2 = 0
    

    quebra = 0
           
    while(1):

        habilita_intertravamento = banco.consulta("intertravamento","habilitado")

        entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        
        pm1 = entradas.pm1
        pm2 = entradas.pm2

        qbv = wiringpi.digitalRead(306) # leitura direta IN7        
        
        ctw1 = entradas.ctw1
        ctw2 = entradas.ctw2

        ihm_soc1 = banco.consulta("comandos","abre_social_externo")
        ihm_soc2 = banco.consulta("comandos","abre_social_interno")        

        a = open("/home/pi/CMM/status_social.cmm","r")
        abre_social = a.read()
        a.close()

        b = open("/home/pi/CMM/status_eclusa.cmm","r")
        abre_eclusa = b.read()
        b.close()

        if ar1 == 1 and reset_ar1 == 1:

            time.sleep(1)           

            evento.enviar("R","132","002")

            ar1 = 0
            reset_ar1 = 0

            rele.desliga(8)

        if ar2 == 1 and reset_ar2 == 1:

            time.sleep(1)           

            evento.enviar("R","132","004")

            ar2 = 0
            reset_ar2 = 0
            
            rele.desliga(8)
                
        if abre_social == "0" and pm1 == 1 and ar1 == 0:

            time.sleep(0.2) # Filtra algum possivel ruido de até 500 milissegundos

            a = open("/home/pi/CMM/status_social.cmm","r")
            abre_social = a.read()
            a.close()

            pm1 = entradas.pm1

            if abre_social == "0" and pm1 == 1: # Se realmente foi um arrombamento liga sirene e notifica o Moni

                log("Confirmado Arrombamento do portão social")
                os.system("mpg123 /home/pi/CMM/mp3/violacao_social.mp3")
                
                rele.liga(8)
                
                evento.enviar("E","132","002")
                
                ar1 = 1
                reset_ar1 = 1                 

        if abre_eclusa == "0" and pm2 == 1 and ar2 == 0:

            time.sleep(0.2) # Filtra algum possivel ruido de até 200 milissegundos

            b = open("/home/pi/CMM/status_eclusa.cmm","r")
            abre_eclusa = b.read()
            b.close()

            pm2 = entradas.pm2

            if abre_eclusa == "0" and pm2 == 1: # Se realmente foi um arrombamento liga sirene e notifica o Moni

                log("Confirmado Arrombamento do portão Eclusa")
                os.system("mpg123 /home/pi/CMM/mp3/violacao_eclusa.mp3")
                rele.liga(8)
                evento.enviar("E","132","004")
                
                ar2 = 1
                reset_ar2 = 1        
       
        if ctw1 == 0 or ihm_soc1 == "1":

            if quebra == 1:

                log("Os portes ainda estão abertos pelo quebra de vidro")
                os.system("mpg123 /home/pi/CMM/mp3/quebra_esta_acionado.mp3")

            else:

                banco.atualiza("comandos","abre_social_externo","0")

                if habilita_intertravamento == "0":

                    log("Intertravamento desabilitado\n")

                    abre = Abre()
                    abre.social()

                else:

                    log("Intertravamento habilitado\n")

                    status = open("/home/pi/CMM/status_social.cmm","w")
                    status.write("1")
                    status.close()
             
                    Intertravamento("abre_social")

                    status = open("/home/pi/CMM/status_social.cmm","w")
                    status.write("0")
                    status.close()

            
        if ctw2 == 0 or ihm_soc2 == "1":

            if quebra == 1:

                log("Os portes ainda estão abertos pelo quebra de vidro")
                os.system("mpg123 /home/pi/CMM/mp3/quebra_esta_acionado.mp3")

            else:

                banco.atualiza("comandos","abre_social_interno","0")

                if habilita_intertravamento == "0":

                    log("Intertravamento desabilitado\n")

                    abre = Abre()
                    abre.eclusa()
                    
                    # bem_vindo
                    
                else:
                    
                    status = open("/home/pi/CMM/status_eclusa.cmm","w")
                    status.write("1")
                    status.close()

                    Intertravamento("abre_eclusa")

                    status = open("/home/pi/CMM/status_eclusa.cmm","w")
                    status.write("0")
                    status.close()

                    saida = 1
                
        if qbv == 0 and quebra == 0:

            log("Quebra de vidro acionado")            
                            
            status = open("/home/pi/CMM/status_eclusa.cmm","w")
            status.write("1")
            status.close()            

            status = open("/home/pi/CMM/status_social.cmm","w")
            status.write("1")
            status.close()

            os.system("mpg123 /home/pi/CMM/mp3/chave_emergencia.mp3")

            
            rele.liga(1)
            rele.liga(3)

            evento.enviar("E","132","005")

            quebra = 1


        if qbv == 1 and quebra == 1:            

            status = open("/home/pi/CMM/status_eclusa.cmm","w")
            status.write("1")
            status.close()            

            status = open("/home/pi/CMM/status_social.cmm","w")
            status.write("1")
            status.close()

            os.system("mpg123 /home/pi/CMM/mp3/restaurada_emergencia.mp3")

            log("Quebra de vidro restaurado")

            rele.desliga(1)
            rele.desliga(3)

            evento.enviar("R","132","005")

            quebra = 0

                        
        time.sleep(0.1)        
                                

class Abre(cmm.Rele): # classe abertura dos portoes registrando no arquivo de controle status_social / status_eclusa

    def social(self):

        status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
        status.write("1")
        status.close()

        rele.pulso(1,3) # Pulso para abrir direto o portão sem intertravamento (Social)
##        log("Abrindo social...")
        
    def eclusa(self):

        status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
        status.write("1")
        status.close()        
    
        rele.pulso(3,3) # Pulso para abrir direto o portão sem intertravamento (Eclusa)
##        log("Abrindo eclusa...")
        
########################################## Métodos de acesso a classe leitor #####################################

def leitor(entrada):

    l = cmm.Leitor()

    if  entrada == ("leitor1_in1"):

        i = l.leitor1_in1()
        return(i)

    if  entrada == ("leitor1_in2"):

        i = l.leitor1_in2()
        return(i)

    if  entrada == ("leitor1_in3"):

        i = l.leitor1_in3()
        return(i)

    if  entrada == ("leitor1_in4"):

        i = l.leitor1_in4()
        return(i)

    if  entrada == ("leitor7_in1"):

        i = l.leitor7_in1()
        return(i)

    if  entrada == ("leitor7_in2"):

        i = l.leitor7_in2()
        return(i)

    if  entrada == ("leitor7_in3"):

        i = l.leitor7_in3()
        return(i)

    if  entrada == ("leitor7_in4"):

        i = l.leitor7_in4()
        return(i)    

################################################ THREADS ROTINAS #################################################


def Garagem1(Rele): # Inicia a thread do portão da garagem importando a classe Rele

    log("Programa Garagem Terreo em execução ")
    
    s = cmm.Expansor()
    
    s.desliga_rele4_exp1() # Garante que a sirene esteja desligada
    s.desliga_rele3_exp1() # Garante que sinaleira esteja com sinal vermelho (NF)
    s.desliga_rele2_exp1() # Garante que o Foto esteja desligado
    s.desliga_rele1_exp1() # Garante que o Abre esteja desligado   

    banco = cmm.Banco()
    em_mudanca = 0
    aberto = 0
            
    while(1):

        hs = time.strftime("%H:%M:%S")
        s = cmm.Expansor()
    
        ihm_gar1 = banco.consulta("comandos","abre_garagem") # Valor inserido pelo botão da interface       
        tx1 =  leitor("leitor1_in3")  # Cantato abre vindo do TX (LINEAR HCS)

        pmg1 = leitor("leitor1_in1")
        
        mudanca = banco.consulta("comandos","mudanca")

        status = open("/home/pi/CMM/status_garagem_1.cmm","r") 
        status_garagem = status.read()
        status.close()
        
        if mudanca == "1" and em_mudanca == 0:

            log("*")
            log("Chave de mudança acionada")

            s.liga_rele3_exp1() # Sinal Verde

            evento.enviar("E","132","025") 

            s.liga_rele1_exp1() # Aciona o rele 1 do modulo 1 (Abre)
            time.sleep(2)
            s.desliga_rele1_exp1()
            time.sleep(1)
            s.liga_rele2_exp1() # Aciona o rele 2 do modulo 1 (Foto)
            
            em_mudanca = 1

        if mudanca == "0" and em_mudanca == 1:
            
            log("Chave de mudança desligada")

            s.desliga_rele3_exp1() # Sinal Vermelho
            evento.enviar("R","132","025")
                            
            s.desliga_rele1_exp1() # Desliga o rele 1 do modulo 1 (Abre)
            s.desliga_rele2_exp1() # Desliga o rele 2 do modulo 1 (Foto) 

            pmg1 = leitor("leitor1_in1")

            cont = 30 # Tempo maximo de espera

            log("Aguardando Garagem fechar após a mudança...")

            while cont > 0:

                pmg1 = leitor("leitor1_in1")

                if(cont == 1): # 30 segundos e não fechou                                      

                    log("Obstruçao do fechamento do portao, enviar evento aqui")
                        
                if (pmg1 == 1): # Portão ja fechou

                    log("Portão fechou")

                    s.desliga_rele3_exp1() # Sinal Vermelho

                    t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                    t.write("0")
                    t.close()
                    
                    cont = 0
                    mudanca1 = 0
                    time.sleep(1)
                    
                time.sleep(1)
                cont = cont - 1

            em_mudanca = 0
            
        if (tx1 == 1 or ihm_gar1 == "1" and em_mudanca == 0):    # Se o tx ou o botão da interface mandou abrir o portão

            status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
            status.write("1")
            status.close()

            time.sleep(0.1)

            tx1 =  leitor("leitor1_in3")
            ihm_gar1 = banco.consulta("comandos","abre_garagem")

            if (tx1 == 1 or ihm_gar1 == "1"): # O tx da linear está direto no abre do portão

                time.sleep(0.1)
                tx1 =  leitor("leitor1_in3")

                if tx1 == 1:

                    log("*")
                    log("Reconheceu tx Garagem") # Se reconheceu o tx, é porque o portão ja esta abrindo

                    s.liga_rele3_exp1() # Sinal Verde (Sinaleira)    

                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                    status.write("1")
                    status.close()

                if ihm_gar1 == "1": # Abre através do expansor (rele 1)

                    log("Reconheceu abre Garagem Interface pela gráfica")

                    s.liga_rele3_exp1() # Sinal Verde (Sinaleira)

                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                    status.write("1")
                    status.close()

                    s.liga_rele1_exp1()
                    time.sleep(2)
                    s.desliga_rele1_exp1()
                    

                banco.atualiza("comandos","abre_garagem","0")                

                time.sleep(3) # Tempo para começar a abrir o portão

                pmg1 = leitor("leitor1_in1")

                cont = 300     # Tempo maximo para deixar o portão aberto (300 = 30 segundos)
                
                if pmg1 == 1: # Portão não abriu apos o comando

                    time.sleep(0.1)
                    pmg1 = leitor("leitor1_in1")

                    if pmg1 == 1: # Portão não abriu apos o comando

                        log("Portão garagem não abriu")

                        s.desliga_rele3_exp1() # Sinal Vermelho
                        
                        evento.enviar("E","132","015") # Emperrado
                        
                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                        status.write("0")
                        status.close()
                                            
                        cont = 0

                if pmg1 == 0: # Portão abriu

                    time.sleep(0.1)                    
                    pmg1 = leitor("leitor1_in1")

                    if pmg1 == 0: # Confirmado que o Portão abriu

                        evento.enviar("E","133","013")

                        while cont > 0:   # Enquanto o portão esta aberto verifica

                            if cont == 300:

                                log("Portão Garagem abriu")
                            
                            pmg1 = leitor("leitor1_in1")
                            
                            if pmg1 == 1: # Se o portão ja fechou

                                log("Portão Garagem fechou")

                                s.desliga_rele3_exp1() # Sinal Vermelho

                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                status.write("0")
                                status.close()
                                
                                evento.enviar("R","133","013") # Envia o evento de fechamento para a central

                                time.sleep(1)

                                aberto = 0
                                
                                cont = 0
                                break
                                
                            if pmg1 == 0:     # Se o portão ainda esta aberto

                                bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1

                                if bar1 == 1: # Se acionou a barreira de entrada

                                    log("Acionou a barreira Garagem")

                                    tempo = 30

                                    while tempo > 0: # Enquanto a barreira esta acionada

                                        bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1

##                                        print("Alguem esta na frente da barreira")                                        


                                        if bar1 == 1:

                                            time.sleep(0.1)

##                                            print("Esperando sair da barreira...")

                                        if bar1 == 0:

                                            time.sleep(0.1)

##                                            print("Saiu da barreira")
                                            break

                                        tempo = tempo - 1
                                        time.sleep(1)
                                        
##                                        print("Passou alguem, verificando dupla passagem...")

                                    s.desliga_rele3_exp1() # Sinal Vermelho
                                    
                                    pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico
                                    
                                    if pmg1 == 0: # Portão ainda aberto

                                        pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico

                                        log("Aguardando portão Garagem fechar")

                                        temp = 30

                                        while temp > 0:  # Enquanto o portão ainda está aberto e tempo menor que 30 seg                         

                                            aberto = 1
                                            
                                            pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico
                                            bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1
                                            tx1 =  leitor("leitor1_in3")  # Cantato abre vindo do TX (LINEAR HCS)  

                                            if bar1 == 1: # Dupla passagem

                                                time.sleep(0.2)
                                                bar1 = leitor("leitor1_in2")

                                                if bar1 == 1:

                                                    log("Dupla passagem Garagem")                                                

                                                    evento.enviar("E","132","016")

                                                    s.liga_rele4_exp1() # Sirene                                            
                                                    time.sleep(10)
                                                    s.desliga_rele4_exp1()                                            

                                                    break

                                            if tx1 == 1: # Alguem acionou o controle enquanto o portão fechava

                                                time.sleep(0.1)
                                                tx1 =  leitor("leitor1_in3")

                                                if tx1 == 1:

                                                    log("Reconheceu abre Garagem enquanto o portão estava aberto")                                                    
                                                    s.liga_rele3_exp1() # Sinal Verde
                                                    temp = 0
                                                    
                                                    break # Sai da função e inicia novamente a verificação
##                                            
                                     
                                            if pmg1 == 1: # portão ja fechou

                                                time.sleep(0.1)
                                                pmg1 = leitor("leitor1_in1")

                                                if pmg1 == 1:

                                                    log("Portão Garagem fechou")

                                                    aberto = 0
                                                    
                                                    s.desliga_rele3_exp1() # Sinal vermelho
                                                    break

                                            temp = temp - 1
                                            time.sleep(0.2)

                                        if aberto == 1:

                                            print("Portão aberto por muito tempo")

                            cont = cont - 1
                            time.sleep(0.1)

                    if cont == 1: # Passaram se 29 segundos e o portão não fechou

                        log("Portão Garagem aberto muito tempo")

                        s.desliga_rele3_exp1() # Sinal Vermelho

                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                        status.write("0")
                        status.close()

                        evento.enviar("E","132","026") # Envia evento de portão aberto (obstrução do fechamento)
                        
                        cont = 0
                        break
                    
            status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
            status.write("0")
            status.close()
            
        if pmg1 == 0 and tx1 == 0 and ihm_gar1 == "0" and em_mudanca == 0 and status_garagem == "0":

            time.sleep(0.1)

            status = open("/home/pi/CMM/status_garagem_1.cmm","r") 
            status_garagem = status.read()
            status.close()
            
            pmg1 = leitor("leitor1_in1")
            
            
            if pmg1 == 0 and status_garagem == "0":

                cont = 10            

                while cont > 0:
                
                    pmg1 = leitor("leitor1_in1")

                    if pmg1 == 0:

                        violacao = 1
                        
                    if pmg1 == 1:
                        
                        violacao = 0                    
                        cont = 1

                    time.sleep(0.1)
                    cont = cont - 1            
                
                if violacao == 1:

                    status = open("/home/pi/CMM/status_garagem_1.cmm","r") 
                    status_garagem = status.read()
                    status.close()
                    
                    pmg1 = leitor("leitor1_in1")
                    ihm_gar1 = banco.consulta("comandos","abre_garagem")
                    tx1 =  leitor("leitor1_in3")

                    if (tx1 == 1 or ihm_gar1 == "1"):

                        pass
                    
                    if pmg1 == 0 and status_garagem == "0":
                        
                        print("violação confirmada do portão garagem 1")
                    
        time.sleep(0.1)
        
        
def Arrombamento(Rele): # Inicia a thread arrombamento de portões
    
    log("Programa arrombamento de portões em execução")

    ar1 = 0 # Variavel arrombamento portão 1
    ar2 = 0
    
    reset_ar1 = 0 # Reseta a variavel do portão para 0
    reset_ar2 = 0
    
    cont1 = 30 # Contador individual para cada reset de arrombamento
    cont2 = 30
        
    while(1):

        entradas = cmm.Entradas()

        pm1 = entradas.pm1
        pm2 = entradas.pm2

        a = open("/home/pi/CMM/status_social.cmm","r")
        abre_social = a.read()
        a.close()

        b = open("/home/pi/CMM/status_eclusa.cmm","r")
        abre_eclusa = b.read()
        b.close()  
                
        if abre_social == "0" and pm1 == 1 and ar1 == 0:

            time.sleep(0.5) # Filtra algum possivel ruido de até 500 milissegundos

            if pm1 == 1: # Se realmente foi um arrombamento liga sirene e notifica o Moni

                log("Arrombamento do portão social")
                os.system("mpg123 /home/pi/CMM/mp3/violacao_social.mp3")
                
                rele.liga(8)
                
                evento.enviar("E","132","002")
                
                ar1 = 1
                reset_ar1 = 1

        if ar1 == 1 and reset_ar1 == 1:

            cont1 = cont1 - 1 # A primeira vez que acontece o arrombamento reseta depois de 30 segundos
            time.sleep(1)

            if cont1 <= 0:

                evento.enviar("R","132","002")

                cont1 = 350 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 5 min
                ar1 = 0
                reset_ar1 = 0
                rele.desliga(8)

                

        if abre_eclusa == "0" and pm2 == 1 and ar2 == 0:

            time.sleep(0.5) # Filtra algum possivel ruido de até 500 milissegundos

            if pm2 == 1: # Se realmente foi um arrombamento liga sirene e notifica o Moni

                log("Arrombamento do portão Eclusa")
                os.system("mpg123 /home/pi/CMM/mp3/violacao_eclusa.mp3")
                rele.liga(8)
                evento.enviar("E","132","004")
                
                ar2 = 1
                reset_ar2 = 1

        if ar2 == 1 and reset_ar2 == 1:

            cont2 = cont2 - 1 # A primeira vez que acontece o arrombamento reseta depois de 30 segundos
            time.sleep(1)

            if cont2 <= 0:

                evento.enviar("R","132","004")

                cont2 = 350 # Se apos o reset o portão continuar aberto envia o evento novamente e espera 5 min
                ar2 = 0
                reset_ar2 = 0
                rele.desliga(8)

        
        time.sleep(2)   

def Servidor(Rele,Abre): 
    
    log("Programa Servidor em execução")
    socket.setdefaulttimeout(9999) # limite tempo socket
    
    host = '0.0.0.0'
    port = 5510

    time.sleep(0.1)

    log("iniciou o servidor")
    
    txt = ("Servidor: ",host, " porta: ", port)
    log(txt)

    while(1):

        
    ############################################### Thread servidor p/ PHP e MONI #################################################################

            socket.setdefaulttimeout(9999)


            def setupServer():
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
                
                try:
                    s.bind((host, port))
                except socket.error as msg:
                    log (msg)
                
                return s

            def setupConnection():
                s.listen(5)
                conn, address = s.accept()
                txt = ("Conectado com: " + address[0] + ":" + str(address[1]))
                log(txt)
                return conn


            def dataTransfer(conn):  # Loop de transferencia e recepção de dados

                log("Entrou no data transfer")

                while True:
                    
                    rele = Rele()
                                                          
                    data = conn.recv(1024)  # Recebe o dado
                    data = data.decode('utf-8')
                    txt = ("data",data)
                    log(txt)
                    dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                    command = dataMessage[0]

                    txt = ("command",command)
                    log(txt)

                    (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e eoutra em resto

                    txt = ("comando e resto",comando,resto)
                    log(txt)
                   
                    if(comando == "SET1"):

                        log("Abrindo portão Social pelo Moni")

                        status = open("/home/pi/CMM/status_social.cmm","w") 
                        status.write("1")
                        status.close()
                        
                        rele.liga(1)

                        time.sleep(2)

                        rele.desliga(1)

                        time.sleep(15)

                        status = open("/home/pi/CMM/status_social.cmm","w") # Volta o arquivo para zero para ativar a verificação de arrombamento
                        status.write("0")
                        status.close()

                        conn.close()                        
                                            

                    elif(comando == "SET2"):
                        
                        log("Abrindo portão Eclusa pelo Moni")

                        status = open("/home/pi/CMM/status_eclusa.cmm","w") 
                        status.write("1")
                        status.close()
                        
                        rele.liga(2)

                        time.sleep(2)

                        rele.desliga(2)

                        time.sleep(15)

                        status = open("/home/pi/CMM/status_eclusa.cmm","w") # Volta o arquivo para zero para ativar a verificação de arrombamento
                        status.write("0")
                        status.close()
                        
                        conn.close()
                        
                       
                    elif(comando == "SET3"):
                        
                        log("reconheceu SET 3")                        
    
                        conn.close()                       

                    elif(comando == "SET4"):
                        log("Abrindo garagem")

                        s2 = Expansor()    
    
                        s2.liga_rele1_exp1() # Abre Garagem
                        s2.liga_rele1_exp1() 
                        time.sleep(3)
                        s2.desliga_rele1_exp1() 
                        s2.desliga_rele1_exp1()
                        
                        conn.close()
                        

                    elif(comando == "SET5"):
                        log("Abrindo subsolo")

                        s2 = Expansor()    
    
                        s2.liga_rele1_exp7() # Abre Garagem
                        s2.liga_rele1_exp7() 
                        time.sleep(3)
                        s2.desliga_rele1_exp7() 
                        s2.desliga_rele1_exp7()
                        
                        conn.close()

                    elif(comando == "SET 6"):
                        log("SET 6, RESET SOCIAL")
                        conn.close()

                    elif(comando == "SET 8"):
                        
                        log("SET 8, RESET ECLUSA")
                        conn.close()

                    elif(comando == "SET 9"):
                        
                        log("SET 9, RESET INTERFONES")
                        conn.close()

                    elif(comando == "SET 10"):
                        
                        log("SET 10, AUXILIAR 1 (ON/OFF)")
                        conn.close()

                    elif(comando == "SET 11"):
                        
                        log("SET 11, AUXILIAR 2 (ON/OFF)")
                        conn.close()

                    elif(comando == "SET 12"):
                        
                        log("APRESENTAÇÃO")
                        conn.close()
                                            

                    else:

                        txt = ("Recebido pelo servidor:",comando)
                        log(txt)

                        reply = 'ok'
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()


            s = setupServer()

            while True:
                
              time.sleep(1) 

              txt = ("\nEscutando na porta",port)
              log(txt)
              try:

                  conn = setupConnection()
                  dataTransfer(conn)
                  log("Oiee")


              except Exception as err:

                  log("Encerrou conexão")

        
def Alarmes_garagem_1(Rele):
    
    log("Programa Alarmes Garagem em execução")
    em_mudanca = 0
    confirmada_mudanca = 0
    confirmada_desliga_mudanca = 0
    mudanca = 0
    
    while(1):         

        s = cmm.Expansor()
        
##        mudanca = banco.consulta("comandos","mudanca")      
        mud1 = leitor("leitor1_in4")  # Chave de mudança
        pmg1 = leitor("leitor1_in1")

        if mud1 == 1 and em_mudanca == 0:            

            cont = 5

            while cont > 0:

                mud1 = leitor("leitor1_in4")

                if mud1 == 0: # Desligou a chave

                    print("filtrou ruido da chave de mudança")
                    confirmada_mudanca = 0
                    cont = 1
                    break

                if mud1 == 1:

                    confirmada_mudanca = 1
                    
                cont = cont - 1
                time.sleep(0.1)

            mud1 = leitor("leitor1_in4")
                    
            if confirmada_mudanca == 1 and mud1 == 1 and em_mudanca == 0: 
                
                banco.atualiza("comandos","mudanca","1")
                print("Atualizado mudança para 1 na tabela")
                
                em_mudanca = 1
            
                time.sleep(5)

        if mud1 == 0 and em_mudanca == 1 and confirmada_mudanca == 1:

            cont = 5

            while cont > 0:

                mud1 = leitor("leitor1_in4")

                if mud1 == 1: # Desligou a chave

                    print("ruido")
                    confirmada_desliga_mudanca = 0
                    cont = 1
                    break

                if mud1 == 0:

                    confirmada_desliga_mudanca = 1
                    
                cont = cont - 1
                time.sleep(0.1)

            if confirmada_desliga_mudanca == 1:
            
                banco.atualiza("comandos","mudanca","0")
                print("Atualizado mudança para 0 na tabela")
                
                em_mudanca = 0
                confirmada_mudanca = 0

                time.sleep(5)
            
            time.sleep(1)
            
        if pmg1 == 0 and mudanca == "0": # Violação do portão da garagem                              

            cont = 10
            violacao = 0
            time.sleep(1)
            
            while cont > 0:

                mudanca = banco.consulta("comandos","mudanca")
                pmg1 = leitor("leitor1_in1")

                if pmg1 == 0 and mudanca == "0":

                    violacao = 1
                    
                if pmg1 == 1 or mudanca == "1":
                    
                    violacao = 0                    
                    cont = 1

                time.sleep(0.1)
                cont = cont - 1

            if violacao == 0: # Filtrou ruido

                time.sleep(1)
                
            if violacao == 1:

                log("violação do portão garagem 1")

                s.desliga_rele3_exp1() # Sinal Vermelho

                s.liga_rele4_exp1() # Sirene
                            
                evento.enviar("E","132","014") # violação do portão garagem

                cont = 30 # Tempo maximo de espera

                log("Aguardando portão fechar")

                while cont > 0:

                    pmg1 = leitor("leitor1_in1")

                    if(pmg1 == 0): # Portão ainda aberto                                      

                        time.sleep(1)
                        cont = cont - 1
                            
                    if (pmg1 == 1): # Portão ja fechou

                        log("Portão fechou")

                        t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                        t.write("0")
                        t.close()
                        
                        cont = 0
                        time.sleep(1)
                        
                        s.desliga_rele4_exp1() # Desliga sirene
                        
                        break            
                
                s.desliga_rele4_exp1() # Desliga sirene

                violacao = 0
                
                time.sleep(20)
                
        time.sleep(1)
        


def Buffer():

    socket.setdefaulttimeout(3) # limite em segundos para enviar o socket

    host = '172.20.1.5'  # '172.20.1.5' Host servidor  Moni
    port = 4010          # 4010 Porta máquina receptora

    log("Programa buffer de eventos em execução")

    enviado = 0

    while(1):        

        socket.setdefaulttimeout(3)

        b = open("/home/pi/CMM/buffer_eventos.txt","r")
        
        for line in b:

            ln = line
            evento = ln.replace("\n","")
            
            if evento != "": # Se houver alguma coisa para enviar

                # Tentanto enviar o evento",evento...

                try:
        
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = (evento + "\r") # ("7000 185808E30500008")  # Envia abriu portão da eclusa para a central de monitormento
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    log(reply.decode('utf-8'))
                    s.close()

                    enviado = 1                    
                                
                except Exception as err: ## Não conseguiu enviar o evento, sem conexão no momento                     
                    time.sleep(10)
                    break
                
                if enviado == 1:
                                               
                    txt = ("Evento enviado ",evento)
                    log(txt)

                    # Cria uma lista e adiciona todos as linhas encontradas em buffer.txt

                    lista = []

                    try:

                        texto = open("/home/pi/CMM/buffer_eventos.txt","r")
                        for l in txt:                        
                            l = l.replace("\n","") # Coloca na lista o evento ja editado
                            lista.append(evento)
                        
                        # Exclui o item enviado da lista

                        for i in lista:

                            try:
                            
                                if i == evento:
                                    indice = lista.index(i)
                                    print("indice do evento a excluir",indice)
                                    txt = ("Excluindo o evento",evento,"posicao",indice)
                                    log(txt)
                                    del(lista[indice])
                                    nova_lista = lista

                            except Exception as err:

                                log(err)
                                
                        texto.close()

                        # Zera o arquivo buffer

                        tx = open("/home/pi/CMM/buffer_eventos.txt","w") 
                        tx.close()

                        # Reescreve o texto com a nova lista editada

                        texto = open("/home/pi/CMM/buffer_eventos.txt","a")
                        for i in nova_lista:
                            texto.write(i + "\n")
                        texto.close()    
                            
                        enviado = 0

                    except Exception as err:
                        txt = ("Erro",err)
                        log(txt)
            
        b.close() # Fecha o arquivo de texto em modo leitura    
        time.sleep(1)
                    
        
#################### Instancia as Classes  #############################################

intertravamento = Intertravamento(cmm.Rele)
abre = Abre()

####################  Declara as threads dos programas disponiveis  ####################

sociais = threading.Thread(target=Portoes_sociais, args=(cmm.Rele,)) # deixar virgula depois do arg 1
garagem1 = threading.Thread(target=Garagem1, args=(cmm.Rele,))
##arrombamento = threading.Thread(target=Arrombamento, args=(cmm.Rele,))
servidor = threading.Thread(target=Servidor, args=(cmm.Rele,Abre,))
buffer = threading.Thread(target=Buffer)

gerenciador = threading.Thread(target=Servidor_qr)

alarmes1 = threading.Thread(target=Alarmes_garagem_1, args=(cmm.Rele,))

##qrcode1 = threading.Thread(target=thread_qrcode1)
##qrcode2 = threading.Thread(target=thread_qrcode2)
##qrcode3 = threading.Thread(target=thread_qrcode3)
##qrcode4 = threading.Thread(target=thread_qrcode4)
######################################### Start dos Programas  #############################################################

sociais.start() # Inicia o programa dos portões sociais
garagem1.start() # Inicia o programa do portão de garagem
##arrombamento.start() # Inicia o programa de automação
#servidor.start() 
##buffer.start() # Inicia o programa Buffer
alarmes1.start() # Inicia a leitura de "interrupções" (chave de mudança garagem1 e arrombamento de portões)

gerenciador.start()

##qrcode1.start()
##qrcode2.start()
##qrcode3.start()
##qrcode4.start()

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

log("Temperatura do processador " + str(temperatura.cpu()) + "°C\n")  # obter temperatura
log("*")


while(1):

    reset = banco.consulta("comandos","reset")

    if reset == "1":

        banco.atualiza("comandos","reset","0")
        log("Reconheceu pedido de reset do sistema")

        os.system("mpg123 /home/pi/CMM/mp3/reiniciando_sistema.mp3")

        time.sleep(4)

        os.system("sudo reboot now")

        
    

    time.sleep(1)

