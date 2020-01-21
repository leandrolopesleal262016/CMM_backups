#!/usr/bin/env python3
# -*-encoding: utf-8 -*-

import json
import mysql.connector # cominica com o mysql no python 3.6
import socket
import signal # Bibloteca para uso do time out
import time
from lista_clientes import _cliente

from wsgiref.simple_server import make_server
from pyramid.view import view_config
from pyramid.config import Configurator


host = '0.0.0.0'
port = 5050

hs = time.strftime("%H:%M:%S") # Hora completa para registro de Log

def log(texto): # Metodo para registro dos eventos no log.txt (exibido na interface grafica)

    hs = time.strftime("%H:%M:%S") 
    data = time.strftime('%d/%m/%y')

    texto = str(texto)

    escrita = ("{} - {}  Evento:  {}\n").format(data, hs, texto)
    escrita = str(escrita)

    l = open("/var/www/html/log/log.txt","a")
    l.write(escrita)
    l.close()

def timeout(signum, frame):

    print ("Excedeu o tempo esperado")
    

log("Iniciou o webservice")

@view_config(route_name='iterar', renderer='json',request_method='GET')
@view_config(route_name='iterar', renderer='json',request_method='DELETE')

def iterar(request):

    ID_recebido = request.matchdict['id']

    if request.method == 'DELETE':
        
        inexistente = 0
        
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
            
            query = ("SELECT * FROM qrcode")  
            cursor.execute(query)

            encontrou = 0
                                
            for i in cursor: # Para cada item da coluna nome faz a comparacao

                if encontrou == 0:
                    ID = i[0] # Seleciona o primeiro item da lista recebida do banco (ID)
                    nome = i[1]
                    ap = i[2]
                    bloco = i[3]
                    cond = i[4]
                    hi = i[5]
                    hf = i[6]
                    di = i[7]
                    df = i[8]
                    ds = i[9]

                if (ID_recebido == ID): # Compara se o ID do banco e igual ao vindo do request ID_recebido

                    encontrou = 1
		    
         
            if encontrou == 0:

                inexistente = 1

                return {ID_recebido:"ID Inexistente"} # ID Vindo do request


            if encontrou == 1:

                print("cond lido no banco",cond)
                query = ("DELETE FROM qrcode WHERE ID = %s") % ID_recebido
                cursor.execute(query)
                cnx.commit()

                print("ID",ID_recebido,"deletado do banco",hs)

                ID = str(ID)
                cond = str(cond)
                texto = (" Evento: Deletado QR Code " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                texto = str(texto)

                arquivo = open("/home/clp/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                arquivo.write(texto)
                arquivo.close()

                encontrou = 0
                inexistente = 0

                return {"ok":ID}

                
            
        finally:

            if inexistente == 0:
                
            
                try:

                    print("\nEnviando deletar pro gerenciador...\n")
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    remover = str("deletar_qr:" + ID_recebido + ":" + cond)

                    command = ("%s")%remover
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    
                    s.close()

                                                  
                except Exception as e:
                    
                    print("\nNao conseguiu enviar deletar pro gerenciador\n", e)

                    print("\nCriar uma rotina aqui para tentar de novo...\n")
                  
                else:

                    print("\nEnviado deletar para o gerenciador\n")
                
                inexistente = 1       

    if request.method == 'GET':  # consulta por id

        ID_recebido = request.matchdict['id']
                
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
            
            
        query = ("SELECT * FROM qrcode")  
        cursor.execute(query)

        encontrou = 0
                            
        for i in cursor: 

            
            ID = i[0] # Seleciona o primeiro item da lista recebida do banco (ID)
            

            if (ID_recebido == ID): # Compara se o ID do banco e igual ao vindo do request ID_recebido

                               
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
                
     
        if encontrou == 0:

            return {"Inexistente": ID_recebido} # ID Vindo do request
            

        if encontrou == 1:

            hi = str(hi)
            hf = str(hf)
            di = str(di)
            df = str(df)
            ID_recebido = str(ID_recebido)

            texto = (" Evento: Consulta QR Code " + nome + " " + ID_recebido + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
            texto = str(texto)
            arquivo = open("/home/clp/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
            arquivo.write(texto)
            arquivo.close()

            return {"Nome": nome, "ID": ID, "Ap": ap, "bloco": bloco, "cond": cond, "hi":hi, "hf": hf, "di": di, "df": df, "ds": ds}

            encontrou = 0
                
                
@view_config(route_name='qrCodes', renderer='json',request_method='POST')
@view_config(route_name='qrCodes', renderer='json',request_method='PUT')

def qrCodes(request):
    

    if request.method == 'POST':

        duplicado = 0

        try:
        
            dados_json = request.json_body  # Tranforma o corpo do body recebido em json
            
            ID = dados_json["ID"]
            nome = dados_json["nome"]
            ap = dados_json["apartamento"]
            bloco = dados_json["bloco"]
            cond = dados_json["condominio"]
            di = dados_json["data_inicio"]
            df = dados_json["data_fim"]
            hi = dados_json["hor_inicio"]
            hf = dados_json["hor_fim"]
            ds = dados_json["dias_semana"]
	    
 	    
            print("Recebido do condfy para cadastro",ID,nome,ap,bloco,cond,di,df,hi,hf,ds)

        except Exception as err:

            print("Erro no formato de um dos itens do dicionario",err)
        
        
        try:
            
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
                    
                    duplicado = 1
                    
                    return {'duplicado': ID}

                else:

                    print("Erro na inclusão do banco",err)

                    return ('erro')

            else:

                print("\nCadastrado com sucesso", ID, nome, cond )

                ID = str(ID)

                return {"ok":ID}                

                                    

        except Exception as e:

            return {'Nao conseguiu cadastrar': e}
        

        finally:
            
            if duplicado == 0:
                
                ID = str(ID)

                texto = (" Evento: Cadastro QR Code ",nome, " " , ID , " ap" , ap , " bloco" , bloco , " " , hs , "\n")
                texto = str(texto)
                arquivo = open("/home/clp/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
                arquivo.write(texto)
                arquivo.close()

                try:  # Tenta enviar para o gerenciador CMMs que enviara o cadastro obtido do BD p/ o CMM correspondente

                    print("\nEnviando cadastrar pro gerenciador...\n")
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = ("cadastrar_qr:%s")%ID
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    s.close()
                                  
                except Exception as e:
                    
                    print("\nNao conseguiu enviar pro gerenciador",e)

                    print("\nCriar uma rotina aqui para tentar de novo...\n")
                    
                    
                else:

                    print("enviou cadastro para o gerenciador")


    if request.method == 'PUT':

        
        try:
        
            dados_json = request.json_body  # Tranforma o corpo do body recebido em json
            
            ID = dados_json["ID"]
            nome = dados_json["nome"]
            ap = dados_json["apartamento"]
            bloco = dados_json["bloco"]
            cond = dados_json["condominio"]
            di = dados_json["data_inicio"]
            df = dados_json["data_fim"]
            hi = dados_json["hor_inicio"]
            hf = dados_json["hor_fim"]
            ds = dados_json["dias_semana"]	    
 	    
           #print("Imprimindo pelo dicionario",ID,nome,ap,bloco,cond,di,df,hi,hf,ds)

        except Exception as err:

            print("Erro no formato de um dos itens do dicionario",err)
        
        
        try:
            
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
                
            
                query = ("UPDATE qrcode SET nome = %s, apartamento = %s, bloco = %s, cond = %s, hora_inicio = %s, hora_final = %s, data_inicio = %s, data_final = %s, dias_semana = %s WHERE ID = %s")
		print("Id sendo atualizado no banco ",ID)
                query_data = (nome,ap,bloco,cond,hi,hf,di,df,ds,ID)
                cursor.execute(query, query_data)
                cnx.commit()

                
            except mysql.connector.Error as err:

                print("Erro na atualização dos dados",err)
                
                return {'erro'}

                
            else:

                print("\nAtualizado com sucesso", ID, nome, cond )

                ID = str(ID)
                return ("ok")
          

        except Exception as e:

            return {'Nao conseguiu atualizar': e}
        

        finally:            
                   
            ID = str(ID)

            texto = (" Evento: Atualizado QR Code ",nome, " " , ID , " ap" , ap , " bloco" , bloco , " " , hs , "\n")
            texto = str(texto)
            arquivo = open("/home/clp/qrcodes.log", "a+") # Escreve o evento no registro de acesso de moradores
            arquivo.write(texto)
            arquivo.close()

            try:  # Tenta enviar para o gerenciador CMMs que enviara o cadastro obtido do BD p/ o CMM correspondente

                print("\nEnviando Atualizar para o gerenciador...\n")
                
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect ((host,port))

                command = ("atualizar:%s")%ID
                s.send(str.encode(command))
                reply = s.recv(1024)
                print(reply.decode('utf-8'))
                print("enviou Atualizar para o gerenciador")
                s.close()
                              
            except Exception as e:
                
                print("\nNao conseguiu enviar atualizar para o gerenciador",e)

                print("\nCriar uma rotina aqui para tentar de novo...\n")                    

            
                        
@view_config(route_name='status', renderer='json',request_method='GET')

def status(request):

    return("ok")

@view_config(route_name='consta', renderer='json',request_method='GET')

def consta(request):

    cond = request.matchdict['numero']
    cond = str(cond)
    
    if request.method == 'GET':
        
        inexistente = 0
    
        try: # PROCURA O ID CORRESPONDENTE NA LISTA 

            numero = cond
            cliente = _cliente(numero) # insatancia a lista de enderecos externa

            condominio = (cliente[0])
##            ID_correspondente = (cliente[1])

            print("\n",condominio,"\n")

        except Exception as e:

            print("\nNao encontrou o cliente correspondente na lista\n")
            
            return("erro")
            

        else:  ########## CRIA WEBSOCKET E ENVIA OS DADOS PARA O CMM CORRESPONDENTE ########

            return("ok")
    
#########################################################  MORADORES  ##################################################################


@view_config(route_name='moradores', renderer='json',request_method='POST')

def moradores(request):    

    if request.method == 'POST':

        duplicado = 0

        try:
        
            dados_json = request.json_body  # Tranforma o corpo do body recebido em json
            
            ID = dados_json["ID"]
            nome = dados_json["nome"]
            ap = dados_json["apartamento"]
            bloco = dados_json["bloco"]
            cond = dados_json["condominio"]
            di = dados_json["data_inicio"]
            df = dados_json["data_fim"]
            hi = dados_json["hor_inicio"]
            hf = dados_json["hor_fim"]
            ds = dados_json["dias_semana"]

           #print("Imprimindo pelo dicionario",ID,nome,ap,bloco,cond,di,df,hi,hf,ds)

        except Exception as err:

            print("Erro no formato de um dos itens do dicionario",err)        
        
        try:
            
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
                
            
                query = ("INSERT INTO moradores (ID, nome, apartamento, bloco, cond, hora_inicio, hora_final, data_inicio, data_final, dias_semana) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
                query_data = (ID,nome,ap,bloco,cond,hi,hf,di,df,ds)
                cursor.execute(query, query_data)
                cnx.commit()

                
            except mysql.connector.Error as err:


                if err.errno == 1062:

                    print("ID duplicado")
                    
                    duplicado = 1
                    
                    return {'duplicado': ID}

                else:

                    print("Erro na inclusão do banco",err)

                    return ('erro')

            else:

                print("\nMorador cadastrado com sucesso", ID, nome, cond )

                ID = str(ID)

                return {"cadastrado":ID}          
                     

        except Exception as e:

            return {'erro': e}        

        finally:
            
            if duplicado == 0:
                
                ID = str(ID)

                texto = (" Evento: Cadastro Morador " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                texto = str(texto)
                arquivo = open("moradores.log", "a+") # Escreve o evento no registro de acesso de moradores
                arquivo.write(texto)
                arquivo.close()

                try:  # Tenta enviar para o gerenciador CMMs que enviara o cadastro obtido do BD p/ o CMM correspondente

                    print("\nEnviando cadastro morador pro gerenciador...\n")
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    command = ("cadastrar:%s")%ID
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    s.close()
                                  
                except Exception as e:
                    
                    print("\nNao conseguiu enviar pro gerenciador",e)

                    print("\nCriar uma rotina aqui para tentar de novo...\n")
                    
                    
                else:

                    print("enviou cadastro para o gerenciador")


@view_config(route_name='itera', renderer='json',request_method='GET')
@view_config(route_name='itera', renderer='json',request_method='DELETE')

def itera(request):

    ID_recebido = request.matchdict['id']

    if request.method == 'DELETE':
        
        inexistente = 0
        
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
            
            query = ("SELECT * FROM moradores")  
            cursor.execute(query)

            encontrou = 0
                                
            for i in cursor: # Para cada item da coluna nome faz a comparacao

                if encontrou == 0:

                    ID = i[0] # Seleciona o primeiro item da lista recebida do banco (ID)
                    nome = i[1]
                    ap = i[2]
                    bloco = i[3]
                    cond = i[4]
                    hi = i[5]
                    hf = i[6]
                    di = i[7]
                    df = i[8]
                    ds = i[9]

                if (ID_recebido == ID): # Compara se o ID do banco e igual ao vindo do request ID_recebido

                    encontrou = 1
		    
         
            if encontrou == 0:

                inexistente = 1

                return {ID_recebido:"ID Inexistente"} # ID Vindo do request


            if encontrou == 1:

                print("cond lido no banco",cond)
                query = ("DELETE FROM moradores WHERE ID = %s") % ID_recebido
                cursor.execute(query)
                cnx.commit()

                print("ID",ID_recebido,"deletado do banco",hs)

                ID = str(ID)
                cond = str(cond)

                texto = (" Evento: Deletado Cadastro " + nome + " " + ID + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
                texto = str(texto)

                arquivo = open("moradores.log", "a+") # Escreve o evento no registro de acesso de moradores
                arquivo.write(texto)
                arquivo.close()

                encontrou = 0
                inexistente = 0

                return ("ok")
         
            
        finally:

            if inexistente == 0:                
            
                try:

                    print("\nEnviando deletar pro gerenciador...\n")
                    
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.connect ((host,port))

                    remover = str("deletar:" + ID_recebido + ":" + cond)

                    command = ("%s")%remover
                    s.send(str.encode(command))
                    reply = s.recv(1024)
                    print(reply.decode('utf-8'))
                    
                    s.close()
                                                  
                except Exception as e:
                    
                    print("\nNao conseguiu enviar deletar pro gerenciador\n", e)

                    print("\nCriar uma rotina aqui para tentar de novo...\n")
                  
                else:

                    print("\nEnviado deletar para o gerenciador\n")
                
                inexistente = 1       

    if request.method == 'GET':  # consulta por id

        ID_recebido = request.matchdict['id']
                
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
            
            
        query = ("SELECT * FROM moradores")  
        cursor.execute(query)

        encontrou = 0
                            
        for i in cursor: 

            
            ID = i[0] # Seleciona o primeiro item da lista recebida do banco (ID)
            

            if (ID_recebido == ID): # Compara se o ID do banco e igual ao vindo do request ID_recebido
                               
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
     
        if encontrou == 0:

            return {"Inexistente": ID_recebido} # ID Vindo do request            

        if encontrou == 1:

            hi = str(hi)
            hf = str(hf)
            di = str(di)
            df = str(df)
            ID_recebido = str(ID_recebido)

            texto = (" Evento: Consulta Cadastro " + nome + " " + ID_recebido + " ap" + ap + " bloco" + bloco + " " + hs + "\n")
            texto = str(texto)

            arquivo = open("moradores.log", "a+") # Escreve o evento no registro de acesso de moradores
            arquivo.write(texto)
            arquivo.close()

            return {"Nome": nome, "ID": ID, "Ap": ap, "bloco": bloco, "cond": cond, "hi":hi, "hf": hf, "di": di, "df": df, "ds": ds}

            encontrou = 0
    


if __name__ == '__main__':
    
    config = Configurator()

    config.add_route('qrCodes', '/qrCodes') # POST Cadastro
    config.add_route('iterar', '/qrCodes/{id}') # DELETE, GET
    config.add_route('status', '/status') # GET
    config.add_route('consta', '/condominios/{numero}') # GET consulta se o condominio esta na lista de clientes cadastrados
    
   
    config.add_route('moradores', '/moradores') # POST Cadastro
    config.add_route('itera', '/moradores/{id}') # DELETE, GET  deleta e obtem cadastro
       
 
    config.add_view(qrCodes, route_name='qrCodes')
    config.add_view(iterar, route_name='iterar')
    config.add_view(status, route_name='status')
    config.add_view(consta, route_name='consta')

    config.add_view(moradores, route_name='moradores')
    config.add_view(itera, route_name='itera')


    config.scan() # Verifica se ha algum decorador
    app = config.make_wsgi_app()
    server = make_server('0.0.0.0', 5511, app)
    print (server.base_environ)
    server.serve_forever()
