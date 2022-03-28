# gc__listoffers
a gui frontend to offer listings on the Golem network

the desktop is back! what? you like the pretty js stuff? then go back to stats.golem.network then! for the rest of us that have no aesthetic sense whatsoever, I present you with gc__listoffers. that said, expect this interface to be klunky for awhile as it needs much work.

the problem gc__listoffers solves is 1) for providers to see at a cursory glance how competitive they are on mainnet given prices they have set for cpu and environment, 2) for requestors to tweak a market strategy on a run-per-run basis in an informed way

**PEACE OF MIND: THIS IS A COMPLETELY FREE SERVICE. it does not spend any glm. the app-key may be necessary, however, to get information about providers**

**NOTE: you will see yourself listed among the results unless the probe for offers was made manually (non-default)**

# quick install
head over to releases and download the zip or tar file from the latest release. extract and double click gc__listoffers.py

# video

https://user-images.githubusercontent.com/46289600/160338409-5b0456fd-4ad7-4613-8900-e9f71c987bb3.mp4

this video demos basic functionality


https://user-images.githubusercontent.com/46289600/155652172-654b37b5-7669-4f1c-bb18-b47fe8bc4053.mp4

this video demonstrates interop with gc_spyu to add model information


# check for new / latest release tag
```bash
(gc_listoffers)$ git fetch
From github.com:krunch3r76/gc__listoffers
   d87b579..01f72be  master     -> origin/master
 * [new tag]         v0.5.8     -> v0.5.8
```

# upgrade installation to latest tag, wiping current installation
```bash
(gc__listoffers)$ git checkout main
(gc__listoffers)$ git reset --hard HEAD
(gc__listoffers)$ git pull
(gc__listoffers)$ git clean -dfx
(gc__listoffers)$ git checkout v0.5.8
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
./gc__listoffers$ git checkout v0.5.8
./gc__listoffers$ python3 gc__listoffers.py
```
On Windows:
```cmd
REM clone as above
.\gc__listoffers> python gc__listoffers.py
```

# how to interpet the interface
if name or address headings are clicked on, sorting is strictly on either of these. however, if you click any of the other columns, sorting occurs from left to right, first sorting on the far left, then next level on the right, and so on.

# requirements

yapapi must be installed

for systems that do not allow https outbound connection, either yagna or golemsp must be running and the app-key should be in the environment (see section on app-key for details)

_python should have been compiled with Tcl support_. this is the default on Windows. this is available as a package on ubuntu. see below. 

**if https connections are not allowed on your machine, it is necessary to be running yagna or golemsp, see the advanced section for this**


## usage tips
touch the radio button pertaining to the subnet of interest

offer scanning can take up to a minute, please be patient, maybe try your hand at a picasso replica

check the boxes to set upper limits on cpu time and env time. go to https://stats.golem.network and use the median values for cpu and env time as a starting point

it is not necessary to refresh when tweaking values!

the total number of offers is listed in large digits near the right

see offer details via the contextual menu system!



# advanced
### starting for remote interaction (for systems without internet connectivity besides golem)
```bash
# on the machine running yagna/golemsp, e.g. in docker, wsl, vmware
$ export YAGNA_APPKEY=<appkey> # if not already done. see section "what is an app key?" below on getting it 
(server) ./gc__listoffers (myvenv) $ python3 gc__listoffers.py serve localhost 8000

# on the remote machine (Windows okay)
(client) ./gc__listoffers $ python3 gc__listoffers.py client <ip-address-of-server> 8000
```

## what is an app key?
an app key is what requestors use to run requests. to find and set your app key before running gc__listoffers and looking up the pertinent name:
```bash
$ yagna app-key list --json
{
  "headers": [
    "name",
    "key", # this tells you that the key comes at the 2nd position in valeues <see below>
    "id",
    "role",
    "created"
  ],
  "values": [
    [
      "golem-cli",
      "591184ff4e7d495aa32ce16c0c72228a", # this is the app key when golemsp is running
      "0xe50dd37bbd930b1bb860010385056ee016b392c3",
      "manager",
      "2021-11-13T01:36:34.907106973"
    ]
  ]
}
$ export YAGNA_APPKEY=591184ff4e7d495aa32ce16c0c72228a # use your key not mine
$ python3 ./gc__listoffers.py
```

# TODO
this is a very long list but i will start it with:
- provide more features to interop with gc__filterms (https://github.com/krunch3r76/gc__filterms)
- provide view/column customization
- add more graphics and sound! hey this is python not python GS (obscure reference to Steve Woz)
