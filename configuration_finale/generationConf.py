import json
import os
from modules.ip_functions import *
from modules.router_links_functions import *
from modules.router_configs import *

#Recupération de l'intentfile
f = open("configuration_finale/intentFile.json", "r")
intentFile = json.load(f)
f.close()

#Chemin où seront stockées les configs
outputPath = "RouterConfigs"

#Séparation de l'intentfile en sous-listes
asList = intentFile["as"]
routers = intentFile["routers"] 
constantes = intentFile["constantes"]

#Recuperation des liens entre les routers sous la forme [(routerA, routerB),(routerB, routerC), ... ]
asLinks=as_links(extract_router_links(routers),asList,routers)

#Génération de tous les sous-réseaux existants par AS
for as_infos in asList:
    as_infos["subnets"]=generate_subnets(as_infos["network_prefix"], as_infos["network_mask"], as_infos["subnet_mask"])

#Génération des IP pour chaque lien
ip_by_links={}
for as_dict in asLinks:
    as_id=list(as_dict.items())[0][0]
    tuples=list(as_dict.items())[0][1]
    for link in tuples:
        for as_infos in asList:
            if as_infos['id']==as_id:
                subnet = as_infos['subnets'].pop(0)
                ip_by_links[link]=(get_subnet_ips(subnet),get_subnet_mask(subnet),get_subnet_ip(subnet))

#Récupération de la liste des VRF sous la forme [(type d'AS, couleur de VRF), .....]
color_list=[]
for as_infos in asList :
    if 'color' in as_infos:
        if not ( (as_infos['type'], as_infos['color']) in color_list ): 
            color_list.append((as_infos['type'], as_infos['color']))


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

    #Creation du fichier de configuration du routeur
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    res = open(f"{outputPath}/R{id}.txt", "w")

    #Début de la conf
    res.write("enable\nconf t\n")
    
    if As_type=='provider':
        res.write('ip cef\n')
    
    #Router de bordure => Ajout des VRF
    if router_type=='provider_edge':
        neighbor_colors=[]

        for adj in router["adj"]:
            neighbor_id = adj["neighbor"]
            neighbor_as = routers[neighbor_id-1]['as']
            if 'color' in asList[neighbor_as-1]:
                neighbor_as_type = asList[neighbor_as-1]['type']
                neighbor_as_color= asList[neighbor_as-1]['color']
                neighbor_colors.append((neighbor_as_type,neighbor_as_color))

        res.write(vrf(id, constantes,neighbor_colors,color_list))
        
    #Router client => Default Route sur le CE
    if router_type == 'client':
        for routerA in routers:
            if routerA['as']==As and routerA['type']=='client_edge':
                edge_router_id=routerA['id']
                res.write(f'ip route 0.0.0.0 0.0.0.0 {edge_router_id}.{edge_router_id}.{edge_router_id}.{edge_router_id}\n')


    #Interface de Loopback
    res.write("interface Loopback0\n"
              f" ip address {id}.{id}.{id}.{id} 255.255.255.255\n")


    #OSPF
    res.write(f" ip ospf {constantes['ospfPid']} area 0\n")
    res.write(f" no shutdown\n")
    res.write("!\n")
    
    #Config des interfaces
    for adj in router["adj"]:
        neighbor = adj['neighbor']
        res.write(f"interface {adj['interface']}\n")

        #Récupération de l'IP et du masque sur le lien
        ip_address,ip_mask = recup_ip_masque(ip_by_links,id,(id,neighbor))

        # Ecrire la VRF sur les liens EGP   
        if router_type == 'provider_edge' and adj['protocol-type']=='egp':
            neighbor = adj['neighbor']
            neighbor_as = routers[neighbor-1]['as']

            if 'color' in asList[neighbor_as-1]:
                res.write(" ip vrf forwarding " + asList[neighbor_as-1]['color'] + "\n")

        
        if adj['protocol-type']=='igp':
            res.write(f" ip ospf {constantes['ospfPid']} area 0\n")
        if (As_type == 'provider' and adj['protocol-type']=='igp'):
            res.write(f" mpls ip\n mpls label protocol ldp\n")
        res.write(f" no shutdown\n")
        res.write(f" ip address {ip_address} {ip_mask}\n")
        res.write("!\n")


    res.write(f"router ospf {constantes['ospfPid']}\n"
                f" router-id 10.10.{id}.{id}\n")    
    
    for (routerA, routerB) in list(ip_by_links.keys()):
        if routerA == id or routerB == id:
            print (ip_by_links[(routerA, routerB)][2])
            print (ip_by_links[(routerA, routerB)][1])


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

    # arreter le programme python


    res.close()
    
    print(f"Configuration du routeur {id} generee !")