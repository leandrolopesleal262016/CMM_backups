# Teste de QR Code

import mysql.connector
from banco import Banco

banco = Banco()

dados = "76130456757395"  # Dados lidos pelo leitor  


ja_encontrou = 0

try:  


        dados = dados[3:] # elimina os 3 primeiros digitos da string dados                        

        dados = int(dados)

        consulta = 1
            
        tabela = [601, 403, 820, 417, 217, 162, 684, 895, 797, 413, 577, 527, 921, 203, 565, 620, 369, 471, 316, 988, 387, 418, 643, 987, 297, 108, 396, 880, 436, 465, 899, 671, 422, 253, 765, 992, 259, 286, 932, 627, 474, 378, 894, 216, 594, 289, 258, 490, 647, 487, 409, 888, 221, 805, 535, 713, 363, 925, 964, 327, 618, 379, 739, 132, 205, 902, 335, 396, 407, 871, 867, 213, 982, 980, 252, 228, 881, 137, 138, 216, 825, 536, 681, 895, 921, 711, 375, 908, 429, 656, 304, 560, 988, 642, 965, 183, 629, 432, 360, 728, 801, 796, 716, 631, 495, 587, 917, 732, 275, 119, 558, 675, 672, 729, 612, 517, 962, 995, 668, 144, 513, 987, 109, 563, 177, 257, 975, 626, 575, 813, 377, 363, 484, 170, 284, 869, 726, 502, 841, 808, 219, 286, 670, 614]                         
        tempo_validade = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460, 470, 480, 490, 500, 510, 520, 530, 540, 550, 560, 570, 580, 590, 600, 610, 620, 630, 640, 650, 660, 670, 680, 690, 700, 710, 720, 730, 740, 750, 760, 770, 780, 790, 800, 810, 820, 830, 840, 850, 860, 870, 880, 890, 900, 910, 920, 930, 940, 950, 960, 970, 980, 990, 1000, 1010, 1020, 1030, 1040, 1050, 1060, 1070, 1080, 1090, 1100, 1110, 1120, 1130, 1140, 1150, 1160, 1170, 1180, 1190, 1200, 1210, 1220, 1230, 1240, 1250, 1260, 1270, 1280, 1290, 1300, 1310, 1320, 1330, 1340, 1350, 1360, 1370, 1380, 1390, 1400, 1410, 1420, 1430, 1440]

        if (1):
            
            for item in tabela:
                     
                id_raiz = int(dados / item)  # divide o valor lido no QR por cada numero da tabela e consulta no banco

##                self.id_raiz = id_raiz
               
                try:  # Tenta conectar com o banco de dados
                    
                    cnx = mysql.connector.connect(user='leandro',database='CMM', password='5510',host='localhost')
                    cursor = cnx.cursor()
                                                          
                except mysql.connector.Error as err:

                    log("Opa, problema com o banco de dados")                                                                              
                    log(err)
                                                                    
                    time.sleep(0.1)                                       
                
                try:                    

                    query = ("SELECT ID FROM qrcode WHERE ID = %s")%id_raiz # procura na coluna ID um código = ao id_raiz
                    cursor.execute(query)

                    for i in cursor: # Se o cursor encontrar o item especificado, prossegue...
                                                                                        
                        id_valido = 1 # Encontrou o ID raiz
                        consulta = 1 # Habilita a consulta de data e horario
                        ja_encontrou = 1 # Depois de encontrar encerra a consulta do ID raiz
                                       
                except Exception as e:
                
                    txt = ("Tipo de erro: " + str(e))
                    log(txt)
                    
                    break
                    
                if ja_encontrou == 1:
                    
                    ja_encontrou = 0                    

                    break
        item = item

        print("ID correspondente",id_raiz)
                
except Exception as e:

    log("Não foi possivel ler os dados recebidos")

pesquisa = (banco.encontra("qrcode","id",id_raiz))

if pesquisa == "0":
    print ("Não encontrou este id no banco")

if pesquisa == "1":
    print ("Encontrou id no banco!")
    
