## Preparation

Use Ubuntu == 20.04

Use bootstrap/okeanos.service to create a ubuntu service in each node.

Then copy the remaining files in bootstrap/ except bootstrap_network.py to /root of each node

On each node, install anaconda and tendermint==0.34.15

Use conda to build a env called okeanos according to environment.yml

## Start network

In local machine create a csv called node_ips.csv and write 33 nodes' ip and name like:

```
okeanos000,1.1.1.1
okeanos001,2.2.2.2
...,...
okeanos032,32.32.32.32
```

Put node_ips.csv and sk.pem of those nodes with bootstrap/bootstrap_network.py

Then run:

```
python bootstrap_network.py
```

 

## Use Lucust to test nodes
In each nodes, upload test file in test/

Use conda to install Lucust

Then run command like:

```
python testOkeanosCW_SW.py 500
```
