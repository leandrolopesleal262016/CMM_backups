#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Alterado em 07/03/2019 15:00 hs

import sys
import threading # Modulo superior Para executar as threads
import json
import mysql.connector # cominica com o mysql no python 3.6
import time
import socket
from lista_clientes import _cliente
from wsgiref.simple_server import make_server
from pyramid.view import view_config
from pyramid.config import Configurator

def log(texto): # Metodo para registro dos eventos no log.txt (exibido na interface grafica)

    try:

        hs = time.strftime("%H:%M:%S") 
        data = time.strftime('%d/%m/%y')

        texto = str(texto)

        escrita = ("{} - {}  Evento:  {}\n").format(data, hs, texto)
        escrita = str(escrita)

        l = open("/var/www/html/log/log.txt","a")
        l.write(escrita)
        l.close()

    except Exception as err:

        l = open("/var/www/html/log.txt","a")
        l.write("Erro na escrita do log")
        l.close()


log("Iniciou o Gerenciador")
print("Em exucucao...visualizar log na interface grafica")

hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log

time.sleep(1)

global deletar_ID
global cadastrar_ID
global enviar

enviar = 0
cadastrar_ID = 0
deletar_ID = 0


####################  Este trecho fica ouvindo os comandos para CADATRAR ou DELETAR pelo ID   ##########

def thread_cadastro():

 
    host = '0.0.0.0'
    port = 5050

    txt = ("Servidor cadastro:",host,"porta:",port)
    log(txt)

   
    def setupServer():
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
        
        try:
            s.bind((host, port))
        except socket.error as msg:
            log(msg)
        return s

    def setupConnection():
        s.listen(5)
        conn, address = s.accept()
        txt =  ("Conectado com: " + address[0] + ":" + str(address[1]))
        log(txt)
        return conn


    def dataTransfer(conn):  # Loop de transferencia e recepcao de dados

        enviar = 0
        
        while True:
             
            data = conn.recv(1024)  # Recebe os dados
            data = data.decode('utf-8')

            txt = ("Dados recebidos do webservice",data)
	    log(txt)
            
            op = str(data.split(":")[0])
            ID_recebido = str(data.split(":")[1])  # ID do QR CODE

            reply = "ok"            
            conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
            conn.close()

            
            if(op == "cadastrar_qr"): # Busca pelo ID no banco de dados e envia pro CMM correspondente

                log("reconheceu cadastrar")
               
                cadastrar_ID = 1
                
                try:

                    log("Cadastrando no CMM...")

                    try:  # Tenta conectar com o banco de dados
        
                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()
                
                          
                    except mysql.connector.Error as err:
                            
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                  
                            log("Alguma coisa esta errada com o nome de usuario ou a senha!")
                            

                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                  
                            log("Esta base de dados nao existe")
                           
                        else:
                                          
                            log(err)                           
                        
                        
                    query = ("SELECT * FROM qrcode")  # Seleciona a tabela qrcode
                    cursor.execute(query)

                    encontrado = 0
                                        
                    for i in cursor: 
                        
                        ID = i[0] # Seleciona o primeiro item da lista recebida do banco (ID)                        

                        if (ID_recebido == ID): # Compara se o ID vindo do request e igual ao do banco   

                                           
                            nome = i[1]
                            ap = i[2]
                            bloco = i[3]
                            cond = i[4]
                            hi = i[5]
                            hf = i[6]
                            di = i[7]
                            df = i[8]
                            ds = i[9]

      			    #nome = nome.encode('utf-8')
			    txt = ("nome vindo banco",nome)
			    log(txt)
                            encontrado = 1

                        if encontrado == 1:

                            #log("Encontrou o id recebido no Banco de Dados")
                            
                            try:

                                #nome = nome.encode('utf-8')
				nome = str(nome)
                                ap = str(ap)
                                bloco = str(bloco)
                                cond = str(cond)
                                hi = str(hi)
                                hf = str(hf)
                                di = str(di)
                                df = str(df)
                                ID = str(ID)
				ds = str(ds)
				
                                arquivo = open("/home/clp/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                                arquivo.write(" Evento: Cadastro de QR Code " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs)
                                arquivo.close()

                                cadastro = {"nome": nome, "ID": ID, "apartamento": ap, "bloco": bloco, "condominio": cond, "hora_inicio":hi, "hora_final": hf, "data_inicio": di, "data_final": df, "dias_semana": ds}
				
                                cnx.close()
                                
                    ####### PROCURA O ID CORRESPONDENTE NA LISTA #########

                                try:

                                    numero = cond
                                    cliente = _cliente(numero) # instancia a lista de enderecos externa

                                    condominio = (cliente[0])
                                    ID_correspondente = (cliente[1])

                                    txt = (condominio,ID_correspondente)
				    log(txt)
				    encontrado = 0

                                except Exception as e:

                                    txt = ("Cadastro: Nao encontrou o cliente correspondente na lista",e)
				    log(txt)
				                                   
                            except Exception as e:

                                log(e)
                                encontrado = 0
                
                
                except Exception as e:

                    txt =  ("Nao conseguiu cadastrar",e)
		    log(txt)
                    
                break
            
            if (op == "deletar_qr"):

                log("reconheceu deletar")

                deletar_ID = 1
     
                try:

                    txt = ("Dados recebidos no delete",data)
		    log(txt)

                    op = str(data.split(":")[0])
                    ID_recebido = str(data.split(":")[1])                    
                    cond = str(data.split(":")[2])

                    txt = ("ID_recebido",ID_recebido,"cond",cond)
		    log(txt)

                except:

                    log("Nao conseguiu dividir a string do delete")

                ####### VERIFICA O CMM CORRESPONDENTE #########

                try:

                    numero = cond
                    cliente = _cliente(numero) # insatancia a lista de enderecos externa

                    condominio = (cliente[0])
                    ID_correspondente = (cliente[1])

                    txt = ("Condominio",condominio,"ID",ID_correspondente)
		    log(txt)

                except Exception as e:

                    txt = ("Nao encontrou o cliente na lista",e)
		    log(txt)
                

##                ########## CRIA WEBSOCKET E ENVIA OS DADOS PARA O CMM CORRESPONDENTE ########

                
                try:

                    host = ID_correspondente
                    port = 5511
                               
                    txt = ("Enviando requisicao %s para o CMM")%op
		    log(txt)
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    
                    remover = ("deletar_qr&" + ID_recebido + ":" + cond)
                    remover = str(remover)

                    command = ("%s")%remover # Dados a serem enviados para o CLP correspondente
                    
                    s.send(str.encode(command))
                    
                    reply = s.recv(1024)
                    txt = (reply.decode('utf-8'))
		    log(txt)

                    s.close()
                                  
                except Exception as e:

                    txt = ("Nao conseguiu enviar para o CMM", e)
		    log(txt)

                    log("Colocando no buffer delete...")

                    try:  # Tenta conectar novamente com o banco de dados
        
                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()
                
                          
                    except mysql.connector.Error as err:
                            
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                  
                            log("Alguma coisa esta errada com o nome de usuario ou a senha!")                           

                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                  
                            log("Esta base de dados nao existe")
                            
                        else:
                                          
                            log(err)
 
                    
                    try:                
            
                        query = ("INSERT INTO buffer_delete (ID, cond) VALUES (%s,%s)")
                        query_data = (ID_recebido,cond)
                        cursor.execute(query, query_data)
                        cnx.commit()

                
                    except Exception as err: # mysql.connector.Error as err:

                        txt = ("Erro na inclusao do banco",err)
			log(txt)                        


                    else:

                        log("Incluido na tabela delete")
			log(txt)

                        ID = str(ID_recebido)

                break
                
                
    s = setupServer()

    while True:
      
      txt = ("GERENCIADOR ESCUTANDO NA PORTA",port)
      log(txt)
      
      try:

          conn = setupConnection()
          dataTransfer(conn) 
                                     
            
      except Exception as e:
        
          log("Encerrou conexao Gerenciador CMM")

####################################  Thread Buffer  ########################################

def buffer():

    ID_1 = 0

    while(1):

        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
            
        try:  # Tenta conectar com o banco de dados
            
            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
            cursor = cnx.cursor()

              
        except mysql.connector.Error as err:
                
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      
                log("Alguma coisa esta errada com o nome de usuario ou a senha!")
               
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
      
                log("Esta base de dados nao existe")
               
            else:
                              
                log(err)                
      
        encontramos = 0

        query = ("SELECT * FROM qrcode WHERE enviado = 0")  # Seleciona a tabela qrcode
        cursor.execute(query)
                            
        for i in cursor:

            ID = i[0]
            nome = i[1]
            ap = i[2]
            bloco = i[3]
            cond = i[4]
            hi = i[5]
            hf = i[6]
            di = i[7]
            df = i[8]
            ds = i[9]
            enviado = i[10]

	    nome = nome.encode('utf-8')
	
	    if enviado == 0:

                encontramos = 1

            if encontramos == 1:

                log("Encontrou na tabela qrcode cadastro ainda nao enviado")

		encontramos = 0
                
                try:
		    
                    nome = str(nome)
                    ap = str(ap)
                    bloco = str(bloco)
                    cond = str(cond)
                    hi = str(hi)
                    hf = str(hf)
                    di = str(di)
                    df = str(df)
                    ID = str(ID)
                    ds = str(ds)
                    enviado = int(enviado)
                   
		    txt = ("nome obtido do banco",nome)
		    log(txt)		    
		    
		    nome = str(nome)

		    #txt = ("nome convertido em utf-8",nome)
		    #log(txt)
                    cadastro = {"nome": nome, "ID": ID, "apartamento": ap, "bloco": bloco, "condominio": cond, "hora_inicio":hi, "hora_final": hf, "data_inicio": di, "data_final": df, "dias_semana": ds}
                   
                    cnx.close()
                    
        ####### PROCURA O ID CORRESPONDENTE NA LISTA #########

                    try:

			txt = ("Numero do cliente recebido do condfy",cond)
			log(txt)

                        numero = cond
                        cliente = _cliente(numero) # insatancia a lista de enderecos externa

                        condominio = (cliente[0])
                        ID_correspondente = (cliente[1])

                        txt = ("Condominio " + condominio + " IP " +  ID_correspondente + " " + nome + " Ap " + ap + " " + bloco)
			log(txt)

                    except Exception as e:

                        if ID == ID_1:

                            pass  #log("Ja registrou cliente nao consta na lista")
                            
                        else:

                            log("Buffer: Nao encontrou o cliente correspondente na lista")

                            arquivo = open("/home/clp/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                            arquivo.write(" Evento: Nao encontrou cliente na lista " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs)
                            arquivo.close()

                            ID_1 = ID

                        pass

                    else:  ########## CRIA WEBSOCKET E ENVIA OS DADOS PARA O CMM CORRESPONDENTE ########

                        try:

                            host = ID_correspondente
                            port = 5511
                               
                            log("Enviando item atraves do buffer para o cliente...")
                            
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect ((host,port))

                            cadastro = str(cadastro)

                            command = ("cadastrar_qr&" + cadastro) # Dados a serem enviados para o CLP correspondente
                            
                            s.send(str.encode(command))
                            
                            reply = s.recv(1024)
                            txt = (reply.decode('utf-8'))
			    log(txt)
                            
                            s.close()
                                          
                        except Exception as e:
                            
                            txt = ("Nao conseguiu enviar para o CMM", e)
			    log(txt)
                            
                        else:

                            txt = ("Enviado evento pelo buffer",hs)
			    log(txt)

                            arquivo = open("/home/clp/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                            arquivo.write(" Evento: Enviado evento para o cliente pelo buffer " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs)
                            arquivo.close()
                            
                            try:

                                try:  # Tenta conectar com o banco de dados
            
                                    cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                                    cursor = cnx.cursor()

                                      
                                except mysql.connector.Error as err:
                                        
                                    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                              
                                        log("Alguma coisa esta errada com o nome de usuario ou a senha!")
                                       
                                    elif err.errno == errorcode.ER_BAD_DB_ERROR:
                              
                                        log("Esta base de dados nao existe")
                                       
                                    else:
                                                      
                                        log(err)
                                       
                                else:

                                    query = ("UPDATE qrcode SET enviado = 1 WHERE ID = %s") %ID 
                                    cursor.execute(query)
                                    cnx.commit()

                                    
                            except mysql.connector.Error as err:

                                txt = ("Erro na atualizacao do valor no campo 'enviado'",err)
				log(txt)
                                
                                break
                               
                            else:

                                log("Atualizado campo 'enviado' para 1")
				log(txt)

                                cnx.close()

                                break
                                
                except Exception as e:

                    log(e)
                    break

	
##############################################  Buffer Delete  ##########################################
                
        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
            
        try:  # Tenta conectar com o banco de dados
            
            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
            cursor = cnx.cursor()

              
        except mysql.connector.Error as err:
                
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      
                log("Alguma coisa esta errada com o nome de usuario ou a senha!")
                
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
      
                log("Esta base de dados nao existe")
                
            else:
                              
                log(err)            
      
        achou = 0

        query = ("SELECT * FROM buffer_delete WHERE enviado = 0")  # Seleciona a tabela qrcode
        cursor.execute(query)
                            
        for i in cursor:

            ID = i[1]
            cond = i[2]
            
            achou = 1

            if achou == 1:

                log("Encontrou na tabela delete_buffer item nao enviado")
                
                try:
                    
                    cond = str(cond)
                    ID = str(ID)                    
                    
                    remover = {"ID": ID,"condominio": cond}

                    cnx.close()
                    
        ####### PROCURA O ID CORRESPONDENTE NA LISTA #########

                    try:

                        numero = cond
                        cliente = _cliente(numero) # insatancia a lista de enderecos externa

                        condominio = (cliente[0])
                        ID_correspondente = (cliente[1])
                       
                        txt = ("Condominio " + condominio + " IP " +  ID_correspondente)
			log(txt)

                    except Exception as e:

                        if ID == ID_1:

                            pass  #log("Ja registrou cliente nao consta na lista")
                            
                        else:

                            log("Delete Nao encontrou o cliente correspondente na lista")

                            arquivo = open("/home/clp/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                            arquivo.write(" Evento: Nao encontrou cliente na lista " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs)
                            arquivo.close()

                            ID_1 = ID

                        pass

                    else:  ########## CRIA WEBSOCKET E ENVIA OS DADOS PARA O CMM CORRESPONDENTE ########

                        try:

                            host = ID_correspondente
                            port = 5511
                              
                            log("Enviando delete atraves do buffer para o cliente...")
                            
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect ((host,port))

                            remover = ("deletar_qr&" + ID + ":" + cond)
                            remover = str(remover)

                            command = ("%s")%remover # Dados a serem enviados para o CLP correspondente
                            
                            s.send(str.encode(command))
                            
                            reply = s.recv(1024)
                            txt = (reply.decode('utf-8'))
			    log(txt)
                            
                            s.close()
                            
                        except Exception as e:
                            
                            txt = ("Nao conseguiu enviar delete para o cliente", e)
			    log(txt)
                            
                        else:

                                                        
                            try:

                                try:  # Tenta conectar com o banco de dados
            
                                    cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                                    cursor = cnx.cursor()

                                      
                                except mysql.connector.Error as err:
                                        
                                    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                              
                                        log("Alguma coisa esta errada com o nome de usuario ou a senha!")
                                       
                                    elif err.errno == errorcode.ER_BAD_DB_ERROR:
                              
                                        log("Esta base de dados nao existe")
                                        
                                    else:
                                                      
                                        log(err)
                                        
                                else:

                                    query = ("UPDATE buffer_delete SET enviado = 1 WHERE ID = %s") %ID 
                                    cursor.execute(query)
                                    cnx.commit()

                                    
                            except mysql.connector.Error as err:

                                txt = ("Erro na atualizacao do valor no campo 'enviado'",err)
				log(txt)
                                
                                break
                                                       

                            else:

                                log("Atualizado campo 'enviado' para 1")
				log(txt)

                                cnx.close()

                                break

                               
                except Exception as e:

                    log(e)
                    break
                
        time.sleep(5)                                



#####################################  THREADS   ############################################

c = threading.Thread(target = thread_cadastro) 
c.start()    

b = threading.Thread(target = buffer) 
b.start() 

#############################################################################################
