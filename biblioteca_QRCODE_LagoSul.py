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
import signal
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
        
        def social():
            
            status = open("status_social.cmm","w") # Para não disparar o arrombamento
            status.write("1")
            status.close()

            print("Abrindo portão social")
            
            self.rele.pulso(self.out,2) # Pulso para abrir direto o portão sem intertravamento 
            
            os.system("mpg123 /home/pi/CMM/mp3/acesso_qr.mp3")

            self.evento.enviar("E","133","015") # Envia abertura
            
            time.sleep(2)
            
            print("Fechando portão social")
            
            self.evento.enviar("R","133","015") # Envia fechamento

            status = open("status_social.cmm","w") # Para não disparar o arrombamento
            status.write("0")
            status.close()
            
        def eclusa():

            status = open("status_eclusa.cmm","w") # Para não disparar o arrombamento
            status.write("1")
            status.close()        
        
            self.rele.pulso(self.out,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)

            print("Abrindo portão eclusa")

            os.system("mpg123 /home/pi/CMM/mp3/acesso_qr.mp3")
            
            self.evento.enviar("E","133","015") # Envia esso por QR Code           

            time.sleep(2)
            
            print("Fechando portão eclusa")
            
            self.evento.enviar("R","133","015") # Envia fechamento

            status = open("status_eclusa.cmm","w") # Para não disparar o arrombamento
            status.write("0")
            status.close()

        def garagem_entrada():

            status = open("status_garagem_entrada.cmm","w") # Para não disparar o arrombamento
            status.write("1")
            status.close()        
        
            self.rele.pulso(self.out,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)

            print("Abrindo portão Garagem Entrada")

            os.system("mpg123 /home/pi/CMM/mp3/acesso_qr.mp3")

            self.evento.enviar("E","133","030") # Envia abertura entrada por qrcode              

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
            
            self.evento.enviar("E","133","031") # Envia abertura saida por qrcode           

            time.sleep(2)
            
            print("Abrindo portão Garagem Saida")            

            status = open("status_garagem_saida.cmm","w") # Para não disparar o arrombamento
            status.write("0")
            status.close()
            

        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
        h = int(time.strftime("%H"))
        data = time.strftime('%d/%m/%y') 
        
        try:

            socket.setdefaulttimeout(99999999)

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.ip_qrcode, 5001) # PORTA PADRAO DO LEITOR DE QR CODE
            time.sleep(0.1)
            sock.connect(server_address)                
            

            print('\nConectado com Leitor QR CODE {} port {}'.format(*server_address),"\n")
                     
            
            consulta = 0
            id_valido = 0
            acesso = 0
            fora_do_horario = 0
            consta_no_banco = 0
            item = 0
            ja_encontrou = 0

            while(1):

                consulta = 0
                id_valido = 0
                acesso = 0
                fora_do_horario = 0
                consta_no_banco = 0
                item = 0
                ja_encontrou = 0


                hs = time.strftime("%H:%M:%S") # MANTEM ATUALIZADO O HORARIO DO REGISTRO DE LOG
                horario_atual = time.strftime("%H:%M")
                
                try: 

                    tamanho = 0

                    dados = sock.recv(128)
                    tamanho += len(dados)
                    
        ##            print ("Dados recebidos",dados,"tamanho",tamanho) # Dados lidos no cartão de QR Code

                    if (tamanho >= 16 or tamanho <8): # Se o QR Code lido não tiver exatamente o mesmo tamanho não consulta o banco de dados

                        consulta = 0
                        dados = 0

        ##            print ("colocou consulta = 0")

                    if (tamanho >= 8 and tamanho < 16): # Se tiver o tamanho exato, prossegue
                                        
                        dados = int(dados) # Elimina as '' e o \r
                        dados = str(dados)

                        print("Dados lidos pelo leitor " + dados)

                        dados = dados[3:] # elimina os 3 primeiros digitos da string dados

                        
                        print("Dados editados",dados)

                        dados = int(dados)

                        consulta = 1
                            
                        tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327, 618, 379, 739, 132, 205, 902, 335, 396, 407, 871, 867, 213, 982, 980, 252, 228, 881, 137, 138, 216, 825, 536, 681, 895, 921, 711, 375, 908, 429, 656, 304, 560, 988, 642, 965, 183, 629, 432, 360, 728, 801, 796, 716, 631, 495, 587, 917, 732, 275, 119, 558, 675, 672, 729, 612, 517, 962, 995, 668, 144, 513, 987, 109, 563, 177, 257, 975, 626, 575, 813, 377, 363, 484, 170, 284, 869, 726, 502, 841, 808, 219, 286, 670, 614]                         
                        tempo_validade = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600, 610, 620, 630, 640, 650, 660, 670, 680, 690, 700, 710, 720, 730, 740, 750, 760, 770, 780, 790, 800, 810, 820, 830, 840, 850, 860, 870, 880, 890, 900, 910, 920, 930, 940, 950, 960, 970, 980, 990, 1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1080, 1090, 1100, 1110, 1120, 1130, 1140, 1150, 1160, 1170, 1180, 1190, 1200, 1210, 1220, 1230, 1240, 1250, 1260, 1270, 1280, 1290, 1300, 1310, 1320, 1330, 1340, 1350, 1360, 1370, 1380, 1390, 1400, 1410, 1420, 1430, 1440]
         
                        if (1):

                            
                            for item in tabela:
                                     
                                id_raiz = int(dados / item)  # divide o valor lido no QR por cada numero da tabela e consulta no banco

                                self.id_raiz = id_raiz

                                # Dividiu o id recebido pelos dados da tabela "item" que resultou no id_raiz

        ##                        print("\n",id_raiz)
                                
                                try:  # Tenta conectar com o banco de dados

                                    signal.alarm(2)
                                    cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                                    cursor = cnx.cursor()
                                    signal.alarm(0)
                                      
                                except mysql.connector.Error as err:

                                    print("Opa, problema com o banco de dados",err)                                                                              
                                    print(err)

                                    arquivo = open("QR_Code.log", "a+") # Escreve o evento no registro de log
                                    arquivo.write("Data: " + data + " " + hs + " Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                                    arquivo.close()
                                                
                                    time.sleep(0.1)
                                       
                                
                                try:                    

                                    query = ("SELECT ID FROM qrcode WHERE ID = %s")%id_raiz # procura na coluna ID um código = ao id_raiz
                                    cursor.execute(query)

                                    for i in cursor: # Se o cursor encontrar o item especificado, prossegue...
                                                                                                        
                                        id_valido = 1 # Encontrou o ID raiz
                                        consulta = 1 # Habilita a consulta de data e horario
                                        ja_encontrou = 1 # Depois de encontrar encerra a consulta do ID raiz
                                        
                                                           
                                except Exception as e:
                                
                                    print("Tipo de erro: " + str(e))
                                    break
                                    
                                if ja_encontrou == 1:
                                    
                                    ja_encontrou = 0

                                    break
                        item = item
                                
                except Exception as e:

                    print("Não foi possivel ler os dados recebidos\n")
                    print("Tipo de erro: " + str(e))
                    
                if consulta == 0:

                    print("\nQR Code em formato invalido")
                    print("Texto",dados,"\n")
                     
                    os.system("mpg123 /home/pi/mp3/206.mp3")#  Formato de QR Code inválido

                    arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de log
                    arquivo.write("Data: " + data + " " + hs + " Evento: Tentativa de uso de QR Code invalido\n")
                    arquivo.close()
                        
                    texto_recebido = ("")

                    time.sleep(3)


                if consulta == 1 :

                    item = item

                    try:  # Tenta conectar com o banco de dados

                        signal.alarm(2)
                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()
                        signal.alarm(0)
                          
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

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write("Data: " + data + " " + hs + " Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                            arquivo.close()
                                        
                            time.sleep(0.1)
                                  
                            pass
                    

                    if id_valido == 1: # Se o cursor encontrou o ID correspondente prossegue...

                        hs = time.strftime("%H:%M:%S") # MANTEM ATUALIZADO O HORARIO DO REGISTRO DE LOG
                        horario_atual = time.strftime("%H:%M")

                        # print("Este ID consta no banco",id_raiz)

                        consta_no_banco = 1

                        try:                    

                            # Primeiro ve se a data ainda não expirou e se o ID ja está liberado o horario
         
                            query = ("SELECT * FROM qrcode WHERE data_final >= CURDATE() AND ID = %s")%id_raiz # Verifica só id e data
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

                                hora_i = str(hora_inicio)
                                hora_f = str(hora_final)
                                hs = str(hs)


                                h_i = (hora_i.split(":")[0])
                                m_i = (hora_i.split(":")[1])
                                h_f = (hora_f.split(":")[0])
                                m_f = (hora_f.split(":")[1])

                                hi = int(h_i )  # Hora inicial como um inteiro para comparar com a hora atual
                                mi = int(m_i)  # Minuto inicial como um inteiro para comparar com o minuto atual

                                hf = int(h_f )  # Hora final como um inteiro para comparar com a hora atual
                                mf = int(m_f)  # Minuto final como um inteiro para comparar com o minuto atual

                                h = hs.split(":")[0] # Hora e minutos atuais do sistema
                                m = hs.split(":")[1]
                                h = int(h)
                                m = int(m)

                                consta_no_banco = 1

                            # Calculos para verificar a compatibilidade do código dinamico com o horario

                                tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327, 618, 379, 739, 132, 205, 902, 335, 396, 407, 871, 867, 213, 982, 980, 252, 228, 881, 137, 138, 216, 825, 536, 681, 895, 921, 711, 375, 908, 429, 656, 304, 560, 988, 642, 965, 183, 629, 432, 360, 728, 801, 796, 716, 631, 495, 587, 917, 732, 275, 119, 558, 675, 672, 729, 612, 517, 962, 995, 668, 144, 513, 987, 109, 563, 177, 257, 975, 626, 575, 813, 377, 363, 484, 170, 284, 869, 726, 502, 841, 808, 219, 286, 670, 614]
                                tempo_validade = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600, 610, 620, 630, 640, 650, 660, 670, 680, 690, 700, 710, 720, 730, 740, 750, 760, 770, 780, 790, 800, 810, 820, 830, 840, 850, 860, 870, 880, 890, 900, 910, 920, 930, 940, 950, 960, 970, 980, 990, 1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1080, 1090, 1100, 1110, 1120, 1130, 1140, 1150, 1160, 1170, 1180, 1190, 1200, 1210, 1220, 1230, 1240, 1250, 1260, 1270, 1280, 1290, 1300, 1310, 1320, 1330, 1340, 1350, 1360, 1370, 1380, 1390, 1400, 1410, 1420, 1430, 1440]
                             
                                minutos_equivalentes = (tempo_validade[tabela.index(item)])-10 # minutos equivalentes a mesma posição em que foi encointrado o multiplicador valido
                                posicao_multiplicador = tabela.index(item)

                                print("Posição do multiplicador valido",tabela.index(item))
                                print("Minutos equivalente",minutos_equivalentes)

                                
                                confere_tabela = hora_inicio + timedelta(minutes = minutos_equivalentes) # Horario correspondente ao qr code usado

                                print("\nQr correspondente as",confere_tabela)

                                confere_tabela = str(confere_tabela)
                                confere_tabela_hora = int(confere_tabela.split(":")[0])
                                confere_tabela_minuto = int(confere_tabela.split(":")[1])
                                confere_tabela_segundos = 00

        ##                        print("Horario correspondente",confere_tabela_hora, confere_tabela_minuto, confere_tabela_segundos)
                                                                               
                                now = datetime.now()

                                horario_atual_hora = now.hour  # Estes valores são do tipo inteiro
                                horario_atual_minuto = now.minute
                                horario_atual_segundo = now.second

                                print("Horario atual no CMM ",hs)

                                if (hi > h): # se o horario inicial é menor do que a hora atual, ainda não foi liberado

                                    print("Ainda não liberado\n")

                                    os.system("mpg123 /home/pi/mp3/207.mp3")

                                    #acesso = 0
                                    fora_do_horario = 1
                                    consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final

                                # Aqui se compara o horario atual com o horario correspondente

                                if confere_tabela_hora == horario_atual_hora :

                                    ja_mudou = 0

                                    #print ("A hora correspondente ao QR code lido é igual a hora atual")

                                    for i in range(1,11):

                                        if confere_tabela_minuto == horario_atual_minuto:

##                                            print ("Qr Code dentro dos 10 minutos validos")

                                            ja_mudou = 1

                                            fora_do_horario = 0
                                                                                
                                            break
                                        
                                        horario_atual_minuto = horario_atual_minuto - 1 # Verifica se esta dentro dos 10 minutos atuais

                                    if ja_mudou == 0 and fora_do_horario == 0:

                                        print("Este QRCode ja mudou")
                                        
                                        os.system("mpg123 /home/pi/mp3/212.mp3")

                                        fora_do_horario = 1

                                        #time.sleep(1)
                                if confere_tabela_hora != horario_atual_hora and fora_do_horario == 0:
                                    
                                    os.system("mpg123 /home/pi/mp3/207.mp3")
                                    print("Fora do horario permitido")

                                    fora_do_horario = 1

                                                           
                                
                                if (hf < h): # se o horario final é menor que o horario atual já expirou

                                    print("Horario do QR Code já Expirou\n")

                                    os.system("mpg123 /home/pi/mp3/208.mp3")

                                    time.sleep(3)

                                    #acesso = 0
                                    consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final

                                if (hf > h and fora_do_horario == 0): # se o horario final for maior que o horario atual, QR Code ainda válido

                                    #print("Dentro do horario permitido\n")

    ##                                os.system("mpg123 /home/pi/mp3/188.mp3")

                                    
                                    arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de acesso de moradores
                                    arquivo.write("Data: " + data + " " + hs + " Evento: Acesso por QR Code " + nome + " Ap " + ap + " bloco " + bloco + "\n")
                                    arquivo.close()
                    
                                    acesso = 1
                                    consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
                                     
                                    
                                if (hf == h): # se a hora final for a mesma da hora atual, verifica os minutos

                                    if mf == 0:

                                        print("Expirou a alguns minutos\n")

                                        os.system("mpg123 /home/pi/mp3/211.mp3")

                                        time.sleep(3)

                                        #acesso = 0
                                        consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final

                                    if (mf != 0 and mf >= m): # se minutos finais forem menores do que minutos atuais, ainda válido

                                        print("Dentro do horario, faltando",mf - m, "minutos")

    ##                                    os.system("mpg123 /home/pi/mp3/188.mp3") # Acesso por QR Code
                                        

                                        arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de acesso de moradores
                                        arquivo.write("Data: " + data + " " + hs + " Evento: Acesso por QR Code " + nome + " Ap " + ap + " bloco " + bloco + "\n")
                                        arquivo.close()
                        
                                        acesso = 1
                                        consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
                                                                      

                                    if (mf != 0 and mf <= m):
                                
                                         print("Expirou\n")

                                         os.system("mpg123 /home/pi/mp3/208.mp3") # Expirou
                                         

                                         time.sleep(3)

                                         #acesso = 0
                                         consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
                                         

                            if acesso == 1: #Verifica o dia da semana que esta autorizado

                                dia = time.strftime("%A")
##                                print ("Hoje é",dia)

                                liberado = "0"

                                b = str(dias_semana)

##                                print("b = ",b)

                                seg = b[0]
                                ter = b[1]
                                qua = b[2]
                                qui = b[3]
                                sex = b[4]
                                sab = b[5]
                                dom = b[6]

                                if dia == "Monday":
                                        
                                    if seg == "1":        
                                        liberado = "1"
                                        
                                    else:        
                                        print("QR Côldi não autorizado as segundas-feiras")
                                        liberado = "0"
                                            

                                if dia == "Tuesday":
                                    
                                    if ter == "1":        
                                        liberado = "1"
                                        
                                    else:        
                                        print("QR Côldi não autorizado as terças-feiras")
                                        liberado = "0" 

                                if dia == "Wednesday":
                                        
                                    if qua == "1":        
                                        liberado = "1"
                                        
                                    else:        
                                        print("QR Côldi não autorizado as quartas-feiras")
                                        liberado = "0"

                                if dia == "Thursday":
                                        
                                    if qui == "1":        
                                        liberado = "1"
                                        
                                    else:        
                                        print("QR Côldi não autorizado as quintas-feiras")
                                        liberado = "0"                                            

                                if dia == "Friday":
                                    
                                    if sex == "1":        
                                        liberado = "1"
                                        
                                    else:        
                                        print("QR Côldi não autorizado as sextas-feiras")
                                        liberado = "0"                                                
                                                        
                                        
                                if dia == "Saturday":
                                    
                                    if sab == "1":        
                                        liberado = "1"
                                        
                                    else:        
                                        print("QR Côldi não autorizado aos sábados")
                                        liberado = "0"
                                        

                                if dia == "Sunday":
                                        
                                    if dom == "1":        
                                        liberado = "1"
                                        
                                    else:
                                        
                                        print("QR Côldi não autorizado aos domingos")
                                        liberado = "0"
                                       

                                if liberado == "1":

                                    if self.notifica == "1":

                                        print("Notificando Condfy, Cliente:",self.cliente,"ID:",self.id_raiz)
                                        
                                        self.avisa_condfy.qr_utilizado(self.cliente,self.id_raiz)
                                    
                                    if (self.portao == "social"):

                                        print ("Acesso por qr code Portão Social Externo")
                                        social()

                                        self.banco.insere("qr_utilizado","id",self.id_raiz) # tabela,coluna,valor
                                        
                                    if (self.portao == "eclusa"):

                                        print ("Acesso por qr code Portão Social Interno")
                                        eclusa()

                                        self.banco.insere("qr_utilizado","id",self.id_raiz) # tabela,coluna,valor
##                                       

                                    if (self.portao == "garagem_entrada"):

                                        print ("Acesso por qr code Entrada Garagem 1 ")

                                        os.system("mpg123 /home/pi/CMM/mp3/bemvindo_LagoSul.mp3")

                                        qr = self.banco.encontra("qr_utilizado","id",self.id_raiz)
##                                       
                                        
                                        if qr == "1":

                                            print("Este QR Code já foi utilizado")

                                            os.system("mpg123 /home/pi/CMM/mp3/qr_utilizado.mp3")

                                            time.sleep(2)

                                        else:
                                        
                                            garagem_entrada()
                                           
                                            self.banco.insere("qr_utilizado","id",self.id_raiz) # tabela,coluna,valor
                                        
                                    if (self.portao == "garagem_saida"):

                                        print ("Saída por qr code Garagem 1")
                                        garagem_saida()                                    


##
                            if acesso == 0 and consta_no_banco == 1 and fora_do_horario == 0:

                                print("QR Code com data expirada")

                                os.system("mpg123 /home/pi/mp3/210.mp3")# Data Expirada
                                print("data expirada")

                                consulta = 1


                            # Aqui será necessário verificar se ja passou do horario final e avisar
                        
                        except Exception as e:
                            
                            print("Tipo de erro: " + str(e))

                        
                    if id_valido == 0:

                        print("QR Code não cadastrado")

                        try:

                            os.system("mpg123 /home/pi/mp3/189.mp3") # QR Code não cadastrado

                        except Exception as err:

                            print(err)

                    fora_do_horario = 0

        except Exception as err:

            print("opa",err)

# Para chamar a classe usar:

##import biblioteca_QRCODE_LagoSul as qr
##import threading
##import sys
##
##
##
##qr1_garagem = qr.Qrcode("172.20.9.8","0054",4,"garagem_entrada","1") # IP,CLIENTE,RELE,PORTAO,NOTIFICA CONDFY
### Ex. qr2_garagem = qr.Qrcode("172.20.9.8","0054",4,"garagem_saida","0")
###     qr_social = qr.Qrcode("172.20.9.8","0054",1,"social","1")
###     qr_eclusa = qr.Qrcode("172.20.9.8","0054",2,"eclusa","0")
##
##def thread_qrcode_garagem(): # Programa que mantem a conexão com o QR Code
##
##    print("\nPrograma QR Code em execução\n")
##
##    qr1_garagem.start()
##
##qr_garagem1 = threading.Thread(target=thread_qrcode_garagem)
##qr_garagem1.start()


        
