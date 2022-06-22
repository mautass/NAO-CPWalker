# coding=utf-8
""" CPWalker data reception and interpretation for NAO BIOfeedback simulation project

Created by: Mauro Tassinari """

import socket
import itertools
import json
import numpy
import struct
import NAO_controller
import threading


def windows(window, vector, k, jump, contIndex, step):
    limit = 10  # Percentage as a function of the walking gait

    if step > 0:
        window[0].append(vector[0][-1])
        window[1].append(vector[1][-1])

    if len(window[0]) > (sum(contIndex[len(contIndex) - 2 * limit:])) and jump == 0 and step > 0 and len(window[0]) > 1:
        # jump == 0 --> Tells us when there has been a change of index
        # "len(window) > sum(contIndex[len(contIndex)-2*limit:]) + 1" --> If the size of the window array is the one required, first we add the elements
        #           on the new index and then eliminate the ones of the first index in the window array.
        # step > 0 --> To ignore the first data received before the first step done by the patient

        # We erase de data from the first index
        window[0] = list(itertools.islice(window[0], contIndex[len(contIndex) - limit * 2], None))
        window[1] = list(itertools.islice(window[1], contIndex[len(contIndex) - limit * 2], None))

    return window


class NAO_CPWalker(object):

    def __init__(self):
        self.CPWalker_IP = 'localhost'
        self.bio_IP = "localhost"
        self.bufferSize = 1024
        # Kinetics & Cinematics port
        self.kin_port = 10000
        # EMG port
        self.emg_port = 20000
        self.biofeedback_socket_port = 8000

        self.nao = NAO_controller.RobotController()

        """ Connect with SimuLink """
        self.simulinkConnect()

        """ Connect with Biofeedback Socket """
        self.biofeedback_socket_connect()
        self.start = 0
        self.end = 0

        """ Variables for data saving """
        self.time = []
        # Kinetics & Cinematics
        self.left_knee = [[], []]  # First element --> Real // Second element --> Reference
        self.right_knee = [[], []]  # First element --> Real // Second element --> Reference
        self.left_hip = [[], []]  # First element --> Real // Second element --> Reference
        self.right_hip = [[], []]  # First element --> Real // Second element --> Reference
        self.right_index = []
        self.left_index = []
        self.torque_left_knee = []
        self.torque_right_knee = []
        self.torque_left_hip = []
        self.torque_right_hip = []
        self.weight = []
        self.pistons = []
        self.traction_ref = []
        self.encoder_left_wheel = []
        self.encoder_right_wheel = []

        # EMG - First element --> Envelope // Second element --> Activation (0 no y 1 yes)
        self.left_lh = [[], []]  # Semimembranous
        self.left_mg = [[], []]  # Gastrocnemius Medialis
        self.left_rf = [[], []]  # Rectus Femoris
        self.left_ta = [[], []]  # Tibialis Anterior
        self.right_lh = [[], []]
        self.right_mg = [[], []]
        self.right_rf = [[], []]
        self.right_ta = [[], []]

        # Initialize sliding windows
        self.cont_index_left = []
        self.contl = 0
        self.cont_index_right = []
        self.contr = 0

        # º Kinematics and kinetics
        self.window_left_knee = [[], []]
        self.window_right_knee = [[], []]
        self.window_left_hip = [[], []]
        self.window_right_hip = [[], []]

        # º EMG and activation
        self.window_left_lh = [[], []]
        self.window_left_mg = [[], []]
        self.window_left_rf = [[], []]
        self.window_left_ta = [[], []]
        self.window_right_lh = [[], []]
        self.window_right_mg = [[], []]
        self.window_right_rf = [[], []]
        self.window_right_ta = [[], []]

        # Steps counter
        self.rightStep = 0
        self.leftStep = 0

        # These variables will be used to know if NAO gave a feedback to the patient in a step so it won't repeat it more than once for
        # every step. If it's value is one, NAO can give a feedback to the patient if necessary. If it's zero it means that the patient
        # didn't need a feedback
        self.act_rightKnee = 0
        self.act_rightHip = 0
        self.act_leftKnee = 0
        self.act_leftHip = 0
        self.act_leftExtHip = 0
        self.act_rightExtHip = 0

        # These variables will count how many seconds the difference between the reference and the real is
        # Needs to do more effort
        self.contLeftKnee_moreEffort = 0
        self.contLeftHip_moreEffort = 0
        self.contRightKnee_moreEffort = 0
        self.contRightHip_moreEffort = 0
        # Needs to do less effort
        self.contLeftKnee_lessEffort = 0
        self.contLeftHip_lessEffort = 0
        self.contRightKnee_lessEffort = 0
        self.contRightHip_lessEffort = 0
        # Is doing correct effort
        self.contLK_correct = 0
        self.contRK_correct = 0
        self.contLH_correct = 0
        self.contRH_correct = 0
        self.do_not_correct_LH = 0
        self.do_not_correct_RH = 0

        # These variables allows the physiotherapist to pick which limb needs feedback
        self.say_art_intro = 0
        self.biofeedbackLeftKnee = 0
        self.biofeedbackLeftHip = 0
        self.biofeedbackExt_lh = 0
        self.biofeedbackRightKnee = 0
        self.biofeedbackRightHip = 0
        self.biofeedbackExt_rh = 0

        # Variables to establish feedback intervals
        self.curr_rstep_interval = 0
        self.curr_lstep_interval = 0
        self.motivation_said = 0
        self.non_feedback_steps = 2  # This is the numbers of intervals in which NAO won't give corrective feedback to the patient

        # Variables for the EMG analysis
        self.left_lh_activated = 0
        self.left_lh_not_activated = 0
        self.left_lh_index = [0]

        self.left_mg_activated = 0
        self.left_mg_not_activated = 0
        self.left_mg_index = [0]

        self.left_rf_activated = 0
        self.left_rf_not_activated = 0
        self.left_rf_index = [0]

        self.left_ta_activated = 0
        self.left_ta_not_activated = 0
        self.left_ta_index = [0]

        self.right_lh_activated = 0
        self.right_lh_not_activated = 0
        self.right_lh_index = [0]

        self.right_mg_activated = 0
        self.right_mg_not_activated = 0
        self.right_mg_index = [0]

        self.right_rf_activated = 0
        self.right_rf_not_activated = 0
        self.right_rf_index = [0]

        self.right_ta_activated = 0
        self.right_ta_not_activated = 0
        self.right_ta_index = [0]

        # These variables allow to give the emg feedback once // 0 means NAO hasn't given feedback
        self.left_lh_done = 0
        self.left_mg_done = 0
        self.left_rf_done = 0
        self.left_ta_done = 0
        self.right_lh_done = 0
        self.right_mg_done = 0
        self.right_rf_done = 0
        self.right_ta_done = 0

        self.left_lh_act = 0
        self.left_mg_act = 0
        self.left_rf_act = 0
        self.left_ta_act = 0
        self.right_lh_act = 0
        self.right_mg_act = 0
        self.right_rf_act = 0
        self.right_ta_act = 0

        self.l_upper_cc_done = 0
        self.r_upper_cc_done = 0
        self.l_lower_cc_done = 0
        self.r_lower_cc_done = 0
        self.r_spast_done = 0
        self.l_spast_done = 0

        # These variables allow the physiotherapist to pick which muscle (EMG) needs feedback
        self.biofeedbackLeft_lh = 0
        self.biofeedbackLeft_mg = 0
        self.biofeedbackLeft_rf = 0
        self.biofeedbackLeft_ta = 0
        self.biofeedbackRight_lh = 0
        self.biofeedbackRight_mg = 0
        self.biofeedbackRight_rf = 0
        self.biofeedbackRight_ta = 0
        self.l_upper_cc = 0
        self.r_upper_cc = 0
        self.l_lower_cc = 0
        self.r_lower_cc = 0
        self.left_spasticity = 0
        self.right_spasticity = 0

        self.cont = 0
        self.bye = 0

    def update(self):
        """ DECISION OF BIOFEEDBACK TROUGH SOCKET """
        try:
            self.socket_msg = self.biofeedback_socket.recv(self.bufferSize)
            self.socket_msg = json.loads(self.socket_msg.decode())
            socket_data = self.socket_msg.get("data")
            print(socket_data)
            self.start = socket_data[0]
            self.biofeedbackLeftKnee = socket_data[1]
            self.biofeedbackRightKnee = socket_data[2]
            self.biofeedbackLeftHip = socket_data[3]
            self.biofeedbackExt_lh = socket_data[4]
            self.biofeedbackRightHip = socket_data[5]
            self.biofeedbackExt_rh = socket_data[6]

            self.l_upper_cc = socket_data[7]
            self.r_upper_cc = socket_data[8]
            self.l_lower_cc = socket_data[9]
            self.r_lower_cc = socket_data[10]
            self.left_spasticity = socket_data[11]
            self.right_spasticity = socket_data[12]

            self.biofeedbackLeft_lh = socket_data[13]
            self.biofeedbackLeft_mg = socket_data[14]
            self.biofeedbackLeft_rf = socket_data[15]
            self.biofeedbackLeft_ta = socket_data[16]
            self.biofeedbackRight_lh = socket_data[17]
            self.biofeedbackRight_mg = socket_data[18]
            self.biofeedbackRight_rf = socket_data[19]
            self.biofeedbackRight_ta = socket_data[20]

            self.end = socket_data[21]

            self.say_art_intro = 1

        except:
            end = 1

        # NAO says goodbye to the patient if the command is received from the interface
        if self.end == 1 and self.nao.behavior_mng_service.getRunningBehaviors() == []:
            print('Session concluded')
            NAO_controller.RobotController.goodbye(self.nao)
            self.bye = 1

        # The data processing starts
        if self.start == 1:
            """ DATA RECEPTION AND PROCESSING """
            self.kinDataReceptionProcessing()
            self.emgDataReceptionProcessing()

            """ NAO INTRODUCTION OF THE FOCUSING ARTICULATION """
            if self.say_art_intro == 1 and self.nao.behavior_mng_service.getRunningBehaviors() == []:
                if self.biofeedbackLeftKnee == 1:
                    threading.Thread(target=NAO_controller.RobotController.lk_first_intro, args=(self.nao,)).start()
                elif self.biofeedbackRightKnee == 1:
                    threading.Thread(target=NAO_controller.RobotController.rk_first_intro, args=(self.nao,)).start()
                elif self.biofeedbackLeftHip == 1 or self.biofeedbackExt_lh == 1:
                    threading.Thread(target=NAO_controller.RobotController.lh_first_intro, args=(self.nao,)).start()
                elif self.biofeedbackRightHip == 1 or self.biofeedbackExt_rh == 1:
                    threading.Thread(target=NAO_controller.RobotController.rh_first_intro, args=(self.nao,)).start()
                self.say_art_intro = 0
            elif self.nao.behavior_mng_service.getRunningBehaviors() != []:
                pass

            """ Variables for data analysis """
            if self.right_index[self.cont] <= 1 and self.right_index[self.cont - 1] >= 200:
                # print('Right gait cycle completed')
                self.rightStep = self.rightStep + 1
                self.act_rightKnee = 1
                self.act_rightHip = 1
                self.act_rightExtHip = 1
                self.right_lh_done = 0
                self.right_mg_done = 0
                self.r_upper_cc_done = 0
                self.r_lower_cc_done = 0
                self.r_spast_done = 0

                # I'm restarting these values, so that everytime a step is finished, the process restart itself.
                self.contRightKnee_moreEffort = 0
                self.contRightHip_moreEffort = 0
                self.contRightKnee_lessEffort = 0
                self.contRightHip_lessEffort = 0

                # Right interval update
                if self.curr_rstep_interval == self.non_feedback_steps + 1:
                    self.curr_rstep_interval = 1
                    self.motivation_said = 0
                else:
                    self.curr_rstep_interval += 1

            if self.left_index[self.cont] <= 1 and self.left_index[self.cont - 1] >= 200:
                # print('Left gait cycle completed')
                self.leftStep = self.leftStep + 1
                self.act_leftKnee = 1
                self.act_leftHip = 1
                self.act_leftExtHip = 1
                self.left_lh_done = 0
                self.left_mg_done = 0
                self.l_upper_cc_done = 0
                self.l_lower_cc_done = 0
                self.l_spast_done = 0

                # I'm restarting these values, so that everytime a step is finished, the process restart itself.
                self.contLeftKnee_moreEffort = 0
                self.contLeftHip_moreEffort = 0
                self.contLeftKnee_lessEffort = 0
                self.contLeftHip_lessEffort = 0

                # Left interval update
                if self.curr_lstep_interval == self.non_feedback_steps + 1:
                    self.curr_lstep_interval = 1
                    self.motivation_said = 0
                else:
                    self.curr_lstep_interval += 1

            """ SLIDING WINDOWS """
            self.slidingWindows()

            """" DATA ANALYSIS """
            if self.leftStep > 0:
                # Left Knee
                self.leftKneeAnalysis()
                # Left Hip
                self.leftHipAnalysis()

            if self.rightStep > 0:
                # Right Knee
                self.rightKneeAnalysis()
                # Right Hip
                self.rightHipAnalysis()

            """ EMG ANALYSIS """
            if self.leftStep > 0:
                self.emgLeft_rf()
                self.emgLeft_ta()
                self.emgLeft_mg()
                self.emgLeft_lh()
            if self.rightStep > 0:
                self.emgRight_rf()
                self.emgRight_ta()
                self.emgRight_mg()
                self.emgRight_lh()

            """ UPPER CO-CONTRACTION """
            if self.leftStep > 0 and self.left_lh_act == 1 and self.left_rf_act == 1 and self.l_upper_cc_done == 0 and self.l_upper_cc == 1:
                print('El paciente está realizando una cocontraccion superior en la pierna izquierda')
                self.l_upper_cc_done = 1
            if self.rightStep > 0 and self.right_lh_act == 1 and self.right_rf_act == 1 and self.r_upper_cc_done == 0 and self.r_upper_cc == 1:
                print('El paciente está realizando una cocontraccion superior en la pierna derecha')
                self.l_upper_cc_done = 1

            """ LOWER CO-CONTRACTION """
            if self.leftStep > 0 and self.left_ta_act == 1 and self.left_mg_act == 1 and self.l_lower_cc_done == 0 and self.l_lower_cc == 1:
                print('El paciente está realizando una cocontraccion inferior en la pierna izquierda')
                self.l_upper_cc_done = 1
            if self.rightStep > 0 and self.right_ta_act == 1 and self.right_mg_act == 1 and self.r_lower_cc_done == 0 and self.r_lower_cc == 1:
                print('El paciente está realizando una cocontraccion inferior en la pierna derecha')
                self.l_upper_cc_done = 1

            """ KNEE EXTENSION IMPAIRMENT """
            # Left leg
            if 120 < self.left_index[-1] < 160 and self.leftStep > 0 and self.left_lh_act == 1 and self.left_mg_act == 1 and self.l_spast_done == 0 and self.left_spasticity == 1:  # Between 60 and 80% human walking gait
                print('El paciente esta activando el Semimembranoso y Gemelo Medial de la pierna izquierda fuera de fase')
                self.l_spast_done = 1
            # Right leg
            if 120 < self.right_index[-1] < 160 and self.rightStep > 0 and self.right_lh_act == 1 and self.right_mg_act == 1 and self.l_spast_done == 0 and self.right_spasticity == 1:  # Between 60 and 80% human walking gait
                print('El paciente esta activando el Semimembranoso y Gemelo Medial de la pierna derecha fuera de fase')
                self.r_spast_done = 1
            self.cont = self.cont + 1

    def kinDataReceptionProcessing(self):
        data_kin = self.kin.recvfrom(1024)
        """ KINEMATIC DATA DECODING """
        # time
        self.time.append(struct.unpack(">i", bytearray(data_kin[0][0] + data_kin[0][1] + data_kin[0][2] + data_kin[0][3]))[0] / 1000.00)
        # left_knee_real
        self.left_knee[0].append(struct.unpack(">h", bytearray(data_kin[0][5] + data_kin[0][4]))[0] + (struct.unpack(">h", bytearray(data_kin[0][7] + data_kin[0][6]))[0] / 1000.00))

        # left_knee_ref
        self.left_knee[1].append(struct.unpack(">h", bytearray(data_kin[0][9] + data_kin[0][8]))[0] + (struct.unpack(">h", bytearray(data_kin[0][11] + data_kin[0][10]))[0] / 1000.00))

        # right_knee_real
        self.right_knee[0].append(struct.unpack(">h", bytearray(data_kin[0][13] + data_kin[0][12]))[0] + (struct.unpack(">h", bytearray(data_kin[0][15] + data_kin[0][14]))[0] / 1000.00))

        # right_knee_ref
        self.right_knee[1].append(struct.unpack(">h", bytearray(data_kin[0][17] + data_kin[0][16]))[0] + (struct.unpack(">h", bytearray(data_kin[0][19] + data_kin[0][18]))[0] / 1000.00))

        # left_hip_real
        if struct.unpack(">h", bytearray(data_kin[0][21] + data_kin[0][20]))[0] == 32767:
            self.left_hip[0].append((-1) * (0 + struct.unpack(">h", bytearray(data_kin[0][23] + data_kin[0][22]))[0] / 1000.00))
        else:
            self.left_hip[0].append(struct.unpack(">h", bytearray(data_kin[0][21] + data_kin[0][20]))[0] + struct.unpack(">h", bytearray(data_kin[0][23] + data_kin[0][22]))[0] / 1000.00)

        # left_hip_ref
        if struct.unpack(">h", bytearray(data_kin[0][25] + data_kin[0][24]))[0] == 32767:
            self.left_hip[1].append((-1) * (0 + struct.unpack(">h", bytearray(data_kin[0][27] + data_kin[0][26]))[0] / 1000.00))
        else:
            self.left_hip[1].append(struct.unpack(">h", bytearray(data_kin[0][25] + data_kin[0][24]))[0] + struct.unpack(">h", bytearray(data_kin[0][27] + data_kin[0][26]))[0] / 1000.00)

        # right_hip_real
        if struct.unpack(">h", bytearray(data_kin[0][29] + data_kin[0][28]))[0] == 32767:
            self.right_hip[0].append((-1) * (0 + struct.unpack(">h", bytearray(data_kin[0][31] + data_kin[0][30]))[0] / 1000.00))
        else:
            self.right_hip[0].append(struct.unpack(">h", bytearray(data_kin[0][29] + data_kin[0][28]))[0] + struct.unpack(">h", bytearray(data_kin[0][31] + data_kin[0][30]))[0] / 1000.00)

        # right_hip_ref
        if struct.unpack(">h", bytearray(data_kin[0][33] + data_kin[0][32]))[0] == 32767:
            self.right_hip[1].append((-1) * (0 + struct.unpack(">h", bytearray(data_kin[0][35] + data_kin[0][34]))[0] / 1000.00))
        else:
            self.right_hip[1].append(struct.unpack(">h", bytearray(data_kin[0][33] + data_kin[0][32]))[0] + struct.unpack(">h", bytearray(data_kin[0][35] + data_kin[0][34]))[0] / 1000.00)
        # right_leg_index
        self.right_index.append(struct.unpack(">B", bytearray(data_kin[0][36]))[0])
        # left_leg_index
        self.left_index.append(struct.unpack(">B", bytearray(data_kin[0][37]))[0])
        # torque_left_knee
        self.torque_left_knee.append(struct.unpack(">h", bytearray(data_kin[0][39] + data_kin[0][38]))[0] + struct.unpack(">h", bytearray(data_kin[0][41] + data_kin[0][40]))[0] / 1000.00)
        # torque_right_knee
        self.torque_right_knee.append(struct.unpack(">h", bytearray(data_kin[0][43] + data_kin[0][42]))[0] + struct.unpack(">h", bytearray(data_kin[0][45] + data_kin[0][44]))[0] / 1000.00)
        # torque_left_hip
        self.torque_left_hip.append(struct.unpack(">h", bytearray(data_kin[0][47] + data_kin[0][46]))[0] + struct.unpack(">h", bytearray(data_kin[0][49] + data_kin[0][48]))[0] / 1000.00)
        # torque_right_hip
        self.torque_right_hip.append(struct.unpack(">h", bytearray(data_kin[0][51] + data_kin[0][50]))[0] + struct.unpack(">h", bytearray(data_kin[0][53] + data_kin[0][52]))[0] / 1000.00)
        # weight
        self.weight.append(struct.unpack(">h", bytearray(data_kin[0][55] + data_kin[0][54]))[0] + struct.unpack(">h", bytearray(data_kin[0][57] + data_kin[0][56]))[0] / 1000.00)
        # pistons
        self.pistons.append(struct.unpack(">B", bytearray(data_kin[0][58]))[0])
        # traction_ref
        self.traction_ref.append(struct.unpack(">h", bytearray(data_kin[0][60] + data_kin[0][59]))[0] + struct.unpack(">h", bytearray(data_kin[0][62] + data_kin[0][61]))[0] / 1000.00)
        # encoder_left_wheel
        self.encoder_left_wheel.append(struct.unpack(">h", bytearray(data_kin[0][64] + data_kin[0][63]))[0] + struct.unpack(">h", bytearray(data_kin[0][66] + data_kin[0][65]))[0] / 1000.00)
        # encoder_right_wheel
        self.encoder_right_wheel.append(struct.unpack(">h", bytearray(data_kin[0][68] + data_kin[0][67]))[0] + struct.unpack(">h", bytearray(data_kin[0][70] + data_kin[0][69]))[0] / 1000.00)

    def emgDataReceptionProcessing(self):
        """ EMG DATA DECODING """
        data_emg_act = str(self.emg.recvfrom(self.bufferSize))
        data_emg_act = json.loads(data_emg_act[data_emg_act.find('{'):data_emg_act.find('}') + 1])

        # Separation of emg and activation data
        data_emg = data_emg_act["emg"]
        self.left_lh[0].append(data_emg[0])
        self.left_mg[0].append(data_emg[1])
        self.left_rf[0].append(data_emg[2])
        self.left_ta[0].append(data_emg[3])
        self.right_lh[0].append(data_emg[4])
        self.right_mg[0].append(data_emg[5])
        self.right_rf[0].append(data_emg[6])
        self.right_ta[0].append(data_emg[7])

        data_act = data_emg_act["binary_activation_values"]
        self.left_lh[1].append(data_act[0])
        self.left_mg[1].append(data_act[1])
        self.left_rf[1].append(data_act[2])
        self.left_ta[1].append(data_act[3])
        self.right_lh[1].append(data_act[4])
        self.right_mg[1].append(data_act[5])
        self.right_rf[1].append(data_act[6])
        self.right_ta[1].append(data_act[7])

    def simulinkConnect(self):
        self.kin = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.kin.bind((self.CPWalker_IP, self.kin_port))

        self.emg = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.emg.bind((self.CPWalker_IP, self.emg_port))

    def biofeedback_socket_connect(self):
        """ CONNECTION TO BIOFEEDBACK CLI SOCKET """
        self.biofeedback_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.biofeedback_socket.bind((self.CPWalker_IP, self.biofeedback_socket_port))
        self.biofeedback_socket.setblocking(0)
        print('Conectado al socket de biofeedback')

    def slidingWindows(self):
        """ Sliding windows for kinematics and kinetics.
            As we want to determine the size of the window as a function of the walking gait, we need to register how many messages has
            been received in each index """

        # This will create a vector of the size of the index where every item will represent how many messages were received in each index
        if self.left_index[-1] != self.left_index[self.cont - 1]:
            self.cont_index_left.append(self.contl)
            self.contl = 0

        if self.right_index[-1] != self.right_index[self.cont - 1]:
            self.cont_index_right.append(self.contr)
            self.contr = 0

        # Left knee
        self.window_left_knee = windows(self.window_left_knee, self.left_knee, self.cont, self.contl, self.cont_index_left, self.leftStep)

        # Right knee
        self.window_right_knee = windows(self.window_right_knee, self.right_knee, self.cont, self.contr, self.cont_index_right, self.rightStep)

        # Left hip
        self.window_left_hip = windows(self.window_left_hip, self.left_hip, self.cont, self.contl, self.cont_index_left, self.leftStep)

        # Right hip
        self.window_right_hip = windows(self.window_right_hip, self.right_hip, self.cont, self.contr, self.cont_index_right, self.rightStep)

        """ Sliding windows for EMG and activation """
        # Semimembranous
        self.window_left_lh = windows(self.window_left_lh, self.left_lh, self.cont, self.contl, self.cont_index_left, self.leftStep)
        self.window_right_lh = windows(self.window_right_lh, self.right_lh, self.cont, self.contr, self.cont_index_right, self.rightStep)

        # Gastrocnemius Medialis
        self.window_left_mg = windows(self.window_left_mg, self.left_mg, self.cont, self.contl, self.cont_index_left, self.leftStep)
        self.window_right_mg = windows(self.window_right_mg, self.right_mg, self.cont, self.contr, self.cont_index_right, self.rightStep)

        # Rectus Femoris
        self.window_left_rf = windows(self.window_left_rf, self.left_rf, self.cont, self.contl, self.cont_index_left, self.leftStep)
        self.window_right_rf = windows(self.window_right_rf, self.right_rf, self.cont, self.contr, self.cont_index_right, self.rightStep)

        # Tibialis Anterior
        self.window_left_ta = windows(self.window_left_ta, self.left_ta, self.cont, self.contl, self.cont_index_left, self.leftStep)
        self.window_right_ta = windows(self.window_right_ta, self.right_ta, self.cont, self.contr, self.cont_index_right, self.rightStep)

        if self.leftStep > 0:
            self.contl = self.contl + 1

        if self.rightStep > 0:
            self.contr = self.contr + 1

    def leftKneeAnalysis(self):
        limit_events_feedback = 50  # Each event = 10ms --> 50*10ms = 0.5s
        limit_dif_feedback = 8  # Limit for the degree difference

        """ ANALYSIS WITH DEGREE DIFFERENCES """
        if 158 > self.left_index[self.cont] > 102:
            diff = numpy.subtract(self.window_left_knee[1], self.window_left_knee[0])
            mean = numpy.mean(diff)

            if mean > limit_dif_feedback:
                self.contLeftKnee_lessEffort = 0
                self.contLK_correct = 0
                self.contLeftKnee_moreEffort = self.contLeftKnee_moreEffort + 1

            if mean < (-1) * limit_dif_feedback:
                self.contLeftKnee_moreEffort = 0
                self.contLK_correct = 0
                self.contLeftKnee_lessEffort = self.contLeftKnee_lessEffort + 1

            if limit_dif_feedback > mean > (-1) * limit_dif_feedback:
                self.contLK_correct += 1
                self.contLeftKnee_lessEffort = 0
                self.contLeftKnee_moreEffort = 0
        else:
            mean = 0
            self.contLK_correct = 0
            self.contLeftKnee_lessEffort = 0
            self.contLeftKnee_moreEffort = 0

        if 158 > self.left_index[self.cont] > 102 and self.act_leftKnee == 1 and self.biofeedbackLeftKnee == 1:
            # The patient does correctly the knee flexion
            if self.contLK_correct >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.left_index[self.cont] > 130:
                print('Nao felicita al paciente por mover bien la rodilla izquierda: ' + str(self.leftStep) + ' en el index: ' + str(self.left_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.congratulates, args=(self.nao,)).start()
                self.act_leftKnee = 0

            # The patient is flexing too much the knee
            if self.contLeftKnee_lessEffort >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.curr_lstep_interval == 1:
                print('Nao dice flexiona menos la rodilla izquierda en el paso: ' + str(self.leftStep) + ' en el index: ' + str(self.left_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.lk_less_effort, args=(self.nao,)).start()
                self.act_leftKnee = 0

            # The patient is not flexing enough the knee
            if self.contLeftKnee_moreEffort >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.curr_lstep_interval == 1:
                print('Nao dice flexiona mas la rodilla izquierda en el paso: ' + str(self.leftStep) + ' en el index: ' + str(self.left_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.lk_more_effort, args=(self.nao,)).start()
                self.act_leftKnee = 0

        # NAO motivates the patient
        if self.curr_lstep_interval == (self.non_feedback_steps / 2.0) + 1 and self.biofeedbackLeftKnee == 1 and self.motivation_said == 0 and self.left_index[self.cont] > 80:
            print('Nao motiva al paciente')
            threading.Thread(target=NAO_controller.RobotController.motivate, args=(self.nao,)).start()
            self.motivation_said = 1

    def leftHipAnalysis(self):
        limit_events_feedback = 80  # Each event = 10ms --> 80*10ms = 0.8s
        limit_dif_feedback = 3  # Limit for the degree difference
        if self.biofeedbackExt_lh == 1:
            limit_dif_feedback = 2  # The extension fail of the hip needs a more restrictive condition

        """ ANALYSIS WITH DEGREE DIFFERENCES """
        diff = numpy.subtract(self.window_left_hip[1], self.window_left_hip[0])
        mean = numpy.mean(diff)

        if self.left_index[-1] == 85 or self.left_index[-1] == 140:
            self.leftHipDiff = []
            mean = 0
            self.contLeftHip_lessEffort = 0
            self.contLH_correct = 0
            self.contLeftHip_moreEffort = 0

        if mean > limit_dif_feedback:
            self.contLeftHip_lessEffort = 0
            self.contLH_correct = 0
            self.contLeftHip_moreEffort = self.contLeftHip_moreEffort + 1

        if mean < (-1) * limit_dif_feedback:
            self.contLeftHip_moreEffort = 0
            self.contLH_correct = 0
            self.contLeftHip_lessEffort = self.contLeftHip_lessEffort + 1

        if limit_dif_feedback > mean > (-1) * limit_dif_feedback:
            self.contLeftHip_lessEffort = 0
            self.contLeftHip_moreEffort = 0
            self.contLH_correct += 1

        """ HIP FLEXION FEEDBACK """
        if self.biofeedbackLeftHip == 1 and 30 >= self.left_index[self.cont] >= 15 and self.act_leftHip == 1 and self.leftStep > 1 and self.do_not_correct_LH == 0:
            if self.contLH_correct >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == []:
                print('Nao felicita al paciente por flexionar bien la cadera izquierda: ' + str(self.leftStep) + ' en el index: ' + str(self.left_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.congratulates, args=(self.nao,)).start()
                self.act_leftHip = 0

        if self.biofeedbackLeftHip == 1 and 200 >= self.left_index[self.cont] >= 140 and self.act_leftHip == 1:
            if self.contLeftHip_lessEffort >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.curr_lstep_interval == 1:
                print('NAO dice flexiona menos la cadera izquierda en el paso: ' + str(self.leftStep) + ' en el index: ' + str(self.left_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.lh_less_effort, args=(self.nao,)).start()
                self.act_leftHip = 0
                self.do_not_correct_LH = 1

            if self.contLeftHip_moreEffort >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.curr_lstep_interval == 1:
                print('Nao dice flexiona más la cadera izquierda en el paso: ' + str(self.leftStep) + ' en el index: ' + str(self.left_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.lh_more_effort, args=(self.nao,)).start()
                self.act_leftHip = 0
                self.do_not_correct_LH = 1

        """ HIP EXTENSION FEEDBACK """
        if 120 > self.left_index[self.cont] > 85 and self.act_leftExtHip == 1 and self.biofeedbackExt_lh == 1 and self.nao.behavior_mng_service.getRunningBehaviors() == []:
            if self.contLeftHip_lessEffort >= limit_events_feedback - 70 and self.curr_lstep_interval == 1:
                # The patient is having a deficiency of effort in the hip extension
                print('NAO dice EMPUJA MÁS HACIA ATRÁS la pierna izquierda en el paso: ' + str(self.leftStep) + ' en el index: ' + str(self.left_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.lh_ext_fail, args=(self.nao,)).start()
                self.act_leftExtHip = 0

            if self.contLH_correct >= limit_events_feedback - 70 and self.left_index[-1] > 115:
                # The patient is doing correctly the hip extension
                print('Nao felicita al paciente por extender bien la cadera izquierda: ' + str(self.leftStep) + ' en el index: ' + str(self.left_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.congratulates, args=(self.nao,)).start()
                self.act_leftExtHip = 0

        if self.curr_lstep_interval == self.non_feedback_steps / 2.0 + 1 and (self.biofeedbackLeftHip == 1 or self.biofeedbackExt_lh == 1) and self.motivation_said == 0 and self.left_index[-1] > 60:
            if self.nao.behavior_mng_service.getRunningBehaviors() == []:
                print('Nao motiva al paciente')
                threading.Thread(target=NAO_controller.RobotController.motivate, args=(self.nao,)).start()
                self.motivation_said = 1

        if self.left_index[-1] > 85:
            self.do_not_correct_LH = 0

    def rightKneeAnalysis(self):
        limit_events_feedback = 50  # Each event = 10ms --> 50*10ms = 0.5s
        limit_dif_feedback = 8  # Limit for the degree difference

        """ ANALYSIS WITH DEGREE DIFFERENCES """
        if 158 > self.right_index[self.cont] > 102:
            diff = numpy.subtract(self.window_right_knee[1], self.window_right_knee[0])
            mean = numpy.mean(diff)

            if mean > limit_dif_feedback:
                self.contRightKnee_lessEffort = 0
                self.contRK_correct = 0
                self.contRightKnee_moreEffort = self.contRightKnee_moreEffort + 1

            if mean < (-1) * limit_dif_feedback:
                self.contRightKnee_moreEffort = 0
                self.contRK_correct = 0
                self.contRightKnee_lessEffort = self.contRightKnee_lessEffort + 1

            if limit_dif_feedback > mean > (-1) * limit_dif_feedback:
                self.contRK_correct += 1
                self.contRightKnee_lessEffort = 0
                self.contRightKnee_moreEffort = 0
        else:
            mean = 0
            self.contRK_correct = 0
            self.contRightKnee_lessEffort = 0
            self.contRightKnee_moreEffort = 0

        if 158 > self.right_index[self.cont] > 102 and self.act_rightKnee == 1 and self.biofeedbackRightKnee == 1:
            # The patient does correctly the knee flexion
            if self.contRK_correct >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.right_index[self.cont] > 130:
                print('Nao felicita al paciente por mover bien la rodilla izquierda: ' + str(self.rightStep) + ' en el index: ' + str(self.right_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.congratulates, args=(self.nao,)).start()
                self.act_rightKnee = 0

            # The patient is flexing too much the knee
            if self.contRightKnee_lessEffort >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.curr_rstep_interval == 1:
                print('Nao dice flexiona menos la rodilla izquierda en el paso: ' + str(self.rightStep) + ' en el index: ' + str(self.right_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.rk_less_effort, args=(self.nao,)).start()
                self.act_rightKnee = 0

            # The patient is not flexing enough the knee
            if self.contRightKnee_moreEffort >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.curr_rstep_interval == 1:
                print('Nao dice flexiona mas la rodilla izquierda en el paso: ' + str(self.rightStep) + ' en el index: ' + str(self.right_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.rk_more_effort, args=(self.nao,)).start()
                self.act_rightKnee = 0

        # NAO motivates the patient
        if self.curr_rstep_interval == (self.non_feedback_steps / 2.0) + 1 and self.biofeedbackRightKnee == 1 and self.motivation_said == 0 and self.right_index[self.cont] > 80:
            print('Nao motiva al paciente')
            threading.Thread(target=NAO_controller.RobotController.motivate, args=(self.nao,)).start()
            self.motivation_said = 1

    def rightHipAnalysis(self):
        limit_events_feedback = 80  # Each event = 10ms --> 80*10ms = 0.8s
        limit_dif_feedback = 3  # Limit for the degree difference
        if self.biofeedbackExt_rh == 1:
            limit_dif_feedback = 2  # The extension fail of the hip needs a more restrictive condition

        """ ANALYSIS WITH DEGREE DIFFERENCES """
        diff = numpy.subtract(self.window_right_hip[1], self.window_right_hip[0])
        mean = numpy.mean(diff)

        if self.right_index[-1] == 85 or self.right_index[-1] == 140:
            self.rightHipDiff = []
            mean = 0
            self.contRightHip_lessEffort = 0
            self.contRH_correct = 0
            self.contRightHip_moreEffort = 0

        if mean > limit_dif_feedback:
            self.contRightHip_lessEffort = 0
            self.contRH_correct = 0
            self.contRightHip_moreEffort = self.contRightHip_moreEffort + 1

        if mean < (-1) * limit_dif_feedback:
            self.contRightHip_moreEffort = 0
            self.contRH_correct = 0
            self.contRightHip_lessEffort = self.contRightHip_lessEffort + 1

        if limit_dif_feedback > mean > (-1) * limit_dif_feedback:
            self.contRightHip_lessEffort = 0
            self.contRightHip_moreEffort = 0
            self.contRH_correct += 1

        """ HIP FLEXION FEEDBACK """
        if self.biofeedbackRightHip == 1 and 30 >= self.right_index[self.cont] >= 15 and self.act_rightHip == 1 and self.rightStep > 1 and self.do_not_correct_RH == 0:
            if self.contRH_correct >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == []:
                print('Nao felicita al paciente por flexionar bien la cadera derecha: ' + str(self.rightStep) + ' en el index: ' + str(self.right_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.congratulates, args=(self.nao,)).start()
                self.act_rightHip = 0

        if self.biofeedbackRightHip == 1 and 200 >= self.right_index[self.cont] >= 140 and self.act_rightHip == 1:
            if self.contRightHip_lessEffort >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.curr_rstep_interval == 1:
                print('NAO dice flexiona menos la cadera derecha en el paso: ' + str(self.rightStep) + ' en el index: ' + str(self.right_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.rh_less_effort, args=(self.nao,)).start()
                self.act_rightHip = 0
                self.do_not_correct_RH = 1

            if self.contRightHip_moreEffort >= limit_events_feedback and self.nao.behavior_mng_service.getRunningBehaviors() == [] and self.curr_rstep_interval == 1:
                print('Nao dice flexiona más la cadera derecha en el paso: ' + str(self.rightStep) + ' en el index: ' + str(self.right_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.rh_more_effort, args=(self.nao,)).start()
                self.act_rightHip = 0
                self.do_not_correct_RH = 1

        """ HIP EXTENSION FEEDBACK """
        if 120 > self.right_index[self.cont] > 85 and self.act_rightExtHip == 1 and self.biofeedbackExt_rh == 1 and self.nao.behavior_mng_service.getRunningBehaviors() == []:
            # print(str(self.contRightHip_lessEffort) + '\t' + str(self.contRightHip_moreEffort) + '\t' + str(self.contRH_correct) + '\t' + str(mean) + '\t\t' + str(self.right_index[-1]))
            if self.contRightHip_lessEffort >= limit_events_feedback - 70 and self.curr_rstep_interval == 1:
                # The patient is having a deficiency of effort in the hip extension
                print('NAO dice EMPUJA MÁS HACIA ATRÁS la pierna derecha en el paso: ' + str(self.rightStep) + ' en el index: ' + str(self.right_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.rh_ext_fail, args=(self.nao,)).start()
                self.act_rightExtHip = 0

            if self.contRH_correct >= limit_events_feedback - 70 and self.right_index[-1] > 115:
                # The patient is doing correctly the hip extension
                print('Nao felicita al paciente por extender bien la cadera derecha: ' + str(self.rightStep) + ' en el index: ' + str(self.right_index[self.cont]) +
                      ' después de ' + str(limit_events_feedback * 0.01) + ' s')
                threading.Thread(target=NAO_controller.RobotController.congratulates, args=(self.nao,)).start()
                self.act_rightExtHip = 0

        if self.curr_rstep_interval == self.non_feedback_steps / 2.0 + 1 and (self.biofeedbackRightHip == 1 or self.biofeedbackExt_rh == 1) and self.motivation_said == 0 and self.right_index[-1] > 60:
            if self.nao.behavior_mng_service.getRunningBehaviors() == []:
                print('Nao motiva al paciente')
                threading.Thread(target=NAO_controller.RobotController.motivate, args=(self.nao,)).start()
                self.motivation_said = 1

        if self.right_index[-1] > 85:
            self.do_not_correct_RH = 0

    def emgLeft_lh(self):
        limit_emg = 3  # %of human walking gait
        if self.window_left_lh[1][-1] == 1:
            self.left_lh_activated = self.left_lh_activated + 1
            self.left_lh_not_activated = 0
            if self.left_lh_index[-1] != self.left_index[-1]:
                self.left_lh_index.append(self.left_index[-1])

        if self.window_left_lh[1][-1] == 0:
            self.left_lh_not_activated = self.left_lh_not_activated + 1

        if self.left_lh_not_activated > self.left_lh_activated:
            self.left_lh_activated = 0
            self.left_lh_index = [0]
            self.left_lh_act = 0

        if len(self.left_lh_index) > 2 * limit_emg:
            self.left_lh_act = 1
            if self.biofeedbackLeft_lh == 1 and self.left_lh_done == 0:
                print('Activacion prolongada del Semimebranoso izquierdo en el ' + str(self.left_index[-1]/2.0) + '% de la fase de marcha')
                self.left_lh_done = 1
                self.left_lh_index = [0]

    def emgLeft_mg(self):
        limit_emg = 3  # %of human walking gait
        if self.window_left_mg[1][-1] == 1:
            self.left_mg_activated = self.left_mg_activated + 1
            self.left_mg_not_activated = 0
            if self.left_mg_index[-1] != self.left_index[-1]:
                self.left_mg_index.append(self.left_index[-1])

        if self.window_left_mg[1][-1] == 0:
            self.left_mg_not_activated = self.left_mg_not_activated + 1

        if self.left_mg_not_activated > self.left_mg_activated:
            self.left_mg_activated = 0
            self.left_mg_index = [0]
            self.left_mg_act = 0

        if len(self.left_mg_index) > 2 * limit_emg:
            self.left_mg_act = 1
            if self.biofeedbackLeft_mg == 1 and self.left_mg_done == 0:
                print('Activacion prolongada del Gemelo Medial izquierdo en el ' + str(self.left_index[-1] / 2.0) + '% de la fase de marcha')
                self.left_mg_done = 1
                self.left_mg_index = [0]

    def emgLeft_rf(self):
        limit_emg = 3  # %of human walking gait
        if self.window_left_rf[1][-1] == 1:
            self.left_rf_activated = self.left_rf_activated + 1
            self.left_rf_not_activated = 0
            if self.left_rf_index[-1] != self.left_index[-1]:
                self.left_rf_index.append(self.left_index[-1])

        if self.window_left_rf[1][-1] == 0:
            self.left_rf_not_activated = self.left_rf_not_activated + 1

        if self.left_rf_not_activated > self.left_rf_activated:
            self.left_rf_activated = 0
            self.left_rf_index = [0]
            self.left_rf_act = 0

        if len(self.left_rf_index) > 2 * limit_emg:
            self.left_rf_act = 1
            if self.biofeedbackLeft_rf == 1 and self.left_rf_done == 0:
                print('Activacion prolongada del Recto Femoral izquierdo en el ' + str(self.left_index[-1] / 2.0) + '% de la fase de marcha')
                self.left_rf_done = 1
                self.left_rf_index = [0]

    def emgLeft_ta(self):
        limit_emg = 3  # %of human walking gait
        if self.window_left_ta[1][-1] == 1:
            self.left_ta_activated = self.left_ta_activated + 1
            self.left_ta_not_activated = 0
            if self.left_ta_index[-1] != self.left_index[-1]:
                self.left_ta_index.append(self.left_index[-1])

        if self.window_left_ta[1][-1] == 0:
            self.left_ta_not_activated = self.left_ta_not_activated + 1

        if self.left_ta_not_activated > self.left_ta_activated:
            self.left_ta_activated = 0
            self.left_ta_index = [0]
            self.left_ta_act = 0

        if len(self.left_ta_index) > 2 * limit_emg:
            self.left_ta_act = 1
            if self.biofeedbackLeft_ta == 1 and self.left_ta_done == 0:
                print('Activacion prolongada del Tibial Anterior izquierdo en el ' + str(self.left_index[-1] / 2.0) + '% de la fase de marcha')
                self.left_ta_done = 1
                self.left_ta_index = [0]

    def emgRight_lh(self):
        limit_emg = 3  # %of human walking gait
        if self.window_right_lh[1][-1] == 1:
            self.right_lh_activated = self.right_lh_activated + 1
            self.right_lh_not_activated = 0
            if self.right_lh_index[-1] != self.right_index[-1]:
                self.right_lh_index.append(self.right_index[-1])

        if self.window_right_lh[1][-1] == 0:
            self.right_lh_not_activated = self.right_lh_not_activated + 1

        if self.right_lh_not_activated > self.right_lh_activated:
            self.right_lh_activated = 0
            self.right_lh_index = [0]
            self.right_lh_act = 0

        if len(self.right_lh_index) > 2 * limit_emg:
            self.right_lh_act = 1
            if self.biofeedbackRight_lh == 1 and self.right_lh_done == 0:
                print('Activacion prolongada del Semimebranoso derecho en el ' + str(self.right_index[-1]/2.0) + '% de la fase de marcha')
                self.right_lh_done = 1
                self.right_lh_index = [0]

    def emgRight_mg(self):
        limit_emg = 3  # %of human walking gait
        if self.window_right_mg[1][-1] == 1:
            self.right_mg_activated = self.right_mg_activated + 1
            self.right_mg_not_activated = 0
            if self.right_mg_index[-1] != self.right_index[-1]:
                self.right_mg_index.append(self.right_index[-1])

        if self.window_right_mg[1][-1] == 0:
            self.right_mg_not_activated = self.right_mg_not_activated + 1

        if self.right_mg_not_activated > self.right_mg_activated:
            self.right_mg_activated = 0
            self.right_mg_index = [0]
            self.right_mg_act = 0

        if len(self.right_mg_index) > 2 * limit_emg:
            self.right_mg_act = 1
            if self.biofeedbackRight_mg == 1 and self.right_mg_done == 0:
                print('Activacion prolongada del Gemelo Medial derecho en el ' + str(self.right_index[-1] / 2.0) + '% de la fase de marcha')
                self.right_mg_done = 1
                self.right_mg_index = [0]

    def emgRight_rf(self):
        limit_emg = 3  # %of human walking gait
        if self.window_right_rf[1][-1] == 1:
            self.right_rf_activated = self.right_rf_activated + 1
            self.right_rf_not_activated = 0
            if self.right_rf_index[-1] != self.right_index[-1]:
                self.right_rf_index.append(self.right_index[-1])

        if self.window_right_rf[1][-1] == 0:
            self.right_rf_not_activated = self.right_rf_not_activated + 1

        if self.right_rf_not_activated > self.right_rf_activated:
            self.right_rf_activated = 0
            self.right_rf_index = [0]
            self.right_rf_act = 0

        if len(self.right_rf_index) > 2 * limit_emg:
            self.right_rf_act = 1
            if self.biofeedbackRight_rf == 1 and self.right_rf_done == 0:
                print('Activacion prolongada del Recto Femoral derecho en el ' + str(self.right_index[-1] / 2.0) + '% de la fase de marcha')
                self.right_rf_done = 1
                self.right_rf_index = [0]

    def emgRight_ta(self):
        limit_emg = 3  # %of human walking gait
        if self.window_right_ta[1][-1] == 1:
            self.right_ta_activated = self.right_ta_activated + 1
            self.right_ta_not_activated = 0
            if self.right_ta_index[-1] != self.right_index[-1]:
                self.right_ta_index.append(self.right_index[-1])

        if self.window_right_ta[1][-1] == 0:
            self.right_ta_not_activated = self.right_ta_not_activated + 1

        if self.right_ta_not_activated > self.right_ta_activated:
            self.right_ta_activated = 0
            self.right_ta_index = [0]
            self.right_ta_act = 0

        if len(self.right_ta_index) > 2 * limit_emg:
            self.right_ta_act = 1
            if self.biofeedbackRight_ta == 1 and self.right_ta_done == 0:
                print('Activacion prolongada del Tibial Anterior derecho en el ' + str(self.right_index[-1] / 2.0) + '% de la fase de marcha')
                self.right_ta_done = 1
                self.right_ta_index = [0]