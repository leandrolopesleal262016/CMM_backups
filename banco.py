import mysql.connector # faz a comunicação com o mysql no python 3.6

class Banco:

    def __init__(self):

        self = self

    def consulta(self,tabela,coluna):
    
        try:  # Tenta conectar com o banco de dados
            
            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
            cursor = cnx.cursor()
                  
        except Exception as err:
                
            print(err)

        else:    
            
            query = ("SELECT {} FROM {}").format (coluna,tabela) # SELECT campo FROM tabela
            cursor.execute(query)
                      
            for (i) in cursor: # Para cada item da coluna nome faz a comparação

                i = str(i)
                i = i.replace("'","")
                i = i.replace("(","")
                i = i.replace(")","")
                i = i.replace(",","")

                return (i)
        cnx.close()

    def encontra(self,tabela,coluna,valor):
    
        try:  # Tenta conectar com o banco de dados
            
            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
            cursor = cnx.cursor()
                  
        except Exception as err:

            print(err)

        else:    
            
            query = ("SELECT {} FROM {}").format (coluna,tabela) # SELECT campo FROM tabela
            cursor.execute(query)

            valor = str(valor)

##            print("Valor a comparar",valor,type(valor))
                      
            for (i) in cursor: # Para cada item da coluna nome faz a comparação

                
                i = str(i)
                i = i.replace("'","")
                i = i.replace("(","")
                i = i.replace(")","")
                i = i.replace(",","")

##                print("Valor do banco",i,type(i))
                
                if i == valor:

                    return ("1")

            return ("0")
        cnx.close()

    def deleta(self,tabela,coluna,valor):

        
        try:            
            
            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
            cursor = cnx.cursor()
            
        except Exception as err:
            
            print(err)

            
        try:
            
        
            query = ("DELETE FROM {} WHERE {} = '{}' ").format (tabela,coluna,valor)
            cursor.execute(query)
            cnx.commit()

            
        except Exception as err:

            print("Erro ao tentar deletar os dados",err)
            
            return ('erro')

            
        else:

            cnx.close()
            print ("Deletado valor",valor,"na coluna",coluna,"da tabela",tabela)
            return("deletado")


    def atualiza(self,tabela,coluna,valor):
        

        try:            
            
            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
            cursor = cnx.cursor()
            
        except Exception as err:
            
            print(err)
            
        try:
            
        
            query = ("UPDATE {} SET {} = {}").format (tabela,coluna,valor)
            cursor.execute(query)
            cnx.commit()

            
        except Exception as err:

            print("Erro na atualização dos dados",err)
            
            return ('erro')

            
        else:

            cnx.close()
            return ("Atualizado valor",valor,"na coluna",coluna,"da tabela",tabela)
            

    def insere(self,tabela,coluna,valor):

        
        try:            
            
            cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
            cursor = cnx.cursor()
            
        except Exception as err:
            
           print(err)

           
        try:
            
        
            query = ("INSERT INTO {}({}) VALUES ({})").format (tabela,coluna,valor)
            cursor.execute(query)
            cnx.commit()

            
        except Exception as err:

            print("Erro na atualização dos dados",err)
            
            return ('erro')

            
        else:

            cnx.close()
            print ("Inserido valor",valor,"na coluna",coluna,"da tabela",tabela)
            return("inserido")
      

    
