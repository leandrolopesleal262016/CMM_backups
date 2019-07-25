#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Alterado em 07/03/2019 15:00 hs

import sys
import threading # Modulo superior Para executar as threads
import json
import mysql.connector # cominica com o mysql no python 3.6
import time
import socket
import signal # Bibloteca para uso do time out
from lista_clientes import _cliente

from wsgiref.simple_server import make_server
from pyramid.view import view_config

from pyramid.config import Configurator


print("Iniciou o Gerenciador\n")

hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log

time.sleep(1)

global deletar_ID
global cadastrar_ID
global enviar

enviar = 0
cadastrar_ID = 0
deletar_ID = 0

def timeout(signum, frame):

    print ("Excedeu o tempo esperado")
    return

####################  Este trecho fica ouvindo os comandos para CADATRAR ou DELETAR pelo ID   ##########

def thread_cadastro():

##    global deletar_ID
##    global cadastrar_ID
 
    host = '0.0.0.0'
    port = 5050

    print("Servidor cadastro:",host,"porta:",port)

   
    def setupServer():
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # "AF_NET" trabalharemos com protocolo ipv4, .SOCK_STREAM USAREMOS TCP
        
        try:
            s.bind((host, port))
        except socket.error as msg:
            print (msg)
        return s

    def setupConnection():
        s.listen(2)
        conn, address = s.accept()
        print ("Conectado com: " + address[0] + ":" + str(address[1]), "\n")
        return conn


    def dataTransfer(conn):  # Loop de transferencia e recepcao de dados

        enviar = 0
        
        while True:
             
            data = conn.recv(1024)  # Recebe os dados
            data = data.decode('utf-8')

            print("Dados recebidos do webservice",data)
            
            op = str(data.split(":")[0])
            ID_recebido = str(data.split(":")[1])  # ID do QR CODE

            reply = "ok"            
            conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
            conn.close()

            
            if(op == "cadastrar"): # Busca pelo ID no banco de dados e envia pro CMM correspondente

                print("\nreconheceu cadastrar\n")
               
                cadastrar_ID = 1
##
##                reply = "ok"            
##                conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
##                conn.close()

                
                try:

                    print ("\nCadastrando no CMM...\n")

                    try:  # Tenta conectar com o banco de dados
        
                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()
                
                          
                    except mysql.connector.Error as err:
                            
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                  
                            print("Alguma coisa esta errada com o nome de usuario ou a senha!")

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write(" Evento: Banco de Dados: Usuario ou senha invalidos\n")
                            arquivo.close()

                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                  
                            print("Esta base de dados nao existe")

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write(" Evento: Banco de Dados: A base de dados nao existe\n")
                            arquivo.close()

                        else:
                                          
                            print(err)

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write(" Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                            arquivo.close()
                                        
                            time.sleep(0.1)
                                  
                            pass
                        
                        
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

                            encontrado = 1


                        if encontrado == 1:

                            print("Encontrou o id recebido no Banco de Dados")
                            
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
				
                                arquivo = open("qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                                arquivo.write(" Evento: Cadastro de QR Code " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                                arquivo.close()

                                cadastro = {"nome": nome, "ID": ID, "apartamento": ap, "bloco": bloco, "condominio": cond, "hora_inicio":hi, "hora_final": hf, "data_inicio": di, "data_final": df, "dias_semana": ds}

                                cnx.close()
                                
                    ####### PROCURA O ID CORRESPONDENTE NA LISTA #########

                                try:

                                    numero = cond
                                    cliente = _cliente(numero) # insatancia a lista de enderecos externa

                                    condominio = (cliente[0])
                                    ID_correspondente = (cliente[1])

                                    print(condominio,ID_correspondente)

                                except Exception as e:

                                    print("Nao encontrou o cliente correspondente na lista")
                                    

                                else:  ########## CRIA WEBSOCKET E ENVIA OS DADOS PARA O CMM CORRESPONDENTE ########

                                    try:

                                        host = ID_correspondente
                                        port = 5511
                                           
                                        print("\nEnviando requisicao para o CMM\n")
                                        
                                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                        s.connect ((host,port))

                                        cadastro = str(cadastro)

                                        command = ("cadastrar&" + cadastro) # Dados a serem enviados para o CLP correspondente
                                        
                                        s.send(str.encode(command))
                                        
                                        reply = s.recv(1024)
                                        print(reply.decode('utf-8'))
                                        
                                        s.close()
                                                      
                                    except Exception as e:
                                        
                                        print("\nNao conseguiu enviar para o CMM\n", e)

                                    else:

                                        try:  # Tenta conectar novamente com o banco de dados
        
                                            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                                            cursor = cnx.cursor()
                                    
                                              
                                        except mysql.connector.Error as err:
                                                
                                            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                                      
                                                print("Alguma coisa esta errada com o nome de usuario ou a senha!")

                                                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                                arquivo.write(" Evento: Banco de Dados: Usuario ou senha invalidos\n")
                                                arquivo.close()

                                            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                                      
                                                print("Esta base de dados nao existe")

                                                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                                arquivo.write(" Evento: Banco de Dados: A base de dados nao existe\n")
                                                arquivo.close()

                                            else:
                                                              
                                                print(err)

                                                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                                arquivo.write(" Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                                                arquivo.close()
                                                            
                                                time.sleep(0.1)
                                                      
                                                pass
                                            
                                            
                                        query = ("SELECT * FROM qrcode")  # Seleciona a tabela qrcode
                                        cursor.execute(query)

                                        encontrou = 0
                                                            
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

                                                encontrou = 1


                                            if encontrou == 1:

                                                print("Encontrou o id recebido no Banco de Dados")
                                                
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
                                                    
                                                    arquivo = open("qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                                                    arquivo.write(" Evento: Cadastro de QR Code " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                                                    arquivo.close()

                                                    cadastro = {"nome": nome, "ID": ID, "apartamento": ap, "bloco": bloco, "condominio": cond, "hora_inicio":hi, "hora_final": hf, "data_inicio": di, "data_final": df, "dias_semana": ds}

                                                except:

                                                    print("Erro na divisao da string")

                                        try:

                                            query = ("UPDATE qrcode SET enviado = 1 WHERE ID = %s") %ID 
                                            cursor.execute(query)
                                            cnx.commit()

                                                
                                        except mysql.connector.Error as err:

                                            print("Erro na atualizacao do banco",err)
                                            break
                                                

                                        else:

                                            print("\nAtualizado campo 'enviado' para 1\n")

                                            cnx.close()
                                            break
           
                            except Exception as e:

                                print (e)
                                encontrou = 0
                
                
                except Exception as e:

                    print ("\nNao conseguiu cadastrar\n",e)
                    
                break
            
            if (op == "deletar"):

                print("\nreconheceu deletar\n")

                deletar_ID = 1

##                reply = "ok"            
##                conn.sendall(str.encode(reply))  # Envia o reply de volta para o cliente  
##                conn.close()
     
                try:

                    print("Dados recebidos no delete",data)

                    op = str(data.split(":")[0])
                    ID_recebido = str(data.split(":")[1])                    
                    cond = str(data.split(":")[2])

                    print("ID_recebido",ID_recebido,"cond",cond)

                except:

                    print("Nao conseguiu dividir a string do delete")

                ####### VERIFICA O CMM CORRESPONDENTE #########

                try:

                    numero = cond
                    cliente = _cliente(numero) # insatancia a lista de enderecos externa

                    condominio = (cliente[0])
                    ID_correspondente = (cliente[1])

                    print("Condominio",condominio,"ID",ID_correspondente)

                except Exception as e:

                    print("\nNao encontrou o cliente na lista\n",e)

                

##                ########## CRIA WEBSOCKET E ENVIA OS DADOS PARA O CMM CORRESPONDENTE ########

                
                try:

                    host = ID_correspondente
                    port = 5511
                               
                    print("\nEnviando requisicao %s para o CMM\n")%op
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    
                    remover = ("deletar&" + ID_recebido + ":" + cond)
                    remover = str(remover)

                    command = ("%s")%remover # Dados a serem enviados para o CLP correspondente
                    
                    s.send(str.encode(command))
                    
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))

                    s.close()
                                  
                except Exception as e:

                    print("\nNao conseguiu enviar para o CMM\n", e)

                    print("Colocando no buffer delete...")

                    try:  # Tenta conectar novamente com o banco de dados
        
                        cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                        cursor = cnx.cursor()
                
                          
                    except mysql.connector.Error as err:
                            
                        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                  
                            print("Alguma coisa esta errada com o nome de usuario ou a senha!")

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write(" Evento: Banco de Dados: Usuario ou senha invalidos\n")
                            arquivo.close()

                        elif err.errno == errorcode.ER_BAD_DB_ERROR:
                  
                            print("Esta base de dados nao existe")

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write(" Evento: Banco de Dados: A base de dados nao existe\n")
                            arquivo.close()

                        else:
                                          
                            print(err)

                            arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                            arquivo.write(" Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                            arquivo.close()
                                        
                            time.sleep(0.1)
                                  
                            pass
                        
                        
##                    query = ("SELECT * FROM buffer_delete")  # Seleciona a tabela qrcode
##                    cursor.execute(query)
##
                     
                    
                    try:                
            
                        query = ("INSERT INTO buffer_delete (ID, cond) VALUES (%s,%s)")
                        query_data = (ID_recebido,cond)
                        cursor.execute(query, query_data)
                        cnx.commit()

                
                    except Exception as err: # mysql.connector.Error as err:

                        print("Erro na inclusao do banco",err)
                        

##                        if err.errno == 1062:
##
##                            print("ID ja esta na tabela delete")
##                            
##                            
##                        else:

##                          print("Erro na inclusão do banco",err)


                    else:

                        print("\nIncluido na tabela delete\n")

                        ID = str(ID_recebido)

                         
##                    break           
                    
                break
                
                
    s = setupServer()

    while True:
      
      print ("\nGERENCIADOR ESCUTANDO NA PORTA",port, "\n")
      
      try:

          conn = setupConnection()
          dataTransfer(conn) 
                                     
            
      except Exception as e:
        
          print("Encerrou conexao Gerenciador CMM")

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
      
                print("Alguma coisa esta errada com o nome de usuario ou a senha!")

                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                arquivo.write(" Evento: Banco de Dados: Usuario ou senha invalidos\n")
                arquivo.close()

            elif err.errno == errorcode.ER_BAD_DB_ERROR:
      
                print("Esta base de dados nao existe")

                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                arquivo.write(" Evento: Banco de Dados: A base de dados nao existe\n")
                arquivo.close()

            else:
                              
                print(err)

                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                arquivo.write(" Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                arquivo.close()
                            
                time.sleep(0.1)
                      
                pass
            
      
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

            encontramos = 1


            if encontramos == 1:

                print("\nEncontrou na tabela qrcode cadastro ainda nao enviado")
                
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
                    
                    cadastro = {"nome": nome, "ID": ID, "apartamento": ap, "bloco": bloco, "condominio": cond, "hora_inicio":hi, "hora_final": hf, "data_inicio": di, "data_final": df, "dias_semana": ds}
                    
                    cnx.close()
                    
        ####### PROCURA O ID CORRESPONDENTE NA LISTA #########

                    try:

                        numero = cond
                        cliente = _cliente(numero) # insatancia a lista de enderecos externa

                        condominio = (cliente[0])
                        ID_correspondente = (cliente[1])

                        print("\nCondominio " + condominio + " IP " +  ID_correspondente + " " + nome + " Ap " + ap + " " + bloco)

                    except Exception as e:

                        if ID == ID_1:

                            pass  #print("Ja registrou cliente nao consta na lista")
                            
                        else:

                            print("Nao encontrou o cliente correspondente na lista")

                            arquivo = open("qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                            arquivo.write(" Evento: Nao encontrou cliente na lista " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                            arquivo.close()

                            ID_1 = ID

                        pass

                    else:  ########## CRIA WEBSOCKET E ENVIA OS DADOS PARA O CMM CORRESPONDENTE ########

                        try:

                            host = ID_correspondente
                            port = 5511
                               
                            print("\nEnviando item atraves do buffer para o cliente...\n")
                            
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect ((host,port))

                            cadastro = str(cadastro)

                            command = ("cadastrar&" + cadastro) # Dados a serem enviados para o CLP correspondente
                            
                            s.send(str.encode(command))
                            
                            reply = s.recv(1024)
                            print(reply.decode('utf-8'))
                            
                            s.close()
                                          
                        except Exception as e:
                            
                            print("\nNao conseguiu enviar para o CMM\n", e)

                            
                        else:

                            print("Enviado evento pelo buffer",hs)

                            arquivo = open("qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                            arquivo.write(" Evento: Enviado evento para o cliente pelo buffer " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                            arquivo.close()
                            
                            try:

                                try:  # Tenta conectar com o banco de dados
            
                                    cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                                    cursor = cnx.cursor()

                                      
                                except mysql.connector.Error as err:
                                        
                                    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                              
                                        print("Alguma coisa esta errada com o nome de usuario ou a senha!")

                                        arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                        arquivo.write(" Evento: Banco de Dados: Usuario ou senha invalidos\n")
                                        arquivo.close()

                                    elif err.errno == errorcode.ER_BAD_DB_ERROR:
                              
                                        print("Esta base de dados nao existe")

                                        arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                        arquivo.write(" Evento: Banco de Dados: A base de dados nao existe\n")
                                        arquivo.close()

                                    else:
                                                      
                                        print(err)

                                        arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                        arquivo.write(" Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                                        arquivo.close()
                                                    
                                        time.sleep(0.1)
                                              
                                        pass
                                else:

                                    query = ("UPDATE qrcode SET enviado = 1 WHERE ID = %s") %ID 
                                    cursor.execute(query)
                                    cnx.commit()

                                    
                            except mysql.connector.Error as err:

                                print("Erro na atualizacao do valor no campo 'enviado'",err)
                                
                                break
                                                       

                            else:

                                print("\nAtualizado campo 'enviado' para 1\n")

                                cnx.close()

                                break

                                                        
                except Exception as e:

                    print(e)
                    break

##############################################  Buffer Delete  ##########################################
                
        hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log
            
        try:  # Tenta conectar com o banco de dados
            
            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
            cursor = cnx.cursor()

              
        except mysql.connector.Error as err:
                
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
      
                print("Alguma coisa esta errada com o nome de usuario ou a senha!")

                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                arquivo.write(" Evento: Banco de Dados: Usuario ou senha invalidos\n")
                arquivo.close()

            elif err.errno == errorcode.ER_BAD_DB_ERROR:
      
                print("Esta base de dados nao existe")

                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                arquivo.write(" Evento: Banco de Dados: A base de dados nao existe\n")
                arquivo.close()

            else:
                              
                print(err)

                arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                arquivo.write(" Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                arquivo.close()
                            
                time.sleep(0.1)
                      
                pass
            
      
        achou = 0

        query = ("SELECT * FROM buffer_delete WHERE enviado = 0")  # Seleciona a tabela qrcode
        cursor.execute(query)
                            
        for i in cursor:

            ID = i[1]
            cond = i[2]
            
            achou = 1


            if achou == 1:

                print("\nEncontrou na tabela delete_buffer item nao enviado")
                
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
                       
                        print("\nCondominio " + condominio + " IP " +  ID_correspondente)

                    except Exception as e:

                        if ID == ID_1:

                            pass  #print("Ja registrou cliente nao consta na lista")
                            
                        else:

                            print("Nao encontrou o cliente correspondente na lista")

                            arquivo = open("qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                            arquivo.write(" Evento: Nao encontrou cliente na lista " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                            arquivo.close()

                            ID_1 = ID

                        pass

                    else:  ########## CRIA WEBSOCKET E ENVIA OS DADOS PARA O CMM CORRESPONDENTE ########

                        try:

                            host = ID_correspondente
                            port = 5511
                               
                            print("\nEnviando delete atraves do buffer para o cliente...\n")
                            
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect ((host,port))

                            remover = ("deletar&" + ID + ":" + cond)
                            remover = str(remover)

                            command = ("%s")%remover # Dados a serem enviados para o CLP correspondente
                            
                            s.send(str.encode(command))
                            
                            reply = s.recv(1024)
                            print(reply.decode('utf-8'))
                            
                            s.close()
                                          
                        except Exception as e:
                            
                            print("\nNao conseguiu enviar delete para o cliente\n", e)

                            
                        else:

                                                        
                            try:

                                try:  # Tenta conectar com o banco de dados
            
                                    cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                                    cursor = cnx.cursor()

                                      
                                except mysql.connector.Error as err:
                                        
                                    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                              
                                        print("Alguma coisa esta errada com o nome de usuario ou a senha!")

                                        arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                        arquivo.write(" Evento: Banco de Dados: Usuario ou senha invalidos\n")
                                        arquivo.close()

                                    elif err.errno == errorcode.ER_BAD_DB_ERROR:
                              
                                        print("Esta base de dados nao existe")

                                        arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                        arquivo.write(" Evento: Banco de Dados: A base de dados nao existe\n")
                                        arquivo.close()

                                    else:
                                                      
                                        print(err)

                                        arquivo = open("log_cmm.txt", "a+") # Escreve o evento no registro de log
                                        arquivo.write(" Evento: Erro de acesso ao Banco pelo QR Code " + err + "\n")
                                        arquivo.close()
                                                    
                                        time.sleep(0.1)
                                              
                                        pass
                                else:

                                    query = ("UPDATE buffer_delete SET enviado = 1 WHERE ID = %s") %ID 
                                    cursor.execute(query)
                                    cnx.commit()

                                    
                            except mysql.connector.Error as err:

                                print("Erro na atualizacao do valor no campo 'enviado'",err)
                                
                                break
                                                       

                            else:

                                print("\nAtualizado campo 'enviado' para 1\n")

                                cnx.close()

                                break

                                                        
                except Exception as e:

                    print(e)
                    break
                
        time.sleep(30)                                



#####################################  THREADS   ############################################

c = threading.Thread(target = thread_cadastro) 
c.start()    

b = threading.Thread(target = buffer) 
b.start() 
############################################## LOOP PRINCIPAL ###############################

##while (1):
##
##
##    time.sleep(1)
