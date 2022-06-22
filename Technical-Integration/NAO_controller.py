""" NAO controller script

    Created by: Mauro Tassinari """

import sys
import qi
import logging
import soundTracker as soundTracker
import time as t


class RobotController(object):

    def __init__(self):
        self.robotName = 'NAO'
        self.ip = '192.168.1.101'
        self.port = 9559
        self.useSpanish = True

        self.session = qi.Session()

        # Connect with NAO
        try:
            self.session.connect("tcp://" + self.ip + ":" + str(self.port))
            print('Connected w/ NAO')
        except RuntimeError:
            logging.debug("Can't connect to Naoqi at ip \"" + self.ip + "\" on port " + str(self.port) + ".\n"
                                                                                                         "Please check your script arguments. Run with -h option for help.")
            sys.exit(1)

        """ Updating the services of the robot """

        # Load memory services to recognize events
        self.memory = self.session.service("ALMemory")

        # Load AlTextToSpeech
        self.tts = self.session.service("ALTextToSpeech")
        self.tts.setLanguage('Spanish')

        # Load animated speech service
        self.animatedSpeechProxy = self.session.service("ALAnimatedSpeech")

        # Load motion service
        self.motion = self.session.service("ALMotion")
        self.motion.wakeUp()

        # Load posture service
        self.posture = self.session.service("ALRobotPosture")

        # Load tracker service
        self.tracker = self.session.service("ALTracker")

        # Create the sound tracker of the robot
        self.soundTracker = soundTracker.Sound_Detector()

        # Load behaviors services
        self.behavior_mng_service = self.session.service("ALBehaviorManager")

        """ Variables creation """
        self.patientName = None
        self.idSession = None
        self.first_time = None
        # Sound tracker
        self.contSound = 0
        self.sound = None
        self.flag_Sound = True  # Allows to control the activation of the sound detector

    def getInfo(self):
        self.patientName = raw_input('Name of the patient >> ')
        self.behavior_mng_service.stopAllBehaviors()
        name = self.behavior_mng_service.getRunningBehaviors()
        while True:
            try:
                self.idSession = int(input('What is the session number? (1 - First, 2 - Second, ...) >> '))
            except:
                print('Invalid answer: only integer numbers are valid. Try again... ')
                continue
            else:
                if self.idSession == 1:
                    while True:
                        try:
                            self.first_time = int(input('Is this the first time that the patient meets NAO? (1 - Yes // 0 - No) >> '))
                        except:
                            print('Invalid answer: only integer numbers are valid. Try again... ')
                            continue

                        if self.first_time == 1:
                            # NAO does the first big introduction
                            self.NAOIntroduction()
                        elif self.first_time == 0:
                            # NAO does a little introduction of the session without introducing itself
                            self.first_session_introduction()
                        break

                if self.idSession > 1:
                    print('Session introduction')
                    self.session_introduction()

                if self.idSession < 0:
                    print('Invalid answer: only positive integer numbers are valid. Try again... ')
                    continue

                break

    def NAOIntroduction(self):
        # NAO introduces itself for the first time, showing how he walks and talks. Also, asks the name of the patient
        self.motion.wakeUp()
        self.animatedSpeechProxy.say("^startTag(animations/Stand, hello) Hola, \\pau=100\\ ^waitTag(animations/Stand, hello). "
                                     "^startTag(me)  Mi nombre es Nao ^waitTag(me). \\pau=50\\Como  te llamas?")
        self.launch_SoundTracker()
        self.behavior_mng_service.runBehavior('robot_intro-313862/behavior_1')
        self.behavior_mng_service.runBehavior('firstsessionintroduction-ad74e5/behavior_1')
        self.behavior_mng_service.runBehavior('transitiontocpw-a3b364/behavior_1')
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def first_session_introduction(self):
        self.motion.wakeUp()
        self.animatedSpeechProxy.say("^startTag(animations/Stand, hello) Hola " + self.patientName + "\\pau=100\\ ^waitTag(animations/Stand, hello). "
                                                                                                     "^startTag(me)^waitTag(me). \\pau=50\\.Espero que estes muy bien!")
        self.behavior_mng_service.runBehavior('firstsessionintroduction-ad74e5/behavior_1')
        self.behavior_mng_service.runBehavior('transitiontocpw-a3b364/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def session_introduction(self):
        self.motion.wakeUp()
        self.animatedSpeechProxy.say("^startTag(animations/Stand, hello) Hola " + self.patientName + "\\pau=100\\ ^waitTag(animations/Stand, hello). "
                                                                                                     "^startTag(me)^waitTag(me). \\pau=50\\.Espero que estes muy bien!")
        self.behavior_mng_service.runBehavior('sessionintroduction-0bd48d/behavior_1')
        self.behavior_mng_service.runBehavior('transitiontocpw-a3b364/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def launch_SoundTracker(self):

        print('launching Sound tracker')
        self.soundTracker.on_Start()
        self.soundTracker.launch_thread()
        t.sleep(2)
        self.contSound = 0
        while self.flag_Sound:
            t.sleep(2)
            self.sound = self.soundTracker.got_sound
            print('Sound received? >> ' + str(self.sound))
            self.say_Hello(self.sound)

    def say_Hello(self, value):

        if value:
            print("Say Hello to the patient")
            t.sleep(2)
            s = "Hola XX, es un placer conocerte!"
            s = s.replace('XX', self.patientName)
            self.animatedSpeechProxy.say(s)
            self.soundTracker.shutdown()
            self.flag_Sound = False
            self.behavior_mng_service.stopAllBehaviors()

        elif not value:
            self.contSound = self.contSound + 1
            print(self.contSound)
            if self.contSound == 1:
                self.tts.say("No te escucho, habla un poco mas duro")
            if self.contSound == 10:
                self.contSound = 0

    def lk_first_intro(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('lk_first_intro-91039c/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def rk_first_intro(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('rk_first_intro-ee0af2/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def lh_first_intro(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('lh_first_intro-8bf24c/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def rh_first_intro(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('rh_first_intro-ae8350/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def lk_more_effort(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('leftknee_more-5775ed/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def lk_less_effort(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('leftknee_less-f85d4c/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def rk_more_effort(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('rightknee_more-fb1ec3/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def rk_less_effort(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('rightknee_less-d9f2a8/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def lh_more_effort(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('lefthip_more-1d59b2/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def lh_less_effort(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('lefthip_less-4f9642/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def lh_ext_fail(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('lh_extfail-8246e4/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def rh_more_effort(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('righthip_more-8a94fe/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def rh_less_effort(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('righthip_less-0e1c02/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def rh_ext_fail(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('rh_extfail-bc2103/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def motivate(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('motivation-caf61a/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def congratulates(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('congrats-b4542f/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()

    def goodbye(self):
        self.behavior_mng_service.runBehavior('standup-aa3c8d/behavior_1')
        self.behavior_mng_service.runBehavior('goodbye-2f191d/behavior_1')
        self.behavior_mng_service.stopAllBehaviors()
