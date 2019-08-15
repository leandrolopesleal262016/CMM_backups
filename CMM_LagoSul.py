#!/home/pi/CMM/bin/python3
# -*- coding:utf-8 -*-

# CMM Oficial com placa de expansão da BRAVAS Technololgy  , criar classes para os outros modulos expansores.
# Desenvolvido por Leandro Leal  rev. 18/07/2019

import biblioteca_CMM as cmm

import time
from datetime import datetime, timedelta
import os     # Executa comandos do sistema operacional Ex.: os.system('sudo reboot now'))
import threading # Modulo superior Para executar as threads
import sys
import socket
import json
import mysql.connector

os.system("mpg123 /home/pi/CMM/mp3/reiniciando_sistema.mp3")

socket.setdefaulttimeout(2) # limite de 2 segundos para enviar o socket

hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
h = int(time.strftime('%H'))
data = time.strftime('%d/%m/%y')

nome = os.popen('hostname').readline()
ip = os.popen('hostname -I').readline()

print("\nNome desta maquina",nome,"com IP",ip)

print("Horario atual",time.strftime("%H:%M:%S"))

############################ INICIA AS CLASSES DA Biblioteca_CMM_Bravas  ########################################

rele = cmm.Rele() # inicia a classe rele com port A em 0
##rele.liga(1)    # Liga rele 1 (podendo ser de 1 a 8)
##rele.desliga(1)  # Desliga rele 1 (podendo ser de 1 a 8)
##rele.pulsa(8,2)  # rele.pulso(rele,tempo)  Pulsa o rele pelo tempo indicado em segundos

entradas = cmm.Entradas()
# Classes para leituras das entradas definidas no arq. config.txt
# Ex. ctw2 = entradas.ctw2
#     qde = entradas.qde                       
#     pm1 = entradas.pm1

saidas = cmm.Saidas()
# Classes para acionamento das saidas definidas no arq. config.txt

narrador = cmm.Narrador()
##narrador.falar("Teste do narrador") # fala o texto enviado - depende de internet
##narrador.gravar("Qrcode não cadastrado","semCadastro") # Grava o texto enviado em nome.mp3

temperatura = cmm.Temperatura()
##print ("\nTemperatura",temperatura.cpu(),"°C\n")  # obter temperatura

email = cmm.Email()
##email.enviar("O Programa acabou de reiniciar\nPosso enviar qualquer mensagem aqui...") # Não usar nenhum caracter especial na mensagem

clima = cmm.Clima()
##tempo = clima.clima_atual()
##print(tempo)

evento = cmm.Evento("0054")
# Inicia a classe para envio de eventos para o Moni com o codigo do cliente

banco = cmm.Banco()
# banco.consulta("tabela","coluna") / banco.atualiza("tabela","coluna","valor")

notifica = cmm.Notifica()
# Condfy - Aviso de QR Code utilizado Ex. notifica.qr_utilizado("2019","83587161") cliete,id do qr utilizado

qr1_garagem = cmm.Qrcode("172.19.1.253","0001",4,"garagem_entrada","1") # IP,Cliente,rele,portao,notificar o condfy) - "172.18.34.247","5987",4,"social" ou "eclusa", "1" notificar o condfy do qrcode usado
qr2_garagem = cmm.Qrcode("172.19.1.249","0001",5,"garagem_saida","0") # IP,Cliente,rele,portao) - "172.18.34.247","5987",4,"social" ou "eclusa"
#qr3 = cmm.Qrcode("172.18.34.249","5987",4,"garagem_entrada") # IP,Cliente,rele,portao) - "172.18.34.247","5987",4,"garagem_entrada" ou "garagem_saida"
#qr4 = cmm.Qrcode("172.18.34.250","5987",5,"garagem_saida") # IP,Cliente,rele,portao) - "172.18.34.247","5987",4,"garagem_entrada" ou "garagem_saida"


##############################################  Threads dos programas  ##########################################################

def thread_qrcode_garagem_1(): # Programa que mantem a conexão com o QR Code

    print("\nPrograma QR Code Garagem entrada em execução\n")

    qr1_garagem.start() # Conecta com o leitor dentro da classe do QR Code

qr_garagem_entrada = threading.Thread(target=thread_qrcode_garagem_1)
qr_garagem_entrada.start()

def thread_qrcode_garagem_2(): # Programa que mantem a conexão com o QR Code

    print("\nPrograma QR Code Garagem saida em execução\n")

    qr2_garagem.start() # Conecta com o leitor dentro da classe do QR Code

qr_garagem_saida = threading.Thread(target=thread_qrcode_garagem_2)
qr_garagem_saida.start()
    

############################################################################################

def Servidor_qr(): ######### Thread servidor Cadastro QR Code ###################

    time.sleep(1)

    deletar = 0
    cadastrar = 0

    host_servidor = '172.19.1.251'  # Host servidor 
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
            s.listen(10)
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
                    corpo = (data.split("&")[1])                   

                    reply = "ok"
                    conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
                    conn.close()

                except Exception as err:

                    print("Dados recebidos estao fora do formato",err)
                    break
    
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

                        print("Vai tentar selecionar na tabela qrcode")

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
                            
                            break

                    break
                    
                if comando == "cadastrar_qr":

                    try:
                       
                        dados = data.replace("cadastrar_qr&","")
                        dados = dados.replace("'",'"')

                    except Exception as err:

                        print("Erro ao formatar os dados para converter em json", err)

                
            #########  Faz o cadastro dos dados recebidos no banco do CMM #######
                    try:

                        
                        dados_json = json.loads(dados)  # Tranforma a string para formato json (dicionario)
                           
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

                    except Exception as err:

                        print("Erro na conversao json",err)
                                       
                    try:                 
  
                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()
                      
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

                        print("\ncadastrado com sucesso ",ID,"\n")                      

                        cnx.close()
                        break                
                 
        s = setupServer()

        while True:
          
          print ("\nEscutando Gerenciador na porta",port_gerenciador,"\n")
          
          try:

              conn = setupConnection()
              dataTransfer(conn) #,saidaA,saidaB,hs)                                         
                
          except:
            
              print("Encerrou conexão com Gerenciador")

def Intertravamento(comando): # Inicia a thread dos portoes sociais importando a classe Rele
        
        entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        
        audio = 0 # Deixa ativo ass mensagens de audio de abertura
        cont = 0

        a = open("/home/pi/CMM/status_social.cmm","r")
        abre_social = a.read()
        a.close()

        b = open("/home/pi/CMM/status_eclusa.cmm","r")
        abre_eclusa = b.read()
        b.close()        
    
        if comando == "abre_social":

            print("Reconheceu o abre_social")

            entradas = cmm.Entradas()
            pm1 = entradas.pm1
                                
            if pm1 == 1: # O portão social já esta aberto

                print("O portão social já esta aberto")
                            
                os.system("mpg123 /home/pi/CMM/mp3/social_aberto.mp3")
                time.sleep(1)

            else: # Se o portão Social esta fechado então pode abrir

                entradas = cmm.Entradas()
                pm2 = entradas.pm2
                                
                if pm2 == 0: # Se Ponto magnético Eclusa fechado
                    
                    s = open("/home/pi/CMM/status_social.cmm","w")
                    s.write("1")
                    s.close()

                    rele.liga(2) # Aqui abrimos o contato da eclusa para impedir que ela seja aberta enquanto o social esta aberto
                    
                    print("Abrindo portão Social")
                    abre.social()

                    if audio == 1: # Ativa as mensagens de abertura e fechamento

                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_social.mp3")                   
                    
                    time.sleep(2) # Tempo minimo para o portão abrir

                    entradas = cmm.Entradas()
                    pm1 = entradas.pm1
                                        
                    if pm1 == 0: # Portão fechado pois não abriu com o comando

                        print("Portão Social emperrado")

                        os.system("mpg123 /home/pi/CMM/mp3/social_emperrado.mp3")
                                                
                        rele.desliga(2) # Fecha o contato e libera a eclusa para ser acionada

                        evento.enviar("E","132","008") # Envia portão emperrado                        

                    if pm1 == 1: # Portão abriu
                        
                        contador = 300 # Tempo maximo para o social ficar aberto 30 segundos
                        print("Esperando por 15 segundos o portão social fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = cmm.Entradas()
                            pm1 = entradas.pm1
                            
                            # Esperando o portão social fechar...
                            
                            if pm1 == 0: # portão fechou

                                print("Portão social fechou")

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
                                
                            entradas = cmm.Entradas()    
                            ctw2 = entradas.ctw2
                            btn2 = entradas.qde
                            
                            if (ctw2 == 0 or btn2 == 0):# and pm1 == 1): # Entrada para abrir o portão da eclusa
                                print("Aguarde o fechamento do social")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Necessario manter esse audio sempre ativo
                                time.sleep(1)
                                
                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1
                            
                entradas = cmm.Entradas()
                pm2 = entradas.pm2
  
                        
        if comando == "abre_eclusa":

            print("Reconheceu o abre_eclusa")

            entradas = cmm.Entradas()
            pm2 = entradas.pm2            

            if pm2 == 1: # O portão Eclusa já esta aberto

                print("O portão Eclusa já esta aberto")

                os.system("mpg123 /home/pi/CMM/mp3/eclusa_aberto.mp3")
                time.sleep(1)

            else: # Se o portão Eclusa esta fechado então pode abrir

                entradas = cmm.Entradas()
                pm2 = entradas.pm2
                pm1 = entradas.pm1

                if pm1 == 0: # Ponto magnético Social fechado, pode abrir a eclusa
                    
                    s = open("/home/pi/CMM/status_eclusa.cmm","w")
                    s.write("1")
                    s.close()

                    rele.liga(1) # Impede o social de abrir enquanto a eclusa esta aberta
                    
                    print("Abrindo portão Eclusa")
                    abre.eclusa()

                    if audio == 1:
                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_eclusa.mp3")
                    
                    time.sleep(3) # Tempo de espera para o portão abrir

                    entradas = cmm.Entradas()
                    pm2 = entradas.pm2
                    
                    if pm2 == 0: # Portão fechado não abriu após o comando

                       print("Portão eclusa emperrado")
                       
                       os.system("mpg123 /home/pi/CMM/mp3/eclusa_emperrado.mp3")
                           
                       rele.desliga(1) # Libera o social para abrir mesmo com a eclusa aberta

                       evento.enviar("E","132","009") # Envia portão emperrado

                    if pm2 == 1: # Portão aberto

                        
                        contador = 300 # Tempo maximo para eclusa ficar aberta 30 segundos
                        print("Esperando por 30 segundos o portão Eclusa fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = cmm.Entradas()
                            pm2 = entradas.pm2
                            
                            # Esperando o portão eclusa fechar...

                            if pm2 == 0: # portão fechou

                                print("Portão Eclusa fechou")

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

                            entradas = cmm.Entradas()
                            ctw1 = entradas.ctw1
                            btn1 = entradas.qbv 

                            if ctw1 == 0 or btn1 == 0: # Alguem esta tentando abrir o social com a eclusa aberta

                                print("Aguarde o fechamento do portão")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Manter esse audio sempre ativo
                                time.sleep(1)
                                

                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1


def Portoes_sociais(Rele): # Programa
    
    sys.stdout.write("\nPrograma Sociais em execução na thread\n")

    saida = 0
        
    while(1):

        entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        
        pm1 = entradas.pm1
        pm2 = entradas.pm2

        btn1 = entradas.qbv        
        btn2 = entradas.qde
        ctw1 = entradas.ctw1
        ctw2 = entradas.ctw2
       
        if ctw1 == 0:

            status = open("/home/pi/CMM/status_social.cmm","w")
            status.write("1")
            status.close()
     
            Intertravamento("abre_social")

            status = open("/home/pi/CMM/status_social.cmm","w")
            status.write("0")
            status.close()

            
        if ctw2 == 0 or btn2 == 0:

            status = open("/home/pi/CMM/status_eclusa.cmm","w")
            status.write("1")
            status.close()

            Intertravamento("abre_eclusa")

            status = open("/home/pi/CMM/status_eclusa.cmm","w")
            status.write("0")
            status.close()

            saida = 1

        if btn1 == 0:

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
                                

class Abre(cmm.Rele): # classe abertura dos portoes registrando no arquivo de controle status_social / status_eclusa

    def social(self):

        status = open("/home/pi/CMM/status_social.cmm","w") # Para não dispara o arrombamento
        status.write("1")
        status.close()

        rele.pulso(4,2) # Pulso para abrir direto o portão sem intertravamento (Social)
        
        print("Abrindo portão social")
               
    def eclusa(self):

        status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não dispara o arrombamento
        status.write("1")
        status.close()        
    
        rele.pulso(5,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)

        print("Abrindo portão eclusa")      
                       

################################################ THREADS ROTINAS #################################################


def Garagem1(Rele): # Inicia a thread do portão da garagem importando a classe Rele

    pass

    
        
def Garagem2(Rele): # Inicia a thread do portão da garagem importando a classe Rele

    pass

    
        
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

        entradas = cmm.Entradas()

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

                cont1 = 300 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 300 segundos (5 min)
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

                cont2 = 300 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 300 segundos (5 min)
                ar2 = 0
                reset_ar2 = 0
                rele.desliga(8)
        
        time.sleep(1)

############################################### Thread servidor p/ PHP e MONI #################################################################

def Servidor(Rele,Abre): 
    
    sys.stdout.write("\nPrograma Servidor em execução\n")
    socket.setdefaulttimeout(9999) # limite tempo socket
    
    host = '0.0.0.0'
    port = 5510

    time.sleep(0.1)

    print("iniciou o servidor")
    
    print("Servidor: ",host, " porta: ", port)

    while(1):        
    

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

                        s2 = cmm.Expansor()    
    
                        s2.liga_rele1_exp1() # Abre Garagem                         
                        time.sleep(3)
                        s2.desliga_rele1_exp1() 
                                                
                        conn.close()
                        

                    elif(comando == "SET5"):
                        print("Abrindo subsolo")

                        s2 = cmm.Expansor()    
    
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

        
def Alarmes(Rele):
    
    sys.stdout.write("\nPrograma Alarmes em execução\n")

    cont1 = 0
    cint2 = 0
    cont3 = 0

    queda_energia = 0
    queda_de_energia = 0
    encerra_queda_de_energia = 0

    quebra_vidro = 0            # variavel de controle    
    quebra_de_vidro = 0         # Variavel para filtro
    encerra_quebra_de_vidro = 0 # Variavel para filtro

    chave_mudanca = 0
    chave_de_mudanca = 0
    encerra_chave_de_mudanca = 0

    while(1):

        entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        qbv = entradas.qbv
        mud = entradas.mud
        qde = entradas.qde

        
        if qbv == 0 and quebra_vidro == 0: # Se o quebra de vidro foi acionado

            # Filtro para ruidos

            cont1 = 10 

            while cont1 > 0:

                entradas = cmm.Entradas() 
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

                quebra_vidro = 1

                evento.enviar("E","132","007") # Envia violação quebra de vidro           

                time.sleep(10)

        if qbv == 1 and quebra_vidro == 1:

            cont1 = 10

            while cont1 > 0: # Filtro para ruidos

                entradas = cmm.Entradas() 
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

                evento.enviar("R","132","007") # Envia violação quebra de vidro

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
                              


        if mud == 0 and chave_mudanca == 0: # Queda de energia

            cont2 = 10

            while cont2 > 0:

                entradas = cmm.Entradas() 
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
                
                evento.enviar("E","132","008") # Envia chave de mudança acionada

                time.sleep(3)

                chave_mudanca = 1

        if mud == 1 and chave_mudanca == 1: # Restaurou energia eletrica

            cont2 = 10

            while cont2 > 0:

                entradas = cmm.Entradas() 
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
                
                os.system("mpg123 /home/pi/CMM/mp3/restaurou_mudanca.mp3")

                evento.enviar("R","132","008") # Envia violação quebra de vidro

                time.sleep(15) # Aguarda os portoes fecharem

                rele.desliga(8) # Desliga sirene

                status = open("/home/pi/CMM/status_social.cmm","w") # Volta o arquivo para zero para ativar a verificação de arrombamento
                status.write("0")
                status.close()

                status = open("/home/pi/CMM/status_eclusa.cmm","w")
                status.write("0")
                status.close()                

                evento.enviar("R","132","008") # Envia restauração chave de mudanca

                time.sleep(3)

                chave_mudanca = 0   
        
        if qde == 0 and queda_energia == 0: # Queda de energia

            cont3 = 20

            while cont3 > 0:

                entradas = cmm.Entradas() 
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

                entradas = cmm.Entradas() 
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
        

def Interface_grafica(): 
    
    sys.stdout.write("\nPrograma do sistema em execução\n")
    
    ihm = cmm.IHM() # Inicia a interface grafica de configuração dos sociais
    
    while(1):

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

                print("Tentanto enviar o evento",evento)

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
                    
                    print("Não conseguiu enviar o evento, sem conexão no momento")
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

intertravamento = Intertravamento(cmm.Rele)
abre = Abre()

####################  Declara as threads dos programas disponiveis  ####################

##entradas = threading.Thread(target=Entradas)
sociais = threading.Thread(target=Portoes_sociais, args=(cmm.Rele,)) # deixar virgula depois do arg 1
garagem1 = threading.Thread(target=Garagem1, args=(cmm.Rele,))
garagem2 = threading.Thread(target=Garagem2, args=(cmm.Rele,))
arrombamento = threading.Thread(target=Arrombamento, args=(cmm.Rele,))
servidor = threading.Thread(target=Servidor_qr)
buffer = threading.Thread(target=Buffer)

alarmes = threading.Thread(target=Alarmes, args=(cmm.Rele,))
interface = threading.Thread(target=Interface_grafica)
##qrcode = threading.Thread(target=thread_qrcode, args=(qrcode,))

######################################### Start dos Programas  #############################################################

##sociais.start() # Inicia o programa dos portões sociais
#garagem1.start() # Inicia o programa do portão de garagem
#garagem2.start() # Inicia o programa do portão de garagem
##arrombamento.start() # Inicia o programa de automação
servidor.start() 
#buffer.start() # Inicia o programa Buffer

##alarmes.start() # In icia a leitura de interrupções (chave de mudança sociais, queda de energia e quebra de vidro)
#interface.start()
##qrcode.start()

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

