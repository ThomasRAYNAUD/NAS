# Network Automation Project


## Presentation
The aim of the project is to write a code that deploys routing protocols across a given network. The network specificities are defined in an `intent_file`. The addressing will be done using **IPv4** addresses.


## First approach
We start by setting a network consisting of 4 routers as shown in Figure 1 : 2 of them are gonna be our provider-edges (PE) and 2 are gonna be our providers (P). Indeed, our first stage is to setup an **MPLS** core formed by these routers. We give each interface an IPv4 address and setup **OSPF(v2)** between them as the IGP protocol. MPLS labels are gonna get assigned on the basis of the routes defined by OSPF. We make sure to assign IP addresses to the loopback of each router so OSPF can trace routes to them. This will help since one of the steps of MPLS Labels advertising is assigning a lable to the loopback of a router.

![Alt text](https://image.noelshack.com/fichiers/2024/13/5/1711706991-captura-de-pantalla-2024-03-29-110916.png)


We are gonna be setting MPLS and **LDP** to route data packets using labels. This will be useful later when we add Clients, since our final objective is to automate the provisioning of BGP/MPLS VPN services in the example of Internet Services. 


#### Automation

In order to automate the deployment of router configuration, we need to create a code that allows us to manipulate the consoles of each router in the GNS3 project from distance. We decided to use the **telnet** protocol, which allows us to establish TCP/IP connexions and access a distant machine. We will be working on the basis of our existing code for the GNS Project we did earlier this year. 

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

- We then go over the _intentFile.json_, where every AS and router of the network is precised, along with its IPv4 addresses, its type, its neighbors, and more. Thanks to **telnet** and by running `if` tests we configure every router. There is a different setup function for all 3 protocols and situations, as well as for making the address plan of the network. A configuration of a random router in the _intentFile.json_ can be seen in the image below.


![Alt text](https://image.noelshack.com/fichiers/2024/15/2/1712668344-captura-de-pantalla-2024-04-09-151210.png)


## Phase 1

After we set up the initial network and we manage to route and forward packets using OSPF(v2), the next phase is to set up **MPLS** and **LDP**, thus creating a MPLS core. This is done thanks to **telnet** and the `res.write()` function, which allows us to write a string into a file. The `res` object allows us to create a path to the _RouterConfigs_ file, where all the configurations of the routers will be written. The configuration of MPLS is done by running the following code : 

```
#Activer MPLS sur tous les liens IGP des provider
        if (As_type == 'provider' and adj['protocol-type']=='igp'):
            res.write(f" mpls ip\n mpls label protocol ldp\n")
```

This sets up MPLS and attributes label advertising to LDP. The configuration is found on the internet. 
Before moving onto the next phase, we make sure :
- LDP session states
- MPLS transport in the core
- Penultimate Hop Popping behaviour

## Phase 2

We now wish to implement **BGP** on the client sites using a **VPN** feature. When used with MPLS, the VPN feature allows several sites to interconnect transparently through a service provider network. Within a VPN, each site can send IP packets to any other site in the same VPN.

There are several ways to configure BGP. We decide to configure our PE routers. We first search for PE routers in the _IntentFile.json_, and then in the _generationConf.py_ file configuration for BGP, we see the following code :
```
#Provider Edge :
    if router_type == "provider_edge":
        res.write(bgp_provider_edge(router,As,id,routers,ip_by_links,asList))
```

This code a function called `bgp_provider_edge` and defined in the _modules_ folder. This function sets up BGP and MPLS VPN on a provider-edge router, on its interface with its neighbors as well as on its Loopback : 

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

Lastly, we need to implement Clients to our network. We add 4 client-edge routers (CE) connected to the PE routers as in the following disposition : 

![Alt text](https://image.noelshack.com/fichiers/2024/15/2/1712676845-captura-de-pantalla-2024-04-09-173240.png)

We have 2 different types of clients : Client Green and Client Red. Indeed, our objective is to create a VPN Tunnel that allows machines belonging to a client to communicate in a private network with machines belonging to the same client but in another sit, thus using MPLS VPN and BGP to create tunnels. 

## Deepening
Ultimately and as add-ins, we decided to implement some other caracteristics to our code.

## How to run



Finally, we achieve to automate the setting of almost any network, as long as an `intent_file` clarifying the specificities of this network is given. We decided to use the following network as a test for a more complex topology : 


![Alt text](https://image.noelshack.com/fichiers/2024/05/2/1706629657-image.png)


The results are satisfactory : the net work has been set up by our code.
 
