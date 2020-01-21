#!/usr/bin/env python3
# coding=UTF-8

# CMM Oficial com placa de expansao da BRAVAS Technololgy
# Desenvolvido por Leandro Leal  rev. 05/11/2019

import RPi.GPIO as GPIO
import time
import biblioteca_CMM as cmm
import cmm_io_entradas as entradas # Entradas digitais fotoacopladas configuradas na interface
import cmm_io_saidas as saidas # Saidas (Rele e transistor) configuradas na interface

##from atualiza_monitor import Monitor # Para atualizacao do monitor da interface graaaaaafica
from expansores import Leitor # teste com uma unica classe com a leitura e acionamento
##import servidor_qr as servidor_qr # Servidor para receber cadastros de qrcodes vindas do gerenviador (Servidor Central)

from datetime import datetime, timedelta
import wiringpi # Biblioteca para usar as GPIO da rasp como saidas ou entradas
import os #      Executa comandos do sistema operacional Ex.: os.system('sudo reboot now'))
import threading # Modulo superior Para executar as threads
import sys
import socket
import _thread as thread

##from filtro import Filtro
##from retorna import Retorna
##
##f = Filtro()
##r = Retorna()

l = Leitor()

socket.setdefaulttimeout(2) # limite de 2 segundos para enviar o socket

os.system("sudo chmod 777 /dev/ttyS0") # Altera a permissao do acesso a serial

os.system("sudo chmod 777 -R /var/www/html/log") # Permissao para escrever no log

os.system("mpg123 /home/pi/CMM/mp3/sistema_carregado.mp3")

mutex = thread.allocate_lock()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

GPIO.setup(11,GPIO.OUT)  # Sinal De buzzer

GPIO.setup(17,GPIO.OUT) # HIGH para enviar LOW para ler dados
GPIO.setup(18,GPIO.OUT) # HIGH para enviar LOW para ler dados


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
    
log("Reiniciou o sistema") 

# Imprimi o nome e o IP do equipamento no log da interface

nome = os.popen('hostname').readline()
nome = str(nome)
nome = nome.replace("\n","")
ip = os.popen('hostname -I').readline()
ip = str(ip)
ip = ip.replace("\n","")
txt = ("Nome desta maquina",nome)
txt = str(txt)
log(txt)

print("Nome desta maquina",nome,"com IP",ip)

############################ INICIA AS CLASSES DA biblioteca_CMM ###############################################

rele = cmm.Rele() # inicia a classe rele com port A em 0
narrador = cmm.Narrador()
temperatura = cmm.Temperatura()
##email = cmm.Email()
##clima = cmm.Clima()
banco = cmm.Banco() # Opreracões CRUD no banco CMM
cliente = banco.consulta("config","cliente")
evento = cmm.Evento("6642") # Inicia a classe evento com o codigo do cliente

###############################################################################################################

def thread_monitor(): # Programa que mantem a conexao com o QR Code

    print("\nPrograma Monitor em execucao\n")

    monitor = Monitor()

    while(1):        

        monitor.loop()
        time.sleep(0.4)
    
##monitor = threading.Thread(target=thread_monitor)
##monitor.start()


def gar1():

    
    exp1 = banco.consulta("entradas","exp1")       

    if(exp1 == "garagem1"):

        log("Programa Garagem 1 executando no expansor 1...")
        
        banco.atualiza("comandos","abre_garagem1","0")
        
        l.desliga_rele4_exp1() # Garante que a sirene esteja desligada
        l.desliga_rele3_exp1() # Garante que sinaleira esteja com sinal vermelho (NF)
        l.desliga_rele2_exp1() # Garante que o Foto esteja desligado
        l.desliga_rele1_exp1() # Garante que o Abre esteja desligado

        eventos = banco.consulta("comandos","eventos")

        mudanca1 = 0
        ja_fechou1 = 0
        violacao = 0

        t = open("/home/pi/CMM/status_garagem_1.cmm","r")
        status_tx1 = t.read()
        t.close()

##        print("status_tx1",status_tx1)
                
        while(1):

            try:            

##                hs = time.strftime("%H:%M:%S")            
            
                ihm_gar1 = banco.consulta("comandos","abre_garagem1") # Valor inserido pelo botao da interface       
                tx1 =  l.leitor1_in3()  # Cantato abre vindo do TX (LINEAR HCS)

                mud1 = l.leitor1_in4()  # Chave de mudanca

                pmg1 = l.leitor1_in1()

                t = open("/home/pi/CMM/status_garagem_1.cmm","r")
                status_tx1 = t.read()
                t.close()
                                           
                            
                if (tx1 == 1 and mudanca1 == 0 or ihm_gar1 == "1" and mudanca1 == 0):   

                    time.sleep(0.1)                
                    tx1 =  l.leitor1_in3()                                

                    if (tx1 == 1 or ihm_gar1 == "1"): # O tx da linear esta direto no abre do portao
                                                
                        time.sleep(0.1)
                        tx1 = l.leitor1_in3()

                        if tx1 == 1 :

                            log("*")
                            log("Reconheceu tx Garagem 1") # Se reconheceu o tx, é porque o portao ja esta abrindo

                            violacao = 0

                            status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                            status.write("1")
                            status.close()

                            l.liga_rele3_exp1() # Sinal Verde (Sinaleira)                            

    ##                        time.sleep(1)

                        if ihm_gar1 == "1": # Abre através do expansor (rele 1)

                            log("*")
                            log("Reconheceu abre Garagem 1 Interface grafica")

                            l.liga_rele3_exp1() # Sinal Verde (Sinaleira)

                            status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                            status.write("1")
                            status.close()

                            l.liga_rele1_exp1() # Pulso para abrir a garagem
                            time.sleep(2)
                            l.desliga_rele1_exp1()

    ##                        time.sleep(1)

    ##                    banco.atualiza("comandos","abre_garagem1","0")                    

                        time.sleep(2) # Tempo para comecar a abrir o portao

                        tentando1 = 3

                        while tentando1 > 0:

                            pmg1 = l.leitor1_in1()
                            tx1 =  l.leitor1_in3() 
                            
                            if pmg1 == 1 and tx1 == 1: # Portao nao abriu apos o comando

                                time.sleep(0.1)
                                pmg1 = l.leitor1_in1()

                                if pmg1 == 1: # Portao nao abriu apos o comando

                                    time.sleep(0.1)
                                    pmg1 = l.leitor1_in1()

                                    if pmg1 == 1:

                                        log("Portao Garagem 1 nao abriu")

                                        l.desliga_rele3_exp1() # Sinal Vermelho                            

    ##                                    if eventos == "1":
    ##                                    
    ##                                        evento.enviar("E","132","015") # Emperrado
    ##
                                        banco.atualiza("comandos","abre_garagem1","0")
                                        
                                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                        status.write("0")
                                        status.close()                                               
                                        

                            if pmg1 == 0: # Portao abriu

                                time.sleep(0.1)                    
                                pmg1 = l.leitor1_in1()

                                if pmg1 == 0: # Confirmado que o Portao abriu

                                    time.sleep(0.1)                    
                                    pmg1 = l.leitor1_in1()

                                    if pmg1 == 0:                                

##                                        if eventos == "1":
                                            
                                        evento.enviar("E","133","013")
                                            
                                        cont1 = 400     # Tempo maximo para deixar 300 = 30 segundos and 

                                        while cont1 > 0:   # Enquanto o portao esta aberto verifica

                                            if cont1 == 400:

                                                log("Portao Garagem 1 abriu")
                                                
                                                l.liga_rele3_exp1() # Sinal verde
                                                
                                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                status.write("1")
                                                status.close()

                                                time.sleep(2)
                                            
                                            pmg1 = l.leitor1_in1()
                                            
                                            if pmg1 == 1 and ja_fechou1 == 0: # Se o portao ja fechou

                                                time.sleep(0.1)
                                                pmg1 = l.leitor1_in1()

                                                if pmg1 == 1:

                                                    time.sleep(0.1)
                                                    pmg1 = l.leitor1_in1()

                                                    if pmg1 == 1:

                                                        log("Portao Garagem 1 fechou C")

                                                        l.desliga_rele3_exp1() # Sinal Vermelho

                                                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                        status.write("0")
                                                        status.close()
                                                        
##                                                        if eventos == "1":
                                                            
                                                        evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                        
                                                        cont1 = 0
                                                        tentando1 = 0
                                                        
                                                        ja_fechou1 = 1
                                                        banco.atualiza("comandos","abre_garagem1","0")  
                                                        
                                                        break                                            
                                                
                                            if pmg1 == 0: # Se o portao ainda esta aberto

                                                time.sleep(0.1)
                                                pmg1 = l.leitor1_in1()

                                                if pmg1 == 0:

                                                    time.sleep(0.1)
                                                    pmg1 = l.leitor1_in1()

                                                    if pmg1 == 0:

                                                        cont2 = 400     # Tempo maximo para deixar 300 = 30 segundos

                                                        while cont2 > 0:   # Enquanto o portao esta aberto verifica

                                                            if cont2 == 400:

                                                                log("Portao Garagem 1 aberto...")
                                                                                                            
                                                            bar1 = l.leitor1_in2() # Faz a leitura da barreira 1
                                                            pmg1 = l.leitor1_in1()

                                                            if bar1 == 1: # Se acionou a barreira de entrada

                                                                time.sleep(0.1)
                                                                bar1 = l.leitor1_in2()

                                                                if bar1 == 1:

                                                                    time.sleep(0.1)
                                                                    bar1 = l.leitor1_in2()

                                                                    if bar1 == 1: # Se acionou a barreira de entrada                                                            

                                                                        log("Acionou a barreira Garagem 1")
##                                                                        l.desliga_rele3_exp1() # Sinal Vermelho

                                                                        tempo = 60

                                                                        while tempo > 0: # Enquanto esta na frente da barreira

                                                                            bar1 = l.leitor1_in2() # Faz a leitura da barreira 1                                                                
                                                                            pmg1 = l.leitor1_in1() # Faz a leitura do ponto magnetico
                                                                            
                                                                            if bar1 == 0:

                                                                                time.sleep(0.1)
                                                                                bar1 = l.leitor1_in2()

                                                                                if bar1 == 0:
                                                                                    
                                                                                    log("Saiu da barreira Garagem 1")
                                                                                    
                                                                                    tempo = 0
                                                                                    time.sleep(1)
                                                                                    break

                                                                            if pmg1 == 1 and ja_fechou1 == 0:

                                                                                time.sleep(0.1)
                                                                                pmg1 = l.leitor1_in1()

                                                                                if pmg1 == 1:                                                                            
        ##
                                                                                    log("Portao Garagem 1 fechou A")
        ##
                                                                                    l.desliga_rele3_exp1() # Sinal Vermelho
        ##
                                                                                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                                    status.write("0")
                                                                                    status.close()

##                                                                                    if eventos == "1":
                                                                                    
                                                                                    evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                                                    
                                                                                    cont2 = 0
                                                                                    
                                                                                    ja_fechou1 = 1
                                                                                    banco.atualiza("comandos","abre_garagem1","0")
                                                                                    
                                                                                    break
                                                                                
                                                                            if tempo == 1:

                                                                                log("Portao Garagem 1 aberto por muito tempo")

                                                                                l.desliga_rele3_exp1() # Sinal Vermelho

##                                                                                l.liga_rele4_exp1() # Sirene                                            
##                                                                                time.sleep(3)
##                                                                                l.desliga_rele4_exp1()

##                                                                                if eventos == "1":

                                                                                evento.enviar("E","132","026") # Envia obstrucao

##                                                                                if eventos == "0":
##
##                                                                                    print("Reconheceu que eventos esta desligado neste nivel")

                                                                                banco.atualiza("comandos","abre_garagem1","0")

                                                                                break

                                                                            tempo = tempo - 1
                                                                            time.sleep(1)

                                                                    pmg1 = l.leitor1_in1()                                                                                                
                                                                    
                                                                    if pmg1 == 0: # Portao ainda aberto

                                                                        time.sleep(0.1)                                                        
                                                                        pmg1 = l.leitor1_in1() # Faz a leitura do ponto magnetico                                        

                                                                        if pmg1 == 0:

                                                                            log("Aguardando 30 segundos portao Garagem 1 fechar")

                                                                            temp = 300
                                                                            entrada_permitida = 0
                                                                            ja_fechou1 = 0

                                                                            time.sleep(1)

                                                                            while temp > 0:  # Enquanto o portao ainda esta aberto e tempo menor que 30 seg
                                                                                
                                                                                pmg1 = l.leitor1_in1() # Faz a leitura do ponto magnetico
                                                                                bar1 = l.leitor1_in2() # Faz a leitura da barreira 1
                                                                                tx1 =  l.leitor1_in3()  # Cantato abre vindo do TX (LINEAR HCS)

                                                                                if tx1 == 1: # Alguem acionou o controle enquanto o portao fechava

                                                                                    time.sleep(0.1)                                                                    
                                                                                    tx1 =  l.leitor1_in3()

                                                                                    if tx1 == 1:

                                                                                        time.sleep(0.1)                                                                    
                                                                                        tx1 =  l.leitor1_in3()

                                                                                        if tx1 == 1:

                                                                                            log("Reconheceu abre Garagem 1 enquanto o portao estava aberto")                                                    
                                                                                            l.liga_rele3_exp1() # Sinal Verde

                                                                                            entrada_permitida = 1 # Reconhece o segundo acionamento
                                                                                                                                                                                                                                                            
            ##                                                                                break # Sai da funcao e inicia novamente a verificacao

                                                                                if bar1 == 1 and entrada_permitida == 1:
                                                                                    
                                                                                    time.sleep(0.1)                                                                    
                                                                                    bar1 = l.leitor1_in2()
                                                                                    
                                                                                    if bar1 == 1:

                                                                                        l.desliga_rele3_exp1() # Sinal Vermelho

                                                                                        tempo2 = 60

                                                                                        while tempo2 > 0: # Enquanto a barreira esta acionada

                                                                                            bar1 = l.leitor1_in2()# Faz a leitura da barreira 1
                                                                                            pmg1 = l.leitor1_in1()
                                                                                            
                                                                                            if bar1 == 0:

                                                                                                time.sleep(0.1)
                                                                                                bar1 = l.leitor1_in2()

                                                                                                if bar1 == 0:

                                                                                                    time.sleep(0.1)
                                                                                                    bar1 = l.leitor1_in2()

                                                                                                    if bar1 == 0:

                                                                                                        log("Saiu da barreira")
                                                                                                        l.desliga_rele3_exp1() # Sinal Vermelho
                                                                                                        log("Entrou segundo veiculo autorizado")

                                                                                                        entrada_permitida = 0
                                                                                                        
                                                                                                        tempo2 = 0
                                                                                                        
                                                                                            if pmg1 == 1 and ja_fechou1 == 0:
         
                                                                                                log("Portao Garagem 1 fechou. A")

                                                                                                l.desliga_rele3_exp1() # Sinal Vermelho

                                                                                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                                                status.write("0")
                                                                                                status.close()

##                                                                                                if eventos == "1":
                                                                                                
                                                                                                evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                                                                
                                                                                                cont2 = 0
                                                                                                temp2 = 0

                                                                                                ja_fechou1 = 1
                                                                                                banco.atualiza("comandos","abre_garagem1","0")  
                                                                                                
                                                                                                break
                                                                                            
                                                                                            if tempo2 == 1:

                                                                                                log("Portao do segundo veiculo aberto por muito tempo")

                                                                                                l.desliga_rele3_exp1() # Sinal Vermelho

##                                                                                                l.liga_rele4_exp1() # Sirene                                            
##                                                                                                time.sleep(3)
##                                                                                                l.desliga_rele4_exp1()

##                                                                                                if eventos == "1":

                                                                                                evento.enviar("E","132","026") # Envia obstrucao

##                                                                                                if eventos == "0":
##
##                                                                                                    print("Reconheceu que eventos esta desligado neste nivel 2")

                                                                                                tempo2 = 1
                                                                                            
                                                                                            tempo2 = tempo2 - 1
                                                                                            time.sleep(1)                                       

                                                                                   
                                                                                if bar1 == 1 and entrada_permitida == 0: # Dupla passagem
                                                                                    
                                                                                    time.sleep(0.5) # Alterado de 0.1 para 0.5 analizar violacoes                                                                    
                                                                                    bar1 = l.leitor1_in2()

                                                                                    if bar1 == 1:

                                                                                        time.sleep(0.2)                                                                    
                                                                                        bar1 = l.leitor1_in2()

                                                                                        if bar1 == 1: # Dupla passagem 

                                                                                            log("Dupla passagem Garagem 1")

                                                                                            l.desliga_rele3_exp1() # Sinal Vermelho

##                                                                                            if eventos == "1":
                                                                                                
                                                                                            evento.enviar("E","132","016")

##                                                                                            l.liga_rele4_exp1() # Sirene                                            
##                                                                                            time.sleep(10)
##                                                                                            l.desliga_rele4_exp1()                                            

                                                                                            break
                                                                                    
                                                                         
                                                                                if pmg1 == 1 and ja_fechou1 == 0: # portao ja fechou

                                                                                    time.sleep(0.1)                                                                    
                                                                                    pmg1 = l.leitor1_in1()

                                                                                    if pmg1 == 1:

                                                                                        time.sleep(0.1)                                                                    
                                                                                        pmg1 = l.leitor1_in1()

                                                                                        if pmg1 == 1:
                                                                                            
                                                                                            l.desliga_rele3_exp1() # Sinal Vermelho

                                                                                            status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                                            status.write("0")
                                                                                            status.close()

##                                                                                            if eventos == "1":
                                                                                            
                                                                                            evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                                                            
                                                                                            temp = 0
                                                                                            cont2 = 0

                                                                                            ja_fechou1 = 1
                                                                                            banco.atualiza("comandos","abre_garagem1","0")

                                                                                            log("Portao Garagem 1 fechou E")
                                                                                            
                                                                                            break                                                                                                                                                     

                                                                                if temp == 1:

                                                                                    log("Portao Garagem 1 aberto por muito tempo")

                                                                                    l.desliga_rele3_exp1() # Sinal Vermelho

##                                                                                    l.liga_rele4_exp1() # Sirene                                            
##                                                                                    time.sleep(3)
##                                                                                    l.desliga_rele4_exp1()

                                                                                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                                    status.write("0")
                                                                                    status.close()

##                                                                                    if eventos == "1":

                                                                                    evento.enviar("E","132","026") # Envia obstrucao

                                                                                    temp = 0
                                                                                    banco.atualiza("comandos","abre_garagem1","0")
                                                                                    break

                                                                                temp = temp - 1
                                                                                time.sleep(0.2)

                                                            if pmg1 == 1 and ja_fechou1 == 0:

                                                                time.sleep(0.1)
                                                                pmg1 = l.leitor1_in1()
                                                                
                                                                if pmg1 == 1:

                                                                    time.sleep(0.1)
                                                                    pmg1 = l.leitor1_in1()
                                                                    
                                                                    if pmg1 == 1:

                                                                        log("Portao Garagem 1 fechou B")
        ##
                                                                        l.desliga_rele3_exp1() # Sinal Vermelho
        ##
                                                                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                        status.write("0")
                                                                        status.close()

##                                                                        if eventos == "1":
                                                                        
                                                                        evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                                        
                                                                        cont2 = 0

                                                                        ja_fechou1 = 1

                                                                        banco.atualiza("comandos","abre_garagem1","0")
                                                                        
                                                                        break
                                                                                        
                                                            if cont2 == 1 and ja_fechou1 == 0:

                                                                log("Atingiu o tempo maximo e o portao da Garagem 1 nao fechou")

                                                                l.desliga_rele3_exp1() # Sinal Vermelho

##                                                                l.liga_rele4_exp1() # Sirene                                            
##                                                                time.sleep(3)
##                                                                l.desliga_rele4_exp1()

                                                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                status.write("0")
                                                                status.close()

                                                                cont2 = 0
                                                                ja_fechou1 = 0

                                                                banco.atualiza("comandos","abre_garagem1","0")
                                                                
                                                                break
                                                            
                                                            time.sleep(0.1)
                                                            cont2 = cont2 - 1
                                                                                
                                                        print("Encerrou o ciclo Garagem 1, saindo do while...")
                                                        break
                                                    
                                            if cont1 == 1 and ja_fechou1 == 0:

                                                log("Atingiu o tempo maximo e o portao da Garagem 1 nao fechou")

                                                l.desliga_rele3_exp1() # Sinal Vermelho

##                                                l.liga_rele4_exp1() # Sirene                                            
##                                                time.sleep(3)
##                                                l.desliga_rele4_exp1()

                                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                status.write("0")
                                                status.close()

                                                cont1 = 0
                                                ja_fechou1 = 0

                                                banco.atualiza("comandos","abre_garagem2","0")
                                                
                                                break
                                            
                                            
                                            cont1 = cont1 - 1
                                            time.sleep(0.1)
                                
    ##                            print("Falhou a leitura pm1, tentara de novo")
                                
                                                            
                            
                            if status_tx1 == "1" and pmg1 == 1:

                                log ("Recebeu comando para abrir Garagem 1 mas o portao nao abriu")
                                
                                l.desliga_rele3_exp1() # Sinal Vermelho
                                
                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                status.write("0")
                                status.close()

                                ja_fechou1 = 0                        
                                banco.atualiza("comandos","abre_garagem1","0")

                            tentando1 = tentando1 - 1
                            time.sleep(0.2)
                            
    ##                        print("Tentando novamente 3 vezes, Garagem 1")
                
                if mud1 == 1 and mudanca1 == 0 : # Chave de mudanca acionada

                    time.sleep(0.1)     
                    mud1 = l.leitor1_in4()  # Chave de mudanca            

                    if mud1 == 1:

                        time.sleep(0.1)     
                        mud1 = l.leitor1_in4()  # Chave de mudanca            

                        if mud1 == 1:

                            log("*")
                            log("Chave de mudanca acionada Garagem 1")

                            violacao = 0

                            l.liga_rele3_exp1() # Sinal Verde

##                            if evento == "1":

                            evento.enviar("E","132","025")                

                            t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                            t.write("1")
                            t.close()

                            l.liga_rele1_exp1() # Aciona o rele 1 do modulo 1 (Abre)
                            time.sleep(2)
                            l.desliga_rele1_exp1()
                            
                            l.liga_rele2_exp1() # Aciona o rele 2 do modulo 1 (Foto)                

                            mudanca1 = 1

                            time.sleep(2)

                if mud1 == 0 and mudanca1 == 1:

                    time.sleep(0.1)
                    mud1 = l.leitor1_in4()

                    if mud1 == 0:

                        time.sleep(0.1)
                        mud1 = l.leitor1_in4()

                        if mud1 == 0:

                            log("Desligada a chave de mudanca Garagem 1")

                            l.desliga_rele3_exp1() # Sinal Vermelho

##                            if evento == "1":

                            evento.enviar("R","132","025")
                                            
                            l.desliga_rele1_exp1() # Desliga o rele 1 do modulo 1 (Abre)
                            l.desliga_rele2_exp1() # Desliga o rele 2 do modulo 1 (Foto) 

                            pmg1 = l.leitor1_in1()

                            cont = 60 # Tempo maximo de espera

                            log("Aguardando portao Garagem 1 fechar depois da mudanca")

                            time.sleep(2)

                            while cont > 0:
                                
                                pmg1 = l.leitor1_in1()                                                              
                                        
                                if pmg1 == 1: # Portao ja fechou

                                    time.sleep(0.1)
                                    pmg1 = l.leitor1_in1()

                                    if pmg1 == 1:

                                        time.sleep(0.1)
                                        pmg1 = l.leitor1_in1()

                                        if pmg1 == 1 :

                                            log("Portao Garagem 1 fechou depois da mudanca")

                                            l.desliga_rele3_exp1() # Sinal Vermelho

                                            t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                                            t.write("0")
                                            t.close()
                                            
                                            cont = 0
                                            mudanca1 = 0
                                            time.sleep(1)
                                            break
                                        
                                if cont == 1:

                                    log("Chave de mudanca Garagem 1 desligou mas o portao nao fechou apos 1 min")

                                    l.desliga_rele3_exp1() # Sinal Vermelho

                                    t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                                    t.write("0")
                                    t.close()

##                                    l.liga_rele4_exp1() # Pulso na Sirene                                            
##                                    time.sleep(3)
##                                    l.desliga_rele4_exp1()                                
                                    
                                    mudanca1 = 0
                                    
                                    time.sleep(1)

                                time.sleep(1)
                                cont = cont - 1         


# Ativar depois de aimentar o tempo do temporizador (tx)                                

                                
                if status_tx1 == "0" and pmg1 == 0 and tx1 == 0 and violacao == 0: # Violacao do portao da garagem
                    
                    time.sleep(0.2)                    

                    t = open("/home/pi/CMM/status_garagem_1.cmm","r")
                    status_tx1 = t.read()
                    t.close() 

                    pmg1 = l.leitor1_in1()

                    if pmg1 == 0 and status_tx1 == "0":

                        time.sleep(0.2)                    

                        t = open("/home/pi/CMM/status_garagem_1.cmm","r")
                        status_tx1 = t.read()
                        t.close() 

                        pmg1 = l.leitor1_in1()

                        if pmg1 == 0 and status_tx1 == "0":

                            log("violacao do portao garagem 1")

                            l.desliga_rele3_exp1() # Sinal Vermelho

    ##                        l.liga_rele4_exp1() # Sirene
                                        
##                            evento.enviar("E","132","014")

                            cont = 30 # Tempo maximo de espera

                            log("Aguardando portao garagem 1 fechar apos violacao")

                            while cont > 0:

                                pmg1 = l.leitor1_in1()

                                if(pmg1 == 0): # Portao ainda aberto                                      

                                    time.sleep(1)
                                    cont = cont - 1
                                        
                                if (pmg1 == 1): # Portao ja fechou

                                    log("Portao fechou")

                                    t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                                    t.write("0")
                                    t.close()
                                    
                                    cont = 0
                                    time.sleep(1)
                                    
                                    l.desliga_rele4_exp1() # Desliga sirene
                                    
                                    break            
                            
                            l.desliga_rele4_exp1() # Desliga sirene

                            violacao = 1
                            
                            time.sleep(1)
                            
                ja_fechou1 = 0
                time.sleep(0.2)
        
            except Exception as err:

                log("Erro na rotina da garagem 1")
                log(err)
            
    log("Saiu do loop da lógica da Garagem 1 ")

g1 = threading.Thread(target=gar1)
g1.start()

def gar2():    
     

    exp2 = banco.consulta("entradas","exp2")    

    if(exp2 == "garagem2"):

        log("Programa Garagem 2 executando no expansor 2...")
        
        l.desliga_rele4_exp2() # Garante que a sirene esteja desligada
        l.desliga_rele3_exp2() # Garante que sinaleira esteja com sinal vermelho (NF)
        l.desliga_rele2_exp2() # Garante que o Foto esteja desligado
        l.desliga_rele1_exp2() # Garante que o Abre esteja desligado

        eventos = banco.consulta("comandos","eventos")

        mudanca2 = 0
        ja_fechou2 = 0
        violacao = 0

        t = open("/home/pi/CMM/status_garagem_2.cmm","r")
        status_tx1 = t.read()
        t.close()
                        
        while(1):

            try:
          
            
                ihm_gar2 = banco.consulta("comandos","abre_garagem2") # Valor inserido pelo botao da interface       
                tx2 =  l.leitor2_in3()  # Cantato abre vindo do TX (LINEAR HCS)

                mud2 = banco.consulta("comandos","mudanca")  # Chave de mudanca remota, abastecimento do gas

                pmg2 = l.leitor2_in1()

                t = open("/home/pi/CMM/status_garagem_2.cmm","r")
                status_tx2 = t.read()
                t.close()                    
                            
                if (tx2 == 1 or ihm_gar2 == "1" and mudanca2 == 0):   

                    time.sleep(0.1)                
                    tx2 =  l.leitor2_in3()                               

                    if (tx2 == 1 or ihm_gar2 == "1"): # O tx da linear esta direto no abre do portao

                        time.sleep(0.1)
                        tx2 = l.leitor2_in3()

                        if tx2 == 1 :

                            log("*")
                            log("Reconheceu tx Garagem 2") # Se reconheceu o tx, é porque o portao ja esta abrindo

                            violacao = 0

                            status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                            status.write("1")
                            status.close()

                            l.liga_rele3_exp2() # Sinal Verde (Sinaleira) 

    ##                        time.sleep(1)

                        if ihm_gar2 == "1": # Abre através do expansor (rele 1)

                            log("*")
                            log("Reconheceu abre Garagem 2 Interface grafica")

                            l.liga_rele3_exp2() # Sinal Verde (Sinaleira)

                            status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                            status.write("1")
                            status.close()

                            l.liga_rele1_exp2() # Pulso para abrir a garagem
                            time.sleep(2)
                            l.desliga_rele1_exp2()

    ##                        time.sleep(1)

    ##                    banco.atualiza("comandos","abre_garagem2","0")                    

                        time.sleep(2) # Tempo para comecar a abrir o portao

                        tentando2 = 3

                        while tentando2 > 0:

                            pmg2 = l.leitor2_in1()
                            tx2 = l.leitor2_in3()
                            
                            if pmg2 == 1 and tx2 == 1: # Portao nao abriu apos o comando

                                time.sleep(0.1)
                                pmg2 = l.leitor2_in1()

                                if pmg2 == 1: # Portao nao abriu apos o comando

                                    time.sleep(0.1)
                                    pmg2 = l.leitor2_in1()

                                    if pmg2 == 1:

                                        log("Portao Garagem 2 nao abriu")

                                        l.desliga_rele3_exp2() # Sinal Vermelho                            

    ##                                    if eventos == "1":
    ##                                    
    ##                                        evento.enviar("E","132","019") # Emperrado
    ##
                                        banco.atualiza("comandos","abre_garagem2","0")
                                        
                                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                        status.write("0")
                                        status.close()                                               
                                        

                            if pmg2 == 0: # Portao abriu

                                time.sleep(0.1)                    
                                pmg2 = l.leitor2_in1()

                                if pmg2 == 0: # Confirmado que o Portao abriu

                                    time.sleep(0.1)                    
                                    pmg2 = l.leitor2_in1()

                                    if pmg2 == 0:                                

                                        if eventos == "1":
                                            
                                            evento.enviar("E","133","017")
                                            
                                        cont1 = 400     # Tempo maximo para deixar 300 = 30 segundos

                                        while cont1 > 0:   # Enquanto o portao esta aberto verifica

                                            if cont1 == 400:

                                                log("Portao Garagem 2 abriu")
                                                
                                                l.liga_rele3_exp2() # Sinal verde
                                                
                                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                status.write("1")
                                                status.close()

                                                time.sleep(2)
                                            
                                            pmg2 = l.leitor2_in1()
                                            
                                            if pmg2 == 1 and ja_fechou2 == 0: # Se o portao ja fechou

                                                time.sleep(0.1)
                                                pmg2 = l.leitor2_in1()

                                                if pmg2 == 1:

                                                    time.sleep(0.1)
                                                    pmg2 = l.leitor2_in1()

                                                    if pmg2 == 1 :

                                                        log("Portao Garagem 2 fechou C")

                                                        l.desliga_rele3_exp2() # Sinal Vermelho

                                                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                        status.write("0")
                                                        status.close()
                                                        
##                                                        if eventos == "1":
                                                            
                                                        evento.enviar("R","133","017") # Envia o evento de fechamento para a central
                                                        
                                                        cont1 = 0
                                                        tentando2 = 0
                                                        
                                                        ja_fechou2 == 1
                                                        banco.atualiza("comandos","abre_garagem2","0")
                                                        
                                                        break                                            
                                                
                                            if pmg2 == 0: # Se o portao ainda esta aberto

                                                time.sleep(0.1)
                                                pmg2 = l.leitor2_in1()

                                                if pmg2 == 0:

                                                    time.sleep(0.1)
                                                    pmg2 = l.leitor2_in1()

                                                    if pmg2 == 0:

                                                        cont2 = 400     # Tempo maximo para deixar 300 = 30 segundos

                                                        while cont2 > 0:   # Enquanto o portao esta aberto verifica

                                                            if cont2 == 400:

                                                                log("Portao Garagem 2 aberto...")
                                                        
                                                            bar2 = l.leitor2_in2() # Faz a leitura da barreira 1
                                                            pmg2 = l.leitor2_in1()

                                                            if bar2 == 1: # Se acionou a barreira de entrada

                                                                time.sleep(0.1)
                                                                bar2 = l.leitor2_in2()

                                                                if bar2 == 1:

                                                                    time.sleep(0.1)
                                                                    bar2 = l.leitor2_in2()

                                                                    if bar2 == 1: # Se acionou a barreira de entrada                                                            

                                                                        log("Acionou a barreira Garagem 2")
##                                                                        l.desliga_rele3_exp2() # Sinal Vermelho

                                                                        tempo = 60

                                                                        while tempo > 0: # Enquanto esta na frente da barreira

                                                                            bar2 = l.leitor2_in2() # Faz a leitura da barreira 1
                                                                            pmg2 = l.leitor2_in1()
                                                                            
                                                                            if bar2 == 0:

                                                                                time.sleep(0.1)
                                                                                bar2 = l.leitor2_in2()

                                                                                if bar2 == 0:
                                                                                    
                                                                                    log("Saiu da barreira Garagem 2")
                                                                                    
                                                                                    tempo = 0
                                                                                    time.sleep(1)
                                                                                    break

                                                                            if pmg2 == 1 and ja_fechou2 == 0:

                                                                                time.sleep(0.1)
                                                                                pmg2 = l.leitor2_in1()

                                                                                if pmg2 == 1:                                                                            
        ##
                                                                                    log("Portao Garagem 2 fechou A")
        ##
                                                                                    l.desliga_rele3_exp2() # Sinal Vermelho
        ##
                                                                                    status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                                    status.write("0")
                                                                                    status.close()

##                                                                                    if eventos == "1":
                                                                                    
                                                                                    evento.enviar("R","133","017") # Envia o evento de fechamento para a central
                                                                                    
                                                                                    cont2 = 0
                                                                                    
                                                                                    ja_fechou2 = 1
                                                                                    banco.atualiza("comandos","abre_garagem2","0")
                                                                                    
                                                                                    break
                                                                                
                                                                            if tempo == 1:

                                                                                log("Portao Garagem 2 aberto por muito tempo")

                                                                                l.desliga_rele3_exp2() # Sinal Vermelho

##                                                                                l.liga_rele4_exp2() # Sirene                                            
##                                                                                time.sleep(3)
##                                                                                l.desliga_rele4_exp2()

                                                                                if eventos == "1":

                                                                                    evento.enviar("E","132","027") # Envia obstrucao

                                                                                if eventos == "0":

                                                                                    print("Reconheceu que eventos esta desligado neste nivel")

                                                                                banco.atualiza("comandos","abre_garagem2","0")

                                                                                break

                                                                            tempo = tempo - 1
                                                                            time.sleep(1) 
                                                                    
                                                                    pmg2 = l.leitor2_in1() # Faz a leitura do ponto magnetico                                    
                                                                    
                                                                    if pmg2 == 0: # Portao ainda aberto

                                                                        time.sleep(0.1)                                                        
                                                                        pmg2 = l.leitor2_in1() # Faz a leitura do ponto magnetico                                        

                                                                        if pmg2 == 0:

                                                                            log("Aguardando 30 segundos portao Garagem 2 fechar")

                                                                            temp = 300
                                                                            entrada_permitida = 0
                                                                            ja_fechou2 = 0

                                                                            time.sleep(1)

                                                                            while temp > 0:  # Enquanto o portao ainda esta aberto e tempo menor que 30 seg
                                                                                
                                                                                pmg2 = l.leitor2_in1() # Faz a leitura do ponto magnetico
                                                                                bar2 = l.leitor2_in2() # Faz a leitura da barreira 1
                                                                                tx2 =  l.leitor2_in3()  # Cantato abre vindo do TX (LINEAR HCS)

                                                                                if tx2 == 1: # Alguem acionou o controle enquanto o portao fechava

                                                                                    time.sleep(0.1)                                                                    
                                                                                    tx2 =  l.leitor2_in3()

                                                                                    if tx2 == 1:

                                                                                        time.sleep(0.1)                                                                    
                                                                                        tx2 =  l.leitor2_in3()

                                                                                        if tx2 == 1:

                                                                                            log("Reconheceu abre Garagem 2 enquanto o portao estava aberto")                                                    
                                                                                            l.liga_rele3_exp2() # Sinal Verde

                                                                                            entrada_permitida = 1 # Reconhece o segundo acionamento
                                                                                                                                                                                                                                                            
            ##                                                                                break # Sai da funcao e inicia novamente a verificacao

                                                                                if bar2 == 1 and entrada_permitida == 1:
                                                                                    
                                                                                    time.sleep(0.1)                                                                    
                                                                                    bar2 = l.leitor2_in2()
                                                                                    
                                                                                    if bar2 == 1:

                                                                                        l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                        tempo2 = 60

                                                                                        while tempo2 > 0: # Enquanto a barreira esta acionada

                                                                                            bar2 = l.leitor2_in2() # Faz a leitura da barreira 1
                                                                                            pmg2 = l.leitor2_in1()

                                                                                            if bar2 == 0:

                                                                                                time.sleep(0.1)
                                                                                                bar2 = l.leitor2_in2()

                                                                                                if bar2 == 0:

                                                                                                    time.sleep(0.1)
                                                                                                    bar2 = l.leitor2_in2()

                                                                                                    if bar2 == 0:

                                                                                                        log("Saiu da barreira Garagem 2")
                                                                                                        l.desliga_rele3_exp2() # Sinal Vermelho
                                                                                                        log("Entrou segundo veiculo autorizado Garagem 2")

                                                                                                        entrada_permitida = 0
                                                                                                        
                                                                                                        tempo2 = 0
                                                                                                        
                                                                                            if pmg2 == 1 and ja_fechou2 == 0:
         
                                                                                                log("Portao Garagem 2 fechou. A")

                                                                                                l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                                                status.write("0")
                                                                                                status.close()

##                                                                                                if eventos == "1":
                                                                                                
                                                                                                evento.enviar("R","133","017") # Envia o evento de fechamento para a central
                                                                                                
                                                                                                cont2 = 0
                                                                                                temp2 = 0

                                                                                                ja_fechou2 = 1
                                                                                                banco.atualiza("comandos","abre_garagem2","0")  
                                                                                                
                                                                                                break
                                                                                                        
                                                                                            if tempo2 == 1:

                                                                                                log("Portao do segundo veiculo aberto por muito tempo Garagem 2 ")

                                                                                                l.desliga_rele3_exp2() # Sinal Vermelho

##                                                                                                l.liga_rele4_exp2() # Sirene                                            
##                                                                                                time.sleep(3)
##                                                                                                l.desliga_rele4_exp2()

                                                                                                if eventos == "1":

                                                                                                    evento.enviar("E","132","027") # Envia obstrucao

                                                                                                if eventos == "0":

                                                                                                    print("Reconheceu que eventos esta desligado neste nivel 2 g2")

                                                                                                tempo2 = 1
                                                                                            
                                                                                            tempo2 = tempo2 - 1
                                                                                            time.sleep(1)                                       

                                                                                   
                                                                                if bar2 == 1 and entrada_permitida == 0: # Dupla passagem
                                                                                    
                                                                                    time.sleep(0.5) # Alterado de 0.1 para 0.5 analizar violacoes                                                                       
                                                                                    bar2 = l.leitor2_in2()

                                                                                    if bar2 == 1:

                                                                                        time.sleep(0.2)                                                                    
                                                                                        bar2 = l.leitor2_in2()

                                                                                        if bar2 == 1: # Dupla passagem                                                                                    
                                                                                            
                                                                                            log("Dupla passagem Garagem 2")
                                                                                            
                                                                                            l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                            if eventos == "1":

                                                                                                log("Nao esta enviando evento no momento")

                                                                                                evento.enviar("E","132","020")

##                                                                                            l.liga_rele4_exp2() # Sirene                                            
##                                                                                            time.sleep(10)
##                                                                                            l.desliga_rele4_exp2()                                            

                                                                                            break
                                                                                    
                                                                         
                                                                                if pmg2 == 1 and ja_fechou2 == 0: # portao ja fechou

                                                                                    time.sleep(0.1)                                                                    
                                                                                    pmg2 = l.leitor2_in1()

                                                                                    if pmg2 == 1:

                                                                                        time.sleep(0.1)                                                                    
                                                                                        pmg2 = l.leitor2_in1()

                                                                                        if pmg2 == 1:
                                                                                            
                                                                                            l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                            log("Portao Garagem 2 fechou C")

                                                                                            status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                                            status.write("0")
                                                                                            status.close()

##                                                                                            if eventos == "1":
                                                                                            
                                                                                            evento.enviar("R","133","017") # Envia o evento de fechamento para a central

                                                                                            temp = 0
                                                                                            cont2 = 0

                                                                                            ja_fechou2 = 1
                                                                                            banco.atualiza("comandos","abre_garagem2","0")

                                                                                            log("Portao Garagem 2 fechou E")
                                                                                            
                                                                                            break
                                                                                        
                                                                                    
                                                                                if temp == 1:

                                                                                    log("Portao Garagem 2 aberto por muito tempo")

                                                                                    l.desliga_rele3_exp2() # Sinal Vermelho

##                                                                                    l.liga_rele4_exp2() # Sirene                                            
##                                                                                    time.sleep(3)
##                                                                                    l.desliga_rele4_exp2()

                                                                                    status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                                    status.write("0")
                                                                                    status.close()

                                                                                    if eventos == "1":

                                                                                        evento.enviar("E","132","027") # Envia obstrucao

                                                                                    temp = 0
                                                                                    banco.atualiza("comandos","abre_garagem2","0")
                                                                                    break

                                                                                temp = temp - 1
                                                                                time.sleep(0.2)

                                                            if pmg2 == 1 and ja_fechou2 == 0:

                                                                time.sleep(0.1)
                                                                pmg2 = l.leitor2_in1()
                                                                
                                                                if pmg2 == 1:

                                                                    time.sleep(0.1)
                                                                    pmg2 = l.leitor2_in1()
                                                                    
                                                                    if pmg2 == 1 :

                                                                        log("Portao Garagem 2 fechou B")

                                                                        l.desliga_rele3_exp2() # Sinal Vermelho

                                                                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                        status.write("0")
                                                                        status.close()

##                                                                        if eventos == "1":
                                                                        
                                                                        evento.enviar("R","133","017") # Envia o evento de fechamento para a central
        ##                                                                
                                                                        cont2 = 0

                                                                        ja_fechou2 = 1

                                                                        banco.atualiza("comandos","abre_garagem2","0") 
                                                                        
                                                                        break
                                                                                        
                                                            if cont2 == 1 and ja_fechou2 == 0:

                                                                log("Atingiu o tempo maximo e o portao da Garagem 2 nao fechou")

                                                                l.desliga_rele3_exp2() # Sinal Vermelho

##                                                                l.liga_rele4_exp2() # Sirene                                            
##                                                                time.sleep(3)
##                                                                l.desliga_rele4_exp2()

                                                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                status.write("0")
                                                                status.close()

                                                                cont2 = 0
                                                                ja_fechou2 = 0

                                                                banco.atualiza("comandos","abre_garagem2","0")
                                                                
                                                                break
                                                            
                                                            time.sleep(0.1)
                                                            cont2 = cont2 - 1
                                                                                
                                                        print("Encerrou o ciclo Garagem 2, saindo do while...")
                                                        break
                                                                        
                                            if cont1 == 1 and ja_fechou2 == 0:

                                                log("Atingiu o tempo maximo e o portao da Garagem 2 nao fechou")

                                                l.desliga_rele3_exp2() # Sinal Vermelho

##                                                l.liga_rele4_exp2() # Sirene                                            
##                                                time.sleep(3)
##                                                l.desliga_rele4_exp2()

                                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                status.write("0")
                                                status.close()

                                                cont1 = 0
                                                ja_fechou2 = 0

                                                banco.atualiza("comandos","abre_garagem2","0")
                                                
                                                break
                                            
                                            cont1 = cont1 - 1
                                            time.sleep(0.1)
                                            
                                        
##                                print("Falhou um leitura do pm2, tentara de novo")

                                    
                                    
                            if status_tx2 == "1" and pmg2 == 0:

                                log ("Recebeu comando para abrir Garagem 2 mas o portao no abriu")
                                
                                l.desliga_rele3_exp2() # Sinal Vermelho
                                
                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                status.write("0")
                                status.close()

                                ja_fechou2 = 0
                                banco.atualiza("comandos","abre_garagem2","0")

                            tentando2 = tentando2 - 1
                            time.sleep(0.2)
                            
                            
                if mud2 == "1" and mudanca2 == 0 : # Chave de mudanca remota, abastecimento do gas
                    
                    log("*")
                    log("Chave de mudanca acionada Garagem 2 abasteciomento do gas")

                    l.liga_rele3_exp2() # Sinal Verde
                    
                    evento.enviar("E","132","25")                

                    t = open("/home/pi/CMM/status_garagem_2.cmm","w")
                    t.write("1")
                    t.close()

                    l.liga_rele1_exp2() # Aciona o rele 1 do modulo 2 (Abre)
                    time.sleep(2)
                    l.desliga_rele1_exp2()
                    l.liga_rele2_exp2() # Aciona o rele 2 do modulo 2 (Foto)                

                    mudanca2 = 1

                    time.sleep(2)

                if mud2 == "0" and mudanca2 == 1:
                                        
                    log("Desligada a chave de mudanca Garagem 2 abastecimento do gas")

                    l.desliga_rele3_exp2() # Sinal Vermelho
                    
                    evento.enviar("R","132","25")
                                    
                    l.desliga_rele1_exp2() # Desliga o rele 1 do modulo 1 (Abre)
                    l.desliga_rele2_exp2() # Desliga o rele 2 do modulo 1 (Foto) 

                    pmg2 = l.leitor2_in1()

                    cont = 60 # Tempo maximo de espera

                    log("Aguardando portao Garagem 2 fechar depois do abasteciment do gas")

                    time.sleep(2)

                    while cont > 0:
                        
                        pmg2 = l.leitor2_in1()                                                              
                                
                        if pmg2 == 1: # Portao ja fechou

                            time.sleep(0.1)
                            pmg2 = l.leitor2_in1()

                            if pmg2 == 1:

                                time.sleep(0.1)
                                pmg2 = l.leitor2_in1()

                                if pmg2 == 1 :

                                    log("Portao Garagem 2 fechou depois do abastecimento do gas")

                                    l.desliga_rele3_exp2() # Sinal Vermelho

                                    t = open("/home/pi/CMM/status_garagem_2.cmm","w")
                                    t.write("0")
                                    t.close()
                                    
                                    cont = 0
                                    mudanca2 = 0
                                    time.sleep(1)
                                    break
                                
                        if cont == 1:

                            log("Chave de mudanca Garagem 2 desligou mas o portao nao fechou após 1 min")

                            l.desliga_rele3_exp2() # Sinal Vermelho

                            t = open("/home/pi/CMM/status_garagem_2.cmm","w")
                            t.write("0")
                            t.close()

                            l.liga_rele4_exp2() # Pulso na Sirene                                            
                            time.sleep(3)
                            l.desliga_rele4_exp2()                                
                            
                            mudanca2 = 0
                            
                            time.sleep(1)

                        time.sleep(1)
                        cont = cont - 1

# Ativar depois de aumentar o tempo do temporizador (tx) para 4 segundos                            
                                        
                if status_tx2 == "0" and pmg2 == 0 and tx2 == 0 and violacao == 0: # Violacao do portao da garagem
                    
                    time.sleep(0.2)                    

                    t = open("/home/pi/CMM/status_garagem_2.cmm","r")
                    status_tx2 = t.read()
                    t.close() 

                    pmg2 = l.leitor2_in1()

                    if pmg2 == 0 and status_tx2 == "0":

                        log("violacao do portao garagem 2")

##                        l.liga_rele4_exp2() # liga sirene
                                                            
##                        evento.enviar("E","132","018")

                        cont = 30 # Tempo maximo de espera

                        log("Aguardando portao garagem 2 fechar apos violacao")

                        while cont > 0:

                            pmg2 = l.leitor2_in1()

                            if(pmg2 == 0): # Portao ainda aberto                                      

                                time.sleep(1)
                                cont = cont - 1
                                    
                            if (pmg2 == 1): # Portao ja fechou

                                log("Portao Garagem 2 fechou apos violacao")

                                t = open("/home/pi/CMM/status_garagem_2.cmm","w")
                                t.write("0")
                                t.close()
                                
                                cont = 0
                                time.sleep(0.2)
                                
                                l.desliga_rele4_exp2() # Desliga sirene
                                
                                break            
                        
                        l.desliga_rele4_exp2() # Desliga sirene

                        violacao = 1
                        
                        time.sleep(1)
                        
                ja_fechou2 = 0
                time.sleep(0.2)

            except Exception as err:

                log("Erro na rotina da garagem 2")
                log(err)
            
    log("Saiu do loop da garagem 2")

g2 = threading.Thread(target=gar2)
g2.start()


def Serv_qr():

    log("Servidor QR em execucao")
        
    servidor_qr.Servidor_qr()

sqr = threading.Thread(target=Serv_qr)
##sqr.start()

# Zera registros para nao abrir porto por eventos que ficaram na memoria

status = open("/home/pi/CMM/status_social.cmm","w") 
status.write("0")
status.close()

status = open("/home/pi/CMM/status_eclusa.cmm","w") 
status.write("0")
status.close()

banco.atualiza("comandos","abre_social_externo","0")
banco.atualiza("comandos","abre_social_interno","0")

banco.atualiza("comandos","reset","0")


def Intertravamento(comando): # Inicia a thread dos portoes sociais importando a classe Rele

        audio = banco.consulta("comandos","audio")
        eventos = banco.consulta("comandos","eventos")
                       
##        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log        
                
        cont = 0

        a = open("/home/pi/CMM/status_social.cmm","r")
        abre_social = a.read()
        a.close()

        b = open("/home/pi/CMM/status_eclusa.cmm","r")
        abre_eclusa = b.read()
        b.close()

        ihm_soc1 = banco.consulta("comandos","abre_social_externo")
        ihm_soc2 = banco.consulta("comandos","abre_social_interno")
    
        if comando == "abre_social":            

            pm1 = entradas.pm1()               
            pm2 = entradas.pm2()

            if pm2 == "0":
                
                log("Agurade o fechamento do Social Externo")
                os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Necessario manter esse audio sempre ativo
                time.sleep(1)
                                
            if pm2 == "1": # Se Ponto magnético Eclusa fechado, pode abrir o social
                                                
                s = open("/home/pi/CMM/status_social.cmm","w")
                s.write("1")
                s.close()

                saidas.liga_blq2() # Aqui abrimos o contato da eclusa para impedir que ela seja aberta enquanto o social esta aberto
              
                social(ihm_soc1)
               
                time.sleep(3) # Tempo minimo para o portao abrir
                   
                pm1 = entradas.pm1()
                                    
                if pm1 == "1": # Portao fechado pois nao abriu com o comando                                      
                    
##                    fechadura = banco.consulta("config","fechadura")

##                    if fechadura == "magnetica":
##
##                        os.system("mpg123 /home/pi/CMM/mp3/empurre.mp3")
##                        
##                        log("Abrindo novamente o social...")
##                        
##                        saidas.pulso_abre1() # Pulso para abrir direto o portao sem intertravamento (Social)
##
##                        saidas.desliga_blq2()
##
##                        status = open("/home/pi/CMM/status_social.cmm","w") 
##                        status.write("0")
##                        status.close()
##
##                        time.sleep(2)
##                        return
                        

##                    if fechadura == "motor":

                    log("Portao Social emperrado")

                    os.system("mpg123 /home/pi/CMM/mp3/social_emperrado.mp3")
                                            
                    saidas.desliga_blq2() # Fecha o contato e libera a eclusa para ser acionada

                    status = open("/home/pi/CMM/status_social.cmm","w") 
                    status.write("0")
                    status.close()

                    time.sleep(2)
                    return

                                           
##                        if eventos == "1":

                    evento.enviar("E","132","008") # Envia portao emperrado                        

                if pm1 == "0": # Portao abriu

##                    if eventos == "1":

                    evento.enviar("E","133","001") # Envia abriu portao
                    
                    contador = 200 # Tempo maximo para o social ficar aberto 30 segundos
                    log("Esperando por 20 segundos o portao Social fechar...")

                    while contador > 0: # enquanto portao esta aberto
                        
                        pm1 = entradas.pm1()
                        
                        if pm1 == "1": # portao fechou

                            log("Portao Social fechou")

##                            if eventos == "1":

                            evento.enviar("R","133","001") # Envia fechamento
                            
                            contador = 0
                                                        
                            s = open("/home/pi/CMM/status_social.cmm","w")
                            s.write("0")
                            s.close()

                            saidas.desliga_blq2() # Fecha o contato e libera a eclusa para ser acionada

                            break

                        if (pm1 == "0" and contador == 1): # Portao ainda aberto após 15 segundos de espera

                            log("Portao Social aberto por muito tempo")

##                            if eventos == "1":

                            evento.enviar("E","132","010") # Envia falha no fechamento social

                            os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                            
                            status = open("/home/pi/CMM/status_social.cmm","w") # Para nao disparar o arrombamento
                            status.write("1")
                            status.close()

                            contador = 0

                            saidas.desliga_blq2() # Fecha o contato e libera a eclusa para ser acionada                                
                           
                        ctw2 = entradas.ctw2()                            
                        
                        if (ctw2 == "1"):# Entrada para abrir o portao da eclusa
                            
                            log("Aguarde o fechamento do Social Externo")
                            os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Necessario manter esse audio sempre ativo
                            time.sleep(1)
                            
                        time.sleep(0.1) # 1 segundo
                        contador = contador - 1                            
            
            pm2 = entradas.pm2()
  
                        
        if comando == "abre_eclusa":            
               
            pm2 = entradas.pm2()
            pm1 = entradas.pm1()

            if pm1 == "1": # Ponto magnético Social fechado, pode abrir a eclusa
                
                s = open("/home/pi/CMM/status_eclusa.cmm","w")
                s.write("1")
                s.close()

                saidas.liga_blq1() # Impede o social de abrir enquanto a eclusa esta aberta
                                
                eclusa(ihm_soc2)                                        
               
                time.sleep(1) # Tempo de espera para o portao abrir
                
                pm2 = entradas.pm2()
                
                if pm2 == "1": # Portao fechado nao abriu após o comando

##                   fechadura = banco.consulta("config","fechadura")
##
##                   if fechadura == "magnetica":
##
##                       os.system("mpg123 /home/pi/CMM/mp3/empurre.mp3")
##
##                       log("Abrindo novamente a eclusa")
##                       
##                       saidas.pulso_abre2()
                       
                   saidas.desliga_blq1()

                   status = open("/home/pi/CMM/status_eclusa.cmm","w") 
                   status.write("0")
                   status.close()

                   time.sleep(1)
                   return

##                   if fechadura == "motor":
##
##                       log("Portao Eclusa emperrado")
##                       
##                       os.system("mpg123 /home/pi/CMM/mp3/eclusa_emperrado.mp3")
##                            
##                       saidas.desliga_blq1() # Libera o social para abrir mesmo com a eclusa aberta
##
##                       status = open("/home/pi/CMM/status_eclusa.cmm","w") 
##                       status.write("0")
##                       status.close()
##                       
##                       if eventos == 1:
##
##                           evento.enviar("E","132","009") # Envia portao emperrado
##
##                       time.sleep(2)
##                       return

                if pm2 == "0": # Portao aberto
                    
##                    if eventos == 1:

                    evento.enviar("E","133","003") # Envia abertura
                    
                    contador = 200 # Tempo maximo para eclusa ficar aberta 20 segundos
                    
                    log("Esperando por 20 segundos o portao Eclusa fechar...")

                    while contador > 0: # enquanto portao esta aberto
                        
                        pm2 = entradas.pm2() 

                        if pm2 == "1": # portao fechou

                            log("Portao Eclusa fechou")

                            saidas.desliga_blq1() # Libera o social para abrir

##                            if eventos == "1":

                            evento.enviar("R","133","003") # Envia fechamento
                            
                            contador = 0
                            
                            s = open("/home/pi/CMM/status_eclusa.cmm","w")
                            s.write("0")
                            s.close()                            

                            break

                        if (pm2 == "0" and contador == 1): # Portao ainda aberto após 15 segundos de espera

                            log("Portao Eclusa aberto por muito tempo")

##                            if eventos == "1":

                            evento.enviar("E","132","011") # Envia falha no fechamento
                            
                            os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                            
                            status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para nao disparar o arrombamento
                            status.write("1")
                            status.close()                                

                            saidas.desliga_blq1() # Libera o social para abrir mesmo com a eclusa aberta

                            contador = 0
                        
                        ctw1 = entradas.ctw1()
                        
                        if (ctw1 == "1"): # Alguem esta tentando abrir o social com a eclusa aberta

                            log("Aguarde o fechamento do Social Interno")
                            os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Manter esse audio sempre ativo
                            time.sleep(1)
                            

                        time.sleep(0.1) # 1 segundo
                        contador = contador - 1
                        
def social(mensagem): # Mensagem informa se o evento veio pelo interface web ou do local

    status = open("/home/pi/CMM/status_social.cmm","w") # Para nao disparar o arrombamento
    status.write("1")
    status.close()

    fechadura = banco.consulta("config","fechadura")
    audio = banco.consulta("config","audio")

    saidas.pulso_abre1() # Pulso para abrir direto o portao sem intertravamento (Social)


    if mensagem == "0": # Fala no local "Abrindo portao social"

        log("Abrindo social...")    

    
    if mensagem == "1": # Via interface web

        log("Abrindo Social pela Central de Monitoramento...")
        os.system("mpg123 /home/pi/CMM/mp3/acionando_pela_central.mp3")    

    if audio == "1":        

        if mensagem == "0":

            if fechadura == "magnetica":

                os.system("mpg123 /home/pi/CMM/mp3/abrindo_social.mp3")                    

    status = open("/home/pi/CMM/status_social.cmm","w") 
    status.write("0")
    status.close()

##    time.sleep(1)
    
def eclusa(mensagem):

    status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para nao disparar o arrombamento
    status.write("1")
    status.close()

    fechadura = banco.consulta("config","fechadura")
    audio = banco.consulta("config","audio")

    

    saidas.liga_abre2() # Pulso para abrir direto o portao sem intertravamento (Eclusa)

    os.system("mpg123 /home/pi/CMM/mp3/portao_aberto.mp3")
        
    log("Narrou empurre a porta para abrir")

    saidas.desliga_abre2()

    

    if mensagem == "0": # local

        log("Abrindo eclusa...")

    if mensagem == "1":

        log("Abrindo Eclusa pela Central de Monitoramento...")
        os.system("mpg123 /home/pi/CMM/mp3/acionando_pela_central.mp3")  

    if audio == "1":

        if mensagem == "0":

            if fechadura == "magnetica":

                os.system("mpg123 /home/pi/CMM/mp3/abrindo_eclusa.mp3")
            
    status = open("/home/pi/CMM/status_eclusa.cmm","w") 
    status.write("0")
    status.close()

##    time.sleep(1)

def Portoes_sociais(Rele): # Programa
    
    log("Programa Sociais em execucao ")

    saida = 0
    qbv_acionado = 0
    banco = cmm.Banco()
##    qbv2 = entradas.qbv2() # Este quebra de vidro abre os dois portões
    arrombamento_1 = 0
    arrombamento_2 = 0
               
    while(1):

        habilita_intertravamento = banco.consulta("intertravamento","habilitado")
                
        pm1 = entradas.pm1()
        pm2 = entradas.pm2()
       
        ctw1 = entradas.ctw1()
        ctw2 = entradas.ctw2()

        qbv1 = entradas.qbv1()
        
        ihm_soc1 = banco.consulta("comandos","abre_social_externo")
        ihm_soc2 = banco.consulta("comandos","abre_social_interno")

        a = open("/home/pi/CMM/status_social.cmm","r")
        abre_soc = a.read()
        a.close()

        b = open("/home/pi/CMM/status_eclusa.cmm","r")
        abre_ecl = b.read()
        b.close()        
            
       
        if ctw1 == "1" and qbv_acionado == 0 or ihm_soc1 == "1" and qbv_acionado == 0:                            

            if habilita_intertravamento == "0":

                log("Intertravamento desabilitado\n")
                
                social(ihm_soc1)

                status = open("/home/pi/CMM/status_social.cmm","w") 
                status.write("0")
                status.close()

            else:

                log("Intertravamento habilitado\n")

                status = open("/home/pi/CMM/status_social.cmm","w")
                status.write("1")
                status.close()
         
                Intertravamento("abre_social")

                status = open("/home/pi/CMM/status_social.cmm","w")
                status.write("0")
                status.close()

            banco.atualiza("comandos","abre_social_externo","0")

            arrombamento_1 = 0
            
        if ctw2 == "1" and qbv_acionado == 0 or ihm_soc2 == "1" and qbv_acionado == 0:            

            if habilita_intertravamento == "0":

                log("Intertravamento desabilitado\n")
                
                eclusa(ihm_soc2) 
                
            else:
                
                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("1")
                status.close()

                Intertravamento("abre_eclusa")

                time.sleep(1) # tempo para evitar violacao eclusa (teste)

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()

                saida = 1

            banco.atualiza("comandos","abre_social_interno","0")

            arrombamento_2 = 0

            time.sleep(1)
                   
        if qbv1 == "1" and qbv_acionado == 0:

            time.sleep(0.2)
            qbv1 = entradas.qbv1()   

            if qbv1 == "1":

                status = open("/home/pi/CMM/status_social.cmm","w")
                status.write("1")
                status.close()

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("1")
                status.close()

                saidas.liga_abre2() # Abre portao interno (fechadura magnetica)
                
                saidas.pulso_abre1() # Abre portao da rua e fecha o foto
                
                saidas.liga_fot_sociais()
                
                log("Acionado o quebra de vidro da Eclusa")                
                os.system("mpg123 /home/pi/CMM/mp3/emergencia.mp3")
                
                evento.enviar("E","132","005")
                
                qbv_acionado = 1

                time.sleep(2)

        if qbv1 == "0" and qbv_acionado == 1:

            time.sleep(0.2)
            qbv1 = entradas.qbv1()

            if qbv1 == "0":

                os.system("mpg123 /home/pi/CMM/mp3/restaurada_emergencia.mp3")

                log("Desligou o quebra de vidro")
                
                saidas.desliga_fot_sociais()
                saidas.desliga_abre2()                

                time.sleep(7) # Tempo pra fechar o portao

                os.system("mpg123 /home/pi/CMM/mp3/automatico.mp3")

                status = open("/home/pi/CMM/status_social.cmm","w")
                status.write("0")
                status.close()

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close() 

                evento.enviar("R","132","005")
                
                qbv_acionado = 0
                
        if abre_soc == "0" and pm1 == "0" and arrombamento_1 == 0 and ctw1 == "0":

            time.sleep(0.2)

            a = open("/home/pi/CMM/status_social.cmm","r")
            abre_soc = a.read()
            a.close()

            pm1 = entradas.pm1()

            if abre_soc == "0" and pm1 == "0":
            
                log("Violacao do portao social")
                os.system("mpg123 /home/pi/CMM/mp3/violacao_social.mp3")
                
                evento.enviar("E","132","002")
                    
                arrombamento_1 = 1

                time.sleep(1)

        if abre_ecl == "0" and pm2 == "0" and arrombamento_2 == 0 and ctw2 == "0":

            time.sleep(2) # Alterado de 0.2 para 2, acompanhar violacoes...

            b = open("/home/pi/CMM/status_eclusa.cmm","r")
            abre_ecl = b.read()
            b.close()
            
            pm2 = entradas.pm2()

            if abre_ecl == "0" and pm2 == "0":

                log("Violacao do portao da eclusa")
                os.system("mpg123 /home/pi/CMM/mp3/violacao_social.mp3")                

                evento.enviar("E","132","004")

                arrombamento_2 = 1

                time.sleep(1)
            
        time.sleep(0.2) 

        
################################################ THREADS ROTINAS #################################################
        
def Arrombamento(Rele): # Inicia a thread arrombamento de portões

    time.sleep(2)
    
    log("Programa arrombamento de portoes sociais em execucao")

    ar1 = 0 # Variavel arrombamento portao 1
    ar2 = 0
    
    reset_ar1 = 0 # Reseta a variavel do portao para 0
    reset_ar2 = 0
    
    segunda_vez1 = 0
    segunda_vez2 = 0
    
    cont1 = 10 # Contador individual para cada reset de arrombamento
    cont2 = 10

    audio = banco.consulta("comandos","audio")
    eventos = banco.consulta("comandos","eventos")

       
    while(1):

        try:
        
            pm1 = entradas.pm1()
            pm2 = entradas.pm2()

            a = open("/home/pi/CMM/status_social.cmm","r")
            abre_social = a.read()
            a.close()

            b = open("/home/pi/CMM/status_eclusa.cmm","r")
            abre_eclusa = b.read()
            b.close()

            if abre_social == "1" or abre_eclusa == "1":

                saidas.desliga_sirene()

            if ar1 == 0 and reset_ar1 == 0 and segunda_vez1 == 1:

                saidas.desliga_sirene()
                segunda_vez1 = 0

            if ar2 == 0 and reset_ar2 == 0 and segunda_vez2 == 1:

                saidas.desliga_sirene()
                segunda_vez2 = 0
                    
            if abre_social == "0" and pm1 == "0" and ar1 == 0:

                time.sleep(1) # Filtra algum possivel ruido de até 500 milissegundos

                a = open("/home/pi/CMM/status_social.cmm","r")
                abre_social = a.read()
                a.close()

                pm1 = entradas.pm1()

                if abre_social == "0" and pm1 == "0": # Se realmente foi um arrombamento liga sirene e notifica o Moni
                    
                    log("Arrombamento do portao social")
                    os.system("mpg123 /home/pi/CMM/mp3/violacao_social.mp3")
                    
                    saidas.liga_sirene()

                    if eventos == "1":

                        evento.enviar("E","132","002")
                    
                    ar1 = 1
                    reset_ar1 = 1

            if ar1 == 1 and reset_ar1 == 1:

                cont1 = cont1 - 1 # A primeira vez que acontece o arrombamento reseta depois de 20 segundos
                time.sleep(1)

                if cont1 == 340:

                    saidas.desliga_sirene()

                if cont1 <= 0:

                    saidas.desliga_sirene()

                    if eventos == "1":

                        evento.enviar("R","132","002")

                    cont1 = 350 # Se apos o reset o portao continuar aberto envia o evento novamente  espera 5 min
                    ar1 = 0
                    reset_ar1 = 0
                    segunda_vez1 = 1

                    saidas.desliga_sirene() # Garantia que esteja desligada
                    
                    

            if abre_eclusa == "0" and pm2 == "0" and ar2 == 0:

                time.sleep(1) # Filtra algum possivel ruido de até 500 milissegundos

                b = open("/home/pi/CMM/status_eclusa.cmm","r")
                abre_eclusa = b.read()
                b.close()

                pm2 = entradas.pm2()

                if abre_eclusa == "0" and pm2 == "0": # Se realmente foi um arrombamento liga sirene e notifica o Moni

                    log("Arrombamento do portao Eclusa")
                    os.system("mpg123 /home/pi/CMM/mp3/violacao_eclusa.mp3")

                    saidas.liga_sirene()

                    if eventos == "1":

                        evento.enviar("E","132","004")
                    
                    ar2 = 1
                    reset_ar2 = 1

            if ar2 == 1 and reset_ar2 == 1:

                cont2 = cont2 - 1 # A primeira vez que acontece o arrombamento reseta depois de 20 segundos
                time.sleep(1)

                if cont2 == 340:

                    saidas.desliga_sirene()

                if cont2 <= 0:

                    saidas.desliga_sirene()

                    if eventos == "1":

                        evento.enviar("R","132","004")

                    cont2 = 350 # Se apos o reset o portao continuar aberto envia o evento novamente e espera 5 min
                    ar2 = 0
                    reset_ar2 = 0
                    segunda_vez2 = 1

                    saidas.desliga_sirene()
            
            time.sleep(1)   

        except Exception as err:

            print("Erro na rotina de alarmes dos sociais")
            txt = ("Erro na rotina de alarmes dos sociais",err)
            log(txt)
            
        time.sleep(5)
        
def alarmes_garagem1():
            
        if pmg1 == "0" and mudanca1 == 0 and status_tx1 == "0": # Violacao do portao da garagem                              

            cont = 10
            violacao = 1
            
            while cont > 0:

                t = open("/home/pi/CMM/status_garagem_1.cmm","r")
                status_tx1 = t.read()
                t.close() 

                pmg1 = l.leitor1_in1()

                if pmg1 == "0" and status_tx1 == "0":

                    violacao = 1
                    
                if pmg1 == "1":
                    
                    violacao = 0
                    break

                time.sleep(0.1)
                cont = cont - 1

##            if violacao == 0: # Filtrou ruido
##
##                pass

            if violacao == 1:

                log("violacao do portao garagem 1")

                l.desliga_rele3_exp1() # Sinal Vermelho

##                l.liga_rele4_exp1() # Sirene
                            
                evento.enviar("E","132","014")

                cont = 30 # Tempo maximo de espera

                log("Aguardando portao fechar")

                while cont > 0:

                    pmg1 = l.leitor1_in1()

                    if(pmg1 == "0"): # Portao ainda aberto                                      

                        time.sleep(1)
                        cont = cont - 1
                            
                    if (pmg1 == "1"): # Portao ja fechou

                        log("Portao fechou")

                        t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                        t.write("0")
                        t.close()


                        
                        cont = 0
                        time.sleep(1)
                        
                        l.desliga_rele4_exp1() # Desliga sirene
                        
                        break            
                
##                l.desliga_rele4_exp1() # Desliga sirene

##                violacao = 0
                
                time.sleep(30)
                
        time.sleep(1)        

def Buffer():

    socket.setdefaulttimeout(3) # limite em segundos para enviar o socket

    host = '172.20.1.5'  # '172.20.1.5' Host servidor  Moni
    port = 4010          # 4010 Porta maquina receptora

    log("Programa buffer de eventos em execucao")

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

                    command = (evento + "\r") # ("7000 185808E30500008")  # Envia abriu portao da eclusa para a central de monitormento
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    log(reply.decode('utf-8'))
                    s.close()

                    enviado = 1                    
                                
                except Exception as err: ## Nao conseguiu enviar o evento, sem conexao no momento                    

                    s.close()

                    time.sleep(10)
                    break
                
                if enviado == 1:
                                               
                    txt = ("Evento enviado ",evento)
                    log(txt)

                    # Cria uma lista e adiciona todos as linhas encontradas em buffer.txt

                    lista = []

                    try:

                        txt = open("/home/pi/CMM/buffer_eventos.txt","r")
                        for l in txt:                        
                            l = l.replace("\n","") # Coloca na lista o evento ja editado
                            lista.append(evento)
                        
                        # Exclui o item enviado da lista

                        for i in lista:
                            
                            if i == evento:
                                indice = lista.index(i)
                                txt = ("Excluindo o evento",evento,"posicao",indice)
                                log(txt)
                                del(lista[indice])
                                nova_lista = lista
                                
                        txt.close()

                        # Zera o arquivo buffer

                        tx = open("/home/pi/CMM/buffer_eventos.txt","w") 
                        tx.close()

                        # Reescreve o texto com a nova lista editada

                        txt = open("/home/pi/CMM/buffer_eventos.txt","a")
                        for i in nova_lista:
                            txt.write(i + "\n")
                        txt.close()    
                            
                        enviado = 0

                    except Exception as err:
                        txt = ("Erro",err)
                        log(txt)
            
        b.close() # Fecha o arquivo de texto em modo leitura    
        time.sleep(1)

############################################### Thread servidor p/ PHP e MONI ###########################################

def Servidor(): 
    
    log("Programa Servidor em execucao")
    socket.setdefaulttimeout(999999) # limite tempo socket
    
    host = '172.18.38.249'
    port = 5510

    time.sleep(0.1)

    log("iniciou o servidor")
    
    txt = ("Servidor: ",host, " porta: ", port)
    log(txt)

    while(1):
            
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


            def dataTransfer(conn):  # Loop de transferencia e recepcao de dados

##                log("Entrou no loop dataTransfer")
                time.sleep(5)

                while True:

                    try:
                                                                              
                        data = conn.recv(1024)  # Recebe o dado
                        data = data.decode('utf-8')
##                        txt = ("data",data)
##                        log(txt)

                        try:
                            
                            dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                            command = dataMessage[0]

                            (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e eoutra em resto

                        except Exception as err:

                            log("Erro na divisao dos dados recebidos")
                       
                        if(comando == "SET 1" or comando == "RESET 1"):
                            
                            mudanca = banco.consulta("comandos","mudanca")

                            if mudanca == "0":

##                                log("Recebeu requisicao para abertura Garagem 2 abastecimento do gas")

                                banco.atualiza("comandos","mudanca","1")
                                
                                evento.enviar("E","132","025")

                                time.sleep(1)

                            if mudanca == "1":

##                                log("Recebeu requisicao para fechamento Garagem 2 abastecimento do gas")

                                banco.atualiza("comandos","mudanca","0")

                                evento.enviar("R","132","025")

                                time.sleep(1)                                                        

                            conn.close()
                            break

                        else:

                            txt = ("Recebido pelo CMM:",comando)
                            log(txt)
                            
                            try:
                        
                                conn.close()

                            except Exception as err:

                                msg = ("Erro no fechamento da conexao A",err)
                                log(msg)

                            break
                            
                    except Exception as err:

                        log(err)

                        try:
                        
                            conn.close()

                        except Exception as err:

                            msg = ("Erro no fechamento da conexao B",err)
                            log(msg)


            s = setupServer()

            while True:
                
              time.sleep(1) 

              txt = ("Escutando na porta",port)
              log(txt)
              try:

                  conn = setupConnection()
                  dataTransfer(conn)
##                  log("Tchau")


              except Exception as err:

                  log("Encerrou conexao")
                    
        
#################### Instancia as Classes  #############################################

intertravamento = Intertravamento(cmm.Rele)


####################  Declara as threads dos programas disponiveis  ####################

sociais = threading.Thread(target=Portoes_sociais, args=(cmm.Rele,)) # deixar virgula depois do arg 1
##garagem1 = threading.Thread(target=Garagem1, args=(cmm.Rele,))
##garagem2 = threading.Thread(target=Garagem2, args=(cmm.Rele,))
arrombamento = threading.Thread(target=Arrombamento, args=(cmm.Rele,))
servidor = threading.Thread(target=Servidor)
#servidor_qr = threading.Thread(target=Servidor_qr)

buffer = threading.Thread(target=Buffer)


######################################### Start dos Programas  #############################################################

sociais.start() # Inicia o programa dos portões sociais

##garagem1.start() # Inicia o programa do portao de garagem
##garagem2.start() # Inicia o programa do portao de garagem
##arrombamento.start() # Inicia o programa de automacao
servidor.start()
##servidor_qr.start() 
##buffer.start() # Inicia o programa Buffer


time.sleep(0.2) # Tempo para colocar as linhas impressas após as linhas de inicio de programa



log("Temperatura processador " + str(temperatura.cpu()) + " C\n")  # obter temperatura

def clima(lugar):

    r = ("http://api.openweathermap.org/data/2.5/weather?q=%s,BR&lang=pt&units=metric&APPID=dd7227b5df6988b8ba34bffd5b6e3450")%lugar
    
    data = request.urlopen(r)
    html = data.read()
    html = html.decode('utf-8')

    html = html.replace("b'","")

    weather = json.loads(html)

    print(weather)

    temperatura = (weather['main']['temp'])
    temperatura = round(temperatura)
    temperatura = str(temperatura)

    nebulosidade = str(weather['clouds']['all'])

    umidade = str(weather['main']['humidity'])

    cidade = str(weather['name'])

    tempo = weather['weather']
    tempo = tempo[0]
    tempo = tempo['description']


    feed_back_clima = str("Em " + cidade + " " + tempo + " e " + temperatura + " graus")

        
    print(feed_back_clima)

try:

    log("*")    
    log("O Sistema esta conectado a internet")
    tempo = clima("Presidente Prudente")
    tempo = str(tempo)
    log(tempo)
    narrador.falar(tempo)
    
except:

    pass

##    os.system("mpg123 /home/pi/CMM/mp3/sem_internet.mp3")
##    log("Sistema sem conexao a internet no momento")

while(1):

    reset = banco.consulta("comandos","reset")

    if reset == "1":

        banco.atualiza("comandos","reset","0")
        
        log("Reiniciando o sistema, aguarde...")

        os.system("mpg123 /home/pi/CMM/mp3/reiniciando_sistema.mp3")

        os.system("sudo reboot now")

    # Colocar aqui o keep alive  
    

    time.sleep(2)

