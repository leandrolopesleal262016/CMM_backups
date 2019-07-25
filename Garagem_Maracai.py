#!/usr/bin/env python3
# -*- coding:utf-8 -*-

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

#######################################  VARIAVEIS GLOBAIS #############################################

global abre_garagem
global barreira_1
global barreira_2
global chave_mudanca
global vrg

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

#global dia_da_semana
global hs
hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
hora = time.strftime('%H:%M')
global h
h = int(time.strftime('%H'))
dia_mes = time.strftime("%d")
y = time.strftime("%Y")
m = time.strftime("%m")
data = time.strftime('%d/%m/%y')



def timeout(signum, frame): # Rotina para quando exceder  3 segundos do envio do socket
    
    print ("Exdeu o tempo esperado",signum)
    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: " + data + " " + hs + " Evento: Exdeu o tempo esperado \n")
    arquivo.close()
    return 
    

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
b3  = GPIO.input(22) # Barreira 3
pmg = GPIO.input(17) # Ponto magnético do portão
ag  = GPIO.input(23) # Comando para abrir a garagem
inib = GPIO.input(24) # Inibidor
manut = GPIO.input(25) # Modo manutenção
energ = GPIO.input(4) # Entrada do rele queda de Energia

barreira_1 = b1 # Sensor Barreira 1
barreira_2 = b2 # Sensor Barreira 2
chave_mudanca = b3 # Sensor Barreira 3
garagem_aberto = pmg # Ponto magnético garagem aberta
abre_garagem = ag # Comando de abertura do portão Garagem
inibidor = inib # Inibidor para passagem a pé pelas barreiras
manutencao = manut # Modo manutenção
falha_energia_nobreak = energ # Entrada do rele queda de Energia

saidaA = 0b00000000 # Zera as saidas do port A (saidas do rele 1 ao rele 8 )
saidaB = 0b00000000 # Zera as saidas do port B (saidas dos reles 9 e 10 e dos transistors 11,12,13)

bus.write_byte_data(MCP23017,0x015,0) # Zera saidas do port B
bus.write_byte_data(MCP23017,0x014,0) # Coloca todas as saidas do PORT A em 0

saidaB = saidaB + 0b00001000 # liga LED VERMELHO saida GPB3
bus.write_byte_data(MCP23017,0x015,saidaB)

signal.signal(signal.SIGALRM, timeout) # Inicia o modulo para funcionamento dos time outs


def servidor_reset():

    try:

        print("\nServidor Reset:",host_servidor,":",port_reset)

        host = host_servidor
        port = 5512

        while(1):

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

                    try:
                        
                        data = conn.recv(1024)  # Recebe o dado
                        data = data.decode('utf-8')
                        dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                        command = dataMessage[0]

                        (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e a outra em resto

                        if(comando == "SET 7"):

                            print ("Reconheceu o pedido de RESET do sistema")

                            conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                            conn.close()

                            os.system('sudo reboot now')

                    except Exception as err:

                        err = str(err)

                        Print("Erro no pedido de reset",err)

            s = setupServer()

            while True:

                #print ("\nEscutando a porta RESET",port_reset, "\n")
                try:

                    conn = setupConnection()
                    dataTransfer(conn) #,saidaA,saidaB,hs

                except:

                    print("Encerrou conexão RESET")
                    
    except Exception as err:

        err = str(err)

        print("Erro na rotina reset", err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina reset " + err + "\n")
        arquivo.close()
############################################### Thread servidor p/ PHP e MONI #################################################################

print("\nServidor p/ Clientes:",host_servidor,":",port_servidor)

def servidor_php(saidaA,saidaB,hs,data):

    try:

        host = host_servidor
        port = port_servidor
        
        vrg = 1

        while(1):

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

                try:

                    global vrg
                    vrg = 1

                    data = conn.recv(1024)  # Recebe o dado
                    data = data.decode('utf-8')
                    dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                    command = dataMessage[0]

                    (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e eoutra em resto


                    if(comando == "SET 1"):
                        print("reconheceu SET 1")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #php = "AP01"
                        #intertravamento(saidaA,saidaB,hs,data,php)

                    if(comando == "SET 2"):
                        print("reconheceu SET 2")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #php = "AP02"
                        #intertravamento(saidaA,saidaB,hs,data,php)

                    if(comando == "SET 3"):
                        print("reconheceu SET 3")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #php = "AP03"
                        #intertravamento(saidaA,saidaB,hs,data,php)

                    if(comando == "SET 4"):
                        print("reconheceu SET 4")
                        php = "AP04"
                        vrg = 1
                        logica_garagem(saidaA,saidaB)
                        vrg = 0
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #break

                    if(comando == "SET 5"):
                        print("reconheceu SET 5")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #php = "AP05"
                        #intertravamento(saidaA,saidaB,hs,data,php)

                    if(comando == "SET 6"):
                        print("SET 6, RESET SOCIAL")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #reset_social(saidaA)

                    if(comando == "SET 8"):
                        
                        print("SET 8, RESET ECLUSA")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #reset_eclusa(saidaA)

                    if(comando == "SET 9"):
                        
                        print("SET 9, RESET INTERFONES")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #reset_interfones(saidaA)

                    if(comando == "SET 10"):
                        
                        print("SET 10")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #auxiliar1(saidaA)

                    if(comando == "SET 11"):
                        
                        print("SET 11")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        

                    if(comando == "SET 12"):
                        
                        print("SET 12")
                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente
                        conn.close()
                        #apresentacao(saidaA,saidaB)

                    else:

                        print(comando)

                        conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente

                        conn.close()
                        
                except Exception  as str:

                    print("Erro no pedido SET",err)

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

    except Exception as err:

        err = str(err)

        print("Erro na rotina servidor PHP",err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina servidor PHP " + err + "\n")
        arquivo.close()
#    vrg = 0



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

except FileNotFoundError: # Caso não exista crie um arquivo com o nome /home/pi//home/pi/log_sea.txt

  with open("/home/pi/log_sea.txt", "a+") as arquivo: # a+ é permissão de leitura e escrita

    arquivo.write(hs,"Criado o arquivo de log para registro de eventos do sistema")


# Rotina para GTTS (API Text to Spech do Google)

def dia_e_hora(hora):

    try:
    
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

    except Exception as err:

        err = str(err)

        print("Erro na rotina dia e hora",err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina dia e hora " + err + "\n")
        arquivo.close()

# Rotina para GTTS

def dia_semana(dia_da_semana):

    try:

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
        
    except exception as err:

        err = str(err)

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina dia semana " + err + "\n")
        arquivo.close()
        
# Rotina para GTTS

def dia_do_mes(dia_mes):

    try:

        voz = gTTS(dia_mes, lang="pt")
        voz.save("dia_mes.mp3")
        pygame.mixer.music.load('dia_mes.mp3')
        pygame.mixer.music.play()
        time.sleep(2)

    except Exception as err:

        err = str(err)
        
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina dia do mes " + err + "\n")
        arquivo.close()

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

    except Exception as err:

        err = str(err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina narrador " + err + "\n")
        arquivo.close()


# Função que obtem o valor da entrada analógica e converte para 1 ou 0 (1 > 800, max 1023 3.3v)
#  - para esta função usar divisor de tensão na entrada analógica para reduzir a tensão para até no máximo 3.3v

def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.

    try:

        if((adcnum >7)or(adcnum <0)):
            return-1
        r =spi.xfer2([1,(8+adcnum)<<4,0])
        adcout =((r[1]&3)<<8)+r[2]
        if (adcout > 600):
            adcout = 1
        else:
            adcout = 0
        return adcout

    except Exception as err:

        err = str(err)

        print("Erro na rotina readadc",err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina readadc " + err + "\n")
        arquivo.close()

def get_cpu_temp(): # retorna o valor da temperatura da cpu do CLP

    try:

        tempFile = open( "/sys/class/thermal/thermal_zone0/temp" )
        cpu_temp = tempFile.read()
        tempFile.close()
        return float(cpu_temp)/1000
    
    except Exception as err:

        err = str(err)

        print("Erro na ronina get cpu temp",err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina get cpu temp " + err + "\n")
        arquivo.close()

def periodico_1min(saidaA,saidaB):

  try:

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
        adc = spi.xfer2([1,(8+channel)<<4,0])
        data = ((adc[1]&3) << 8) + adc[2]
        return data

      # Converte a entrada da leitura analógica solicitada em Volts.

      def ConvertVolts(data,places):

        volts = (data * 20.4698) / 1000
        volts = round(volts,places)
        return volts

      def mede_tensao_baterias():

        analog = ReadChannel(0)
        volts = ConvertVolts(analog,1) # Mostra 1 casa decimal depois da virgula
        print("\nBateria Garagem {}V\n".format(volts))

        arquivo = open("medidor_bateria.txt", "w+") # Escreve o evento no registro de log
        bateria = str (volts)
        arquivo.write (bateria)
        arquivo.write("\n")
        arquivo.close()
        
        v1 = volts

        bat = 1
            
        if v1<10:

          print(hs,"A bateria do sistema está baixa\n")

          try:

            signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))
            
            command = ("7000 185853E30200000")  # Bateria do sistema está baixa
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))
            bat = 0
            
            s.close()
            
            signal.alarm(0)

          except:

            print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de Bateria do sistema baixa")
            
          

        if v1>11 and bat == 0:

            print(hs,"Bateria Ok\n")

            try:

                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185853R30200015")  # Bateria do sistema está ok
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))

                s.close()
                
                signal.alarm(0)

            except:

                print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de Bateria do sistema ok")
            

      while(1):

        time.sleep(1.5)

        print ("Temperatura da CPU: ",round(get_cpu_temp()),"ºC\n")
        temperatura = round(get_cpu_temp())

        print ("Horario atual",hs)


        if (temperatura >= 70):

          print ("Atenção!, alta temperatura do processador, verificar o funcionamento do cooler!")

          try:

              signal.alarm(2)
              s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
              s.connect ((host,port))

              command = ("7000 185853E15800015")  # Alta temperatura no processador do SEA (setor 18)
              s.send(str.encode(command))
              reply = s.recv(1024)
              print(reply.decode('utf-8'))

              s.close()
              
              signal.alarm(0)

          except:

              print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de Alta temperatura no processador")
          

          arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
          arquivo.write("Data: ")
          arquivo.write(data)
          arquivo.write(" ")
          arquivo.write(hs)
          arquivo.write(" Evento: Alta temperatura do processador")
          arquivo.write("\n")
          arquivo.close()

        time.sleep(120)
        
  except Exception as err:

      err = str(err)

      print("Erro na rotina periodico", err)
      arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
      arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina periodico " + err + "\n")
      arquivo.close()
        
def logica_inibidor(saidaA,saidaB):

    try:

        b1  = GPIO.input(18) # Barreira 1
        b2  = GPIO.input(27) # Barreira 2
        b3  = GPIO.input(22) # Barreira 3
        pmg = GPIO.input(17) # Ponto magnético do portão
        ag  = GPIO.input(23) # Comando para abrir a garagem
        inib = GPIO.input(24) # Inibidor
        manut = GPIO.input(25) # Modo manutenção
        energ = GPIO.input(4) # Entrada do rele queda de Energia

        barreira_1 = b1 # Sensor Barreira 1
        barreira_2 = b2 # Sensor Barreira 2
        chave_mudanca = b3 # Sensor Barreira 3
        garagem_aberto = pmg # Ponto magnético garagem aberta
        abre_garagem = ag # Comando de abertura do portão Garagem
        inibidor = inib # Inibidor para passagem a pé pelas barreiras
        manutencao = manut # Modo manutenção
        falha_energia_nobreak = energ # Entrada do rele queda de Energia

        global vrg
        vrg = 1

        saidaA = saidaA + 0b00001000 # Abre portão da garagem (pulso Rele 1)
        bus.write_byte_data(MCP23017,0x014,saidaA)
        print("\n\nAbrindo portão da garagem com inibidor")
        time.sleep(1)
        saidaA = saidaA - 0b00001000
        bus.write_byte_data(MCP23017,0x014,saidaA)

        
        pygame.mixer.music.load('mp3/141.mp3') # Abrindo portão com inibidor
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
          time.sleep(0.1)

        try:

            signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))

            command = ("7000 185853E13300015")  # Envia "abriu portão da garagem" para o moni
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))

            s.close()
            
            signal.alarm(0)

        except:

            print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento abriu portão da garagem")
        

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Abriu portão da garagem")
        arquivo.write("\n")
        arquivo.close()

        tempo_inibido = 150 # fica aberto 15 segundos com o inibidor
        verificar = 0
        stop30 = 0
        alguem_passou = 0
        nenhum_veiculo_entrando = 0
        passou_pedestre = 0

     #   time.sleep(4) # Tempo para ignorar o acionamento da barreira pelo portão
        
        while (tempo_inibido > 0):

            b1  = GPIO.input(18) # Barreira 1
            b2  = GPIO.input(27) # Barreira 2
            b3  = GPIO.input(22) # Barreira 3
            pmg = GPIO.input(17) # Ponto magnético do portão
            ag  = GPIO.input(23) # Comando para abrir a garagem
            inib = GPIO.input(24) # Inibidor
            manut = GPIO.input(25) # Modo manutenção
            energ = GPIO.input(4) # Entrada do rele queda de Energia

            barreira_1 = b1 # Sensor Barreira 1
            barreira_2 = b2 # Sensor Barreira 2
            chave_mudanca = b3 # Sensor Barreira 3
            garagem_aberto = pmg # Ponto magnético garagem aberta
            abre_garagem = ag # Comando de abertura do portão Garagem
            inibidor = inib # Inibidor para passagem a pé pelas barreiras
            manutencao = manut # Modo manutenção
            falha_energia_nobreak = energ # Entrada do rele queda de Energia

            if tempo_inibido == 1:

                if pmg == 1:
                
                    print ("Ja fechou depois de abrir com inibidor")
                    
                    try:

                        signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185853R13300015")  # Envia Fechou portão da garagem para o moni
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))

                        s.close()

                        tempo_inibido = 1
                        
                        signal.alarm(0)

                    except:

                        print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem com inibidor")

                                
            tempo_inibido = tempo_inibido - 1
            time.sleep (0.1)
            
   
        vrg = 0
        return (saidaA,saidaB)

    except Exception as err:

        err = str(err)

        print("Erro na rotina inibidor",err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina inibidor " + err + "\n")
        arquivo.close()
        


def fecha_portao(saidaA,saidaB):

    
    b1  = GPIO.input(18) # Barreira 1
    b2  = GPIO.input(27) # Barreira 2
    b3  = GPIO.input(22) # Barreira 3
    pmg = GPIO.input(17) # Ponto magnético do portão
    ag  = GPIO.input(23) # Comando para abrir a garagem
    inib = GPIO.input(24) # Inibidor
    manut = GPIO.input(25) # Modo manutenção
    energ = GPIO.input(4) # Entrada do rele queda de Energia

    barreira_1 = b1 # Sensor Barreira 1
    barreira_2 = b2 # Sensor Barreira 2
    chave_mudanca = b3 # Sensor Barreira 3
    garagem_aberto = pmg # Ponto magnético garagem aberta
    abre_garagem = ag # Comando de abertura do portão Garagem
    inibidor = inib # Inibidor para passagem a pé pelas barreiras
    manutencao = manut # Modo manutenção
    falha_energia_nobreak = energ # Entrada do rele queda de Energia

    stop7 = 0

    verificando = 0

    def verificar_violacao():

        try:

            b1  = GPIO.input(18) # Barreira 1
            b2  = GPIO.input(27) # Barreira 2
            b3  = GPIO.input(22) # Barreira 3
            pmg = GPIO.input(17) # Ponto magnético do portão
            ag  = GPIO.input(23) # Comando para abrir a garagem
            inib = GPIO.input(24) # Inibidor
            manut = GPIO.input(25) # Modo manutenção
            energ = GPIO.input(4) # Entrada do rele queda de Energia

            barreira_1 = b1 # Sensor Barreira 1
            barreira_2 = b2 # Sensor Barreira 2
            chave_mudanca = b3 # Sensor Barreira 3
            garagem_aberto = pmg # Ponto magnético garagem aberta
            abre_garagem = ag # Comando de abertura do portão Garagem
            inibidor = inib # Inibidor para passagem a pé pelas barreiras
            manutencao = manut # Modo manutenção
            falha_energia_nobreak = energ # Entrada do rele queda de Energia

            verificando = 0

            if(barreira_2 == 1):

                print("Verificando violação...")
                verificando = 1
                stop12 = 0

                while verificando == 1:

                    b1  = GPIO.input(18) # Barreira 1
                    b2  = GPIO.input(27) # Barreira 2
                    b3  = GPIO.input(22) # Barreira 3
                    pmg = GPIO.input(17) # Ponto magnético do portão
                    ag  = GPIO.input(23) # Comando para abrir a garagem
                    inib = GPIO.input(24) # Inibidor
                    manut = GPIO.input(25) # Modo manutenção
                    energ = GPIO.input(4) # Entrada do rele queda de Energia

                    barreira_1 = b1 # Sensor Barreira 1
                    barreira_2 = b2 # Sensor Barreira 2
                    chave_mudanca = b3 # Sensor Barreira 3
                    garagem_aberto = pmg # Ponto magnético garagem aberta
                    abre_garagem = ag # Comando de abertura do portão Garagem
                    inibidor = inib # Inibidor para passagem a pé pelas barreiras
                    manutencao = manut # Modo manutenção
                    falha_energia_nobreak = energ # Entrada do rele queda de Energia

                    saiu = 0

                    if barreira_1 == 1:
                        
                        saiu = 1
                        print("Saindo um veiculo aproveitando portão aberto")
                        stop12 = 0

                        while saiu == 1:

                            b2  = GPIO.input(27) # Barreira 2
                            barreira_2 = b2 # Sensor Barreira 2

                            if stop12 == 0:

                                print("Aguardando veiculo sair para fechar")
                                stop12 = 1

                            if barreira_2 == 0:

                                saiu = 0

                            if saiu == 0:

                                print("Veiculo saiu") # Avisar o Moni
                                

                                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                                arquivo.write("Data: ")
                                arquivo.write(data)
                                arquivo.write(" ")
                                arquivo.write(hs)
                                arquivo.write(" Evento: Passagem Saida")
                                arquivo.write("\n")
                                arquivo.close()
                                            
                                fecha_portao(saidaA,saidaB)
                                verificando = 0
                                return
                                

                    if barreira_2 == 0:

                        print("Violação de pedestre")
                        
                        violacao_pedestre()

                        verificando = 0
                        return
                    
        except Exception as err:

            err = str(err)

            print("Erro na rotina verificar violação", err)

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina verificar violação " + err + "\n")
            arquivo.close()
            

    def dupla_passagem():

        try:

            print ("Dupla passagem") #Avisar o Moni
            
            pygame.mixer.music.load('mp3/099.mp3') # Dupla passagem
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            try:

                signal.alarm(2)  # Time out de 3 segundos
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect ((host,port))
                command = ("7000 185853E13000021")  # Envia Dupla passagem para o moni
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))

                s.close()
                
                signal.alarm(0)

            except:

                print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Dupla passagem")
                
            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(data)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Dupla passagem")
            arquivo.write("\n")
            arquivo.close()
                
            fecha_portao(saidaA,saidaB)
            
        except Exception as err:

            err = str(err)

            print ("Erro na rotina dupla passagem",err)
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina dupla passagem " + err + "\n")
            arquivo.close()
            
    def violacao_pedestre():

        try:

            print("Entrou na lógica violação de pedestre") # Avisar o Moni
            
            pygame.mixer.music.load('mp3/143.mp3') #Violação de pedestre
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            try:

                signal.alarm(2)  # Time out de 3 segundos
                s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                s.connect ((host,port))
                command = ("7000 185853E13000015")  # Envia vioação garagem para o moni
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))

                s.close()
                
                signal.alarm(0)

            except:

                print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento vioação garagem")
                
            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(data)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Violação garagem")
            arquivo.write("\n")
            arquivo.close()
            
            fecha_portao(saidaA,saidaB)

        except Exception as err:

            err = str(err)

            print("Erro na rotina violação de pedestre",err)
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina violação de pedestre " + err + "\n")
            arquivo.close()
        
################################################### COMEÇA A FECHAR ##################################

    if garagem_aberto == 1:
        
        print("\nO portão da garagem já esta fechado!")
##        return  # Foi retirado este return pra testar  10/05/2019 21hs
        #print("\nO proximo comando de fechar vai abrir!")
    
    print("\nFechando portão da garagem")



    try:

        signal.alarm(2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect ((host,port))

        command = ("7000 185853R13300015")  # Envia Fechou portão da garagem para o moni
        s.send(str.encode(command))
##        reply = s.recv(1024)
##        print(reply.decode('utf-8'))

        s.close()
        
        signal.alarm(0)

    except:

        arquivo = open("/home/pi/log_sea.txt", "a+")
        arquivo.write("Data: " + data + " " + hs + "Evento: Não enviou o evento Fechou portão da garagem\n")
        arquivo.close()
        
        print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
            

    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Fechou portão da Garagem apos a rotina fechar")
    arquivo.write("\n")
    arquivo.close()

    tempo = 120
    stop20 = 0
    stop21 = 0
    carro_na_calcada = 0
    
    while tempo > 0:

        try:

            b1  = GPIO.input(18) # Barreira 1
            b2  = GPIO.input(27) # Barreira 2
            b3  = GPIO.input(22) # Barreira 3
            pmg = GPIO.input(17) # Ponto magnético do portão
            ag  = GPIO.input(23) # Comando para abrir a garagem
            inib = GPIO.input(24) # Inibidor
            manut = GPIO.input(25) # Modo manutenção
            energ = GPIO.input(4) # Entrada do rele queda de Energia

            barreira_1 = b1 # Sensor Barreira 1
            barreira_2 = b2 # Sensor Barreira 2
            chave_mudanca = b3 # Sensor Barreira 3
            garagem_aberto = pmg # Ponto magnético garagem aberta
            abre_garagem = ag # Comando de abertura do portão Garagem
            inibidor = inib # Inibidor para passagem a pé pelas barreiras
            manutencao = manut # Modo manutenção
            falha_energia_nobreak = energ # Entrada do rele queda de Energia

            if barreira_2 == 1: 

                print("Barreira 2 acionou")
                
                if barreira_1 == 0:

                    print("Chama a lógica verificar violação")
                    verificar_violacao()
                    return


                if barreira_1 == 1:

                    print("Chama a lógica dupla passagem")
                    dupla_passagem()
                    return

            tempo = tempo - 1
            time.sleep(0.1)
            
            if stop7 == 0:

                print("Verificando possivel violação...")
                stop7 = 1

            if garagem_aberto == 1 and tempo < 80:

                print("Garagem aberto = 1 e tempo menor que 80")

                break

        except Exception as err:

            err = str(err)

            print ("Erro no while tempo > 0",err)
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Erro no while tempo > 0 " + err + "\n")
            arquivo.close()
            
    time.sleep(2)        
    
    if garagem_aberto == 0:

        print("FECHANDO NOVAMENTE PELA ROTINA FECHAR")
        fecha_portao(saidaA,saidaB)
            
    print("Saiu da rotina fechar")
    
    return

 
def logica_garagem(saidaA, saidaB):

    try:

        global fim
        vrg = 1
        fim = 0
        p = 0

        # print("Ponto magnético antes de abrir o portão:", garagem_aberto)

        saidaA = saidaA + 0b00001000 # Abre portão da garagem (pulso Rele 1)
        bus.write_byte_data(MCP23017,0x014,saidaA)
        print("\n\nAbrindo portão da garagem")
        time.sleep(1)
        saidaA = saidaA - 0b00001000
        bus.write_byte_data(MCP23017,0x014,saidaA)

        print("ligou a luz")

        saidaA = saidaA + 0b00000100 # Acende a luz por 30 segundos
        bus.write_byte_data(MCP23017,0x014,saidaA)

            
    ##    pygame.mixer.music.load('mp3/101.mp3') # Abrindo portão da garagem
    ##    pygame.mixer.music.play()
    ##    while pygame.mixer.music.get_busy():
    ##      time.sleep(0.1)

        try:

            signal.alarm(2)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect ((host,port))

            command = ("7000 185853E13300015")  # Envia "abriu portão da garagem" para o moni
            s.send(str.encode(command))
            reply = s.recv(1024)
            print(reply.decode('utf-8'))

            s.close()
            
            signal.alarm(0)

        except:

            print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento abriu portão da garagem")
        

        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Abriu portão da garagem")
        arquivo.write("\n")
        arquivo.close()

       
        time.sleep(4) # Tempo para ignorar o acionamento da barreira pelo portão

        #print("Ponto magnético depois que começa abri o portão:", garagem_aberto)

        t = 180 # Tempo que o portão ficará aberto (18 segundos) caso ninguem entre ou saia

        while (t > 0):

            b1  = GPIO.input(18) # Barreira 1
            b2  = GPIO.input(27) # Barreira 2
            b3  = GPIO.input(22) # Barreira 3
            pmg = GPIO.input(17) # Ponto magnético do portão
            ag  = GPIO.input(23) # Comando para abrir a garagem
            inib = GPIO.input(24) # Inibidor
            manut = GPIO.input(25) # Modo manutenção
            energ = GPIO.input(4) # Entrada do rele queda de Energia

            barreira_1 = b1 # Sensor Barreira 1
            barreira_2 = b2 # Sensor Barreira 2
            chave_mudanca = b3 # Sensor Barreira 3
            garagem_aberto = pmg # Ponto magnético garagem aberta
            abre_garagem = ag # Comando de abertura do portão Garagem
            inibidor = inib # Inibidor para passagem a pé pelas barreiras
            manutencao = manut # Modo manutenção
            falha_energia_nobreak = energ # Entrada do rele queda de Energia

            
            if t == 180:

                print("Entrou na logica da garagem")
                
            
            if (barreira_2 == 1): # Alguém acionou a barreira 2 ?

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
                    b3  = GPIO.input(22) # Barreira 3
                    pmg = GPIO.input(17) # Ponto magnético do portão
                    ag  = GPIO.input(23) # Comando para abrir a garagem
                    inib = GPIO.input(24) # Inibidor
                    manut = GPIO.input(25) # Modo manutenção
                    energ = GPIO.input(4) # Entrada do rele queda de Energia

                    barreira_1 = b1 # Sensor Barreira 1
                    barreira_2 = b2 # Sensor Barreira 2
                    chave_mudanca = b3 # Sensor Barreira 3
                    garagem_aberto = pmg # Ponto magnético garagem aberta
                    abre_garagem = ag # Comando de abertura do portão Garagem
                    inibidor = inib # Inibidor para passagem a pé pelas barreiras
                    manutencao = manut # Modo manutenção
                    falha_energia_nobreak = energ # Entrada do rele queda de Energia

                    aguardando_sair = 0

                   
                    if (barreira_1 == 1 and opA == 0 and opB == 0 and stop1 == 0):  # Se a barreira 1 está acionada
                                            
                        print("Entrando um veiculo")
                        opA = 1
                        stop1 = 1
                    
                    if (barreira_1 == 0 and opA == 0 and stop2 == 0):

                        #print("Nenhum veiculo entrando")
                        opB = 1
                        stop2 = 1

                    #teste para evitar a violação de pedestre na saida de veiculo
                    time.sleep(0.2)

                    if (barreira_1 == 1 and opB == 1 and op2 == 0):

                        print("Saindo um veiculo")
                        op2 = 1
                                          
                    if (barreira_1 == 0 and opB == 1 and op2 == 0 and op3 == 0): #Se b1 não está acionada e não há nenhum veiculo entrando

                        
                        if(barreira_2 == 1 and stop10 == 0): # Se a barreira 2 ainda está acionada

                            #print("Verificando...")
                            stop10 = 1

                        if(barreira_2 == 0): # Se a barreira 2 desacionou sem acionar a barreira 1

                            print("Violação de pedestre")

                            saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
                            bus.write_byte_data(MCP23017,0x014,saidaA)

                            saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
                            bus.write_byte_data(MCP23017,0x015,saidaB)

                            pygame.mixer.music.load('mp3/143.mp3') # Violação da Garagem
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)

                            try:

                                signal.alarm(2)
                                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                s.connect ((host,port))
                                command = ("7000 185853E13000015")  # Violação portão da garagem
                                s.send(str.encode(command))
                                reply = s.recv(1024)
                                print(reply.decode('utf-8'))

                                s.close()
                                
                                signal.alarm(0)

                            except:

                                print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de violação da Garagem")
                            

                            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write("Data: ")
                            arquivo.write(data)
                            arquivo.write(" ")
                            arquivo.write(hs)
                            arquivo.write(" Evento: Violação do portão da Garagem")
                            arquivo.write("\n")
                            arquivo.close()
                                                    
                            fecha_portao(saidaA,saidaB)
                            
                            saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
                            bus.write_byte_data(MCP23017,0x014,saidaA)

                            saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
                            bus.write_byte_data(MCP23017,0x015,saidaB)                        

                            t = 0
                            op3 = 1
                            return (t,op3)

                    if (barreira_1 == 1 and opA == 1 and op2 == 0 and aguardando_sair == 0): # Se b1  e op1 (entrando um veiculo) forem verdadeiros

                        aguardando_sair = 1
                        stop3 = 0

                        while aguardando_sair == 1:

                            b1  = GPIO.input(18) # Barreira 1
                            b2  = GPIO.input(27) # Barreira 2
                            barreira_1 = b1 # Sensor Barreira 1
                            barreira_2 = b2 # Sensor Barreira 2
                            
                                                
                            if(barreira_2 == 1 and stop3 == 0): # Se a barreira 2 ainda está acionada

                                print("Aguardando o veiculo entrar...")
                                time.sleep(0.1)
                                aguardando_sair = 1
                                stop3 = 1

                            if(barreira_2 == 0): # Se a barreira 2 desacionou

                                print("Veiculo ja entrou, fechando em 1 segundo...")

    ##                            pygame.mixer.music.load('mp3/018.mp3') # Entrada de veiculo
    ##                            pygame.mixer.music.play()
    ##                            while pygame.mixer.music.get_busy():
    ##                                time.sleep(0.1)


                                arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                                arquivo.write("Data: ")
                                arquivo.write(data)
                                arquivo.write(" ")
                                arquivo.write(hs)
                                arquivo.write(" Evento: Passagem Entrada")
                                arquivo.write("\n")
                                arquivo.close()

                                op3 = 1
                                
                                time.sleep(2)
                                
                                fecha_portao(saidaA,saidaB)
                                aguardando_sair = 0
                                t = 0

                    if (barreira_2 == 1 and op2 == 1 and stop4 == 0):

                        print("Aguardando veiculo sair para fechar...")
                        stop4 = 1

                    if (barreira_2 == 0 and op2 == 1):

                        print("Veiculo saiu, já pode fechar.")


                        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                        arquivo.write("Data: ")
                        arquivo.write(data)
                        arquivo.write(" ")
                        arquivo.write(hs)
                        arquivo.write(" Evento: Passagem Saida")
                        arquivo.write("\n")
                        arquivo.close()
                        
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

            print("Não detectou nenhuma entrada nem saida")
            
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

        saidaA = saidaA - 0b00000100 # Apaga a luz 
        bus.write_byte_data(MCP23017,0x014,saidaA)

        print("desligou a luz")
        
        print("Saiu do loop logica da garagem")
        return saidaA

    except Exception as err:

        err = str(err)

        print("Erro na rotina logica da garagem")
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina logica da garagem " + err + "\n")
        arquivo.close()


def thread_violacao(saidaA,saidaB):

    try:

        time.sleep(0.5)

        
        pmg = GPIO.input(17) # Ponto magnético do portão
        garagem_aberto = pmg # Ponto magnético garagem aberta

        print("\nIniciou thread de violação\n")
        
        while(1):
                   
            if(garagem_aberto == 0 and vrg == 0): # Ponto magnético (Garagem aberta) e portão não foi acionado

                print("Garagem abriu sem acionamento")
                
                cont = 6

                while(cont > 0):

                    saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
                    bus.write_byte_data(MCP23017,0x014,saidaA)

    ##                saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
    ##                bus.write_byte_data(MCP23017,0x015,saidaB)

                    pygame.mixer.music.load('mp3/053.mp3') # Violação da Garagem
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
    ##
    ##                saidaB = saidaB - 0b00000010 #desliga saida de audio 2 (rele 10)
    ##                bus.write_byte_data(MCP23017,0x015,saidaB)
    ##             
                    

                    try:

                        signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185853E13000015")  # Violação portão da garagem
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))
                        print("Enviou violação de portão para o Moni")

                        s.close()
                        
                        signal.alarm(0)

                    except:

                        print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de violação da Garagem")
                    

                    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                    arquivo.write("Data: ")
                    arquivo.write(data)
                    arquivo.write(" ")
                    arquivo.write(hs)
                    arquivo.write(" Evento: Violação do portão da Garagem")
                    arquivo.write("\n")
                    arquivo.close()

                    time.sleep(30)
          

                    if(garagem_aberto == 0 and vrg == 0):

                        cont = cont + 1

                        print("Fechando portão da garagem pela thread violação")

                        saidaA = saidaA + 0b00001000 # Fecha portão da garagem (pulso Rele )
                        bus.write_byte_data(MCP23017,0x014,saidaA)
                        time.sleep(1)
                        saidaA = saidaA - 0b00001000
                        bus.write_byte_data(MCP23017,0x014,saidaA)

                        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
                        arquivo.write("Data: ")
                        arquivo.write(data)
                        arquivo.write(" ")
                        arquivo.write(hs)
                        arquivo.write(" Evento: Fechando portão da Garagem thread violacao")
                        arquivo.write("\n")
                        arquivo.close()

                        saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
                        bus.write_byte_data(MCP23017,0x014,saidaA)

                        return(saidaA,saidaB)

                    if (garagem_aberto == 1 or vrg == 1):

                        saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
                        bus.write_byte_data(MCP23017,0x014,saidaA)
                     
                        cont = 6
                        
                        return(saidaA,saidaB)

    except Exception as err:

        err = str(err)

        print("Erro na rotina thread violação")
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina thread violacao " + err + "\n")
        arquivo.close()

def portas_de_vidro(saidaA,saidaB,h,dia_da_semana):

    try:

        monitorando = 0
        acesso1 = 0
        acesso2 = 0
        cont = 0
        contador = 0
        
        time.sleep(0.1)

        print("\nIniciou Thread Portas de vidro")
        
        while(1):
            

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

            pm1 = readadc(1)
            pm2 = readadc(2)
            ctw1 = readadc(3) 
            ctw2 = readadc(4)
            btn_s1 = readadc(5)
            btn_s2 = readadc(6)
            aux2 = readadc(7)

         
            if cont == 0: # Executa uma unica vez
                
                print("\nMonitorando portas de vidro",hora,"hs")
     
                cont = 1

                
            if (ctw1 == 1 ): 

                print ("Abrindo porta de vidro 1 CTW")

                saidaA = saidaA + 0b00000001 # Abre porta vidro 1
                bus.write_byte_data(MCP23017,0x014,saidaA)
                time.sleep(5)
                saidaA = saidaA - 0b00000001 # fecha porta vidro 1
                bus.write_byte_data(MCP23017,0x014,saidaA)

                time.sleep(2)

                print("Porta de vidro 1 fechou")

    ##            if (btn_s1 == 1):
    ##
    ##                print("Botão quebra de vidro acionado")
    ##
    ##                saidaA = saidaA + 0b00000001 # Abre porta vidro 1
    ##                bus.write_byte_data(MCP23017,0x014,saidaA)
    ##                
    ##
    ##            if (btn_s1 == 0):
    ##
    ##                saidaA = saidaA - 0b00000001 # fecha porta vidro 1
    ##                bus.write_byte_data(MCP23017,0x014,saidaA)

            if (btn_s1 == 1): 

                print ("Abrindo porta de vidro 1 BTN")

                saidaA = saidaA + 0b00000001 # Abre porta vidro 1
                bus.write_byte_data(MCP23017,0x014,saidaA)
                time.sleep(5)
                saidaA = saidaA - 0b00000001 # fecha porta vidro 1
                bus.write_byte_data(MCP23017,0x014,saidaA)

                time.sleep(2)

                print("Porta de vidro 1 fechou")

            if (ctw2 == 1): # and acesso2 == 0):

                print ("Abrindo porta de vidro 2 CTW")

                saidaA = saidaA + 0b00000010 # Abre porta vidro 2
                bus.write_byte_data(MCP23017,0x014,saidaA)
                time.sleep(5)
                saidaA = saidaA - 0b00000010 # fecha porta vidro 2
                bus.write_byte_data(MCP23017,0x014,saidaA)

                time.sleep(2)

                print("Porta de vidro 2 fechou")

            if (btn_s2 == 1): # and acesso2 == 0):

                print ("Abrindo porta de vidro 2 BTN")

                saidaA = saidaA + 0b00000010 # Abre porta vidro 2
                bus.write_byte_data(MCP23017,0x014,saidaA)
                time.sleep(5)
                saidaA = saidaA - 0b00000010 # fecha porta vidro 2
                bus.write_byte_data(MCP23017,0x014,saidaA)

                time.sleep(2)

                print("Porta de vidro 2 fechou")

    except Exception as err:

        err = str(err)

        print("Erro na rotina portas de vidro",err)
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina portas de vidro " + err + "\n")
        arquivo.close()

def thread_acende_luz(saidaA,saidaB):

    try:

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
                
    except Exception as err:

        err = str(err)

        print("Erro na rotina acende as luzes")
        arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina ecende luzes " + err + "\n")
        arquivo.close()
                                    
cont = 0
energia = 1
aux = 0
periodico = 0

php = 0
AP01 = 0
vrg = 0
acesso1 = 0
acesso2 = 0
#pmg = GPIO.input(17) # Ponto magnético do portão
#garagem_aberto = pmg # Ponto magnético garagem aberta
falha_nobreak = 0 # Variavel de controle para executar o aviso uma unica vez

########################################################### Start das Threads #####################################################

s = threading.Thread(target = servidor_php,args=(saidaA,saidaB,hs,data)) # Inicia o servidor com endereço 172.20.6.14 porta 5510
s.start()

p1 = threading.Thread(target = periodico_1min,args=(saidaA,saidaB)) # Envia feed back de temperatura do sistema e tensão de baterias a cada minuto
p1.start()

rst = threading.Thread(target = servidor_reset) # Inicia o servidor para reset
rst.start()

viol = threading.Thread(target = thread_violacao,args=(saidaA,saidaB)) # Inicia a thread da violação
viol.start()

lg2 = threading.Thread(target = portas_de_vidro,args=(saidaA,saidaB,h,dia_da_semana)) # Inicia thread logica dos portas do Hall
lg2.start()

##luz = threading.Thread(target = thread_acende_luz,args=(saidaA,saidaB)) # Inicia thread liga luzes da garagem
##luz.start()

###################################################################################################################################
try:

        signal.alarm(2)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect ((host,port))

        command = ("7000 185853E13000019")  # Envia RESET CMM
        s.send(str.encode(command))
        reply = s.recv(1024)
        print(reply.decode('utf-8'))

        s.close()
        
        signal.alarm(0)

except Exception as err:

    err = str(err)

    print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento RESET Garagem",err)
    arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: " + data + " " + hs + " Evento: Erro Não conseguiu enviar o evento RESET da garagem " + err + "\n")
    arquivo.close()
    


arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
arquivo.write("Data: " + data + " " + hs + " Evento: RESET CLP \n")
arquivo.close()

pygame.mixer.music.load('mp3/048.mp3') # Sistema carregado
pygame.mixer.music.play()
while pygame.mixer.music.get_busy():
    time.sleep(0.01)

time.sleep(1)

while(True):

        
    b1  = GPIO.input(18) # Barreira 1
    b2  = GPIO.input(27) # Barreira 2
    b3  = GPIO.input(22) # Barreira 3
    pmg = GPIO.input(17) # Ponto magnético do portão
    ag  = GPIO.input(23) # Comando para abrir a garagem
    inib = GPIO.input(24) # Inibidor
    manut = GPIO.input(25) # Modo manutenção
    energ = GPIO.input(4) # Entrada do rele queda de Energia

    barreira_1 = b1 # Sensor Barreira 1
    barreira_2 = b2 # Sensor Barreira 2
    chave_mudanca = b3 # Sensor Barreira 3
    garagem_aberto = pmg # Ponto magnético garagem aberta
    abre_garagem = ag # Comando de abertura do portão Garagem
    inibidor = inib # Inibidor para passagem a pé pelas barreiras
    manutencao = manut # Modo manutenção
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
    data = time.strftime('%d/%m/%y') # Data completa para uso nos registros de Log


####################################################### executa uma unica vez #######################################################

    if (cont == 0):

        try:
        
    ##
    ##        saidaA = saidaA + 0b00000010 # Abre porta vidro 2
    ##        bus.write_byte_data(MCP23017,0x014,saidaA)
    ##
    ##        time.sleep(0.5)
    ##
    ##        saidaA = saidaA + 0b00000001 # Abre porta vidro 1
    ##        bus.write_byte_data(MCP23017,0x014,saidaA)
    ##
    ##        print ("Portas de vidro abertas\n")

            bus.write_byte_data(MCP23017,0x014,0b00000000) # Zera as saídas do Port A (inicia reles de 1 -8 desligados)
            bus.write_byte_data(MCP23017,0x015,0b00000000)  # Zera as saídas do Port B (inicia reles 9,10 desligados, saidas 11,12,13 (transistors)desligados

            cont = 1

    ##        saidaB = saidaB + 0b00000001 # Liga saida de audio 2 (rele 10)
    ##        bus.write_byte_data(MCP23017,0x015,saidaB)

            

    ##        saidaB = saidaB - 0b00000001 # Desliga saida de audio 2 (rele 10)
    ##        bus.write_byte_data(MCP23017,0x015,saidaB)

            time.sleep(0.2)

            print("\n",dia_mes,"/",m,"/",y,dia_da_semana)
            print ("\n",hora,"hs\n")

            saidaB = saidaB - 0b00001000 # desliga LED VERMELHO saida GPB3
            bus.write_byte_data(MCP23017,0x015,saidaB)

            saidaB = saidaB + 0b00000100 # liga LED AZUL saida GPB3
            bus.write_byte_data(MCP23017,0x015,saidaB)

    ##        saidaB = saidaB + 0b00010000 # Liga Cooler
    ##        bus.write_byte_data(MCP23017,0x015,saidaB)

            print("Cooler ligado")

           
            

            #Teste do giroflex
            #saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
            #bus.write_byte_data(MCP23017,0x014,saidaA)
            
    #############################################################################################################

    ##    def ReadChannel(channel):
    ##    adc = spi.xfer2([1,(8+channel)<<4,0])
    ##    data = ((adc[1]&3) << 8) + adc[2]
    ##    return data
        except Exception as err:

            err = str(err)

            print("Erro na rotina executa uma vez",err)
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Errona rotina executa uma vez " + err + "\n")
            arquivo.close()
        

    def readadc(adcnum):  # Faz a leitura da porta analógica e retorna 1 caso a leitura for mair que 800 e zero se for menor.

        try:

            if((adcnum >7)or(adcnum <0)):
                return-1
            r =spi.xfer2([1,(8+adcnum)<<4,0])
            adcout =((r[1]&3)<<8)+r[2]
            if (adcout > 600):
                adcout = 1                
            else:
                adcout = 0
            return adcout

        except Exception as err:

            err = str(err)

            print("Erro na rotina readadc",err)
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina readadc do while principal " + err + "\n")
            arquivo.close()
            

    pm1 = readadc(1)
    pm2 = readadc(2)
    ctw1 = readadc(3)
    ctw2 = readadc(4)
    btn_s1 = readadc(5)
    btn_s2 = readadc(6)
    aux2 = readadc(7)

    

##    if (ctw1 == 1 and acesso1 == 0):
##
##        print ("Abrindo porta de vidro 1")
##
##        saidaA = saidaA + 0b00000001 # Abre porta vidro 1
##        bus.write_byte_data(MCP23017,0x014,saidaA)
##        time.sleep(4)
##        saidaA = saidaA - 0b00000001 # fecha porta vidro 1
##        bus.write_byte_data(MCP23017,0x014,saidaA)
##
##        acesso1 = 1
##
##    if (ctw1 == 0 and acesso1 == 1):
##
##        acesso1 = 0
##
##    if (ctw2 == 1 and acesso2 == 0):
##
##        print ("Abrindo porta de vidro 2")
##
##        saidaA = saidaA + 0b00000010 # Abre porta vidro 2
##        bus.write_byte_data(MCP23017,0x014,saidaA)
##        time.sleep(4)
##        saidaA = saidaA - 0b00000010 # fecha porta vidro 2
##        bus.write_byte_data(MCP23017,0x014,saidaA)
##
##        acesso2 = 1
##
##    if (ctw2 == 0 and acesso2 == 1):
##
##         acesso2 = 0

    if(abre_garagem == 1 and vrg == 0 ):    # Sinal de abertura do portão da garagem (TX, MONI ou SEA SOFTWARE)

        logica_garagem(saidaA,saidaB)

    if(inibidor == 1):

        logica_inibidor(saidaA,saidaB)

    if (chave_mudanca == 1):

        try:
            mudanca = 0

            print("Acionou chave de mudança")
        
            time.sleep(0.2)

            conta = 20

            b3  = GPIO.input(22) # Barreira 3
            chave_mudanca = b3 # Sensor Barreira 3

            if (chave_mudanca == 0):

                print("Filtrou ruido na chave de mudanca")
                pass

            if (chave_mudanca == 1):

##                time.sleep(0.2)
##                mudanca = 1                

                while (conta > 0 ):

                    try:
                    
                        b3  = GPIO.input(22) # Barreira 3
                        chave_mudanca = b3 # Sensor Barreira 3

                        if (chave_mudanca == 0):

                            print("Filtrou oscilação na chave de mudança")

                            time.sleep(0.1)

                            if conta > 0:

                                conta = 0
                                
                            mudanca = 0
##                            conta = 0
                          

                        if (chave_mudanca == 1):

                            if mudanca  == 0:

                                print("Confirmado chave de mudanca acionada")

                            time.sleep(0.1)

                            if conta > 0:

                                conta = conta - 1

                            mudanca = 1

                    except Exception as err:

                        err = str(err)

                        print("Ero na rotina filtro do botao",err)
                        
                if (mudanca == 0):

                    print("Não permaneceu ligada a chave de mudança")
                    

                if (chave_mudanca == 1 and mudanca == 1):

                    print("Em modo de mudança")
                    
                    vrg = 1
                    
                    saidaA = saidaA + 0b00001000 # Abre portão com chave de mudança
                    bus.write_byte_data(MCP23017,0x014,saidaA)

                    time.sleep(1)

                    saidaA = saidaA + 0b00010000 # fecha o foto para manter o portão aberto
                    bus.write_byte_data(MCP23017,0x014,saidaA)
                    
                    print("\n\nAbrindo portão da garagem com chave de mudança")

                    chave = 1

                    pygame.mixer.music.load('mp3/151.mp3') # Chave de mudança acionada
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.01)

                       
                    
                    try:

                        signal.alarm(2)
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.connect ((host,port))

                        command = ("7000 185853E13000020")  # Envia Chave de mudança acionada (verificar evento e setor)
                        s.send(str.encode(command))
                        reply = s.recv(1024)
                        print(reply.decode('utf-8'))

                        s.close()
                        
                        signal.alarm(0)

                    except:

                        print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento Chave de mudança garagem")
                        
                    
                    print("Sistema em modo de mudança")

                    while (chave == 1):

                        b3  = GPIO.input(22) # Chave de mudança
                        chave_mudanca = b3
                
                                   
                        time.sleep(1)

                        if (chave_mudanca == 0):

                            print("\n\nFechando portão Garagem com chave de mudança")

                            saidaA = saidaA - 0b00010000 # abre o foto para fechar o portão
                            bus.write_byte_data(MCP23017,0x014,saidaA)

                            pygame.mixer.music.load('mp3/152.mp3') # Chave de mudança desligada
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.01)

                            time.sleep(1)
                                        
                            saidaA = saidaA - 0b00001000 # Fecha portão
                            bus.write_byte_data(MCP23017,0x014,saidaA)
                            

    ##                        time.sleep(1)
    ##
    ##                        pygame.mixer.music.load('mp3/021.mp3') # Sistema em modo automatico
    ##                        pygame.mixer.music.play()
    ##                        while pygame.mixer.music.get_busy():
    ##                            time.sleep(0.01)

                            chave = 0

                            vrg = 0
            

    ##    if (manutencao == 1):
    ##        
    ##        pygame.mixer.music.load('mp3/122.mp3') # Modo manutenção
    ##        pygame.mixer.music.play()
    ##        while pygame.mixer.music.get_busy():
    ##            time.sleep(0.1)
    ##
    ##        modo_manutencao(hs,data)
                            
        except Exception as err:

            err = str(err)

            print("Erro na rotina chave de mudança",err)
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina chave de mudança " + err + "\n")
            arquivo.close()

            mudanca = 0
            
    if (falha_energia_nobreak == 1 and falha_nobreak == 0): # entrada IN8

        try:

            print ("Falha de energia na alimentação do no break")

            pygame.mixer.music.load('mp3/137.mp3') # Falha de energia na alimentação do nobreak
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            try:

                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185853E30100019")  # Envia falha na alimenação do noobreak
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))

                s.close()
                
                signal.alarm(0)

            except:

                print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento Falaha alimetação Noobreak Garagem")
            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(data)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Falaha alimetação Noobreak Garagem")
            arquivo.write("\n")
            arquivo.close()

            falha_nobreak = 1

        except Exception as err:

            err = str(err)

            print("Erro na rotina falha na alimentação do noobreak")
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina falha de alimentação do noobreak " + err + "\n")
            arquivo.close()

    if (falha_energia_nobreak == 0 and falha_nobreak == 1): # entrada IN8

        try:

            print ("Restaurou alimentação do no break")

            pygame.mixer.music.load('mp3/138.mp3') # Falha de energia na alimentação do nobreak
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

            try:

                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 185853R30100019")  # Envia Restauração alimenação do noobreak
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))

                s.close()
                
                signal.alarm(0)

            except:

                print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento Restauração alimetação Noobreak Garagem")
            

            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(data)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Restauração alimetação Noobreak")
            arquivo.write("\n")
            arquivo.close()

            falha_nobreak = 0

        except Exception as err:

            err = str(err)

            print("Erro na rotina restauração da alimentação do Noobreak")
            arquivo = open("/home/pi/log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: " + data + " " + hs + " Evento: Erro na rotina restauração alimentação do Noobreak" + err + "\n")
            arquivo.close()
            
    
    
    time.sleep(0.1)
