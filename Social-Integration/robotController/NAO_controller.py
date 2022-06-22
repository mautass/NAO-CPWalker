# -*- coding: cp1252 -*-
import sys
import qi
import resources.dialogs as dialogs
import soundTracker as soundTracker
import logging
import time as t
from time import time
import random


class RobotController(object):

    def __init__(self, settings={'name': "NAO",
                                 'ip': '192.168.1.101',
                                 'port': 9559,
                                 'UseSpanish': True,
                                 'MotivationTime': 300000000,
                                 'HeartRate_Lim': 140,
                                 'Cerv_Lim': 0,
                                 'Thor_Lim': 0

                                 }):

        self.settings = settings
        self.ip = self.settings['ip']
        self.port = self.settings['port']
        self.useSpanish = self.settings['UseSpanish']
        self.patient = None

        self.session = qi.Session()
        try:
            self.session.connect("tcp://" + self.ip + ":" + str(self.port))

        except RuntimeError:
            logging.debug("Can't connect to Naoqi at ip \"" + self.ip + "\" on port " + str(self.port) + ".\n"
                                                                                                         "Please check your script arguments. Run with -h option for help.")
            sys.exit(1)

        self.robotName = self.settings['name']
        self.HR_lim = self.settings['HeartRate_Lim']
        self.Cer_lim = self.settings['Cerv_Lim']
        self.Thor_lim = self.settings['Thor_Lim']
        self.dialogs = dialogs.Dialogs()

        self.go_on = True
        self.soun_ON = None

        # Updating the services of the robot

        # Load memory services to recognize events
        self.memory = self.session.service("ALMemory")

        # Load AlTextToSpeech
        self.tts = self.session.service("ALTextToSpeech")
        self.setLanguage('Spanish')

        # Load animated speech service
        self.animatedSpeechProxy = self.session.service("ALAnimatedSpeech")

        # Load motion service
        self.motion = self.session.service("ALMotion")

        # Load posture service
        self.posture = self.session.service("ALRobotPosture")

        # Load tracker service
        self.tracker = self.session.service("ALTracker")

        # Create the sound tracker of the robot
        self.soundTracker = soundTracker.Sound_Detector()

        # Load behaviors services
        self.behavior_mng_service = self.session.service("ALBehaviorManager")
        self.behavior_mng_service.stopAllBehaviors()


        self.flag_Sound = True
        self.launchDialogs()

        """
        Counters
        """
        self.cont_BrazoDr = 1
        self.act_BrazoDr = None
        self.BD_activado = False

        self.cont_BrazoIz = 1
        self.act_BrazoIz = None
        self.BI_activado = False

        self.cont_PiernaDr = 1
        self.act_PiernaDr = None
        self.PD_activado = False

        self.cont_PiernaIz = 1
        self.act_PiernaIz = None
        self.PI_activado = False

        self.cont_cabeza = 1
        self.act_cabeza = None
        self.cab_activado = False

        self.cont_elefante = 1
        self.act_elefante = None
        self.elef_activado = False

        self.cont_mono = 1
        self.act_mono = None
        self.mono_activado = False

        self.cont_ave = 1
        self.act_ave = None
        self.ave_activado = False

        self.cont_raton = 1
        self.act_raton = None
        self.raton_activado = False

        self.tiempo_no_repx = 0
        self.tiempo_no_repv = 0

    def setLanguage(self, value):
        self.tts.setLanguage(value)

    def setVolume(self, value):
        curr_Vol = self.tts.getVolume()
        print(curr_Vol)
        self.tts.setVolume(value)

    def launchDialogs(self):
        # loading dialogs
        self.dialogs.load_dialogs()

    def start_Introduction(self):
        # Function to start the introduction with NAO

        self.motion.wakeUp()
        self.animatedSpeechProxy.say(self.dialogs.WelcomeSentence)

    def launch_SoundTracker(self):

        print('launching Sound tracker')
        self.soundTracker.on_Start()
        self.soundTracker.launch_thread()
        t.sleep(2)
        self.cont = 0
        while self.flag_Sound == True:
            t.sleep(2)
            self.sound = self.soundTracker.got_sound
            print(self.sound)
            self.say_Hello(self.sound)

    def tracking_faces(self):
        # targetName = "Face"
        # faceWidth = 0.1
        # self.tracker.registerTarget(targetName, faceWidth)
        #
        # # start tracker.
        # self.tracker.track(targetName)
        time.sleep(1)

    def say_Hello(self, value):

        if value == True:
            print("Say Hello to the patient")
            t.sleep(2)
            s = self.dialogs.get_welcome_sentence()
            s = s.replace('XX', self.patient['name'])
            self.animatedSpeechProxy.say(s)
            self.soundTracker.shutdown()
            self.flag_Sound = False

        elif (value == False):
            self.cont = self.cont + 1
            print(self.cont)
            if (self.cont == 1):
                self.tts.say(self.dialogs.noListeningSentence)
            if self.cont == 10:
                self.cont = 0

    def load_selfPresentation(self):
        # Set the robot self presentation
        self.motion.wakeUp()
        self.behavior_mng_service.runBehavior('robot_intro-f8648f/behavior_1')

    def load_patientPresentation(self):
        # Set the behavior to introduce patient presentation
        self.behavior_mng_service.runBehavior('intro_yourself-883ef7/behavior_1')

    def load_standUp(self):
        # Set the robot self presentation
        self.behavior_mng_service.runBehavior('standup-d44a55/behavior_1')

    def load_ElephantBehavior(self):
        self.act_elefante = True
        self.elef_activado = True
        self.act_BrazoDr = False
        self.act_BrazoIz = False
        self.act_PiernaDr = False
        self.act_PiernaIz = False
        self.act_cabeza = False
        self.act_mono = False
        self.act_ave = False
        self.act_raton = False
        # Set the behavior to make an elephant
        self.load_standUp()
        self.behavior_mng_service.runBehavior('elephant-7550d5/behavior_1')

    def load_MouseBehavior(self):
        self.act_raton = True
        self.raton_activado = True
        self.act_elefante = False
        self.act_BrazoDr = False
        self.act_BrazoIz = False
        self.act_PiernaDr = False
        self.act_PiernaIz = False
        self.act_cabeza = False
        self.act_mono = False
        # Set the behavior to make an elephant
        self.load_standUp()
        self.behavior_mng_service.runBehavior('mouse-286ea0/behavior_1')

    def load_gorillaBehavior(self):
        self.act_mono = True
        self.mono_activado = True
        self.act_elefante = False
        self.act_BrazoDr = False
        self.act_BrazoIz = False
        self.act_PiernaDr = False
        self.act_PiernaIz = False
        self.act_cabeza = False
        self.act_ave = False
        self.act_raton = False
        # set the behavior to make a gorilla
        self.load_standUp()
        self.behavior_mng_service.runBehavior('gorilla-b5bbf5/behavior_1')

    def load_butterflyBehavior(self):
        self.ave_activado = True
        self.act_ave = True
        self.act_elefante = False
        self.act_BrazoDr = False
        self.act_BrazoIz = False
        self.act_PiernaDr = False
        self.act_PiernaIz = False
        self.act_cabeza = False
        self.act_mono = False
        self.act_raton = False
        # ser the behavior to make a butterfly
        self.load_standUp()
        self.behavior_mng_service.runBehavior('butterfly-fe943b/behavior_1')

    def load_HeadExplanation(self):
        self.cab_activado = True
        self.act_cabeza = True
        self.act_elefante = False
        self.act_BrazoDr = False
        self.act_BrazoIz = False
        self.act_PiernaDr = False
        self.act_PiernaIz = False
        self.act_mono = False
        self.act_ave = False
        self.act_raton = False

        # set the behavior to make move the robot's head
        self.load_standUp()
        self.behavior_mng_service.runBehavior("cabeza-882689/behavior_1")

    def load_ArmLExplanation(self):
        self.BI_activado = True
        self.act_BrazoIz = True
        self.act_elefante = False
        self.act_BrazoDr = False
        self.act_PiernaDr = False
        self.act_PiernaIz = False
        self.act_cabeza = False
        self.act_mono = False
        self.act_ave = False
        self.act_raton = False
        # set the behavior to make move the robot's left arm
        self.load_standUp()
        self.behavior_mng_service.runBehavior('nao1_brazoiz-329b85/behavior_1')

    def load_ArmRExplanation(self):
        self.BD_activado = True
        self.act_BrazoDr = True
        self.act_elefante = False
        self.act_PiernaDr = False
        self.act_BrazoIz = False
        self.act_PiernaIz = False
        self.act_cabeza = False
        self.act_mono = False
        self.act_ave = False
        self.act_raton = False
        # set the behavior to make move the robot's right arm
        self.load_standUp()
        self.behavior_mng_service.runBehavior('brazodr-ef940c/behavior_1')

    def load_LegLExplanation(self):
        self.PI_activado = True
        self.act_PiernaIz = True
        self.act_elefante = False
        self.act_BrazoDr = False
        self.act_BrazoIz = False
        self.act_PiernaDr = False
        self.act_cabeza = False
        self.act_mono = False
        self.act_ave = False
        self.act_raton = False
        # set the behavior to make move the robot's left leg
        self.load_standUp()
        self.behavior_mng_service.runBehavior('piernaiz2-9b6b62/behavior_1')

    def load_LegRExplanation(self):
        self.PD_activado = True
        self.act_PiernaDr = True
        self.act_elefante = False
        self.act_BrazoDr = False
        self.act_BrazoIz = False
        self.act_PiernaIz = False
        self.act_cabeza = False
        self.act_mono = False
        self.act_ave = False
        self.act_raton = False
        # set the behavior to make move the robot's right leg
        self.load_standUp()
        self.behavior_mng_service.runBehavior('piernadr-8fd733/behavior_1')

    def load_name(self):
        # set the behavior to ask the patient's name
        self.load_standUp()
        self.behavior_mng_service.runBehavior('nombre-e64e27/behavior_1')

    def load_age(self):
        # set the behavior to ask the patient's age
        self.load_standUp()
        self.behavior_mng_service.runBehavior('edad-37b6a6/behavior_1')

    def load_activity(self):
        # set the behavior to show it's taichi movement
        self.load_standUp()
        self.behavior_mng_service.runBehavior('actividad-0b56b7/behavior_1')

    def load_bye(self):
        # set the behavior to make move the robot's head
        self.load_standUp()
        self.behavior_mng_service.runBehavior('adios-65b195/behavior_1')

    def load_Speech(self, speech):
        s = speech
        self.animatedSpeechProxy.say(s)

    def load_Right(self):
        tiempo2 = time()
        if (tiempo2 - self.tiempo_no_repv) > 5:
            if self.act_ave is False and self.act_mono is False and self.act_raton is False and self.act_elefante is False:
                print("1")
                self.load_standUp()
                behaviors = ['check_1-dc0fc5/behavior_1', 'check_2-2f6680/behavior_1', 'check_3-5a98d4/behavior_1']
                i = random.randint(0, len(behaviors) - 1)
                self.behavior_mng_service.runBehavior(behaviors[i])
            elif self.act_raton:
                print("2")
                self.load_standUp()
                self.behavior_mng_service.runBehavior('check_rat-247c4e/behavior_1')
            elif self.act_elefante:
                print("3")
                self.load_standUp()
                self.behavior_mng_service.runBehavior('check_elephant-c1d94c/behavior_1')
            elif self.act_ave:
                print("4")
                self.load_standUp()
                self.behavior_mng_service.runBehavior('check_bird-7b958f/behavior_1')
            elif self.act_mono:
                print("45")
                self.load_standUp()
                self.behavior_mng_service.runBehavior('check_monkey-3de8fa/behavior_1')

            self.tiempo_no_repv = time()
        else:
            print("No porque han pasado: " + str(tiempo2 - self.tiempo_no_repv))
            t.sleep(1)

    def load_Wrong(self):
        tiempo1 = time()

        if (tiempo1 - self.tiempo_no_repx) > 5:
            self.load_standUp()
            behaviors = ['no-0ef1d3/behavior_1', 'no_1-53de65/behavior_1', 'no_2-8f9f45/behavior_1']
            i = random.randint(0, len(behaviors) - 1)
            self.behavior_mng_service.runBehavior(behaviors[i])
            """
            Check which activity we are in and count the number of times the patient makes a mistake
            """
            if self.act_BrazoDr:
                self.cont_BrazoDr = self.cont_BrazoDr + 1
            elif self.act_BrazoIz:
                self.cont_BrazoIz = self.cont_BrazoIz + 1
            elif self.act_PiernaDr:
                self.cont_PiernaDr = self.cont_PiernaDr + 1
            elif self.act_PiernaIz:
                self.cont_PiernaIz = self.cont_PiernaIz + 1
            elif self.act_cabeza:
                self.cont_cabeza = self.cont_cabeza + 1
            elif self.act_elefante:
                self.cont_elefante = self.cont_elefante + 1
            elif self.act_mono:
                self.cont_mono = self.cont_mono + 1
            elif self.act_ave:
                self.cont_ave = self.cont_ave + 1
            elif self.act_raton:
                self.cont_raton = self.cont_raton + 1

            self.tiempo_no_repx = time()
        else:
            print("No porque han pasado: " + str(tiempo1 - self.tiempo_no_repx))
            t.sleep(1)

    def start_session(self):
        print('Start_session')
        self.motion.wakeUp()
        self.animatedSpeechProxy.say(self.dialogs.TherapyWelcomeSentence)
        t.sleep(3)

    def setData(self, data):

        self.ecg = data['ecg']
        self.emg = data['ecg']

        if self.ecg['hr'] > 160:
            self.say(self.dialogs.hrIsUpSentence)

        if ((self.emg['MuscleName'] == "RigthGluteus") and (self.emg['Contractions'] == 0)):
            print('No hay contraccion del Gluteo derecho')

        if ((self.emg['MuscleName'] == "LeftGluteus") and (self.emg['Contractions'] == 0)):
            print('No hay contraccion del Gluteo izquierdo')

    def shutdown(self):
        self.animatedSpeechProxy.say(self.dialogs.ByeSentence)
        if self.motion.robotIsWakeUp():
            self.tracker.stopTracker()
            self.motion.rest()
            self.tracker.unregisterAllTargets()

        if (self.behavior_mng_service.isBehaviorRunning('robot_intro-f8648f/behavior_1')):
            self.behavior_mng_service.stopBehavior('robot_intro-f8648f/behavior_1')

        if (self.behavior_mng_service.isBehaviorRunning('intro_yourself-883ef7/behavior_1')):
            self.behavior_mng_service.stopBehavior('intro_yourself-883ef7/behavior_1')


def Test():
    nao = RobotController()
    # nao.tracking_faces()
    nao.start_Introduction()
    nao.launch_SoundTracker()
    nao.shutdown()

# if __name__ == '__main__':
# nao = RobotController()
