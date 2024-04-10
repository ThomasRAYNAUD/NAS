# Network Automation Project


## Presentation
The aim of the project is to write a code that deploys routing protocols across a given network. The network specificities are defined in an `intent_file`. The addressing will be done using **IPv4** addresses.


## Overall approach
We start by setting a network consisting of 4 routers, as shown in Figure 1 : 2 of them are gonna be our provider-edges (PE) and the 2 others are gonna be our providers (P). Indeed, our first stage is to setup an **MPLS** core formed by these routers. We give each interface an IPv4 address and setup **OSPF(v2)** between them as the IGP protocol. MPLS labels are gonna get assigned on the basis of the routes defined by OSPF. We make sure to assign IP addresses to the loopback of each router so OSPF can trace routes to them. This will help since one of the steps of MPLS Labels advertising is assigning a lable to the loopback of a router.

![Alt text](https://image.noelshack.com/fichiers/2024/13/5/1711706991-captura-de-pantalla-2024-03-29-110916.png)


We are gonna be setting MPLS and **LDP** to route data packets using labels. This will be useful later when we add Clients, since our final objective is to automate the provisioning of BGP/MPLS VPN services, in the example of Internet Services. 


### Automation

Our main objective is to automate the whole configuration process In order to do so, we need to create a code that allows us to manipulate the consoles of each router in the GNS3 project from distance. We decided to use the **telnet** protocol, which allows us to establish TCP/IP connexions and access a distant machine. We will be working on the basis of our existing code for the GNS Project we did earlier this year. 

This is how our code will eventually work :

- We first retrieve the nodes of every router. This is done in the _script.py_ file. We interact with a GNS3 server in order to retrieve a list of the routers in the network. In this loop, for each router name in the routers list, the code retrieves the corresponding node from the GNS3 project and its port. `tn.write` allows us to write directly in the terminal of a router : 

```
for router in routers: 
    router_node = lab.get_node(router)
    print(router_node)
    if router_node:  # si le noeud existe
        telnet_port = router_node.console  # on récupère le port telnet du noeud
        telnet_host = "127.0.0.1"
        telnet_timeout = 10
        tn = telnetlib.Telnet(telnet_host, telnet_port, timeout=telnet_timeout)  # connexion au routeur par telnet
        tn.write(b"\r\n")
```

- We then go over the _intentFile.json_, where every AS and router of the network is precised, along with its IPv4 addresses for each interface, its type, its neighbors, and more. Thanks to telnet and by running `if` tests, we configure every router. There is a different setup function for every situation, as well as for making the address plan of the network. A configuration of a random router in the _intentFile.json_ can be seen in the image below.


![Alt text](https://image.noelshack.com/fichiers/2024/15/2/1712668344-captura-de-pantalla-2024-04-09-151210.png)


## Phase 1

After we set up the initial network and we manage to route and forward packets using OSPF(v2), the next phase is to set up MPLS and LDP, thus creating a MPLS core. This is done thanks to telnet and the `res.write()` function, which allows us to write a string into a file. The `res` object allows us to create a path to the _RouterConfigs_ file, where all the configurations of the routers will be written. The configuration of MPLS is done by running the following code : 

```
#Activer MPLS sur tous les liens IGP des provider
        if (As_type == 'provider' and adj['protocol-type']=='igp'):
            res.write(f" mpls ip\n mpls label protocol ldp\n")
```

This sets up MPLS and gives the work of label advertising to LDP. The configuration for setting up MPLS and LDP is found on the internet. 

Before moving onto the next phase, we make sure :
- LDP session states
- MPLS transport in the core
- Penultimate Hop Popping behaviour

## Phase 2

We now wish to implement **BGP** on the client sites using a **VPN** feature. When used with MPLS, the VPN feature allows several sites to interconnect transparently through a service provider network. Within a VPN, each site can send IP packets to any other site in the same VPN.

There are several ways to configure BGP. We want to configure it our PE routers. We first search for PE routers in the _IntentFile.json_, and then, in the _generationConf.py_ file, we use the following `if` condition :

```
#Provider Edge :
    if router_type == "provider_edge":
        res.write(bgp_provider_edge(router,As,id,routers,ip_by_links,asList))
```

This code calls the function `bgp_provider_edge` defined in the _modules_ folder, which sets up BGP and MPLS VPN on a provider-edge router, on its interface with its neighbors, and on its Loopback : 

```
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

```

The provider-edge routers are now configured with BGP and are able to use MPLS VPN to route within private networks. 

## Phase 3

Lastly, we need to implement Clients to our network. We add 4 client-edge routers (CE) connected to the PE routers as in the following distribution : 

![Alt text](https://image.noelshack.com/fichiers/2024/15/2/1712676845-captura-de-pantalla-2024-04-09-173240.png)

We have 2 different types of clients : Client Green and Client Red. Indeed, our objective is to create a VPN Tunnel that allows machines belonging to a client to communicate in a private network with machines belonging to the same client but in another site, thus making use of MPLS VPN and BGP. 

If we want `R11` to communicate with `R9` without other routers knowing about the existance of the packets sent, we need to configure **VRF** in the PE routers and associate VRF to the PE-CE interfaces. In order to do this, we implement an entry in the  _IntentFile.json_ called `color` to identify different clients and therefore set up different VRF's. We also need to make sure the AS type is a client. We then iterate over the file and use the `vrf()` function, which allows us to configure the VRF. 

```
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
```

We make sure to set VRF only on PE routers : 

```
#Ecrire la VRF sur les liens EGP   
        if router_type == 'provider_edge' and adj['protocol-type']=='egp':
            neighbor = adj['neighbor']
            neighbor_as = routers[neighbor-1]['as']

            if 'color' in asList[neighbor_as-1]:
                res.write(" ip vrf forwarding " + asList[neighbor_as-1]['color'] + "\n")
```

We now use :
- A normal BGP configuration on the CE
- A normal BGP configuration on the VRF of the PE

Before moving on, we make sure that routes appear at the right place and that there is no leaking among customers.

## Deepening

Ultimately and as add-ins, we decided to implement some other caracteristics to our code.


#### Route reflector

We implemented the route reflector functionnality. This allows us to gain in rapidity in our network by placing an additional router in the network, called the "route reflector". Instead of the routers establishing BGP sessions with every other router, they are gonna establish its BGP session with the route reflector. The route reflector's task is then to distribute every routing table to the different routers, acting like some sort of hub that frees space in the network. 

In order to configure this setup, we need to configure "route reflector clients", these being the routers that are gonna be connected to the route reflector via BGP. The next step is to configure our PE routers so that they communicate only to the route reflector.

## How to run

In order to run our code, you will need to open the _Documents.gns3project_ file. This will open a GNS3 configuration where the routers in the network are deployed but have no internal configuration. 

You will then need to open a terminal, go to the _configuration_finale_, and run _generationConf.py_ :

```
cd path/to/configuration_finale
python generationConf.py
```
This will establish the configuration of every router in the network following the instructions given in _IntentFile.json_.


 
