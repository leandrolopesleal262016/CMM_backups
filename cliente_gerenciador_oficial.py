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
    
                    if comando == "deletar":

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
                        
                    if comando == "cadastrar":

                        try:

                            print("\nReconheceu cadastrar")
                           
                            dados = data.replace("cadastrar&","")
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
