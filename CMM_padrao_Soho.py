#!/usr/bin/env python3
# coding=UTF-8

# Para iniciar o programa via supervisor sudo supervisorctl start cmm

# CMM Oficial com placa de expansão da BRAVAS Technololgy
# Desenvolvido por Leandro Leal  rev. 05/11/2019

import RPi.GPIO as GPIO
import time
import biblioteca_CMM as cmm
import cmm_io_entradas as entradas # Entradas digitais fotoacopladas configuradas na interface
import cmm_io_saidas as saidas # Saidas (Rele e transistor) configuradas na interface

##from atualiza_monitor import Monitor # Para atualização do monitor da interface grááááááfica
from expansores import Leitor # teste com uma unica classe com a leitura e acionamento
import servidor_qr as servidor_qr # Servidor para receber cadastros de qrcodes vindas do gerenviador (Servidor Central)

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

os.system("sudo chmod 777 /dev/ttyS0") # Altera a permissão do acesso a serial

os.system("sudo chmod 777 -R /var/www/html/log") # Permissão para escrever no log

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
email = cmm.Email()
clima = cmm.Clima()
banco = cmm.Banco() # Oprerações CRUD no banco CMM
##cliente = banco.consulta("config","cliente")
evento = cmm.Evento("6653") # Inicia a classe evento com o codigo do cliente

###############################################################################################################

def thread_monitor(): # Programa que mantem a conexão com o QR Code

    print("\nPrograma Monitor em execução\n")

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
                
        while(1):

            try:
            

                hs = time.strftime("%H:%M:%S")            
            
                ihm_gar1 = banco.consulta("comandos","abre_garagem1") # Valor inserido pelo botão da interface       
                tx1 =  l.leitor1_in3()  # Cantato abre vindo do TX (LINEAR HCS)

                mud1 = l.leitor1_in4()  # Chave de mudança

                t = open("/home/pi/CMM/status_garagem_1.cmm","r")
                status_tx1 = t.read()
                t.close()
                           
                            
                if (tx1 == 1 or ihm_gar1 == "1"):   

                    time.sleep(0.1)                
                    tx1 =  l.leitor1_in3()                                

                    if (tx1 == 1 or ihm_gar1 == "1"): # O tx da linear está direto no abre do portão
                                                
                        time.sleep(0.1)
                        tx1 = l.leitor1_in3()

                        if tx1 == 1 :

                            log("*")
                            log("Reconheceu tx Garagem 1") # Se reconheceu o tx, é porque o portão ja esta abrindo

                            l.liga_rele3_exp1() # Sinal Verde (Sinaleira)    

                            status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                            status.write("1")
                            status.close()

    ##                        time.sleep(1)

                        if ihm_gar1 == "1": # Abre através do expansor (rele 1)

                            log("*")
                            log("Reconheceu abre Garagem 1 Interface gráfica")

                            l.liga_rele3_exp1() # Sinal Verde (Sinaleira)

                            status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                            status.write("1")
                            status.close()

                            l.liga_rele1_exp1() # Pulso para abrir a garagem
                            time.sleep(2)
                            l.desliga_rele1_exp1()

    ##                        time.sleep(1)

    ##                    banco.atualiza("comandos","abre_garagem1","0")                    

                        time.sleep(2) # Tempo para começar a abrir o portão

                        tentando1 = 3

                        while tentando1 > 0:

                            pmg1 = l.leitor1_in1()
                            tx1 =  l.leitor1_in3() 
                            
                            if pmg1 == 1 and tx1 == 1: # Portão não abriu apos o comando

                                time.sleep(0.1)
                                pmg1 = l.leitor1_in1()

                                if pmg1 == 1: # Portão não abriu apos o comando

                                    time.sleep(0.1)
                                    pmg1 = l.leitor1_in1()

                                    if pmg1 == 1:

                                        log("Portão Garagem 1 não abriu")

                                        l.desliga_rele3_exp1() # Sinal Vermelho                            

    ##                                    if eventos == "1":
    ##                                    
    ##                                        evento.enviar("E","132","015") # Emperrado
    ##
                                        banco.atualiza("comandos","abre_garagem1","0")
                                        
                                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                        status.write("0")
                                        status.close()                                               
                                        

                            if pmg1 == 0: # Portão abriu

                                time.sleep(0.1)                    
                                pmg1 = l.leitor1_in1()

                                if pmg1 == 0: # Confirmado que o Portão abriu

                                    time.sleep(0.1)                    
                                    pmg1 = l.leitor1_in1()

                                    if pmg1 == 0:                                

                                        if eventos == "1":
                                            
                                            evento.enviar("E","133","013")
                                            
                                        cont1 = 400     # Tempo maximo para deixar 300 = 30 segundos and 

                                        while cont1 > 0:   # Enquanto o portão esta aberto verifica

                                            if cont1 == 400:

                                                log("Portão Garagem 1 abriu")
                                                
                                                l.liga_rele3_exp1() # Sinal verde
                                                
                                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                status.write("1")
                                                status.close()

                                                time.sleep(2)
                                            
                                            pmg1 = l.leitor1_in1()
                                            
                                            if pmg1 == 1 and ja_fechou1 == 0: # Se o portão ja fechou

                                                time.sleep(0.1)
                                                pmg1 = l.leitor1_in1()

                                                if pmg1 == 1:

                                                    time.sleep(0.1)
                                                    pmg1 = l.leitor1_in1()

                                                    if pmg1 == 1:

                                                        log("Portão Garagem 1 fechou C")

                                                        l.desliga_rele3_exp1() # Sinal Vermelho

                                                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                        status.write("0")
                                                        status.close()
                                                        
                                                        if eventos == "1":
                                                            
                                                            evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                        
                                                        cont1 = 0
                                                        tentando1 = 0
                                                        
                                                        ja_fechou1 = 1
                                                        banco.atualiza("comandos","abre_garagem1","0")  
                                                        
                                                        break                                            
                                                
                                            if pmg1 == 0: # Se o portão ainda esta aberto

                                                time.sleep(0.1)
                                                pmg1 = l.leitor1_in1()

                                                if pmg1 == 0:

                                                    time.sleep(0.1)
                                                    pmg1 = l.leitor1_in1()

                                                    if pmg1 == 0:

                                                        cont2 = 400     # Tempo maximo para deixar 300 = 30 segundos

                                                        while cont2 > 0:   # Enquanto o portão esta aberto verifica

                                                            if cont2 == 400:

                                                                log("Portão Garagem 1 aberto...")
                                                                                                            
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
                                                                        l.desliga_rele3_exp1() # Sinal Vermelho

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
                                                                                    log("Portão Garagem 1 fechou A")
        ##
                                                                                    l.desliga_rele3_exp1() # Sinal Vermelho
        ##
                                                                                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                                    status.write("0")
                                                                                    status.close()

                                                                                    if eventos == "1":
                                                                                    
                                                                                        evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                                                    
                                                                                    cont2 = 0
                                                                                    
                                                                                    ja_fechou1 = 1
                                                                                    banco.atualiza("comandos","abre_garagem1","0")
                                                                                    
                                                                                    break
                                                                                
                                                                            if tempo == 1:

                                                                                log("Portão Garagem 1 aberto por muito tempo")

                                                                                l.desliga_rele3_exp1() # Sinal Vermelho

                                                                                l.liga_rele4_exp1() # Sirene                                            
                                                                                time.sleep(3)
                                                                                l.desliga_rele4_exp1()

                                                                                if eventos == "1":

                                                                                    evento.enviar("E","132","026") # Envia obstruçao

                                                                                if eventos == "0":

                                                                                    print("Reconheceu que eventos esta desligado neste nivel")

                                                                                banco.atualiza("comandos","abre_garagem1","0")

                                                                                break

                                                                            tempo = tempo - 1
                                                                            time.sleep(1)

                                                                    pmg1 = l.leitor1_in1()                                                                                                
                                                                    
                                                                    if pmg1 == 0: # Portão ainda aberto

                                                                        time.sleep(0.1)                                                        
                                                                        pmg1 = l.leitor1_in1() # Faz a leitura do ponto magnetico                                        

                                                                        if pmg1 == 0:

                                                                            log("Aguardando 30 segundos portão Garagem 1 fechar")

                                                                            temp = 300
                                                                            entrada_permitida = 0
                                                                            ja_fechou1 = 0

                                                                            time.sleep(1)

                                                                            while temp > 0:  # Enquanto o portão ainda está aberto e tempo menor que 30 seg
                                                                                
                                                                                pmg1 = l.leitor1_in1() # Faz a leitura do ponto magnetico
                                                                                bar1 = l.leitor1_in2() # Faz a leitura da barreira 1
                                                                                tx1 =  l.leitor1_in3()  # Cantato abre vindo do TX (LINEAR HCS)

                                                                                if tx1 == 1: # Alguem acionou o controle enquanto o portão fechava

                                                                                    time.sleep(0.1)                                                                    
                                                                                    tx1 =  l.leitor1_in3()

                                                                                    if tx1 == 1:

                                                                                        time.sleep(0.1)                                                                    
                                                                                        tx1 =  l.leitor1_in3()

                                                                                        if tx1 == 1:

                                                                                            log("Reconheceu abre Garagem 1 enquanto o portão estava aberto")                                                    
                                                                                            l.liga_rele3_exp1() # Sinal Verde

                                                                                            entrada_permitida = 1 # Reconhece o segundo acionamento
                                                                                                                                                                                                                                                            
            ##                                                                                break # Sai da função e inicia novamente a verificação

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
         
                                                                                                log("Portão Garagem 1 fechou. A")

                                                                                                l.desliga_rele3_exp1() # Sinal Vermelho

                                                                                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                                                status.write("0")
                                                                                                status.close()

                                                                                                if eventos == "1":
                                                                                                
                                                                                                    evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                                                                
                                                                                                cont2 = 0
                                                                                                temp2 = 0

                                                                                                ja_fechou1 = 1
                                                                                                banco.atualiza("comandos","abre_garagem1","0")  
                                                                                                
                                                                                                break
                                                                                            
                                                                                            if tempo2 == 1:

                                                                                                log("Portão do segundo veiculo aberto por muito tempo")

                                                                                                l.desliga_rele3_exp1() # Sinal Vermelho

                                                                                                l.liga_rele4_exp1() # Sirene                                            
                                                                                                time.sleep(3)
                                                                                                l.desliga_rele4_exp1()

                                                                                                if eventos == "1":

                                                                                                    evento.enviar("E","132","026") # Envia obstruçao

                                                                                                if eventos == "0":

                                                                                                    print("Reconheceu que eventos esta desligado neste nivel 2")

                                                                                                tempo2 = 1
                                                                                            
                                                                                            tempo2 = tempo2 - 1
                                                                                            time.sleep(1)                                       

                                                                                   
                                                                                if bar1 == 1 and entrada_permitida == 0: # Dupla passagem
                                                                                    
                                                                                    time.sleep(0.1)                                                                    
                                                                                    bar1 = l.leitor1_in2()

                                                                                    if bar1 == 1:

                                                                                        if bar1 == 1 and entrada_permitida == 0: # Dupla passagem
                                                                                    
                                                                                            time.sleep(0.1)                                                                    
                                                                                            bar1 = l.leitor1_in2()

                                                                                            log("Dupla passagem Garagem 1")

                                                                                            l.desliga_rele3_exp1() # Sinal Vermelho

                                                                                            if eventos == "1":

                                                                                                evento.enviar("E","132","016")

                                                                                            l.liga_rele4_exp1() # Sirene                                            
                                                                                            time.sleep(10)
                                                                                            l.desliga_rele4_exp1()                                            

                                                                                            break
                                                                                    
                                                                         
                                                                                if pmg1 == 1 and ja_fechou1 == 0: # portão ja fechou

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

                                                                                            if eventos == "1":
                                                                                            
                                                                                                evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                                                            
                                                                                            temp = 0
                                                                                            cont2 = 0

                                                                                            ja_fechou1 = 1
                                                                                            banco.atualiza("comandos","abre_garagem1","0")

                                                                                            log("Portão Garagem 1 fechou E")
                                                                                            
                                                                                            break                                                                                                                                                     

                                                                                if temp == 1:

                                                                                    log("Portão Garagem 1 aberto por muito tempo")

                                                                                    l.desliga_rele3_exp1() # Sinal Vermelho

                                                                                    l.liga_rele4_exp1() # Sirene                                            
                                                                                    time.sleep(3)
                                                                                    l.desliga_rele4_exp1()

                                                                                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                                    status.write("0")
                                                                                    status.close()

                                                                                    if eventos == "1":

                                                                                        evento.enviar("E","132","026") # Envia obstruçao

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

                                                                        log("Portão Garagem 1 fechou B")
        ##
                                                                        l.desliga_rele3_exp1() # Sinal Vermelho
        ##
                                                                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                                                        status.write("0")
                                                                        status.close()

                                                                        if eventos == "1":
                                                                        
                                                                            evento.enviar("R","133","013") # Envia o evento de fechamento para a central
                                                                        
                                                                        cont2 = 0

                                                                        ja_fechou1 = 1

                                                                        banco.atualiza("comandos","abre_garagem1","0")
                                                                        
                                                                        break
                                                                                        
                                                            if cont2 == 1 and ja_fechou1 == 0:

                                                                log("Atingiu o tempo máximo e o portão da Garagem 1 não fechou")

                                                                l.desliga_rele3_exp1() # Sinal Vermelho

                                                                l.liga_rele4_exp1() # Sirene                                            
                                                                time.sleep(3)
                                                                l.desliga_rele4_exp1()

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

                                                log("Atingiu o tempo máximo e o portão da Garagem 1 não fechou")

                                                l.desliga_rele3_exp1() # Sinal Vermelho

                                                l.liga_rele4_exp1() # Sirene                                            
                                                time.sleep(3)
                                                l.desliga_rele4_exp1()

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

                                log ("Recebeu comando para abrir Garagem 1 mas o portão nao abriu")
                                
                                l.desliga_rele3_exp1() # Sinal Vermelho
                                
                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                status.write("0")
                                status.close()

                                ja_fechou1 = 0                        
                                banco.atualiza("comandos","abre_garagem1","0")

                            tentando1 = tentando1 - 1
                            time.sleep(0.2)
                            
    ##                        print("Tentando novamente 3 vezes, Garagem 1")

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
                
        while(1):

            try:

                hs = time.strftime("%H:%M:%S")            
            
                ihm_gar2 = banco.consulta("comandos","abre_garagem2") # Valor inserido pelo botão da interface       
                tx2 =  l.leitor2_in3()  # Cantato abre vindo do TX (LINEAR HCS)

                mud2 = l.leitor2_in4()  # Chave de mudança

                t = open("/home/pi/CMM/status_garagem_2.cmm","r")
                status_tx2 = t.read()
                t.close()
                           
                            
                if (tx2 == 1 or ihm_gar2 == "1"):   

                    time.sleep(0.1)                
                    tx2 =  l.leitor2_in3()                               

                    if (tx2 == 1 or ihm_gar2 == "1"): # O tx da linear está direto no abre do portão

                        time.sleep(0.1)
                        tx2 = l.leitor2_in3()

                        if tx2 == 1 :

                            log("*")
                            log("Reconheceu tx Garagem 2") # Se reconheceu o tx, é porque o portão ja esta abrindo

                            l.liga_rele3_exp2() # Sinal Verde (Sinaleira)    

                            status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                            status.write("1")
                            status.close()

    ##                        time.sleep(1)

                        if ihm_gar2 == "1": # Abre através do expansor (rele 1)

                            log("*")
                            log("Reconheceu abre Garagem 2 Interface gráfica")

                            l.liga_rele3_exp2() # Sinal Verde (Sinaleira)

                            status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                            status.write("1")
                            status.close()

                            l.liga_rele1_exp2() # Pulso para abrir a garagem
                            time.sleep(2)
                            l.desliga_rele1_exp2()

    ##                        time.sleep(1)

    ##                    banco.atualiza("comandos","abre_garagem2","0")                    

                        time.sleep(2) # Tempo para começar a abrir o portão

                        tentando2 = 3

                        while tentando2 > 0:

                            pmg2 = l.leitor2_in1()
                            tx2 = l.leitor2_in3()
                            
                            if pmg2 == 1 and tx2 == 1: # Portão não abriu apos o comando

                                time.sleep(0.1)
                                pmg2 = l.leitor2_in1()

                                if pmg2 == 1: # Portão não abriu apos o comando

                                    time.sleep(0.1)
                                    pmg2 = l.leitor2_in1()

                                    if pmg2 == 1:

                                        log("Portão Garagem 2 não abriu")

                                        l.desliga_rele3_exp2() # Sinal Vermelho                            

    ##                                    if eventos == "1":
    ##                                    
    ##                                        evento.enviar("E","132","019") # Emperrado
    ##
                                        banco.atualiza("comandos","abre_garagem2","0")
                                        
                                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                        status.write("0")
                                        status.close()                                               
                                        

                            if pmg2 == 0: # Portão abriu

                                time.sleep(0.1)                    
                                pmg2 = l.leitor2_in1()

                                if pmg2 == 0: # Confirmado que o Portão abriu

                                    time.sleep(0.1)                    
                                    pmg2 = l.leitor2_in1()

                                    if pmg2 == 0:                                

                                        if eventos == "1":
                                            
                                            evento.enviar("E","133","017")
                                            
                                        cont1 = 400     # Tempo maximo para deixar 300 = 30 segundos

                                        while cont1 > 0:   # Enquanto o portão esta aberto verifica

                                            if cont1 == 400:

                                                log("Portão Garagem 2 abriu")
                                                
                                                l.liga_rele3_exp2() # Sinal verde
                                                
                                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                status.write("1")
                                                status.close()

                                                time.sleep(2)
                                            
                                            pmg2 = l.leitor2_in1()
                                            
                                            if pmg2 == 1 and ja_fechou2 == 0: # Se o portão ja fechou

                                                time.sleep(0.1)
                                                pmg2 = l.leitor2_in1()

                                                if pmg2 == 1:

                                                    time.sleep(0.1)
                                                    pmg2 = l.leitor2_in1()

                                                    if pmg2 == 1 :

                                                        log("Portão Garagem 2 fechou")

                                                        l.desliga_rele3_exp2() # Sinal Vermelho

                                                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                        status.write("0")
                                                        status.close()
                                                        
                                                        if eventos == "1":
                                                            
                                                            evento.enviar("R","133","017") # Envia o evento de fechamento para a central
                                                        
                                                        cont1 = 0
                                                        
                                                        ja_fechou2 == 1
                                                        banco.atualiza("comandos","abre_garagem2","0")

                                                        time.sleep(1)
                                                        
                                                        break                                            
                                                
                                            if pmg2 == 0: # Se o portão ainda esta aberto

                                                time.sleep(0.1)
                                                pmg2 = l.leitor2_in1()

                                                if pmg2 == 0:

                                                    time.sleep(0.1)
                                                    pmg2 = l.leitor2_in1()

                                                    if pmg2 == 0:

                                                        cont2 = 400     # Tempo maximo para deixar 300 = 30 segundos

                                                        while cont2 > 0:   # Enquanto o portão esta aberto verifica

                                                            if cont2 == 400:

                                                                log("Portão Garagem 2 aberto...")
                                                        
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
                                                                        l.desliga_rele3_exp2() # Sinal Vermelho

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
                                                                                    log("Portão Garagem 2 fechou A")
        ##
                                                                                    l.desliga_rele3_exp2() # Sinal Vermelho
        ##
                                                                                    status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                                    status.write("0")
                                                                                    status.close()

                                                                                    if eventos == "1":
                                                                                    
                                                                                        evento.enviar("R","133","017") # Envia o evento de fechamento para a central
                                                                                    
                                                                                    cont2 = 0
                                                                                    
                                                                                    ja_fechou2 = 1
                                                                                    banco.atualiza("comandos","abre_garagem2","0")

                                                                                    time.sleep(1)
                                                                                    
                                                                                    break
                                                                                
                                                                            if tempo == 1:

                                                                                log("Portão Garagem 2 aberto por muito tempo")

                                                                                l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                l.liga_rele4_exp2() # Sirene                                            
                                                                                time.sleep(3)
                                                                                l.desliga_rele4_exp2()

                                                                                if eventos == "1":

                                                                                    evento.enviar("E","132","027") # Envia obstruçao

                                                                                if eventos == "0":

                                                                                    print("Reconheceu que eventos esta desligado neste nivel g2")

                                                                                banco.atualiza("comandos","abre_garagem2","0")

                                                                                break

                                                                            tempo = tempo - 1
                                                                            time.sleep(1) 
                                                                    
                                                                    pmg2 = l.leitor2_in1() # Faz a leitura do ponto magnetico                                    
                                                                    
                                                                    if pmg2 == 0: # Portão ainda aberto

                                                                        time.sleep(0.1)                                                        
                                                                        pmg2 = l.leitor2_in1() # Faz a leitura do ponto magnetico                                        

                                                                        if pmg2 == 0:

                                                                            log("Aguardando 30 segundos portão Garagem 2 fechar")

                                                                            temp = 300
                                                                            entrada_permitida = 0
                                                                            ja_fechou2 = 0

                                                                            time.sleep(1)

                                                                            while temp > 0:  # Enquanto o portão ainda está aberto e tempo menor que 30 seg
                                                                                
                                                                                pmg2 = l.leitor2_in1() # Faz a leitura do ponto magnetico
                                                                                bar2 = l.leitor2_in2() # Faz a leitura da barreira 1
                                                                                tx2 =  l.leitor2_in3()  # Cantato abre vindo do TX (LINEAR HCS)

                                                                                if tx2 == 1: # Alguem acionou o controle enquanto o portão fechava

                                                                                    time.sleep(0.1)                                                                    
                                                                                    tx2 =  l.leitor2_in3()

                                                                                    if tx2 == 1:

                                                                                        time.sleep(0.1)                                                                    
                                                                                        tx2 =  l.leitor2_in3()

                                                                                        if tx2 == 1:

                                                                                            log("Reconheceu abre Garagem 2 enquanto o portão estava aberto")                                                    
                                                                                            l.liga_rele3_exp2() # Sinal Verde

                                                                                            entrada_permitida = 1 # Reconhece o segundo acionamento
                                                                                                                                                                                                                                                            
            ##                                                                                break # Sai da função e inicia novamente a verificação

                                                                                if bar2 == 1 and entrada_permitida == 1:
                                                                                    
                                                                                    time.sleep(0.1)                                                                    
                                                                                    bar2 = l.leitor2_in2()
                                                                                    
                                                                                    if bar2 == 1:

                                                                                        tempo2 = 60

                                                                                        while tempo2 > 0: # Enquanto a barreira esta acionada

                                                                                            bar2 = l.leitor2_in2() # Faz a leitura da barreira 1                                                                                                                                                                                                                                                       

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
                                                                                                        time.sleep(1)

                                                                                            if pmg2 == 1 and ja_fechou2 == 0:
         
                                                                                                log("Portão Garagem 2 fechou. E")

                                                                                                l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                                                status.write("0")
                                                                                                status.close()

                                                                                                if eventos == "1":
                                                                                                
                                                                                                    evento.enviar("R","133","017") # Envia o evento de fechamento para a central
                                                                                                
                                                                                                cont2 = 0
                                                                                                temp = 0

                                                                                                ja_fechou2 = 1
                                                                                                banco.atualiza("comandos","abre_garagem2","0")

                                                                                                time.sleep(1)
                                                                                                
                                                                                                break
                                                                                                        
                                                                                            if tempo2 == 1:

                                                                                                log("Portão do segundo veiculo aberto por muito tempo Garagem 2 ")

                                                                                                l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                                l.liga_rele4_exp2() # Sirene                                            
                                                                                                time.sleep(3)
                                                                                                l.desliga_rele4_exp2()

                                                                                                if eventos == "1":

                                                                                                    evento.enviar("E","132","027") # Envia obstruçao

                                                                                                if eventos == "0":

                                                                                                    print("Reconheceu que eventos esta desligado neste nivel 2 g2")

                                                                                                tempo2 = 1
                                                                                            
                                                                                            tempo2 = tempo2 - 1
                                                                                            time.sleep(1)                                       

                                                                                   
                                                                                if bar2 == 1 and entrada_permitida == 0: # Dupla passagem
                                                                                    
                                                                                    time.sleep(0.1)                                                                    
                                                                                    bar2 = l.leitor2_in2()

                                                                                    if bar2 == 1:

                                                                                        if bar2 == 1 and entrada_permitida == 0: # Dupla passagem
                                                                                    
                                                                                            time.sleep(0.1)                                                                    
                                                                                            bar2 = l.leitor2_in2()

                                                                                            log("Dupla passagem Garagem 2")
                                                                                            
                                                                                            l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                            if eventos == "1":

                                                                                                evento.enviar("E","132","020")

                                                                                            l.liga_rele4_exp2() # Sirene                                            
                                                                                            time.sleep(10)
                                                                                            l.desliga_rele4_exp2()                                            

                                                                                            break
                                                                                    
                                                                         
                                                                                if pmg2 == 1 and ja_fechou2 == 0: # portão ja fechou

                                                                                    time.sleep(0.1)                                                                    
                                                                                    pmg2 = l.leitor2_in1()

                                                                                    if pmg2 == 1:

                                                                                        time.sleep(0.1)                                                                    
                                                                                        pmg2 = l.leitor2_in1()

                                                                                        if pmg2 == 1:
                                                                                            
                                                                                            l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                            log("Portão Garagem 2 fechou C")

                                                                                            status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                                            status.write("0")
                                                                                            status.close()

                                                                                            if eventos == "1":
                                                                                            
                                                                                                evento.enviar("R","133","017") # Envia o evento de fechamento para a central

                                                                                            ja_fechou2 = 1
                                                                                            
                                                                                            temp = 0
                                                                                            banco.atualiza("comandos","abre_garagem2","0")

                                                                                            time.sleep(1)
                                                                                            
                                                                                            break
                                                                                        
                                                                                    
                                                                                if temp == 1:

                                                                                    log("Portão Garagem 2 aberto por muito tempo")

                                                                                    l.desliga_rele3_exp2() # Sinal Vermelho

                                                                                    l.liga_rele4_exp2() # Sirene                                            
                                                                                    time.sleep(3)
                                                                                    l.desliga_rele4_exp2()

                                                                                    status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                                    status.write("0")
                                                                                    status.close()

                                                                                    if eventos == "1":

                                                                                        evento.enviar("E","132","027") # Envia obstruçao

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

                                                                        log("Portão Garagem 2 fechou B")

                                                                        l.desliga_rele3_exp2() # Sinal Vermelho

                                                                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                                                        status.write("0")
                                                                        status.close()

                                                                        if eventos == "1":
                                                                        
                                                                            evento.enviar("R","133","017") # Envia o evento de fechamento para a central
        ##                                                                
                                                                        cont2 = 0

                                                                        ja_fechou2 = 1

                                                                        banco.atualiza("comandos","abre_garagem2","0")

                                                                        time.sleep(1)
                                                                        
                                                                        break
                                                                                        
                                                            if cont2 == 1 and ja_fechou2 == 0:

                                                                log("Atingiu o tempo máximo e o portão da Garagem 2 não fechou")

                                                                l.desliga_rele3_exp2() # Sinal Vermelho

                                                                l.liga_rele4_exp2() # Sirene                                            
                                                                time.sleep(3)
                                                                l.desliga_rele4_exp2()

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

                                                log("Atingiu o tempo máximo e o portão da Garagem 2 não fechou")

                                                l.desliga_rele3_exp2() # Sinal Vermelho

                                                l.liga_rele4_exp2() # Sirene                                            
                                                time.sleep(3)
                                                l.desliga_rele4_exp2()

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

                                log ("Recebeu comando para abrir Garagem 2 mas o portão no abriu")
                                
                                l.desliga_rele3_exp2() # Sinal Vermelho
                                
                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                status.write("0")
                                status.close()

                                ja_fechou2 = 0
                                banco.atualiza("comandos","abre_garagem2","0")

                            tentando2 = tentando2 - 1
                            time.sleep(0.2)
                            
##                            print("Tentando novamente por 3 vezes Garagem 2...")
                            
                if mud2 == 1 and mudanca2 == 0 : # Chave de mudança acionada

                    time.sleep(0.1)     
                    mud2 = l.leitor2_in4()  # Chave de mudança            

                    if mud2 == 1:

                        time.sleep(0.1)     
                        mud2 = l.leitor2_in4()  # Chave de mudança            

                        if mud2 == 1:

                            log("*")
                            log("Chave de mudança acionada Garagem 2")

                            l.liga_rele3_exp2() # Sinal Verde

                            if evento == "1":

                                evento.enviar("E","132","25")                

                            t = open("/home/pi/CMM/status_garagem_2.cmm","w")
                            t.write("1")
                            t.close()

                            l.liga_rele1_exp2() # Aciona o rele 1 do modulo 1 (Abre)
                            time.sleep(2)
                            l.desliga_rele1_exp2()
                            l.liga_rele2_exp2() # Aciona o rele 2 do modulo 1 (Foto)                

                            mudanca2 = 1

                            time.sleep(2)

                if mud2 == 0 and mudanca2 == 1:

                    time.sleep(0.1)
                    mud2 = l.leitor2_in4()

                    if mud2 == 0:

                        time.sleep(0.1)
                        mud2 = l.leitor2_in4()

                        if mud2 == 0:

                            log("Desligada a chave de mudança")

                            l.desliga_rele3_exp2() # Sinal Vermelho

                            if evento == "1":

                                evento.enviar("R","132","25")
                                            
                            l.desliga_rele1_exp2() # Desliga o rele 1 do modulo 1 (Abre)
                            l.desliga_rele2_exp2() # Desliga o rele 2 do modulo 1 (Foto) 

                            pmg2 = l.leitor2_in1()

                            cont = 60 # Tempo maximo de espera

                            log("Aguardando portão Garagem 2 fechar depois da mudanca")

                            time.sleep(2)

                            while cont > 0:
                                
                                pmg2 = l.leitor2_in1()                                                              
                                        
                                if pmg2 == 1: # Portão ja fechou

                                    time.sleep(0.1)
                                    pmg2 = l.leitor2_in1()

                                    if pmg2 == 1:

                                        time.sleep(0.1)
                                        pmg2 = l.leitor2_in1()

                                        if pmg2 == 1 :

                                            log("Portão Garagem 2 fechou depois da mudança")

                                            l.desliga_rele3_exp2() # Sinal Vermelho

                                            t = open("/home/pi/CMM/status_garagem_2.cmm","w")
                                            t.write("0")
                                            t.close()
                                            
                                            cont = 0
                                            mudanca2 = 0
                                            time.sleep(1)
                                            break
                                        
                                if cont == 1:

                                    log("Chave de mudança Garagem 2 desligou mas o portão nao fechou após 1 min")

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

                ja_fechou2 = 0
                time.sleep(0.2)

            except Exception as err:

                log("Erro na rotina da garagem 2")
                log(err)
            
    log("Saiu do loop da garagem 2")

g2 = threading.Thread(target=gar2)
g2.start()


def Serv_qr():

    log("Servidor QR em execução")
        
    servidor_qr.Servidor_qr()

sqr = threading.Thread(target=Serv_qr)
sqr.start()

# Zera registros para não abrir porto por eventos que ficaram na memoria

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
                       
        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log        
                
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
            
##            pm1 = entradas.pm1()
##                                            
##            if pm1 == "0": # O portão social já esta aberto
##
##                time.sleep(0.1)
##                pm1 = entradas.pm1()
##
##                if pm1 == "0":
##                    
##                    log("O portão Social já esta aberto")
##                                
##                    os.system("mpg123 /home/pi/CMM/mp3/social_aberto.mp3")
##                    time.sleep(1)

##            else: # Se o portão Social esta fechado então pode abrir

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
               
                time.sleep(1) # Tempo minimo para o portão abrir
                   
                pm1 = entradas.pm1()
                                    
                if pm1 == "1": # Portão fechado pois não abriu com o comando                                      
                    
##                    fechadura = banco.consulta("config","fechadura")

##                    if fechadura == "magnetica":

                    os.system("mpg123 /home/pi/CMM/mp3/empurre.mp3")
                    
                    log("Abrindo novamente o social...")
                    
                    saidas.pulso_abre1() # Pulso para abrir direto o portão sem intertravamento (Social)

                    saidas.desliga_blq2()

                    status = open("/home/pi/CMM/status_social.cmm","w") 
                    status.write("0")
                    status.close()

                    time.sleep(2)
                    return
                        

##                    if fechadura == "motor":
##
##                        log("Portão Social emperrado")
##
##                        os.system("mpg123 /home/pi/CMM/mp3/social_emperrado.mp3")
##                                                
##                        saidas.desliga_blq2() # Fecha o contato e libera a eclusa para ser acionada
##
##                        status = open("/home/pi/CMM/status_social.cmm","w") 
##                        status.write("0")
##                        status.close()
##
##                        time.sleep(2)
##                        return
##
##                                           
##                        if eventos == "1":
##
##                            evento.enviar("E","132","008") # Envia portão emperrado                        

                if pm1 == "0": # Portão abriu

                    if eventos == "1":

                        evento.enviar("E","133","001") # Envia abriu portão
                    
                    contador = 200 # Tempo maximo para o social ficar aberto 30 segundos
                    log("Esperando por 20 segundos o portão Social fechar...")

                    while contador > 0: # enquanto portão está aberto
                        
                        pm1 = entradas.pm1()
                        
                        if pm1 == "1": # portão fechou

                            log("Portão Social fechou")

                            if eventos == "1":

                                evento.enviar("R","133","001") # Envia fechamento
                            
                            contador = 0
                                                        
                            s = open("/home/pi/CMM/status_social.cmm","w")
                            s.write("0")
                            s.close()

                            saidas.desliga_blq2() # Fecha o contato e libera a eclusa para ser acionada

                            break

                        if (pm1 == "0" and contador == 1): # Portão ainda aberto após 15 segundos de espera

                            log("Portão Social aberto por muito tempo")

                            if eventos == "1":

                                evento.enviar("E","132","010") # Envia falha no fechamento social

                            os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                            
                            status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
                            status.write("1")
                            status.close()

                            contador = 0

                            saidas.desliga_blq2() # Fecha o contato e libera a eclusa para ser acionada                                
                           
                        ctw2 = entradas.ctw2()                            
                        
                        if (ctw2 == "1"):# Entrada para abrir o portão da eclusa
                            
                            log("Aguarde o fechamento do Social Externo")
                            os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Necessario manter esse audio sempre ativo
                            time.sleep(1)
                            
                        time.sleep(0.1) # 1 segundo
                        contador = contador - 1                            
            
            pm2 = entradas.pm2()
  
                        
        if comando == "abre_eclusa":
            
##            pm2 = entradas.pm2()           
##
##            if pm2 == "0": # O portão Eclusa já esta aberto
##
##                log("O portão Eclusa já esta aberto")

##                os.system("mpg123 /home/pi/CMM/mp3/eclusa_aberto.mp3")
##                time.sleep(1)

##            else: # Se o portão Eclusa esta fechado então pode abrir
                
            pm2 = entradas.pm2()
            pm1 = entradas.pm1()

            if pm1 == "1": # Ponto magnético Social fechado, pode abrir a eclusa
                
                s = open("/home/pi/CMM/status_eclusa.cmm","w")
                s.write("1")
                s.close()

                saidas.liga_blq1() # Impede o social de abrir enquanto a eclusa esta aberta
                
                eclusa(ihm_soc2)                                        
               
                time.sleep(1) # Tempo de espera para o portão abrir
                
                pm2 = entradas.pm2()
                
                if pm2 == "1": # Portão fechado não abriu após o comando

##                   fechadura = banco.consulta("config","fechadura")

##                   if fechadura == "magnetica":

                   os.system("mpg123 /home/pi/CMM/mp3/empurre.mp3")

                   log("Abrindo novamente a eclusa")
                   
                   saidas.pulso_abre2()
                   
                   saidas.desliga_blq1()

                   status = open("/home/pi/CMM/status_eclusa.cmm","w") 
                   status.write("0")
                   status.close()

                   time.sleep(2)
                   return

##                   if fechadura == "motor":
##
##                       log("Portão Eclusa emperrado")
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
##                           evento.enviar("E","132","009") # Envia portão emperrado
##
##                       time.sleep(2)
##                       return

                if pm2 == "0": # Portão aberto

                    if eventos == 1:

                        evento.enviar("E","133","003") # Envia abertura
                    
                    contador = 200 # Tempo maximo para eclusa ficar aberta 20 segundos
                    
                    log("Esperando por 20 segundos o portão Eclusa fechar...")

                    while contador > 0: # enquanto portão está aberto
                        
                        pm2 = entradas.pm2() 

                        if pm2 == "1": # portão fechou

                            log("Portão Eclusa fechou")

                            if eventos == "1":

                                evento.enviar("R","133","003") # Envia fechamento
                            
                            contador = 0
                            
                            s = open("/home/pi/CMM/status_eclusa.cmm","w")
                            s.write("0")
                            s.close()

                            saidas.desliga_blq1() # Libera o social para abrir

                            break

                        if (pm2 == "0" and contador == 1): # Portão ainda aberto após 15 segundos de espera

                            log("Portão Eclusa aberto por muito tempo")

                            if eventos == "1":

                                evento.enviar("E","132","011") # Envia falha no fechamento
                            
                            os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                            
                            status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
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

    status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
    status.write("1")
    status.close()

##    fechadura = banco.consulta("config","fechadura")
##    audio = banco.consulta("config","audio")

    saidas.pulso_abre1() # Pulso para abrir direto o portão sem intertravamento (Social)


    if mensagem == "0": # Fala no local "Abrindo portão social"

        log("Abrindo social...")    

    
    if mensagem == "1": # Via interface web

        log("Abrindo Social pela Central de Monitoramento...")
        os.system("mpg123 /home/pi/CMM/mp3/acionando_pela_central.mp3")    

##    if audio == "1":        
##
##        if mensagem == "0":
##
##            if fechadura == "motor":
##
##                os.system("mpg123 /home/pi/CMM/mp3/abrindo_social.mp3")                    

    status = open("/home/pi/CMM/status_social.cmm","w") 
    status.write("0")
    status.close()

##    time.sleep(1)
    
def eclusa(mensagem):

    status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
    status.write("1")
    status.close()

##    fechadura = banco.consulta("config","fechadura")
##    audio = banco.consulta("config","audio")

    saidas.pulso_abre2() # Pulso para abrir direto o portão sem intertravamento (Eclusa)

    if mensagem == "0": # local

        log("Abrindo eclusa...")

    if mensagem == "1":

        log("Abrindo Eclusa pela Central de Monitoramento...")
        os.system("mpg123 /home/pi/CMM/mp3/acionando_pela_central.mp3")  
##
##    if audio == "1":
##
##        if mensagem == "0":
##
##            if fechadura == "motor":
##
##                os.system("mpg123 /home/pi/CMM/mp3/abrindo_eclusa.mp3")
            
    status = open("/home/pi/CMM/status_eclusa.cmm","w") 
    status.write("0")
    status.close()

##    time.sleep(1)

def Portoes_sociais(Rele): # Programa
    
    log("Programa Sociais em execução ")

    saida = 0
    qbv_acionado = 0
    banco = cmm.Banco()
    qbv2 = entradas.qbv2() # Este quebra de vidro abre os dois portões
               
    while(1):

        habilita_intertravamento = banco.consulta("intertravamento","habilitado")
                
        pm1 = entradas.pm1()
        pm2 = entradas.pm2()
       
        ctw1 = entradas.ctw1()
        ctw2 = entradas.ctw2()

        qbv1 = entradas.qbv1()
        
        ihm_soc1 = banco.consulta("comandos","abre_social_externo")
        ihm_soc2 = banco.consulta("comandos","abre_social_interno")
       
        if ctw1 == "1" or ihm_soc1 == "1":                            

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
            
        if ctw2 == "1" or ihm_soc2 == "1":            

            if habilita_intertravamento == "0":

                log("Intertravamento desabilitado\n")
                
                eclusa(ihm_soc2) 
                
            else:
                
                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("1")
                status.close()

                Intertravamento("abre_eclusa")

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()

                saida = 1

            banco.atualiza("comandos","abre_social_interno","0")
                   
        if qbv1 == "1" and qbv_acionado == 0:

            time.sleep(0.2)
            qbv1 = entradas.qbv1()   

            if qbv1 == "1":

##                fechadura = banco.consulta("config","fechadura")
##
##                if fechadura == "magnetica":

                saidas.liga_abre1()
                saidas.liga_abre1()
                    

##                if fechadura == "motor":
##
##                    saidas.pulso_abre1()
##                    saidas.pulso_abre2()
##                    liga_fot_sociais()
                
                log("Acionado o quebra de vidro da Eclusa")                
                os.system("mpg123 /home/pi/CMM/mp3/emergencia.mp3")

                status = open("/home/pi/CMM/status_social.cmm","w")
                status.write("1")
                status.close()

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("1")
                status.close()

                saidas.liga_abre1()
                saidas.liga_abre2()
                
                qbv_acionado = 1

        if qbv1 == "0" and qbv_acionado == 1:

            time.sleep(0.2)
            qbv1 = entradas.qbv1()

            if qbv1 == "0":

##                fechadura = banco.consulta("config","fechadura")
##
##                if fechadura == "magnetica":

                saidas.desliga_abre1()
                saidas.desliga_abre2()
                    

##                if fechadura == "motor":
##                    
##                    desliga_fot_sociais()
                
                log("Restaurou quebra de vidro da Eclusa")
                os.system("mpg123 /home/pi/CMM/mp3/restaurada_emergencia.mp3")

                saidas.desliga_abre1()
                saidas.desliga_abre2()

##                fechadura = banco.consulta("config","fechadura")
##
##                if fechadura == "magnetica":
                
                time.sleep(1)

##                if fechadura == "motor":
##
##                    log("Aguardando 5 segundos para fechamento dos portoes sociais")                
##                    time.sleep(5)

                os.system("mpg123 /home/pi/CMM/mp3/automatico.mp3")    

                status = open("/home/pi/CMM/status_social.cmm","w")
                status.write("0")
                status.close()

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()                
                
                
                qbv_acionado = 0
            
        time.sleep(0.1) 

        
################################################ THREADS ROTINAS #################################################
        
def Arrombamento(Rele): # Inicia a thread arrombamento de portões

    time.sleep(2)
    
    log("Programa arrombamento de portões sociais em execução")

    ar1 = 0 # Variavel arrombamento portão 1
    ar2 = 0
    
    reset_ar1 = 0 # Reseta a variavel do portão para 0
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
                    
                    log("Arrombamento do portão social")
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

                    cont1 = 350 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 5 min
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

                    log("Arrombamento do portão Eclusa")
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

                    cont2 = 350 # Se apos o reset o portão continuar aberto envia o evento novamente e espera 5 min
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
            
        if pmg1 == "0" and mudanca1 == 0 and status_tx1 == "0": # Violação do portão da garagem                              

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

                log("violação do portão garagem 1")

                l.desliga_rele3_exp1() # Sinal Vermelho

                l.liga_rele4_exp1() # Sirene
                            
                #evento.enviar("E","132","014")

                cont = 30 # Tempo maximo de espera

                log("Aguardando portão fechar")

                while cont > 0:

                    pmg1 = l.leitor1_in1()

                    if(pmg1 == "0"): # Portão ainda aberto                                      

                        time.sleep(1)
                        cont = cont - 1
                            
                    if (pmg1 == "1"): # Portão ja fechou

                        log("Portão fechou")

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
                        
                        rele.liga(4)

                        time.sleep(2)

                        rele.desliga(4)

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
                        
                        rele.liga(5)

                        time.sleep(2)

                        rele.desliga(5)

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
                        s2.l.desliga_rele1_exp1() 
                        s2.l.desliga_rele1_exp1()
                        
                        conn.close()
                        

                    elif(comando == "SET5"):
                        log("Abrindo subsolo")

                        s2 = Expansor()    
    
                        s2.liga_rele1_exp7() # Abre Garagem
                        s2.liga_rele1_exp7() 
                        time.sleep(3)
                        s2.l.desliga_rele1_exp7() 
                        s2.l.desliga_rele1_exp7()
                        
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
                    
        
#################### Instancia as Classes  #############################################

intertravamento = Intertravamento(cmm.Rele)


####################  Declara as threads dos programas disponiveis  ####################

sociais = threading.Thread(target=Portoes_sociais, args=(cmm.Rele,)) # deixar virgula depois do arg 1
##garagem1 = threading.Thread(target=Garagem1, args=(cmm.Rele,))
##garagem2 = threading.Thread(target=Garagem2, args=(cmm.Rele,))
arrombamento = threading.Thread(target=Arrombamento, args=(cmm.Rele,))
servidor = threading.Thread(target=Servidor, args=(cmm.Rele,))
#servidor_qr = threading.Thread(target=Servidor_qr)

buffer = threading.Thread(target=Buffer)


######################################### Start dos Programas  #############################################################

sociais.start() # Inicia o programa dos portões sociais
##garagem1.start() # Inicia o programa do portão de garagem
##garagem2.start() # Inicia o programa do portão de garagem
##arrombamento.start() # Inicia o programa de automação
#servidor.start()
##servidor_qr.start() 
##buffer.start() # Inicia o programa Buffer


time.sleep(0.2) # Tempo para colocar as linhas impressas após as linhas de inicio de programa



log("Temperatura processador " + str(temperatura.cpu()) + "°C\n")  # obter temperatura

try:

    log("*")    
    log("O Sistema está conectado a internet")
    tempo = clima.clima_atual()
    tempo = str(tempo)
    log(tempo)
    narrador.falar(tempo)

except:

    os.system("mpg123 /home/pi/CMM/mp3/sem_internet.mp3")
    log("Sistema sem conexão a internet no momento")

while(1):

    reset = banco.consulta("comandos","reset")

    if reset == "1":

        banco.atualiza("comandos","reset","0")
        
        log("Reiniciando o sistema, aguarde...")

        os.system("mpg123 /home/pi/CMM/mp3/reiniciando_sistema.mp3")

        os.system("sudo reboot now")

    # Colocar aqui o keep alive  
    

    time.sleep(1)

