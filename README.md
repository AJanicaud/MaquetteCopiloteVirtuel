# IHM & IA pour un copilote virtuel

**ISAE-Supaéro - projet de 3e année**

## Contexte

Dans le cadre du Projet Innovation et Entrepreneuriat de dernière année à l'ISAE-Supaéro, une étude des possibilités de copilote virtuel pour aider le pilote, notamment en situation de stress, a été réalisée par Thibaud Durivaux, Valentin Ligier, Paul Legoux, Quentin Zerguini et Noé Aurelle (2017-2018).

Ce dépôt contient le code source de la maquette dynamique créée afin d'illustrer une application simple, reposant sur une tablette (sous forme de web app), avec commandes vocales basiques, et faisant usage du simulateur de vol [FlightGear](http://home.flightgear.org/).

Le dossier `snippets` contient la partie extraction des données météo à partir du modèle Arome de Météo France ([site officiel](https://donneespubliques.meteofrance.fr) : Données de modèle atmosphérique à aire limitée à haute résolution), non intégrée à la maquette (dans laquelle les données de vent sont fixées arbitrairement).

## Architecture de la maquette

La maquette est composée de trois parties principales :

* _front-end_: page web dynamique (HTML/CSS/JavaScript) ;
* _back-end_: ensemble de scripts réalisant le traitement des données (Python) ;
* serveur web: lien entre _front-end_ et _back-end_ (Node.js).

Un schéma synoptique (**Architecture.png**) résume l'ensemble des blocs utilisés ainsi que leurs interactions.

## Utilisation de la maquette

Les trois différentes parties de la maquette, ainsi que FlightGear, peuvent être exécutées sur des ordinateurs différents sur le même réseau. L'usage typique est de tout lancer sur le même ordinateur, à l'exception de la page web qui peut être ouverte sur une tablette.

L'ordre d'exécution n'importe que pour `main.py`.

Dans 3 consoles séparées :

* __FlightGear__: `fgfs --telnet=socket,out,60,localhost,5555,udp`
* __Serveur__: `cd nodeServer ; node launch.js`
* __*Front-end*__: Navigateur web vers [http://localhost:8080](http://localhost:8080)
* __*Back-end*__: `cd main ; python main.py`

Les mots reconnus sont, dans l'ordre d'exécution :

* déroutement ;
* LFCL, LFBO ou LFBR ;
* retour.
