#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# IN1 - Ponto magnético 1 (Portão externo) GPIO 17
# IN2 - Ponto magnético 2 (Portão Interno) GPIO 18
# IN3 - CTW1 - Abre portão Externo (Entrada) GPIO 27
# IN4 - CTW - Abre portão Interno (Entrada) GPIO 22
# IN5 - BT1 - Abre portão Externo (Saida) GPIO 23
# IN6 - BT2 - Abre portão Interno (Saida) GPIO 24
# IN7 - Modo Manutenção  GPIO 25
# IN8 - Quebra de vidro  GPIO 4

# OUT1 ABRE PORTÃO SOCIAL
# OUT2 ABRE PORTÃO ECLUSA

# OUT 9 E OUT 10 SAIDA DE AUDIO (COMUM + COMUM)


# OUT 11 LED VERMELHO
# OUT 12 LED AZUL
# OUT 13 cooler

from gtts import gTTS  # importamos o modúlo gTTS
import pygame # Permite a utilização do modulo para execução de mp3
import time # Funções de tempo
import datetime  # Funções de data

import RPi.GPIO as GPIO
import smbus  # para funcionamento dos módulos com interface I2C
import spidev
import os     # Permite a execução de comandos do sistema operacional dentro do script Ex.: os.system('sudo reboot now')
import serial # Para comunicação serial com arduino
import mysql.connector # faz a comunicação com o mysql no python 3.6
import socket # Permite a comunicação via socket
import threading # Modulo superior Para executar as threads
import _thread as thread # Modulo basico para executar as threads
import signal # Bibloteca para uso do time out
import sys

def timeout(signum, frame): # Rotina para quando exceder  3 segundos do envio do socket
   
    print ("Exdeu o tempo esperado",signum)
    return

host = '172.20.1.5'  # Host servidor  Moni
port = 4010          # Porta máquina receptora testes

host_servidor = '172.18.11.247'  # Host servidor SEA (PHP e moni como clientes)
port_servidor = 5510           # Servidor para que os clientes enviem os SETs para o SEA

port_reset = 5512

mutex = thread.allocate_lock() # trava a thread para ser executada sózinha

GPIO.setwarnings(False) # desabilita mensagens de aviso

GPIO.setmode(GPIO.BCM) # Modo de endereço dos pinos BCM

spi =spidev.SpiDev() # Parametros da configuração da comunicação SPI (Entrada Portas Analógcas)
spi.open(0,0)
spi.max_speed_hz=1000000

pygame.init() # Inicia o pygame para uso do módulo de voz

pygame.mixer.music.set_volume(0.1) # Ajusta o volume geral das narrações do modulo de voz


bus = smbus.SMBus(1) # Parametros de configuração do módulo MCP23017 - SAIDA DOS RELÊS via I2C
MCP23017 = 0X20 # Endereço do módulo de saidas dos reles 
MCP3008 = 0
bus.write_byte_data(MCP23017,0x00,0x00) #defina todo GPA como saida 0x00
bus.write_byte_data(MCP23017,0x01,0x00) #defina todo GPB como saida 0x01

# Define os pinos que serão entradas:

GPIO.setup(17,GPIO.IN)#GPIO0 (in 1)
GPIO.setup(18,GPIO.IN)#GPIO1 (in 2)
GPIO.setup(27,GPIO.IN)#GPIO2 (in 3)
GPIO.setup(22,GPIO.IN)#GPIO3 (in 4)
GPIO.setup(23,GPIO.IN)#gpio4 (in 5)
GPIO.setup(24,GPIO.IN)#GPIO5 (in 6)
GPIO.setup(25,GPIO.IN)#GPIO6 (in 7)
GPIO.setup(4,GPIO.IN) #GPIO7 (in 8)

IN1 = GPIO.input(17)
IN2 = GPIO.input(18)
IN3 = GPIO.input(27)
IN4 = GPIO.input(22)
IN5 = GPIO.input(23)
IN6 = GPIO.input(24)
IN7 = GPIO.input(25)
IN8 = GPIO.input(4)
    
global vrg # evita violação em caso de acionamento remoto

global saidaA
global saidaB

saidaA = 0b00000000 # Zera as saidas do port A (saidas do rele 1 ao rele 8 )
saidaB = 0b00000000 # Zera as saidas do port B (saidas dos reles 9 e 10 e dos transistors 11,12,13)

bus.write_byte_data(MCP23017,0x015,0) # Zera saidas do port B
bus.write_byte_data(MCP23017,0x014,0) # Coloca todas as saidas do PORT A em 0

saidaB = saidaB + 0b00001000 # liga LED VERMELHO saida GPB3
bus.write_byte_data(MCP23017,0x015,saidaB)

signal.signal(signal.SIGALRM, timeout) # Inicia o modulo para funcionamento dos time outs


try:  # Conecta com o servidor Moni e envia o reconhecimento "oi"#######################################

  signal.alarm(2)
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  s.connect ((host,port))

  command = ("oi")
  s.send(str.encode(command))
  reply = s.recv(1024)
  print(reply.decode('utf-8'))

  print("Criada conexão TCP IP com:",host,"Port:",port)

  s.close()

  signal.alarm(0)

except Exception as e:

  print("Não conseguiu estabelecer conexão TCP/IP")
  print(e)



############################################### Thread servidor para RESET ##############################

def servidor_reset():

    time.sleep(0.1)

    print("Servidor:",host_servidor,"porta:",port_reset)

    host = '172.18.11.247'
    port = 5512

    while(1):

        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #"AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            print ("Socket para reset criado!\n")
            try:
                s.bind((host, port))
            except socket.error as msg:
                print (msg)
            #print ("Ligação do socket reset completa.\n")
            return s

        def setupConnection():
            s.listen(2)
            conn, address = s.accept()
            print ("Conectado com: " + address[0] + ":" + str(address[1]), "\n")
            return conn


        def dataTransfer(conn):  # Loop de transferencia e recepção de dados

            while True:


                data = conn.recv(1024)  # Recebe o dado
                data = data.decode('utf-8')
                dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                command = dataMessage[0]

                (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e a outra em resto

                if(comando == "SET 7"):

                    print("RECONHECEU RESET")

                    os.system('sudo reboot now')

                conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                conn.close()

        s = setupServer()

        while True:

          print ("Escutando a porta RESET",port_reset, "\n")

          try:

              conn = setupConnection()
              dataTransfer(conn) #,saidaA,saidaB,hs

          except:

              print("Encerrou conexão RESET")

############################################### Thread servidor p/ PHP e MONI #################################################################

print("Servidor:",host_servidor,"porta:",port_servidor)

def servidor_php(saidaA,saidaB,hs,data):

    host = '172.18.11.247'
    port = 5510
   

    while(1):

        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            print ("Socket servidor PHP e MONI criado!\n")
            try:
                s.bind((host, port))
            except socket.error as msg:
                print (msg)
            #print ("Ligação do socket completa.\n")
            return s

        def setupConnection():
            s.listen(5)
            conn, address = s.accept()
            print ("Conectado com: " + address[0] + ":" + str(address[1]), "\n")
            return conn


        def dataTransfer(conn):  # Loop de transferencia e recepção de dados

            #while True:

                global vrg

                data = conn.recv(1024)  # Recebe o dado
                data = data.decode('utf-8')
                dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                command = dataMessage[0]

                (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e eoutra em resto


                if(comando == "SET 1"):
                    print("reconheceu SET 1")
                    php = "AP01"
                    intertravamento(saidaA,saidaB,hs,data,php)

                if(comando == "SET 2"):
                    print("reconheceu SET 2")
                    php = "AP02"
                    intertravamento(saidaA,saidaB,hs,data,php)

                if(comando == "SET 8"):
                    print("Reconheceu SET 8")
                    reset_interfones(saidaA,saidaB)
                        

                # if(comando == "SET 3"):
                    # print("reconheceu SET 3")
                    # php = "AP03"
                    # intertravamento(saidaA,saidaB,hs,data,php)

                # if(comando == "SET 4"):
                    # print("reconheceu SET 4")
                    # php = "AP04"
                    # vrg = 1
                    # logica_garagem(saidaA)

                # if(comando == "SET 5"):
                    # print("reconheceu SET 5")
                    # php = "AP05"
                    # intertravamento(saidaA,saidaB,hs,data,php)

                else:

                    print(comando)

                conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente

                conn.close()


        s = setupServer()

        while True:
            
          time.sleep(3)
          global vrg
          vrg = 0

          print ("\nEscutando a porta",port, "\n")
          try:

              conn = setupConnection()
              dataTransfer(conn)
              print("Oiee")


          except:

              print("Encerrou conexão")


########################## Tradução dos dias da semana para módulo de voz caso usar GTTS (somente online)

if (time.strftime("%A") == "Sunday"):
    dia_da_semana = "Domingo"

if (time.strftime("%A") == "Monday"):
    dia_da_semana = "Segunda feira"

if (time.strftime("%A") == "Tuesday"):
    dia_da_semana = "Terça feira"

if (time.strftime("%A") == "Wednesday"):
    dia_da_semana = "Quarta feira"

if (time.strftime("%A") == "Thursday"):
    dia_da_semana = "Quinta feira"

if (time.strftime("%A") == "Friday"):
    dia_da_semana = "Sexta feira"

if (time.strftime("%A") == "Saturday"):
    dia_da_semana = "Sábado"

global hs
hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
hora = time.strftime('%H:%M')
global h
h = int(time.strftime('%H'))
dia_mes = time.strftime("%d")
y = time.strftime("%Y")
m = time.strftime("%m")
data = time.strftime('%d/%m/%y')

# Cria um arquivo de texto para registro dos eventos do sistema

try:  # caso já exista, escreva que o sistema foi reiniciado

  arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
  arquivo.write("Data: ")
  arquivo.write(data)
  arquivo.write(" ")
  arquivo.write(hs)
  arquivo.write(" Evento: O sistema foi reiniciado")
  arquivo.write("\n")
  arquivo.close()

except FileNotFoundError: # Caso não exista crie um arquivo com o nome /home/pi/log_sea.txt

  with open("/home/pi/log_sea.txt", "a+") as arquivo: # a+ é permissão de leitura e escrita

    arquivo.write(hs,"Criado o arquivo de log para registro de eventos do sistema")


# Rotina para GTTS (API Text to Spech do Google)

def dia_e_hora(hora):
    if (h<12):
      periodo = "Bom dia!"

    if (h>12 and h<18):
      periodo = "Boa tarde!"


    if (h>=18 and h<=23):
      periodo = "Boa noite!"

    voz = gTTS(periodo, lang="pt")
    voz.save("periodo.mp3")
    voz = gTTS("Agora são", lang="pt")
    voz.save("voz_hora.mp3")
    voz = gTTS(hora, lang="pt")
    voz.save("voz_hora1.mp3")

    pygame.mixer.music.load('voz_hora.mp3')
    pygame.mixer.music.play()
    time.sleep(1.2)
    pygame.mixer.music.load('voz_hora1.mp3')
    pygame.mixer.music.play()
    time.sleep(2.5)

# Rotina para GTTS

def dia_semana(dia_da_semana):

    voz = gTTS("e hoje é", lang="pt")
    voz.save("hoje_e.mp3")
    voz = gTTS(dia_da_semana, lang="pt")
    voz.save("dia_semana.mp3")

    pygame.mixer.music.load('hoje_e.mp3')
    pygame.mixer.music.play()
    time.sleep(1.05)
    pygame.mixer.music.load('dia_semana.mp3')
    pygame.mixer.music.play()
    time.sleep(2)

# Rotina para GTTS

def dia_do_mes(dia_mes):

    voz = gTTS(dia_mes, lang="pt")
    voz.save("dia_mes.mp3")
    pygame.mixer.music.load('dia_mes.mp3')
    pygame.mixer.music.play()
    time.sleep(2)

# Rotina para GTTS

def narrador(mensagem):

    try:

        voz = gTTS(mensagem, lang="pt")  # guardamos o nosso texto na variavel voz
        voz.save("mensagem.mp3")  # salvamos com o comando save em mp3
        pygame.mixer.music.load('mensagem.mp3')
        pygame.mixer.music.play()
        print ("Reproduzindo Texto no narrador")
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        print("terminou o narração")

    except:

        print ("narrador não esta funcionando")

# Função que obtem o valor da entrada analógica e converte para 1 ou 0 (1 > 800, max 1023 3.3v)
#  - para esta função usar divisor de tensão na entrada analógica para reduzir a tensão para até no máximo 3.3v

def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.
  if((adcnum >7)or(adcnum <0)):
      return-1
  r =spi.xfer2([1,(8+adcnum)<<4,0])
  adcout =((r[1]&3)<<8)+r[2]
  if (adcout > 600):
    adcout = 1
  else:
    adcout = 0
  return adcout

def get_cpu_temp(): # retorna o valor da temperatura da cpu do CLP
    tempFile = open( "/sys/class/thermal/thermal_zone0/temp" )
    cpu_temp = tempFile.read()
    tempFile.close()
    return float(cpu_temp)/1000

def periodico_1min():

    while(1):
               
        print ("Temperatura da CPU:",round (get_cpu_temp()),"C\n")
        time.sleep(120)
	
	
def intertravamento(saidaA,saidaB,hs,data,php):

    vrg = 1

    IN1 = GPIO.input(17)
    IN2 = GPIO.input(18)
    IN3 = GPIO.input(27)
    IN4 = GPIO.input(22)
    IN5 = GPIO.input(23)
    IN6 = GPIO.input(24)
    IN7 = GPIO.input(25)
    IN8 = GPIO.input(4)
		 
    pm_social = IN1
    pm_eclusa = IN2
    ctw_social = IN3
    ctw_eclusa = IN4
    bt1 = IN5
    bt2 = IN6
    manut = IN7
    quebra_de_vidro = IN8

    try:

        IN1 = GPIO.input(17)
        IN2 = GPIO.input(18)
        IN3 = GPIO.input(27)
        IN4 = GPIO.input(22)
        IN5 = GPIO.input(23)
        IN6 = GPIO.input(24)
        IN7 = GPIO.input(25)
        IN8 = GPIO.input(4)
		 
        pm_social = IN1
        pm_eclusa = IN2
        ctw_social = IN3
        ctw_eclusa = IN4
        bt1 = IN5
        bt2 = IN6
        manut = IN7
        quebra_de_vidro = IN8

        verifica_portão_social = 0
        verifica_portão_eclusa = 0
        cont = 0

        if(ctw_social == 1 or php == "AP01" or bt1 == 1):  # Sinal do CTW Social

            if (pm_eclusa == 1): # Portão da Eclusa Fechado

                print ("Abriu portão social")

                saidaA = saidaA + 0b00000001 #aciona rele 1 (abre portão social)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                time.sleep(3)

                saidaA = saidaA - 0b00000001 #desliga rele 1 (fecha portão social)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                verifica_portão_social = 1

                
                if (h < 12 ):

                    print ("Bom dia")

                    pygame.mixer.music.load('mp3/010.mp3') # Bom dia
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                if (h >= 12 and h < 18 ):

                    print("Boa tarde")

                    pygame.mixer.music.load('mp3/009.mp3') # Boa tarde
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                if (h >= 18 ):

                    print("Boa noite")

                    pygame.mixer.music.load('mp3/150.mp3') # Boa noite
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                try:

                         
                    signal.alarm(2)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = ("7000 185734E13300001")  # Envia abriu portão SOCIAL para a central de monitormento
                    s.send(str.encode(command))

                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
                        
                except:

                    print("Não conseguiu enviar o evento: Abriu portão Externo")
                s.close()

                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Portão Social abriu")
                arquivo.write("\n")
                arquivo.close()

                c = 100 # espera 10 segundos pra fechar ########################### TEMPO DE ESPERA PARA FECHAR PORTÃO SOCIAL
                    
                while c > 0:

                    IN1 = GPIO.input(17)
                    IN4 = GPIO.input(22)
                    pm_social = IN1
                    ctw_eclusa = IN4
                                     
                    if (ctw_eclusa == 1):  # Botão da Eclusa pressionado?
                          
                        print("Espere o fechamento do primeiro portão")
                          
                        pygame.mixer.music.load('mp3/049.mp3') # Espere o fechamento do primeiro portão
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            time.sleep(0.1)
                                            
                    if (pm_social == 1): # Já Fechou portão social
  
                        print ("Já Fechou portão social")

                        try:
                            
                            signal.alarm(2)
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect ((host,port))

                            command = ("7000 185734R13300001")  # Envia fechou portão social para a central de monitormento
                            s.send(str.encode(command))

                            reply = s.recv(1024)
                            print(reply.decode('utf-8'))

                            s.close()
                            
                            signal.alarm(0)
                                
                        except:

                            print("Não conseguiu enviar o evento: Fechou portão social")
                        

                        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                        arquivo.write("Data: ")
                        arquivo.write(data)
                        arquivo.write(" ")
                        arquivo.write(hs)
                        arquivo.write(" Evento: Portão Social fechou")
                        arquivo.write("\n")
                        arquivo.close()

                        verifica_portão_social = 0
                    
                        vrg = 0

                        print ("Portão já fechou")
                        c = 1

                        break
                                            
                    c = c - 1
                    time.sleep(0.1)

            if (pm_eclusa == 0):

                print("Portão da Eclusa esta aberto")

                pygame.mixer.music.load('mp3/049.mp3') # Espere o fechamento do primeiro portão
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                  time.sleep(0.1)


        if(ctw_eclusa == 1 or php == "AP02" or bt2 == 1):
            
            if (pm_social == 1): # Portão Social Fechado

                saidaA = saidaA + 0b00000010 #aciona rele 2 (abre portão eclusa)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                time.sleep(3)
                     
                saidaA = saidaA - 0b00000010 #desliga rele 2 
                bus.write_byte_data(MCP23017,0x014,saidaA)

                print ("Abriu portão eclusa")
                                
                try:

                    signal.alarm(2)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = ("7000 185734E13300003")  # Envia abriu portão da eclusa para a central de monitormento
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))

                    s.close()
                    
                    signal.alarm(0)
                        
                except:
            
                    print("Não conseguiu enviar o evento Abriu portão da Eclusa")
                
              
                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Portão eclusa abriu")
                arquivo.write("\n")
                arquivo.close()
                 
                c = 100 # espera 10 segundos pra fechar
              
                while c > 0:
                    
                    IN2 = GPIO.input(18)
                    IN3 = GPIO.input(27)
                 
                    pm_eclusa = IN2
                    ctw_social = IN3

                    if (ctw_social == 1):  # Botão Social pressionado?

                        print("Espere o fechamento do primeiro portão")

                        pygame.mixer.music.load('mp3/049.mp3')
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            time.sleep(0.1)
					
                    if (pm_eclusa == 1):

                        print("Portão da eclusa já fechou")

                        try:

                            signal.alarm(2)
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect ((host,port))

                            command = ("7000 185734R13300003")  # Envia fechou portão da eclusa para a central de monitormento
                            s.send(str.encode(command))
                            reply = s.recv(1024)
                            print(reply.decode('utf-8'))

                            s.close()
                            
                            signal.alarm(0)

                        except:
                    
                            print("Não conseguiu enviar o evento Fechou portão da Eclusa")
                        
                      
                        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                        arquivo.write("Data: ")
                        arquivo.write(data)
                        arquivo.write(" ")
                        arquivo.write(hs)
                        arquivo.write(" Evento: Portão eclusa fechou")
                        arquivo.write("\n")
                        arquivo.close()
                        
                        c = 1

                    c = c - 1
                    time.sleep(0.1)
				
            if (pm_social == 0):

                print("Espere o fechamento do primeiro portão")

                pygame.mixer.music.load('mp3/049.mp3')
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                  time.sleep(0.1)

    except Exception as err:

        print("Erro na rotina intertravamento",err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina intertravamento\n")
        arquivo.close()
                 

    print("Saiu do intertravamento\n")

    vrg = 0
    

def thread_violacao(saidaA,saidaB,vrg):

    time.sleep(5)


    print ("Iniciou a thread de violação de portões...")

    while(1):

        IN1 = GPIO.input(17)
        IN2 = GPIO.input(18)
        IN3 = GPIO.input(27)
        IN4 = GPIO.input(22)
        IN5 = GPIO.input(23)
        IN6 = GPIO.input(24)
        IN7 = GPIO.input(25)
        IN8 = GPIO.input(4)
         
        pm_social = IN1
        pm_eclusa = IN2
        ctw_social = IN3
        ctw_eclusa = IN4
        bt1 = IN5
        bt2 = IN6
        manut = IN7
        quebra_de_vidro = IN8

        if (vrg == 0 and pm_social == 0):
            
            time.sleep(5)

            if (vrg == 0 and pm_social == 0):
                
                print ("Gerou uma violação da entrada social")

                try:

                    signal.alarm(2)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = ("7000 185734E13000002")  # Envia violação da entrada social
                    s.send(str.encode(command))

                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))

                    s.close()
                    
                    signal.alarm(0)
                    
                except:

                    print("Não conseguiu enviar o evento: Violação da entrada social")
                

                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Violação da entrada social")
                arquivo.write("\n")
                arquivo.close()

                time.sleep(30)

                return vrg

        if (vrg == 0 and pm_eclusa == 0):
            
            time.sleep(5)

            if (vrg == 0 and pm_eclusa == 0):

                print ("Gerou uma violação da entrada da eclusa")

                try:

                    signal.alarm(2)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = ("7000 185734E13000004")  # Envia violação da entrada da eclusa
                    s.send(str.encode(command))

                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))

                    s.close()
                    
                    signal.alarm(0)
                    
                except:

                    print("Não conseguiu enviar o evento: Violação da entrada da eclusa")
                

                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Violação da entrada da eclusa")
                arquivo.write("\n")
                arquivo.close()

                time.sleep(30)

                return vrg

def reset_interfones(saidaA,saidaB):

    print("REINICIANDO INTERFONES")
    
    saidaA = saidaA + 0b10000000 #aciona rele 8 (reset interfones)
    bus.write_byte_data(MCP23017,0x014,saidaA)
    time.sleep(10)
    saidaA = saidaA - 0b10000000 
    bus.write_byte_data(MCP23017,0x014,saidaA)
    
    print("Resetou Interfones")
        
def thread_portao_aberto(saidaA,saidaB):

    IN1 = GPIO.input(17)
    IN2 = GPIO.input(18)
         
    pm_social = IN1
    pm_eclusa = IN2

    conta = 0

    time.sleep(1)

    print ("Iniciou a thread de portão aberto")

    while(1):

        IN1 = GPIO.input(17)
        IN2 = GPIO.input(18)
             
        pm_social = IN1
        pm_eclusa = IN2

        if (pm_social == 0): # Portão abriu

            conta = 120

            while (conta > 0):

                if (pm_social == 1): # Se o portão já fechou sai do while

                    break
                
                if (pm_social == 0): # Se o portão ainda esta aberto conta 2 min
                    
                    time.sleep(1)
                    conta = conta - 1

                    if conta == 1: # Ja deu os 2 min
                        
                        print ("Portão esta aberto a mais de 2 minutos")

                        try:

                            signal.alarm(2)
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect ((host,port))

                            command = ("7000 185734E90600001")  # Envia violação portão aberto
                            s.send(str.encode(command))

                            reply = s.recv(1024)
                            print(reply.decode('utf-8'))

                            s.close()
                            
                            signal.alarm(0)
                            
                        except:

                            print("Não conseguiu enviar o evento: Violação portão aberto")
                        

                        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                        arquivo.write("Data: ")
                        arquivo.write(data)
                        arquivo.write(" ")
                        arquivo.write(hs)
                        arquivo.write(" Evento: Violação Portão")
                        arquivo.write("\n")
                        arquivo.close()

                        print("Enviou evento de portão aberto")

                

    
cont = 0
php = 0
AP01 = 0
vrg = 0
qbv = 0

########################################################### Start das Threads #####################################################

s = threading.Thread(target = servidor_php,args=(saidaA,saidaB,hs,data)) # Inicia o servidor PHP
s.start()

p1 = threading.Thread(target = periodico_1min) # Envia feed back de temperatura do sistema e tensão de baterias a cada minuto
p1.start()

rst = threading.Thread(target = servidor_reset) # Inicia o servidor para reset
rst.start()

##viol = threading.Thread(target = thread_violacao,args=(saidaA,saidaB,vrg)) # Inicia a thread da violação
##viol.start()

##pt_aberto = threading.Thread(target = thread_portao_aberto,args=(saidaA,saidaB))
##pt_aberto.start()
###################################################################################################################################


while(True):

    
    IN1 = GPIO.input(17)
    IN2 = GPIO.input(18)
    IN3 = GPIO.input(27)
    IN4 = GPIO.input(22)
    IN5 = GPIO.input(23)
    IN6 = GPIO.input(24)
    IN7 = GPIO.input(25)
    IN8 = GPIO.input(4)
     
    pm_social = IN1
    pm_eclusa = IN2
    ctw_social = IN3
    ctw_eclusa = IN4
    bt1 = IN5
    bt2 = IN6
    manut = IN7
    quebra_de_vidro = IN8

    hora = time.strftime('%H:%M') # Hora no formato Hora e minutos (Ex. 14:30)
    h = int(time.strftime('%H')) # Somente a hora para uso na rotina do GTTS p/ identificar o periodo (manhã,tarde,noite)
    dia_mes = time.strftime("%d") # Somente o dia do mês (Ex. 15)
    y = time.strftime("%Y") # Somente o Ano (Ex. 2018)
    m = time.strftime("%m") # Somente o mês (Ex. 05)
    dia_mes_ano = (dia_mes,"/",m,"/",y,dia_da_semana)
    dia = str(dia_mes_ano)
    d = (dia_mes,"/",m,"/",y,)

    hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log (14:30:58)
    data = time.strftime('%d/%m/%y') # Data completa para uso nos registros de Log


####################################################### executa uma unica vez #######################################################

    if (cont == 0):

        time.sleep(0.3)

        print ("Programa Automático em execução\n")

        bus.write_byte_data(MCP23017,0x014,0b00000000) # Zera as saídas do Port A (inicia reles de 1 -8 desligados)
        bus.write_byte_data(MCP23017,0x015,0b00000000)  # Zera as saídas do Port B (inicia reles 9,10 desligados, saidas 11,12,13 (transistors)desligados

        cont = 1

        
        pygame.mixer.music.load('mp3/048.mp3') # Sistema carregado
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        time.sleep(1)

        
        print(dia_mes,"/",m,"/",y,dia_da_semana,hora,"hs\n")

        saidaB = saidaB - 0b00001000 # desliga LED VERMELHO saida GPB3
        bus.write_byte_data(MCP23017,0x015,saidaB)

        saidaB = saidaB + 0b00000100 # liga LED AZUL saida GPB3
        bus.write_byte_data(MCP23017,0x015,saidaB)

        saidaB = saidaB + 0b00010000 # liga cooler
        bus.write_byte_data(MCP23017,0x015,saidaB)

        print("Cooler ligado")

        time.sleep(0.5)

        #modo_manutencao(hs,data,0)

        #narrador("Sistema conectado a internet")

        try:

            signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))

            command = ("7000 185734E13000017")  # Envia violação e reset
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))

            s.close()
            
            signal.alarm(0)

        except:

            print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento Equipamento ligado")
        
###########################################################################################################

          
    if(ctw_social == 1 or bt1 == 1):    # Sinal de abertura do portão social (CTW, MONI ou SEA SOFTWARE)

        print("\nEntrada do sinal CTW SOCIAL")

        intertravamento(saidaA,saidaB,hs,data,php)

    if(ctw_eclusa == 1 or bt2 == 1):
        
        print("\nEntrada do sinal CTW ECLUSA")
    
        intertravamento(saidaA,saidaB,hs,data,php)

    if pm_social == 0:

        time.sleep(0.1)

        cont = 40
        
        while cont > 0:

            IN1 = GPIO.input(17)
            IN2 = GPIO.input(18)
   
            pm_social = IN1
            pm_eclusa = IN2

            if pm_social == 0:

                con = cont - 1
                time.sleep(0.1)

            if pm_social == 1:

                #print ("Filtrou ruido pm social")
                
                break

            if cont == 1:

                print ("Gerou uma violação da entrada social")

                try:

                    signal.alarm(2)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = ("7000 185734E13000002")  # Envia violação da entrada social
                    s.send(str.encode(command))

                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))

                    s.close()
                    
                    signal.alarm(0)
                    
                except:

                    print("Não conseguiu enviar o evento: Violação da entrada social")
                

                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Violação da entrada social")
                arquivo.write("\n")
                arquivo.close()

    if pm_eclusa == 0:

        time.sleep(0.1)

        cont = 40
        
        while cont > 0:

            IN1 = GPIO.input(17)
            IN2 = GPIO.input(18)
   
            pm_social = IN1
            pm_eclusa = IN2

            if pm_eclusa == 0:

                con = cont - 1
                time.sleep(0.1)

            if pm_eclusa == 1:

                #print ("Filtrou ruido pm Eclusa")
                
                break

            if cont == 1:

                print ("Gerou uma violação da entrada da eclusa")

                try:

                    signal.alarm(2)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = ("7000 185734E13000004")  # Envia violação da entrada da eclusa
                    s.send(str.encode(command))

                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))

                    s.close()
                    
                    signal.alarm(0)
                    
                except:

                    print("Não conseguiu enviar o evento: Violação da entrada da eclusa")
                

                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Violação da entrada da eclusa")
                arquivo.write("\n")
                arquivo.close()

      		
    if (quebra_de_vidro == 1 and qbv == 0):

        time.sleep(2)

        if (quebra_de_vidro == 1):

            print(dia_mes,"/",m,"/",y,dia_da_semana,hora,"hs\n")
            
            print ("Botão de emergencia (quebra de vidro) acionado!")

            saidaA = saidaA + 0b00000001 #aciona rele 1 (abre portão social)
            bus.write_byte_data(MCP23017,0x014,saidaA)

            saidaA = saidaA + 0b00000010 #aciona rele 2 (abre portão eclusa)
            bus.write_byte_data(MCP23017,0x014,saidaA)

            pygame.mixer.music.load('mp3/030.mp3') # Saida de Emergencia
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            try:

                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185734E13000005")  # Envia violação, trocar por evento de emergencia
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))

                s.close()
                
                signal.alarm(0)

            except:

                print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento Quebra de Vidro")
            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(data)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: EMERGÊNCIA")
            arquivo.write("\n")
            arquivo.close()

            qbv = 1

    if (quebra_de_vidro == 0 and qbv == 1):

        time.sleep(2)

        if (quebra_de_vidro == 0):

            print ("Botão de emergencia (quebra de vidro) RESTAUROU")

            print(dia_mes,"/",m,"/",y,dia_da_semana,hora,"hs\n")

            saidaA = saidaA - 0b00000001 #aciona rele 1 (FECHA portão social)
            bus.write_byte_data(MCP23017,0x014,saidaA)

            saidaA = saidaA - 0b00000010 #aciona rele 2 (FECHOU portão eclusa)
            bus.write_byte_data(MCP23017,0x014,saidaA)

            pygame.mixer.music.load('mp3/030.mp3') # Sistema em modo automático
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            try:

                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185734R13000005")  # Envia violação, quebra de vidro
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))

                s.close()
                
                signal.alarm(0)

            except:

                print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento Restauração Quebra de Vidro")
            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(data)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: RESTAUROU EMERGÊNCIA")
            arquivo.write("\n")
            arquivo.close()

            qbv = 0

       

            
    time.sleep(0.1)
