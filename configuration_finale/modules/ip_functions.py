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

def get_subnet_ip(subnet):
    # Convertir le sous-réseau en objet ipaddress
    subnet_ip = ipaddress.IPv4Network(subnet)

    return str(subnet_ip.network_address)


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