# gc__listoffers
a gui frontend to offer listings on the Golem network

the desktop is back! what? you like the pretty js stuff? then go back to stats.golem.network then! for the rest of us that have no aesthetic sense whatsoever, I present you with gc__listoffers. that said, expect this interface to be klunky for awhile as it needs much work.

the problem gc__listoffers solves is 1) for providers to see at a cursory glance how competitive they are on mainnet given prices they have set for cpu and environment, 2) for requestors to tweak a market strategy on a run-per-run basis in an informed way

**PEACE OF MIND: THIS IS A COMPLETELY FREE SERVICE. it does not spend any glm. the app-key may be necessary, however, to get information about providers**

**NOTE: you won't see yourself listed among the results unless the probe for offers was made over stats (disabled feature)**

# quick install
head over to releases and download the zip or tar file from the latest release. extract and double click gc__listoffers.py

# video

https://user-images.githubusercontent.com/46289600/160338409-5b0456fd-4ad7-4613-8900-e9f71c987bb3.mp4

this video demos basic functionality

# check for new / latest release tag
```bash
(gc_listoffers)$ git fetch
From github.com:krunch3r76/gc__listoffers
   d87b579..01f72be  master     -> origin/master
 * [new tag]         v0.10.2     -> v0.10.2
```

# upgrade installation to latest tag, wiping current installation
```bash
(gc__listoffers)$ git checkout main
(gc__listoffers)$ git reset --hard HEAD
(gc__listoffers)$ git pull
(gc__listoffers)$ git clean -dfx
(gc__listoffers)$ git checkout v0.10.2
```
# usage
## ensure python3-tk is installed
```bash
(ubuntu) $ sudo apt-get install python3-tk
```
## clone, setup python environment, and run
```bash
$ git clone https://github.com/krunch3r76/gc__listoffers.git
$ cd gc__listoffers
./gc__listoffers$ git checkout v0.10.2
./gc__listoffers$ python3 gc__listoffers.py
```
On Windows:
```cmd
REM clone as above (or double click from explorer)
.\gc__listoffers> python gc__listoffers.py
```

# how to interpet the interface
if name or address headings are clicked on, sorting is strictly on either of these. however, if you click any of the other columns, sorting occurs from left to right, first sorting on the far left, then next level on the right, and so on.

# requirements
yagna or golemsp version v0.12.0++ (beginning with Marble Castle)
```bash
$ curl -sSf https://join.golem.network/as-requestor | bash -
```

yapapi
```bash
$ pip install -U yapapi
```

either yagna or golemsp must be running
```bash
$ yagna service run
```

the app-key should be in the environment (see section on app-key for details)

_python should have been compiled with Tcl support_. this is the default on Windows. this is available as a package on ubuntu. see below. 


## usage tips
touch the radio button pertaining to the subnet of interest

offer scanning can take up to a few minutes, please be patient, maybe try your hand at a picasso replica

check the boxes to set upper limits on cpu time and env time. go to https://stats.golem.network and use the median values for cpu and env time as a starting point

it is not necessary to refresh when tweaking values!

the total number of offers is listed in large digits near the right

see offer details via the contextual menu system!

red nodes are nodes on the tglm payment network (testing payment network)


## what is an app key?
an app key is what requestors use to run requests. to find and set your app key before running gc__listoffers and looking up the pertinent name:
```bash
$ yagna app-key list --json
[
  {
    "created": "2022-11-29T07:31:46.995858851",
    "id": "0x19ca46449dd7a8a4acf91313c8641981ca65b6f0",
    "key": "66f80425db2b48fabe8cf11e27377dc4",
    "name": "golem-cli",
    "role": "manager"
  }
]
$ export YAGNA_APPKEY=66f80425db2b48fabe8cf11e27377dc4# use your key not mine
$ python3 ./gc__listoffers.py
```
follow a similar logic for Windows

# troubleshooting
if the console helper reports not understanding why it got no results, your yapapi library is most likely not up to date. please run `pip install yapapi -U`

# advanced (TEMPORARILY NON-APPLICABLE)
### starting for remote interaction (for systems without internet connectivity besides containerized golem)
**REMOTE INTERACTION IS BROKEN, IT WILL BE FIXED SOON**
```bash
# on the machine running yagna/golemsp, e.g. in docker, wsl, vmware
$ export YAGNA_APPKEY=<appkey> # if not already done. see section "what is an app key?" below on getting it 
(server) ./gc__listoffers (myvenv) $ python3 gc__listoffers.py serve localhost 8000

# on the remote machine (Windows okay)
(client) ./gc__listoffers $ python3 gc__listoffers.py client <ip-address-of-server> 8000
```

# TODO
this is a very long list but i will start it with:
- provide more features to interop with gc__filterms (https://github.com/krunch3r76/gc__filterms)
- provide view/column customization
- add more graphics and sound! hey this is python not python GS (obscure reference to Steve Woz)
