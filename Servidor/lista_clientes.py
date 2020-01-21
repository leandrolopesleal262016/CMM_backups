def _cliente(numero):
    
    cliente = {} # cria um dicionario vazio para ir adicionando clientes pos

    cliente ['5922'] = ['Caparao','172.20.6.137']
    cliente ['5920'] = ['Camila','172.20.6.14']
    cliente ['5808'] = ['Costa Tropical','172.18.30.251']
    cliente ['5853'] = ['Maracai','172.18.12.250']
    cliente ['5734'] = ['Riachuelo','172.55.0.17']
    cliente ['2019'] = ['Maquete','172.20.6.14']
    cliente ['5410'] = ['Desenvolvimento','172.20.6.143']
    cliente ['9014'] = ['Central de Monitoramento','172.20.6.14']
    cliente ['6639'] = ['Siena','172.18.36.252']
    cliente ['5785'] = ['Parati','172.20.6.146']
    cliente ['5987'] = ['Carmem','172.18.34.247']
    cliente ['0001'] = ['LagoSul','172.19.1.251']
    cliente ['0054'] = ['Central de Monitoramento', '172.20.6.14']
    cliente ['6653'] = ['Soho','172.18.37.238']

    for i in cliente:

        if numero == i:
            
            c = cliente[i]
            return c






