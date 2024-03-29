def vrf(id, constantes, neighbor_colors, color_list):
    string=""
    # pour chaque couleur, on crée une vrf
    
    for (neighbor_type,neighbor_color) in neighbor_colors :
        # connaitre ses voisins, pour chaque voisin dans une VRF, on rentre que la vrf (couleur) de ce voisin
        if neighbor_type == 'server':
            rd=constantes[f'route-target-{neighbor_color}'].split(':')
            rd[1]=str(id)
            rd=rd[0]+':'+rd[1]
            string += (f"ip vrf {neighbor_color}\n rd {rd}\n"
                f" route-target export {constantes[f'route-target-{neighbor_color}']}\n"
                f" route-target import {constantes[f'route-target-{neighbor_color}']}\n")
            for (as_type,as_color) in color_list:
                if as_type != 'server':
                    string += f" route-target import {constantes[f'route-target-{as_color}']}\n"
        else:
            rd=constantes[f'route-target-{neighbor_color}'].split(':')
            rd[1]=str(id)
            rd=rd[0]+':'+rd[1]
            string += (f"ip vrf {neighbor_color}\n rd {rd}\n"
                f" route-target export {constantes[f'route-target-{neighbor_color}']}\n"
                f" route-target import {constantes[f'route-target-{neighbor_color}']}\n")
            for (as_type,as_color) in color_list:
                if as_type == 'server':
                    string += f" route-target import {constantes[f'route-target-{as_color}']}\n"
    return string
