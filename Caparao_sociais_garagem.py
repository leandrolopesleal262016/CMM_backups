#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# CMM Garagem v1.0 05/10/2018

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
##import json

socket.setdefaulttimeout(3) # Define o timeout do socket

########################################  VARIAVEIS GLOBAIS #############################################

# global garagem_aberto
global abre_garagem
global barreira_1
global barreira_2
global chave_mudanca
global vrg
global saidaA
global saidaB


def timeout(signum, frame): # Rotina para quando exceder  3 segundos do envio do socket

    print ("Exdeu o tempo esperado",signum)
    pass


host = '172.20.1.5'  # Host servidor  Moni
port = 4010          # Porta máquina receptora testes

host_servidor = '0.0.0.0'  # Host servidor SEA (PHP e moni como clientes)
port_servidor = 5510           # Servidor para que os clientes enviem os SETs para o SEA
port_reset = 5512

mutex = thread.allocate_lock() # trava a thread para ser executada sózinha
GPIO.setwarnings(False) # desabilita mensagens de aviso
GPIO.setmode(GPIO.BCM) # Modo de endereço dos pinos BCM

spi =spidev.SpiDev() # Parametros da configuração da comunicação SPI (Entrada Portas Analógcas)
spi.open(0,0)
spi.max_speed_hz=1000000

pygame.init() # Inicia o pygame para uso do módulo de voz
pygame.mixer.music.set_volume(0.3) # Ajusta o volume geral das narrações do modulo de voz

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

b1  = GPIO.input(18) # Barreira 1
b2  = GPIO.input(27) # Barreira 2
mud  = GPIO.input(22) # Barreira 3
pmg = GPIO.input(17) # Ponto magnético do portão
ag  = GPIO.input(23) # Comando para abrir a garagem
inib = GPIO.input(24) # Inibidor
qbv = GPIO.input(25) # Modo manutenção
energ = GPIO.input(4) # Entrada do rele queda de Energia

barreira_1 = b1 # Sensor Barreira 1
barreira_2 = b2 # Sensor Barreira 2
chave_mudanca = mud # Sensor Barreira 3
garagem_aberto = pmg # Ponto magnético garagem aberta
abre_garagem = ag # Comando de abertura do portão Garagem
inibidor = inib # Inibidor para passagem a pé pelas barreiras
emergencia = qbv # Modo manutenção
falha_energia_nobreak = energ # Entrada do rele queda de Energia

saidaA = 0b00000000 # Zera as saidas do port A (saidas do rele 1 ao rele 8 )
saidaB = 0b00000000 # Zera as saidas do port B (saidas dos reles 9 e 10 e dos transistors 11,12,13)

bus.write_byte_data(MCP23017,0x015,0) # Zera saidas do port B
bus.write_byte_data(MCP23017,0x014,0) # Coloca todas as saidas do PORT A em 0

saidaB = saidaB + 0b00001000 # liga LED VERMELHO saida GPmud
bus.write_byte_data(MCP23017,0x015,saidaB)

signal.signal(signal.SIGALRM, timeout) # Inicia o modulo para funcionamento dos time outs

#global dia_da_semana
global hs
hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
hora = time.strftime('%H:%M')
global h
h = int(time.strftime('%H'))
dia_mes = time.strftime("%d")
y = time.strftime("%Y")
m = time.strftime("%m")
global date
date = time.strftime('%d/%m/%y')

################################################# Clases ##################################################

class Evento:

    def __init__(self,cliente):

        self.protocolo = "7000 18"  # Protocolo
        self.cliente = cliente  # Cliete
        self.zona = "00" # Partição
        self.finalizador = "" # Finalizador
      
    def enviar_contact_id(self,cond,evento,setor):

        self.cond = cond
        self.evento = evento
        self.setor = setor
        protocolo = self.protocolo
        cliente = self.cliente
        zona = self.zona
        
        tupla = (protocolo,cliente,cond,evento,zona,setor) # Monta a string para enviar
##        print("tupla",tupla)
        contact_texto = str(tupla)
        
        a = (contact_texto.split ("'")[1])
        b = (contact_texto.split ("'")[3])
        c = (contact_texto.split ("'")[5])
        d = (contact_texto.split ("'")[7])
        e = (contact_texto.split ("'")[9])
        g = ""
       
        t = (a,cliente,b,c,d,e,g)
        cliente = str(cliente)
        g = str(g)
        
        evento = (a + cliente + b + c + d + e + g) # Junta as partes dixando nulo os espaços
        
        arquivo = open("buffer_eventos.txt", "a+") # Escreve o evento no registro de log
        arquivo.write( evento + "\n")
        arquivo.close()

        try:
             
            #signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))

            command = (evento)  # Envia evento
            s.send(str.encode(command))

            reply = s.recv(1024)
            print(reply.decode('utf-8'))
            #signal.alarm(0)
                
        except:

            print("Evento não enviado, colocado no buffer")
            
            arquivo = open("buffer_eventos.txt", "a+") # Escreve o evento no registro de log
            arquivo.write( evento + "\n")
            arquivo.close()
            
        s.close()


################################################# Thread servidor para RESET ##############################

def servidor_reset():

    print("\nServidor Reset:",host_servidor,":",port_reset)

    host = host_servidor
    port = port_reset

    while(1):

        socket.setdefaulttimeout(9999)

        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #"AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            #print ("Socket para reset criado!\n")
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

                if(comando == "SET 10"):

                    print ("Reconheceu o pedido de RESET do sistema")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                   

                    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                    arquivo.write("Data: ")
                    arquivo.write(date)
                    arquivo.write(" ")
                    arquivo.write(hs)
                    arquivo.write(" Evento: Reconheceu o pedido de RESET do sistema")
                    arquivo.write("\n")
                    arquivo.close()
                    
                    os.system('sudo reboot now')

                    

        s = setupServer()

        while True:

          #print ("\nEscutando a porta RESET",port_reset, "\n")

          try:

              conn = setupConnection()
              dataTransfer(conn) #,saidaA,saidaB,hs

          except:

              print("Encerrou conexão RESET")

################################################# AUTO RESET ##############################

def auto_reset():

    time.sleep(0.4)

    contador_reset = 600 # 10 minutos

    arquivo = open("/home/pi/keep_alive.txt", "w") # Escreve o evento no registro de log
    arquivo.write("0")
    arquivo.close()

    print("Auto RESET keep alive funcionando...\n")

    
    while(1):

        arquivo = open('/home/pi/keep_alive.txt','r')
        leitura = arquivo.read()
        arquivo.close()

        

        if leitura == "1":

            print("Dados lidos no arquivo de texto: ",leitura)

            print("Zerando o contador de autorest\n")

            contador_reset = 300 # 5 minutos
            
            arquivo = open("/home/pi/keep_alive.txt", "w") # Escreve o evento no registro de log
            arquivo.write("0")
            arquivo.close()

        if contador_reset == 0:

            print("Reiniciando sistema por falta do keep alive")
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + date + " Evento: AUTORESET CMM Sociais/Garagem\n")
            arquivo.close()


            time.sleep(1)

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(date)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Sistema reiniciado pelo Autoreset por falta do keep alive")
            arquivo.write("\n")
            arquivo.close()
            
            os.system('sudo reboot now')
            
##            contador_reset = 350

        contador_reset = contador_reset - 1
        time.sleep(1)
##        print(contador_reset)

                    

        

############################################### Thread servidor p/ PHP e MONI #################################################################



def servidor_php(saidaA,saidaB,hs,date):

    print("\nServidor p/ Clientes:",host_servidor,":",port_servidor)

    host = host_servidor
    port = port_servidor
    
    vrg = 1

    while(1):

        socket.setdefaulttimeout(9999)

        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            #print ("Socket criado!\n")
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

            while True:

                global vrg
                vrg = 1

                data = conn.recv(1024)  # Recebe o dado
                data = data.decode('utf-8')
                dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                command = dataMessage[0]

                (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e eoutra em resto


                if(comando == "SET 1"):
                    
                    print("reconheceu SET 1")
                    

##                    print ("Abrindo portão Rua",hs)

                    
##                    saidaA = saidaA + 0b00000001 # Abre portão rua
##                    bus.write_byte_data(MCP23017,0x014,saidaA)
##                    time.sleep(3)
##                    saidaA = saidaA - 0b00000001 
##                    bus.write_byte_data(MCP23017,0x014,saidaA)
                    
##                    reply = "ok"
##                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #php = "AP01"
                    #intertravamento(saidaA,saidaB,hs,data,php)

                if(comando == "SET 2"):
                    
                    print("reconheceu SET 2")
                                        
##                    print ("Abrindo portão Eclusa",hs)

##                    reply = ("ok")
##                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()

##                    saidaA = saidaA + 0b00000010 # Abre Eclusa
##                    bus.write_byte_data(MCP23017,0x014,saidaA)
##                    time.sleep(3)
##                    saidaA = saidaA - 0b00000010 
##                    bus.write_byte_data(MCP23017,0x014,saidaA)

                    

                if(comando == "SET 3"):
                    
                    print("reconheceu SET 3")

                    reply = ("ok")
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()

                if(comando == "SET 4"):
                    
                    print("reconheceu SET 4")
                    php = "AP04"
                    vrg = 1
                    logica_garagem(saidaA,saidaB)
                    vrg = 0

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #break

                if(comando == "SET 5"):
                    print("reconheceu SET 5")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #php = "AP05"
                    #intertravamento(saidaA,saidaB,hs,data,php)

                if(comando == "SET 6"):
                    print("SET 6, RESET SOCIAL")

                    reply = "6"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #reset_social(saidaA)

                if(comando == "SET 8"):
                    
                    print("SET 8, RESET ECLUSA")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #reset_eclusa(saidaA)

                if(comando == "SET 9"):
                    
                    print("SET 9, RESET INTERFONES")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #reset_interfones(saidaA)

                if(comando == "SET 10"):
                    
                    print("SET 10")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #auxiliar1(saidaA)

                if(comando == "SET 11"):
                    
                    print("SET 11")
                    
                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    

                if(comando == "SET 12"):
                    
                    print("SET 12")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #apresentacao(saidaA,saidaB)

                if(comando == "SET 13"):
                    
                    print("SET 12")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #apresentacao(saidaA,saidaB)

                if(comando == "SET 14"):
                    
                    print("SET 14")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #apresentacao(saidaA,saidaB)

                if(comando == "SET 15"):
                    
                    print("SET 15")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #apresentacao(saidaA,saidaB)

                if(comando == "SET 16"):
                    
                    print("SET 16")

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                    conn.close()
                    #apresentacao(saidaA,saidaB)

                else:

                    print(comando)

                conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente

                conn.close()


        s = setupServer()

        while True:
            
          time.sleep(1)
          #global vrg
          vrg = 0

          #print ("\nEscutando a porta",port, "\n")
          try:

              conn = setupConnection()
              dataTransfer(conn)
              print("Oiee")


          except:

              print("Encerrou conexão")

#    vrg = 0

#Tradução dos dias da semana para módulo de voz caso usar GTTS (somente online)

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


# Cria um arquivo de texto para registro dos eventos do sistema

try:  # caso já exista, escreva que o sistema foi reiniciado

  arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
  arquivo.write("Data: ")
  arquivo.write(date)
  arquivo.write(" ")
  arquivo.write(hs)
  arquivo.write(" Evento: O sistema foi reiniciado")
  arquivo.write("\n")
  arquivo.close()

except FileNotFoundError: # Caso não exista crie um arquivo com o nome log_sea.txt

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

    voz = gTTS(mensagem, lang="pt")  # guardamos o nosso texto na variavel voz
    voz.save("mensagem.mp3")  # salvamos com o comando save em mp3
    pygame.mixer.music.load('mensagem.mp3')
    pygame.mixer.music.play()
    print ("Reproduzindo Texto no narrador")
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

    print("terminou o narração")


# Função que obtem o valor da entrada analógica e converte para 1 ou 0 (1 > 800, max 1023 3.3v)
#  - para esta função usar divisor de tensão na entrada analógica para reduzir a tensão para até no máximo 3.3v

def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.
  if((adcnum >7)or(adcnum <0)):
      return-1
  r =spi.xfer2([1,(8+adcnum)<<4,0])
  adcout =((r[1]&3)<<8)+r[2]
  if (adcout > 800):
    adcout = 1
  else:
    adcout = 0
  return adcout

def get_cpu_temp(): # retorna o valor da temperatura da cpu do CLP
    tempFile = open( "/sys/class/thermal/thermal_zone0/temp" )
    cpu_temp = tempFile.read()
    tempFile.close()
    return float(cpu_temp)/1000

def periodico_1min(saidaA,saidaB):

  def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso for mair que 800 e zero se for menor.
      
      if((adcnum >7)or(adcnum <0)):
          return-1
      r =spi.xfer2([1,(8+adcnum)<<4,0])
      adcout =((r[1]&3)<<8)+r[2]

      if (adcout > 800):
        adcout = 1
      else:
        adcout = 0
      return adcout

  # Faz a leitura analogica da entrada solicitada (de A0 a A7)

  def ReadChannel(channel):

    media = []
    
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]

    for i in (range(1,31)):
        
        adc = spi.xfer2([1,(8+channel)<<4,0])
        data = ((adc[1]&3) << 8) + adc[2]
        x = data
        media.append(x)
        time.sleep(0.1)

    total = 0
    
    for e in media:

        total += e

    data = (total / len(media))
        
    return data

  # Converte a entrada da leitura analógica solicitada em Volts.

  def ConvertVolts(data,places):

    volts = (data * 20.4698) / 1000
    volts = round(volts,places)
    return volts

  def mede_tensao_baterias():

    media = 0

    for item in range(1,11):

        analog = ReadChannel(0)
        volts = ConvertVolts(analog,1) # Mostra 1 casa decimal depois da virgula

        time.sleep(0.1)

        media = media + volts

    media = (media / 10)
    media = round(media)

            
    arquivo = open("medidor_bateria.txt", "a+") # Escreve o evento no registro de log
    bateria = str (media)
    arquivo.write ("Tensão da bateria Sociais " + bateria + "v " + hs + " " + date)
    arquivo.write("\n")
    arquivo.close()
    
    v1 = media

    bat = 1
	
    if v1<10:

        time.sleep(0.5)

        if v1<10:
            

            print(hs,"A bateria do sistema está baixa\n")

            try:

##                #signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185922E30200006")  # Bateria do sistema está baixa
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                bat = 0
                s.close()
##                #signal.alarm(0)

            except:

                print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento de Bateria do sistema baixa")
                
           

    if v1>10 and bat == 0:

        print(hs,"Bateria Ok\n")

        try:

##            #signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))

            command = ("7000 185922R30200006")  # Bateria do sistema está ok
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))
            s.close()
##            #signal.alarm(0)

        except:

            print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento de Bateria do sistema ok")
        

  print("Iniciou a thread periodico")

  while(1):

    time.sleep(1.5)

    print ("Temperatura da CPU: ",round(get_cpu_temp()),"ºC\n")
    temperatura = round(get_cpu_temp())

    print ("Horario atual",hs)


    mede_tensao_baterias()

    # As temperaturas podem chegar até 85º, porem a partir de 80º o proprio
    # sistema derruba o processamento pela metade para diminuir a temperatura.


    if (temperatura >= 70):

      print ("Atenção!, alta temperatura do processador, verificar o funcionamento do cooler!")

      try:

##          signal.alarm(2)
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s.connect ((host,port))

          command = ("7000 185922E15800006")  # Alta temperatura no processador do SEA (setor 18)
          s.send(str.encode(command))
          reply = s.recv(1024)
          print(reply.decode('utf-8'))
          s.close()
##          signal.alarm(0)

      except:

          print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento de Alta temperatura no processador")
      

      arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
      arquivo.write("Data: ")
      arquivo.write(date)
      arquivo.write(" ")
      arquivo.write(hs)
      arquivo.write(" Evento: Alta temperatura do processador")
      arquivo.write("\n")
      arquivo.close()

    time.sleep(350) # 5 minutos

def logica_inibidor(saidaA,saidaB):

    b1  = GPIO.input(18) # Barreira 1
    b2  = GPIO.input(27) # Barreira 2
    mud  = GPIO.input(22) # Barreira 3
    pmg = GPIO.input(17) # Ponto magnético do portão
    ag  = GPIO.input(23) # Comando para abrir a garagem
    inib = GPIO.input(24) # Inibidor
    qbv = GPIO.input(25) # Quebra de viro
    energ = GPIO.input(4) # Entrada do rele queda de Energia

    barreira_1 = b1 # Sensor Barreira 1
    barreira_2 = b2 # Sensor Barreira 2
    chave_mudanca = mud # Sensor Barreira 3
    garagem_aberto = pmg # Ponto magnético garagem aberta
    abre_garagem = ag # Comando de abertura do portão Garagem
    inibidor = inib # Inibidor para passagem a pé pelas barreiras
    emergencia = qbv # Modo manutenção
    falha_energia_nobreak = energ # Entrada do rele queda de Energia

    global vrg
    vrg = 1

    saidaA = saidaA + 0b00001000 # Abre portão da garagem (pulso Rele 1)
    bus.write_byte_data(MCP23017,0x014,saidaA)
    print("\n\nAbrindo portão da garagem com inibidor",hs)
    time.sleep(1)
    saidaA = saidaA - 0b00001000
    bus.write_byte_data(MCP23017,0x014,saidaA)

    
    pygame.mixer.music.load('mp3/141.mp3') # Abrindo portão com inibidor
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
      time.sleep(0.1)

    try:

        #signal.alarm(2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect ((host,port))

        command = ("7000 185922E13300006")  # Envia "abriu portão da garagem" para o moni
        s.send(str.encode(command))
        reply = s.recv(1024)
        print(reply.decode('utf-8'))
        s.close()
        #signal.alarm(0)

    except:

        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento abriu portão da garagem")
    

    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(date)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Abriu portão da garagem")
    arquivo.write("\n")
    arquivo.close()

    tempo_inibido = 400 # fica aberto 40 segundos com o inibidor
    verificar = 0
    stop30 = 0
    alguem_passou = 0
    nenhum_veiculo_entrando = 0
    passou_pedestre = 0

 #   time.sleep(4) # Tempo para ignorar o acionamento da barreira pelo portão
    
    while (tempo_inibido > 0):

        b1  = GPIO.input(18) # Barreira 1
        b2  = GPIO.input(27) # Barreira 2
        mud  = GPIO.input(22) # Barreira 3
        pmg = GPIO.input(17) # Ponto magnético do portão
        ag  = GPIO.input(23) # Comando para abrir a garagem
        inib = GPIO.input(24) # Inibidor
        qbv = GPIO.input(25) # Modo manutenção
        energ = GPIO.input(4) # Entrada do rele queda de Energia

        barreira_1 = b1 # Sensor Barreira 1
        barreira_2 = b2 # Sensor Barreira 2
        chave_mudanca = mud # Sensor Barreira 3
        garagem_aberto = pmg # Ponto magnético garagem aberta
        abre_garagem = ag # Comando de abertura do portão Garagem
        inibidor = inib # Inibidor para passagem a pé pelas barreiras
        emergencia = qbv # Modo manutenção
        falha_energia_nobreak = energ # Entrada do rele queda de Energia


        if barreira_1 == 0 and barreira_2 == 0: # se acionou a b1 e a b2 juntas
            
            print("Entrando ou saindo veiculo com inibidor!")
            
            time.sleep(2)
            
            pygame.mixer.music.load('mp3/142.mp3') # Não use o inibidor com veiculo
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
              time.sleep(0.1)

            print("avisou do inibidor")
            
           
        if garagem_aberto == 1:
        
            print("\nO portão da garagem já fechou!")

            try:

                #signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185922R13300006")  # Envia Fechou portão da garagem para o moni
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                s.close()
                #signal.alarm(0)

            except:

                print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
            
            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(date)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Fechando portão da Garagem")
            arquivo.write("\n")
            arquivo.close()

            time.sleep(3)
        
            break


        tempo_inibido = tempo_inibido - 1
        time.sleep (0.1)
##
##    if alguem_passou == 0:
##
##        print("Abriram com inibidor, mas não houve passagem")
##        fecha_portao(saidaA,saidaB)
   
    vrg = 0
    return (saidaA,saidaB,vrg)


def fecha_portao(saidaA,saidaB):

     

    b1  = GPIO.input(18) # Barreira 1
    b2  = GPIO.input(27) # Barreira 2
    mud  = GPIO.input(22) # Barreira 3
    pmg = GPIO.input(17) # Ponto magnético do portão
    ag  = GPIO.input(23) # Comando para abrir a garagem
    inib = GPIO.input(24) # Inibidor
    qbv = GPIO.input(25) # Modo manutenção
    energ = GPIO.input(4) # Entrada do rele queda de Energia

    barreira_1 = b1 # Sensor Barreira 1
    barreira_2 = b2 # Sensor Barreira 2
    chave_mudanca = mud # Sensor Barreira 3
    garagem_aberto = pmg # Ponto magnético garagem aberta
    abre_garagem = ag # Comando de abertura do portão Garagem
    inibidor = inib # Inibidor para passagem a pé pelas barreiras
    emergencia = qbv # Modo manutenção
    falha_energia_nobreak = energ # Entrada do rele queda de Energia

    stop7 = 0

    verificando = 0

    def verificar_violacao():

        b1  = GPIO.input(18) # Barreira 1
        b2  = GPIO.input(27) # Barreira 2
        mud  = GPIO.input(22) # Barreira 3
        pmg = GPIO.input(17) # Ponto magnético do portão
        ag  = GPIO.input(23) # Comando para abrir a garagem
        inib = GPIO.input(24) # Inibidor
        qbv = GPIO.input(25) # Modo manutenção
        energ = GPIO.input(4) # Entrada do rele queda de Energia

        barreira_1 = b1 # Sensor Barreira 1
        barreira_2 = b2 # Sensor Barreira 2
        chave_mudanca = mud # Sensor Barreira 3
        garagem_aberto = pmg # Ponto magnético garagem aberta
        abre_garagem = ag # Comando de abertura do portão Garagem
        inibidor = inib # Inibidor para passagem a pé pelas barreiras
        emergencia = qbv # Modo manutenção
        falha_energia_nobreak = energ # Entrada do rele queda de Energia

        verificando = 0

        print("Verificando violação...")

        if(barreira_2 == 0):

            
            verificando = 1
            stop12 = 0

            while verificando == 1:

                b1  = GPIO.input(18) # Barreira 1
                b2  = GPIO.input(27) # Barreira 2
                mud  = GPIO.input(22) # Barreira 3
                pmg = GPIO.input(17) # Ponto magnético do portão
                ag  = GPIO.input(23) # Comando para abrir a garagem
                inib = GPIO.input(24) # Inibidor
                qbv = GPIO.input(25) # Modo manutenção
                energ = GPIO.input(4) # Entrada do rele queda de Energia

                barreira_1 = b1 # Sensor Barreira 1
                barreira_2 = b2 # Sensor Barreira 2
                chave_mudanca = mud # Sensor Barreira 3
                garagem_aberto = pmg # Ponto magnético garagem aberta
                abre_garagem = ag # Comando de abertura do portão Garagem
                inibidor = inib # Inibidor para passagem a pé pelas barreiras
                emergencia = qbv # Modo manutenção
                falha_energia_nobreak = energ # Entrada do rele queda de Energia

                saiu = 0

                if barreira_1 == 0:
                    
                    saiu = 1
                    print("Saindo um veiculo aproveitando portão aberto")
                    stop12 = 0

                    while saiu == 1:

                        b2  = GPIO.input(27) # Barreira 2
                        barreira_2 = b2 # Sensor Barreira 2

                        if stop12 == 0:

                            print("Aguardando veiculo sair para fechar")
                            stop12 = 1

                        if barreira_2 == 1:

                            saiu = 0

                        if saiu == 0:

                            print("Veiculo saiu") # Avisar o Moni
                            

                            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write("Data: ")
                            arquivo.write(date)
                            arquivo.write(" ")
                            arquivo.write(hs)
                            arquivo.write(" Evento: Passagem Saida")
                            arquivo.write("\n")
                            arquivo.close()
                                        
                            fecha_portao(saidaA,saidaB)
                            verificando = 0
                            return
                            

                if barreira_2 == 1:

                    print("Violação de pedestre")
                    
                    violacao_pedestre()

                    verificando = 0
                    return
                    

    def dupla_passagem():

        print ("Dupla passagem",hs) #Avisar o Moni
        
        pygame.mixer.music.load('mp3/099.mp3') # Dupla passagem
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

##        evento.enviar_contact_id('E','130','021') # Evento ou Restauração / Evento / Setor

        try:

            #signal.alarm(2)  # Time out de 3 segundos
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect ((host,port))
            command = ("7000 185922E13000021")  # Envia Dupla passagem para o moni
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))
            s.close()
            #signal.alarm(0)

        except:

            print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Dupla passagem")
            
        

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(date)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Dupla passagem")
        arquivo.write("\n")
        arquivo.close()
            
        fecha_portao(saidaA,saidaB)

    def violacao_pedestre():

        print("Entrou na lógica violação de pedestre") # Avisar o Moni
        
        pygame.mixer.music.load('mp3/143.mp3') #Violação de pedestre
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

##        evento.enviar_contact_id('E','130','015') # Evento ou Restauração / Evento / Setor

        try:

            #signal.alarm(2)  # Time out de 3 segundos
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect ((host,port))
            command = ("7000 185922E13000015")  # Envia vioação garagem para o moni
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))
            s.close()
            #signal.alarm(0)

        except:

            print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento violação garagem")
            
        

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(date)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Violação pedestre garagem")
        arquivo.write("\n")
        arquivo.close()
        
        fecha_portao(saidaA,saidaB)
        
################################################### COMEÇA A FECHAR ##################################

    if garagem_aberto == 1:
        
        print("\nO portão da garagem já fechou!")

##        evento.enviar_contact_id('R','133','006') # Evento ou Restauração / Evento / Setor

        try:

            #signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))

            command = ("7000 185922R13300006")  # Envia Fechou portão da garagem para o moni
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))
            s.close()
            #signal.alarm(0)

        except:

            print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
        
        

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(date)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Fechando portão da Garagem")
        arquivo.write("\n")
        arquivo.close()
    
        return
        #print("\nO proximo comando de fechar vai abrir!")
    
    print("\nAnalisando o fechamento do portão")

    tempo = 150 # Tempo que leva pra fechar = 12 seg.
    stop20 = 0
    stop21 = 0
    carro_na_calcada = 0
    
    while tempo > 0:

        b1  = GPIO.input(18) # Barreira 1
        b2  = GPIO.input(27) # Barreira 2
        mud  = GPIO.input(22) # Barreira 3
        pmg = GPIO.input(17) # Ponto magnético do portão
        ag  = GPIO.input(23) # Comando para abrir a garagem
        inib = GPIO.input(24) # Inibidor
        qbv = GPIO.input(25) # Modo manutenção
        energ = GPIO.input(4) # Entrada do rele queda de Energia

        barreira_1 = b1 # Sensor Barreira 1
        barreira_2 = b2 # Sensor Barreira 2
        chave_mudanca = mud # Sensor Barreira 3
        garagem_aberto = pmg # Ponto magnético garagem aberta
        abre_garagem = ag # Comando de abertura do portão Garagem
        inibidor = inib # Inibidor para passagem a pé pelas barreiras
        emergencia = qbv # Modo manutenção
        falha_energia_nobreak = energ # Entrada do rele queda de Energia

        if barreira_1 == 0: 

            print("Barreira 1 acionou")

            time.sleep(0.2)
            
            if barreira_2 == 1: # Barreira 2 desligada ?

                violacao_pedestre()
                return

            if barreira_2 == 0:

                print("Saida de veiculo aproveitando portão aberto")
                return


        if barreira_2 == 0: 

            print("Barreira 2 acionou")

            time.sleep(0.2)
            
            if barreira_1 == 1:

                print("Chama a lógica verificar violação")
                verificar_violacao() 
                return


            if barreira_1 == 0:

                print("Chama a lógica dupla passagem")
                dupla_passagem()
                return

                    
            
            
        tempo = tempo - 1
        time.sleep(0.1)

        if stop7 == 0:

            print("Verificando possivel violação...")
            stop7 = 1

        if garagem_aberto == 1 and tempo < 80:

##            evento.enviar_contact_id('R','133','006') # Evento ou Restauração / Evento / Setor

            try:

                #signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185922R13300006")  # Envia Fechou portão da garagem para o moni
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                s.close()
                #signal.alarm(0)

            except:

                print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
                
           
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(date)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Fechando portão da Garagem")
            arquivo.write("\n")
            arquivo.close()

            break
        
##    print ("Ignorando a barreira 2 no fechamento...")
##        
##    time.sleep(5) # Ignora o acionamento da barreira 6 segundos antes de terminar de fechar
  
    if garagem_aberto == 0:

        print("Analisando... portão ainda aberto")
        fecha_portao(saidaA,saidaB)
            
    print("Saiu da rotina fechar")
    
    return

 
def logica_garagem(saidaA, saidaB):

     

    global fim
    vrg = 1
    fim = 0
    p = 0

    # print("Ponto magnético antes de abrir o portão:", garagem_aberto)

    saidaA = saidaA + 0b00001000 # Abre portão da garagem (pulso Rele 1)
    bus.write_byte_data(MCP23017,0x014,saidaA)
    print("\n\nAbrindo portão da garagem",hs)
    time.sleep(1)
    saidaA = saidaA - 0b00001000
    bus.write_byte_data(MCP23017,0x014,saidaA)

        
##    pygame.mixer.music.load('mp3/101.mp3') # Abrindo portão da garagem
##    pygame.mixer.music.play()
##    while pygame.mixer.music.get_busy():
##      time.sleep(0.1)

##    evento.enviar_contact_id('E','133','006') # Evento ou Restauração / Evento / Setor

    try:

        #signal.alarm(2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect ((host,port))

        command = ("7000 185922E13300006")  # Envia "abriu portão da garagem" para o moni
        s.send(str.encode(command))
        reply = s.recv(1024)
        print(reply.decode('utf-8'))
        s.close()
        #signal.alarm(0)

    except:

        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento abriu portão da garagem")
    

    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(date)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Abriu portão da garagem")
    arquivo.write("\n")
    arquivo.close()

   
    #time.sleep(4) # Tempo para ignorar o acionamento da barreira pelo portão

    #print("Ponto magnético depois que começa abri o portão:", garagem_aberto)

    t = 300 # Tempo que o portão ficará aberto (18 segundos) 12 seg para abrir + 6 seg aberto 

    while (t > 0):

        b1  = GPIO.input(18) # Barreira 1
        b2  = GPIO.input(27) # Barreira 2
        mud  = GPIO.input(22) # Barreira 3
        pmg = GPIO.input(17) # Ponto magnético do portão
        ag  = GPIO.input(23) # Comando para abrir a garagem
        inib = GPIO.input(24) # Inibidor
        qbv = GPIO.input(25) # Modo manutenção
        energ = GPIO.input(4) # Entrada do rele queda de Energia

        barreira_1 = b1 # Sensor Barreira 1
        barreira_2 = b2 # Sensor Barreira 2
        chave_mudanca = mud # Sensor Barreira 3
        garagem_aberto = pmg # Ponto magnético garagem aberta
        abre_garagem = ag # Comando de abertura do portão Garagem
        inibidor = inib # Inibidor para passagem a pé pelas barreiras
        emergencia = qbv # Modo manutenção
        falha_energia_nobreak = energ # Entrada do rele queda de Energia

        
        if t == 300:

            print("Entrou na logica da garagem")
            
        
        if (barreira_2 == 0): # Alguém acionou a barreira 2 ?

            print("Barreira 2 acionou")

            print ("Verificando...")

            opA = 0
            opB = 0
            op2 = 0
            op3 = 0
            stop1 = 0
            stop2 = 0
            stop3 = 0
            stop4 = 0
            stop5 = 0
            stop10 = 0
			
            b = 300 # aguarda durante 30 segundos
            p = 0

            while op3 == 0: # Enquanto o ciclo não foi concluido

                b1  = GPIO.input(18) # Barreira 1
                b2  = GPIO.input(27) # Barreira 2
                mud  = GPIO.input(22) # Barreira 3
                pmg = GPIO.input(17) # Ponto magnético do portão
                ag  = GPIO.input(23) # Comando para abrir a garagem
                inib = GPIO.input(24) # Inibidor
                qbv = GPIO.input(25) # Modo manutenção
                energ = GPIO.input(4) # Entrada do rele queda de Energia

                barreira_1 = b1 # Sensor Barreira 1
                barreira_2 = b2 # Sensor Barreira 2
                chave_mudanca = mud # Sensor Barreira 3
                garagem_aberto = pmg # Ponto magnético garagem aberta
                abre_garagem = ag # Comando de abertura do portão Garagem
                inibidor = inib # Inibidor para passagem a pé pelas barreiras
                emergencia = qbv # Modo manutenção
                falha_energia_nobreak = energ # Entrada do rele queda de Energia

                aguardando_sair = 0

               
                if (barreira_1 == 0 and opA == 0 and opB == 0 and stop1 == 0):  # Se a barreira 1 está acionada
					
                    print("Entrando um veiculo")
                    opA = 1
                    stop1 = 1
                
                if (barreira_1 == 1 and opA == 0 and stop2 == 0):

                    print("Nenhum veiculo entrando")
                    opB = 1
                    stop2 = 1

                #teste para evitar a violação de pedestre na saida de veiculo
                time.sleep(2)

                if (barreira_1 == 0 and opB == 1 and op2 == 0):

                    print("Saindo um veiculo")
                    op2 = 1
                                      
                if (barreira_1 == 1 and opB == 1 and op2 == 0 and op3 == 0): #Se b1 não está acionada e não há nenhum veiculo entrando

                    
                    if(barreira_2 == 0 and stop10 == 0): # Se a barreira 2 ainda está acionada

                        #print("Verificando...")
                        stop10 = 1

                    if(barreira_2 == 1): # Se a barreira 2 desacionou sem acionar a barreira 1

                        print("Violação de pedestre",hs)

##                        saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
##                        bus.write_byte_data(MCP23017,0x014,saidaA)

##                        saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
##                        bus.write_byte_data(MCP23017,0x015,saidaB)

                        pygame.mixer.music.load('mp3/143.mp3') # Violação da Garagem
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            time.sleep(0.1)

##                        evento.enviar_contact_id('E','130','015') # Evento ou Restauração / Evento / Setor

                        try:

                            #signal.alarm(2)
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect ((host,port))
                            command = ("7000 185922E13000015")  # Violação portão da garagem
                            s.send(str.encode(command))
                            reply = s.recv(1024)
                            print(reply.decode('utf-8'))
                            s.close()
                            #signal.alarm(0)

                        except:

                            print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento de violação da Garagem")
                        

                        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                        arquivo.write("Data: ")
                        arquivo.write(date)
                        arquivo.write(" ")
                        arquivo.write(hs)
                        arquivo.write(" Evento: Violação do portão da Garagem")
                        arquivo.write("\n")
                        arquivo.close()
                                                
                        fecha_portao(saidaA,saidaB)
                        
##                        saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
##                        bus.write_byte_data(MCP23017,0x014,saidaA)

##                        saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
##                        bus.write_byte_data(MCP23017,0x015,saidaB)                        

                        t = 0
                        op3 = 1
                        return (t,op3)

                if (barreira_1 == 0 and opA == 1 and op2 == 0 and aguardando_sair == 0): # Se b1  e op1 (entrando um veiculo) forem verdadeiros

                    aguardando_sair = 1
                    stop3 = 0

                    while aguardando_sair == 1:

                        b1  = GPIO.input(18) # Barreira 1
                        b2  = GPIO.input(27) # Barreira 2
                        barreira_1 = b1 # Sensor Barreira 1
                        barreira_2 = b2 # Sensor Barreira 2
                        
                                            
                        if(barreira_2 == 0 and stop3 == 0): # Se a barreira 2 ainda está acionada

                            print("Aguardando o veiculo entrar...")
                            time.sleep(0.1)
                            aguardando_sair = 1
                            stop3 = 1

                        if(barreira_2 == 1): # Se a barreira 2 desacionou

                            print("Veiculo ja entrou, fechando em 2 segundo...")

##                            pygame.mixer.music.load('mp3/018.mp3') # Entrada de veiculo
##                            pygame.mixer.music.play()
##                            while pygame.mixer.music.get_busy():
##                                time.sleep(0.1)


##                            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
##                            arquivo.write("Data: ")
##                            arquivo.write(data)
##                            arquivo.write(" ")
##                            arquivo.write(hs)
##                            arquivo.write(" Evento: Passagem Entrada")
##                            arquivo.write("\n")
##                            arquivo.close()

                            op3 = 1
                            
                            time.sleep(4)
                            
                            fecha_portao(saidaA,saidaB)
                            aguardando_sair = 0
                            t = 0

                if (barreira_2 == 0 and op2 == 1 and stop4 == 0):

                    print("Aguardando veiculo sair para fechar...")
                    stop4 = 1

                if (barreira_2 == 1 and op2 == 1):

                    print("Veiculo saiu, fechando em 2 segundos.")

                    time.sleep(2)


##                    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
##                    arquivo.write("Data: ")
##                    arquivo.write(data)
##                    arquivo.write(" ")
##                    arquivo.write(hs)
##                    arquivo.write(" Evento: Passagem Saida")
##                    arquivo.write("\n")
##                    arquivo.close()
                    
                    op3 = 1
                    fecha_portao(saidaA,saidaB)
                    t = 0

            fim = 1

        time.sleep(0.1) # Conta 1 milisegundo e subtrai 1 de "t"
        t = t - 1

        if (garagem_aberto == 1 and t < 100):

            break
        
    op3 = 1
	    

    if fim == 0:

        print("\n Não detectou nenhuma entrada nem saida",hs)
        
##        pygame.mixer.music.load('mp3/135.mp3') # Abriu mas não pássou ninguem
##        pygame.mixer.music.play()
##        while pygame.mixer.music.get_busy():
##            time.sleep(0.1)

        fecha_portao(saidaA,saidaB)        
			
    if fim == 1:

        pmg = GPIO.input(17) # Ponto magnético do portão
        garagem_aberto = pmg # Ponto magnético garagem aberta

        #print("Ponto magnético:", garagem_aberto)
        
        
        if garagem_aberto == 0:

            print("FECHANDO O PORTÃO NOVAMENTE")
            fecha_portao(saidaA,saidaB)
            
        if garagem_aberto == 1:
            
            print ("Portão fechado.")
           
            
    fim = 0
    vrg = 0  # Variavel global de controle para controlar violação de portão
    print("Saiu do loop logica da garagem")
    return saidaA


def thread_violacao(saidaA,saidaB):

    time.sleep(0.5)

   
    print("\nIniciou thread de violação\n")

     
    
    while(1):
        

        pmg = GPIO.input(17) # Ponto magnético do portão
        garagem_aberto = pmg # Ponto magnético garagem aberta
               
        if(garagem_aberto == 0 and vrg == 0): # Ponto magnético (Garagem aberta) e portão não foi acionado

            time.sleep(1) # Filtro

            if(garagem_aberto == 0 and vrg == 0):

                print("Garagem abriu sem acionamento",hs)

##                saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
##                bus.write_byte_data(MCP23017,0x014,saidaA)
                
                cont = 3

                while(cont > 0):

                  
                    pygame.mixer.music.load('mp3/053.mp3') # Violação da Garagem
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                        
##                    evento.enviar_contact_id('E','130','006') # Evento ou Restauração / Evento / Setor

                    try:

                        #signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185922E13000006")  # Violação portão da garagem
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))
                        print("Enviou violação portão Garagem para o Moni")
                        s.close()
                        #signal.alarm(0)

                    except:

                        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento de violação da Garagem")
                    

                    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                    arquivo.write("Data: ")
                    arquivo.write(date)
                    arquivo.write(" ")
                    arquivo.write(hs)
                    arquivo.write(" Evento: Violação do portão da Garagem")
                    arquivo.write("\n")
                    arquivo.close()

                    time.sleep(20)

##                    saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
##                    bus.write_byte_data(MCP23017,0x014,saidaA)
      

                if(garagem_aberto == 0 and vrg == 0):

                    cont = cont + 1

                    print("Portão ainda esta aberto")

                    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                    arquivo.write("Data: ")
                    arquivo.write(date)
                    arquivo.write(" ")
                    arquivo.write(hs)
                    arquivo.write(" Evento: Portão ainda aberto")
                    arquivo.write("\n")
                    arquivo.close()

                    #return(saidaA,saidaB)

                if (garagem_aberto == 1 or vrg == 1):

                    time.sleep(0.1)

##                    saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
##                    bus.write_byte_data(MCP23017,0x014,saidaA)
                 
                    cont = 3
                    
                    return(saidaA,saidaB)
                
            return(saidaA,saidaB) # Aleração incluida esta linha (problema: giroflex acinando0
        
def portoes_sociais(saidaA,saidaB,hs,dia_da_semana):

    global vrs
    vrs = 0

    monitorando = 0
    acesso1 = 0
    acesso2 = 0
    cont = 0
    contador = 0
    
    entrega_gas = 0
    disparo_cerca = 0
    
    time.sleep(0.1)

      # Passar o cliente que esta enviando

    print("\nIniciou Thread Portões Sociais")
    
    while(1):
                
        qbv = GPIO.input(25) # Modo manutenção
        emergencia = qbv # Modo manutenção

        saidaA = saidaA        

        def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.
          if((adcnum >7)or(adcnum <0)):
              return-1
          r =spi.xfer2([1,(8+adcnum)<<4,0])
          adcout =((r[1]&3)<<8)+r[2]
          if (adcout > 800):
            adcout = 1
          else:
            adcout = 0
          return adcout

        pm1 = readadc(1)
        pm2 = readadc(2)
        ctw1 = readadc(3) 
        ctw2 = readadc(4)
        ctw3 = readadc(5)
        pm_gas = readadc(6)
        cerca = readadc(7)
       
     
        if cont == 0: # Executa uma unica vez
            
            print("\nMonitorando portões sociais",hora,"hs")
 
            cont = 1


##        if (cerca == 0 and disparo_cerca == 0):
##
##            print ("Disparou cerca eletrica")
##
##            try:
##
##                    signal.alarm(2)
##                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##                    s.connect ((host,port))
##
##                    command = ("7000 185922E13300040")  # Abriu portão do gás
##                    s.send(str.encode(command))
##                    reply = s.recv(1024)
##                    print(reply.decode('utf-8'))
##                    print("Enviou violação de portão do gás")
##                    signal.alarm(0)
##
##            except:
##
##                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Abriu portão do gás")
##            s.close()
##
##            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
##            arquivo.write("Data: ")
##            arquivo.write(data)
##            arquivo.write(" ")
##            arquivo.write(hs)
##            arquivo.write(" Evento: Abriu portão do gás")
##            arquivo.write("\n")
##            arquivo.close()
##
##            entrega_gas = 1
##
##            
##
##        if (cerca == 1 and disparo_cerca == 1):
##
##            time.sleep(0.2)
##            
##            cerca = readadc(7)
##
##            time.sleep(0.2)
##
##            if (cerca == 1):
##                
##                print ("Restaurou Cerca eletrica")
##                
##                try:
##
##                        signal.alarm(2)
##                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##                        s.connect ((host,port))
##
##                        command = ("7000 185922R13300040")  # Fechou portão do gás
##                        s.send(str.encode(command))
##                        reply = s.recv(1024)
##                        print(reply.decode('utf-8'))
##                        print("Enviou Fechou portão gás para o Moni")
##                        signal.alarm(0)
##
##                except:
##
##                        print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão do gás")
##                s.close()
##
##                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
##                arquivo.write("Data: ")
##                arquivo.write(data)
##                arquivo.write(" ")
##                arquivo.write(hs)
##                arquivo.write(" Evento: Fechou portão do gás")
##                arquivo.write("\n")
##                arquivo.close()
##
##                disparo_cerca = 0

            

##        if (pm_gas == 0 and entrega_gas == 0):
##
##            time.sleep(0.2)
##
##            pm_gas = readadc(6)
##
##            time.sleep(0.2)
##
##            if (pm_gas == 0):
##
##                print ("Portão do gás abriu")
##
##                try:
##
##                        signal.alarm(2)
##                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##                        s.connect ((host,port))
##
##                        command = ("7000 185922E13000040")  # Abriu portão do gás
##                        s.send(str.encode(command))
##                        reply = s.recv(1024)
##                        print(reply.decode('utf-8'))
##                        print("Enviou Abriu portão do gás para o Moni")
##                        signal.alarm(0)
##
##                except:
##
##                        print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Abriu portão do gás")
##                s.close()
##
##                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
##                arquivo.write("Data: ")
##                arquivo.write(data)
##                arquivo.write(" ")
##                arquivo.write(hs)
##                arquivo.write(" Evento: Abriu portão do gás")
##                arquivo.write("\n")
##                arquivo.close()
##
##                entrega_gas = 1

            

##        if (pm_gas == 1 and entrega_gas == 1):
##
##            print ("Portão do gás já fechou")
##            
##            try:
##
##                    signal.alarm(2)
##                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##                    s.connect ((host,port))
##
##                    command = ("7000 185922R13000040")  # Fechou portão do gás
##                    s.send(str.encode(command))
##                    reply = s.recv(1024)
##                    print(reply.decode('utf-8'))
##                    print("Enviou Fechou portão gás para o Moni")
##                    signal.alarm(0)
##
##            except:
##
##                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão do gás")
##            s.close()
##
##            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
##            arquivo.write("Data: ")
##            arquivo.write(data)
##            arquivo.write(" ")
##            arquivo.write(hs)
##            arquivo.write(" Evento: Fechou portão do gás")
##            arquivo.write("\n")
##            arquivo.close()
##
##            entrega_gas = 0

       
            
        if (ctw1 == 1 or ctw3 == 1):# or ctw3 == 1):

            print("ctw1")

            time.sleep(0.2)

            vrs = 1
         
            if (pm2 == 1):
                
                print ("Abrindo portão Rua",hs)

                saidaA = saidaA + 0b00000001 # Abre portão rua
                bus.write_byte_data(MCP23017,0x014,saidaA)
                time.sleep(3)
                saidaA = saidaA - 0b00000001 
                bus.write_byte_data(MCP23017,0x014,saidaA)

                aberto = 0 

                while(aberto < 11): # tempo para evitar a leitura da violação do portão

                     
                    ctw2 = readadc(4)

                    if (ctw2 == 1):

                        print ("Aguarde o fechamento da Eclusa")

                        pygame.mixer.music.load('mp3/049.mp3') # Sistema carregado
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            time.sleep(0.01)

                                                
                    aberto = aberto + 1
                    time.sleep(1)

            vrs = 0

        if (ctw2 == 1 ):

            time.sleep(0.2)

            print ("ctw2")

            vrs = 1

            if (pm1 == 1):
                

                print ("Abrindo portão Eclusa",hs)

                saidaA = saidaA + 0b00000010 # Abre Eclusa
                bus.write_byte_data(MCP23017,0x014,saidaA)
                time.sleep(3)
                saidaA = saidaA - 0b00000010 
                bus.write_byte_data(MCP23017,0x014,saidaA)

                aberto = 0 # tempo para evitar a leitura da violaão do portão

                while(aberto < 11):

                    ctw1 = readadc(3)
                                              
                    if (ctw1 == 1):
                        
                         print ("Aguarde o fechamento do Social")

                         pygame.mixer.music.load('mp3/050.mp3') # Aguarde o fechamento do primeiro portão
                         pygame.mixer.music.play()
                         while pygame.mixer.music.get_busy():
                             time.sleep(0.1)

                    aberto = aberto + 1
                    time.sleep(1)

        if (emergencia == 1):

            print("Botão quebra de vidro acionada",hs)

            
            global vrg

            vrs = 1
            vrg = 1
            
            em_emergencia = 1


            saidaA = saidaA + 0b00000001 # Abre portão rua Rele 1
            bus.write_byte_data(MCP23017,0x014,saidaA)
            time.sleep(1)
            saidaA = saidaA - 0b00000001 
            bus.write_byte_data(MCP23017,0x014,saidaA)

            time.sleep(0.2)

            saidaA = saidaA + 0b00000010 # Abre Eclusa Rele 2
            bus.write_byte_data(MCP23017,0x014,saidaA)
            time.sleep(1)
            saidaA = saidaA - 0b00000010 
            bus.write_byte_data(MCP23017,0x014,saidaA)
            
            time.sleep(0.2)

            saidaA = saidaA + 0b00001000 # Pulso Abre portão da Garagem Rele 4
            bus.write_byte_data(MCP23017,0x014,saidaA)
            time.sleep(1)
            saidaA = saidaA - 0b00001000 
            bus.write_byte_data(MCP23017,0x014,saidaA)

            saidaA = saidaA + 0b00010000 # fecha o foto para manter o portão aberto # Rele 5
            bus.write_byte_data(MCP23017,0x014,saidaA)

            saidaA = saidaA + 0b00000100 # Fecha o foto dos dois portões Sociais Rele 3
            bus.write_byte_data(MCP23017,0x014,saidaA)


            pygame.mixer.music.load('mp3/030.mp3') # Saida de emergencia acionada
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
##            evento.enviar_contact_id('E','130','005') # Evento ou Restauração / Evento / Setor
                

            try:

                #signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185922E13000005")  # Violação quebra de vidro
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                s.close()
                #signal.alarm(0)
                
            except:

                print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Modo teste de funcionamento")

            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(date)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Saida de Emergencia acionada")
            arquivo.write("\n")
            arquivo.close()

            while (em_emergencia == 1):

                qbv = GPIO.input(25) 
                emergencia = qbv

                time.sleep(0.5)
                
                if emergencia == 0:
                    
                    time.sleep(0.5)

                    if emergencia == 0:
                    
                        print ("Saindo do modo de emergencia") # acha rapido

                        pygame.mixer.music.load('mp3/156.mp3') # Botão quebra de vidro desligado
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            time.sleep(0.01)

                        saidaA = saidaA - 0b00000100 # Abre o foto dos dois portões Sociais
                        bus.write_byte_data(MCP23017,0x014,saidaA)

                        time.sleep(0.2)

                        saidaA = saidaA - 0b00010000 # abre o foto para fechar o portão da garagem
                        bus.write_byte_data(MCP23017,0x014,saidaA)

                        time.sleep(10)

                        em_emergencia = 0
                    
                    
            print("Saiu do wile")
                
            vrs = 0
            vrg = 0
             	

def thread_violacao_sociais(saidaA,saidaB):

    #global saidaA,saidaB
    

    print("\nIniciou Thread Violação Portões Sociais")
    
    while(1):
        

        def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.
          if((adcnum >7)or(adcnum <0)):
              return-1
          r =spi.xfer2([1,(8+adcnum)<<4,0])
          adcout =((r[1]&3)<<8)+r[2]
          if (adcout > 800):
            adcout = 1
          else:
            adcout = 0
          return adcout

        pm1 = readadc(1)
        pm2 = readadc(2)
       
        time.sleep(0.5)

               
        if(pm1 == 0 and vrs == 0): # Ponto magnético aberto sem que o portão tenha sido acionado

            time.sleep(1)

            pm1 = readadc(1)

            falso = 0
            filtro = 100 # Filtra por 5 segundos

            while (pm1 == 0 and filtro > 0): # Enquanto o portão esta aberto

                if (pm1 == 0):

                    filtro = filtro - 1
                    
                    time.sleep(0.1)
                    

                if (pm1 == 1):

                    print("Filtrou ruido pm1 Social")
                    falso = 1

                    return falso
               
            if(pm1 == 0 and vrs == 0 and falso == 0):

                print("Portão Social abriu sem acionamento",hs)
                
                cont = 3

                while(cont > 0):

##                    saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
##                    bus.write_byte_data(MCP23017,0x014,saidaA)


                    pygame.mixer.music.load('mp3/051.mp3') # Violação portão social
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)


                    try:

                        #signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185922E13000002")  # Violação portão Social
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))
                        print("Enviou violação portão Social para o Moni")
                        s.close()
                        #signal.alarm(0)

                    except:

                        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento de violação da Garagem")
                    

                    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                    arquivo.write("Data: ")
                    arquivo.write(date)
                    arquivo.write(" ")
                    arquivo.write(hs)
                    arquivo.write(" Evento: Violação do portão Social")
                    arquivo.write("\n")
                    arquivo.close()

                    time.sleep(30)

                    cont = cont-1
                 

                    if (pm1 == 1 or vrs == 1):

                        time.sleep(1)

##                        saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
##                        bus.write_byte_data(MCP23017,0x014,saidaA)

                        time.sleep(1)
                     
                        cont = 0
                        
                        break

        if(pm2 == 0 and vrs == 0): # Ponto magnético aberto sem que o portão tenha sido acionado

            time.sleep(1)

            pm2 = readadc(2)

            falso = 0
            filtro = 100 # Filtra por 5 segundos

            while (pm2 == 0 and filtro > 0): # Enquanto o portão esta aberto

                if (pm2 == 0):

                    filtro = filtro - 1
                    
                    time.sleep(0.1)
                    

                if (pm2 == 1):

                    print("Filtrou ruido pm2 Eclusa")
                    falso = 1

                    return falso
            
            if(pm2 == 0 and vrs == 0 and falso == 0):

                                
                print("Portão Eclusa abriu sem acionamento",hs)
                
                cont = 3

                while(cont > 0):

##                    saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
##                    bus.write_byte_data(MCP23017,0x014,saidaA)


                    pygame.mixer.music.load('mp3/052.mp3') # Violação portão Eclusa
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

##                    evento.enviar_contact_id('E','130','004') # Evento ou Restauração / Evento / Setor


                    try:

                        #signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185922E13000004")  # Violação portão Eclusa
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))
                        print("Enviou violação portão Eclusa para o Moni")
                        s.close()
                        #signal.alarm(0)

                    except:

                        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento de violação da Garagem")
                    

                    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                    arquivo.write("Data: ")
                    arquivo.write(date)
                    arquivo.write(" ")
                    arquivo.write(hs)
                    arquivo.write(" Evento: Violação do portão Eclusa")
                    arquivo.write("\n")
                    arquivo.close()

                    time.sleep(30)

                    cont=cont-1
                 

                    if (pm2 == 1 or vrs == 1):

                        time.sleep(1)

##                        saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
##                        bus.write_byte_data(MCP23017,0x014,saidaA)

                        time.sleep(1)
                     
                        cont = 0
                        
                        break
        
def thread_acende_luz(saidaA,saidaB):

    print("\nIniciou thread da iluminação\n")
    
    while(1):

        pmg = GPIO.input(17) # Ponto magnético do portão
        garagem_aberto = pmg


        if (garagem_aberto == 0):

            print("ligou a luz")

            saidaA = saidaA + 0b00000100 # Acende a luz por 30 segundos
            bus.write_byte_data(MCP23017,0x014,saidaA)

            time.sleep(60)

            saidaA = saidaA - 0b00000100 # Apaga a luz 
            bus.write_byte_data(MCP23017,0x014,saidaA)

            print("desligou a luz")

            time.sleep(10)

def gas_cerca_eletrica():

    time.sleep(1)

    print ("\nIniciou a tred da cerca eletrica e portão do gás")

    disparo_cerca = 0
    entrega_gas = 0

     

    while(1):


        def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.

            if((adcnum >7)or(adcnum <0)):
                return-1

            r =spi.xfer2([1,(8+adcnum)<<4,0])
            adcout =((r[1]&3)<<8)+r[2]

            filtro = 30
            adcout = 0

            while(filtro > 0):

                r =spi.xfer2([1,(8+adcnum)<<4,0])
                adcout =((r[1]&3)<<8)+r[2]

                if (adcout > 800):
                    adcout = 1

                if (adcout < 800):

                    break

                time.sleep(0.1)

            return adcout


        pm_gas = readadc(6)
        cerca = readadc(7)
        
        if (cerca == 0 and disparo_cerca == 0):

            time.sleep(1)

            cerca = readadc(7)

            time.sleep(1)

            if (cerca == 0 and disparo_cerca == 0):

                print ("Disparou cerca eletrica")

##                evento.enviar_contact_id('E','133','040') # Evento ou Restauração / Evento / Setor

                try:

                        #signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185922E13300040")  # Abriu portão do gás
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))
                        print("Enviou violação de portão do gás")
                        s.close()
                        #signal.alarm(0)

                except:

                        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Abriu portão do gás")
                

                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(date)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Abriu portão do gás")
                arquivo.write("\n")
                arquivo.close()

                disparo_cerca = 1

        if (cerca == 1 and disparo_cerca == 1):

            time.sleep(1)
            
            cerca = readadc(7)

            time.sleep(1)

            if (cerca == 1 and disparo_cerca == 1):
                
                print ("Restaurou Cerca eletrica")

##                evento.enviar_contact_id('R','133','040') # Evento ou Restauração / Evento / Setor
                
                try:

                        #signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185922R13300040")  # Fechou portão do gás
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))
                        print("Enviou Fechou portão gás para o Moni")
                        s.close()
                        #signal.alarm(0)
                        

                except:

                        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão do gás")
                

                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(date)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Fechou portão do gás")
                arquivo.write("\n")
                arquivo.close()

                disparo_cerca = 0

            

        if (pm_gas == 0 and entrega_gas == 0):

            time.sleep(1)
            
            pm_gas = readadc(6)
            
            time.sleep(1)

            if (pm_gas == 0):

                print ("Portão do gás abriu")

##                evento.enviar_contact_id('E','133','040') # Evento ou Restauração / Evento / Setor

                try:

                        #signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185922E13300040")  # Abriu portão do gás
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))
                        print("Enviou Abriu portão do gás para o Moni")
                        s.close()
                        #signal.alarm(0)

                except:

                        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Abriu portão do gás")
                        
                

                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(date)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Abriu portão do gás")
                arquivo.write("\n")
                arquivo.close()

                entrega_gas = 1

            

        if (pm_gas == 1 and entrega_gas == 1):

            time.sleep(1)
            
            pm_gas = readadc(6)
            
            time.sleep(1)

            if (pm_gas == 1):

                print ("Portão do gás já fechou")

##                evento.enviar_contact_id('R','133','040') # Evento ou Restauração / Evento / Setor
                
                
                try:

                        #signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185922R13300040")  # Fechou portão do gás
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))
                        print("Enviou Fechou portão gás para o Moni")
                        s.close()
                        #signal.alarm(0)

                except:

                        print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão do gás")
                
                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(date)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Fechou portão do gás")
                arquivo.write("\n")
                arquivo.close()

                entrega_gas = 0

        time.sleep(10)
                                    
cont = 0
energia = 1
aux = 0
periodico = 0

foi_tres_vezes = 0
contagem = 0
mudanca = 0

php = 0
AP01 = 0
vrg = 0
acesso1 = 0
acesso2 = 0
#pmg = GPIO.input(17) # Ponto magnético do portão
#garagem_aberto = pmg # Ponto magnético garagem aberta
falha_nobreak = 0 # Variavel de controle para executar o aviso uma unica vez

########################################################### Start das Threads #####################################################

s = threading.Thread(target = servidor_php,args=(saidaA,saidaB,hs,date)) # Inicia o servidor com endereço 172.20.6.14 porta 5510
s.start()

##p1 = threading.Thread(target = periodico_1min,args=(saidaA,saidaB)) # Envia feed back de temperatura do sistema e tensão de baterias a cada minuto
##p1.start()

rst = threading.Thread(target = servidor_reset) # Inicia o servidor para reset
rst.start()

a_rst = threading.Thread(target = auto_reset) # Inicia auto reset
a_rst.start()

gas = threading.Thread(target = gas_cerca_eletrica) # Inicia o servidor portão do gás e cerca elétrica
gas.start()

#viol = threading.Thread(target = thread_violacao,args=(saidaA,saidaB)) # Inicia a thread da violação
#viol.start()

#viol_s = threading.Thread(target = thread_violacao_sociais,args=(saidaA,saidaB)) # Inicia a thread da violação sociais
#viol_s.start()

lg2 = threading.Thread(target = portoes_sociais,args=(saidaA,saidaB,hs,dia_da_semana)) # Inicia thread logica dos portões sociais
lg2.start()

#luz = threading.Thread(target = thread_acende_luz,args=(saidaA,saidaB)) # Inicia thread liga luzes da garagem
#luz.start()

###################################################################################################################################

contador_keep_alive = 1200 # 2 minutos


while(True):  # Programa principal
    
    b1  = GPIO.input(18) # Barreira 1
    b2  = GPIO.input(27) # Barreira 2
    mud  = GPIO.input(22) # Barreira 3
    pmg = GPIO.input(17) # Ponto magnético do portão
    ag  = GPIO.input(23) # Comando para abrir a garagem
    inib = GPIO.input(24) # Inibidor
    qbv = GPIO.input(25) # Modo manutenção
    energ = GPIO.input(4) # Entrada do rele queda de Energia

    barreira_1 = b1 # Sensor Barreira 1
    barreira_2 = b2 # Sensor Barreira 2
    chave_mudanca = mud # Sensor Barreira 3
    garagem_aberto = pmg # Ponto magnético garagem aberta
    abre_garagem = ag # Comando de abertura do portão Garagem
    inibidor = inib # Inibidor para passagem a pé pelas barreiras
    emergencia = qbv # QUEBRA DE VIDRO
    falha_energia_nobreak = energ # Entrada do rele queda de Energia

    hora = time.strftime('%H:%M') # Hora no formato Hora e minutos (Ex. 14:30)
    h = int(time.strftime('%H')) # Somente a hora para uso na rotina do GTTS p/ identificar o periodo (manhã,tarde,noite)
    dia_mes = time.strftime("%d") # Somente o dia do mês (Ex. 15)
    y = time.strftime("%Y") # Somente o Ano (Ex. 2018)
    m = time.strftime("%m") # Somente o mês (Ex. 05)
    dia_mes_ano = (dia_mes,"/",m,"/",y,dia_da_semana)
    dia = str(dia_mes_ano)
    d = (dia_mes,"/",m,"/",y,)

    hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log (14:30:58)
    date = time.strftime('%d/%m/%y') # Data completa para uso nos registros de Log

     
####################################################### executa uma unica vez #######################################################
   
    if (cont == 0):
        

        bus.write_byte_data(MCP23017,0x014,0b00000000) # Zera as saídas do Port A (inicia reles de 1 -8 desligados)
        bus.write_byte_data(MCP23017,0x015,0b00000000)  # Zera as saídas do Port B (inicia reles 9,10 desligados, saidas 11,12,13 (transistors)desligados

        cont = 1


        pygame.mixer.music.load('mp3/048.mp3') # Sistema carregado
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.01)

        time.sleep(1)


        print("\n",dia_mes,"/",m,"/",y,dia_da_semana)
        print ("\n",hora,"hs\n")

        saidaB = saidaB - 0b00001000 # desliga LED VERMELHO saida GPmud
        bus.write_byte_data(MCP23017,0x015,saidaB)

        saidaB = saidaB + 0b00000100 # liga LED AZUL saida GPmud
        bus.write_byte_data(MCP23017,0x015,saidaB)

        saidaB = saidaB + 0b00010000 # Liga Cooler
        bus.write_byte_data(MCP23017,0x015,saidaB)
        print("Cooler ligado")
        
   
##        try:
##
##            signal.alarm(2)
##            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##            s.connect ((host,port))
##
##            command = ("7000 185922E13000016")  # Envia RESET CMM
##            s.send(str.encode(command))
##            reply = s.recv(1024)
##            print(reply.decode('utf-8'))
##            s.close()
##            signal.alarm(0)
##
##        except:
##
##            print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento RESET SEA Garagem")
##            
        

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(date)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: RESET CMM Garagem")
        arquivo.write("\n")
        arquivo.close()

        def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.
            
          if((adcnum >7)or(adcnum <0)):
              return-1
          r =spi.xfer2([1,(8+adcnum)<<4,0])
          adcout =((r[1]&3)<<8)+r[2]
          if (adcout > 800):
            adcout = 1
          else:
            adcout = 0
          return adcout

        pm1 = readadc(1)
        pm2 = readadc(2)
        ctw1 = readadc(3)
        ctw2 = readadc(4)
        btn_s1 = readadc(5)
        pm_gas = readadc(6)
        cerca = readadc(7)

        print("\n Status do sensor do portão do gás",pm_gas)
        print ("\n Status da cerca elétrica",cerca)

        
####################################### LOGICA DA GARAGEM ##################################################


  

    if(abre_garagem == 1 and vrg == 0 ):    # Sinal de abertura do portão da garagem (TX, MONI ou SEA SOFTWARE)

        print("Reconheceu o comando abre")

        logica_garagem(saidaA,saidaB)

    
    if(inibidor == 1):

        print ("Reconheceu o comando inibidor")

        logica_inibidor(saidaA,saidaB)

    if (garagem_aberto == 1 and foi_tres_vezes == 1): # Se o portão já fechou zera "foi_tres_vezes"

        foi_tres_vezes = 0

        print("Zerou a variavel foi_tres_vezes")

    if (garagem_aberto == 0 and vrg == 0 and foi_tres_vezes == 0): # Se o portão abriu sem acionamento

        time.sleep(1)

        if (garagem_aberto == 0):
        

            print("Garagem abriu sem acionamento",hs)

                    
##            saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
##            bus.write_byte_data(MCP23017,0x014,saidaA)


            pygame.mixer.music.load('mp3/053.mp3') # Violação da Garagem
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

##            evento.enviar_contact_id('E','130','006') # Evento ou Restauração / Evento / Setor
               

            try:

                #signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185922E13000006")  # Violação portão da garagem
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                print("Enviou violação portão Garagem para o Moni")
                s.close()
                #signal.alarm(0)

            except:

                print("Data: ",date, "Hora: ",hs,"Evento: Não enviou o evento de violação da Garagem")
            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(date)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Violação do portão da Garagem")
            arquivo.write("\n")
            arquivo.close()

            time.sleep(15)

        if contagem < 3:

            contagem = contagem + 1

            print("Enviou o evento",contagem,"vez")
            
            time.sleep(1)

        if contagem == 3:
   
##            saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
##            bus.write_byte_data(MCP23017,0x014,saidaA)

            foi_tres_vezes = 1

            print("Já enviou três vezes o evento de violação de portão")

            contagem = 0

            time.sleep(1)
    
    if (chave_mudanca == 1 and mudanca == 0): # Chave mudança

        time.sleep(1)

        if (chave_mudanca == 1): # Se a chave permanecer ligada, entra em modo de mudança

            print ("Reconheceu comando chave de mudança")

            vrg = 1

                       
            saidaA = saidaA + 0b00001000 # Pulso Abre portão com chave de mudança
            bus.write_byte_data(MCP23017,0x014,saidaA)

            time.sleep(1)
                                
            saidaA = saidaA - 0b00001000 
            bus.write_byte_data(MCP23017,0x014,saidaA)

            saidaA = saidaA + 0b00010000 # fecha o foto para manter o portão aberto
            bus.write_byte_data(MCP23017,0x014,saidaA)
            
            print("\n\nAbrindo portão da garagem com chave de mudança",hs)

            chave = 1

            pygame.mixer.music.load('mp3/151.mp3') # Chave de mudança acionada
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.01)

##            evento.enviar_contact_id('E','130','020') # Evento ou Restauração / Evento / Setor
  
            
            try:

                #signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185922E13000020")  # Envia Chave de mudança acionada (verificar evento e setor)
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                s.close()
                #signal.alarm(0)

            except:

                print("Data: ",date,hs,"Evento: Não conseguiu enviar o evento Chave de mudança garagem")
                
            
            
            print("Sistema em modo de mudança")

            mudanca = 1
            
            vrg = 1    

##            if (chave == 1):
##
##                mud  = GPIO.input(22) # Chave de mudança
##                chave_mudanca = mud
##                  
##                time.sleep(1)

    if (chave_mudanca == 0 and mudanca == 1):

        print("\n\nFechando portão Garagem com chave de mudança")

        saidaA = saidaA - 0b00010000 # abre o foto para fechar garagem
        bus.write_byte_data(MCP23017,0x014,saidaA)        

        pygame.mixer.music.load('mp3/152.mp3') # Chave de mudança desligada
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.01)

        time.sleep(1)

        pygame.mixer.music.load('mp3/021.mp3') # Sistema em modo automatico
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.01)

        chave = 0
        mud = 0
        
        print("Aguardando 7 segundos o portão fechar...")

        time.sleep(7)

        mudanca = 0
            
        vrg = 0    
                     
    

    if (falha_energia_nobreak == 1 and falha_nobreak == 0): # entrada IN8

        print ("Falha de energia na alimentação do no break")

        pygame.mixer.music.load('mp3/137.mp3') # Falha de energia na alimentação do nobreak
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

##        evento.enviar_contact_id('E','301','019') # Evento ou Restauração / Evento / Setor falha na alimenação do noobreak

        try:

            #signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))

            command = ("7000 185922E30100019")  # Envia falha na alimenação do noobreak
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))
            s.close()
            #signal.alarm(0)

        except:

            print("Data: ",date,hs,"Evento: Não conseguiu enviar o evento Falaha alimetação Noobreak Garagem")
        

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(date)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Falha alimetação Noobreak Garagem")
        arquivo.write("\n")
        arquivo.close()

        falha_nobreak = 1
##
    if (falha_energia_nobreak == 0 and falha_nobreak == 1): # entrada IN8

        print ("Restaurou alimentação do no break")

        pygame.mixer.music.load('mp3/138.mp3') # Falha de energia na alimentação do nobreak
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

##        evento.enviar_contact_id('R','301','019')

        try:

            #signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))

            command = ("7000 185922R30100019")  # Envia Restauração alimenação do noobreak
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))
            s.close()
            #signal.alarm(0)

        except:

            print("Data: ",date,hs,"Evento: Não conseguiu enviar o evento Restauração alimetação Noobreak Garagem")
        

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(date)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Restauração alimetação Noobreak")
        arquivo.write("\n")
        arquivo.close()

        falha_nobreak = 0

    if contador_keep_alive == 0:

        print("\nRegistrado keep alive = 1")

        arquivo = open("/home/pi/keep_alive.txt", "w") # Escreve o evento no registro de log
        arquivo.write("1")
        arquivo.close()

        contador_keep_alive = 1200 # 2 minutos
        
    contador_keep_alive = contador_keep_alive - 1    

    time.sleep(0.1)
        
