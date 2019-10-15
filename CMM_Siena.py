#!/usr/bin/env python3
# coding=UTF-8

# CMM Oficial com placa de expansão da BRAVAS Technololgy
# Desenvolvido por Leandro Leal  rev. 26/09/2019

import RPi.GPIO as GPIO
import time
import biblioteca_CMM as cmm

from datetime import datetime, timedelta
import wiringpi # Biblioteca para usar as GPIO da rasp como saidas ou entradas
import os     # Executa comandos do sistema operacional Ex.: os.system('sudo reboot now'))
import threading # Modulo superior Para executar as threads
import sys
import socket
import _thread as thread

socket.setdefaulttimeout(2) # limite de 2 segundos para enviar o socket


def log(texto): # Metodo para registro dos eventos no log.txt (exibido na interface grafica)

    hs = time.strftime("%H:%M:%S") 
    data = time.strftime('%d/%m/%y')

    texto = str(texto)

    if texto == "*":

        l = open("/var/www/html/log/log.txt","a")
        l.write("\n")
        l.close()

    else:        

        texto = texto.replace("'","")
        texto = texto.replace(",","")
        texto = texto.replace("(","")
        texto = texto.replace(")","")

        escrita = ("{} - {}  Evento:  {}\n").format(data, hs, texto)
        escrita = str(escrita)

        l = open("/var/www/html/log/log.txt","a")
        l.write(escrita)
        l.close()

log("*") # Deixa uma linha em branco no log da interface    
log("Reiniciou o sistema")


os.system("mpg123 /home/pi/CMM/mp3/sistema_carregado.mp3") 

# Imprimi o nome e o IP do equipamento no log da interface
nome = os.popen('hostname').readline()
nome = str(nome)
nome = nome.replace("\n","")
ip = os.popen('hostname -I').readline()
ip = str(ip)
ip = ip.replace("\n","")
txt = ("Nome desta maquina",nome,"com IP",ip)
txt = str(txt)

log(txt)
log("*") # pula uma linha no log


############################ INICIA AS CLASSES DA biblioteca_CMM ###############################################

rele = cmm.Rele() # inicia a classe rele com port A em 0
narrador = cmm.Narrador()
temperatura = cmm.Temperatura()
email = cmm.Email()
clima = cmm.Clima()
entradas = cmm.Entradas() # Classe para leitura das entradas digitais do CMM
saidas = cmm.Saidas()  # Classe para acionamento dos reles e saidas transistorizadas do CMM
evento = cmm.Evento("6639") # Inicia a classe evento com o codigo do cliente
banco = cmm.Banco() # Oprerações CRUD no banco CMM

qr2 = cmm.Qrcode("172.18.36.243","6639",1,"social","1","1","acesso_qr.mp3") # IP,Cliente,rele,portao,notifica) - "172.18.34.247","5987",4,"social" ou "eclusa"
qr1 = cmm.Qrcode("172.18.36.245","6639",1,"eclusa","0","2","acesso_qr.mp3") # IP,Cliente,rele,portao,notifica) - "172.18.34.247","5987",4,"social" ou "eclusa" 172.18.36.245","6639
qr3 = cmm.Qrcode("172.18.36.247","6639",3,"eclusa","0","3","acesso_qr.mp3") # IP,Cliente,rele,portao,notifica) - "172.18.34.247","5987",4,"social" ou "eclusa"
qr4 = cmm.Qrcode("172.18.36.248","6639",3,"eclusa","0","4","acesso_qr.mp3") # IP,Cliente,rele,portao,notifica) - "172.18.34.247","5987",4,"social" ou "eclusa"

# 172.20.9.5 IP qrcode bancada

############################## Intertravamento dos portões sociais #############################################

def thread_qrcode1(): # Programa do QR Code 1

    log("Programa QR Code social entrada em execução")

    qr1.start() # Inicia o qr code do portão social    

def thread_qrcode2(): # Programa do QR Code 2

    log("Programa QR Code social saida em execução")

    qr2.start() # Inicia o qrcode do portão da eclusa
    
def thread_qrcode3(): # Programa do QR Code 3

    log("Programa QR Code eclusa entrada em execução")

    qr3.start() # Inicia o qrcode do portão da eclusa

def thread_qrcode4(): # Programa do QR Code 4

    log("Programa QR Code eclusa saida em execução")

    qr4.start() # Inicia o qrcode do portão da eclusa

def servidor_gerenciador():

    time.sleep(1)

    socket.setdefaulttimeout(999999)

    deletar = 0
    cadastrar = 0

    host_servidor = '172.18.36.252'  # Host servidor SEA (PHP e moni como clientes)
    port_gerenciador = 5511# Servidor para receber dados do gerenciador
    

    print("Ouvindo Gerenciador na porta",port_gerenciador)
    
    while(1):

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

                            print("\nReconheceu cadastrar qrcode")
                           
                            dados = data.replace("cadastrar_qr&","")
                            dados = dados.replace("'",'"')
                            
##                            print("Dados convertidos: ", dados)

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



def Intertravamento(comando): # Inicia a thread dos portoes sociais importando a classe Rele
        
        entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        
        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
        
        audio = 0 # Deixa ativo ass mensagens de audio de abertura
        cont = 0

        a = open("/home/pi/CMM/status_social.cmm","r")
        abre_social = a.read()
        a.close()

        b = open("/home/pi/CMM/status_eclusa.cmm","r")
        abre_eclusa = b.read()
        b.close()        

    
        if comando == "abre_social":

            entradas = cmm.Entradas()
            pm1 = entradas.pm1
                                
            if pm1 == 1: # O portão social já esta aberto

                log("O portão social já esta aberto")
                            
                os.system("mpg123 /home/pi/CMM/mp3/social_aberto.mp3")
                time.sleep(1)

            else: # Se o portão Social esta fechado então pode abrir

                entradas = cmm.Entradas()
                pm2 = entradas.pm2
                                
                if pm2 == 0: # Se Ponto magnético Eclusa fechado
                    
                    s = open("/home/pi/CMM/status_social.cmm","w")
                    s.write("1")
                    s.close()

                    rele.liga(5) # Aqui abrimos o contato da eclusa para impedir que ela seja aberta enquanto o social esta aberto
                    
                    txt = ("Abrindo portão Social")
                    log(txt)
                    abre.social()

                    if audio == 1: # Ativa as mensagens de abertura e fechamento

                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_social.mp3")                   
                    
                    time.sleep(2) # Tempo minimo para o portão abrir

                    entradas = cmm.Entradas()
                    pm1 = entradas.pm1
                                        
                    if pm1 == 0: # Portão fechado pois não abriu com o comando

                        log("Portão Social emperrado")

                        os.system("mpg123 /home/pi/CMM/mp3/social_emperrado.mp3")
                                                
                        rele.desliga(5) # Fecha o contato e libera a eclusa para ser acionada

                        evento.enviar("E","132","008") # Envia portão emperrado                        

                    if pm1 == 1: # Portão abriu

                        evento.enviar("E","133","001") # Envia abriu portão
                        
                        contador = 300 # Tempo maximo para o social ficar aberto 30 segundos
                        log("Esperando por 15 segundos o portão social fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = cmm.Entradas()
                            pm1 = entradas.pm1
                            
                            # Esperando o portão social fechar...
                            
                            if pm1 == 0: # portão fechou

                                log("Portão social fechou")
                                
                                evento.enviar("R","133","001") # Envia fechamento
                                
                                contador = 1
                                                            
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(5) # Fecha o contato e libera a eclusa para ser acionada

                                break

                            if (pm1 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                log("Portão social aberto por muito tempo")
                                
                                evento.enviar("E","132","010") # Envia falha no fechamento social

                                os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                                
                                status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
                                status.write("1")
                                status.close()

                                contador = 0

                                rele.desliga(5) # Fecha o contato e libera a eclusa para ser acionada
                                
                            entradas = cmm.Entradas()    
                            ctw2 = entradas.ctw2
                            btn2 = entradas.qde
                            
                            if (ctw2 == 0 or btn2 == 0):# and pm1 == 1): # Entrada para abrir o portão da eclusa
                                log("Agurade o fechamento do social")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Necessario manter esse audio sempre ativo
                                time.sleep(1)
                                
                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1
                            
                entradas = cmm.Entradas()
                pm2 = entradas.pm2
  
                        
        if comando == "abre_eclusa":

            entradas = cmm.Entradas()
            pm2 = entradas.pm2            

            if pm2 == 1: # O portão Eclusa já esta aberto

                log("O portão Eclusa já esta aberto")

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

                    rele.liga(6) # Impede o social de abrir enquanto a eclusa esta aberta
                    
                    txt = ("Abrindo portão Eclusa")
                    log(txt)
                    abre.eclusa()
                                        

                    if audio == 1:
                        os.system("mpg123 /home/pi/CMM/mp3/abrindo_eclusa.mp3")
                    
                    time.sleep(2) # Tempo de espera para o portão abrir

                    entradas = cmm.Entradas()
                    pm2 = entradas.pm2
                    
                    if pm2 == 0: # Portão fechado não abriu após o comando

                       log("Portão eclusa emperrado")
                       
                       os.system("mpg123 /home/pi/CMM/mp3/eclusa_emperrado.mp3")
                            
                       rele.desliga(6) # Libera o social para abrir mesmo com a eclusa aberta

                       evento.enviar("E","132","009") # Envia portão emperrado

                    if pm2 == 1: # Portão aberto

                        evento.enviar("E","133","003") # Envia abertura
                        
                        contador = 300 # Tempo maximo para eclusa ficar aberta 30 segundos
                        log("Esperando por 30 segundos o portão Eclusa fechar...")

                        while contador > 0: # enquanto portão está aberto

                            entradas = cmm.Entradas()
                            pm2 = entradas.pm2
                            
                            # Esperando o portão eclusa fechar...

                            if pm2 == 0: # portão fechou

                                log("Portão Eclusa fechou")
                                
                                evento.enviar("R","133","003") # Envia fechamento
                                
                                contador = 1
                                
                                s = open("/home/pi/CMM/status_social.cmm","w")
                                s.write("0")
                                s.close()

                                rele.desliga(6) # Libera o social para abrir

                                break

                            if (pm2 == 1 and contador == 1): # Portão ainda aberto após 15 segundos de espera

                                log("Portão Eclusa aberto por muito tempo")
                                
                                evento.enviar("E","132","011") # Envia falha no fechamento
                                
                                os.system("mpg123 /home/pi/CMM/mp3/obstrucao.mp3")
                                
                                status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
                                status.write("1")
                                status.close()                                

                                rele.desliga(6) # Libera o social para abrir mesmo com a eclusa aberta

                                contador = 0

                            entradas = cmm.Entradas()
                            ctw1 = entradas.ctw1
                            

                            if ctw1 == 0 : # Alguem esta tentando abrir o social com a eclusa aberta

                                log("Aguarde o fechamento do portão")
                                os.system("mpg123 /home/pi/CMM/mp3/aguarde_fechamento.mp3") # Manter esse audio sempre ativo
                                time.sleep(1)
                                

                            time.sleep(0.1) # 1 segundo
                            contador = contador - 1


def Portoes_sociais(Rele): # Programa
    
    log("Programa Sociais em execução ")

    saida = 0
    banco = cmm.Banco()

    entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        
    pm1 = entradas.pm1
    pm2 = entradas.pm2

    qbv = wiringpi.digitalRead(306) # leitura direta IN7     
        
    ctw1 = entradas.ctw1
    ctw2 = entradas.ctw2
    

    quebra = 0
           
    while(1):

        habilita_intertravamento = banco.consulta("intertravamento","habilitado")

        entradas = cmm.Entradas() # Inicia classe para leitura das entradas
        
        pm1 = entradas.pm1
        pm2 = entradas.pm2

        qbv = wiringpi.digitalRead(306) # leitura direta IN7        
        
        ctw1 = entradas.ctw1
        ctw2 = entradas.ctw2

##        banco = Banco()

        ihm_soc1 = banco.consulta("comandos","abre_social_externo")
        ihm_soc2 = banco.consulta("comandos","abre_social_interno")
       
        if ctw1 == 0 or ihm_soc1 == "1":

            if quebra == 1:

                log("Os portes ainda estão abertos pelo quebra de vidro")
                os.system("mpg123 /home/pi/CMM/mp3/quebra_esta_acionado.mp3")

            else:

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

            if quebra == 1:

                log("Os portes ainda estão abertos pelo quebra de vidro")
                os.system("mpg123 /home/pi/CMM/mp3/quebra_esta_acionado.mp3")

            else:

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
                
        if qbv == 0 and quebra == 0:

            log("Quebra de vidro acionado")            
                            
            status = open("/home/pi/CMM/status_eclusa.cmm","w")
            status.write("1")
            status.close()            

            status = open("/home/pi/CMM/status_social.cmm","w")
            status.write("1")
            status.close()

            os.system("mpg123 /home/pi/CMM/mp3/chave_emergencia.mp3")

            
            rele.liga(1)
            rele.liga(3)

            evento.enviar("E","132","005")

            quebra = 1


        if qbv == 1 and quebra == 1:            

            status = open("/home/pi/CMM/status_eclusa.cmm","w")
            status.write("1")
            status.close()            

            status = open("/home/pi/CMM/status_social.cmm","w")
            status.write("1")
            status.close()

            os.system("mpg123 /home/pi/CMM/mp3/restaurada_emergencia.mp3")

            log("Quebra de vidro restaurado")

            rele.desliga(1)
            rele.desliga(3)

            evento.enviar("R","132","005")

            quebra = 0

                        
        time.sleep(0.1)        
                                

class Abre(cmm.Rele): # classe abertura dos portoes registrando no arquivo de controle status_social / status_eclusa

    def social(self):

        status = open("/home/pi/CMM/status_social.cmm","w") # Para não disparar o arrombamento
        status.write("1")
        status.close()

        rele.pulso(1,2) # Pulso para abrir direto o portão sem intertravamento (Social)
        log("Abrindo social...")
        
    def eclusa(self):

        status = open("/home/pi/CMM/status_eclusa.cmm","w") # Para não disparar o arrombamento
        status.write("1")
        status.close()        
    
        rele.pulso(3,2) # Pulso para abrir direto o portão sem intertravamento (Eclusa)
        log("Abrindo eclusa...")
        
########################################## Métodos de acesso a classe leitor #####################################

def leitor(entrada):

    l = cmm.Leitor()

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

    log("Programa Garagem Terreo em execução ")
    
    s = cmm.Expansor()
    
    s.desliga_rele4_exp1() # Garante que a sirene esteja desligada
    s.desliga_rele3_exp1() # Garante que sinaleira esteja com sinal vermelho (NF)
    s.desliga_rele2_exp1() # Garante que o Foto esteja desligado
    s.desliga_rele1_exp1() # Garante que o Abre esteja desligado

##    s.liga_rele3_exp1() # Sinal Verde (Sinaleira)
##    s.desliga_rele3_exp1() # Sinal Vermelho (Sinaleira)
    

    banco = cmm.Banco()
            
    while(1):

        hs = time.strftime("%H:%M:%S")
        s = cmm.Expansor()
    
        ihm_gar1 = banco.consulta("comandos","abre_garagem") # Valor inserido pelo botão da interface       
        tx1 =  leitor("leitor1_in3")  # Cantato abre vindo do TX (LINEAR HCS)
                
        if (tx1 == 1 or ihm_gar1 == "1"):    # Se o tx ou o botão da interface mandou abrir o portão

            time.sleep(0.1)

            tx1 =  leitor("leitor1_in3")
            ihm_gar1 = banco.consulta("comandos","abre_garagem")

            if (tx1 == 1 or ihm_gar1 == "1"): # O tx da linear está direto no abre do portão

                time.sleep(0.1)
                tx1 =  leitor("leitor1_in3")

                if tx1 == 1:

                    log("Reconheceu tx Garagem") # Se reconheceu o tx, é porque o portão ja esta abrindo

                    s.liga_rele3_exp1() # Sinal Verde (Sinaleira)    

                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                    status.write("1")
                    status.close()

                if ihm_gar1 == "1": # Abre através do expansor (rele 1)

                    log("Reconheceu abre Garagem Interface pela gráfica")

                    s.liga_rele3_exp1() # Sinal Verde (Sinaleira)

                    status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                    status.write("1")
                    status.close()

                    s.liga_rele1_exp1()
                    time.sleep(2)
                    s.desliga_rele1_exp1()
                    

                banco.atualiza("comandos","abre_garagem","0")                

                time.sleep(3) # Tempo para começar a abrir o portão

                pmg1 = leitor("leitor1_in1")

                cont = 300     # Tempo maximo para deixar o portão aberto (300 = 30 segundos)
                
                if pmg1 == 1: # Portão não abriu apos o comando

                    time.sleep(0.1)
                    pmg1 = leitor("leitor1_in1")

                    if pmg1 == 1: # Portão não abriu apos o comando

                        log("Portão garagem não abriu")

                        s.desliga_rele3_exp1() # Sinal Vermelho
                        
                        evento.enviar("E","132","015") # Emperrado
                        
                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                        status.write("0")
                        status.close()
                                            
                        cont = 0

                if pmg1 == 0: # Portão abriu

                    time.sleep(0.1)                    
                    pmg1 = leitor("leitor1_in1")

                    if pmg1 == 0: # Confirmado que o Portão abriu

                        evento.enviar("E","133","013")

                        while cont > 0:   # Enquanto o portão esta aberto verifica

                            if cont == 300:

                                log("Portão Garagem abriu")
                            
                            pmg1 = leitor("leitor1_in1")
                            
                            if pmg1 == 1: # Se o portão ja fechou

                                log("Portão Garagem fechou")

                                s.desliga_rele3_exp1() # Sinal Vermelho

                                status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                                status.write("0")
                                status.close()
                                
                                evento.enviar("R","133","013") # Envia o evento de fechamento para a central

                                time.sleep(1)

                                
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

                                    s.desliga_rele3_exp1() # Sinal Vermelho
                                    
                                    pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico
                                    
                                    if pmg1 == 0: # Portão ainda aberto

                                        pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico

                                        log("Aguardando portão Garagem fechar")

                                        temp = 300

                                        while temp > 30:  # Enquanto o portão ainda está aberto e tempo menor que 30 seg                         

                                            pmg1 = leitor("leitor1_in1") # Faz a leitura do ponto magnetico
                                            bar1 = leitor("leitor1_in2") # Faz a leitura da barreira 1
                                            tx1 =  leitor("leitor1_in3")  # Cantato abre vindo do TX (LINEAR HCS)  

                                            if bar1 == 1: # Dupla passagem

                                                time.sleep(0.2)
                                                bar1 = leitor("leitor1_in2")

                                                if bar1 == 1:

                                                    log("Dupla passagem Garagem")                                                

                                                    evento.enviar("E","132","016")

                                                    s.liga_rele4_exp1() # Sirene                                            
                                                    time.sleep(10)
                                                    s.desliga_rele4_exp1()                                            

                                                    break

                                            if tx1 == 1: # Alguem acionou o controle enquanto o portão fechava

                                                log("Reconheceu abre Garagem enquanto o portão estava aberto")
                                                
                                                s.liga_rele3_exp1() # Sinal Verde

                                                temp = 0
                                                
                                                break # Sai da função e inicia novamente a verificação

##                                            
                                     
                                            if pmg1 == 1: # portão ja fechou

                                                log("Portão Garagem fechou")
                                                s.desliga_rele3_exp1() # Sinal vermelho
                                                break

                                            temp = temp - 1
                                            time.sleep(0.1)

##                                    time.sleep(1)                                

                            cont = cont - 1
                            time.sleep(0.1)

                    if cont == 1: # Passaram se 29 segundos e o portão não fechou

                        log("Portão Garagem aberto muito tempo")

                        s.desliga_rele3_exp1() # Sinal Vermelho

                        status = open("/home/pi/CMM/status_garagem_1.cmm","w") 
                        status.write("0")
                        status.close()

                        evento.enviar("E","132","026") # Envia evento de portão aberto (obstrução do fechamento)
                        
                        cont = 0
                        break
        time.sleep(0.1)
        
def Garagem2(Rele): # Inicia a thread do portão da garagem importando a classe Rele

    log("Programa Garagem Subsolo em execução ")

    s2 = Expansor()    
    
    s2.desliga_rele4_exp7() # Garante que a sirene esteja desligada
    s2.desliga_rele1_exp7() # Garante que o Abre esteja desligado
    s2.desliga_rele2_exp7() # Garante que o Foto esteja desligado

    banco = cmm.Banco()
            
    while(1):

        hs = time.strftime("%H:%M:%S")        
        s2 = Expansor()

        ihm_gar2 = banco.consulta("comandos","abre_subsolo")        
        tx2 =  leitor("leitor7_in3")  # Cantato abre vindo do TX (LINEAR HCS)               
        
        if (tx2 == 1 or ihm_gar2 == "1"):    # Se o tx mandou abrir o portão

            time.sleep(0.1)

            tx2 =  leitor("leitor7_in3")

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
                    
                    evento.enviar("E","132","019")
                    
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
                                    
                                # Passou alguem Subsolo, verificando dupla passagem...

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

                                                evento.enviar("E","132","020")

                                                s2.liga_rele4_exp7() # Sirene
                                                time.sleep(10)
                                                s2.desliga_rele4_exp7()

                                                break

                                        if tx2 == 1: # Alguem acionou o controle enquanto o portão fechava

                                            cont = 0
                                            
                                            break # Sai da função e inicia novamente a verificação

                                        time.sleep(0.1)
                                        
                                # Fim do cilo Subsolo

                                time.sleep(1)

                        cont = cont - 1
                        time.sleep(0.2)

                    if cont == 1: # Passaram se 29 segundos e o portão não fechou

                        log("Portão Subsolo aberto muito tempo")

                        status = open("/home/pi/CMM/status_garagem_2.cmm","w") 
                        status.write("0")
                        status.close()

                        evento.enviar("E","132","027")# Envia evento de portão aberto
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

                cont1 = 350 # Se apos o reset o portão continuar aberto envia o evento novamente  espera 5 min
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

                cont2 = 350 # Se apos o reset o portão continuar aberto envia o evento novamente e espera 5 min
                ar2 = 0
                reset_ar2 = 0
                rele.desliga(8)

        
        time.sleep(2)   

def Servidor(Rele,Abre): 
    
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
                        
                        rele.liga(1)

                        time.sleep(2)

                        rele.desliga(1)

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
                        
                        rele.liga(2)

                        time.sleep(2)

                        rele.desliga(2)

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

        s = cmm.Expansor()

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

                s.liga_rele3_exp1() # Sinal Verde

                evento.enviar("E","132","25")                

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

                s.desliga_rele3_exp1() # Sinal Vermelho

                evento.enviar("R","132","25")
                                
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

                        s.desliga_rele3_exp1() # Sinal Vermelho

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

                s.desliga_rele3_exp1() # Sinal Vermelho

                s.liga_rele4_exp1() # Sirene
                            
                evento.enviar("E","132","014") # violação do portão garagem

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
                                            
                evento.enviar("E","132","018")

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

                # Tentanto enviar o evento",evento...

                try:
        
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = (evento + "\r") # ("7000 185808E30500008")  # Envia abriu portão da eclusa para a central de monitormento
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    log(reply.decode('utf-8'))
                    s.close()

                    enviado = 1                    
                                
                except Exception as err: ## Não conseguiu enviar o evento, sem conexão no momento                    

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

intertravamento = Intertravamento(cmm.Rele)
abre = Abre()

####################  Declara as threads dos programas disponiveis  ####################

sociais = threading.Thread(target=Portoes_sociais, args=(cmm.Rele,)) # deixar virgula depois do arg 1
garagem1 = threading.Thread(target=Garagem1, args=(cmm.Rele,))
garagem2 = threading.Thread(target=Garagem2, args=(cmm.Rele,))
arrombamento = threading.Thread(target=Arrombamento, args=(cmm.Rele,))
servidor = threading.Thread(target=Servidor, args=(cmm.Rele,Abre,))
buffer = threading.Thread(target=Buffer)

gerenciador = threading.Thread(target=servidor_gerenciador)

alarmes1 = threading.Thread(target=Alarmes_garagem_1, args=(cmm.Rele,))
alarmes2 = threading.Thread(target=Alarmes_garagem_1, args=(cmm.Rele,))

qrcode1 = threading.Thread(target=thread_qrcode1)
qrcode2 = threading.Thread(target=thread_qrcode2)
qrcode3 = threading.Thread(target=thread_qrcode3)
qrcode4 = threading.Thread(target=thread_qrcode4)
######################################### Start dos Programas  #############################################################

sociais.start() # Inicia o programa dos portões sociais
garagem1.start() # Inicia o programa do portão de garagem
##garagem2.start() # Inicia o programa do portão de garagem
arrombamento.start() # Inicia o programa de automação
#servidor.start() 
buffer.start() # Inicia o programa Buffer
alarmes1.start() # Inicia a leitura de "interrupções" (chave de mudança garagem1 e arrombamento de portões)
##alarmes2.start()
gerenciador.start()
qrcode1.start()
qrcode2.start()
qrcode3.start()
qrcode4.start()

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

log("Temperatura do processador " + str(temperatura.cpu()) + "°C\n")  # obter temperatura
log("*")


while(1):

    reset = banco.consulta("comandos","reset")

    if reset == "1":

        banco.atualiza("comandos","reset","0")
        log("Reconheceu pedido de reset do sistema")

        os.system("mpg123 /home/pi/CMM/mp3/reiniciando_sistema.mp3")

        time.sleep(4)

        os.system("sudo reboot now")

        
    

    time.sleep(1)

