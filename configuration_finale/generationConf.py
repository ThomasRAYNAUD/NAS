import json
import os
import ipaddress




def recup_ip_masque(dico, id, link_tuple):
    # Vérifier si le tuple de liens existe dans le dictionnaire
    if link_tuple in dico:
        # Vérifier si l'identifiant est présent dans le tuple de liens
        if id in link_tuple:
            # Récupérer l'adresse IP et le masque de sous-réseau associés à l'identifiant dans le tuple de liens
            ip_index = link_tuple.index(id)
            return dico[link_tuple][0][ip_index], dico[link_tuple][1]
        else:
            # Récupérer l'autre adresse IP et le masque de sous-réseau dans le tuple de liens
            ip_index = 1 if link_tuple.index(id) == 0 else 0
            return dico[link_tuple][0][ip_index], dico[link_tuple][1]
    # Vérifier si le tuple inversé est présent dans le dictionnaire
    elif link_tuple[::-1] in dico:
        # Vérifier si l'identifiant est présent dans le tuple inversé de liens
        if id in link_tuple[::-1]:
            # Récupérer l'adresse IP et le masque de sous-réseau associés à l'identifiant dans le tuple inversé de liens
            ip_index = link_tuple[::-1].index(id)
            return dico[link_tuple[::-1]][0][ip_index], dico[link_tuple[::-1]][1]
        else:
            # Récupérer l'autre adresse IP et le masque de sous-réseau dans le tuple inversé de liens
            ip_index = 1 if link_tuple[::-1].index(id) == 0 else 0
            return dico[link_tuple[::-1]][0][ip_index], dico[link_tuple[::-1]][1]
    else:
        return None, None

def get_subnet_mask(subnet):
    # Convertir le sous-réseau en objet ipaddress
    subnet_ip = ipaddress.IPv4Network(subnet)

    # Obtenir le masque de sous-réseau du sous-réseau donné
    subnet_mask = subnet_ip.netmask

    return str(subnet_mask)

def get_subnet_ips(subnet):
    # Convertir le sous-réseau en objet ipaddress
    subnet_ip = ipaddress.IPv4Network(subnet)

    # Extraire les adresses IP de ce sous-réseau
    ips = [str(ip) for ip in subnet_ip.hosts()]

    return ips

def generate_subnets(network, netmask, subnet_mask):
    # Convertir les adresses IP et les masques en objets de type ipaddress
    network_ip = ipaddress.IPv4Network(network + '/' + str(netmask), strict=False)
    subnet_mask = ipaddress.IPv4Network('0.0.0.0/' + str(subnet_mask), strict=False)

    # Générer et afficher tous les sous-réseaux correspondant au masque de sous-réseau fourni
    subnets = []
    for subnet in network_ip.subnets(new_prefix=subnet_mask.prefixlen):
        subnets.append(str(subnet))

    return subnets

def extract_router_links(routers):
    links = set()
    for router in routers:
        router_id = router['id']
        for neighbor in router['adj']:
            neighbor_id = neighbor['neighbor']
            # Ajouter le lien dans l'ensemble en s'assurant qu'il n'y a pas de doublons
            if (router_id, neighbor_id) not in links and (neighbor_id, router_id) not in links:
                links.add((router_id, neighbor_id))

    return list(links)

def as_links(router_links, as_dict, router_dict):
    as_links_list = []

    for link in router_links:
        router1, router2 = link 

        # Recherche des AS correspondant à chaque routeur
        as_router1 = None
        as_router2 = None

        for router in router_dict:
            if router['id'] == router1:
                as_router1 = router['as']
            elif router['id'] == router2:
                as_router2 = router['as']

        # Vérification si l'un des deux AS est de type provider
        if as_router1 is not None and as_router2 is not None:
            as_type_router1 = None
            as_type_router2 = None

            for as_info in as_dict:
                if as_info['id'] == as_router1:
                    as_type_router1 = as_info['type']
                elif as_info['id'] == as_router2:
                    as_type_router2 = as_info['type']

            # Stockage dans le dictionnaire correspondant à l'AS
            current_as = None
            if as_type_router1 == 'provider' or as_type_router2 == 'provider':
                current_as = as_router1 if as_type_router1 == 'provider' else as_router2
            else:
                current_as = as_router1

            link_dict = {current_as: [link]}  # Créer un nouveau dictionnaire avec une liste contenant le lien

            # Vérification si l'AS existe déjà dans la liste de dictionnaires
            as_exists = False
            for item in as_links_list:
                if current_as in item:
                    as_exists = True
                    item[current_as].append(link)
                    break

            # Si l'AS n'existe pas encore, ajouter le nouveau dictionnaire
            if not as_exists:
                as_links_list.append(link_dict)

    return as_links_list


def vrf(asList, constantes):
    colors=[]
    string=""
    for num_as in asList:
        if num_as["color"] and num_as["color"] not in colors:
            colors.append(num_as["color"])
                
    for color in colors :
        string += (f"ip vrf {color}\n rd {constantes[f'route-dist-{color}']}\n"
            f" route-target export {constantes[f'route-target-{color}']}\n"
            f" route-target import {constantes[f'route-target-{color}']}\n")
        
    return string
        


        

            
         
        
            


#LECTURE DE L'INTENT FILE

#Récupération de l'intent file

f = open("configuration_finale/intentFiles/intentFileTestNetwork.json", "r")
intentFile = json.load(f)
f.close()

outputPath = "./NewRouterConfigs"

#Routeurs
routers = intentFile["routers"] 
nbRouter = len(routers)
constantes = intentFile["constantes"]

#AS
asList = intentFile["as"]
nbAs = len(asList)

#Tous les sous-réseaux d'un AS
for dicAs in asList:
    dicAs["subnets"]=generate_subnets(dicAs["network_prefix"], dicAs["network_mask"], dicAs["subnet_mask"])


#Recuperation des liens entre les routers
asLinks=as_links(extract_router_links(routers),asList,routers)

#Generation des IP associés à chaque router
ip_by_links={}

for as_dict in asLinks:
    as_id=list(as_dict.items())[0][0]
    tuples=list(as_dict.items())[0][1]
    for link in tuples:
        for as_infos in asList:
            if as_infos['id']==as_id:
                subnet = as_infos['subnets'].pop(0)
                ip_by_links[link]=(get_subnet_ips(subnet),get_subnet_mask(subnet))

#Constantes
ospfProcess = str(intentFile["constantes"]["ospfPid"])


#Ecriture de la configuration pour chaque routeur
for router in routers:
    #Recuperation des infos du routeur
    id = router["id"]
    As = router["as"]
    if router["type"]=="client":
        router_type="client"
        As_type="client"
    elif router["type"]=="client_edge":
        router_type="client_edge"
        As_type="client"
    elif router["type"]=="provider_edge":
        router_type="provider_edge"
        As_type="provider"
    elif router["type"]=="provider":
        router_type="provider"
        As_type="provider"

    #Creation du fichier de configuration du routeur sous la même forme que les fichiers de configuration de GNS3
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    res = open(f"{outputPath}/R{id}.txt", "w")
    # si le fichier ne s'est pas ouvert

    res.write("enable\nconf t\n")
    
    if As_type=='provider':
        res.write('ip cef\n')
    if router_type=='provider_edge':
        res.write(vrf(asList, constantes))
        
        
        

    #Interface de Loopback
    res.write("interface Loopback0\n"
              f" ip address {id}.{id}.{id}.{id} 255.255.255.255\n")
    #ospf sur tous les routeurs
    res.write(f" ip ospf {ospfProcess} area 0\n")
    res.write(f" no shutdown\n")
    res.write("!\n")
    
    # configuration des interfaces en suivant les adjacences du json
    for adj in router["adj"]:
        neighbor = adj['neighbor']
        res.write(f"interface {adj['interface']}\n")

        #Récupération de l'IP et du masque
        ip_address,ip_mask = recup_ip_masque(ip_by_links,id,(id,neighbor))

        # Ecrire la VRF sur les liens EGP
      

    
        if As_type == 'provider' and adj['protocol-type']=='egp':
            neighbor = adj['neighbor']
            neighbor_as = routers[neighbor-1]['as']
            color = asList[neighbor_as-1]['color'] 
            res.write(" ip vrf forwarding " + color + "\n")
                
        if adj['protocol-type']=='igp':
            res.write(f" ip ospf {ospfProcess} area 0\n")
        if (As_type == 'provider' and adj['protocol-type']=='igp'):
            res.write(f" mpls ip\n mpls label protocol ldp\n")
        res.write(f" no shutdown\n")
        res.write(f" ip address {ip_address} {ip_mask}\n")
        res.write("!\n")


    res.write(f"router ospf {ospfProcess}\n"
                f" router-id 10.10.{id}.{id}\n")    
    

    if router_type=="client_edge":
        res.write(f"!\n")
        res.write(f"router bgp {As}\n")
        res.write(f" bgp router-id 10.10.10.{id}\n")
        egp_neighbors = [adj['neighbor'] for adj in router['adj'] if adj['protocol-type'] == 'egp']
        # récupe des voisins de l'egp
        for neighbor in egp_neighbors:
            for router1 in routers:
                if router1['id'] == neighbor:
                    ip_address_voisin, ip_mask = recup_ip_masque(ip_by_links, neighbor, (neighbor, id))
                    res.write(f' neighbor {ip_address_voisin} remote-as {router1["as"]}\n')
                    res.write(f'!\n')
                    res.write(f' address-family ipv4\n')
                    res.write(f' neighbor {ip_address_voisin} activate\n')
                    # parmis tous les routeurs, si un autre customer est dans la même as que ce routeur
                    for router2 in routers:
                        if router2['type'] == "client_edge" and router2['as'] == As and router2['id'] != id:
                            res.write(f' neighbor {ip_address_voisin} allowas-in\n')
                            break
                    res.write(f' exit-address-family\n')
        res.write(f" address-family ipv4\n")
        for [network, mask] in router['advertised_networks']:
            res.write(f'  network {network} mask {mask}\n') 

        res.write(f"!\n")

        
    res.write("!\n")

    #Configuration BGP
    if router_type == "provider_edge":
        res.write(f"router bgp {As}\n")
        res.write(f" bgp router-id 10.10.10.{id}\n")
        res.write("bgp log-neighbor-changes\n")
        for routeuur in routers:
            if routeuur["as"]==As and routeuur["type"]=="provider_edge" and routeuur["id"]!=id:
                res.write(f" neighbor {routeuur['id']}.{routeuur['id']}.{routeuur['id']}.{routeuur['id']} remote-as {As}\n")
                res.write(f" neighbor {routeuur['id']}.{routeuur['id']}.{routeuur['id']}.{routeuur['id']} update-source Loopback0\n")
        
        res.write("!\n")
        res.write("address-family vpnv4\n")
        
        for routeuur in routers:
            if routeuur["as"]==As and routeuur["type"]=="provider_edge" and routeuur["id"]!=id:
                res.write(f" neighbor {routeuur['id']}.{routeuur['id']}.{routeuur['id']}.{routeuur['id']} activate\n")
                res.write(f" neighbor {routeuur['id']}.{routeuur['id']}.{routeuur['id']}.{routeuur['id']} send-community both\n")
        res.write("exit-address-family\n")
        res.write("!\n")




        for neighbor in router["adj"]:
            if neighbor["protocol-type"]=="egp":
                idvoisin = neighbor["neighbor"]
                for routeurrr in routers:
                    if routeurrr["id"]==idvoisin:
                        asnumero = routeurrr["as"]
                        for asss in asList:
                            if asss["id"]==asnumero:
                                    res.write(f"address-family ipv4 vrf {asss['color']}\n")
                                    ip_address_voisin,ip_mask_voisin = recup_ip_masque(ip_by_links,idvoisin,(id,idvoisin))
                                    res.write(f"neighbor {ip_address_voisin} remote-as {asnumero}\n")
                                    res.write(f"neighbor {ip_address_voisin} activate\n")
                                    res.write("exit-address-family\n")
                                    res.write("!\n")
                            
        

                


    
    



    res.close()
    
    print(f"Configuration du routeur {id} generee !")