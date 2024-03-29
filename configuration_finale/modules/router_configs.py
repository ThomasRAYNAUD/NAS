from modules.ip_functions import recup_ip_masque

def vrf(id, constantes, neighbor_colors, color_list):
    config = ""

    for (neighbor_type, neighbor_color) in neighbor_colors:
        if neighbor_type == 'server':
            rd = constantes[f'route-target-{neighbor_color}'].split(':')
            rd[1] = str(id)
            rd = rd[0] + ':' + rd[1]
            config += (
                f"ip vrf {neighbor_color}\n rd {rd}\n"
                f" route-target export {constantes[f'route-target-{neighbor_color}']}\n"
                f" route-target import {constantes[f'route-target-{neighbor_color}']}\n"
            )
            for (as_type, as_color) in color_list:
                if as_type != 'server':
                    config += f" route-target import {constantes[f'route-target-{as_color}']}\n"
        else:
            rd = constantes[f'route-target-{neighbor_color}'].split(':')
            rd[1] = str(id)
            rd = rd[0] + ':' + rd[1]
            config += (
                f"ip vrf {neighbor_color}\n rd {rd}\n"
                f" route-target export {constantes[f'route-target-{neighbor_color}']}\n"
                f" route-target import {constantes[f'route-target-{neighbor_color}']}\n"
            )
            for (as_type, as_color) in color_list:
                if as_type == 'server':
                    config += f" route-target import {constantes[f'route-target-{as_color}']}\n"
    return config

def bgp_client_edge(router, As, id, routers, ip_by_links):
    config = ""
    config += "!\n"
    config += f"router bgp {As}\n"
    config += f" bgp router-id 10.10.10.{id}\n"
    egp_neighbors = [adj['neighbor'] for adj in router['adj'] if adj['protocol-type'] == 'egp']

    for neighbor in egp_neighbors:
        for router1 in routers:
            if router1['id'] == neighbor:
                ip_address_voisin, ip_mask = recup_ip_masque(ip_by_links, neighbor, (neighbor, id))
                config += (
                    f' neighbor {ip_address_voisin} remote-as {router1["as"]}\n'
                    f'!\n'
                    f' address-family ipv4\n'
                    f' neighbor {ip_address_voisin} activate\n'
                )
                for router2 in routers:
                    if router2['type'] == "client_edge" and router2['as'] == As and router2['id'] != id:
                        config += f' neighbor {ip_address_voisin} allowas-in\n'
                        break
                config += f' exit-address-family\n'

    config += " address-family ipv4\n"
    for [network, mask] in router['advertised_networks']:
        config += f'  network {network} mask {mask}\n'

    config += "!\n"
    return config

def bgp_provider_edge(router, As, id, routers, ip_by_links, asList):
    config = ""
    config += f"router bgp {As}\n"
    config += f" bgp router-id 10.10.10.{id}\n"
    config += "bgp log-neighbor-changes\n"

    for routeur in routers:
        if routeur["as"] == As and routeur["type"] == "provider_edge" and routeur["id"] != id:
            config += (
                f" neighbor {routeur['id']}.{routeur['id']}.{routeur['id']}.{routeur['id']} remote-as {As}\n"
                f" neighbor {routeur['id']}.{routeur['id']}.{routeur['id']}.{routeur['id']} update-source Loopback0\n"
            )

    config += "!\n"
    config += "address-family vpnv4\n"

    for routeur in routers:
        if routeur["as"] == As and routeur["type"] == "provider_edge" and routeur["id"] != id:
            config += (
                f" neighbor {routeur['id']}.{routeur['id']}.{routeur['id']}.{routeur['id']} activate\n"
                f" neighbor {routeur['id']}.{routeur['id']}.{routeur['id']}.{routeur['id']} send-community both\n"
            )

    config += "exit-address-family\n"
    config += "!\n"

    for neighbor in router["adj"]:
        if neighbor["protocol-type"] == "egp":
            idvoisin = neighbor["neighbor"]
            for routeur in routers:
                if routeur["id"] == idvoisin:
                    asnumero = routeur["as"]
                    for asss in asList:
                        if asss["id"] == asnumero:
                            ip_address_voisin, ip_mask_voisin = recup_ip_masque(ip_by_links, idvoisin, (id, idvoisin))
                            config += (
                                f"address-family ipv4 vrf {asss['color']}\n"
                                f"neighbor {ip_address_voisin} remote-as {asnumero}\n"
                                f"neighbor {ip_address_voisin} activate\n"
                                "exit-address-family\n"
                                "!\n"
                            )
    return config