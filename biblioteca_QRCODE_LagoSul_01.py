#!/usr/bin/env python3
# -*- coding:utf-8 -*-

# Biblioteca QR Code 24/06/2019

import time
from datetime import datetime, timedelta
import os     # Executa comandos do sistema operacional Ex.: os.system('sudo reboot now'))
import sys
from biblioteca_CMM_oficial import Rele, Evento
from banco import Banco # Classe para inserções, consulta e atualização no banco de dados CMM

import socket
import mysql.connector
from condfy import Notifica

######################################  Leitor QR Code  #############################################

class Qrcode(Rele,Evento,Notifica,Banco):

    print("Instanciou a classe Qrcode")

    def __init__(self,ip,cliente,rele,portao,notifica):

        Rele.__init__(self)
        Evento.__init__(self,cliente)

        self.cliente = cliente
        self.rele = Rele()
        self.evento = Evento(cliente) # "5987"
        self.ip_qrcode = ip #'172.18.34.249'
        self.out = rele
        self.portao = portao
        self.avisa_condfy = Notifica()
        self.banco = Banco()

        if notifica == "1":
            
            self.notifica = "1"

        else:

             self.notifica = "0"
            
    def start(self):

        def garagem_entrada():

            status = open("status_garagem_entrada.cmm","w") # Para não disparar o arrombamento
            status.write("1")
            status.close()        
        
            self.rele.pulso(self.out,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)

            print("Abrindo portão Garagem Entrada")

            os.system("mpg123 /home/pi/CMM/mp3/acesso_qr.mp3")

            status = open("status_garagem_entrada.cmm","w") # Para não disparar o arrombamento
            status.write("0")
            status.close()
            
        def garagem_saida():

            status = open("status_garagem_saida.cmm","w") # Para não disparar o arrombamento
            status.write("1")
            status.close()        
        
            self.rele.pulso(self.out,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)

            print("Abrindo portão Garagem Saida")

            os.system("mpg123 /home/pi/CMM/mp3/ate_logo.mp3")

            status = open("status_garagem_saida.cmm","w") # Para não disparar o arrombamento
            status.write("0")
            status.close()

        data = time.strftime('%d/%m/%y') 
        
        try:

            socket.setdefaulttimeout(99999999)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.ip_qrcode, 5001) # PORTA PADRAO DO LEITOR DE QR CODE
            time.sleep(0.1)
            sock.connect(server_address)

            print('\nConectado com Leitor QR CODE {} port {}'.format(*server_address),"\n")

            while(1):

                consulta = 0
                id_valido = 0
                acesso = 0
                fora_do_horario = 0
                item = 0

                hs = time.strftime("%H:%M:%S") # MANTEM ATUALIZADO O HORARIO DO REGISTRO DE LOG

                try: 

                    tamanho = 0
                    dados = sock.recv(128)
                    tamanho += len(dados)

                    if (tamanho >= 16 or tamanho <8): # Se o QR Code lido não tiver exatamente o mesmo tamanho não consulta o banco de dados

                        consulta = 0
                        dados = 0

                    if (tamanho >= 8 and tamanho < 16): # Se tiver o tamanho exato, prossegue
                                        
                        dados = int(dados) # Elimina as '' e o \r
                        dados = str(dados)

                        print("Dados lidos pelo leitor " + dados)

                        dados = dados[3:] # elimina os 3 primeiros digitos da string dados

                        dados = int(dados)
                        consulta = 1
                            
                        tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327, 618, 379, 739, 132, 205, 902, 335, 396, 407, 871, 867, 213, 982, 980, 252, 228, 881, 137, 138, 216, 825, 536, 681, 895, 921, 711, 375, 908, 429, 656, 304, 560, 988, 642, 965, 183, 629, 432, 360, 728, 801, 796, 716, 631, 495, 587, 917, 732, 275, 119, 558, 675, 672, 729, 612, 517, 962, 995, 668, 144, 513, 987, 109, 563, 177, 257, 975, 626, 575, 813, 377, 363, 484, 170, 284, 869, 726, 502, 841, 808, 219, 286, 670, 614]                         

                        if (1):
                            
                            for item in tabela:
                                     
                                id_raiz = int(dados / item)  # divide o valor lido no QR por cada numero da tabela e consulta no banco

                                self.id_raiz = id_raiz
                                
                                try:

                                    cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                                    cursor = cnx.cursor()

                                except mysql.connector.Error as err:

                                    print("Opa, problema com o banco de dados",err)                                                                              
                                    print(err)
                                
                                try:                    

                                    query = ("SELECT ID FROM qrcode WHERE ID = %s")%id_raiz
                                    cursor.execute(query)

                                    for i in cursor: # Se o cursor encontrar o item especificado, prossegue...
                                                                                                        
                                        id_valido = 1 # Encontrou o ID raiz
                                        consulta = 1 # Habilita a consulta de data e horario

                                except Exception as e:
                                
                                    print("Tipo de erro: " + str(e))
                                    break

                        item = item
                                
                except Exception as e:

                    print("Não foi possivel ler os dados recebidos\n")
                    print("Tipo de erro: " + str(e))
                    
                if consulta == 0:

                    print("\nQR Code em formato invalido")
                    print("Texto",dados,"\n")
                     
                    os.system("mpg123 /home/pi/mp3/206.mp3")#  Formato de QR Code inválido
                    time.sleep(3)

                if consulta == 1:

                    item = item

                    try:

                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()

                    except mysql.connector.Error as err:
                            
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                  
                            print("Alguma coisa esta errada com o nome de usuario ou a senha!")

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write("Data: " + data + " " + hs + " Evento: Banco de Dados: Usuario ou senha invalidos\n")
                            arquivo.close()

                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                  
                            print("Esta base de dados não existe!")

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write("Data: " + data + " " + hs + " Evento: Banco de Dados: A base de dados não existe\n")
                            arquivo.close()

                        else:
                                          
                            print(err)

                    if id_valido == 1:

                        hs = time.strftime("%H:%M:%S")
                        consta_no_banco = 1

                        try:

                            query = ("SELECT * FROM qrcode WHERE data_final >= CURDATE() AND ID = %s")%id_raiz
                            cursor.execute(query)
                                  
                            for i in cursor: # Se encontrar o item especificado, divide as informações e salva nas variaveis
                                                     
                                ID = i[0]
                                nome = i[1]
                                ap = i[2]
                                bloco = i[3]
                                cond = i[4]
                                hora_inicio = i[5]
                                hora_final = i[6]
                                data_inicio = i[7]
                                data_final = i[8]
                                dias_semana = i[9]

                                print("\nID",ID,"\nNome",nome,"valido de",data_inicio.strftime('%d/%m/%Y'),"até",data_final.strftime('%d/%m/%Y'),"das",hora_inicio,"as",hora_final,"hs","dias da semana",dias_semana)

                                hs = str(hs)
                                consta_no_banco = 1

                            # Calculos para verificar a compatibilidade do código dinamico com o horario

                                tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327, 618, 379, 739, 132, 205, 902, 335, 396, 407, 871, 867, 213, 982, 980, 252, 228, 881, 137, 138, 216, 825, 536, 681, 895, 921, 711, 375, 908, 429, 656, 304, 560, 988, 642, 965, 183, 629, 432, 360, 728, 801, 796, 716, 631, 495, 587, 917, 732, 275, 119, 558, 675, 672, 729, 612, 517, 962, 995, 668, 144, 513, 987, 109, 563, 177, 257, 975, 626, 575, 813, 377, 363, 484, 170, 284, 869, 726, 502, 841, 808, 219, 286, 670, 614]
                                tempo_validade = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600, 610, 620, 630, 640, 650, 660, 670, 680, 690, 700, 710, 720, 730, 740, 750, 760, 770, 780, 790, 800, 810, 820, 830, 840, 850, 860, 870, 880, 890, 900, 910, 920, 930, 940, 950, 960, 970, 980, 990, 1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1080, 1090, 1100, 1110, 1120, 1130, 1140, 1150, 1160, 1170, 1180, 1190, 1200, 1210, 1220, 1230, 1240, 1250, 1260, 1270, 1280, 1290, 1300, 1310, 1320, 1330, 1340, 1350, 1360, 1370, 1380, 1390, 1400, 1410, 1420, 1430, 1440]
                             
                                minutos_equivalentes = (tempo_validade[tabela.index(item)])-10 # minutos equivalentes a mesma posição em que foi encontrado o multiplicador valido

                                print("Posição do multiplicador valido",tabela.index(item))
                                print("Minutos equivalente",minutos_equivalentes)
                                
                                confere_tabela = hora_inicio + timedelta(minutes = minutos_equivalentes) # Horario correspondente ao qr code usado
                                horario_atual = datetime.now()

                                print("\nQr correspondente as",confere_tabela) # Horario do qr code
                                print("Horario atual no CMM",horario_atual) # Horario atual

                                atrasado = 1
                                mudou = 1

                                for i in range (1,11): # Verifica 10 minutos a frente

                                    if (confere_tabela == horario_atual): # Hora qrcode = Hora atual

                                        acesso = 1
                                        consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
                                        atrasado = 0
                                        mudou = 0
                                        break

                                    horario_atual = horario_atual + timedelta(minutes=1)

                                if atrasado == 1:

                                    for i in range(1, 11):  # Verifica 10 minutos pra traz

                                        if (confere_tabela == horario_atual):  # Hora qrcode = Hora atual

                                            acesso = 1
                                            consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
                                            mudou = 0
                                            break

                                        horario_atual = horario_atual - timedelta(minutes=1)

                                if mudou == 1 and fora_do_horario == 0:

                                    print("Este QRCode ja mudou")
                                    os.system("mpg123 /home/pi/mp3/212.mp3")

                                    fora_do_horario = 1


                                if liberado == "1":

                                    if (self.portao == "garagem_entrada"):

                                        print ("Acesso por qr code Entrada Garagem")
                                        os.system("mpg123 /home/pi/CMM/mp3/bemvindo_LagoSul.mp3")

                                        qr = self.banco.encontra("qr_utilizado","id",self.id_raiz)

                                        if qr == "1":

                                            print("Este QR Code já foi utilizado")
                                            os.system("mpg123 /home/pi/CMM/mp3/qr_utilizado.mp3")
                                            time.sleep(2)

                                        else:
                                        
                                            garagem_entrada()
                                            self.banco.insere("qr_utilizado","id",self.id_raiz) # tabela,coluna,valor

                                            if self.notifica == "1":
                                                print("Notificando Condfy, Cliente:", self.cliente, "ID:", self.id_raiz)

                                                self.avisa_condfy.qr_utilizado(self.cliente, self.id_raiz)

                                    if (self.portao == "garagem_saida"):

                                        print ("Saída por qr code Garagem")
                                        saindo = self.banco.encontra("qr_utilizado", "id", self.id_raiz)

                                        if saindo == "1": # QR ja utilizado, ja pode sair

                                            garagem_saida()

                                            print("Deletando da tabela qr utilizado...")
                                            self.banco.deleta("qr_utilizado", "id", self.id_raiz)
                                            print("Deletando da tabela qrcode...")
                                            self.banco.deleta("qrcode", "id", self.id_raiz)

                            if acesso == 0 and consta_no_banco == 1 and fora_do_horario == 0:

                                print("QR Code com data expirada")
                                os.system("mpg123 /home/pi/mp3/210.mp3")# Data Expirada

                        except Exception as e:
                            
                            print("Tipo de erro: " + str(e))
                        
                    if id_valido == 0:

                        print("QR Code não cadastrado")
                        os.system("mpg123 /home/pi/mp3/189.mp3") # QR Code não cadastrado

        except Exception as err:

            print("opa",err)

