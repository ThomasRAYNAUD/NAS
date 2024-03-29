
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
