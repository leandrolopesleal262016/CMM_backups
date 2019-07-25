#/usr/bin/env pyhon3

from gtts import gTTS  # importamos o modúlo gTTS
import pygame
import time
import datetime
from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import smbus  # para funcionamento dos módulos com interface I2C 
import spidev
import os     # Executa comandos do sistema operacional Ex.: os.system('sudo reboot now'))
import serial # Para comunicação serial com arduino
import mysql.connector # faz a comunicação com o mysql no python 3.6
import socket
import threading # Modulo superior Para executar as threads
import _thread as thread # Modulo basico para executar as threads
import signal # Bibloteca para uso do time out
import sys
import smtplib  # Permite enviar emails
import json
from urllib import request #para efetuar a requisicao da API openweather


def timeout(signum, frame):

    #raise Exception ("Excedeu o tempo esperado!\n")
    print ("Excedeu o tempo esperado")
    return

host = '172.20.1.5'  # Host servidor  Moni
port = 4010          # Porta máquina receptora testes


host_servidor = '0.0.0.0'  # Host servidor SEA (PHP e moni como clientes)
port_servidor = 5510           # Servidor para que os clientes acessem o CLP SEA (SEA Software)

port_gerenciador = 5511

port_reset = 5512

mutex = thread.allocate_lock() # trava a thread para ser executada sózinha

GPIO.setwarnings(False) # desabilita mensagens de aviso

GPIO.setmode(GPIO.BCM) # Modo de endereço dos pinos BCM

ser = serial.Serial("/dev/ttyS0", 9600) #Configura a serial e a velocidade de transmissao

#valor_recebido = ser.readline()

spi =spidev.SpiDev() # Parametros da configuração da comunicação SPI (Entrada Portas Analógcas)
spi.open(0,0)
spi.max_speed_hz=1000000

pygame.init() # Inicia o pygame para uso do módulo de voz

bus = smbus.SMBus(1) # Parametros de configuração do módulo MCP23017 - SAIDA DOS RELÊS via I2C
MCP23017 = 0X20 # Endereço do módulo de saidas dos reles (A0 - A2)
MCP3008 = 0
bus.write_byte_data(MCP23017,0x00,0x00) #defina todo GPA como saida 0x00 
bus.write_byte_data(MCP23017,0x01,0x00) #defina todo GPB como saida 0x01 

# Define os pinos que serão entradas:

GPIO.setup(17,GPIO.IN)#GPIO0
GPIO.setup(18,GPIO.IN)#GPIO1
GPIO.setup(27,GPIO.IN)#GPIO2 
GPIO.setup(22,GPIO.IN)#GPIO3
GPIO.setup(23,GPIO.IN)#gpio4
GPIO.setup(24,GPIO.IN)#GPIO5
GPIO.setup(25,GPIO.IN)#GPIO6
GPIO.setup(4,GPIO.IN) #GPIO7 (in 8)


saidaA = 0b00000000
saidaB = 0b00000000

bus.write_byte_data(MCP23017,0x015,0) # Zera saidas do port B 
bus.write_byte_data(MCP23017,0x014,0) # Coloca todas as saidas do PORT A em 0

saidaB = saidaB + 0b00001000 # liga LED VERMELHO saida GPB3
bus.write_byte_data(MCP23017,0x015,saidaB)

signal.signal(signal.SIGALRM, timeout)

##try:  # Conecta com o servidor Moni e envia o reconhecimento "oi" ##################################
##  
##  signal.alarm(2)
##  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##  s.connect ((host,port))
##
##  command = ("oi")
##  s.send(str.encode(command))
##  reply = s.recv(1024)
##  print(reply.decode('utf-8'))
##  print("Criada conexão TCP IP com:",host,"Port:",port)
##  signal.alarm(0)
##  
##except Exception as e:
##    
##  print("Não conseguiu estabelecer conexão TCP/IP")
##  print(e)
##  
##  s.close()

#############################################  Clima  #########################################

def clima():

    
    h = int(time.strftime('%H')) # Somente a hora para uso na rotina do GTTS p/ identificar o periodo (manhã,tarde,noite)

    if (h<12):
      periodo = "Bom dia!"

    if (h>12 and h<18):
      periodo = "Boa tarde!"

        		
    if (h>=18 and h<=23):
      periodo = "Boa noite!"
    
    try:

        data = request.urlopen("http://api.openweathermap.org/data/2.5/weather?q=Bauru,BR&lang=pt&units=metric&APPID=dd7227b5df6988b8ba34bffd5b6e3450")
        html = data.read()
           
        html = html.decode('utf-8') # Evita erros de acento nos dados recebidos da API
        html = html.replace("b'","")
        html = html.replace("'","")
    
    except Exception as err:

        print("Não obteve retorno da API",err)

    try:

        weathe = json.loads(html)

    except Exception as err:

        print("Erro em converter para JSON",err)

    try:

        
        temperatura = (weathe['main']['temp'])
        temperatura = round(temperatura)
        temperatura = str(temperatura)

        nebulosidade = str(weathe['clouds']['all'])

        umidade = str(weathe['main']['humidity'])

        tempo = weathe['weather']
        tempo = tempo[0]
        tempo = tempo['description']

    except Exception as err:

        print("Erro na obtenção dos dados do dicionario",err)

    feed_back_clima = str(periodo + ", hoje em bauru," + tempo + ",e " + temperatura + " graus")

    narrador(feed_back_clima)


############################################### Thread servidor GERENCIADOR CMM #########################

def servidor_gerenciador():

    time.sleep(1)

    deletar = 0
    cadastrar = 0

    print("Ouvindo Gerenciador na porta",port_gerenciador)
    
    while(1):

        hs = time.strftime("%H:%M:%S") # MANTEM ATUALIZADO O HORARIO DO REGISTRO DE LOG
        
              
        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            
            try:
                s.bind((host_servidor, port_gerenciador))
            except socket.error as msg:
                print (msg)
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


##                    print("dados recebidos",data)

                    comando = (data.split("&")[0])
                    print("Comando", comando)

                    corpo = (data.split("&")[1])
                    print("Corpo",corpo)
                    

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
                            
                                arquivo = open("qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                                arquivo.write(" Evento: Deletado QR Code " + "ID" + ID + hs + "\n")
                                arquivo.close()

                                break

                        break
                        
                    if comando == "cadastrar_qr":

                        try:

                            print("\nReconheceu cadastrar")
                           
                            dados = data.replace("cadastrar_qr&","")
                            dados = dados.replace("'",'"')
                            
##                            print("Dados convertidos: ", dados)

                        except Exception as err:

                            print("Erro ao formatar os dados para converter em json", err)

                    
                #########  Faz o cadastro dos dados recebidos no banco do CMM #######
                        try:
                            
                            dados_json = json.loads(dados)  # Tranforma a string para formato json (dicionario)
                               
                            ID = str(dados_json["ID"])
                            nome = str(dados_json["nome"])
                            ap = str(dados_json["apartamento"])
                            bloco = str(dados_json["bloco"])
                            cond = str(dados_json["condominio"])
                            di = str(dados_json["data_inicio"])
                            df = str(dados_json["data_final"])
                            hi = str(dados_json["hora_inicio"])
                            hf = str(dados_json["hora_final"])
                            ds = str(dados_json["dias_semana"])

                        except Exception as err:

                            print("Erro na conversao json")

                                           
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

                            arquivo = open("qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
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


#################################################### LEITOR QR CODE  ##################################################################

def qr_code():
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_address = ('172.20.2.134', 5001) # Endereço do QR Code maquete
    
    time.sleep(0.1)
    
    print('Leitor QR CODE {} port {}'.format(*server_address),"\n")
    sock.connect(server_address)

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

##                print ("colocou consulta = 0")

            if (tamanho >= 8 and tamanho < 16): # Se tiver o tamanho exato, prossegue
                                
                dados = int(dados) # Elimina as '' e o \r
                dados = str(dados)

                dados = dados[3:] # elimina os 3 primeiros digitos da string dados

                
                print("Dados editados",dados,type(dados))

                dados = int(dados)

                consulta = 1
                    
                
                tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327]
                         
                tempo_validade = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600]

                if (1):

                    
                    for item in tabela:
                             
                        id_raiz = int(dados / item)  # divide o valor lido no QR por cada numero da tabela e consulta no banco

                        # Dividiu o id recebido pelos dados da tabela "item" que resultou no id_raiz

                        #print("\n",id_raiz)
                        
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
                        
                        try:                    

                            query = ("SELECT ID FROM qrcode WHERE ID = %s")%id_raiz # procura na coluna ID um código = ao id_raiz
                            cursor.execute(query)

                            for i in cursor: # Se o cursor encontrar o item especificado, prossegue...
                                                                                                
                                id_valido = 1 # Encontrou o ID raiz
                                consulta = 1 # Habilita a consulta de data e horario
                                ja_encontrou = 1 # Depois de encontrar encerra a consulta do ID raiz
                                
                                                   
                        except Exception as e:
                        
                            print("Tipo de erro: " + str(e))
                            
                        if ja_encontrou == 1:
                            
                            ja_encontrou = 0

                            break
                item = item
                        
        except Exception as e:

            print("Não foi possivel ler os dados recebidos ")

            print("Tipo de erro: " + str(e))
            
        if consulta == 0:

            print("\nQR Code em formato invalido")
            print("Texto",dados,"\n")

            pygame.mixer.music.load('mp3/206.mp3') # Formato de QR Code inválido
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

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

                        tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327]
                        tempo_validade = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600]

                        #print("Aqui o item vale",item)
                    
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

                            pygame.mixer.music.load('mp3/207.mp3') # Fora do horario
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)

                            #acesso = 0
                            fora_do_horario = 1
                            consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final

                        # Aqui se compara o horario atual com o horario correspondente

                        if confere_tabela_hora == horario_atual_hora :

                            ja_mudou = 0

                            #print ("A hora correspondente ao QR code lido é igual a hora atual")

                            for i in range(1,11):

                                if confere_tabela_minuto == horario_atual_minuto:

                                    print ("Qr Code dentro dos 10 minutos validos")

                                    ja_mudou = 1

                                    fora_do_horario = 0
                                                                        
                                    break
                                
                                horario_atual_minuto = horario_atual_minuto - 1 # Verifica se esta dentro dos 10 minutos atuais

                            if ja_mudou == 0 and fora_do_horario == 0:

                                print("Este QRCode ja mudou")

                                pygame.mixer.music.load('mp3/212.mp3') # Este QRCode ja mudou 
                                pygame.mixer.music.play()
                                while pygame.mixer.music.get_busy():
                                    time.sleep(0.1)

                                fora_do_horario = 1

                                #time.sleep(1)
                        if confere_tabela_hora != horario_atual_hora and fora_do_horario == 0:

                            pygame.mixer.music.load('mp3/212.mp3') # Este QRCode ja mudou 
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)

                            fora_do_horario = 1

                                                   
                        
                        if (hf < h): # se o horario final é menor que o horario atual já expirou

                            print("Horario do QR Code já Expirou\n")

                            pygame.mixer.music.load('mp3/208.mp3') # Expirou
                            pygame.mixer.music.play()
                            while pygame.mixer.music.get_busy():
                                time.sleep(0.1)

                            time.sleep(3)

                            #acesso = 0
                            consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final

                        if (hf > h and fora_do_horario == 0): # se o horario final for maior que o horario atual, QR Code ainda válido

                            #print("Dentro do horario permitido\n")

                            pygame.mixer.music.load('mp3/188.mp3') # Acesso por QR Code
                            pygame.mixer.music.play()

                            
                            arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de acesso de moradores
                            arquivo.write("Data: " + data + " " + hs + " Evento: Acesso por QR Code " + nome + " Ap " + ap + " bloco " + bloco + "\n")
                            arquivo.close()
            
                            acesso = 1
                            consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
                             
                            
                        if (hf == h): # se a hora final for a mesma da hora atual, verifica os minutos

                            if mf == 0:

                                print("Expirou a alguns minutos\n")

                                pygame.mixer.music.load('mp3/211.mp3') # Expirou
                                pygame.mixer.music.play()
                                while pygame.mixer.music.get_busy():
                                    time.sleep(0.1)

                                time.sleep(3)

                                #acesso = 0
                                consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final

                            if (mf != 0 and mf >= m): # se minutos finais forem menores do que minutos atuais, ainda válido

                                print("Dentro do horario, faltando",mf - m, "minutos")

                                pygame.mixer.music.load('mp3/188.mp3') # Acesso por QR Code
                                pygame.mixer.music.play()

                                arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de acesso de moradores
                                arquivo.write("Data: " + data + " " + hs + " Evento: Acesso por QR Code " + nome + " Ap " + ap + " bloco " + bloco + "\n")
                                arquivo.close()
                
                                acesso = 1
                                consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
                                                              

                            if (mf != 0 and mf <= m):
                        
                                 print("Expirou\n")

                                 pygame.mixer.music.load('mp3/208.mp3') # Expirou
                                 pygame.mixer.music.play()
                                 while pygame.mixer.music.get_busy():
                                    time.sleep(0.1)

                                 time.sleep(3)

                                 #acesso = 0
                                 consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
                                 

                    if acesso == 1:

                        intertravamento(saidaA,saidaB,hs,data,"QR",nome)

                    if acesso == 0 and consta_no_banco == 1 and fora_do_horario == 0:

                        print("QR Code com data expirada")

                        pygame.mixer.music.load('mp3/210.mp3') # Data Expirada
                        pygame.mixer.music.play()
                        while pygame.mixer.music.get_busy():
                            time.sleep(0.1)

                        consulta = 1


                    # Aqui será necessário verificar se ja passou do horario final e avisar
                
                except Exception as e:
                    
                    print("Tipo de erro: " + str(e))

                
            if id_valido == 0:

                print("QR Code não cadastrado")

                pygame.mixer.music.load('mp3/189.mp3') # Não cadastrado
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

            
            fora_do_horario = 0



###################################################### LEITOR QR CODE  ##################################################################
##
##def qr_code():
##    
##    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##
##    server_address = ('172.20.2.134', 5001) # Endereço do QR Code 
##    
##    time.sleep(0.1)
##    
##    print('Leitor QR CODE {} port {}'.format(*server_address),"\n")
##    sock.connect(server_address)
##
##    consulta = 0
##    id_valido = 0
##    acesso = 0
##    fora_do_horario = 0
##    consta_no_banco = 0
##    item = 0
##    ja_encontrou = 0
##
##    while(1):
##
##        consulta = 0
##        id_valido = 0
##        acesso = 0
##        fora_do_horario = 0
##        consta_no_banco = 0
##        item = 0
##        ja_encontrou = 0
##
##
##        hs = time.strftime("%H:%M:%S") # MANTEM ATUALIZADO O HORARIO DO REGISTRO DE LOG
##        horario_atual = time.strftime("%H:%M")
##        
##        try: 
##
##            tamanho = 0
##
##            dados = sock.recv(128)
##            tamanho += len(dados)
##            
##            print ("Dados recebidos",dados,"tamanho",tamanho) # Dados lidos no cartão de QR Code
##
##            if (tamanho >= 16 or tamanho <8): # Se o QR Code lido não tiver exatamente o mesmo tamanho não consulta o banco de dados
##
##                consulta = 0
##                dados = 0
##
####                print ("colocou consulta = 0")
##
##            if (tamanho >= 8 and tamanho < 16): # Se tiver o tamanho exato, prossegue
##                                
##                dados = int(dados) # Elimina as '' e o \r
##                dados = str(dados)
##
##                dados = dados[3:] # elimina os 3 primeiros digitos
##
##                                
##                print("Dados editados",d)
##
##                dados = int(dados)
##
##                consulta = 1
##                    
##                
##                tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327]
##                tempo_validade = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600]
##
##                if (1):
##
##                    
##                    for item in tabela:
##                             
##                        id_raiz = int(dados / item)  # divide o valor lido no QR por cada numero da tabela e consulta no banco
##
##                        # Dividiu o id recebido pelos dados da tabela "item" que resultou no id_raiz
##
##                        try:  # Tenta conectar com o banco de dados
##
##                            signal.alarm(2)
##                            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
##                            cursor = cnx.cursor()
##                            signal.alarm(0)
##                              
##                        except mysql.connector.Error as err:
##                                
##                            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
##                      
##                                print("Alguma coisa esta errada com o nome de usuario ou a senha!")
##
##                                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
##                                arquivo.write("Data: " + data + " " + hs + " Evento: Banco de Dados: Usuario ou senha invalidos\n")
##                                arquivo.close()
##
##                            elif err.errno == errorcode.ER_BAD_DB_ERROR:
##                      
##                                print("Esta base de dados não existe!")
##
##                                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
##                                arquivo.write("Data: " + data + " " + hs + " Evento: Banco de Dados: A base de dados não existe\n")
##                                arquivo.close()
##
##                            else:
##                                              
##                                print(err)
##
##                                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
##                                arquivo.write("Data: " + data + " " + hs + " Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
##                                arquivo.close()
##                                            
##                                time.sleep(0.1)
##                                      
##                                pass
##                        
##                        try:                    
##
##                            query = ("SELECT ID FROM qrcode WHERE ID = %s")%id_raiz # procura na coluna ID um código = ao id_raiz
##                            cursor.execute(query)
##
##                            for i in cursor: # Se o cursor encontrar o item especificado, prossegue...
##                                                                                                
##                                id_valido = 1 # Encontrou o ID raiz
##                                consulta = 1 # Habilita a consulta de data e horario
##                                ja_encontrou = 1 # Depois de encontrar encerra a consulta do ID raiz
##                                
##                                                   
##                        except Exception as e:
##                        
##                            print("Tipo de erro: " + str(e))
##                            
##                        if ja_encontrou == 1:
##                            
##                            ja_encontrou = 0
##
##                            break
##                item = item
##                        
##        except Exception as e:
##
##            print("Não foi possivel ler os dados recebidos ")
##
##            print("Tipo de erro: " + str(e))
##            
##        if consulta == 0:
##
##            print("\nQR Code em formato invalido")
##            print("Texto",dados,"\n")
##
##            pygame.mixer.music.load('mp3/206.mp3') # Formato de QR Code inválido
##            pygame.mixer.music.play()
##            while pygame.mixer.music.get_busy():
##                time.sleep(0.1)
##
##            arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de log
##            arquivo.write("Data: " + data + " " + hs + " Evento: Tentativa de uso de QR Code invalido\n")
##            arquivo.close()
##                
##            texto_recebido = ("")
##
##            time.sleep(3)
##
##
##        if consulta == 1 :
##
##            item = item
##
##            try:  # Tenta conectar com o banco de dados
##
##                signal.alarm(2)
##                cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
##                cursor = cnx.cursor()
##                signal.alarm(0)
##                  
##            except mysql.connector.Error as err:
##                    
##                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
##          
##                    print("Alguma coisa esta errada com o nome de usuario ou a senha!")
##
##                    arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
##                    arquivo.write("Data: " + data + " " + hs + " Evento: Banco de Dados: Usuario ou senha invalidos\n")
##                    arquivo.close()
##
##                elif err.errno == errorcode.ER_BAD_DB_ERROR:
##          
##                    print("Esta base de dados não existe!")
##
##                    arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
##                    arquivo.write("Data: " + data + " " + hs + " Evento: Banco de Dados: A base de dados não existe\n")
##                    arquivo.close()
##
##                else:
##                                  
##                    print(err)
##
##                    arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
##                    arquivo.write("Data: " + data + " " + hs + " Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
##                    arquivo.close()
##                                
##                    time.sleep(0.1)
##                          
##                    pass
##            
##
##            if id_valido == 1: # Se o cursor encontrou o ID correspondente prossegue...
##
##                # print("Este ID consta no banco",id_raiz)
##
##                consta_no_banco = 1
##
##                try:                    
##
##                    # Primeiro ve se a data ainda não expirou e se o ID ja está liberado o horario
## 
##                    query = ("SELECT * FROM qrcode WHERE data_final >= CURDATE() AND ID = %s")%id_raiz # Verifica só id e data
##                    cursor.execute(query)
##                          
##                    for i in cursor: # Se encontrar o item especificado, divide as informações e salva nas variaveis
##
##                                             
##                        ID = i[0]
##                        nome = i[1]
##                        ap = i[2]
##                        bloco = i[3]
##                        cond = i[4]
##                        hora_inicio = i[5]
##                        hora_final = i[6]
##                        data_inicio = i[7]
##                        data_final = i[8]
##                        dias_semana = i[9]
##
##                        print("\nID",ID,"\nNome",nome,"valido de",data_inicio.strftime('%d/%m/%Y'),"até",data_final.strftime('%d/%m/%Y'),"das",hora_inicio,"as",hora_final,"hs","dias da semana",dias_semana)
##
##                        hora_i = str(hora_inicio)
##                        hora_f = str(hora_final)
##                        hs = str(hs)
##
##
##                        h_i = (hora_i.split(":")[0])
##                        m_i = (hora_i.split(":")[1])
##                        h_f = (hora_f.split(":")[0])
##                        m_f = (hora_f.split(":")[1])
##
##                        hi = int(h_i )  # Hora inicial como um inteiro para comparar com a hora atual
##                        mi = int(m_i)  # Minuto inicial como um inteiro para comparar com o minuto atual
##
##                        hf = int(h_f )  # Hora final como um inteiro para comparar com a hora atual
##                        mf = int(m_f)  # Minuto final como um inteiro para comparar com o minuto atual
##
##                        h = hs.split(":")[0] # Hora e minutos atuais do sistema
##                        m = hs.split(":")[1]
##                        h = int(h)
##                        m = int(m)
##
##                        consta_no_banco = 1
##
##                    # Calculos para verificar a compatibilidade do código dinamico com o horario
##
##                        tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327]
##                        tempo_validade = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600]
##
##                        #print("Aqui o item vale",item)
##                    
##                        minutos_equivalentes = tempo_validade[tabela.index(item)] # minutos equivalentes a mesma posição em que foi encointrado o multiplicador valido
##                        posicao_multiplicador = tabela.index(item)
##
####                        print("Posição do multiplicador valido",tabela.index(item))
####                        print("Minutos equivalente",minutos_equivalentes)
##
##                        
##                        confere_tabela = hora_inicio + timedelta(minutes = minutos_equivalentes) # Horario correspondente ao qr code usado
##
##                        print("\nQr correspondente as",confere_tabela)
##
##                        confere_tabela = str(confere_tabela)
##                        confere_tabela_hora = int(confere_tabela.split(":")[0])
##                        confere_tabela_minuto = int(confere_tabela.split(":")[1])
##                        confere_tabela_segundos = 00
##
####                        print("Horario correspondente",confere_tabela_hora, confere_tabela_minuto, confere_tabela_segundos)
##                                                                       
##                        now = datetime.now()
##
##                        horario_atual_hora = now.hour  # Estes valores são do tipo inteiro
##                        horario_atual_minuto = now.minute
##                        horario_atual_segundo = now.second
##
##                        print("Horario atual no CMM ",hs)
##
##                        if (hi > h): # se o horario inicial é menor do que a hora atual, ainda não foi liberado
##
##                            print("Ainda não liberado\n")
##
##                            pygame.mixer.music.load('mp3/207.mp3') # Fora do horario
##                            pygame.mixer.music.play()
##                            while pygame.mixer.music.get_busy():
##                                time.sleep(0.1)
##
##                            #acesso = 0
##                            fora_do_horario = 1
##                            consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
##
##                        # Aqui se compara o horario atual com o horario correspondente
##
##                        if confere_tabela_hora == horario_atual_hora :
##
##                            ja_mudou = 0
##
##                            #print ("A hora correspondente ao QR code lido é igual a hora atual")
##
##                            for i in range(1,11):
##
##                                if confere_tabela_minuto == horario_atual_minuto:
##
##                                    print ("Qr Code dentro dos 10 minutos validos")
##
##                                    ja_mudou = 1
##
##                                    fora_do_horario = 0
##                                                                        
##                                    break
##                                
##                                horario_atual_minuto = horario_atual_minuto - 1 # Verifica se esta dentro dos 10 minutos atuais
##
##                            if ja_mudou == 0 and fora_do_horario == 0:
##
##                                print("Este QRCode ja mudou")
##
##                                pygame.mixer.music.load('mp3/212.mp3') # Este QRCode ja mudou 
##                                pygame.mixer.music.play()
##                                while pygame.mixer.music.get_busy():
##                                    time.sleep(0.1)
##
##                                fora_do_horario = 1
##
##                                #time.sleep(1)
##                        if confere_tabela_hora != horario_atual_hora and fora_do_horario == 0:
##
##                            pygame.mixer.music.load('mp3/212.mp3') # Este QRCode ja mudou 
##                            pygame.mixer.music.play()
##                            while pygame.mixer.music.get_busy():
##                                time.sleep(0.1)
##
##                            fora_do_horario = 1
##
##                                                   
##                        
##                        if (hf < h): # se o horario final é menor que o horario atual já expirou
##
##                            print("Horario do QR Code já Expirou\n")
##
##                            pygame.mixer.music.load('mp3/208.mp3') # Expirou
##                            pygame.mixer.music.play()
##                            while pygame.mixer.music.get_busy():
##                                time.sleep(0.1)
##
##                            time.sleep(3)
##
##                            #acesso = 0
##                            consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
##
##                        if (hf > h and fora_do_horario == 0): # se o horario final for maior que o horario atual, QR Code ainda válido
##
##                            #print("Dentro do horario permitido\n")
##
##                            pygame.mixer.music.load('mp3/188.mp3') # Acesso por QR Code
##                            pygame.mixer.music.play()
##
##                            arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de acesso de moradores
##                            arquivo.write("Data: " + data + " " + hs + " Evento: Acesso por QR Code " + nome + " Ap " + ap + " bloco " + bloco + "\n")
##                            arquivo.close()
##            
##                            acesso = 1
##                            consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
##                             
##                            
##                        if (hf == h): # se a hora final for a mesma da hora atual, verifica os minutos
##
##                            if mf == 0:
##
##                                print("Expirou a alguns minutos\n")
##
##                                pygame.mixer.music.load('mp3/211.mp3') # Expirou
##                                pygame.mixer.music.play()
##                                while pygame.mixer.music.get_busy():
##                                    time.sleep(0.1)
##
##                                time.sleep(3)
##
##                                #acesso = 0
##                                consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
##
##                            if (mf != 0 and mf >= m): # se minutos finais forem menores do que minutos atuais, ainda válido
##
##                                print("Dentro do horario, faltando",mf - m, "minutos")
##
##                                pygame.mixer.music.load('mp3/188.mp3') # Acesso por QR Code
##                                pygame.mixer.music.play()
##
##                                arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de acesso de moradores
##                                arquivo.write("Data: " + data + " " + hs + " Evento: Acesso por QR Code " + nome + " Ap " + ap + " bloco " + bloco + "\n")
##                                arquivo.close()
##                
##                                acesso = 1
##                                consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
##                                                              
##
##                            if (mf != 0 and mf <= m):
##                        
##                                 print("Expirou\n")
##
##                                 pygame.mixer.music.load('mp3/208.mp3') # Expirou
##                                 pygame.mixer.music.play()
##                                 while pygame.mixer.music.get_busy():
##                                    time.sleep(0.1)
##
##                                 time.sleep(3)
##
##                                 #acesso = 0
##                                 consta_no_banco = 0  # zera a variavel para não narrar a mensagem no final
##                                 
##
##                    if acesso == 1:
##
##                        rele.pulsa(1,2)
##
##                    if acesso == 0 and consta_no_banco == 1 and fora_do_horario == 0:
##
##                        print("QR Code com data expirada")
##
##                        pygame.mixer.music.load('mp3/210.mp3') # Data Expirada
##                        pygame.mixer.music.play()
##                        while pygame.mixer.music.get_busy():
##                            time.sleep(0.1)
##
##                        consulta = 1
##
##
##                    # Aqui será necessário verificar se ja passou do horario final e avisar
##                
##                except Exception as e:
##                    
##                    print("Tipo de erro: " + str(e))
##
##                
##            if id_valido == 0:
##
##                print("QR Code não cadastrado")
##
##                pygame.mixer.music.load('mp3/189.mp3') # Não cadastrado
##                pygame.mixer.music.play()
##                while pygame.mixer.music.get_busy():
##                    time.sleep(0.1)
##
##            
##            fora_do_horario = 0



############################################### Thread servidor para RESET ##############################

def servidor_reset():

    time.sleep(1)

    print("Servidor:",host_servidor,"porta:",port_reset)
    
    host = '172.20.6.14'
    port = 5512

    
    while(1):
        
        #mutex.acquire()
      
        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            print ("Socket para reset criado!\n")
            try:
                s.bind((host, port))
            except socket.error as msg:
                print (msg)
            print ("Ligação do socket reset completa.\n")
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

                (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e eoutra em resto 
                

                if(comando == "SET 7"):

                    print ("Reiniciando o sistema...")

                    time.sleep(1)
                    
                    os.system('sudo reboot now')
                    
                                        
                conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
                
                                                                                                
                
                conn.close()
                
          
        s = setupServer()

        while True:
          
          print ("\nEscutando a porta RESET",port_reset, "\n")
          
          try:

              conn = setupConnection()
              dataTransfer(conn) #,saidaA,saidaB,hs)
                                         
                
          except:
            
              print("Encerrou conexão RESET")

############################################### Thread servidor p/ PHP e MONI #################################################################


def servidor_php(saidaA,saidaB,hs,data):
    
    host = '172.20.6.14'
    port = 5510

    time.sleep(1.5)

    print("Servidor:",host_servidor,"porta:",port_servidor)
    
    while(1):
        
        #mutex.acquire()
      
        def setupServer():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
            print ("Socket criado!\n")
            try:
                s.bind((host, port))
            except socket.error as msg:
                print (msg)
            print ("Ligação do socket completa.\n")
            return s

        def setupConnection():
            s.listen(5)
            conn, address = s.accept()
            print ("Conectado com: " + address[0] + ":" + str(address[1]), "\n")
            return conn


        def dataTransfer(conn):  # Loop de transferencia e recepção de dados
            
            while True:

                            
                data = conn.recv(1024)  # Recebe o dado
                data = data.decode('utf-8')
                print (data)
                dataMessage = data.split(' ',1)# Separa o comando do resto dos dados
                command = dataMessage[0]

                (comando,resto) = data.split("\r") # Divide os dados da variavel data e guarda uma parte em comando e eoutra em resto 
                

                if(comando == "SET 1"): 
                    print("reconheceu SET 1")
                    php = "AP01"
                    intertravamento(saidaA,saidaB,hs,data,php,"")

                if(comando == "SET 2"): 
                    print("reconheceu SET 2")
                    php = "AP02"
                    intertravamento(saidaA,saidaB,hs,data,php,"")

                if(comando == "SET 3"): 
                    print("reconheceu SET 3")
                    php = "AP03"
                    intertravamento(saidaA,saidaB,hs,data,php,"")

                if(comando == "SET 4"): 
                    print("reconheceu SET 4")
                    php = "AP04"
                    global vrg
                    vrg = 1
                    logica_garagem(saidaA)

                if(comando == "SET 5"):
                    
                    print("Iniciar apresentação")
                    
                    demo(saidaA)

                if(comando == "SET 6"):
                    
                    print("SET 6 ")

                    pygame.mixer.music.load('mp3/190.mp3') # Reiniciando os interfones
                    pygame.mixer.music.play()

                    
                    time.sleep(3)
                    

                if(comando == "SET 7"):
                    
                    print("SET 7 ")

                    pygame.mixer.music.load('mp3/191.mp3') # Reiniciando centrais dos portões
                    pygame.mixer.music.play()

                    
                    time.sleep(3)
                    

                if(comando == "SET 8"):
                    
                    print("SET 8")

                    pygame.mixer.music.load('mp3/192.mp3') # Reiniciando central de PABX
                    pygame.mixer.music.play()

                    
                    time.sleep(3)

                
                if(comando == "SET 9"):
                    
                    print("SET 9")
                    
                    pygame.mixer.music.load('mp3/193.mp3') # Acionamento Reset Auxiliar
                    pygame.mixer.music.play()
                    
                    
                    time.sleep(3)

                
                if(comando == "SET 10"):
                    
                    print("SET 10")

                    pygame.mixer.music.load('mp3/205.mp3') # Reiniciando CLP
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                    arquivo = open("/home/pi/log_cmm.txt", "a+") # Escreve o evento no registro de log
                    arquivo.write("Data: " + data + " " + hs + " Evento: Reiniciando CLP pelo aplicativo\n")
                    arquivo.close()

                    os.system('sudo reboot now')

                if(comando == "SET 11"):
                    
                    print("SET 11")

                    pygame.mixer.music.load('mp3/170.mp3') # Tecnicos a caminho
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                    
                    time.sleep(3)

                if(comando == "SET 12"):
                    
                    print("SET 12")

                    pygame.mixer.music.load('mp3/172.mp3') # Desculpe nos o inconveniente
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                   
                    time.sleep(3)

                if(comando == "SET 13"):
                    
                    print("SET 13")

                    pygame.mixer.music.load('mp3/171.mp3') # Atualizando o sistema
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                   
                    time.sleep(3)

                if(comando == "SET 14"):
                    
                    print("SET 14")

                    pygame.mixer.music.load('mp3/175.mp3') #Atenção afaste se do portão
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                    
                    time.sleep(3)

                if(comando == "SET 15"):
                    
                    print("SET 15")

                    pygame.mixer.music.load('mp3/173.mp3') # mensagem Estamos verificando o problema
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)


                    time.sleep(3)
                
                if(comando == "SET 16"): 
                    print("SET 16 sem função")
                    

                else:
                    print(comando)

                reply = "ok"                                
                conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
                                                                         
                
                conn.close()
                
          
        s = setupServer()

        while True:
          
          print ("\nEscutando a porta",port, "\n")   
          try:

              conn = setupConnection()
              dataTransfer(conn) #,saidaA,saidaB,hs)
              print("Oiee")
                           
                
          except:
            
              print("Encerrou conexão")
              
    


#################################################### LEITOR DO QR CODE  ##################################################################

##def qr_code(saidaA,saidaB):
##
##    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##
##    server_address = ('172.20.2.134', 5001) # Endereço do QR Code
##
##    time.sleep(0.1)
##
##    print('Leitor QR CODE {} port {}'.format(*server_address),"\n")
##    sock.connect(server_address)
##
##    consulta = 0
##    qr_invalido = 0
##
##    while(1):
##
##        try:
##
##            hs = time.strftime("%H:%M:%S") # MANTEM ATUALIZADO O HORARIO DO REGISTRO DE LOG
##
##            amount_received = 0
##
##            dados = sock.recv(128)
##            amount_received += len(dados)
##
##            texto_recebido = ('received {!r}'.format(dados))
##            print("Texto recebido",texto_recebido)
##
##            if texto_recebido != (b''):
##
##                qr = (texto_recebido.split ("'")[1])   # Limpa o "b" que aparece no inicio
##                code = (qr.split ("\r")[0])
##
##
##                n = (code.split ("das")[0])
##                nome = n.replace(" ","")
##                hor = (code.split("das")[1])
##                horario = (hor.split("dia")[0])
##                d = (hor.split("dia")[1])
##                dia = (d.split(" ")[1])
##
##                cond = (d.split("dia")[0])
##                condominio = (cond.split(" ")[2])
##
##                consulta = 1
##
##        except:
##
##            if consulta == 0:
##
##                print("QR Code em formato invalido")
##
##                pygame.mixer.music.load('mp3/206.mp3') # Formato de QR Code inválido
##                pygame.mixer.music.play()
##                while pygame.mixer.music.get_busy():
##                    time.sleep(0.1)
##
##                qr_invalido = 1
##                texto_recebido = (b'')
##
##                time.sleep(2)
##
##
##        if consulta == 1 :
##
##            try:  # Tenta conectar com o banco de dados 
##                signal.alarm(2)
##                cnx =mysql.connector.connect(user='leandro',database='CMM',password='5510',host='localhost')
##                cursor = cnx.cursor()
##                signal.alarm(0)
##
##            except mysql.connector.Error as err:
##
##                if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
##
##                    print("Alguma coisa esta errada com o nome de usuario ou a senha!")
##
##                    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
##                    arquivo.write("Data: ")
##                    arquivo.write(data)
##                    arquivo.write(" ")
##                    arquivo.write(hs)
##                    arquivo.write(" Evento: Erro no acesso ao banco de dados pelo QR Code (usuario ou senha invalidos)")
##                    arquivo.write("\n")
##                    arquivo.close()
##
##                elif err.errno == errorcode.ER_BAD_DB_ERROR:
##
##                    print("Esta base de dados não existe!")
##
##                    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
##                    arquivo.write("Data: ")
##                    arquivo.write(data)
##                    arquivo.write(" ")
##                    arquivo.write(hs)
##                    arquivo.write(" Evento: Erro acesso ao Banco pelo QR Code, a base de dados não existe")
##                    arquivo.write("\n")
##                    arquivo.close()
##
##                else:
##
##                    print(err)
##
##                    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
##                    arquivo.write("Data: ")
##                    arquivo.write(data)
##                    arquivo.write(" ")
##                    arquivo.write(hs)
##                    arquivo.write(" Evento: Erro acesso ao Banco pelo QR Code " + err)
##                    arquivo.write("\n")
##                    arquivo.close()
##
##                    time.sleep(0.1)
##
##                    pass
##
##
##            query = ("SELECT nome FROM qrcode") # Seleciona no Banco a tabela qrcode e a coluna nome
##            cursor.execute(query)
##
##            valido = 0
##            cont = 0
##
##            for (i) in cursor: # Para cada item da coluna nome faz a comparação
##
##                i = str(i)
##
##                it = (i.split ("(")[1])
##                ite = (it.split (",")[0])
##                m = (ite.split("'")[1])
##                item = m.replace(" ","") # Tira os espaços entre as letras para não errar na comparação
##
##                if (item == nome and cont == 0): # Compara se o codigo recebido pela serial é o mesmo lido da linha comparada
##
##                    print("Acesso de",item,data,"as",hs)
##
##                    arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de acesso de moradores
##                    arquivo.write("Evento: Acesso por QR Code " + nome + " " + data + " as " + hs)
##                    arquivo.write("\n")
##                    arquivo.close()
##
##                    valido = 1
##                    cont = 1
##
##                    
##            if (valido == 1):
##
##                pygame.mixer.music.load('mp3/188.mp3') # Acesso por QR Code
##                pygame.mixer.music.play()
##                
##                saidaA = saidaA + 0b00000001 # Abre portão social
##                bus.write_byte_data(MCP23017,0x014,saidaA) 
##                time.sleep(2)
##                saidaA = saidaA - 0b00000001 
##                bus.write_byte_data(MCP23017,0x014,saidaA)
##                time.sleep(2)
##                texto_recebido = (b'')
##
##            if (valido == 0):
##            
##                pygame.mixer.music.load('mp3/189.mp3') # QR Code não cadastrado
##                pygame.mixer.music.play()
##
##                print("Tentativa de uso QR Code não cadstrado",data,"as",hs)
##
##                arquivo = open("acesso_de_moradores.txt", "a+") # Escreve o evento no registro de acesso de moradores
##                arquivo.write("Evento: Tentativa de uso QR Code não cadstrado " + data + " as " + hs)
##                arquivo.write("\n")
##                arquivo.close()
##                time.sleep(2)
##                texto_recebido = (b'')
##                
##           
##        consulta = 0
            

        
########################################################################################################################################## 
   

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

hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
hora = time.strftime('%H:%M')
h = int(time.strftime('%H'))
dia_mes = time.strftime("%d")
y = time.strftime("%Y")
m = time.strftime("%m")
data = time.strftime('%d/%m/%y')

# Cria um arquivo de texto para registro dos eventos do sistema

try:  # caso já exista, escreva que o sistema foi reiniciado
  
  arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
  arquivo.write("Data: ")
  arquivo.write(data)
  arquivo.write(" ")
  arquivo.write(hs)
  arquivo.write(" Evento: O sistema foi reiniciado")
  arquivo.write("\n")
  arquivo.close()
        
except FileNotFoundError: # Caso não exista crie um arquivo com o nome log_sea.txt
        
  with open("log_sea.txt", "a+") as arquivo:

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

##    pygame.mixer.init(25500)  
    voz = gTTS(mensagem, lang="pt")  # guardamos o nosso texto na variavel voz
    voz.save("mensagem.mp3")  # salvamos com o comando save em mp3
    time.sleep(0.2)
    os.system("mpg123 mensagem.mp3")
    
##    pygame.mixer.music.load('mensagem.mp3')
##    pygame.mixer.music.play()
##    print ("Reproduzindo Texto no narrador")
##    while pygame.mixer.music.get_busy():
##       
##        time.sleep(0.1)
    print("terminou o narração")


def modo_manutencao(hs,data): # (Ainda em desenvolvimento...)

    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Sistema em modo de manutenção")
    arquivo.write("\n")
    arquivo.close()
    
    saidaA = saidaA + 0b00000001 #aciona rele 1 (abre portão social)
    bus.write_byte_data(MCP23017,0x014,saidaA)
    print ("Abrir portão social")
    texto_recebido

    # Abre fecha o portão e verifica se o portão fechou (ponto magnético)

    	
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


# Lógica de intertravamento dos portões sociais  
 
def intertravamento(saidaA,saidaB,hs,data,php,nome): # data,AP01):
        
         print("Entrou na rotina intertravamento")

         if(php == "QR"): # se recebeu requisição do qr code para abrir
             
             saidaA = saidaA + 0b00000001 #aciona rele 1 (abre portão social)
             bus.write_byte_data(MCP23017,0x014,saidaA)

             try:
                

                 h = int(time.strftime('%H'))

                 if (h<12):

                     periodo = "Bom dia!,"

                 if (h>=12 and h<18):

                     periodo = "Boa tarde!,"

                                    
                 if (h>=18 and h<=23):

                     periodo = "Boa noite!,"

                 narrador (periodo + nome) # Sauda e fala o nome

             except Exception as err:

                 print("Não conseguiu narrar o nome",err)

             time.sleep(2)

             saidaA = saidaA - 0b00000001 #desliga rele 1 (fecha portão social)
             bus.write_byte_data(MCP23017,0x014,saidaA)
                
             print ("Fechou portão social")
         
         if(GPIO.input(27) ==1 or php == "AP01"):  # Sinal do CTW Social
            
            if (pm_eclusa == 1): # Portão da Eclusa Fechado

              saidaA = saidaA + 0b00000001 #aciona rele 1 (abre portão social)
              bus.write_byte_data(MCP23017,0x014,saidaA)

              rele1 = 1
        
              print ("Abrir portão social")

              try:
                      
                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 189091E13300001")  # Envia abriu portão para a central de monitormento
                s.send(str.encode(command))

                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                signal.alarm(0)
                
              except:

                print("Não conseguiu estabelecer conexão TCP/IP")
                s.close()

              arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
              arquivo.write("Data: ")
              arquivo.write(data)
              arquivo.write(" ")
              arquivo.write(hs)
              arquivo.write(" Evento: Portão Social abriu")
              arquivo.write("\n")
              arquivo.close()
                
              pygame.mixer.music.load('mp3/045.mp3') # Abrindo portão social
              pygame.mixer.music.play()
              while pygame.mixer.music.get_busy():
                time.sleep(0.1)

              
              c = 100 # espera 10 segundos pra fechar ########################### TEMPO DE ESPERA PARA FECHAR PORTÃO SOCIAL
              
              while c > 0:

                
                if (GPIO.input(22) == 1):  # Botão da Eclusa pressionado?
                  
                  print("Espere o fechamento do primeiro portão")
                  
                  pygame.mixer.music.load('mp3/049.mp3') # Espere o fechamento do primeiro portão
                  pygame.mixer.music.play()
                  while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                else:
                  c = c - 1
                  time.sleep(0.1)
                            
              time.sleep(1)
                      
              
              if (GPIO.input(4) == 1 and rele1 == 1): # Reset Serviço

                print("Reset do modo de Serviço")

                try:

                  signal.alarm(2)
                  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                  s.connect ((host,port))

                  command = ("7000 189091RS0101000")  # Envia Reset do modo de Serviço para a central de monitormento
                  s.send(str.encode(command))
                  reply = s.recv(1024)
                  print(reply.decode('utf-8'))
                  signal.alarm(0)
                  
                except:

                  print("Não conseguiu enviar o evento Reset de Serviço")
                  s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Reset do modo de Serviço")
                arquivo.write("\n")
                arquivo.close()
				
                saidaA = saidaA - 0b00000001 #desliga rele 1 (fecha portão social)
                bus.write_byte_data(MCP23017,0x014,saidaA)
                
                print ("Fechou portão social")

                try:

                  signal.alarm(2)
                  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                  s.connect ((host,port))

                  command = ("7000 189091R13300001")  # Envia fechou portão social para a central de monitormento
                  s.send(str.encode(command))
                  reply = s.recv(1024)
                  print(reply.decode('utf-8'))
                  signal.alarm(0)
                  
                except:

                  print("Não conseguiu enviar o evento Fechou portão social")
                  s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Portão social fechou")
                arquivo.write("\n")
                arquivo.close()
                
                saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
                bus.write_byte_data(MCP23017,0x014,saidaA)
                
                pygame.mixer.music.load('mp3/055.mp3') # Fechando portão social
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                  time.sleep(0.1)
                rele1 = 0

                time.sleep(6) # Tempo para fechar o portão Social
                
                saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
                bus.write_byte_data(MCP23017,0x014,saidaA)
                
##              rele1 = 1
##              return rele1
              else:

                saidaA = saidaA - 0b00000001 # Desliga rele 1 (Fecha Portão Social)
                bus.write_byte_data(MCP23017,0x014,saidaA)
                    
                print ("Fechar portão social")

                try:

                  signal.alarm(2)
                  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                  s.connect ((host,port))

                  command = ("7000 189091R13300001")  # Envia fechou portão, para a central de monitormento
                  s.send(str.encode(command))
                  reply = s.recv(1024)
                  print(reply.decode('utf-8'))
                  signal.alarm(0)
                  
                except:

                  print("Não conseguiu enviar o evento Fechou portão social")
                  s.close()
					
                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Portão social fechou")
                arquivo.write("\n")
                arquivo.close()
                                        
                pygame.mixer.music.load('mp3/055.mp3') # Fechando portão social
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                  time.sleep(0.1)

                rele1 = 0
                AP01 = 0
                
            if (pm_eclusa == 0): # Portão da Eclusa Aberto
			
              print ("Espere o fechamento do segundo portão")
              
              pygame.mixer.music.load('mp3/050.mp3')
              pygame.mixer.music.play()
              while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
              time.sleep(1)
         
         
         if (GPIO.input(22) == 1 or php == "AP02"):  # Sinal CTW abertura da Eclusa
           
            if (pm_social == 1): # Portão Social Fechado

              saidaA = saidaA + 0b00000010 #aciona rele 2 (abre portão eclusa)
              bus.write_byte_data(MCP23017,0x014,saidaA)
              
              print ("Abrir portão eclusa")

              try:

                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 189091E13300002")  # Envia abriu portão da eclusa para a central de monitormento
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                signal.alarm(0)
                
              except:
    
                print("Não conseguiu enviar o evento Abriu portão da Eclusa")
                s.close()
			  
              arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
              arquivo.write("Data: ")
              arquivo.write(data)
              arquivo.write(" ")
              arquivo.write(hs)
              arquivo.write(" Evento: Portão eclusa abriu")
              arquivo.write("\n")
              arquivo.close()
              
              pygame.mixer.music.load('mp3/046.mp3')
              pygame.mixer.music.play()
              while pygame.mixer.music.get_busy():
                time.sleep(0.1)
                
              rele2 = 1
              c = 100 # espera 10 segundos pra fechar
              
              while c > 0:

                time.sleep(0.1)
                if (GPIO.input(27) == 1):  # Botão Social pressionado?

                  print("Espere o fechamento do primeiro portão")

                  pygame.mixer.music.load('mp3/049.mp3')
                  pygame.mixer.music.play()
                  while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                else:
                  c = c - 1
              
              time.sleep(1)

##              in_A2 = readadc(1)
##              
##              if(in_A2 == 1): # Sensor de presença eclusa estiver acionado
##
##                print ("Portão eclusa obstruido")
##
##                try:
##
##                  signal.alarm(2)
##                  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##                  s.connect ((host,port))
##
##                  command = ("7000 189091ES0400000")  # Envia Obstrução portão da eclusa para a central de monitormento
##                  s.send(str.encode(command))
##                  reply = s.recv(1024)
##                  print(reply.decode('utf-8'))
##                  signal.alarm(0)
##                  
##                except:
##
##                  print("Não conseguiu enviar o evento Obstrução portão da Eclusa")
##                  s.close()
##
##                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
##                arquivo.write("Data: ")
##                arquivo.write(data)
##                arquivo.write(" ")
##                arquivo.write(hs)
##                arquivo.write(" Evento: Obstrução portão eclusa")
##                arquivo.write("\n")
##                arquivo.close()
##        
##                pygame.mixer.music.load('mp3/054.mp3') # Desobstrua o portão
##                pygame.mixer.music.play()
##                while pygame.mixer.music.get_busy():
##                  time.sleep(0.1)
##                rele2 = 1
##
##                saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
##                bus.write_byte_data(MCP23017,0x014,saidaA)
##
##                time.sleep(2) 
##                    
##                while (in_A2 == 1): # Enquanto sensor de presença eclusa estiver acionado
##
##                  in_A2 = readadc(1) 
##                  
##                  if in_A2 == 0: # Desobstruiu
##					
##                    try:
##
##                      signal.alarm(2)
##                      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##                      s.connect ((host,port))
##
##                      command = ("7000 189091RS0400000")  # Envia Restauração da obstrução portão da eclusa para a central de monitormento
##                      s.send(str.encode(command))
##                      reply = s.recv(1024)
##                      print(reply.decode('utf-8'))
##                      signal.alarm(0)
##                      
##                    except:
##
##                      print("Não conseguiu enviar o evento Restauração obstrução portão da Eclusa")
##                      s.close()
##					
##                  saidaA = saidaA - 0b00000010 #desliga rele 2 (fecha eclusa)
##                  bus.write_byte_data(MCP23017,0x014,saidaA)
##
##                  print("Portão eclusa fechou")
##
##                  try:
##
##                    signal.alarm(2)
##                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##                    s.connect ((host,port))
##
##                    command = ("7000 189091R13300002")  # Envia Portão eclusa fechou para a central de monitormento
##                    s.send(str.encode(command))
##                    reply = s.recv(1024)
##                    print(reply.decode('utf-8'))
##                    signal.alarm(0)
##                    
##                  except:
##
##                    print("Não conseguiu enviar o evento Portão Eclusa fechou")
##                    s.close()
##					
##                  arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
##                  arquivo.write("Data: ")
##                  arquivo.write(data)
##                  arquivo.write(" ")
##                  arquivo.write(hs)
##                  arquivo.write(" Evento: Portão eclusa fechou")
##                  arquivo.write("\n")
##                  arquivo.close()
##					
##                  saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
##                  bus.write_byte_data(MCP23017,0x014,saidaA)
##                    
##                  pygame.mixer.music.load('mp3/056.mp3') # Fechando Portão da Eclusa
##                  pygame.mixer.music.play()
##                  while pygame.mixer.music.get_busy():
##                    time.sleep(0.1)
##                  rele2 = 0
##
##                  saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
##                  bus.write_byte_data(MCP23017,0x014,saidaA)
##                    
##                  if (GPIO.input(27) == 1):  # Botão Social pressionado?
##                      
##                    print("Espere o fechamento do primeiro portão")
##
##                    saidaB = saidaB + 0b00000010 # Liga saida de audio 2 (rele 10) ######################### Seleciona saida de audio 2
##                    bus.write_byte_data(MCP23017,0x015,saidaB)
##                    
##                    pygame.mixer.music.load('mp3/049.mp3') # Espere o fechamento do portão
##                    pygame.mixer.music.play()
##                    while pygame.mixer.music.get_busy():
##                      time.sleep(0.1)
##
##                    saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
##                    bus.write_byte_data(MCP23017,0x015,saidaB)
##                    
##                  time.sleep(0.2)
              
              if (GPIO.input(25) == 0 and rele2 == 1): # Fecha portão da Eclusa
                	
                saidaA = saidaA - 0b00000010 #desliga rele 2 (Fecha portão da Eclusa)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                print("Fechou portão da Eclusa")

                try:
                        
                  signal.alarm(2)
                  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                  s.connect ((host,port))

                  command = ("7000 189091R13300002")  # Envia Portão eclusa fechou para a central de monitormento
                  s.send(str.encode(command))
                  reply = s.recv(1024)
                  print(reply.decode('utf-8'))
                  signal.alarm(0)
                  
                except:

                  print("Não conseguiu enviar o evento Portão Eclusa fechou")
                  s.close()
				
                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Portão Eclusa fechou")
                arquivo.write("\n")
                arquivo.close()
				
                saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                saidaB = saidaB + 0b00000010 # Liga saida de audio 2 (rele 10)
                bus.write_byte_data(MCP23017,0x015,saidaB)
                    
                pygame.mixer.music.load('mp3/056.mp3') # Fechando portão da eclusa
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                  time.sleep(0.1)

                saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
                bus.write_byte_data(MCP23017,0x015,saidaB)
                  
                saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                rele1 = 0
           		  
            if (pm_social == 0): # Se o portão Social estiver Aberto
			
              print ("Espere o fechamento do primeiro portão")

              saidaB = saidaB + 0b00000010 # Liga saida de audio 2 (rele 10)
              bus.write_byte_data(MCP23017,0x015,saidaB)
                   
              pygame.mixer.music.load('mp3/049.mp3') # Espere o fechamento do portão
              pygame.mixer.music.play()
              while pygame.mixer.music.get_busy():
                time.sleep(0.1)
      
              saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
              bus.write_byte_data(MCP23017,0x015,saidaB)
              
              time.sleep(1)

         if (php == "AP03"):  # Abre portão de acesso (ligar no "BOT" da placa do portão de acesso)

           print ("Abrindo portão de acesso")

           
           saidaA = saidaA + 0b00000100 #aciona rele 3
           bus.write_byte_data(MCP23017,0x014,saidaA)

           pygame.mixer.music.load('mp3/102.mp3') # Abrindo portão de acesso
           pygame.mixer.music.play()
           while pygame.mixer.music.get_busy():
             time.sleep(0.1)

           try:

                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 189091E13300003")  # Envia abriu portão da eclusa para a central de monitormento
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                signal.alarm(0)
                
           except:
    
                print("Não conseguiu enviar o evento Abriu portão de Acesso")
                s.close()
			  
                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Portão de acesso abriu")
                arquivo.write("\n")
                arquivo.close()
              
           time.sleep(10)

           saidaA = saidaA - 0b00000100 # Fecha portão de acesso
           bus.write_byte_data(MCP23017,0x014,saidaA)

           print ("Fechando portão de acesso")

           pygame.mixer.music.load('mp3/103.mp3')
           pygame.mixer.music.play()
           while pygame.mixer.music.get_busy():
             time.sleep(0.1)

           try:

                signal.alarm(2)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("7000 189091R13300003")  # Envia fechou portão da eclusa para a central de monitormento
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                signal.alarm(0)
                
           except:
    
                print("Não conseguiu enviar o evento Fechou portão de Acesso")
                s.close()
			  
                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Portão de acesso fechou")
                arquivo.write("\n")
                arquivo.close()

           

         print("Saiu da rotina intertravamento") 
         

def get_cpu_temp(): # retorna o valor da temperatura da cpu do CLP
    tempFile = open( "/sys/class/thermal/thermal_zone0/temp" )
    cpu_temp = tempFile.read()
    tempFile.close()
    return float(cpu_temp)/1000

def emergencia(saidaA,saidaB,hs,data):

    in0 = GPIO.input(17)
    in1 = GPIO.input(18)
    in2 = GPIO.input(27)
    in3 = GPIO.input(22)
    in4 = GPIO.input(23)
    in5 = GPIO.input(24)
    in6 = GPIO.input(25)
    in7 = GPIO.input(4)
       
    pm_social = in0
    pm_eclusa = in1
    ctw_social = in2
    ctw_eclusa = in3
    chave_emergencia = in4
    chave_servico = in5
    falha_energia = in6
    quebra_de_vidro = in7

    
    print ("Modo de emergência acionado")

    try:
            
      signal.alarm(2)
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect ((host,port))

      command = ("7000 189091ES0200000")  # Envia Restauração modo de Emergencia para a central de monitormento
      s.send(str.encode(command))
      reply = s.recv(1024)
      print(reply.decode('utf-8'))
      signal.alarm(0)
      
    except:
    
      print("Não conseguiu enviar o evento Restauração modo de Emergencia")
      s.close()
    
    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Sistema em modo de emergência")
    arquivo.write("\n")
    arquivo.close()

    saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
    bus.write_byte_data(MCP23017,0x014,saidaA)

    saidaB = saidaB + 0b00000010 # Liga saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)

    pygame.mixer.music.load('mp3/077.mp3') # Sistema de emergencia acionado
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
      time.sleep(0.1)

    time.sleep(1)

    saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)

    saidaA = saidaA - 0b10000000  # Desliga rele 8 (Giroflex)
    bus.write_byte_data(MCP23017,0x014,saidaA)
      
    while (GPIO.input(23) == 1): # Enquanto a chave de emergência estiver acionada

        if(GPIO.input(27) ==1): #  Se o sinal do CTW do portão social for acionado

          print("social acionado")	   
          intertravamento(saidaA,saidaB,hs,data,0,"")
      
      
        if(GPIO.input(22) ==1): # Se o sinal do CTW do portão do portão eclusa for acionado

          print("eclusa acionado")	   
          intertravamento(saidaA,saidaB,hs,data,0,"") # Chama a rotina de intertravamento com o rele do CTW acionado


        time.sleep(0.1)

    saidaB = saidaB + 0b00000010 # Liga saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)
          
    print("Saiu do modo de emergencia")

    try:
            
      signal.alarm(2)
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect ((host,port))

      command = ("7000 189091RS0200000")  # Envia Restauração modo de Emergencia para a central de monitormento
      s.send(str.encode(command))
      reply = s.recv(1024)
      print(reply.decode('utf-8'))
      signal.alarm(0)
      
    except:
    
      print("Não conseguiu enviar o evento Restauração modo de Emergencia")
      s.close()

    arquivo = open("log_sea.txt", "a+") # Escreve no registro de log
    arquivo.write(hs)
    arquivo.write(" Saiu do modo de emergência")
    arquivo.write("\n")
    arquivo.close()
        
    pygame.mixer.music.load('mp3/021.mp3') # Sistema operando em modo automático
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
      time.sleep(0.1)
    
    saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)

def servico(saidaA,saidaB,hs,data):

    reset = 0
    terminando = 0
      
    tempo_servico = 70  # Determina o tempo que os portões ficarão abertos (inicia com 5 min)
    maximo = 0
    saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
    bus.write_byte_data(MCP23017,0x014,saidaA)
        
    print("Chave de serviço acionada")

    try:
            
      signal.alarm(2)   
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect ((host,port))

      command = ("7000 189091ES0100000")  # Envia Chave de Serviço acionada para a central de monitormento
      s.send(str.encode(command))
      reply = s.recv(1024)
      print(reply.decode('utf-8'))
      signal.alarm(0)
      
    except:
    
      print("Não conseguiu enviar o evento Chave de Serviço acionada")
      s.close()

    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Chave de serviço acionada")
    arquivo.write("\n")
    arquivo.close()
    
    saidaA = saidaA + 0b00000001 #aciona rele 1 (abre portão social)
    bus.write_byte_data(MCP23017,0x014,saidaA)
	
    print ("Abriu portão social")

    try:
            
      signal.alarm(3)   
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect ((host,port))

      command = ("7000 189091E13300001")  # Envia Abriu portão social para a central de monitormento
      s.send(str.encode(command))
      reply = s.recv(1024)
      print(reply.decode('utf-8'))
      signal.alarm(0)
      
    except:

      print("Não conseguiu enviar o evento Abriu portão social")
      s.close()
	
    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Portão social abriu")
    arquivo.write("\n")
    arquivo.close()
        
    saidaA = saidaA + 0b00000010 #aciona rele 2 (Abre portão eclusa)
    bus.write_byte_data(MCP23017,0x014,saidaA)
	
    print ("Abrir portão Eclusa")
	
    try:
            
      signal.alarm(3)   
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect ((host,port))

      command = ("7000 189091E13300002")  # Envia Abriu portão da Eclusa para a central de monitormento
      s.send(str.encode(command))
      reply = s.recv(1024)
      print(reply.decode('utf-8'))
      signal.alarm(0)
      
    except:
    
      print("Não conseguiu enviar o evento Abriu portão da Eclusa")
      s.close()

    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Portão eclusa abriu")
    arquivo.write("\n")
    arquivo.close()
	
    saidaB = saidaB + 0b00000010 # Liga saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)
          
    pygame.mixer.music.load('mp3/040.mp3') # Mensagem: Abrindo portões, acione a chave novamente para manter abertos.
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
      time.sleep(0.1)
	  
    time.sleep(1)
    
    saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)
              
    saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
    bus.write_byte_data(MCP23017,0x014,saidaA)

    while (tempo_servico > 0 ):#Logica de aumento de tempo
        
      if (GPIO.input(24) == 1 and tempo_servico > 0 and tempo_servico < 300):
        
        tempo_servico = tempo_servico + 600 # Adiciona mais 10 min ao tempo

        arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Acrescentado mais 10 minutos ao tempo de serviço")
        arquivo.write("\n")
        arquivo.close()
		
        saidaB = saidaB + 0b00000010 # Liga saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)
           
        pygame.mixer.music.load('mp3/079.mp3') # Mensagem: Adicionado mais 10 minutos
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
          time.sleep(0.1)
    
        saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)

      if (GPIO.input(24) == 1 and tempo_servico > 300 and tempo_servico < 900):

        tempo_servico = tempo_servico + 1800 # Adiciona mais 30 min ao tempo

        arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Acrescentado mais 30 minutos ao tempo de serviço")
        arquivo.write("\n")
        arquivo.close()

        saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)

        pygame.mixer.music.load('mp3/080.mp3') # Mensagem: Adicionado mais 30 minutos
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
          time.sleep(0.1)

        time.sleep(1)

        saidaB = saidaB - 0b00000010 # desliga saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)
            
      if (GPIO.input(24) == 1 and tempo_servico > 900 and maximo == 0):

        tempo_servico = 3600 # Adiciona 1h ao tempo (tempo máximo)
        arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Acrescentado 1 hora ao tempo de serviço")
        arquivo.write("\n")
        arquivo.close()

        saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)

        pygame.mixer.music.load('mp3/081.mp3') # Mensagem: Adicionado mais 1h (maximo permitido)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
          time.sleep(0.1)

        saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)
          
        maximo = 1

      if(GPIO.input(4) == 1): # reset_servico
            
        saidaA = saidaA + 0b10000000 # Liga rele 8 (Giroflex)
        bus.write_byte_data(MCP23017,0x014,saidaA)

        print("Saiu do modo de Serviço")

        try:

          signal.alarm(3)
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s.connect ((host,port))

          command = ("7000 189091RS0100000")  # Envia Saiu do modo de Serviço para a central de monitormento
          s.send(str.encode(command))
          reply = s.recv(1024)
          print(reply.decode('utf-8'))
          signal.alarm(0)
          
        except:

          print("Não conseguiu enviar o evento Saiu do modo de Serviço")
          s.close()
		
        arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Saiu do modo de Serviço")
        arquivo.write("\n")
        arquivo.close()
      
        time.sleep(1)

        saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)
           
        pygame.mixer.music.load('mp3/082.mp3')  # Fim do tempo de serviço
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
          time.sleep(0.1)

        saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)

        saidaA = saidaA - 0b00000001 # Fecha portão social
        bus.write_byte_data(MCP23017,0x014,saidaA)
        
        print ("Fechou portão social")

        try:
                
          signal.alarm(3)
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s.connect ((host,port))

          command = ("7000 189091R13300001")  # Envia Fechou portão social para a central de monitormento
          s.send(str.encode(command))
          reply = s.recv(1024)
          print(reply.decode('utf-8'))
          signal.alarm(0)
          
        except:
   
          print("Não conseguiu enviar o evento Fechou portão social")
          s.close()

        arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Fechou portão Social")
        arquivo.write("\n")
        arquivo.close()
      
        saidaA = saidaA - 0b00000010 # Fecha portão eclusa
        bus.write_byte_data(MCP23017,0x014,saidaA)
        
        print ("Fechou portão Eclusa")

        try:
                
          signal.alarm(3)
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s.connect ((host,port))

          command = ("7000 189091R13300002")  # Envia Fechou portão Eclusa para a central de monitormento
          s.send(str.encode(command))
          reply = s.recv(1024)
          print(reply.decode('utf-8'))
          signal.alarm(0)
          
        except:

          print("Não conseguiu enviar o evento Fechou portão Eclusa")
          s.close()

        arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Fechou portão da Eclusa")
        arquivo.write("\n")
        arquivo.close()
      
        tempo_servico = 0
        reset = 1

        saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)

        pygame.mixer.music.load('mp3/021.mp3')  # Sistema operando em modo automático
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
          time.sleep(0.1)

        saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)

        time.sleep(6) # Tempo para fechamento do portão ################## Tempo até que o portão termine de fechar

        saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
        bus.write_byte_data(MCP23017,0x014,saidaA)

      tempo_servico = tempo_servico - 0.1

      # Rotina para converter os segundos em minutos

      seg_restantes = tempo_servico % 3600
      minutos = seg_restantes // 60
      seg_restantes_final = seg_restantes % 60
        
      if (minutos == 0 and terminando == 0):
                
        saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)

        pygame.mixer.music.load('mp3/041.mp3') # Falta 1 minuto para o fim do tempo de serviço
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
          time.sleep(0.1)

        time.sleep(1)

        saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
        bus.write_byte_data(MCP23017,0x015,saidaB)

        terminando = 1

      print("Tempo restante: {:.0f}:{:.0f}s ".format(minutos,seg_restantes_final))

      time.sleep(0.1)
        
        
    if(reset == 0): # Se otempo de serviço acabou sem pressionar o reset

      saidaA = saidaA + 0b10000000 # Liga rele 8 (Giroflex)
      bus.write_byte_data(MCP23017,0x014,saidaA)

      print("Saiu do modo de Serviço")
	  
      try:
              
        signal.alarm(3)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect ((host,port))

        command = ("7000 189091RS0100000")  # Envia Saiu do modo de Serviço para a central de monitormento
        s.send(str.encode(command))
        reply = s.recv(1024)
        print(reply.decode('utf-8'))
        signal.alarm(0)
        
      except:

        print("Não conseguiu enviar o evento Saiu do modo de Serviço")
        s.close()

      arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
      arquivo.write("Data: ")
      arquivo.write(data)
      arquivo.write(" ")
      arquivo.write(hs)
      arquivo.write(" Evento: Saiu do modo de Serviço")
      arquivo.write("\n")
      arquivo.close()
      
      time.sleep(1)

      saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
      bus.write_byte_data(MCP23017,0x015,saidaB)

      pygame.mixer.music.load('mp3/082.mp3') # Fim do tempo de serviço
      pygame.mixer.music.play()
      while pygame.mixer.music.get_busy():
        time.sleep(0.1)

      saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
      bus.write_byte_data(MCP23017,0x015,saidaB)

      saidaA = saidaA - 0b00000001 # Fecha portão social
      bus.write_byte_data(MCP23017,0x014,saidaA)
      
      print ("Fechou portão social")
	  
      try:
              
        signal.alarm(3)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect ((host,port))

        command = ("7000 189091R13300001")  # Envia Fechou portão social para a central de monitormento
        s.send(str.encode(command))
        reply = s.recv(1024)
        print(reply.decode('utf-8'))
        signal.alarm(0)
        
      except:

        print("Não conseguiu enviar o evento Fechou portão social")
        s.close()

              
      arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
      arquivo.write("Data: ")
      arquivo.write(data)
      arquivo.write(" ")
      arquivo.write(hs)
      arquivo.write(" Evento: Fechou portão Social")
      arquivo.write("\n")
      arquivo.close()
      
      saidaA = saidaA - 0b00000010 # Fecha portão eclusa
      bus.write_byte_data(MCP23017,0x014,saidaA)
      
      print ("Fechou portão Eclusa")
	  
      try:

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect ((host,port))

        command = ("7000 189091R13300002")  # Envia Fechou portão Eclusa para a central de monitormento
        s.send(str.encode(command))
        reply = s.recv(1024)
        print(reply.decode('utf-8'))

      except:

        print("Não conseguiu enviar o evento Fechou portão Eclusa")
        s.close()

      arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
      arquivo.write("Data: ")
      arquivo.write(data)
      arquivo.write(" ")
      arquivo.write(hs)
      arquivo.write(" Evento: Fechou portão da Eclusa")
      arquivo.write("\n")
      arquivo.close()
      
      tempo_servico = 0
      reset = 1

      saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
      bus.write_byte_data(MCP23017,0x015,saidaB)

      pygame.mixer.music.load('mp3/021.mp3') # Sistema em modo automático
      pygame.mixer.music.play()
      while pygame.mixer.music.get_busy():
        time.sleep(0.1)

      time.sleep(1)
		
      saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
      bus.write_byte_data(MCP23017,0x015,saidaB)

      time.sleep(6) # Tempo para fechamento do portão ################## Tempo de espera para fechamento do portão 

      saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex)
      bus.write_byte_data(MCP23017,0x014,saidaA)

      return saidaA
	
def violacao_social(saidaA,saidaB,hs,data):

    print("Violação do portão Social")
    
    try:
            
      signal.alarm(3)  
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect ((host,port))
      
      command = ("7000 189091E12000001")  # Violação portão social
      s.send(str.encode(command))
      reply = s.recv(1024)
      print(reply.decode('utf-8'))
      signal.alarm(0)
      
    except:

      print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de violação do portão social")
      s.close()
      
    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Violação do portão Social")
    arquivo.write("\n")
    arquivo.close()

    saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
    bus.write_byte_data(MCP23017,0x014,saidaA)
      
    saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)
    
    pygame.mixer.music.load('mp3/051.mp3')
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
      time.sleep(0.1)
    time.sleep(2)

    if(GPIO.input(17) == 0): # Se o ponto magnético Social continua aberto
      pygame.mixer.music.load('mp3/059.mp3') # Avisa que o portão Social esta aberto.
      pygame.mixer.music.play()
      while pygame.mixer.music.get_busy():
        time.sleep(0.1)
      time.sleep(3)

      saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
      bus.write_byte_data(MCP23017,0x015,saidaB)

      saidaA = saidaA - 0b10000000  # Desliga rele 8 (Giroflex)
      bus.write_byte_data(MCP23017,0x014,saidaA)

def violacao_eclusa(saidaA,saidaB,hs,data):

    print("Violação so Portão da Eclusa")
    	  
    try:
            
      signal.alarm(3)  
      s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      s.connect ((host,port))
       
      command = ("7000 189091E12002000")  # Violação portão da eclusa
      s.send(str.encode(command))
      reply = s.recv(1024)
      print(reply.decode('utf-8'))
      signal.alarm(0)
      
    except:

      print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de violação da eclusa")
      s.close()

    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Violação do portão da Eclusa")
    arquivo.write("\n")
    arquivo.close()
    
    saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex)
    bus.write_byte_data(MCP23017,0x014,saidaA)
    
    saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)

    pygame.mixer.music.load('mp3/052.mp3') # Violação da Eclusa
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
      time.sleep(0.1)

    time.sleep(1)

    saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)

    if(GPIO.input(18) == 0): # Se o ponto magnético da Eclusa continua aberto

      saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
      bus.write_byte_data(MCP23017,0x015,saidaB)
     
      pygame.mixer.music.load('mp3/060.mp3') # Avisa que o portão da Eclusa esta aberto.
      pygame.mixer.music.play()
      while pygame.mixer.music.get_busy():
        time.sleep(0.1)
      
    time.sleep(3)

    saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
    bus.write_byte_data(MCP23017,0x015,saidaB)

    saidaA = saidaA - 0b10000000  # Desliga rele 8 (Giroflex)
    bus.write_byte_data(MCP23017,0x014,saidaA)

def periodico_1min():

  # Faz a leitura analogica da entrada solicitada (de A0 a A7)

  def ReadChannel(channel):
    adc = spi.xfer2([1,(8+channel)<<4,0])
    data = ((adc[1]&3) << 8) + adc[2]
    return data

  # Converte a entrada da leitura analógica solicitada em Volts.

  def ConvertVolts(data,places):
    
    volts = (data * 20.6) / float(1022)
    volts = round(volts,places)
    return volts
  
  def mede_tensao_baterias():

        
    analog = ReadChannel(3)
    volts = ConvertVolts(analog,1) # Mostra 1 casa decimal depois da virgula
    print("\n")
    print ("--------------------------------------------")
    print("Bateria 1 (Analog 2) {} (Tensão: {}V)".format(analog,volts))
    v1 = volts
      
    analog = ReadChannel(4)
    volts = ConvertVolts(analog,1) # Mostra 1 casa decimal depois da virgula
    print ("--------------------------------------------")
    print("Bateria 2 (Analog 3) {} (Tensão: {}V)".format(analog,volts))
    v2 = volts
     
    analog = ReadChannel(5)
    volts = ConvertVolts(analog,1) # Mostra 1 casa decimal depois da virgula 
    print ("--------------------------------------------")
    print("Bateria 3 (Aanalog 4) {} (Tensão: {}V)".format(analog,volts))
    print ("--------------------------------------------")
    print("\n")
    v3 = volts

    # Quando as baterias estiverem conectadas descomentar esse trecho

  ##    if v1<10:
  ##
  ##      print("A bateria do sistema está baixa")
  ##
  ##      try:
  ##
  ##        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  ##        s.connect ((host,port))
  ##        if ("#"):
  ##          print("Mensagem inválida, verifique o códico")
  ##        else:
  ##          command = ("7000 189091E30200001")  # Bateria do sistema está baixa
  ##          s.send(str.encode(command))
  ##          reply = s.recv(1024)
  ##          print(reply.decode('utf-8'))
  ##
  ##      except:
  ##
  ##        print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de Bateria do sistema baixa")
  ##        s.close()
  ##
  ##      if v2<10:
  ##
  ##        print("A bateria dos portões sociais está baixa")
  ##
  ##        try:
  ##
  ##          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  ##          s.connect ((host,port))
  ##          if ("#"):
  ##            print("Mensagem inválida, verifique o códico")
  ##          else:
  ##            command = ("7000 189091E30900001")  # Bateria dodo portão social está baixa
  ##            s.send(str.encode(command))
  ##            reply = s.recv(1024)
  ##            print(reply.decode('utf-8'))
  ##
  ##        except:
  ##
  ##          print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de Bateria dos portões sociais baixa")
  ##          s.close()
  ##          
  ##      if v3<10:
  ##
  ##        print("A bateria do portão da garagem está baixa")
  ##
  ##        try:
  ##
  ##          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  ##          s.connect ((host,port))
  ##          if ("#"):
  ##            print("Mensagem inválida, verifique o códico")
  ##          else:
  ##            command = ("7000 189091E31100004")  # Bateria dodo portão da garagem está baixa
  ##            s.send(str.encode(command))
  ##            reply = s.recv(1024)
  ##            print(reply.decode('utf-8'))
  ##
  ##        except:
  ##
  ##          print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de Bateria do portão da garagem está baixa")
  ##          s.close()

  while(1):

    time.sleep(60)
    
    print ("Temperatura da CPU: ",round(get_cpu_temp()),"ºC\n")
    temperatura = round(get_cpu_temp())

    mede_tensao_baterias()
    # As temperaturas podem chegar até 85º, porem a partir de 80º o proprio
    # sistema derruba o processamento pela metade para diminuir a temperatura.
          
    if (temperatura > 70): 

      print ("Atenção!, alta temperatura do processador, verificar o funcionamento do cooler!")

      try:
              
          signal.alarm(3)  
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s.connect ((host,port))
                
          command = ("7000 189091E15800000")  # Alta temperatura no processador do CLP
          s.send(str.encode(command))
          reply = s.recv(1024)
          print(reply.decode('utf-8'))
          signal.alarm(0)
          
      except:

          print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de Alta temperatura no processador")
          s.close()

      arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
      arquivo.write("Data: ")
      arquivo.write(data)
      arquivo.write(" ")
      arquivo.write(hs)
      arquivo.write(" Evento: Alta temperatura do processador")
      arquivo.write("\n")
      arquivo.close()

         
    

def logica_garagem(saidaA):

    vrg = 1

    saidaA = saidaA + 0b00001000 # Abre portão da garagem (Rele 4)
    bus.write_byte_data(MCP23017,0x014,saidaA)

    pygame.mixer.music.load('mp3/101.mp3') # Abrindo portão da garagem
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
      time.sleep(0.1)

    try:

                      
         signal.alarm(3)  
         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         s.connect ((host,port))
                
         command = ("7000 189091E13300004")  # Envia "abriu portão da garagem" para o moni
         s.send(str.encode(command))
         reply = s.recv(1024)
         print(reply.decode('utf-8'))
         signal.alarm(0)

    except:

         print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento abriu portão da garagem")
         s.close()

    arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
    arquivo.write("Data: ")
    arquivo.write(data)
    arquivo.write(" ")
    arquivo.write(hs)
    arquivo.write(" Evento: Abriu portão da garagem")
    arquivo.write("\n")
    arquivo.close()

    time.sleep(1)
    
			
    t = 300 # Tempo que o portão ficará aberto (30 segundos)
 
    while (t > 0):

        b1  = readadc(0) # Barreira 1
        b2  = readadc(1) # Barreira 2
        pmg = readadc(2) # Ponto magnético do portão
        ag  = readadc(7) # Comando para abrir a garagem
        
        barreira_1 = b1 # Lê o A0 (Sensor Barreira 1) e registra 0 ou 1 na variavel 
        barreira_2 = b2 # Lê o A1 (Sensor Barreira 2) e registra 0 ou 1 na variavel 
        garagem_aberto = pmg # Lê o A2 (Ponto magnético garagem aberta)
        abre_garagem = ag # Lê a entrada A7 (Comando de abertura do portão Garagem)
        
        print("Entrou na logica da garagem")
       
        if(barreira_1 == 0): # Se o sensor de barreira 1 acionou
          
          print ("Barreira 1 acionada")
          
          a = 300 # Espera cerca de 30 segundos
          p1 = 0
               
          while a > 0:

              b1  = readadc(0) # Barreira 1
              b2  = readadc(1) # Barreira 2
              pmg = readadc(2) # Ponto magnético do portão
              ag  = readadc(7) # Comando para abrir a garagem
              barreira_1 = b1 # Lê o A0 (Sensor Barreira 1) e registra 0 ou 1 na variavel
              barreira_2 = b2 # Lê o A1 (Sensor Barreira 2) e registra 0 ou 1 na variavel
              garagem_aberto = pmg # Lê o A2 (Ponto magnético garagem aberta)
              abre_garagem = ag # Lê a entrada A7 (Comando de abertura do portão Garagem)
              
              print ("Entrou na logica da barreira 2")

              if barreira_1 == 1 and p1 == 0: # Se a barreira 1 desacionou
                  
                print("Entrou um pedestre")

                saidaA = saidaA - 0b00001000 # Fecha portão da garagem (Rele 4)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                try:
                      
                    signal.alarm(3)  
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))
                            
                    command = ("7000 189091E13000008")  # Envia Violação entrada da garagem (pedestre) para o moni
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
                    print ("Enviou violação da garagem paro o moni")
                    
                except:

                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Violação entrada da garagem (pedestre)")
                    s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Violação entrada da garagem (pedestre)")
                arquivo.write("\n")
                arquivo.close()
                
               # time.sleep(1)
             

                try:
                      
                    signal.alarm(3)  
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))
                            
                    command = ("7000 189091R13300004")  # Envia Fechou portão da garagem para o moni
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
                      
                except:

                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
                    s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Fechou portão da garagem")
                arquivo.write("\n")
                arquivo.close()
                                      
                pygame.mixer.music.load('mp3/025.mp3') # Violação entrada da garagem (pedestre)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                
                t = 1     
                return saidaA

              if barreira_2 == 0 and p1 == 0: # Se a barreira 2 acionou com a 1 acionada
                print("Entrou um veiculo")
                      
                pygame.mixer.music.load('mp3/018.mp3') # Entrada de veiculo
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                try:

                      
                    signal.alarm(3)  
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))
                            
                    command = ("7000 189091EL0100004")  # Envia "Entrada de veiculo" para o moni
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
                      
                except:

                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Entrada de veículo")
                    s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Entrada de veículo")
                arquivo.write("\n")
                arquivo.close()
                
                time.sleep(1)
                                    
                saidaA = saidaA - 0b00001000 # Fecha portão da garagem (Rele 4)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                try:

                    signal.alarm(3)  
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))
                            
                    command = ("7000 189091R13300004")  # Envia Fechou ortão da garagem (pedestre) para o moni
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
                      
                except:

                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
                    s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Fechou portão da garagem")
                arquivo.write("\n")
                arquivo.close()

                p1 = 1
                d = 70 # enquanto o portão fecha espera 5 segundos para verificar uma possivel dupla passagem

                time.sleep(0.1)
                
                while(d > 0):

                    b1  = readadc(0) # Barreira 1
                    
                    barreira_1 = b1 # Lê o A0 (Sensor Barreira 1) e registra 0 ou 1 na variavel

                    if(barreira_1 == 0): # Se a barreira 1 acionou
                      print ("Dupla passagem")

                      pygame.mixer.music.load('mp3/099.mp3') # Dupla passagem
                      pygame.mixer.music.play()
                      while pygame.mixer.music.get_busy():
                          time.sleep(0.1)

                      try:

                          signal.alarm(3)  # Time out de 3 segundos
                          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                          s.connect ((host,port))
                                
                          command = ("7000 189091E13000009")  # Envia Dupla passagem para o moni
                          s.send(str.encode(command))
                          reply = s.recv(1024)
                          print(reply.decode('utf-8'))
                          signal.alarm(0)
          
                      except:

                          print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Dupla passagem")
                          s.close()

                      arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                      arquivo.write("Data: ")
                      arquivo.write(data)
                      arquivo.write(" ")
                      arquivo.write(hs)
                      arquivo.write(" Evento: Dupla passagem")
                      arquivo.write("\n")
                      arquivo.close()

                    d = d - 1
                    time.sleep(0.1)
                    print ("Verificando possivel dupla passagem")
                           
                return saidaA
								
              a = a - 1
              time.sleep(0.1)
              t = 1
              
        if barreira_2 == 0: # Se a barreira 2 acionou
            
          print("Logica barreira 2")
          b = 300 # aguarda durante 30 segundos
          p = 0

          while b > 0:

              b1  = readadc(0) # Barreira 1
              b2  = readadc(1) # Barreira 2
              pmg = readadc(2) # Ponto magnético do portão
              ag  = readadc(7) # Comando para abrir a garagem
              barreira_1 = b1 # Lê o A0 (Sensor Barreira 1) e registra 0 ou 1 na variavel
              barreira_2 = b2 # Lê o A1 (Sensor Barreira 2) e registra 0 ou 1 na variavel
              garagem_aberto = pmg # Lê o A2 (Ponto magnético garagem aberta)
              abre_garagem = ag # Lê a entrada A7 (Comando de abertura do portão Garagem)

              print("While barreira 2")

              if barreira_2 == 1 and p == 0:  # Barreira 2 desacionou

                print("Violação da entrada, pedestre")
                
                saidaA = saidaA - 0b00001000 # Fecha portão da garagem (Rele 4)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                try:

                    signal.alarm(3)  
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))
                                
                    command = ("7000 189091E13000008")  # Envia Violação entrada da garagem (pedestre) para o moni
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
          
                except:

                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Violação entrada da garagem (pedestre)")
                    s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Violação entrada da garagem (pedestre)")
                arquivo.write("\n")
                arquivo.close()

                time.sleep(0.5)

                try:
                      
                    signal.alarm(3)  
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))
                            
                    command = ("7000 189091R13300004")  # Envia Fechou portão da garagem para o moni
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
                      
                except:

                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
                    s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Fechou portão da garagem")
                arquivo.write("\n")
                arquivo.close()

                pygame.mixer.music.load('mp3/025.mp3') # Violação entrada da garagem (pedestre)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                                
                p = 1
                return saidaA
            
          
              if barreira_1 == 0 and p == 0: # barreira 1 acionou

                print("Saida de veiculo")

                pygame.mixer.music.load('mp3/027.mp3') # Saida de veiculo
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                try:

                    signal.alarm(3)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))
                                
                    command = ("7000 189091EL0200004")  # Saida de veículo
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
          
                except:

                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Saída de veiculo")
                    s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Saída de veiculo")
                arquivo.write("\n")
                arquivo.close()
                                                    
                saidaA = saidaA - 0b00001000 # Fecha portão da garagem (Rele 4)
                bus.write_byte_data(MCP23017,0x014,saidaA)

                print("Fechando portão")
                
                pygame.mixer.music.load('mp3/100.mp3') # Fechando portão da garagem
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)

                try:

                    signal.alarm(3)
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))
                                
                    command = ("7000 189091R13300004")  # Envia Fechou portão da garagem para o moni
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    signal.alarm(0)
          
                except:

                    print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
                    s.close()

                arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                arquivo.write("Data: ")
                arquivo.write(data)
                arquivo.write(" ")
                arquivo.write(hs)
                arquivo.write(" Evento: Fechou portão da garagem")
                arquivo.write("\n")
                arquivo.close()

                p = 1
                d = 50

                while(d > 0):

                    b1  = readadc(0) # Barreira 1
                    
                    barreira_1 = b1 # Lê o A0 (Sensor Barreira 1) e registra 0 ou 1 na variavel

                    if(barreira_1 == 0): # Se a barreira 1 acionou
                        
                      print ("Dupla passagem")

                      pygame.mixer.music.load('mp3/099.mp3') # Dupla passagem
                      pygame.mixer.music.play()
                      while pygame.mixer.music.get_busy():
                          time.sleep(0.1)

                      try:

                          signal.alarm(3)  # Time out de 3 segundos
                          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                          s.connect ((host,port))
                                
                          command = ("7000 189091E13000009")  # Envia Dupla passagem para o moni
                          s.send(str.encode(command))
                          reply = s.recv(1024)
                          print(reply.decode('utf-8'))
                          signal.alarm(0)
          
                      except:

                          print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Dupla passagem")
                          s.close()

                      arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
                      arquivo.write("Data: ")
                      arquivo.write(data)
                      arquivo.write(" ")
                      arquivo.write(hs)
                      arquivo.write(" Evento: Dupla passagem")
                      arquivo.write("\n")
                      arquivo.close()

                    d = d - 1
                    time.sleep(0.1)
                    print ("Verificando possivel dupla passagem")
                
                return saidaA
            
              b = b - 1
              time.sleep(0.1)
              t = 1
              
        time.sleep(0.1) # Conta 1 milisegundo e subtrai 1 de "t"
        t = t - 1

    print("Saiu do loop logica da garagem")

    saidaA = saidaA - 0b00001000 # Fecha portão da garagem (Rele 4)
    bus.write_byte_data(MCP23017,0x014,saidaA)

    print("Fechando portão da garagem")

    try:

        signal.alarm(3)  
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect ((host,port))
                            
        command = ("7000 189091R13300004")  # Envia Fechou ortão da garagem (pedestre) para o moni
        s.send(str.encode(command))
        reply = s.recv(1024)
        print(reply.decode('utf-8'))
        signal.alarm(0)
                      
    except:

        print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Fechou portão da garagem")
        s.close()

        arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
        arquivo.write("Data: ")
        arquivo.write(data)
        arquivo.write(" ")
        arquivo.write(hs)
        arquivo.write(" Evento: Fechou portão da garagem")
        arquivo.write("\n")
        arquivo.close()

    vrg = 0
    return saidaA


def loop_da_garagem():

    while(1):

        ag  = readadc(7)
        abre_garagem = ag # Lê a entrada A7 (requisição de abertura do portão Garagem)

        if(abre_garagem == 0):    # Lógica do portão da garagem

            logica_garagem(saidaA)
    
def leitor(ser,saidaA,hs,data):
  
    try:

      if(ser.inWaiting()): # Se houver alguma entrada na serial

        letra = ser.readline()
        letra.decode("utf-8")
        lt = str (letra)
        
        ed = (lt.split ("'")[1])   # Limpa o "b" que aparece no inicio
        letra = (ed.split ("\\")[0]) 
        print("\nLeitor",letra)

        cd = ser.readline()
        cd.decode("utf-8")
        cod = str (cd)
        
        ed_cod = (cod.split ("'")[1])
        codigo = (ed_cod.split ("\\")[0]) 
        print(codigo,"\n")
        
        time.sleep(0.5)  # tempo de espera para que o rele do modulo leitor acione
        
        if(GPIO.input(27) == 1): # Acionamento do relê do CTW para abertura do portão social

          query = ("SELECT codigo FROM moradores") # Seleciona a coluna "codigo" da tabela "moradores" no banco de dados SEA
          cursor.execute(query)

          valido = 0
                  
          for (i) in cursor: # Para cada item da coluna "codigo" faz a comparação

            i = str(i)
            it = (i.split ("'")[1])   
            item = (it.split (",")[0])
          
            if item == codigo: # Compara se o codigo recebido pela serial é o mesmo lido da linha comparada
            
              #print("Usuario Cadastrado")
                            
              arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
              arquivo.write("Data: ")
              arquivo.write(data)
              arquivo.write(" ")
              arquivo.write(hs)
              arquivo.write(" Evento: Acesso morador cadastrado")
              arquivo.write("\n")
              arquivo.close()
         
              valido = 1
              pass
              
          if valido == 0:

            print("Usuario não cadastrado")   

            arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
            arquivo.write("Data: ")
            arquivo.write(data)
            arquivo.write(" ")
            arquivo.write(hs)
            arquivo.write(" Evento: Usuário não cadastrado")
            arquivo.write("\n")
            arquivo.close()
                        
            pygame.mixer.music.load('mp3/029.mp3') # Usuario não cadastrado
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
              time.sleep(0.1)

            return valido
          
        return valido,codigo
      
    except:

      print("Não foi possivel fazer a leitura da tag")

      arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
      arquivo.write("Data: ")
      arquivo.write(data)
      arquivo.write(" ")
      arquivo.write(hs)
      arquivo.write(" Evento: Não foi possivel fazer a leitura da tag")
      arquivo.write("\n")
      arquivo.close()
                
      time.sleep(0.1)
      
    pass

def demo(saidaA):

        pygame.mixer.music.load('mp3/104.mp3') # Apresentação 1
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        time.sleep(1)

        pygame.mixer.music.load('mp3/105.mp3') # Apresentação 2
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        time.sleep(1)

        saidaA = saidaA + 0b00000001 #aciona rele 1 (abre portão social)
        bus.write_byte_data(MCP23017,0x014,saidaA)

        pygame.mixer.music.load('mp3/045.mp3') # Abrindo portão social
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        time.sleep(1)

        pygame.mixer.music.load('mp3/106.mp3') # Apresentação 3
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        time.sleep(1)

        saidaA = saidaA - 0b00000001 #aciona rele 1 (fecha portão social)
        bus.write_byte_data(MCP23017,0x014,saidaA)
        
        pygame.mixer.music.load('mp3/055.mp3') # Fechando portão social
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        time.sleep(1)

        
        pygame.mixer.music.load('mp3/107.mp3') # Abrindo eclusa
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        
        time.sleep(1)
        
        saidaA = saidaA + 0b00000010 #abre portão eclusa
        bus.write_byte_data(MCP23017,0x014,saidaA)

        pygame.mixer.music.load('mp3/108.mp3') # 
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        saidaA = saidaA - 0b00000010 #fecha portão eclusa)
        bus.write_byte_data(MCP23017,0x014,saidaA)

        time.sleep(1)

        saidaA = saidaA + 0b00001000 # abre portão da garagem
        bus.write_byte_data(MCP23017,0x014,saidaA)

        pygame.mixer.music.load('mp3/109.mp3') # Abrindo eclusa
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        
        time.sleep(1)

        pygame.mixer.music.load('mp3/110.mp3') # 
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        
        time.sleep(1)

        pygame.mixer.music.load('mp3/111.mp3') # 
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        
        time.sleep(1)

        pygame.mixer.music.load('mp3/112.mp3') # a
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        time.sleep(1)

        saidaA = saidaA - 0b00001000 # Fecha portão da garagem
        bus.write_byte_data(MCP23017,0x014,saidaA)
        

        pygame.mixer.music.load('mp3/113.mp3') # Abrindo eclusa
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        
        time.sleep(1)

        pygame.mixer.music.load('mp3/114.mp3') # Abrindo eclusa
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        
        time.sleep(1)

        
        pygame.mixer.music.load('mp3/020.mp3') # Abrindo eclusa
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        time.sleep(1)
        
        

        return(saidaA)

# Ao descomentar essas linhas o sistema da uma mensagem de boas vindas,
# somente se estiver conectado a internet 

# narrador ("Olá eu sou a assistente de configuração do CLP cia, aguarde um instante, fazendo atualizações")
     
         
#dia_e_hora(hora)
#dia_semana(dia_da_semana)
#narrador("tudo certo!")

cont = 0
energia = 1
aux = 0
periodico = 0

rele1 = 0
rele2 = 0
rele3 = 0
rele4 = 0
rele5 = 0
rele6 = 0
rele7 = 0
rele8 = 0
rele9 = 0
rele10 = 0
rele11 = 0
rele12 = 0
rele13 = 0

global vrg

########################################################### Start das Threads #####################################################

s = threading.Thread(target = servidor_php, args=(saidaA,saidaB,hs,data)) # Inicia o servidor com endereço 172.20.6.14 porta 5510
s.start()

##p1 = threading.Thread(target = periodico_1min) # Envia feed back de temperatura do sistema e tensão de baterias a cada minuto
##p1.start()
##
qr = threading.Thread(target = qr_code) # Inicia a thread QR Code
qr.start()

gr = threading.Thread(target = servidor_gerenciador) 
gr.start()


rst = threading.Thread(target = servidor_reset) # Inicia o servidor para reset
rst.start()

###################################################################################################################################

php = 0
AP01 = 0

      
while(True):    

    
    in0 = GPIO.input(17)  # Configuraçoes de entrada
    in1 = GPIO.input(18)
    in2 = GPIO.input(27)
    in3 = GPIO.input(22)
    in4 = GPIO.input(23)
    in5 = GPIO.input(24)
    in6 = GPIO.input(25)
    in7 = GPIO.input(4)
    b1  = readadc(0)
    b2  = readadc(1)
    pmg = readadc(2)
    ag  = readadc(7)
    
    pm_social = in0      # Configuração de variaveis que fazem leitura das entradas
    pm_eclusa = in1
    ctw_social = in2
    ctw_eclusa = in3
    chave_emergencia = in4
    chave_servico = in5
    falha_energia = in6
    reset_servico = in7
    barreira_1 = b1 # Lê o A0 (Sensor Barreira 1) e registra 0 ou 1 na variavel 
    barreira_2 = b2 # Lê o A1 (Sensor Barreira 2) e registra 0 ou 1 na variavel 
    garagem_aberto = pmg # Lê o A0 (Ponto magnético garagem aberta) in_A0
    abre_garagem = ag # Lê a entrada A7 (requisição de abertura do portão Garagem)

    letra = 0
    codigo = 0
    
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

      vrg = 0
                
      print ("Programa Automático em execução\n")
      bus.write_byte_data(MCP23017,0x014,0b00000000) # Zera as saídas do Port A (inicia reles de 1 -8 desligados)
      bus.write_byte_data(MCP23017,0x015,0b00000000)  # Zera as saídas do Port B (inicia reles 9,10 desligados, saidas 11,12,13 (transistors) desligados
      cont = 1
      
      saidaB = saidaB + 0b00000010 # Liga saida de audio 2 (rele 10)
      bus.write_byte_data(MCP23017,0x015,saidaB)
      
      pygame.mixer.music.load('mp3/048.mp3') # Sistema carregado
      pygame.mixer.music.play()
      while pygame.mixer.music.get_busy():
        time.sleep(0.1)

      time.sleep(1)

      saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
      bus.write_byte_data(MCP23017,0x015,saidaB)

      time.sleep(2)
      
      print(dia_mes,"/",m,"/",y,dia_da_semana)
      print (hora,"hs\n")
      
      saidaB = saidaB - 0b00001000 # desliga LED VERMELHO saida GPB3
      bus.write_byte_data(MCP23017,0x015,saidaB)

##      query = ("SELECT * FROM moradores") # requisita os nomes da tabela moradores
##      cursor.execute(query)
##
##      print ("Lista de moradores cadastrados\n")
##      
##      for (item) in cursor: # imprimi na tela os nomes da tabela moradores
##
##          item = str(item)
##          Id = (item.split(",")[0])
##          ID = (Id.split("(")[1])
##          nome = (item.split(",")[1])
##          nome = (item.split("'")[1])
##          ap = (item.split(",")[2])
##          st = (item.split(",")[3])
##          st = (item.split("'")[3])
##          codigo = (item.split(",")[4])
##          cod = (codigo.split("'")[1])
##          
##          print("ID",ID,nome,"Ap",ap,st,"TAG",cod)
          
      saidaB = saidaB + 0b00000100 # liga LED AZUL saida GPB3
      bus.write_byte_data(MCP23017,0x015,saidaB)
               
      try:

          signal.alarm(3)
          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          s.connect ((host,port))
        
          command = ("7000 189091E30500008")  # COMUNICA O RESET DO SISTEMA
 #        command = ("7000 189091E80000000") # Teste
          s.send(str.encode(command))
          reply = s.recv(1024)
          print(reply.decode('utf-8'))
        
          signal.alarm(0)

      except:

          print("Data: ",data,hs,"Evento: Não conseguiu enviar o evento de auto teste")
          s.close()

    
##      try:
##
##          # Credenciais
##          remetente    = 'leandrolopesleal26@gmail.com'
##          senha        = 'novajesuscr332'
##     
##          # Informações da mensagem
##          destinatario = 'leandrolopesleal26@gmail.com'
##          assunto      = 'O CLP Reiniciou'
##          texto        = 'Esse email foi enviado usando python! :)'
##     
##          # Preparando a mensagem
##          msg = '\r\n'.join([
##            'From: %s' % remetente,
##            'To: %s' % destinatario,
##            'Subject: %s' % assunto,
##            '',
##            '%s' % texto
##            ])
##     
##          # Enviando o email
##          server = smtplib.SMTP('localhost',587)
##          server.starttls()
##          server.login(remetente,senha)
##          server.sendmail(remetente, destinatario, msg)
##          server.quit()
##
##      except Exception as e:
##
##          print("\nNão conseguiu enviar o email\n", e)
##          #server.quit()
##

    if(barreira_1 == 0 or barreira_2 == 0):

      print("Atenção saida de pedestres não permitida")
      
      pygame.mixer.music.load('mp3/026.mp3') #
      pygame.mixer.music.play()
      while pygame.mixer.music.get_busy():
        time.sleep(0.1)
        
      time.sleep(2)
          
    if(ctw_social == 1):       # Abertura do portão social

      intertravamento(saidaA,saidaB,hs,data,0,"")

    if(ctw_eclusa == 1):       # Abertura do portão eclusa

      intertravamento(saidaA,saidaB,hs,data,0,"")

    if(abre_garagem == 0):    # Lógica do portão da garagem

      logica_garagem(saidaA)

    if(garagem_aberto == 1): # Ponto magnético (Garagem aberta)

        if (vrg == 0): # Variavel global definida para comunicação de estado entre Threads

          print ("\nViolação da Garagem\n")

          saidaA = saidaA + 0b10000000 #aciona rele 8 (Giroflex) 
          bus.write_byte_data(MCP23017,0x014,saidaA) 

          saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10) 
          bus.write_byte_data(MCP23017,0x015,saidaB) 

          pygame.mixer.music.load('mp3/053.mp3') # Violação da Garagem 
          pygame.mixer.music.play() 

          while pygame.mixer.music.get_busy(): 
            time.sleep(0.1) 

          try: 

              signal.alarm(3)   
              s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
              s.connect ((host,port)) 

              command = ("7000 189091E13000007")  # Violação portão da garagem 

              s.send(str.encode(command)) 
              reply = s.recv(1024) 
              print(reply.decode('utf-8')) 
              signal.alarm(0) 
 
          except: 

              print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento de violação da Garagem") 

              s.close() 

          arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log 
          arquivo.write("Data: ") 
          arquivo.write(data) 
          arquivo.write(" ") 
          arquivo.write(hs) 
          arquivo.write(" Evento: Violação do portão da Garagem") 
          arquivo.write("\n") 
          arquivo.close() 
      
          time.sleep(3) 

          saidaA = saidaA - 0b10000000 # Desliga rele 8 (Giroflex) 
          bus.write_byte_data(MCP23017,0x014,saidaA) 

          saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10) 
          bus.write_byte_data(MCP23017,0x015,saidaB)
  
    
    if(chave_emergencia ==1): # Chave de emergencia acionada

      emergencia(saidaA,saidaB,hs,data)
        	
    if(chave_servico == 1):    # Chave de serviço

      print("Chave de serviço acionada")
      servico(saidaA,saidaB,hs,data)

    if (falha_energia == 1):

        demo(saidaA)

##        print("Abriu um evento de portaria no Moni")
##
##        try:
##              
##            signal.alarm(3)
##            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##            s.connect ((host,port))
##            
##            command = ("7000 189091E80000000")  # ABRE TELA NO MONI
##
##            s.send(str.encode(command))
##            reply = s.recv(1024)
##            print(reply.decode('utf-8'))
##            
##            signal.alarm(0)
##
##        except:
##
##            print("Data: ",data,hs,"Evento: Não conseguiu abrir um evento de portaria no Moni")
##            s.close()


#        demo(saidaA)
        
##      if aux == 0:
##          
##        print ("Estamos sem energia elétrica")
##
##        try:
##
##          s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##          s.connect ((host,port))
##          
##          command = ("7000 189091E30100000")  # Falha energia elétrica
##          s.send(str.encode(command))
##          reply = s.recv(1024)
##          print(reply.decode('utf-8'))
##
##        except:
##
##          print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Falha de enegia elétrica")
##          s.close()
##  
##        
##        arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
##        arquivo.write("Data: ")
##        arquivo.write(data)
##        arquivo.write(" ")
##        arquivo.write(hs)
##        arquivo.write(" Evento: Estamos sem energia elétrica")
##        arquivo.write("\n")
##        arquivo.close()
##
##        saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
##        bus.write_byte_data(MCP23017,0x015,saidaB)
##                
##        pygame.mixer.music.load('mp3/043.mp3')
##        pygame.mixer.music.play()
##        while pygame.mixer.music.get_busy():
##          time.sleep(0.1)
##        aux = 1
##
##        saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
##        bus.write_byte_data(MCP23017,0x015,saidaB)
##        
##    if (falha_energia == 0 and aux == 1):
##
##      print ("Restauração da energia elétrica")
##
##      try:
##
##        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##        s.connect ((host,port))
##          
##        command = ("7000 189091R30100000")  # Restauração energia elétrica
##        s.send(str.encode(command))
##        reply = s.recv(1024)
##        print(reply.decode('utf-8'))
##
##      except:
##
##        print("Data: ",data, "Hora: ",hs,"Evento: Não enviou o evento Restauração de enegia elétrica")
##        s.close()
##
##      arquivo = open("log_sea.txt", "a+") # Escreve o evento no registro de log
##      arquivo.write("Data: ")
##      arquivo.write(data)
##      arquivo.write(" ")
##      arquivo.write(hs)
##      arquivo.write(" Evento: Restauração da energia elétrica")
##      arquivo.write("\n")
##      arquivo.close()
##
##      saidaB = saidaB + 0b00000010 #aciona saida de audio 2 (rele 10)
##      bus.write_byte_data(MCP23017,0x015,saidaB)
##          
##      pygame.mixer.music.load('mp3/044.mp3')
##      pygame.mixer.music.play()
##      while pygame.mixer.music.get_busy():
##        time.sleep(0.1)
##
##      saidaB = saidaB - 0b00000010 # Desliga saida de audio 2 (rele 10)
##      bus.write_byte_data(MCP23017,0x015,saidaB)
##
##      aux = 0

# Rotina de leitura do leitor de tags a cada 0,1 seg.

          
#    retorno = leitor(ser,saidaA,hs,data)   # Chama a rontina leitor e grava o retorno em "retorno" 
#    valido = retorno               # Atribui o valor de "retorno" a variavel "valido"

    
#    val = str(valido)
#    valido = (val.split(",")[0])
      
        
#    if (valido == "(1") : # Se o cliente estiver cadastrado no banco de dados abre o portão social.

      # Acomunicação do evento para o moni ocorre dentro da rotina intertravamento

#     intertravamento(saidaA,saidaB,hs,data,0)
#      valido = 0
       
    time.sleep(0.1)
