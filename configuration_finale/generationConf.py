import json, os


#LECTURE DE L'INTENT FILE

#Récupération de l'intent file
f = open("/home/hipp/Documents/TC/NAS/NAS/configuration_finale/intentFiles/intentFileTestNetwork.json", "r")
intentFile = json.load(f)
f.close()

outputPath = "./NewRouterConfigs"

#Routeurs
routers = intentFile["routers"]
nbRouter = len(routers)

#AS
asList = intentFile["as"]
nbAs = len(asList)


print(routers)
print(nbRouter)
print(asList)
print(nbAs)
#Dictionnaire contenant les couples idAs / Préfixe réseau associé
asPrefix = {}
for i in range(nbAs):
    asInfos = asList[i]
    asPrefix[asInfos["id"]] = asInfos["ip-prefix"]

print(asPrefix)


#Dictionnaire contenant les index des derniers sous-reseaux utilises pour chaque AS.
#Utilsé pour la generation des adresses IP des liens IGP
dicoSousRes = {} 
for id in asPrefix:
    dicoSousRes[id] = 0

print(dicoSousRes)



#Initialisation d'une matrice contenant les numeros des sous-reseaux entre chaque routeur
#Utilsé pour la generation des adresses IP des liens IGP
matIdSousReseauxAs = [] 
for i in range(0,nbRouter):
    matIdSousReseauxAs.append([])
    for j in range(nbRouter):
        matIdSousReseauxAs[i].append(0)

print(matIdSousReseauxAs)




#Constantes
ospfProcess = str(intentFile["constantes"]["ospfPid"])

#Ecriture de la configuration pour chaque routeur
for router in routers:
    
    #Recuperation des infos du routeur
    id = router["id"]
    As = router["as"]
    
    #Creation du fichier de configuration du routeur sous la même forme que les fichiers de configuration de GNS3
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
    res = open(f"{outputPath}/R{id}.txt", "w")

    res.write("enable\nconf t\n")

    #Interface de Loopback
    res.write("interface Loopback0\n"
              f" ip address {id}.{id}.{id}.{id} 255.255.255.255\n")
    
    res.write(f" ipv6 ospf {ospfProcess} area 0\n")
    res.write("!\n")

    #Interfaces
    for adj in router["adj"]:
        
        for link in adj["links"]:
            #Generation de l'addresse IP
            
            #Ecriture de l'interface et de son adresse IP dans le fichier de configuration

            res.write(f"interface {link['interface']}\n")

            res.write(f" ip address {link['ip_address']} {link['network_mask']}\n")
            
            res.write(f" ipv6 ospf {ospfProcess} area 0\n")

            res.write(f" mpls ip\n mpls label protocol ldp\n")

            res.write("!\n")
             

    res.write(f"ipv6 router ospf {ospfProcess}\n"
                f" router-id 10.10.{id}.{id}\n")    
                
    res.write("!\n")
    
    res.close()

    print(f"Configuration du routeur {id} generee !")