
#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# CMM Oficial com placa de expansão da BRAVAS Technololgy
# Desenvolvido por Leandro Leal  rev. 24/06/2019

import RPi.GPIO as GPIO
import time
from biblioteca_CMM_oficial import Rele,Narrador,Temperatura,Email,Clima,Evento
from biblioteca_QRCODE import Qrcode
from IHM_Sociais import IHM
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
import serial # Para comunicação serial com arduino
import json
import mysql.connector

socket.setdefaulttimeout(2) # limite de 2 segundos para enviar o socket

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
##narrador = Narrador()
temperatura = Temperatura()
##email = Email()
##clima = Clima()
evento = Evento("5987") # Inicia a classe evento com o codigo do cliente
qr1 = Qrcode("172.18.34.249","5987",4,"social","1") # IP,Cliente,rele,portao) - "172.18.34.247","5987",4,"social" ou "eclusa"
qr2 = Qrcode("172.18.34.250","5987",5,"eclusa","0") # IP,Cliente,rele,portao) - "172.18.34.247","5987",4,"social" ou "eclusa"

##ihm = IHM() 

##qrcode = Qrcode() # Instancia a classe do leitor de qrcode
##wiegand = Wiegand()
##rele_qr = Rele_qr() # Instanciar loclamente com o IP do leitor para acionamento do rele do equipamento
## Ex. rele_qr = Rele_qr("172.20.9.5",5000) # Conecta com o Qrcode deste endereço para acionamento do rele e leitura da entrada auxiliar

##print("Conteudo do play1 ",ihm.get_cbox("play1"))

print("Reiniciou o sistema",hs)
 
##############################################  Threads dos programas  ##########################################################

def thread_qrcode1(): # Programa do QR Code 1

    sys.stdout.write("\nPrograma QR Code social em execução\n")

    qr1.start() # Inicia o qr code do portão social
    

def thread_qrcode2(): # Programa do QR Code 2

    sys.stdout.write("\nPrograma QR Code eclusa em execução\n")

    qr2.start() # Inicia o qrcode do portão da eclusa

  
######################################  CLASSES  ###########################################

class Entradas(object): # Inicia a thread leitura das entradas para controle de todos os programas
    
    def __init__(self):            
    
        self.IN1 = wiringpi.digitalRead(300)  # Configuraçoes pinos de entrada necessarios para atualizar as entradas
        self.IN2 = wiringpi.digitalRead(301)  # entradas constantes
        self.IN3 = wiringpi.digitalRead(302)
        self.IN4 = wiringpi.digitalRead(303)
        self.IN5 = wiringpi.digitalRead(304)
        self.IN6 = wiringpi.digitalRead(305)
        self.IN7 = wiringpi.digitalRead(306)
        self.IN8 = wiringpi.digitalRead(307)

        self.A = GPIO.input(4) # Entrada A  # entradas constantes
        self.B = GPIO.input(27) # Entrada B 
        self.C = GPIO.input(22) # Entrada C 
        self.D = GPIO.input(10) # Entrada D

        entradas = []    
        txt = open("/home/pi/CMM/config.txt",'r')    
        for line in txt: 
            entradas.append(line)
        txt.close()
        
        line1 = (entradas[0])         # Coloca na variavel line1 o texto encontrado na linha 1
        line1 = line1.replace("\n","")  # Retira o \n do texto
        line2 = (entradas[1])         
        line2 = line2.replace("\n","")
        line3 = (entradas[2])
        line3 = line3.replace("\n","")
        line4 = (entradas[3])
        line4 = line4.replace("\n","")
        line5 = (entradas[4])
        line5 = line5.replace("\n","")  
        line6 = (entradas[5])
        line6 = line6.replace("\n","")  
        line7 = (entradas[6])
        line7 = line7.replace("\n","")
        line8 = (entradas[7])
        line8 = line8.replace("\n","")
        line9 = (entradas[8])
        line9 = (line9.replace("\n",""))
        line10 = (entradas[9])
        line10 = (line10.replace("\n",""))
        line11 = (entradas[10])
        line11 = (line11.replace("\n",""))
        line12 = (entradas[11])
        line12 = (line12.replace("\n",""))

            
        if line1 == "IN1":            
            self.pm1 = self.IN1
        if line1 == "IN2":
            self.pm1 = self.IN2
        if line1 == "IN3":
            self.pm1 = self.IN3
        if line1 == "IN4":
            self.pm1 = self.IN4
        if line1 == "IN5":
            self.pm1 = self.IN5
        if line1 == "IN6":
            self.pm1 = self.IN6
        if line1 == "IN7":
            self.pm1 = self.IN7
        if line1 == "IN8":
            self.pm1 = self.IN8
        if line1 == "A":
            self.pm1 = self.A
        if line1 == "B":
            self.pm1 = self.B
        if line1 == "C":
            self.pm1 = self.C
        if line1 == "D":
            self.pm1 = self.D
        if line1 == " --- ":
            self.pm1 == None

        if line2 == "IN1":            
            self.pm2 = self.IN1
        if line2 == "IN2":
            self.pm2 = self.IN2
        if line2 == "IN3":
            self.pm2 = self.IN3
        if line2 == "IN4":
            self.pm2 = self.IN4
        if line2 == "IN5":
            self.pm2 = self.IN5
        if line2 == "IN6":
            self.pm2 = self.IN6
        if line2 == "IN7":
            self.pm2 = self.IN7
        if line2 == "IN8":
            self.pm2 = self.IN8
        if line2 == "A":
            self.pm2 = self.A
        if line2 == "B":
            self.pm2 = self.B
        if line2 == "C":
            self.pm2 = self.C
        if line2 == "D":
            self.pm2 = self.D
        if line2 == " --- ":
            self.pm2 = None

        if line3 == "IN1":            
            self.pm3 = self.IN1
        if line3 == "IN2":
            self.pm3 = self.IN2
        if line3 == "IN3":
            self.pm3 = self.IN3
        if line3 == "IN4":
            self.pm3 = self.IN4
        if line3 == "IN5":
            self.pm3 = self.IN5
        if line3 == "IN6":
            self.pm3 = self.IN6
        if line3 == "IN7":
            self.pm3 = self.IN7
        if line3 == "IN8":
            self.pm3 = self.IN8
        if line3 == "A":
            self.pm3 = self.A
        if line3 == "B":
            self.pm3 = self.B
        if line3 == "C":
            self.pm3 = self.C
        if line3 == "D":
            self.pm3 = self.D
        if line3 == " --- ":
            self.pm3 = None

            
        if line4 == "IN1":            
            self.pm4 = self.IN1
        if line4 == "IN2":
            self.pm4 = self.IN2
        if line4 == "IN3":
            self.pm4 = self.IN3
        if line4 == "IN4":
            self.pm4 = self.IN4
        if line4 == "IN5":
            self.pm4 = self.IN5
        if line4 == "IN6":
            self.pm4 = self.IN6
        if line4 == "IN7":
            self.pm4 = self.IN7
        if line4 == "IN8":
            self.pm4 = self.IN8
        if line4 == "A":
            self.pm4 = self.A
        if line4 == "B":
            self.pm4 = self.B
        if line4 == "C":
            self.pm4 = self.C
        if line4 == "D":
            self.pm4 = self.D
        if line4 == " --- ":
            self.pm4 = None
            
        if line5 == "IN1":            
            self.pm5 = self.IN1
        if line5 == "IN2":
            self.pm5 = self.IN2
        if line5 == "IN3":
            self.pm5 = self.IN3
        if line5 == "IN4":
            self.pm5 = self.IN4
        if line5 == "IN5":
            self.pm5 = self.IN5
        if line5 == "IN6":
            self.pm5 = self.IN6
        if line5 == "IN7":
            self.pm5 = self.IN7
        if line5 == "IN8":
            self.pm5 = self.IN8
        if line5 == "A":
            self.pm5 = self.A
        if line5 == "B":
            self.pm5 = self.B
        if line5 == "C":
            self.pm5 = self.C
        if line5 == "D":
            self.pm5 = self.D
        if line5 == " --- ":
            self.pm5 = None

        if line6 == "IN1":            
            self.qbv = self.IN1
        if line6 == "IN2":
            self.qbv = self.IN2
        if line6 == "IN3":
            self.qbv = self.IN3
        if line6 == "IN4":
            self.qbv = self.IN4
        if line6 == "IN5":
            self.qbv = self.IN5
        if line6 == "IN6":
            self.qbv = self.IN6
        if line6 == "IN7":
            self.qbv = self.IN7
        if line6 == "IN8":
            self.qbv = self.IN8
        if line6 == "A":
            self.qbv = self.A
        if line6 == "B":
            self.qbv = self.B
        if line6 == "C":
            self.qbv = self.C
        if line6 == "D":
            self.qbv = self.D
        if line6 == " --- ":
            self.qbv = None

        if line7 == "IN1":            
            self.mud = self.IN1
        if line7 == "IN2":
            self.mud = self.IN2
        if line7 == "IN3":
            self.mud = self.IN3
        if line7 == "IN4":
            self.mud = self.IN4
        if line7 == "IN5":
            self.mud = self.IN5
        if line7 == "IN6":
            self.mud = self.IN6
        if line7 == "IN7":
            self.mud = self.IN7
        if line7 == "IN8":
            self.mud = self.IN8
        if line7 == "A":
            self.mud = self.A
        if line7 == "B":
            self.mud = self.B
        if line7 == "C":
            self.mud = self.C
        if line7 == "D":
            self.mud = self.D
        if line7 == " --- ":
            self.mud = None

        if line8 == "IN1":            
            self.qde = self.IN1
        if line8 == "IN2":
            self.qde = self.IN2
        if line8 == "IN3":
            self.qde = self.IN3
        if line8 == "IN4":
            self.qde = self.IN4
        if line8 == "IN5":
            self.qde = self.IN5
        if line8 == "IN6":
            self.qde = self.IN6
        if line8 == "IN7":
            self.qde = self.IN7
        if line8 == "IN8":
            self.qde = self.IN8
        if line8 == "A":
            self.qde = self.A
        if line8 == "B":
            self.qde = self.B
        if line8 == "C":
            self.qde = self.C
        if line8 == "D":
            self.qde = self.D
        if line8 == " --- ":
            self.qde = None

        if line9 == "IN1":            
            self.ctw4 = self.IN1
        if line9 == "IN2":
            self.ctw4 = self.IN2
        if line9 == "IN3":
            self.ctw4 = self.IN3
        if line9 == "IN4":
            self.ctw4 = self.IN4
        if line9 == "IN5":
            self.ctw4 = self.IN5
        if line9 == "IN6":
            self.ctw4 = self.IN6
        if line9 == "IN7":
            self.ctw4 = self.IN7
        if line9 == "IN8":
            self.ctw4 = self.IN8
        if line9 == "A":
            self.ctw4 = self.A
        if line9 == "B":
            self.ctw4 = self.B
        if line9 == "C":
            self.ctw4 = self.C
        if line9 == "D":
            self.ctw4 = self.D
        if line9 == " --- ":
            self.ctw4 = None

        if line10 == "IN1":            
            self.ctw3 = self.IN1
        if line10 == "IN2":
            self.ctw3 = self.IN2
        if line10 == "IN3":
            self.ctw3 = self.IN3
        if line10 == "IN4":
            self.ctw3 = self.IN4
        if line10 == "IN5":
            self.ctw3 = self.IN5
        if line10 == "IN6":
            self.ctw3 = self.IN6
        if line10 == "IN7":
            self.ctw3 = self.IN7
        if line10 == "IN8":
            self.ctw3 = self.IN8
        if line10 == "A":
            self.ctw3 = self.A
        if line10 == "B":
            self.ctw3 = self.B
        if line10 == "C":
            self.ctw3 = self.C
        if line10 == "D":
            self.ctw3 = self.D
        if line10 == " --- ":
            self.ctw3 = None

        if line11 == "IN1":            
            self.ctw2 = self.IN1
        if line11 == "IN2":
            self.ctw2 = self.IN2
        if line11 == "IN3":
            self.ctw2 = self.IN3
        if line11 == "IN4":
            self.ctw2 = self.IN4
        if line11 == "IN5":
            self.ctw2 = self.IN5
        if line11 == "IN6":
            self.ctw2 = self.IN6
        if line11 == "IN7":
            self.ctw2 = self.IN7
        if line11 == "IN8":
            self.ctw2 = self.IN8
        if line11 == "A":
            self.ctw2 = self.A
        if line11 == "B":
            self.ctw2 = self.B
        if line11 == "C":
            self.ctw2 = self.C
        if line11 == "D":
            self.ctw2 = self.D
        if line11 == " --- ":
            self.ctw2 = None

        if line12 == "IN1":            
            self.ctw1 = self.IN1
        if line12 == "IN2":
            self.ctw1 = self.IN2
        if line12 == "IN3":
            self.ctw1 = self.IN3
        if line12 == "IN4":
            self.ctw1 = self.IN4
        if line12 == "IN5":
            self.ctw1 = self.IN5
        if line12 == "IN6":
            self.ctw1 = self.IN6
        if line12 == "IN7":
            self.ctw1 = self.IN7
        if line12 == "IN8":
            self.ctw1 = self.IN8
        if line12 == "A":
            self.ctw1 = self.A
        if line12 == "B":
            self.ctw1 = self.B
        if line12 == "C":
            self.ctw1 = self.C
        if line12 == "D":
            self.ctw1 = self.D
        if line12 == " --- ":
            self.ctw1 = None  

    def pm1(self):
        return self.pm1

    def pm2(self):
        return self.pm2    

    def pm3(self):
        return self.pm3

    def pm4(self):
        return self.pm4

    def pm5(self):
        return self.pm5

    def qbv(self):
        return self.qbv

    def mud(self):
        return self.mud

    def qde(self):
        return self.qde

    def ctw1(self):
        return self.ctw1

    def ctw2(self):
        return self.ctw2

    def ctw3(self):
        return self.ctw3

    def ctw4(self):
        return self.ctw4

##entradas = Entradas()

class Saidas(object): # Inicia a thread leitura das entradas para controle de todos os programas
    
    def __init__(self):            
    
        saidas = []    
        txt = open("/home/pi/CMM/config.txt",'r')    
        for line in txt: 
            entradas.append(line)
        txt.close()        
        
        line12 = (saidas[12])
        line12 = (line12.replace("\n",""))
        line13 = (saidas[13])
        line13 = (line13.replace("\n",""))
        line14 = (saidas[14])
        line14 = (line14.replace("\n",""))        
        line15 = (saidas[15])
        line15 = (line15.replace("\n",""))
        line16 = (saidas[16])
        line16 = (line16.replace("\n",""))
        line17 = (saidas[16])
        line17 = (line17.replace("\n",""))
        line18 = (saidas[17])
        line18 = (line18.replace("\n",""))
        line19 = (saidas[17])
        line19 = (line19.replace("\n",""))
        line20 = (saidas[18])
        line20 = (line20.replace("\n",""))
        line21 = (saidas[18])
        line21 = (line21.replace("\n",""))
        line22 = (saidas[19])
        line22 = (line22.replace("\n",""))
        line23 = (saidas[19])
        line23 = (line123.replace("\n",""))

            
        if line12 == "IN1":            
            self.rua = self.IN1
        if line12 == "IN2":
            self.rua = self.IN2
        if line12 == "IN3":
            self.rua = self.IN3
        if line12 == "IN4":
            self.rua = self.IN4
        if line12 == "IN5":
            self.rua = self.IN5
        if line12 == "IN6":
            self.rua = self.IN6
        if line12 == "IN7":
            self.rua = self.IN7
        if line12 == "IN8":
            self.rua = self.IN8
        if line12 == "A":
            self.rua = self.A
        if line12 == "B":
            self.rua = self.B
        if line12 == "C":
            self.rua = self.C
        if line12 == "D":
            self.rua = self.D
        if line12 == " --- ":
            self.rua == None

        if line13 == "IN1":            
            self.eclusa = self.IN1
        if line13 == "IN2":
            self.eclusa = self.IN2
        if line13 == "IN3":
            self.eclusa = self.IN3
        if line13 == "IN4":
            self.eclusa = self.IN4
        if line13 == "IN5":
            self.eclusa = self.IN5
        if line13 == "IN6":
            self.eclusa = self.IN6
        if line13 == "IN7":
            self.eclusa = self.IN7
        if line13 == "IN8":
            self.eclusa = self.IN8
        if line13 == "A":
            self.eclusa = self.A
        if line13 == "B":
            self.eclusa = self.B
        if line13 == "C":
            self.eclusa = self.C
        if line13 == "D":
            self.eclusa = self.D
        if line13 == " --- ":
            self.eclusa = None

        if line14 == "IN1":            
            self.pm3 = self.IN1
        if line14 == "IN2":
            self.pm3 = self.IN2
        if line14 == "IN3":
            self.pm3 = self.IN3
        if line14 == "IN4":
            self.pm3 = self.IN4
        if line14 == "IN5":
            self.pm3 = self.IN5
        if line14 == "IN6":
            self.pm3 = self.IN6
        if line14 == "IN7":
            self.pm3 = self.IN7
        if line14 == "IN8":
            self.pm3 = self.IN8
        if line14 == "A":
            self.pm3 = self.A
        if line14 == "B":
            self.pm3 = self.B
        if line14 == "C":
            self.pm3 = self.C
        if line14 == "D":
            self.pm3 = self.D
        if line14 == " --- ":
            self.pm3 = None

            
        if line15 == "IN1":            
            self.pm4 = self.IN1
        if line15 == "IN2":
            self.pm4 = self.IN2
        if line15 == "IN3":
            self.pm4 = self.IN3
        if line15 == "IN4":
            self.pm4 = self.IN4
        if line15 == "IN5":
            self.pm4 = self.IN5
        if line15 == "IN6":
            self.pm4 = self.IN6
        if line15 == "IN7":
            self.pm4 = self.IN7
        if line15 == "IN8":
            self.pm4 = self.IN8
        if line15 == "A":
            self.pm4 = self.A
        if line15 == "B":
            self.pm4 = self.B
        if line15 == "C":
            self.pm4 = self.C
        if line15 == "D":
            self.pm4 = self.D
        if line15 == " --- ":
            self.pm4 = None
            
        if line16 == "IN1":            
            self.pm5 = self.IN1
        if line16 == "IN2":
            self.pm5 = self.IN2
        if line16 == "IN3":
            self.pm5 = self.IN3
        if line16 == "IN4":
            self.pm5 = self.IN4
        if line16 == "IN5":
            self.pm5 = self.IN5
        if line16 == "IN6":
            self.pm5 = self.IN6
        if line16 == "IN7":
            self.pm5 = self.IN7
        if line16 == "IN8":
            self.pm5 = self.IN8
        if line16 == "A":
            self.pm5 = self.A
        if line16 == "B":
            self.pm5 = self.B
        if line16 == "C":
            self.pm5 = self.C
        if line16 == "D":
            self.pm5 = self.D
        if line16 == " --- ":
            self.pm5 = None

        if line17 == "IN1":            
            self.qbv = self.IN1
        if line17 == "IN2":
            self.qbv = self.IN2
        if line17 == "IN3":
            self.qbv = self.IN3
        if line17 == "IN4":
            self.qbv = self.IN4
        if line17 == "IN5":
            self.qbv = self.IN5
        if line17 == "IN6":
            self.qbv = self.IN6
        if line17 == "IN7":
            self.qbv = self.IN7
        if line17 == "IN8":
            self.qbv = self.IN8
        if line17 == "A":
            self.qbv = self.A
        if line17 == "B":
            self.qbv = self.B
        if line17 == "C":
            self.qbv = self.C
        if line17 == "D":
            self.qbv = self.D
        if line17 == " --- ":
            self.qbv = None

        if line18 == "IN1":            
            self.mud = self.IN1
        if line18 == "IN2":
            self.mud = self.IN2
        if line18 == "IN3":
            self.mud = self.IN3
        if line18 == "IN4":
            self.mud = self.IN4
        if line18 == "IN5":
            self.mud = self.IN5
        if line18 == "IN6":
            self.mud = self.IN6
        if line18 == "IN7":
            self.mud = self.IN7
        if line18 == "IN8":
            self.mud = self.IN8
        if line18 == "A":
            self.mud = self.A
        if line18 == "B":
            self.mud = self.B
        if line18 == "C":
            self.mud = self.C
        if line18 == "D":
            self.mud = self.D
        if line18 == " --- ":
            self.mud = None

        if line19 == "IN1":            
            self.qde = self.IN1
        if line19 == "IN2":
            self.qde = self.IN2
        if line19 == "IN3":
            self.qde = self.IN3
        if line19 == "IN4":
            self.qde = self.IN4
        if line19 == "IN5":
            self.qde = self.IN5
        if line19 == "IN6":
            self.qde = self.IN6
        if line19 == "IN7":
            self.qde = self.IN7
        if line19 == "IN8":
            self.qde = self.IN8
        if line19 == "A":
            self.qde = self.A
        if line19 == "B":
            self.qde = self.B
        if line19 == "C":
            self.qde = self.C
        if line19 == "D":
            self.qde = self.D
        if line19 == " --- ":
            self.qde = None

        if line20 == "IN1":            
            self.ctw4 = self.IN1
        if line20 == "IN2":
            self.ctw4 = self.IN2
        if line20 == "IN3":
            self.ctw4 = self.IN3
        if line20 == "IN4":
            self.ctw4 = self.IN4
        if line20 == "IN5":
            self.ctw4 = self.IN5
        if line20 == "IN6":
            self.ctw4 = self.IN6
        if line20 == "IN7":
            self.ctw4 = self.IN7
        if line20 == "IN8":
            self.ctw4 = self.IN8
        if line20 == "A":
            self.ctw4 = self.A
        if line20 == "B":
            self.ctw4 = self.B
        if line20 == "C":
            self.ctw4 = self.C
        if line20 == "D":
            self.ctw4 = self.D
        if line20 == " --- ":
            self.ctw4 = None

        if line21 == "IN1":            
            self.ctw3 = self.IN1
        if line21 == "IN2":
            self.ctw3 = self.IN2
        if line21 == "IN3":
            self.ctw3 = self.IN3
        if line21 == "IN4":
            self.ctw3 = self.IN4
        if line21 == "IN5":
            self.ctw3 = self.IN5
        if line21 == "IN6":
            self.ctw3 = self.IN6
        if line21 == "IN7":
            self.ctw3 = self.IN7
        if line21 == "IN8":
            self.ctw3 = self.IN8
        if line21 == "A":
            self.ctw3 = self.A
        if line21 == "B":
            self.ctw3 = self.B
        if line21 == "C":
            self.ctw3 = self.C
        if line21 == "D":
            self.ctw3 = self.D
        if line21 == " --- ":
            self.ctw3 = None

        if line22 == "IN1":            
            self.ctw2 = self.IN1
        if line22 == "IN2":
            self.ctw2 = self.IN2
        if line22 == "IN3":
            self.ctw2 = self.IN3
        if line22 == "IN4":
            self.ctw2 = self.IN4
        if line22 == "IN5":
            self.ctw2 = self.IN5
        if line22 == "IN6":
            self.ctw2 = self.IN6
        if line22 == "IN7":
            self.ctw2 = self.IN7
        if line22 == "IN8":
            self.ctw2 = self.IN8
        if line22 == "A":
            self.ctw2 = self.A
        if line22 == "B":
            self.ctw2 = self.B
        if line22 == "C":
            self.ctw2 = self.C
        if line22 == "D":
            self.ctw2 = self.D
        if line22 == " --- ":
            self.ctw2 = None

        if line23 == "IN1":            
            self.ctw1 = self.IN1
        if line23 == "IN2":
            self.ctw1 = self.IN2
        if line23 == "IN3":
            self.ctw1 = self.IN3
        if line23 == "IN4":
            self.ctw1 = self.IN4
        if line23 == "IN5":
            self.ctw1 = self.IN5
        if line23 == "IN6":
            self.ctw1 = self.IN6
        if line23 == "IN7":
            self.ctw1 = self.IN7
        if line23 == "IN8":
            self.ctw1 = self.IN8
        if line23 == "A":
            self.ctw1 = self.A
        if line23 == "B":
            self.ctw1 = self.B
        if line23 == "C":
            self.ctw1 = self.C
        if line23 == "D":
            self.ctw1 = self.D
        if line23 == " --- ":
            self.ctw1 = None  

    def rua(self):
        return self.rua

    def eclusa(self):
        return self.eclusa    

    def pm3(self):
        return self.pm3

    def pm4(self):
        return self.pm4

    def pm5(self):
        return self.pm5

    def qbv(self):
        return self.qbv

    def mud(self):
        return self.mud

    def qde(self):
        return self.qde

    def ctw1(self):
        return self.ctw1

    def ctw2(self):
        return self.ctw2

    def ctw3(self):
        return self.ctw3

    def ctw4(self):
        return self.ctw4

def Intertravamento(comando): # Inicia a thread dos portoes sociais importando a classe Rele
        
        entradas = Entradas() # Inicia classe para leitura das entradas        

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

            print("Reconheceu o abre_social")

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
                    
                    print("Abrindo portão Social")

                    if audio == 1: # Ativa as mensagens de abertura e fechamento

                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_social.mp3")                   
                    
                    time.sleep(2) # Tempo minimo para o portão abrir

                    entradas = Entradas()
                    pm1 = entradas.pm1
                                
                    if pm1 == 0: # Portão fechado pois não abriu com o comando

                        print("Portão Social emperrado")
                        evento.enviar("E","130","011") # Envia portão emperrado
                        
                        rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada

                        os.system("mpg123 /home/pi/CMM/mp3/social_emperrado.mp3")

                    if pm1 == 1: # Portão abriu

                        evento.enviar("E","133","001") # Envia abriu portão
                        
                        contador = 300 # Tempo maximo para o social ficar aberto 30 segundos
                        print("Esperando por 15 segundos o portão social fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = Entradas()
                            pm1 = entradas.pm1
                            
                            # Esperando o portão social fechar...
                            
                            if pm1 == 0: # portão fechou

                                print("Portão social fechou")
                                evento.enviar("R","133","001") # Envia fechamento
                                contador = 1
                                                            
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada

                                break

                            if (pm1 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                print("Portão social aberto por muito tempo")
                                
                                evento.enviar("E","130","013") # Envia falha no fechamento social

                                os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                                
                                status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
                                status.write("1")
                                status.close()

                                contador = 0

                                rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada
                                
                            entradas = Entradas()    
                            ctw2 = entradas.ctw2
                            
                            if (ctw2 == 0):# and pm1 == 1): # Entrada para abrir o portão da eclusa
                                print("Agurade o fechamento do social")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_social.mp3") # Necessario manter esse audio sempre ativo
                                time.sleep(1)
                                
                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1
##                            print(contador)
                            
                entradas = Entradas()
                pm2 = entradas.pm2
                
##                if pm2 == 1:
##
##                    print("Aguarde o fechamento")
##                    os.system("mpg123 /home/pi/CMM/mp3/aguarde_social.mp3")
##                    time.sleep(2)
                        
        if comando == "abre_eclusa":

            print("Reconheceu o abre_eclusa")

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
                    print("Abrindo portão Eclusa")

                    if audio == 1:
                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_eclusa.mp3")
                    
                    time.sleep(3) # Tempo de espera para o portão abrir

                    entradas = Entradas()
                    pm2 = entradas.pm2
                    
                    if pm2 == 0: # Portão fechado não abriu após o comando

                       print("Portão emperrado")
                       evento.enviar("E","130","012") # Envia portão emperrado
                       if audio == 1:
                           os.system("mpg123 /home/pi/CMM/mp3/eclusa_emperrado.mp3")
                           
                       rele.desliga(1) # Libera o social para abrir mesmo com a eclusa aberta 

                    if pm2 == 1: # Portão aberto

                        evento.enviar("E","133","003") # Envia abertura
                        
                        contador = 300 # Tempo maximo para eclusa ficar aberta 30 segundos
                        print("Esperando por 30 segundos o portão Eclusa fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = Entradas()
                            pm2 = entradas.pm2
                            
                            # Esperando o portão eclusa fechar...

                            if pm2 == 0: # portão fechou

                                print("Portão Eclusa fechou")
                                evento.enviar("R","133","003") # Envia fechamento
                                contador = 1
                                
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(1) # Libera o social para abrir

                                break

                            if (pm2 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                print("Portão Eclusa aberto por muito tempo")
                                
                                evento.enviar("E","130","014") # Envia falha no fechamento
                                
                                os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                                
                                status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
                                status.write("1")
                                status.close()                                

                                rele.desliga(1) # Libera o social para abrir mesmo com a eclusa aberta

                                contador = 0

                            entradas = Entradas()
                            ctw1 = entradas.ctw1

                            if ctw1 == 0: # Alguem esta tentando abrir o social com a eclusa aberta

                                print("Aguarde o fechamento do portão")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_eclusa.mp3") # Manter esse audio sempre ativo
                                time.sleep(1)
                                

                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1
##                            print(contador)
                            
##                if pm1 == 1:
##
##                    print("Aguarde o fechamento da eclusa")
##                    os.system("mpg123 /home/pi/CMM/mp3/aguarde_eclusa.mp3")
##                    time.sleep(2)
                                    

class Abre(Rele): # Inicia a thread dos portoes sociais importando a classe Rele


    def social(self):

        status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
        status.write("1")
        status.close()

        rele.pulso(4,2) # Pulso para abrir direto o portão sem intertravamento (Social)
        
        print("Abrindo portão social")
        evento.enviar("E","133","001") # Envia abertura
        
    def eclusa(self):

        status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
        status.write("1")
        status.close()        
    
        rele.pulso(5,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)

        print("Abrindo portão eclusa")      
        evento.enviar("E","133","003") # Envia abertura
        
                

################################################ THREADS ROTINAS #################################################

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
    cont1 = 60 # Contador individual para cada reset de arrombamento
    cont2 = 60
    cont3 = 60
    cont4 = 60
    cont5 =60
    cont6 = 60
    cont7 = 60
    
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
                
        if pm1 == 1 and ar1 == 0:

            time.sleep(1) # Filtra algum possivel ruido de até 1 segundo
            a = open("/home/pi/CMM/status_social.cmm","r")
            abre_social = a.read()
            a.close()

            if abre_social == "1": #pm1 == 1: # Se realmente foi um arrombamento liga sirene e notifica o Moni

                print("Arrombamento do portão social")
                os.system("mpg123 /home/pi/CMM/mp3/violacao_social.mp3")
                rele.liga(8)
                evento.enviar("E","120","002")
                
                ar1 = 1
                reset_ar1 = 1

        if ar1 == 1 and reset_ar1 == 1:

            cont1 = cont1 - 1 # A primeira vez que acontece o arrombamento reseta depois de 30 segundos
            time.sleep(1)

            if cont1 <= 0:

                evento.enviar("R","120","002")

                cont1 = 30 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 60 segundos
                ar1 = 0
                reset_ar1 = 0
                rele.desliga(8)

                

        if pm2 == 1 and ar2 == 0:

            time.sleep(1) # Filtra algum possivel ruido de até 500 milissegundos

            b = open("/home/pi/CMM/status_eclusa.cmm","r")
            abre_eclusa = b.read()
            b.close()

            if abre_eclusa: #pm2 == 1: # Se realmente foi um arrombamento liga sirene e notifica o Moni

                print("Arrombamento do portão Eclusa")
                os.system("mpg123 /home/pi/CMM/mp3/violacao_eclusa.mp3")
                rele.liga(8)
                evento.enviar("E","120","004")
                
                ar2 = 1
                reset_ar2 = 1

        if ar2 == 1 and reset_ar2 == 1:

            cont2 = cont2 - 1 # A primeira vez que acontece o arrombamento reseta depois de 30 segundos
            time.sleep(1)

            if cont2 <= 0:

                evento.enviar("R","120","004")

                cont2 = 60 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 60 segundos
                ar2 = 0
                reset_ar2 = 0
                rele.desliga(8)

        
        time.sleep(2)   


def Servidor(Rele): ######### Thread servidor Cadastro QR Code ###################

    time.sleep(1)

    deletar = 0
    cadastrar = 0

    host_servidor = '172.18.34.247'  # Host servidor 
    port_gerenciador = 5511# porta para receber dados do gerenciador
    

##    print("Ouvindo Gerenciador na porta",port_gerenciador)
    
    while(1):

        socket.setdefaulttimeout(9999)

        hs = time.strftime("%H:%M:%S") # MANTEM ATUALIZADO O HORARIO DO REGISTRO DE LOG
        
              
        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            
            try:
                s.bind((host_servidor, port_gerenciador))
            except socket.error as msg:
                print ("Erro servidor gerenciador",msg)
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


                    print("dados recebidos",data)

                    comando = (data.split("&")[0])
##                    print("Comando", comando)

                    corpo = (data.split("&")[1])
##                    print("Corpo",corpo)
                    

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
                    conn.close()

                except Exception as err:

                    print("Dados recebidos estao fora do formato",err)
                    break

                try:
    
                    if comando == "deletar_qr":

                        print("\nReconheceu deletar")

                        
                        ID = corpo.split(":")[0]

                        print("ID", ID)
                        
                        cliente = corpo.split(":")[1]

                        print("cliente",cliente)
                        

                        try:  # Tenta conectar com o banco de dados
                    
                            print('Conectando banco de dados...')  
                            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                            cursor = cnx.cursor()
                            print('Conectado\n')
                          
                        except mysql.connector.Error as err:
                            
                            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                              
                                print("Alguma coisa esta errada com o nome de usuario ou a senha!")
                            
                            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                              
                                print("Esta base de dados nao existe")
                            
                            else:
                              
                                print(err)

                        else:

                            query = ("SELECT * FROM qrcode")  # Seleciona a tabela qrcode
                            cursor.execute(query)

                            encontrou = 0
                    
                        for i in cursor:

                            if encontrou == 0:
                                   
                                ID_recebido = str(i[0]) # Seleciona o primeiro item da lista recebida do banco (ID)

                                                                
                                if (ID_recebido == ID): # Compara se o ID vindo do request e igual ao do banco   

                                    print("Achou o id no banco...")

                                    encontrou = 1
                                

                        if encontrou == 0:

                            print("id inexistente")

                        if encontrou == 1:
                                    
                            try:
                                
                            
                                query = ("DELETE FROM qrcode WHERE ID = %s")%ID
                                cursor.execute(query)
                                cnx.commit()
                                   
                                
                            except Exception as err:  # mysql.connector.Error as err:


                                print("Id inexistente",ID,err)
                                cnx.close()
                                

                            else:


                                print("ID",ID,"deletado do banco")
                                
                                ID = str(ID)
                                cliente = str(cliente)
                            
                                arquivo = open("/home/pi/CMM/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                                arquivo.write(" Evento: Deletado QR Code " + "ID" + ID + hs + "\n")
                                arquivo.close()

                                break

                        break
                        
                    if comando == "cadastrar_qr":

                        try:

                            print("\nReconheceu cadastrar qrcode")
                           
                            dados = data.replace("cadastrar_qr&","")
                            dados = dados.replace("'",'"')
                            
                            print("Dados convertidos: ", dados)

                        except Exception as err:

                            print("Erro ao formatar os dados para converter em json", err)

                    
                #########  Faz o cadastro dos dados recebidos no banco do CMM #######
                        try:

##                            dados = dados.encode('utf-8')
####                            dados = json.dumps(dados)
##                            dados = str(dados)
##                            print(dados,type(dados))
##                            dados_json = dados.encode('utf-8')
##                            dados = dados.encode('unicode-escape')
                            
                            dados_json = json.loads(dados)  # Tranforma a string para formato json (dicionario)
##                            print(dados_json)
                               
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

##                            nome = nome.encode("utf-8")

                        except Exception as err:

                            print("Erro na conversao json",err)

                                           
                        try:  # Tenta conectar com o banco de dados
                    
                            print('Conectando banco de dados...')  
                            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                            cursor = cnx.cursor()
                            print('Conectado\n')
                          
                        except mysql.connector.Error as err:
                            
                            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                              
                                print("Alguma coisa esta errada com o nome de usuario ou a senha!")
                            
                            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                              
                                print("Esta base de dados nao existe")
                            
                            else:
                              
                                print(err)
                        try:

                            print("Tentando inserir os dados editados no banco...")
                            
                        
                            query = ("INSERT INTO qrcode (ID, nome, apartamento, bloco, cond, hora_inicio, hora_final, data_inicio, data_final, dias_semana) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                            query_data = (ID,nome,ap,bloco,cond,hi,hf,di,df,ds)
                            cursor.execute(query, query_data)
                            cnx.commit()

                            
                        except mysql.connector.Error as err:


                            if err.errno == 1062:

                                print("ID duplicado")

                                cnx.close()
                                break
                                
                                
                            else:

                                print("Erro na inclusão do banco",err)

                        else:


                            print("\ncadastrado com sucesso ",ID)

                            arquivo = open("/home/pi/CMM/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                            arquivo.write(" Evento: Deletado QR Code " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                            arquivo.close()

                            cnx.close()
                            break

                except Exception as e:

                    print("Erro na rotina cadastrar ou deletar")
                 
        s = setupServer()

        while True:
          
          print ("\nEscutando Gerenciador na porta",port_gerenciador,"\n")
          
          try:

              conn = setupConnection()
              dataTransfer(conn) #,saidaA,saidaB,hs)
                                         
                
          except:
            
              print("Encerrou conexão com Gerenciador")

              
def Portoes_sociais(Rele): # Programa
    
    sys.stdout.write("\nPrograma Sociais em execução\n")   
        
    while(1):

        entradas = Entradas() # Inicia classe para leitura das entradas
        
        pm1 = entradas.pm1
        pm2 = entradas.pm2
##        pm3 = entradas.pm3
##        pm4 = entradas.pm4
        qbv = entradas.qbv
        mud = entradas.mud
        qde = entradas.qde
        ctw1 = entradas.ctw1
        ctw2 = entradas.ctw2
        ctw3 = entradas.ctw3
        ctw4 = entradas.ctw4  
        
        
        if ctw1 == 0:

            status = open("/home/pi/CMM/status_social.cmm","w")
            status.write("1")
            status.close()
     
            Intertravamento("abre_social")

            status = open("/home/pi/CMM/status_social.cmm","w")
            status.write("0")
            status.close()

        if ctw2 == 0:

            status = open("/home/pi/CMM/status_eclusa.cmm","w")
            status.write("1")
            status.close()

            Intertravamento("abre_eclusa")

            status = open("/home/pi/CMM/status_eclusa.cmm","w")
            status.write("0")
            status.close()
                
        time.sleep(0.1)
        
def Alarmes(Rele):
    
    sys.stdout.write("\nPrograma Alarmes em execução\n")

    cont1 = 0
    cont2 = 0
    cont3 = 0
    cont4 = 0

    queda_energia = 0           # variaveis de controle  
    queda_de_energia = 0
    encerra_queda_de_energia = 0

    quebra_vidro = 0              
    quebra_de_vidro = 0         
    encerra_quebra_de_vidro = 0 
  
    quebra_vidro_A = 0              
    quebra_de_vidro_A = 0         
    encerra_quebra_de_vidro_A = 0 

    chave_mudanca = 0
    chave_de_mudanca = 0
    encerra_chave_de_mudanca = 0

    while(1):

        entradas = Entradas() # Inicia classe para leitura das entradas
        qbv = entradas.qbv
        mud = entradas.mud
        qde = entradas.qde
        IN5 = wiringpi.digitalRead(304)
        
        if qbv == 0 and quebra_vidro == 0: # Se o quebra de vidro foi acionado

            # Filtro para ruidos

            cont1 = 20

            while cont1 > 0:

                entradas = Entradas() 
                qbv = entradas.qbv

                if qbv == 0: # Ainda esta acionado

                    quebra_de_vidro = 1

                else:

                    quebra_de_vidro = 0
                    cont1 = 0
                    
                time.sleep(0.1)
                cont1 = cont1 - 1

            if quebra_de_vidro == 1:            

                print("Quebra de vidro acionado")

                rele.liga(8) # Liga sirene

                abre.social() # Ao invocar esta função ela ja coloca o arquivo de texto em 1 para não gerear arrombamento
                abre.eclusa()

                os.system("mpg123 /home/pi/CMM/mp3/emergencia.mp3")

                time.sleep(1)

                rele.liga(3) # Foto dos 2 poortões (mantem os doid portões abertos)
                rele.liga(5) # Mantem abre da eclusa acionado

                quebra_vidro = 1

                evento.enviar("E","130","007") # Envia violação quebra de vidro           

                time.sleep(10)

        if qbv == 1 and quebra_vidro == 1:

            # Filtro para ruidos

            cont1 = 20

            while cont1 > 0:

                entradas = Entradas() 
                qbv = entradas.qbv

                if qbv == 1: # Ainda esta acionado

                    encerra_quebra_de_vidro = 1

                else:

                    encerra_quebra_de_vidro = 0
                    cont = 0

                time.sleep(0.1)
                cont1 = cont1 - 1

            if encerra_quebra_de_vidro == 1:

                print("Quebra de vidro restaurado")
                
                rele.desliga(3) # Desliga fotocelula
                rele.desliga(5) # Fecha eclusa

                evento.enviar("R","130","007") # Envia violação quebra de vidro

                time.sleep(15) # Aguarda os portoes fecharem

                rele.desliga(8) # Desliga sirene

                status = open("/home/pi/CMM/status_social.cmm","w") # Volta o arquivo para zero para ativar a verificação de arrombamento
                status.write("0")
                status.close()

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()

                quebra_vidro = 0

                print("Sistema em modo automatico")
                os.system("mpg123 /home/pi/CMM/mp3/automatico.mp3")

        if IN5 == 0 and quebra_vidro_A == 0: # Se o quebra de vidro foi acionado

            # Filtro para ruidos

            cont4 = 20

            while cont4 > 0:

                IN5 = wiringpi.digitalRead(304)

                if IN5 == 0: # Ainda esta acionado

                    quebra_de_vidro_A = 1

                else:

                    quebra_de_vidro_A = 0
                    cont4 = 0
                    
                time.sleep(0.1)
                cont4 = cont4 - 1

            if quebra_de_vidro_A == 1:            

                print("Quebra de vidro Eclusa acionado")
                rele.liga(8) # Liga sirene
                
                os.system("mpg123 /home/pi/CMM/mp3/emergencia.mp3")
                time.sleep(1)
                
                quebra_vidro_A = 1

                evento.enviar("E","130","006") # Envia violação quebra de vidro     

                time.sleep(10)

        if IN5 == 1 and quebra_vidro_A == 1:

            # Filtro para ruidos

            cont4 = 20

            while cont4 > 0:

                IN5 = wiringpi.digitalRead(304)

                if IN5 == 1: # Ainda esta acionado

                    encerra_quebra_de_vidro_A = 1

                else:

                    encerra_quebra_de_vidro_A = 0
                    cont = 0

                time.sleep(0.1)
                cont4 = cont4 - 1

            if encerra_quebra_de_vidro_A == 1:

                print("Quebra de vidro restaurado")                
                
                evento.enviar("R","130","006") # Envia violação quebra de vidro

                time.sleep(15) # Aguarda os portoes fecharem

                rele.desliga(8) # Desliga sirene

                status = open("/home/pi/CMM/status_social.cmm","w") # Volta o arquivo para zero para ativar a verificação de arrombamento
                status.write("0")
                status.close()

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()

                quebra_vidro_A = 0

                print("Sistema em modo automatico")
                os.system("mpg123 /home/pi/CMM/mp3/automatico.mp3")
                              


        if mud == 0 and chave_mudanca == 0: 

            # Filtro para ruidos

            cont2 = 10

            while cont2 > 0:

                entradas = Entradas() 
                mud = entradas.mud

                if mud == 0: # Ainda esta acionado

                    chave_de_mudanca = 1

                else:

                    chave_de_mudanca = 0
                    cont2 = 0
                    
                time.sleep(0.1)
                cont2 = cont2 - 1

            if chave_de_mudanca == 1:

                print("Chave de mudança acionada")

                rele.liga(8) # Liga sirene

                abre.social() # Ao invocar esta função ela ja coloca o arquivo de texto em 1 para não gerear arrombamento
                abre.eclusa()

                os.system("mpg123 /home/pi/CMM/mp3/mudanca.mp3")

                time.sleep(1)

                rele.liga(3) # Foto dos 2 poortões (mantem os dois portões abertos)
                rele.liga(5) # Mamtem o abre da eclusa acionado
                
                evento.enviar("E","130","008") # Envia chave de mudança acionada

                time.sleep(3)

                chave_mudanca = 1

        if mud == 1 and chave_mudanca == 1: # Restaurou energia eletrica

            # Filtro para ruidos

            cont2 = 10

            while cont2 > 0:

                entradas = Entradas() 
                mud = entradas.mud

                if mud == 1: # Ainda esta acionado

                    encerra_chave_de_mudanca = 1

                else:

                    encerra_chave_de_mudanca = 0
                    cont2 = 0
                    
                time.sleep(0.1)
                cont2 = cont2 - 1

            if encerra_chave_de_mudanca == 1:

                print("Chave de mudança restaurada")

                rele.desliga(3) # Desliga fotocelula
                rele.desliga(5) 
                
                os.system("mpg123 /home/pi/CMM/mp3/restaurou_mudanca.mp3")

                evento.enviar("R","130","008") # Restaurou chave de mudança

                time.sleep(15) # Aguarda os portoes fecharem

                rele.desliga(8) # Desliga sirene

                status = open("/home/pi/CMM/status_social.cmm","w") # Volta o arquivo para zero para ativar a verificação de arrombamento
                status.write("0")
                status.close()

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()                

                evento.enviar("R","130","008") # Envia restauração chave de mudanca

                time.sleep(3)

                chave_mudanca = 0   
        
        if qde == 0 and queda_energia == 0: # Queda de energia

            # Filtro para ruidos

            cont3 = 20

            while cont3 > 0:

                entradas = Entradas() 
                qde = entradas.qde

                if qde == 0: # Ainda esta acionado

                    queda_de_energia = 1

                else:

                    queda_de_energia = 0
                    cont3 = 0
                    
                time.sleep(0.1)
                cont3 = cont3 - 1

            if queda_de_energia == 1:                

                print("Queda de energia")

                os.system("mpg123 /home/pi/CMM/mp3/queda_energia.mp3")
                
                evento.enviar("E","301","000") # Envia queda de energia elétrica

                time.sleep(3)

                queda_energia = 1

        if qde == 1 and queda_energia == 1: # Restaurou energia eletrica

            cont3 = 20

            while cont3 > 0:

                entradas = Entradas() 
                qde = entradas.qde

                if qde == 1: # Ainda esta acionado

                    encerra_queda_de_energia = 1

                else:

                    encerra_queda_de_energia = 0
                    cont3 = 0
                    
                time.sleep(0.1)
                cont3 = cont3 - 1

            if encerra_queda_de_energia == 1:

                print("Restaurou energia eletrica")

                os.system("mpg123 /home/pi/CMM/mp3/restaurou_energia.mp3")

                evento.enviar("R","301","000") # Envia restauração de energia elétrica

                time.sleep(3)

                queda_energia = 0

        time.sleep(1)        


def Sistema(Rele,Temperatura): 
    
    sys.stdout.write("\nPrograma do sistema em execução\n")

    cont = 600 # Equivale a 60 segundos

    ihm = IHM() # Inicia a interface grafica de configuração dos sociais
    
    while(1):

##        entradas = Entradas()
##
##        ctw1 = entradas.ctw1
##        ctw2 = entradas.ctw2
##        ctw3 = entradas.ctw3
##        ctw4 = entradas.ctw4
##
##        if ctw1 == 1:
##            print("CTW 1 = 1")
##            ct1 = 1
##        if ctw1 != 1:
##            
##        print("CTW 2 ", ctw2)
##        print("CTW 3 ", ctw3)
##        print("CTW 4 ", ctw4)

        time.sleep(1)

def Buffer():

    socket.setdefaulttimeout(4) # limite de 2 segundos para enviar o socket

    host = '172.20.1.5'  # '172.20.1.5' Host servidor  Moni
    port = 4010          # 4010 Porta máquina receptora

    print("Iniciou o programa buffer")

    enviado = 0

    while(1):

        b = open("/home/pi/CMM/buffer_eventos.txt","r")
        
        for line in b:

            ln = line
            
            if (len(ln) > 5 ): # Se houver alguma coisa para enviar

                print("Encontrou na linha do buffer.txt:",ln)

                evento = ln.replace("\n","")
                
                try:
        
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = (evento + "\r")
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    s.close()

                    enviado = 1                    
                                
                except Exception as err:
                    
                    print("Não conseguiu enviar o evento, sem conexão no momento")
                    s.close()

                    time.sleep(10)
                    break
                
                if enviado == 1:
                                               
                    print("Evento enviado pelo buffer",evento)           

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
##                                print("Excluindo o evento",evento,"posicao",indice)
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
            else:

                time.sleep(5)
                
        b.close() # Fecha o arquivo de texto em modo leitura    
        time.sleep(1)
                

            
    
        
#################### Instancia as Classes  #############################################

intertravamento = Intertravamento(Rele)
abre = Abre()

####################  Declara as threads dos programas disponiveis  ####################

entradas = threading.Thread(target=Entradas)
sociais = threading.Thread(target=Portoes_sociais, args=(Rele,)) # deixar virgula depois do arg 1
##arrombamento = threading.Thread(target=Arrombamento, args=(Rele,))
servidor = threading.Thread(target=Servidor, args=(Rele,))
buffer = threading.Thread(target=Buffer)

alarmes = threading.Thread(target=Alarmes, args=(Rele,))
sistema = threading.Thread(target=Sistema, args=(Rele,Temperatura,))
qrcode1 = threading.Thread(target=thread_qrcode1)
qrcode2 = threading.Thread(target=thread_qrcode2)
##wiegand = threading.Thread(target=thread_wiegand, args=(Rele,wiegand))


######################################### Start dos Programas  #############################################################

sociais.start() # Inicia o programa dos portões sociais
##arrombamento.start() # Inicia o programa de automação
servidor.start() # Inicia o programa de automação
buffer.start() # Inicia o programa Buffer

alarmes.start() # In icia a leitura de interrupções
##sistema.start()
qrcode1.start()
qrcode2.start()

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

##evento.enviar_contact_id('E','130','001') # Evento ou Restauração / Evento / Setor

###################################################################################################

sys.stdout.write("\nTemperatura " + str(temperatura.cpu()) + "°C\n")  # obter temperatura


while(1):    
    

    time.sleep(1)

