#!/home/pi/CMM/bin/python3
# -*- coding:utf-8 -*-

# CMM Oficial com placa de expansão da BRAVAS Technololgy
# Desenvolvido por Leandro Leal  rev. 17/09/2019

import RPi.GPIO as GPIO
import time

from biblioteca_CMM_oficial import Rele,Narrador,Temperatura,Email,Clima,Evento
from cmm_io import Entradas, Saidas # Classes para leituras das entradas e acionamento das saidas definidas no arq. config.txt
##from modulos_expansores import Expansor, Leitor # Acionamento e Leitura das entradas dos expansores

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
import serial # Parhome/pi/CMM/mp3a comunicação serial com arduino
from banco import Banco
import _thread as thread
import libscrc # biblioteca para calculo do CRC (Controle de Redundancia) - usado no protocolo modbus


def log(texto): # Metodo para registro dos eventos no log.txt (exibido na interface grafica)

    hs = time.strftime("%H:%M:%S") 
    data = time.strftime('%d/%m/%y')

    texto = str(texto)

    escrita = ("{} - {}  Evento:  {}\n").format(data, hs, texto)
    escrita = str(escrita)

    l = open("/var/www/html/log.txt","a")
    l.write(escrita)
    l.close()
    
log("Reiniciou o sistema")

mutex = thread.allocate_lock() # Trava a thread para que seja executada sozina

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

GPIO.setup(17,GPIO.OUT) # HIGH para enviar LOW para ler dados
GPIO.setup(18,GPIO.OUT) # HIGH para enviar LOW para ler dados

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
nome = str(nome)
nome = nome.replace("\n","")

ip = os.popen('hostname -I').readline()
ip = str(ip)
ip = ip.replace("\n","")

txt = ("Nome desta maquina",nome,"com IP",ip)
txt = str(txt)
txt = txt.replace("'","")
txt = txt.replace(",","")

txt = txt.replace("(","")
txt = txt.replace(")","")
log(txt)

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

##log("Conteudo do play1 ",ihm.get_cbox("play1"))

############################################## Escreve na serial ################################################################
ser = serial.Serial("/dev/ttyS0", 115200)

def escreve_serial(packet):    

    try:
            
        mutex.acquire() # Trava para acesso exclusivo
        

        time.sleep(0.15)
                
        GPIO.output(17, 1)  
        GPIO.output(18, 1)
        
        time.sleep(0.05)
        
        ser.write(packet)
        
        time.sleep(0.002)
        
        GPIO.output(17, 0)  
        GPIO.output(18, 0)

        time.sleep(0.02)
        
        bytesToRead = ser.inWaiting()  
        in_bin = ser.read(bytesToRead)
        
        mutex.release() # Desbloqueia trava de acesso
        
        return in_bin

    except Exception as err:

        print("\nErro na leitura da serial",err)
        log("Erro na serial")
        return("erro")

class monta_pacote_in():

    def __init__(self):

        self = self
##        self.ser = ser
        
    def ler(self,modulo): # passar dados como string

        modulo = int(modulo,16) # Converte para um inteiro de base 16

        def crc16(byte):

            byte = bytes(byte)

            self.crc16 = libscrc.modbus(byte) #b'\x07\x05\x00\x00\xFF\x00')  # Estrutura para calculo do CRC

            bin2str = (hex(self.crc16))
            bin2str = str(bin2str)

            p = "0x"

            a1 = bin2str[-2]
            a2 = bin2str[-1]
            if a1 == "x":
                a1 = "0"
            a = p + a1 + a2            

            b1 = bin2str[-4]
            b2 = bin2str[-3]
            if b1 == "x":
                b1 = "0"
            b = p + b1 + b2
            
            return(a,b) 
               
        packet = bytearray()  
        packet.append(modulo) # Endreço do modulo 
        packet.append(0x02) # Modo leitura
        packet.append(0x00) # 
        packet.append(0x00) # Endereço registrador inicial
        packet.append(0x00) # 
        packet.append(0x04) # Registradores a serem lidos

        crc = crc16(packet)

        a = int(crc[0],16)
        b = int(crc[1],16)
            
        packet.append(a) # Controle de redundancia
        packet.append(b) # Controle de redundancia
               
        in_bin = escreve_serial(packet)

        in_bin = str(in_bin)

        if in_bin == "b''": # reenviando leitura

            cont = 5

            while cont > 0:

##                print("reenviando leitura")

                in_bin = escreve_serial(packet)

                if in_bin == "b''":

                    time.sleep(0.1)
                    cont = cont - 1

                else:

                    return(in_bin)                      

        return(in_bin)

class retorna:

    def __init__(self):

        self = self

    def entrada(self,b,entrada_requisitada):
            
        in1 = 0
        in2 = 0
        in3 = 0
        in4 = 0

        if (b == "1" or b =="3" or b =="5" or b =="7" or b =="9" or b =="b" or b =="d" or b =="f"):
            in1 = 1
        
        if (b == "2" or b =="3" or b =="6" or b =="7" or b =="a" or b =="b" or b =="e" or b =="f"):
            in2 = 1
        
        if (b == "4" or b =="5" or b =="6" or b =="7" or b =="c" or b =="d" or b =="e" or b =="f"):
            in3 = 1
        
        if (b == "8" or b =="9" or b =="a" or b =="b" or b =="c" or b =="d" or b =="e" or b =="f"):
            in4 = 1

        if entrada_requisitada == 'in1':

            entrada_requisitada = in1
            
        if entrada_requisitada == 'in2':

            entrada_requisitada = in2

        if entrada_requisitada == 'in3':

            entrada_requisitada = in3

        if entrada_requisitada == 'in4':

            entrada_requisitada = in4
       
        return(entrada_requisitada)

class limpa:

    def _init__(self):

        self = self

    def string(self,i):

        try:

            i = str(i.split('\\')) 
            i = i.replace("x","")
            i = i.replace("'","")
            i = i.replace("`","")
            i = i.replace(" ","")
            i = i.replace("!","")
            i = i.replace("I","")
            i = i.replace('"',"")
            i = i.replace("[","")
            i = i.replace("]","")
       
            return(i)

        except:
            pass

class filtro(limpa):

    def __init__(self):
        
        self.limpa = limpa()

    def mdl1(self,i):

        if i != b'':

            i = self.limpa.string(i) 
            
            try:
                
                i= i.split(",")
                                
                i = (i[4])  # Obtem da lista o byte referente ao estado das entradas                    
                b = (i[-1]) # Obtem do byte a metade que contem os bits que representa as entradas
                                        
                if i == "05a": # Formatações devido ao retorno do byte com representação em ascii
                    b = "5"            
                if i == "ta":
                    b = "9"
                if i == "n":
                    b = "a"
                if i == "r":
                    b = "d"
                if i == "":
                    b = "d"
                if i == "0eL":
                    b = "e"
                if i == "rM":
                    b = "d"
                if i == "01H":                    
                    b = "1"
                                             
                return(b)
            
            except:

                #print("erro fitro mdl1")
                pass


    def mdl2(self,i):

        if i != b'':                
            
            i = self.limpa.string(i) 
            
            try:
                
                i= i.split(",")
                                
                i = (i[4])  # Obtem da lista o byte referente ao estado das entradas  
                  
                b = (i[-1]) # Obtem do byte a metade que contem os bits que representa as entradas
                        
                if i == "05a": # Formatações devido ao retorno do byte com representação em ascii
                    b = "5"            
                if i == "ta":
                    b = "9"
                if i == "n":
                    b = "a"
                if i == "r":
                    b = "d"
                if i == "":
                    b = "d"
                if i == "0eL":
                    b = "e"
                if i == "rM":
                    b = "d"                            
                
                return(b)
            
            except:

                #print("erro fitro mdl2")
                pass

    def mdl3(self,i):

        if i != "b''":                
            
            i = self.limpa.string(i) 

        try:
            
            i= i.split(",")
                            
            i = (i[4])  # Obtem da lista o byte referente ao estado das entradas                    
            b = (i[-1]) # Obtem do byte a metade que contem os bits que representa as entradas
                                
            if i == "05a": # Formatações devido ao retorno do byte com representação em ascii
                b = "5"            
            if i == "ta":
                b = "9"
            if i == "n":
                b = "a"
            if i == "r":
                b = "d"
            if i == "":
                b = "d"
            if i == "0eL":
                b = "e"
            if i == "rM":
                b = "d"
            if i == "01a":
                b = "1"
            if i == "053":
                b = "5"
            if i == "062":
                b = "6"
            if i == "t6":
                b = "9"
            if i == "n7":
                b = "a"
            if i == "ra":
                b = "d"
                                    
            return(b)
        
        except:
            
            #print("erro fitro mdl3")
            pass

    def mdl4(self,i):       

        if i != "b''":                
            
            i = self.limpa.string(i) 

        try:
            
            i= i.split(",")
                            
            i = (i[4])               
            b = (i[-1])             
                                
            if i == "05aG": 
                b = "5"
            if i == "06F": 
                b = "6"
            if i == "taB": 
                b = "9"
            if i == "nC": 
                b = "a"
            if i == "r": 
                b = "d"
            
                                    
            return(b)
        
        except:

            pass
            
            #print("erro fitro mdl4")
        


    def mdl5(self,i):       

        if i != "b''":                
            
            i = self.limpa.string(i) 

        try:
            
            i= i.split(",")
                            
            i = (i[4])               
            b = (i[-1])            
                                
            if i == "01a": 
                b = "1"
            if i == "02y": 
                b = "2"
            if i == "t": 
                b = "9"
            if i == "n": 
                b = "a"
            if i == "ra}": 
                b = "d"
            if i == "0e|": 
                b = "e"                        
                                    
            return(b)
        
        except:

            pass
            
            #print("erro fitro mdl5")

    def mdl6(self,i):       

        if i != "b''":                
            
            i = self.limpa.string(i) 

        try:
            
            i= i.split(",")
                            
            i = (i[4])               
            b = (i[-1])
                                
            if i == "01a<": 
                b = "1"
            if i == "02=": 
                b = "2"
            if i == "t": 
                b = "9"
            if i == "n": 
                b = "a"
            if i == "ra9": 
                b = "d"
            if i == "0e8": 
                b = "e"                        
                                    
            return(b)
        
        except:

            pass
            
            #print("erro fitro mdl6")

    def mdl7(self,i):

        if i != "b''":
                    
            i = self.limpa.string(i)

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])

                
                if i == "05a": 
                    b = "5"            
                if i == "ta":
                    b = "9"
                if i == "n":
                    b = "a"
                if i == "r":
                    b = "d"
               
                return (b)                            

            except:

                #print("erro fitro mdl7")
                pass

    def mdl8(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])               

                if i == "01c":
                    b = "1"
                if i == "02#":
                    b = "2"                
                if i == "05b": 
                    b = "5"            
                if i == "tb":
                    b = "9"
                if i == "n":
                    b = "a"
                if i == "rc":
                    b = "d"
                if i == "0e#":
                    b = "e"
               
                return (b)                            

            except:

                #print("erro fitro mdl9")
                pass

    def mdl9(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])                

                if i == "01b(":
                    b = "1"
                if i == "02)\\":
                    b = "2"                
                if i == "05c": 
                    b = "5"
                if i == "06#": 
                    b = "6"
                if i == "tc":
                    b = "9"
                if i == "n#":
                    b = "a"
                if i == "rb-":
                    b = "d"
                              
                return (b)                            

            except:

                #print("erro fitro mdl9")
                pass

    def mdl10(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])                

                if i == "01b(":
                    b = "1"
                if i == "02)\\":
                    b = "2"                
                if i == "05c": 
                    b = "5"
                if i == "06#": 
                    b = "6"
                if i == "tc":
                    b = "9"
                if i == "n#":
                    b = "a"
                if i == "rb-":
                    b = "d"
                              
                return (b)                            

            except:

                #print("erro fitro mdl10")
                pass

    def mdl11(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])

                if i == "01c":
                    b = "1"                    
                if i == "02#":                    
                    b = "2"                    
                if i == "05bS": 
                    b = "5"                    
                if i == "06R\\": 
                    b = "6"                    
                if i == "tbV":
                    b = "9"                    
                if i == "nW\\":
                    b = "a"                    
                if i == "rc":
                    b = "d"                    
                if i == "0e#":
                    b = "e"
                              
                return (b)                            

            except:

                #print("erro fitro mdl11")
                pass

    def mdl12(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])

                

                if i == "01b":
                    b = "1"      
                if i == "05c\\": 
                    b = "5"                    
                if i == "06#&": 
                    b = "6"                    
                if i == "tc\\":
                    b = "9"                    
                if i == "n##":
                    b = "a"                    
                if i == "rb":
                    b = "d"                    
                                              
                return (b)                            

            except:

                #print("erro fitro mdl12")
                pass

    def mdl13(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])

                if i == "01c":
                    b = "1"
                if i == "02#":
                    b = "2" 
                if i == "05b": 
                    b = "5"      
                if i == "tb":
                    b = "9"                    
                if i == "n":
                    b = "a"                    
                if i == "rc":
                    b = "d"
                if i == "0e#":
                    b = "e"                
                                              
                return (b)                            

            except:

                pass
##                print("erro fitro mdl13")

    def mdl14(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])                

                if i == "01c":
                    b = "1"
                if i == "02#":
                    b = "2"
                if i == "04":                    
                    b = "4" 
                if i == "05b": 
                    b = "5"
                if i == "06":
                    b = "6"
                if i == "07":
                    b = "7"
                if i == "06":
                    b = "6" 
                if i == "tb":
                    b = "9"                    
                if i == "n":
                    b = "a"
                if i == "0b":
                    b = "b"
                if i == "0c":
                    b = "c" 
                if i == "rcY":
                    b = "d"
                if i == "0e#X":
                    b = "e"                
                                              
                return (b)                            

            except:

                #print("erro fitro mdl14")
                pass

    def mdl15(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])
                
                if i == "01b":
                    b = "1"               
                if i == "05cc": 
                    b = "5"
                if i == "06#b": 
                    b = "6"
                if i == "tcf":
                    b = "9"                    
                if i == "n#g":
                    b = "a"                    
                if i == "rb":
                    b = "d" 
                                              
                return (b)                            

            except:

                #print("erro fitro mdl15")
                pass

    def mdl16(self,i):

        if i != "b''":
        
            i = self.limpa.string(i) 

            try:

                i= i.split(",")
                    
                i = (i[4])  
                b = (i[-1])                

                if i == "01et":
                    b = "1"               
                if i == "02%u": 
                    b = "2"
                if i == "05d": 
                    b = "5"
                if i == "06$":
                    b = "6"                    
                if i == "td":
                    b = "9"                    
                if i == "n$":
                    b = "a"
                if i == "req":
                    b = "d"                    
                if i == "0e%p":
                    b = "e"
                                              
                return (b)                            

            except:

                #print("erro fitro mdl16")
                pass


    
class Leitor(monta_pacote_in,retorna,filtro):

    def __init__(self):
        
##        self.ser = ser # 9600 38400 115200 Configura a serial e a velocidade de transmissao
        self.mod = monta_pacote_in()
        self.retorna = retorna()
        self.filtro = filtro()
           
# Leitor mdulo expansor 1

    def leitor1_in1(self):

        i = self.mod.ler('0x01') # modulo, entrada
        b = self.filtro.mdl1(i)       
        in1 = self.retorna.entrada(b,'in1')

        return(in1)            
            
    
    def leitor1_in2(self):

        i = self.mod.ler('0x01') 
        
        b = self.filtro.mdl1(i)
        in2 = self.retorna.entrada(b,'in2')

        return(in2)

          
    def leitor1_in3(self):
    
        i = self.mod.ler('0x01')      
        b = self.filtro.mdl1(i)
        in3 = self.retorna.entrada(b,'in3')

        return(in3)
    
            
    def leitor1_in4(self):
    
        i = self.mod.ler('0x01') 
        b = self.filtro.mdl1(i) 
        in4 = self.retorna.entrada(b,'in4')

        return(in4)
                              
# Leitor mdulo expansor 2

    def leitor2_in1(self):

        i = self.mod.ler('0x02') # modulo
        b = self.filtro.mdl2(i) # Limpa e edita os dados recebidos da leitura (i)
        in1 = self.retorna.entrada(b,'in1') 

        return(in1)
            
           
    def leitor2_in2(self):

        i = self.mod.ler('0x02')
        b = self.filtro.mdl2(i)        
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
           
    def leitor2_in3(self):
    
        i = self.mod.ler('0x02')   
        b = self.filtro.mdl2(i) 
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor2_in4(self):
    
        i = self.mod.ler('0x02')  
        b = self.filtro.mdl2(i) 
        in4 = self.retorna.entrada(b,'in4') 

        return(in4)            
            
    
# Leitor mdulo expansor 3

    def leitor3_in1(self):

        i = self.mod.ler('0x03') # modulo, entrada
        b = self.filtro.mdl3(i) # Limpa e edita os dados recebidos da leitura (i)
        in1 = self.retorna.entrada(b,'in1') # Confere em uma tabela binaria qual o valor da entrada requisitada 'in1'
        
        return(in1)
    
    def leitor3_in2(self):

        i = self.mod.ler('0x03') 
        b = self.filtro.mdl3(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor3_in3(self):
    
        i = self.mod.ler('0x03') 
        b = self.filtro.mdl3(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor3_in4(self):
    
        i = self.mod.ler('0x03') 
        b = self.filtro.mdl3(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)


# Leitor mdulo expansor 4
                      
    def leitor4_in1(self):        

        i = self.mod.ler('0x04') # modulo, entrada        
        b = self.filtro.mdl4(i)
        in1 = self.retorna.entrada(b,'in1')

        return (in1)                            

            ##    
    def leitor4_in2(self):

        i = self.mod.ler('0x04') 
        b = self.filtro.mdl4(i)
        in2 = self.retorna.entrada(b,'in2')                

        return(in2)

            
    def leitor4_in3(self):

        i = self.mod.ler('0x04')
        b = self.filtro.mdl4(i)                    
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)

           
    def leitor4_in4(self):
    
        i = self.mod.ler('0x04') 
        b = self.filtro.mdl4(i)
        in4 = self.retorna.entrada(b,'in4') 

        return(in4)

# Leitor mdulo expansor 5
                      
    def leitor5_in1(self):        

        i = self.mod.ler('0x05') # modulo, entrada        
        b = self.filtro.mdl5(i)
        in1 = self.retorna.entrada(b,'in1')

        return (in1)                            

               
    def leitor5_in2(self):

        i = self.mod.ler('0x05') 
        b = self.filtro.mdl5(i)
        in2 = self.retorna.entrada(b,'in2')                

        return(in2)

            
    def leitor5_in3(self):

        i = self.mod.ler('0x05') 
        b = self.filtro.mdl5(i)                    
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)

           
    def leitor5_in4(self):
    
        i = self.mod.ler('0x05') 
        b = self.filtro.mdl5(i)
        in4 = self.retorna.entrada(b,'in4') 

        return(in4)

# Leitor mdulo expansor 6
                      
    def leitor6_in1(self):        

        i = self.mod.ler('0x06') # modulo, entrada        
        b = self.filtro.mdl6(i)
        in1 = self.retorna.entrada(b,'in1')

        return (in1)                            

               
    def leitor6_in2(self):

        i = self.mod.ler('0x06') 
        b = self.filtro.mdl6(i)
        in2 = self.retorna.entrada(b,'in2')                

        return(in2)

            
    def leitor6_in3(self):

        i = self.mod.ler('0x06') 
        b = self.filtro.mdl6(i)                    
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)

           
    def leitor6_in4(self):
    
        i = self.mod.ler('0x06') 
        b = self.filtro.mdl6(i)
        in4 = self.retorna.entrada(b,'in4') 

        return(in4)
            
# Leitor mdulo expansor 7

    def leitor7_in1(self):

        i = self.mod.ler('0x07')       
        b = self.filtro.mdl7(i) 
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor7_in2(self):

        i = self.mod.ler('0x07') 
        b = self.filtro.mdl7(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor7_in3(self):
    
        i = self.mod.ler('0x07') 
        b = self.filtro.mdl7(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor7_in4(self):
    
        i = self.mod.ler('0x07') 
        b = self.filtro.mdl7(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)
              
# Leitor mdulo expansor 8

    def leitor8_in1(self):

        i = self.mod.ler('0x08')       
        b = self.filtro.mdl8(i) 
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor8_in2(self):

        i = self.mod.ler('0x08') 
        b = self.filtro.mdl8(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor8_in3(self):
    
        i = self.mod.ler('0x08') 
        b = self.filtro.mdl8(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor8_in4(self):
    
        i = self.mod.ler('0x08') 
        b = self.filtro.mdl8(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)

# Leitor mdulo expansor 9

    def leitor9_in1(self):

        i = self.mod.ler('0x09')       
        b = self.filtro.mdl9(i) 
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor9_in2(self):

        i = self.mod.ler('0x09') 
        b = self.filtro.mdl9(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor9_in3(self):
    
        i = self.mod.ler('0x09') 
        b = self.filtro.mdl9(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor9_in4(self):
    
        i = self.mod.ler('0x09') 
        b = self.filtro.mdl9(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)

# Leitor mdulo expansor 10

    def leitor10_in1(self):

        i = self.mod.ler('0x0a')       
        b = self.filtro.mdl10(i) 
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor10_in2(self):

        i = self.mod.ler('0x0a') 
        b = self.filtro.mdl10(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor10_in3(self):
    
        i = self.mod.ler('0x0a') 
        b = self.filtro.mdl10(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor10_in4(self):
    
        i = self.mod.ler('0x0b') 
        b = self.filtro.mdl11(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)

# Leitor mdulo expansor 11

    def leitor11_in1(self):

        i = self.mod.ler('0x0b')        
        b = self.filtro.mdl11(i) 
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor11_in2(self):

        i = self.mod.ler('0x0b') 
        b = self.filtro.mdl11(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor11_in3(self):
    
        i = self.mod.ler('0x0b') 
        b = self.filtro.mdl11(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor11_in4(self):
    
        i = self.mod.ler('0x0b') 
        b = self.filtro.mdl11(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)

# Leitor mdulo expansor 12

    def leitor12_in1(self):

        i = self.mod.ler('0x0c')        
        b = self.filtro.mdl12(i) 
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor12_in2(self):

        i = self.mod.ler('0x0c') 
        b = self.filtro.mdl12(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor12_in3(self):
    
        i = self.mod.ler('0x0c') 
        b = self.filtro.mdl12(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor12_in4(self):
    
        i = self.mod.ler('0x0c') 
        b = self.filtro.mdl12(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)

# Leitor mdulo expansor 13

    def leitor13_in1(self):

        i = self.mod.ler('0x0d')       
        b = self.filtro.mdl13(i) 
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor13_in2(self):

        i = self.mod.ler('0x0d') 
        b = self.filtro.mdl13(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor13_in3(self):
    
        i = self.mod.ler('0x0d') 
        b = self.filtro.mdl13(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor13_in4(self):
    
        i = self.mod.ler('0x0d') 
        b = self.filtro.mdl13(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)

# Leitor mdulo expansor 14

    def leitor14_in1(self):

        i = self.mod.ler('0x0e')        
        b = self.filtro.mdl14(i)        
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor14_in2(self):

        i = self.mod.ler('0x0e') 
        b = self.filtro.mdl14(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor14_in3(self):
    
        i = self.mod.ler('0x0e') 
        b = self.filtro.mdl14(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor14_in4(self):
    
        i = self.mod.ler('0x0e') 
        b = self.filtro.mdl14(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)
    
# Leitor mdulo expansor 15

    def leitor15_in1(self):

        i = self.mod.ler('0x0f')        
        b = self.filtro.mdl15(i)        
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor15_in2(self):

        i = self.mod.ler('0x0f') 
        b = self.filtro.mdl15(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor15_in3(self):
    
        i = self.mod.ler('0x0f') 
        b = self.filtro.mdl15(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor15_in4(self):
    
        i = self.mod.ler('0x0f') 
        b = self.filtro.mdl15(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)

# Leitor mdulo expansor 16

    def leitor16_in1(self):

        i = self.mod.ler('0x10')        
        b = self.filtro.mdl16(i)        
        in1 = self.retorna.entrada(b,'in1') 
        
        return(in1)
    
    def leitor16_in2(self):

        i = self.mod.ler('0x10') 
        b = self.filtro.mdl16(i)
        in2 = self.retorna.entrada(b,'in2')
        
        return(in2)
            
         
    def leitor16_in3(self):
    
        i = self.mod.ler('0x10') 
        b = self.filtro.mdl16(i)
        in3 = self.retorna.entrada(b,'in3') 

        return(in3)
            
            
    def leitor16_in4(self):
    
        i = self.mod.ler('0x10') 
        b = self.filtro.mdl16(i)
        in4 = self.retorna.entrada(b,'in4')
        
        return(in4)

#############################################  Acionamento reles Expansores  ##############################


class monta_pacote():

    def __init__(self):

        self = self
##        self.ser = ser
        
    def aciona(self,modulo,rele,funcao): # passar dados como string '0x01','0x01','0xFF'

        modulo = int(modulo,16)
        rele = int(rele,16)
        funcao = int(funcao,16)

        def crc16(byte):

            byte = bytes(byte)

            self.crc16 = libscrc.modbus(byte) #b'\x07\x05\x00\x00\xFF\x00')  # Estrutura para calculo do CRC

            bin2str = (hex(self.crc16))
            bin2str = str(bin2str)

            p = "0x"

            a1 = bin2str[-2]
            a2 = bin2str[-1]
            if a1 == "x":
                a1 = "0"
            a = p + a1 + a2
            
##            print("a",a)

            b1 = bin2str[-4]
            b2 = bin2str[-3]
            if b1 == "x":
                b1 = "0"
            b = p + b1 + b2
            
##            print("b",b)
            
            return(a,b) 
                
        packet = bytearray()  
        packet.append(modulo) # endereço do modulo (dip switch) 
        packet.append(0x05) # modo acionamento de rele 
        packet.append(0x00) #            
        packet.append(rele) # endereço do rele (00,01,02,03) 
        packet.append(funcao) # Liga / Desliga rele
        packet.append(0x00) #
       
        crc = crc16(packet)

        a = int(crc[0],16)
        b = int(crc[1],16)

        packet.append(a) # Controle de redundancia 
        packet.append(b) # Controle de redundancia        
        
        in_bin = escreve_serial(packet)

        in_bin = str(in_bin)

        if in_bin == "b''": # reenviando acionamento rele
            
            cont = 5

            while cont > 0:

##                print("dentro da rotina de reenvio acionamento")

                in_bin = escreve_serial(packet)

                if in_bin == "b''":

                    time.sleep(0.1)
                    cont = cont - 1

                else:

                    return(in_bin)      

        return(in_bin)
        

class Expansor(monta_pacote):

    def __init__(self):

##        self.ser = ser # 9600 38400 115200 
        self.mod = monta_pacote()        
    
# Acionamentos modulo expansor 1

    def liga_rele1_exp1(self):

        self.mod.aciona('0x01','0x00','0xFF') # Modulo, rele , funcao

    def desliga_rele1_exp1(self):

        self.mod.aciona('0x01','0x00','0x00') 

    def liga_rele2_exp1(self):

        self.mod.aciona('0x01','0x01','0xFF') 

    def desliga_rele2_exp1(self):

        self.mod.aciona('0x01','0x01','0x00') 

    def liga_rele3_exp1(self):

        self.mod.aciona('0x01','0x02','0xFF') 

    def desliga_rele3_exp1(self):

        self.mod.aciona('0x01','0x02','0x00')

        
    def liga_rele4_exp1(self):

        self.mod.aciona('0x01','0x03','0xFF')

    def desliga_rele4_exp1(self):

        self.mod.aciona('0x01','0x03','0x00')        


# Acionamentos modulo expansor 2
    
    def liga_rele1_exp2(self):

        self.mod.aciona('0x02','0x00','0xFF') # Modulo, rele , funcao

    def desliga_rele1_exp2(self):

        self.mod.aciona('0x02','0x00','0x00')        

    def liga_rele2_exp2(self):

        self.mod.aciona('0x02','0x01','0xFF') 

    def desliga_rele2_exp2(self):

        self.mod.aciona('0x02','0x01','0x00')        

    def liga_rele3_exp2(self):

        self.mod.aciona('0x02','0x02','0xFF') 

    def desliga_rele3_exp2(self):

        self.mod.aciona('0x02','0x02','0x00')        

    def liga_rele4_exp2(self):

        self.mod.aciona('0x02','0x03','0xFF') 

    def desliga_rele4_exp2(self):

        self.mod.aciona('0x02','0x03','0x00')
        

# Acionamentos modulo expansor 3
    
    def liga_rele1_exp3(self):

        self.mod.aciona('0x03','0x00','0xFF') # Modulo, rele , funcao

    def desliga_rele1_exp3(self):

        self.mod.aciona('0x03','0x00','0x00')        

    def liga_rele2_exp3(self):

        self.mod.aciona('0x03','0x01','0xFF') 

    def desliga_rele2_exp3(self):

        self.mod.aciona('0x03','0x01','0x00')        

    def liga_rele3_exp3(self):

        self.mod.aciona('0x03','0x02','0xFF') 

    def desliga_rele3_exp3(self):

        self.mod.aciona('0x03','0x02','0x00')        

    def liga_rele4_exp3(self):

        self.mod.aciona('0x03','0x03','0xFF') 

    def desliga_rele4_exp3(self):

        self.mod.aciona('0x03','0x03','0x00') 


# Acionamentos modulo expansor 4
    
    def liga_rele1_exp4(self):

        self.mod.aciona('0x04','0x00','0xFF') # Modulo, rele , funcao

    def desliga_rele1_exp4(self):

        self.mod.aciona('0x04','0x00','0x00')        

    def liga_rele2_exp4(self):

        self.mod.aciona('0x04','0x01','0xFF') 

    def desliga_rele2_exp4(self):

        self.mod.aciona('0x04','0x01','0x00')        

    def liga_rele3_exp4(self):

        self.mod.aciona('0x04','0x02','0xFF') 

    def desliga_rele3_exp4(self):

        self.mod.aciona('0x04','0x02','0x00')        

    def liga_rele4_exp4(self):

        self.mod.aciona('0x04','0x03','0xFF') 

    def desliga_rele4_exp4(self):

        self.mod.aciona('0x04','0x03','0x00')

# Acionamentos modulo expansor 5
    
    def liga_rele1_exp5(self):

        self.mod.aciona('0x05','0x00','0xFF') # Modulo, rele , funcao

    def desliga_rele1_exp5(self):

        self.mod.aciona('0x05','0x00','0x00')        

    def liga_rele2_exp5(self):

        self.mod.aciona('0x05','0x01','0xFF') 

    def desliga_rele2_exp5(self):

        self.mod.aciona('0x05','0x01','0x00')        

    def liga_rele3_exp5(self):

        self.mod.aciona('0x05','0x02','0xFF') 

    def desliga_rele3_exp5(self):

        self.mod.aciona('0x05','0x02','0x00')        

    def liga_rele4_exp5(self):

        self.mod.aciona('0x05','0x03','0xFF') 

    def desliga_rele4_exp5(self):

        self.mod.aciona('0x05','0x03','0x00')

# Acionamentos modulo expansor 6
    
    def liga_rele1_exp6(self):

        self.mod.aciona('0x06','0x00','0xFF') # Modulo, rele , funcao

    def desliga_rele1_exp6(self):

        self.mod.aciona('0x06','0x00','0x00')        

    def liga_rele2_exp6(self):

        self.mod.aciona('0x06','0x01','0xFF') 

    def desliga_rele2_exp6(self):

        self.mod.aciona('0x06','0x01','0x00')        

    def liga_rele3_exp6(self):

        self.mod.aciona('0x06','0x02','0xFF') 

    def desliga_rele3_exp6(self):

        self.mod.aciona('0x06','0x02','0x00')        

    def liga_rele4_exp6(self):

        self.mod.aciona('0x06','0x03','0xFF') 

    def desliga_rele4_exp6(self):

        self.mod.aciona('0x06','0x03','0x00') 

# Acionamentos modulo expansor 7    
    
    def liga_rele1_exp7(self):

        self.mod.aciona('0x07','0x00','0xFF') 

    def desliga_rele1_exp7(self):

        self.mod.aciona('0x07','0x00','0x00') 

    def liga_rele2_exp7(self):

        self.mod.aciona('0x07','0x01','0xFF') 

    def desliga_rele2_exp7(self):

        self.mod.aciona('0x07','0x01','0x00') 

    def liga_rele3_exp7(self):

        self.mod.aciona('0x07','0x02','0xFF') 

    def desliga_rele3_exp7(self):

        self.mod.aciona('0x07','0x02','0x00') 
  
    def liga_rele4_exp7(self):

        self.mod.aciona('0x07','0x03','0xFF')        
    def desliga_rele4_exp7(self):

        self.mod.aciona('0x07','0x03','0x00')

# Acionamentos modulo expansor 8   
    
    def liga_rele1_exp8(self):

        self.mod.aciona('0x08','0x00','0xFF') 

    def desliga_rele1_exp8(self):

        self.mod.aciona('0x08','0x00','0x00') 

    def liga_rele2_exp8(self):

        self.mod.aciona('0x08','0x01','0xFF') 

    def desliga_rele2_exp8(self):

        self.mod.aciona('0x08','0x01','0x00') 

    def liga_rele3_exp8(self):

        self.mod.aciona('0x08','0x02','0xFF') 

    def desliga_rele3_exp8(self):

        self.mod.aciona('0x08','0x02','0x00') 
  
    def liga_rele4_exp8(self):

        self.mod.aciona('0x08','0x03','0xFF')        
    def desliga_rele4_exp8(self):

        self.mod.aciona('0x08','0x03','0x00')

# Acionamentos modulo expansor 9    
    
    def liga_rele1_exp9(self):

        self.mod.aciona('0x09','0x00','0xFF') 

    def desliga_rele1_exp9(self):

        self.mod.aciona('0x09','0x00','0x00') 

    def liga_rele2_exp9(self):

        self.mod.aciona('0x09','0x01','0xFF') 

    def desliga_rele2_exp9(self):

        self.mod.aciona('0x09','0x01','0x00') 

    def liga_rele3_exp9(self):

        self.mod.aciona('0x09','0x02','0xFF') 

    def desliga_rele3_exp9(self):

        self.mod.aciona('0x09','0x02','0x00') 
  
    def liga_rele4_exp9(self):

        self.mod.aciona('0x09','0x03','0xFF')        
    def desliga_rele4_exp9(self):

        self.mod.aciona('0x09','0x03','0x00')

# Acionamentos modulo expansor 10    
    
    def liga_rele1_exp10(self):

        self.mod.aciona('0xa','0x00','0xFF') 

    def desliga_rele1_exp10(self):

        self.mod.aciona('0xa','0x00','0x00') 

    def liga_rele2_exp10(self):

        self.mod.aciona('0xa','0x01','0xFF') 

    def desliga_rele2_exp10(self):

        self.mod.aciona('0xa','0x01','0x00') 

    def liga_rele3_exp10(self):

        self.mod.aciona('0xa','0x02','0xFF') 

    def desliga_rele3_exp10(self):

        self.mod.aciona('0xa','0x02','0x00') 
  
    def liga_rele4_exp10(self):

        self.mod.aciona('0xa','0x03','0xFF')        
    def desliga_rele4_exp10(self):

        self.mod.aciona('0xa','0x03','0x00')

# Acionamentos modulo expansor 11    
    
    def liga_rele1_exp11(self):

        self.mod.aciona('0xb','0x00','0xFF') 

    def desliga_rele1_exp11(self):

        self.mod.aciona('0xb','0x00','0x00') 

    def liga_rele2_exp11(self):

        self.mod.aciona('0xb','0x01','0xFF') 

    def desliga_rele2_exp11(self):

        self.mod.aciona('0xb','0x01','0x00') 

    def liga_rele3_exp11(self):

        self.mod.aciona('0xb','0x02','0xFF') 

    def desliga_rele3_exp11(self):

        self.mod.aciona('0xb','0x02','0x00') 
  
    def liga_rele4_exp11(self):

        self.mod.aciona('0xb','0x03','0xFF')        
    def desliga_rele4_exp11(self):

        self.mod.aciona('0xb','0x03','0x00')

# Acionamentos modulo expansor 12    
    
    def liga_rele1_exp12(self):

        self.mod.aciona('0xc','0x00','0xFF') 

    def desliga_rele1_exp12(self):

        self.mod.aciona('0xc','0x00','0x00') 

    def liga_rele2_exp12(self):

        self.mod.aciona('0xc','0x01','0xFF') 

    def desliga_rele2_exp12(self):

        self.mod.aciona('0xc','0x01','0x00') 

    def liga_rele3_exp12(self):

        self.mod.aciona('0xc','0x02','0xFF') 

    def desliga_rele3_exp12(self):

        self.mod.aciona('0xc','0x02','0x00') 
  
    def liga_rele4_exp12(self):

        self.mod.aciona('0xc','0x03','0xFF')        
    def desliga_rele4_exp12(self):

        self.mod.aciona('0xc','0x03','0x00')

# Acionamentos modulo expansor 13    
    
    def liga_rele1_exp13(self):

        self.mod.aciona('0xd','0x00','0xFF') 

    def desliga_rele1_exp13(self):

        self.mod.aciona('0xd','0x00','0x00') 

    def liga_rele2_exp13(self):

        self.mod.aciona('0xd','0x01','0xFF') 

    def desliga_rele2_exp13(self):

        self.mod.aciona('0xd','0x01','0x00') 

    def liga_rele3_exp13(self):

        self.mod.aciona('0xd','0x02','0xFF') 

    def desliga_rele3_exp13(self):

        self.mod.aciona('0xd','0x02','0x00') 
  
    def liga_rele4_exp13(self):

        self.mod.aciona('0xd','0x03','0xFF')        
    def desliga_rele4_exp13(self):

        self.mod.aciona('0xd','0x03','0x00')

# Acionamentos modulo expansor 14    
    
    def liga_rele1_exp14(self):

        self.mod.aciona('0xe','0x00','0xFF') 

    def desliga_rele1_exp14(self):

        self.mod.aciona('0xe','0x00','0x00') 

    def liga_rele2_exp14(self):

        self.mod.aciona('0xe','0x01','0xFF') 

    def desliga_rele2_exp14(self):

        self.mod.aciona('0xe','0x01','0x00') 

    def liga_rele3_exp14(self):

        self.mod.aciona('0xe','0x02','0xFF') 

    def desliga_rele3_exp14(self):

        self.mod.aciona('0xe','0x02','0x00') 
  
    def liga_rele4_exp14(self):

        self.mod.aciona('0xe','0x03','0xFF')        
    def desliga_rele4_exp14(self):

        self.mod.aciona('0xe','0x03','0x00')

# Acionamentos modulo expansor 15    
    
    def liga_rele1_exp15(self):

        self.mod.aciona('0xf','0x00','0xFF') 

    def desliga_rele1_exp15(self):

        self.mod.aciona('0xf','0x00','0x00') 

    def liga_rele2_exp15(self):

        self.mod.aciona('0xf','0x01','0xFF') 

    def desliga_rele2_exp15(self):

        self.mod.aciona('0xf','0x01','0x00') 

    def liga_rele3_exp15(self):

        self.mod.aciona('0xf','0x02','0xFF') 

    def desliga_rele3_exp15(self):

        self.mod.aciona('0xf','0x02','0x00') 
  
    def liga_rele4_exp15(self):

        self.mod.aciona('0xf','0x03','0xFF')        
    def desliga_rele4_exp15(self):

        self.mod.aciona('0xf','0x03','0x00')

# Acionamentos modulo expansor 16    
    
    def liga_rele1_exp16(self):

        self.mod.aciona('0x10','0x00','0xFF') 

    def desliga_rele1_exp16(self):

        self.mod.aciona('0x10','0x00','0x00') 

    def liga_rele2_exp16(self):

        self.mod.aciona('0x10','0x01','0xFF') 

    def desliga_rele2_exp16(self):

        self.mod.aciona('0x10','0x01','0x00') 

    def liga_rele3_exp16(self):

        self.mod.aciona('0x10','0x02','0xFF') 

    def desliga_rele3_exp16(self):

        self.mod.aciona('0x10','0x02','0x00') 
  
    def liga_rele4_exp16(self):

        self.mod.aciona('0x10','0x03','0xFF')        
    def desliga_rele4_exp16(self):

        self.mod.aciona('0x10','0x03','0x00')

 
##############################################  Threads dos programas  ##########################################################

def thread_qrcode(qrcode): # Programa do QR Code

    log("Programa QR Code em execução")

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
##            log("Estado das enradas A B C D ",A,B,C,D," ligado (0)")
##            cont = 1
    
        if comando == "abre_social":

##            log("Reconheceu o abre_social",hs)

            entradas = Entradas()
            pm1 = entradas.pm1
                                
            if pm1 == 1: # O portão social já esta aberto

                log("O portão social já esta aberto")
                            
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
                    
                    txt = ("Abrindo portão Social")
                    log(txt)
                    abre.social()

                    if audio == 1: # Ativa as mensagens de abertura e fechamento

                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_social.mp3")                   
                    
                    time.sleep(2) # Tempo minimo para o portão abrir

                    entradas = Entradas()
                    pm1 = entradas.pm1
                                        
                    if pm1 == 0: # Portão fechado pois não abriu com o comando

                        log("Portão Social emperrado")

                        os.system("mpg123 /home/pi/CMM/mp3/social_emperrado.mp3")
                                                
                        rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada

                        evento.enviar("E","132","008") # Envia portão emperrado                        

                    if pm1 == 1: # Portão abriu

##                        evento.enviar("E","133","001") # Envia abriu portão
                        
                        contador = 300 # Tempo maximo para o social ficar aberto 30 segundos
                        log("Esperando por 15 segundos o portão social fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = Entradas()
                            pm1 = entradas.pm1
                            
                            # Esperando o portão social fechar...
                            
                            if pm1 == 0: # portão fechou

                                log("Portão social fechou")
##                                evento.enviar("R","133","001") # Envia fechamento
                                contador = 1
                                                            
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada

                                break

                            if (pm1 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                log("Portão social aberto por muito tempo")
                                
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
                                log("Agurade o fechamento do social")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_para_acionar.mp3") # Necessario manter esse audio sempre ativo
                                time.sleep(1)
                                
                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1
                            
                entradas = Entradas()
                pm2 = entradas.pm2
  
                        
        if comando == "abre_eclusa":

##            log("Reconheceu o abre_eclusa")

            entradas = Entradas()
            pm2 = entradas.pm2            

            if pm2 == 1: # O portão Eclusa já esta aberto

                log("O portão Eclusa já esta aberto")

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
                    
                    txt = ("Abrindo portão Eclusa")
                    log(txt)
                    abre.eclusa()
                                        

                    if audio == 1:
                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_eclusa.mp3")
                    
                    time.sleep(3) # Tempo de espera para o portão abrir

                    entradas = Entradas()
                    pm2 = entradas.pm2
                    
                    if pm2 == 0: # Portão fechado não abriu após o comando

                       log("Portão eclusa emperrado")
                       
                       os.system("mpg123 /home/pi/CMM/mp3/eclusa_emperrado.mp3")
                            
                       rele.desliga(1) # Libera o social para abrir mesmo com a eclusa aberta

                       evento.enviar("E","132","009") # Envia portão emperrado

                    if pm2 == 1: # Portão aberto

##                        evento.enviar("E","133","003") # Envia abertura
                        
                        contador = 300 # Tempo maximo para eclusa ficar aberta 30 segundos
                        log("Esperando por 30 segundos o portão Eclusa fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = Entradas()
                            pm2 = entradas.pm2
                            
                            # Esperando o portão eclusa fechar...

                            if pm2 == 0: # portão fechou

                                log("Portão Eclusa fechou")
##                                evento.enviar("R","133","003") # Envia fechamento
                                contador = 1
                                
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(1) # Libera o social para abrir

                                break

                            if (pm2 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                log("Portão Eclusa aberto por muito tempo")
                                
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

                                log("Aguarde o fechamento do portão")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_para_acionar.mp3") # Manter esse audio sempre ativo
                                time.sleep(1)
                                

                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1


def Portoes_sociais(Rele): # Programa
    
    log("Programa Sociais em execução ")

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

        banco = Banco()

        ihm_soc1 = banco.consulta("comandos","abre_social_externo")
        ihm_soc2 = banco.consulta("comandos","abre_social_interno")
       
        if ctw1 == 0 or ihm_soc1 == "1":

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
                
        if btn2 == 0:
            
            if habilita_intertravamento == "0":

                log("Intertravamento desabilitado\n")

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

                log("Intertravamento desabilitado\n")

                abre = Abre()
                abre.social()

            else:

                log("Intertravamento habilitado\n")

                if saida == 1:

                    log ("Abrindo pelo botão de saida")
                    os.system("mpg123 /home/pi/CMM/mp3/ate_logo.mp3")
                    Intertravamento("abre_social")                
                
                    saida = 0

                else:

                    log("Uso incorreto do sistema")
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
        log("Abrindo social...")
        
    def eclusa(self):

        status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não dispara o arrombamento
        status.write("1")
        status.close()        
    
        rele.pulso(5,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)
        log("Abrindo eclusa...")
        
########################################## Métodos de acesso a classe leitor #####################################

def leitor(entrada):

##    mutex.acquire() # Trava para acesso exclusivo

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
    
##    mutex.release() # Desbloqueia trava de acesso

################################################ THREADS ROTINAS #################################################


def Garagem1(Rele): # Inicia a thread do portão da garagem importando a classe Rele

    log("Programa Garagem Terreo em execução ")
    
    s = Expansor()
    
    s.desliga_rele4_exp1() # Garante que a sirene esteja desligada    
    s.desliga_rele1_exp1() # Garante que o Abre esteja desligado    
    s.desliga_rele2_exp1() # Garante que o Foto esteja desligado

    banco = Banco()
            
    while(1):

        hs = time.strftime("%H:%M:%S")
        s = Expansor()

        ihm_gar1 = banco.consulta("comandos","abre_garagem")        
        tx1 =  leitor("leitor1_in3")  # Cantato abre vindo do TX (LINEAR HCS)
                
        if (tx1 == 1 or ihm_gar1 == "1"):    # Se o tx mandou abrir o portão

            time.sleep(0.1)

            if (tx1 == 1 or ihm_gar1 == "1"):

                log("reconheceu tx Garagem")

                if ihm_gar1 == "1":

                    s.liga_rele1_exp1()
                    time.sleep(2)
                    s.desliga_rele1_exp1()
                    

                banco.atualiza("comandos","abre_garagem","0")

                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                status.write("1")
                status.close()

                time.sleep(3) # Tempo para começar a abrir o portão

                pmg1 = leitor("leitor1_in1")

                cont = 150     # Tempo maximo para deixar o portão aberto (150 = 30 segundos)
                
                if pmg1 == 1: # Portão não abriu apos o comando

                    log("Portão garagem não abriu")
                    evento.enviar("E","132","015") # Emperrado
                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                    status.write("0")
                    status.close()
                                        
                    cont = 0

                if pmg1 == 0: # Portão abriu

    ##                    evento.enviar("E","133","013")

                    while cont > 0:   # Enquanto o portão esta aberto verifica

                        if cont == 150:

                            log("Portão Garagem abriu")
                        
                        pmg1 = leitor("leitor1_in1")
                        
                        if pmg1 == 1: # Se o portão ja fechou

                            log("Portão Garagem fechou\n")

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

                                log("Acionou a barreira Garagem")

                                while bar1 == 1: # Enquanto a barreira esta acionada

                                    bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1

                                    # Alguem esta na frente da barreira

                                    time.sleep(0.1)
                                    
    ##                                log("Passou alguem, verificando dupla passagem...")

                                pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico
                                
                                if pmg1 == 0:

                                    pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico

                                    log("Aguardando portão Garagem fechar")

                                    while pmg1 == 0:  # Enquanto o portão ainda não fechou                                

                                        pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico
                                        bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1
                                        tx1 =  leitor("leitor1_in3")  # Cantato abre vindo do TX (LINEAR HCS)  

                                        if bar1 == 1: # Dupla passagem

                                            time.sleep(0.2)
                                            bar1 = leitor("leitor1_in2")

                                            if bar1 == 1:

                                                log("Dupla passagem Garagem")

                                                evento.enviar("E","132","019")

                                                s.liga_rele4_exp1() # Sirene                                            
                                                time.sleep(10)
                                                s.desliga_rele4_exp1()                                            

                                                break

                                        if tx1 == 1: # Alguem acionou o controle enquanto o portão fechava

                                            cont = 0
                                            
                                            break # Sai da função e inicia novamente a verificação

                                        time.sleep(0.1)
                                 
    ##                                log("Fim do cilo Garagem")

                                time.sleep(1)

                        cont = cont - 1
                        time.sleep(0.2)

                    if cont == 1: # Passaram se 29 segundos e o portão não fechou

                        log("Portão Garagem aberto muito tempo")

                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                        status.write("0")
                        status.close()

                        evento.enviar("E","132","019") # Envia evento de portão aberto
                        cont = 0
                        break
        time.sleep(0.1)
        
def Garagem2(Rele): # Inicia a thread do portão da garagem importando a classe Rele

    log("Programa Garagem Subsolo em execução ")

    s2 = Expansor()    
    
    s2.desliga_rele4_exp7() # Garante que a sirene esteja desligada
    s2.desliga_rele1_exp7() # Garante que o Abre esteja desligado
    s2.desliga_rele2_exp7() # Garante que o Foto esteja desligado

    banco = Banco()
            
    while(1):

        hs = time.strftime("%H:%M:%S")        
        s2 = Expansor()

        ihm_gar2 = banco.consulta("comandos","abre_subsolo")        
        tx2 =  leitor("leitor7_in3")  # Cantato abre vindo do TX (LINEAR HCS)               
        
        if (tx2 == 1 or ihm_gar2 == "1"):    # Se o tx mandou abrir o portão

            time.sleep(0.1)
            #tx2 =  leitor("leitor7_in3")

            if (tx2 == 1 or ihm_gar2 == "1"):

                log("reconheceu tx Subsolo")

                if ihm_gar2 == "1":

                    s2.liga_rele1_exp7()
                    time.sleep(2)
                    s2.desliga_rele1_exp7()
                    

                banco.atualiza("comandos","abre_subsolo","0")

                status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                status.write("1")
                status.close()

                time.sleep(3) # Tempo para começar a abrir o portão

                pmg2 = leitor("leitor7_in1")

                cont = 150     # Tempo maximo para deixar o portão aberto (150 = 30 segundos)
                
                if pmg2 == 1: # Portão não abriu apos o comando

                    log("Portão Subsolo não abriu")
                    evento.enviar("E","132","018")
                    status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                    status.write("0")
                    status.close()
                                    
                    cont = 0

                if pmg2 == 0: # Portão abriu

                    while cont > 0:   # Enquanto o portão esta aberto verifica

                        if cont == 150:

                            log("Portão Subsolo abriu")
                        
                        pmg2 = leitor("leitor7_in1")
                        
                        if pmg2 == 1: # Se o portão ja fechou

                            log("Portão Subsolo fechou\n")

                            status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                            status.write("0")
                            status.close()

                            time.sleep(2)
                            
                            cont = 0
                            break
                            
                        if pmg2 == 0:     # Se o portão ainda esta aberto

                            bar2 = leitor("leitor7_in2") # Faz a leitura da barreira 1

                            if bar2 == 1: # Se acionou a barreira de entrada

                                log("Acionou a barreira Subsolo")

                                while bar2 == 1: # Enquanto a barreira esta acionada

                                    bar2 = leitor("leitor7_in2") # Faz a leitura da barreira 1

                                    # Alguem esta na frente da barreira

                                    time.sleep(0.1)
                                    
##                                log("Passou alguem Subsolo, verificando dupla passagem...")

                                pmg2 = leitor("leitor7_in1") # Faz a leitura do ponto magnetico
                                
                                if pmg2 == 0:

                                    pmg2 = leitor("leitor7_in1") # Faz a leitura do ponto magnetico

                                    log("Aguardando portão Subsolo fechar")

                                    while pmg2 == 0:  # Enquanto o portão ainda não fechou                                

                                        pmg2 = leitor("leitor7_in1") # Faz a leitura do ponto magnetico
                                        bar2 = leitor("leitor7_in2") # Faz a leitura da barreira 1
                                        tx2 =  leitor("leitor7_in3")  # Cantato abre vindo do TX (LINEAR HCS)  

                                        if bar2 == 1: # Dupla passagem

                                            time.sleep(0.2)
                                            bar2 = leitor("leitor7_in2")

                                            if bar2 == 1:

                                                log("Dupla passagem Subsolo")

                                                evento.enviar("E","132","019")

                                                s2.liga_rele4_exp7() # Sirene
                                                time.sleep(10)
                                                s2.desliga_rele4_exp7()

                                                break

                                        if tx2 == 1: # Alguem acionou o controle enquanto o portão fechava

                                            cont = 0
                                            
                                            break # Sai da função e inicia novamente a verificação

                                        time.sleep(0.1)
                                        
##                                log("Fim do cilo Subsolo")                                

                                time.sleep(1)

                        cont = cont - 1
                        time.sleep(0.2)

                    if cont == 1: # Passaram se 29 segundos e o portão não fechou

                        log("Portão Subsolo aberto muito tempo")

                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                        status.write("0")
                        status.close()

                        evento.enviar("E","132","019")# Envia evento de portão aberto
                        cont = 0
                        break     
        time.sleep(0.1)
        
def Arrombamento(Rele): # Inicia a thread arrombamento de portões
    
    log("Programa arrombamento de portões em execução")

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

                cont1 = 60 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 60 segundos
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

                cont2 = 60 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 60 segundos
                ar2 = 0
                reset_ar2 = 0
                rele.desliga(8)

        
        time.sleep(2)   

def Servidor(Rele,Abre): # Inicia a thread do portão da garagem importando a classe Rele
    
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

    mudanca1 = 0
    
    while(1): 
        
##        l = Leitor() # inicia a classe para leitura das entradas dos modulos expansores 
        s = Expansor()

        pmg1 = leitor("leitor1_in1") # Ponto magnetico portão leitor 1 entrada 1      
        mud1 = leitor("leitor1_in4")  # Chave de mudança

        t = open("/home/pi/CMM/status_garagem_1.cmm","r")
        status_tx1 = t.read()
        t.close()
                

        if mud1 == 1 and mudanca1 == 0: # Chave de mudança acionada

            time.sleep(0.1)

            pmg1 = leitor("leitor1_in1") # Ponto magnetico portão leitor 1 entrada 1      
            mud1 = leitor("leitor1_in4")  # Chave de mudança            

            if mud1 == 1 and mudanca1 == 0:    

                log("Chave de mudança acionada Garagem")

                evento.enviar("E","132","26")                

                t = open("/home/pi/CMM/status_garagem_1.cmm","w")
                t.write("1")
                t.close()

                s.liga_rele1_exp1() # Aciona o rele 1 do modulo 1 (Abre)
                time.sleep(2)
                s.desliga_rele1_exp1()
                s.liga_rele2_exp1() # Aciona o rele 2 do modulo 1 (Foto)                

                mudanca1 = 1

        if mud1 == 0 and mudanca1 == 1:

            time.sleep(0.1)
            mud1 = leitor("leitor1_in4")

            if mud1 == 0:

                log("Desligada a chave de mudança")

                evento.enviar("R","132","26")
                                
                s.desliga_rele1_exp1() # Desliga o rele 1 do modulo 1 (Abre)
                s.desliga_rele2_exp1() # Desliga o rele 2 do modulo 1 (Foto) 

                pmg1 = leitor("leitor1_in1")

                cont = 30 # Tempo maximo de espera

                log("Aguardando portão Garagem fechar depois da mudanca")

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
                        mudanca1 = 0
                        time.sleep(1)
                        break
            
        if pmg1 == 0 and mudanca1 == 0 and status_tx1 == "0": # Violação do portão da garagem                              

            cont = 10
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

                log("violação do portão garagem 1")

                s.liga_rele4_exp1() # Sirene
                            
                evento.enviar("E","132","014")

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

##                violacao = 0
                
                time.sleep(30)
                
        time.sleep(1)
        
def Alarmes_garagem_2(Rele):

    log("Programa Alarmes Garagem Subsolo em execução")

    mudanca2 = 0
    
    while(1):        

        s2 = Expansor()
        
        pmg2 = leitor("leitor7_in1") # Ponto magnetico portão leitor 1 entrada 1        

        t = open("/home/pi/CMM/status_garagem_2.cmm","r")
        status_tx2 = t.read()
        t.close()
                                
        if pmg2 == 0 and status_tx2 == "0": # Violação do portão da garagem
            
            cont = 10
            violacao = 1
            
            while cont > 0: # Filtro

                t = open("/home/pi/CMM/status_garagem_2.cmm","r")
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

                log("violação do portão Subsolo")

                s2.liga_rele4_exp7() # Sirene
                                            
                evento.enviar("E","132","016")

                cont = 30 # Tempo maximo de espera

                log("Aguardando portão Subsolo fechar apos violação")

                while cont > 0:

                    pmg2 = leitor("leitor7_in1")

                    if(pmg2 == 0): # Portão ainda aberto                                      

                        time.sleep(1)
                        cont = cont - 1
                            
                    if (pmg2 == 1): # Portão ja fechou

                        log("Portão Subsolo fechou")

                        t = open("/home/pi/CMM/status_garagem_2.cmm","w")
                        t.write("0")
                        t.close()
                        
                        cont = 0
                        time.sleep(1)
                        
                        s2.desliga_rele4_exp7() # Desliga sirene
                        
                        break
                    
                s2.desliga_rele4_exp7() # Desliga sirene
                
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

##                log("Tentanto enviar o evento",evento)

                try:
        
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = (evento + "\r") # ("7000 185808E30500008")  # Envia abriu portão da eclusa para a central de monitormento
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    log(reply.decode('utf-8'))
                    s.close()

                    enviado = 1                    
                                
                except Exception as err:
                    
##                    log("Não conseguiu enviar o evento, sem conexão no momento",err)
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

##log ("\nTemperatura",temperatura.cpu(),"°C\n")  # obter temperatura

##email.enviar("O Programa acabou de reiniciar\nPosso enviar qualquer mensagem aqui...") # Não usar nenhum caracter especial na mensagem

##tempo = clima.clima_atual()
##log(tempo)

##evento.enviar_contact_id('E','132','001') # Evento ou Restauração / Evento / Setor

###################################################################################################

log("Temperatura " + str(temperatura.cpu()) + "°C\n")  # obter temperatura



while(1):

    # Colocar aqui o keep alive  
    

    time.sleep(1)

