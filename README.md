# gc__listoffers
a gui frontend to offer listings on the Golem network

the desktop is back! what? you like the pretty json stuff? then go back to stats.golem.network then! for the rest of us that have no aesthetic sense whatsoever, I present you you gc__listoffers. that said, expect this interface to be klunky for awhile as it needs much work.

the problem gc__listoffers solves is 1) for providers to see at a cursory glance how competitive they are on mainnet given prices they have set for cpu and environment, 2) for requestors to tweak a market strategy on a run-per-run basis.

**NOTE: although this will work when golemsp instead of yagna is running, you will only be able to see other providers, not yourself!**

# requirements
**YAGNA_APPKEY must be in your environment for this to run successfuly**.
either yagna or golemsp must be running
yapapi must be installed

```bash
$ pip install yapapi -U
# start yagna or golemsp
$ yagna service run
$ # golemsp run
```
note: this is under heavy development and the gui may sometimes be unresponsive

# usage
first clone it:
```bash
$ git clone https://github.com/krunch3r76/gc__listoffers.git
$ cd gc__listoffers
$ git checkout v0.0.1
```

## starting
### starting locally
```bash
./gc__listoffers $ python3 application.py
```

### starting for remote interaction
```bash
# on the machine running yagna/golemsp, e.g. in docker
(server) ./gc__listoffers $ python3 application.py serve localhost 8000

# on the remote machine (Windows okay)
(client) ./gc__listoffers $ python3 applicaion.py client <ip-address-of-server> 8000
```

## usage tips
touch the radio button pertaining to the subnet of interest
offer scanning can take up to a minute, please be patient
check the boxes to set upper limits on cpu time and env time
it is not necessary to refresh when tweaking values!
the total number of offers is listed in large digits near the bottom left


# TODO
this is a very long list but i will start it with:
1) provide features to interop with gc__filterms (https://github.com/krunch3r76/gc__filterms)
2) prevent gui lockups
3) provide view/column customization
