#Must sometimes run the command, on windows Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Currentuser first!
#Inspired and picked some lines from https://github.com/dquercus/pioneeravclient/blob/master/pioneeravclient/clients.py

import requests
import json
import telnetlib
import time
import datetime
import logging
from time import sleep

IPRC = "192.168.1.239"
PortRC = "8102"
URLVI = "http://volumio.local:3000/api/v1/getstate"
URLRC = "http://192.168.1.239/StatusHandler.asp"
VolumeVI = ""
StatusVI = ""
StatusRC = ""
Stoppedtime = time.time()
Stoppedtimeset = False
logging.basicConfig(filename="logfile.log", level=logging.DEBUG)


#if reciever status er off og play status er play, send signal om å starte reciever, vent litt sett riktig input, vent litt sett riktig lydnivå
#if reciever status er on og play status er play, ikke gjør noe, nullstill teller for av
#if reciever status er off og play status er stop, ikke gjør noe
#if reciever status er on og play status er stop, vent 20 minutter, sjekk om play status er stop, hvis det skru av reciever.

def PioneerTN(cmd):
    command = cmd.encode('ascii', cmd) + b"\r\n"
    #print("command sent : ")
    logging.debug(command)
    tn = telnetlib.Telnet(IPRC,PortRC)
    tn.read_eager()
    tn.write(command)
    sleep(0.5)
    output = tn.read_eager().decode("utf-8").strip()
    tn.close()
    logging.debug(output)
    return(output)


def RampVolumeTo(volume):
    ExVolstring = PioneerTN("?V")
    ExVolsub = ExVolstring[3:]
    ExVolint = float(ExVolsub)
    logging.debug(ExVolint)
    logging.debug(volume)
    ramp = abs(volume - ExVolint)/10
    CurVolint = ExVolint
    while CurVolint < volume:
        CurVolint += ramp
        CurVolstr = str(CurVolint)
        if CurVolint < 100:
            CurVolstr = "0" + CurVolstr
        CurVolstrsub = CurVolstr[:3]
        PioneerTN(CurVolstrsub + "VL")
        sleep(0.25)
    while CurVolint > volume:
        CurVolint -= ramp
        CurVolstr = str(CurVolint)
        if CurVolint < 100:
            CurVolstr = "0" + CurVolstr
        CurVolstrsub = CurVolstr[:3]
        PioneerTN(CurVolstrsub + "VL")
        sleep(0.25)

def Mainprogram():
    global Stoppedtime, Stoppedtimeset
    v = requests.get(url = URLVI)
    v_dict = v.json()
    logging.debug(v_dict["status"])
    StatusVI = v_dict["status"]
    VolumeVI = v_dict["volume"]
    if StatusVI == "pause":
        StatusVI == "stop"
    StatusRC = PioneerTN("?P")
    logging.debug(StatusRC)
    #if reciever status er off og play status er play, send signal om å starte reciever, vent litt sett riktig input, vent litt sett riktig lydnivå
    if StatusVI == "play":
        if StatusRC == "PWR1":
            logging.debug("Power on reciever")
            PioneerTN("PO")
            sleep(6)
            PioneerTN("04FN")
            sleep(1)
            RampVolumeTo(131)
    #if reciever status er on og play status er stop, vent 20 minutter, sjekk om play status er stop, hvis det, sett input til TV og skru av reciever.
    if StatusVI == "stop":
        if StatusRC == "PWR0":
            if Stoppedtimeset == False:
                Stoppedtime = time.time()
                Stoppedtimeset = True

            if time.time() - Stoppedtime>60 * 15: #Shut down after 15 minutes
                logging.debug("Power off Reciever")
                PioneerTN("05FN") #Setter input til TV
                RampVolumeTo(101)
                sleep(6)
                PioneerTN("PF")
                Stoppedtimeset = False #For å resette timer
            logging.debug(time.time() - Stoppedtime)

    #if reciver status er on og play status er play
    if StatusVI == "play":
        if StatusRC == "PWR0":
            #last_time = open(timerfile, "r") # Her er målet å skrive tiden til en fil, så vente 30 min, så skru av rec.
            Stoppedtimeset = False #For å resette timer
            #timediff = current_time - last_time
            #outputfile = open(timerfile,"w")
            #outputfile.write(current_time)
            #print(timediff)


while True:
    logging.debug(time.ctime())
    Mainprogram()
    sleep(5)
