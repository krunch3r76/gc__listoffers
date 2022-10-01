# broca.py
# retrieve messages from an array of messages, building each message applying rules such as substition

import random

random.seed()

dialogs = []
dialog1 = {
    "script": "greetings. please press refresh to see the providers on the default"
    " subnet, public-beta.\n\n",
    "substitutions": {
        "greetings": ["howdy", "hello", "hey"],
        "press": ["click"],
        "Note": ["Be advised", "Heads up"],
        "see": ["find"],
        "listed": ["displayed"],
    },
}
dialogs.append(dialog1)

dialog2 = {
    "script": "i am now collecting offers broadcast on the provider network.\n\n"
    "this may take some time especially if it has been awhile since"
    " i last checked. also, i do not always get all the offers, so"
    " if the number seems low, please refresh again.",
    "substitutions": {
        "collecting": ["gathering", "searching for"],
        "broadcast": ["transmitted"],
        "awhile": ["a long time", "like forever"],
        "number": ["count"],
        "refresh": ["press refresh"],
    },
}

dialog2 = {
    "script": "i am now attempting to make an outbound connection to "
    "https://stats.golem.network to obtain the provider listing. "  #        "failing this, i will fallback to probe for offers manually, "\
    #        "in which case this might take a few minutes!"
    ,
    "substitutions": {
        "attempting": ["trying"],
        "to make an outbound connection to": ["to connect with"],
        "a few minutes": ["awhile"],
    },
}
dialogs.append(dialog2)

dialog3 = {
    "script": "this sure is taking awhile. don't fret. i'll have some"
    " offers for you soon enough.",
    "substitutions": {
        "awhile": ["long time"],
        "fret": ["stress"],
        "soon enough": ["before long"],
    },
}
dialogs.append(dialog3)

dialog4 = {
    "script": "okay, the offers i found are displayed in the table" " above. you can press ENTER on the filter fields to apply a particular filter.",
    "substitutions": {
        "okay": ["super", "great", "excellent", "yipee", "perfect"],
        "found": ["discovered"],
        "displayed": ["represented"],
        "count": ["total", "number"],
        "refresh": ["press refresh"],
    },
}
dialogs.append(dialog4)


dialog5 = {
    "script": "uh oh! it looks like your API key is unset or invalid."
    "please paste a valid key into the entry field next to manual probe"
    " or make sure the environment variable has been set to YAGNA_APPKEY."
    " if you don't know what to do, please refer to the README on github."
    " Also, make sure yagna (or golemsp) is running and that the yapapi sdk has been installed.",
    "substitutions": {"uh oh!": ["oh gosh!", "oh-my-gosh!", "oh bother."]},
}
dialogs.append(dialog5)


dialog6 = {
    "script": "wtf! i didn't get any results."
    " this is most unusual. i am not equipped for this."
    " sorry i can't be of more help here!",
    "substitutions": {
        "wtf!": ["holy cow!", "oh man!", "dude!", "holy crap!", "oh sh*t!"],
        "unusual": ["bizarre"],
        "i am not equipped for this.": ["i didn't sign up for this."],
    },
}
dialogs.append(dialog6)


dialog7 = {
    "script": "uh oh! it looks like your API key for the server is invalid."
    " please check it and paste it to the manual probe entry field on the bottom."
    " or you can export the environment variable on the server side, YAGNA_APPKEY, as well and then run the server again."
    " if you don't know what to do, please refer to the README on github.",
    "substitutions": {"uh oh!": ["oh gosh!", "oh-my-gosh!", "oh bother."]},
}
dialogs.append(dialog7)


dialog8 = {
    "script": "the remote connection failed. please make sure you are running a separate"
    " instance of the application and that the ip address and port are accessible!",
    "substitutions": {
        "failed": ["could not be made.", "rejected the connection attempt."],
        "make sure": ["ensure"],
    },
}
dialogs.append(dialog8)

dialog9 = {
    "script": "uh oh, it looks like yagna is not running."
    " be sure you are running either yagna or golemsp!",
    "substitutions": {"uh oh": ["oh crap", "oh bother"], "make sure": ["ensure"]},
}
dialogs.append(dialog9)


dialog10 = {
    "script": "i am now collecting offers directly from"
    " the network. this may take awhile",
    "substitutions": {"now": ["currently", "presently"], "take awhile":
        ["take some time", "be awhile", "a few minutes at first"]},
}
dialogs.append(dialog10)
def yes_or_no():
    """randomly return T or F"""
    flip = random.getrandbits(1)
    return True if flip == 1 else False


def fetch_new_dialog(idx):
    """take a dialogue, make random word substitions, and return the dialog"""
    original = (dialogs[int(idx)])["script"]
    built = original
    for key, val in dialogs[idx]["substitutions"].items():
        if yes_or_no():
            choice_count = len(val)
            built = built.replace(key, val[random.randrange(0, choice_count)])
    return built
