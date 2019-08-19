#!/home/pi/CMM/bin/python3
# -*- coding:utf-8 -*-

# CMM Oficial com placa de expansão da BRAVAS Technololgy
# Desenvolvido por Leandro Leal  rev. 19/08/2019

import RPi.GPIO as GPIO
import time

from biblioteca_CMM_oficial import Rele,Narrador,Temperatura,Email,Clima,Evento
from cmm_io import Entradas, Saidas # Classes para leituras das entradas e acionamento das saidas definidas no arq. config.txt
from expansor_modbus import Expansor # Acionamento de saidas dos expansores
from leitor_modbus import Leitor  # Leitura das entradas dos expansores
from IHM_Sociais import IHM

##import metodo_leitor_modbus as l

from datetime import datetime, timedelta
import wiringpi # Biblioteca para usar as GPIO da rasp como saidas ou entradas
import os     # Executa comandos do sistema operacional Ex.: os.system('sudo reboot now'))
import threading # Modulo superior Para executar as threads
import sys
from tkinter import *
from tkinter import ttk
from functools import partial
from tkinter import messagebox
import socket
import serial # Parhome/pi/CMM/mp3a comunicação serial com arduino
from banco import Banco


os.system("mpg123 /home/pi/CMM/mp3/reiniciando_sistema.mp3")
time.sleep(1)
os.system("mpg123 /home/pi/CMM/mp3/bemvindo_cam.mp3")

socket.setdefaulttimeout(2) # limite de 2 segundos para enviar o socket

##mutex = thread.allocate_lock() # Trava a thread para que seja executada sozina

#ser = serial.Serial("/dev/ttyS0", 9600) #Configura a serial e a velocidade de transmissao

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4,GPIO.IN)
GPIO.setup(27,GPIO.IN)
GPIO.setup(22,GPIO.IN)
GPIO.setup(10,GPIO.IN)

GPIO.setup(11,GPIO.OUT)
GPIO.setup(12,GPIO.OUT)

A = GPIO.input(4) # ENTRADAS NÃO FOTOACOPLADAS (As entradas A B C D então normalmente em nivel lógico HIGH (1))
B = GPIO.input(27)
C = GPIO.input(22)
D = GPIO.input(10)

buzzer = GPIO.output(11,1) # Sinal De buzzer informando ligou
time.sleep(0.2)
buzzer = GPIO.output(11,0)


hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
h = int(time.strftime('%H'))
data = time.strftime('%d/%m/%y')

global entradas
entradas = ["A", "B", "C", "D", "IN1", "IN2", "IN3", "ctw1", "ctw2", "qbv", "qde", "IN8"]
global mp3

nome = os.popen('hostname').readline()
ip = os.popen('hostname -I').readline()

print("Nome desta maquina",nome,"com IP",ip)

############################ INICIA AS CLASSES DA Biblioteca_CMM_Bravas  ########################################

rele = Rele() # inicia a classe rele com port A em 0
narrador = Narrador()
temperatura = Temperatura()
email = Email()
clima = Clima()
evento = Evento("5667") # Inicia a classe evento com o codigo do cliente


##qrcode = Qrcode() # Instancia a classe do leitor de qrcode
##wiegand = Wiegand()
##rele_qr = Rele_qr() # Instanciar loclamente com o IP do leitor para acionamento do rele do equipamento
## Ex. rele_qr = Rele_qr("172.20.9.5",5000) # Conecta com o Qrcode deste endereço para acionamento do rele e leitura da entrada auxiliar

##print("Conteudo do play1 ",ihm.get_cbox("play1"))
 
##############################################  Threads dos programas  ##########################################################

def thread_qrcode(qrcode): # Programa do QR Code

    sys.stdout.write("\nPrograma QR Code em execução\n")

##    qrcode.leitor("172.20.9.5",5001) # Conecta com o Qrcode deste endereço e inicia o programa do leitor

  
######################################  CLASSES  ###########################################

entradas = Entradas()
saidas = Saidas()

############################################################################################

def Intertravamento(comando): # Inicia a thread dos portoes sociais importando a classe Rele
        
        entradas = Entradas() # Inicia classe para leitura das entradas
        
        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
        
        audio = 0 # Deixa ativo ass mensagens de audio de abertura
        cont = 0

        a = open("/home/pi/CMM/status_social.cmm","r")
        abre_social = a.read()
        a.close()

        b = open("/home/pi/CMM/status_eclusa.cmm","r")
        abre_eclusa = b.read()
        b.close()
        
##        if cont == 0: # Executa uma unica vez
##
##            print("Estado das enradas A B C D ",A,B,C,D," ligado (0)")
##            cont = 1
    
        if comando == "abre_social":

##            print("Reconheceu o abre_social",hs)

            entradas = Entradas()
            pm1 = entradas.pm1
                                
            if pm1 == 1: # O portão social já esta aberto

                print("O portão social já esta aberto")
                            
                os.system("mpg123 /home/pi/CMM/mp3/social_aberto.mp3")
                time.sleep(1)

            else: # Se o portão Social esta fechado então pode abrir

                entradas = Entradas()
                pm2 = entradas.pm2
                                
                if pm2 == 0: # Se Ponto magnético Eclusa fechado
                    
                    s = open("/home/pi/CMM/status_social.cmm","w")
                    s.write("1")
                    s.close()

                    rele.liga(2) # Aqui abrimos o contato da eclusa para impedir que ela seja aberta enquanto o social esta aberto
                    
                    print("Abrindo portão Social",hs)
                    abre.social()

                    if audio == 1: # Ativa as mensagens de abertura e fechamento

                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_social.mp3")                   
                    
                    time.sleep(2) # Tempo minimo para o portão abrir

                    entradas = Entradas()
                    pm1 = entradas.pm1
                                        
                    if pm1 == 0: # Portão fechado pois não abriu com o comando

                        print("Portão Social emperrado")

                        os.system("mpg123 /home/pi/CMM/mp3/social_emperrado.mp3")
                                                
                        rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada

                        evento.enviar("E","132","008") # Envia portão emperrado                        

                    if pm1 == 1: # Portão abriu

##                        evento.enviar("E","133","001") # Envia abriu portão
                        
                        contador = 300 # Tempo maximo para o social ficar aberto 30 segundos
                        print("Esperando por 15 segundos o portão social fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = Entradas()
                            pm1 = entradas.pm1
                            
                            # Esperando o portão social fechar...
                            
                            if pm1 == 0: # portão fechou

                                print("Portão social fechou")
##                                evento.enviar("R","133","001") # Envia fechamento
                                contador = 1
                                                            
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada

                                break

                            if (pm1 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                print("Portão social aberto por muito tempo")
                                
                                evento.enviar("E","132","010") # Envia falha no fechamento social

                                os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                                
                                status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
                                status.write("1")
                                status.close()

                                contador = 0

                                rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada
                                
                            entradas = Entradas()    
                            ctw2 = entradas.ctw2
                            btn2 = entradas.qde
                            
                            if (ctw2 == 0 or btn2 == 0):# and pm1 == 1): # Entrada para abrir o portão da eclusa
                                print("Agurade o fechamento do social")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_para_acionar.mp3") # Necessario manter esse audio sempre ativo
                                time.sleep(1)
                                
                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1
                            
                entradas = Entradas()
                pm2 = entradas.pm2
  
                        
        if comando == "abre_eclusa":

##            print("Reconheceu o abre_eclusa")

            entradas = Entradas()
            pm2 = entradas.pm2            

            if pm2 == 1: # O portão Eclusa já esta aberto

                print("O portão Eclusa já esta aberto")

                os.system("mpg123 /home/pi/CMM/mp3/eclusa_aberto.mp3")
                time.sleep(1)

            else: # Se o portão Eclusa esta fechado então pode abrir

                entradas = Entradas()
                pm2 = entradas.pm2
                pm1 = entradas.pm1

                if pm1 == 0: # Ponto magnético Social fechado, pode abrir a eclusa
                    
                    s = open("/home/pi/CMM/status_eclusa.cmm","w")
                    s.write("1")
                    s.close()

                    rele.liga(1) # Impede o social de abrir enquanto a eclusa esta aberta
                    
                    print("Abrindo portão Eclusa",hs)
                    abre.eclusa()
                                        

                    if audio == 1:
                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_eclusa.mp3")
                    
                    time.sleep(3) # Tempo de espera para o portão abrir

                    entradas = Entradas()
                    pm2 = entradas.pm2
                    
                    if pm2 == 0: # Portão fechado não abriu após o comando

                       print("Portão eclusa emperrado")
                       
                       os.system("mpg123 /home/pi/CMM/mp3/eclusa_emperrado.mp3")
                           
                       rele.desliga(1) # Libera o social para abrir mesmo com a eclusa aberta

                       evento.enviar("E","132","009") # Envia portão emperrado

                    if pm2 == 1: # Portão aberto

##                        evento.enviar("E","133","003") # Envia abertura
                        
                        contador = 300 # Tempo maximo para eclusa ficar aberta 30 segundos
                        print("Esperando por 30 segundos o portão Eclusa fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = Entradas()
                            pm2 = entradas.pm2
                            
                            # Esperando o portão eclusa fechar...

                            if pm2 == 0: # portão fechou

                                print("Portão Eclusa fechou")
##                                evento.enviar("R","133","003") # Envia fechamento
                                contador = 1
                                
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(1) # Libera o social para abrir

                                break

                            if (pm2 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                print("Portão Eclusa aberto por muito tempo")
                                
                                evento.enviar("E","132","011") # Envia falha no fechamento
                                
                                os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                                
                                status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
                                status.write("1")
                                status.close()                                

                                rele.desliga(1) # Libera o social para abrir mesmo com a eclusa aberta

                                contador = 0

                            entradas = Entradas()
                            ctw1 = entradas.ctw1
                            btn1 = entradas.qbv 

                            if ctw1 == 0 or btn1 == 0: # Alguem esta tentando abrir o social com a eclusa aberta

                                print("Aguarde o fechamento do portão")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_para_acionar.mp3") # Manter esse audio sempre ativo
                                time.sleep(1)
                                

                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1


def Portoes_sociais(Rele): # Programa
    
    sys.stdout.write("\nPrograma Sociais em execução na thread\n")

    saida = 0
    banco = Banco()
           
    while(1):

        habilita_intertravamento = banco.consulta("intertravamento","habilitado")

        entradas = Entradas() # Inicia classe para leitura das entradas
        
        pm1 = entradas.pm1
        pm2 = entradas.pm2

        btn1 = entradas.qbv        
        btn2 = entradas.qde
        ctw1 = entradas.ctw1
        ctw2 = entradas.ctw2
       
        if ctw1 == 0:

            if habilita_intertravamento == "0":

                print("\nIntertravamento desabilitado\n")

                abre = Abre()
                abre.social()

            else:

                print("\nIntertravamento habilitado\n")

                status = open("/home/pi/CMM/status_social.cmm","w")
                status.write("1")
                status.close()
         
                Intertravamento("abre_social")

                status = open("/home/pi/CMM/status_social.cmm","w")
                status.write("0")
                status.close()

            
        if ctw2 == 0:

            if habilita_intertravamento == "0":

                print("\nIntertravamento desabilitado\n")

                abre = Abre()
                abre.eclusa()

                bem_vindo

            else:
                
                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("1")
                status.close()

                Intertravamento("abre_eclusa")

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()

                saida = 1
                
        if btn2 == 0:
            
            if habilita_intertravamento == "0":

                print("\nIntertravamento desabilitado\n")

                abre = Abre()
                abre.eclusa()

            else:
                
                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("1")
                status.close()

                Intertravamento("abre_eclusa")

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()

                saida = 1


        if btn1 == 0:

            if habilita_intertravamento == "0":

                print("\nIntertravamento desabilitado\n")

                abre = Abre()
                abre.social()

            else:

                print("\nIntertravamento habilitado\n")

                if saida == 1:

                    print ("Abrindo pelo botão de saida")
                    os.system("mpg123 /home/pi/CMM/mp3/ate_logo.mp3")
                    Intertravamento("abre_social")                
                
                    saida = 0

                else:

                    print("Uso incorreto do sistema")
                    os.system("mpg123 /home/pi/CMM/mp3/uso_incorreto.mp3")
                    evento.enviar("E","132","023")
                    time.sleep(1)

                
                
        time.sleep(0.1)                             
                                

class Abre(Rele): # classe abertura dos portoes registrando no arquivo de controle status_social / status_eclusa

    def social(self):

        status = open("/home/pi/CMM/status_social.cmm","w") # Para não dispara o arrombamento
        status.write("1")
        status.close()

        rele.pulso(4,2) # Pulso para abrir direto o portão sem intertravamento (Social)
     
        
    def eclusa(self):

        status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não dispara o arrombamento
        status.write("1")
        status.close()        
    
        rele.pulso(5,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)

########################################## Métodos de acesso a classe leitor #####################################

def leitor(entrada):

    l = Leitor()

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

    sys.stdout.write("\nPrograma Garagem 1 em execução na thread\n")
    
    s = Expansor()

    time.sleep(0.1)
    s.desliga_rele4_exp1() # Garante que a sirene esteja desligada
    time.sleep(0.1)
    s.desliga_rele1_exp1() # Garante que o Abre esteja desligado
    time.sleep(0.1)
    s.desliga_rele2_exp1() # Garante que o Foto esteja desligado
    time.sleep(0.1)    
        
    while(1):

        hs = time.strftime("%H:%M:%S")
        
##        l = Leitor() # inicia a classe para leitura das entradas dos modulos expansores 
        s = Expansor()
        
        tx1 =  leitor("leitor1_in3")  # Cantato abre vindo do TX (LINEAR HCS)
                
        if (tx1 == 1):    # Se o tx mandou abrir o portão

            time.sleep(0.2)
            tx1 =  leitor("leitor1_in3")

            if (tx1 == 1): # Verifica novamente para evitar ruido

                print("\nreconheceu tx Garagem",hs,"\n")

                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                status.write("1")
                status.close()

                time.sleep(2) # Tempo para começar a abrir o portão

                pmg1 = leitor("leitor1_in1")

                cont = 60     # Tempo maximo para deixar o portão aberto (60 = 30 segundos)
                
                if pmg1 == 1: # Portão não abriu apos o comando

                    print("Portão garagem não abriu")
                    evento.enviar("E","132","015") # Emperrado
                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                    status.write("0")
                    status.close()
                                        
                    cont = 0

                if pmg1 == 0: # Portão abriu

##                    evento.enviar("E","133","013")

                    while cont > 0:   # Enquanto o portão esta aberto verifica

                        if cont == 60:

                            print("Portão Garagem abriu")
                        
                        pmg1 = leitor("leitor1_in1")
                        
                        if pmg1 == 1: # Se o portão ja fechou

                            print("Portão Garagem fechou\n")

                            status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                            status.write("0")
                            status.close()

                            time.sleep(2)

##                            evento.enviar("R","133","013")

                            # Envia o evento de fechamento para a central
                            cont = 0
                            break
                            
                        if pmg1 == 0:     # Se o portão ainda esta aberto

                            bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1

                            if bar1 == 1: # Se acionou a barreira de entrada

                                print("Acionou a barreira 1")

                                while bar1 == 1: # Enquanto a barreira esta acionada

                                    bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1

                                    # Alguem esta na frente da barreira

                                    time.sleep(0.1)
                                    
                                print("Passou alguem, verificando dupla passagem...")

                                pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico
                                
                                if pmg1 == 0:

                                    pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico

                                    print("Aguardando portão Garagem fechar")

                                    while pmg1 == 0:  # Enquanto o portão ainda não fechou                                

                                        pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico
                                        bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1
                                        tx1 =  leitor("leitor1_in3")  # Cantato abre vindo do TX (LINEAR HCS)  

                                        if bar1 == 1: # Dupla passagem

                                            time.sleep(0.2)
                                            bar1 = leitor("leitor1_in2")

                                            if bar1 == 1:

                                                print("Dupla passagem Garagem")

                                                evento.enviar("E","132","019")

                                                s.liga_rele4_exp1() # Sirene                                            
                                                time.sleep(10)
                                                s.desliga_rele4_exp1()                                            

                                                break

                                        if tx1 == 1: # Alguem acionou o controle enquanto o portão fechava

                                            cont = 0
                                            
                                            break # Sai da função e inicia novamente a verificação

                                        time.sleep(0.2)
                                 
                                print("Fim do cilo Garagem")

                                time.sleep(1)

                        cont = cont - 1
                        time.sleep(0.5)

                    if cont == 1: # Passaram se 29 segundos e o portão não fechou

                        print("Portão Garagem aberto muito tempo")

                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                        status.write("0")
                        status.close()

                        evento.enviar("E","132","019") # Envia evento de portão aberto
                        cont = 0
                        break
        time.sleep(0.1)
        
def Garagem2(Rele): # Inicia a thread do portão da garagem importando a classe Rele

    sys.stdout.write("\nPrograma Garagem Subsolo em execução na thread\n")

    s2 = Expansor()

    time.sleep(0.1)
    s2.desliga_rele4_exp7() # Garante que a sirene esteja desligada
    time.sleep(0.1)
    s2.desliga_rele1_exp7() # Garante que o Abre esteja desligado
    time.sleep(0.1)
    s2.desliga_rele2_exp7() # Garante que o Foto esteja desligado
    time.sleep(0.1)

    mudanca2 = 0
    
    while(1):

        hs = time.strftime("%H:%M:%S")
        
##        l2 = Leitor() # inicia a classe para leitura das entradas dos modulos expansores 
        s2 = Expansor()
        
        tx2 =  leitor("leitor7_in3")  # Cantato abre vindo do TX (LINEAR HCS)               
        
        if (tx2 == 1):    # Se o tx mandou abrir o portão

            time.sleep(0.2)
            tx2 =  leitor("leitor7_in3")

            if (tx2 == 1):

                print("\nreconheceu tx Subsolo",hs,"\n")

                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                status.write("1")
                status.close()

                time.sleep(2) # Tempo para começar a abrir o portão

                pmg2 = leitor("leitor7_in1")

                cont = 60     # Tempo maximo para deixar o portão aberto (60 = 30 segundos)
                
                if pmg2 == 1: # Portão não abriu apos o comando

                    print("Portão Subsolo não abriu")                    

                    evento.enviar("E","132","018")

                    status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                    status.write("0")
                    status.close()
                                    
                    cont = 0

                if pmg2 == 0: # Portão abriu

                    while cont > 0:   # Enquanto o portão esta aberto verifica

                        if cont == 60:

                            print("Portão Subsolo abriu")
                        
                        pmg2 = leitor("leitor7_in1")
                        
                        if pmg2 == 1: # Se o portão ja fechou

                            print("Portão Subsolo fechou\n")

                            # Envia o evento de fechamento para a central
                            cont = 0
                            break
                            
                        if pmg2 == 0:     # Se o portão ainda esta aberto

                            bar2 = leitor("leitor7_in2") # Faz a leitura da barreira 1

                            if bar2 == 1: # Se acionou a barreira de entrada

                                print("Acionou a barreira 1 Subsolo")

                                while bar2 == 1: # Enquanto a barreira esta acionada

                                    bar2 = leitor("leitor7_in2") # Faz a leitura da barreira 1

                                    # Alguem esta na frente da barreira

                                    time.sleep(0.1)
                                    
                                print("Passou alguem Subsolo, verificando dupla passagem...")

                                pmg2 = leitor("leitor7_in1") # Faz a leitura do ponto magnetico
                                
                                if pmg2 == 0:

                                    pmg2 = leitor("leitor7_in1") # Faz a leitura do ponto magnetico

                                    print("Aguardando portão Subsolo fechar apos entrada ou saida")

                                    while pmg2 == 0:  # Enquanto o portão ainda não fechou                                

                                        pmg2 = leitor("leitor7_in1") # Faz a leitura do ponto magnetico
                                        bar2 = leitor("leitor7_in2") # Faz a leitura da barreira 1
                                        tx2 =  leitor("leitor7_in3")  # Cantato abre vindo do TX (LINEAR HCS)  

                                        if bar2 == 1: # Dupla passagem

                                            time.sleep(0.2)
                                            bar2 = leitor("leitor7_in2")

                                            if bar2 == 1:

                                                print("Dupla passagem Subsolo")

                                                evento.enviar("E","132","019")

                                                s2.liga_rele4_exp7() # Sirene
                                                time.sleep(10)
                                                s2.desliga_rele4_exp7()

                                                break

                                        if tx2 == 1: # Alguem acionou o controle enquanto o portão fechava

                                            cont = 0                                       
                                            break # Sai da função e inicia novamente a verificação

                                        time.sleep(0.2)
                                        
                                print("Fim do cilo Subsolo")

                                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                                status.write("0")
                                status.close()

                                time.sleep(1)

                        cont = cont - 1
                        time.sleep(0.5)

                    if cont == 1: # Passaram se 29 segundos e o portão não fechou

                        print("Portão Subsolo aberto muito tempo")

                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                        status.write("0")
                        status.close()

                        evento.enviar("E","132","019")# Envia evento de portão aberto
                        cont = 0
                        break     
        time.sleep(0.1)
        
def Arrombamento(Rele): # Inicia a thread arrombamento de portões
    
    sys.stdout.write("\nPrograma arrombamento de portões em execução\n")

    ar1 = 0 # Variavel arrombamento portão 1
    ar2 = 0
    ar3 = 0
    ar4 = 0
    ar5 = 0
    ar6 = 0
    ar7 = 0
    reset_ar1 = 0 # Reseta a variavel do portão para 0
    reset_ar2 = 0
    reset_ar3 = 0
    reset_ar4 = 0
    reset_ar5 = 0 
    reset_ar6 = 0
    reset_ar7 = 0
    cont1 = 30 # Contador individual para cada reset de arrombamento
    cont2 = 30
    cont3 = 30
    cont4 = 30
    cont5 = 30
    cont6 = 30
    cont7 = 30
    
    while(1):

        entradas = Entradas()

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

                print("Arrombamento do portão social")
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

                cont1 = 60 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 60 segundos
                ar1 = 0
                reset_ar1 = 0
                rele.desliga(8)

                

        if abre_eclusa == "0" and pm2 == 1 and ar2 == 0:

            time.sleep(0.5) # Filtra algum possivel ruido de até 500 milissegundos

            if pm2 == 1: # Se realmente foi um arrombamento liga sirene e notifica o Moni

                print("Arrombamento do portão Eclusa")
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

                cont2 = 60 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 60 segundos
                ar2 = 0
                reset_ar2 = 0
                rele.desliga(8)

        
        time.sleep(2)   

def Servidor(Rele,Abre): # Inicia a thread do portão da garagem importando a classe Rele
    
    sys.stdout.write("\nPrograma Servidor em execução\n")
    socket.setdefaulttimeout(9999) # limite tempo socket
    
    host = '0.0.0.0'
    port = 5510

    time.sleep(0.1)

    print("iniciou o servidor")
    
    print("Servidor: ",host, " porta: ", port)

    while(1):

        
    ############################################### Thread servidor p/ PHP e MONI #################################################################

            socket.setdefaulttimeout(9999)


            def setupServer():
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
                
                try:
                    s.bind((host, port))
                except socket.error as msg:
                    print (msg)
                
                return s

            def setupConnection():
                s.listen(5)
                conn, address = s.accept()
                print ("Conectado com: " + address[0] + ":" + str(address[1]), "\n")
                return conn


            def dataTransfer(conn):  # Loop de transferencia e recepção de dados

                print("Entrou no data transfer")

                while True:
                    
                    rele = Rele()
                                                          
                    data = conn.recv(1024)  # Recebe o dado
                    data = data.decode('utf-8')
                    print("data",data)
                    dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                    command = dataMessage[0]

                    print("command",command)

                    (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e eoutra em resto

                    print("comando e resto",comando,resto)
                   
                    if(comando == "SET1"):

                        print("Abrindo portão Social pelo Moni")

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
                        
                        print("Abrindo portão Eclusa pelo Moni")

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
                        
                        print("reconheceu SET 3")                        
    
                        conn.close()                       

                    elif(comando == "SET4"):
                        print("Abrindo garagem")

                        s2 = Expansor()    
    
                        s2.liga_rele1_exp1() # Abre Garagem
                        s2.liga_rele1_exp1() 
                        time.sleep(3)
                        s2.desliga_rele1_exp1() 
                        s2.desliga_rele1_exp1()
                        
                        conn.close()
                        

                    elif(comando == "SET5"):
                        print("Abrindo subsolo")

                        s2 = Expansor()    
    
                        s2.liga_rele1_exp7() # Abre Garagem
                        s2.liga_rele1_exp7() 
                        time.sleep(3)
                        s2.desliga_rele1_exp7() 
                        s2.desliga_rele1_exp7()
                        
                        conn.close()

                    elif(comando == "SET 6"):
                        print("SET 6, RESET SOCIAL")
                        conn.close()

                    elif(comando == "SET 8"):
                        
                        print("SET 8, RESET ECLUSA")
                        conn.close()

                    elif(comando == "SET 9"):
                        
                        print("SET 9, RESET INTERFONES")
                        conn.close()

                    elif(comando == "SET 10"):
                        
                        print("SET 10, AUXILIAR 1 (ON/OFF)")
                        conn.close()

                    elif(comando == "SET 11"):
                        
                        print("SET 11, AUXILIAR 2 (ON/OFF)")
                        conn.close()

                    elif(comando == "SET 12"):
                        
                        print("APRESENTAÇÃO")
                        conn.close()
                                            

                    else:

                        print("Recebido pelo servidor:",comando) 

                        reply = 'ok'
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()


            s = setupServer()

            while True:
                
              time.sleep(1) 

              print ("\nEscutando na porta",port, "\n")
              try:

                  conn = setupConnection()
                  dataTransfer(conn)
                  print("Oiee")


              except Exception as err:

                  print("Encerrou conexão")

        
def Alarmes_garagem_1(Rele):
    
    sys.stdout.write("\nPrograma Alarmes em execução\n")

    mudanca1 = 0
    
    while(1): 
        
##        l = Leitor() # inicia a classe para leitura das entradas dos modulos expansores 
        s = Expansor()

        pmg1 = leitor("leitor1_in1") # Ponto magnetico portão leitor 1 entrada 1        
        time.sleep(0.1)
        mud1 = leitor("leitor1_in4")  # Chave de mudança

        t = open("/home/pi/CMM/status_garagem_1.cmm","r")
        status_tx1 = t.read()
        t.close()
                

        if mud1 == 1 and mudanca1 == 0: # Chave de mudança acionada

            #Fazer um filtro aqui

            time.sleep(0.2)
            mud1 = leitor("leitor1_in4")

            if mud1 == 1:

                t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                t.write("1")
                t.close()

                s.liga_rele1_exp1() # Aciona o rele 1 do modulo 1 (Abre)
                time.sleep(2)
                s.liga_rele2_exp1() # Aciona o rele 2 do modulo 1 (Foto)                

                mudanca1 = 1

        if mud1 == 0 and mudanca1 == 1:

            time.sleep(0.2)
            mud1 = leitor("leitor1_in4")

            if mud1 == 0:
                                
                s.desliga_rele1_exp1() # Desliga o rele 1 do modulo 1 (Abre)
                s.desliga_rele2_exp1() # Desliga o rele 2 do modulo 1 (Foto) 

                pmg1 = leitor("leitor1_in1")

                cont = 30 # Tempo maximo de espera

                print("Aguardando portão fechar depois da mudanca")

                while cont > 0:

                    pmg1 = leitor("leitor1_in1")

                    if(pmg1 == 0): # Portão ainda aberto                                      

                        time.sleep(1)
                        cont = cont - 1
                            
                    if (pmg1 == 1): # Portão ja fechou

                        print("Portão fechou")

                        t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                        t.write("0")
                        t.close()
                        
                        cont = 0
                        mudanca1 = 0
                        time.sleep(1)
                        break
            
        if pmg1 == 0 and mudanca1 == 0 and status_tx1 == "0": # Violação do portão da garagem

            time.sleep(0.2)
            pmg1 = leitor("leitor1_in1")                      

            cont = 5
            violacao = 1
            
            while cont > 0:

                t = open("/home/pi/CMM/status_garagem_1.cmm","r")
                status_tx1 = t.read()
                t.close() 

                pmg1 = leitor("leitor1_in1")

                if pmg1 == 0 and status_tx1 == "0":

                    violacao = 1                    

                if pmg1 == 1:
                    
                    violacao = 0
                    break

                time.sleep(0.1)
                cont = cont - 1

            if violacao == 0: # Filtrou ruido

                pass

            if violacao == 1:

                print("violação do portão garagem 1")

                s.liga_rele4_exp1() # Sirene
                            
                evento.enviar("E","132","014")

                cont = 30 # Tempo maximo de espera

                print("Aguardando portão fechar")

                while cont > 0:

                    pmg1 = leitor("leitor1_in1")

                    if(pmg1 == 0): # Portão ainda aberto                                      

                        time.sleep(1)
                        cont = cont - 1
                            
                    if (pmg1 == 1): # Portão ja fechou

                        print("Portão fechou")


                        
                        cont = 0
                        time.sleep(1)
                        
                        s.desliga_rele4_exp1() # Desliga sirene
                        
                        break            
                
                s.desliga_rele4_exp1() # Desliga sirene

##                violacao = 0
                
                time.sleep(5)
        time.sleep(1)
        
def Alarmes_garagem_2(Rele):    

    mudanca2 = 0
    
    while(1):
        
##        l2 = Leitor() # inicia a classe para leitura das entradas dos modulos expansores 
        s2 = Expansor()

        time.sleep(0.1)
        pmg2 = leitor("leitor7_in1") # Ponto magnetico portão leitor 1 entrada 1        
##        time.sleep(0.1)       
##        mud2 = leitor("leitor7_in4")  # Chave de mudança

        t = open("/home/pi/CMM/status_garagem_2.cmm","r")
        status_tx2 = t.read()
        t.close()

##        if mud2 == 1 and mudanca2 == 0: # Chave de mudança acionada
##
##            time.sleep(0.2)
##            mud2 = leitor("leitor7_in4")
##
##            if mud2 == 1:
##
##                t = open("/home/pi/CMM/status_garagem_2.cmm","w")
##                t.write("1")
##                t.close()
##                
##                s2.liga_rele1_exp7() # Aciona o rele 1 do modulo 2 (Abre)
##                time.sleep(2)                
##                s2.liga_rele2_exp7() # Aciona o rele 2 do modulo 2 (Foto)
##
##                mudanca2 = 1
##
##        if mud2 == 0 and mudanca2 == 1:
##
##            time.sleep(0.2)
##            mud2 = leitor("leitor7_in4")
##
##            if mud2 == 0:
##                
##                s2.desliga_rele1_exp7() # Desliga o rele 1 do modulo 1 (Abre)                             
##                s2.desliga_rele2_exp7() # Desliga o rele 2 do modulo 1 (Foto)
##                
##                pmg2 = leitor("leitor7_in1")
##
##                cont = 30 # Tempo maximo de espera
##
##                print("Aguardando portão Subsolo fechar")
##
##                while cont > 0:
##
##                    pmg2 = leitor("leitor7_in1")
##
##                    if(pmg2 == 0): # Portão ainda aberto                                      
##
##                        time.sleep(1)
##                        cont = cont - 1
##                            
##                    if (pmg2 == 1): # Portão ja fechou
##
##                        print("Portão Subsolo fechou")
##
##                        t = open("/home/pi/CMM/status_garagem_2.cmm","w")
##                        t.write("0")
##                        t.close()
##                        
##                        cont = 0
##                        mudanca2 = 0
##                        time.sleep(2)
##                        break
                                
        if pmg2 == 0 and status_tx2 == "0": # Violação do portão da garagem

            time.sleep(0.2) 
            pmg2 = leitor("leitor7_in1")
            
            cont = 5
            violacao = 1
            
            while cont > 0: # Filtro

                t = open("/home/pi/CMM/status_garagem_1.cmm","r")
                status_tx2 = t.read()
                t.close() 

                pmg2 = leitor("leitor7_in1")

                if pmg2 == 0 and status_tx2 == "0":
                    
                    violacao = 1

                if pmg2 == 1:
                    
                    violacao = 0
                    break

                time.sleep(0.1)
                cont = cont - 1

            if violacao == 0: # Filtrou ruido

                pass

            if violacao == 1:

                print("violação do portão Subsolo")

                s2.liga_rele4_exp7() # Sirene
                                            
                evento.enviar("E","132","016")

                cont = 30 # Tempo maximo de espera

                print("Aguardando portão Subsolo fechar apos violação")

                while cont > 0:

                    pmg2 = leitor("leitor7_in1")

                    if(pmg2 == 0): # Portão ainda aberto                                      

                        time.sleep(1)
                        cont = cont - 1
                            
                    if (pmg2 == 1): # Portão ja fechou

                        print("Portão Subsolo fechou")

                        t = open("/home/pi/CMM/status_garagem_2.cmm","w")
                        t.write("0")
                        t.close()
                        
                        cont = 0
                        time.sleep(1)
                        
                        s2.desliga_rele4_exp7() # Desliga sirene
                        
                        break
                    
                s2.desliga_rele4_exp7() # Desliga sirene
                
                time.sleep(5)

        time.sleep(1)


def Buffer():

    socket.setdefaulttimeout(3) # limite em segundos para enviar o socket

    host = '172.20.1.5'  # '172.20.1.5' Host servidor  Moni
    port = 4010          # 4010 Porta máquina receptora

    print("Programa buffer de eventos em execução")

    enviado = 0

    while(1):

        socket.setdefaulttimeout(3)

        b = open("/home/pi/CMM/buffer_eventos.txt","r")
        
        for line in b:

            ln = line
            evento = ln.replace("\n","")
            
            if evento != "": # Se houver alguma coisa para enviar

##                print("Tentanto enviar o evento",evento)

                try:
        
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = (evento + "\r") # ("7000 185808E30500008")  # Envia abriu portão da eclusa para a central de monitormento
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    s.close()

                    enviado = 1                    
                                
                except Exception as err:
                    
##                    print("Não conseguiu enviar o evento, sem conexão no momento",err)
                    s.close()

                    time.sleep(10)
                    break
                
                if enviado == 1:
                                               
                    print("Evento enviado ",evento)           

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
                                print("Excluindo o evento",evento,"posicao",indice)
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
                        print("Erro",err)
            
        b.close() # Fecha o arquivo de texto em modo leitura    
        time.sleep(1)
                    
        
#################### Instancia as Classes  #############################################

intertravamento = Intertravamento(Rele)
abre = Abre()

####################  Declara as threads dos programas disponiveis  ####################

##entradas = threading.Thread(target=Entradas)
sociais = threading.Thread(target=Portoes_sociais, args=(Rele,)) # deixar virgula depois do arg 1
garagem1 = threading.Thread(target=Garagem1, args=(Rele,))
garagem2 = threading.Thread(target=Garagem2, args=(Rele,))
arrombamento = threading.Thread(target=Arrombamento, args=(Rele,))
servidor = threading.Thread(target=Servidor, args=(Rele,Abre,))
buffer = threading.Thread(target=Buffer)

alarmes1 = threading.Thread(target=Alarmes_garagem_1, args=(Rele,))
alarmes2 = threading.Thread(target=Alarmes_garagem_1, args=(Rele,))


######################################### Start dos Programas  #############################################################

sociais.start() # Inicia o programa dos portões sociais
garagem1.start() # Inicia o programa do portão de garagem
garagem2.start() # Inicia o programa do portão de garagem
#arrombamento.start() # Inicia o programa de automação
#servidor.start() 
buffer.start() # Inicia o programa Buffer

alarmes1.start() # Inicia a leitura de "interrupções" (chave de mudança garagem1 e arrombamento de portões)
alarmes2.start()
##qrcode.start()
##wiegand.start()

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

##print ("\nTemperatura",temperatura.cpu(),"°C\n")  # obter temperatura

##email.enviar("O Programa acabou de reiniciar\nPosso enviar qualquer mensagem aqui...") # Não usar nenhum caracter especial na mensagem

##tempo = clima.clima_atual()
##print(tempo)

##evento.enviar_contact_id('E','132','001') # Evento ou Restauração / Evento / Setor

###################################################################################################

sys.stdout.write("\nTemperatura " + str(temperatura.cpu()) + "°C\n")  # obter temperatura



while(1):

    # Colocar aqui o keep alive  
    

    time.sleep(1)

