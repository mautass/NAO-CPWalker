""" Biofeedback choosing CLI

Created by: Mauro Tassinari """

import socket
import json

host = 'localhost'
port = 8000
biofeedback_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
biofeedback_socket.connect((host, port))
print('Conectado al servidor')

""" Message sent: [start, left_knee, right_knee, left_hip, right_hip, l_upper_cc, r_upper_cc, l_lower_cc, r_lower_cc, left_spasticity, right_spasticity, l_lh, l_mg, l_rf, l_ta, r_lh, r_mg, r_rf, r_ta] 
        --> 'Start' can be 1 or 0, where 1 means the process has to initiate, and 0 that the process hasn't started
        --> 'left_knee', 'right_knee', 'left_hip' and 'right_hip' can be declared as 1 if the physiotherapist wants to receive feedback from that joint
        --> 'l_upper_cc' and 'r_upper_cc' must be set to 1 if the physiotherapist wants to know if its occurring co-contraction between Rectus Femoris and Semimembranosus
        --> 'l_lower_cc' and 'r_lower_cc' must be set to 1 if the physiotherapist wants to know if its occurring co-contraction between Gastrocnemius Medialis and TIbialis Anterior
        --> 'left_spasticity' and 'right_spasticity' must be set to 1 if the physiotherapist wants to know if its occurring a simultaneous activation of the Semimembranous and Gastrocnemius Medialis between the 60 and 80% of walking gait
        --> 'l_lh, l_mg, l_rf, l_ta, r_lh, r_mg, r_rf, r_ta' can be declared as 1 if the physiotherapist wants to receive feedback from that muscle """

start = 0
end = 0
left_knee = 0
right_knee = 0
left_hip = 0
ext_lh = 0
right_hip = 0
ext_rh = 0
l_upper_cc, r_upper_cc, l_lower_cc, r_lower_cc, left_spasticity, right_spasticity = 0, 0, 0, 0, 0, 0
l_lh = 0
l_mg = 0
l_rf = 0
l_ta = 0
r_lh = 0
r_mg = 0
r_rf = 0
r_ta = 0

while True:
    print('Current values: ')
    print('    Start = ' + str(start) + ' / End = ' + str(end))
    print('    Joint feedback: Left knee flexion = ' + str(left_knee) + ' / Right knee flexion = ' + str(right_knee) + ' / Left hip flexion = ' + str(left_hip) + ' / Left hip extension = ' + str(ext_lh) +
          ' / Right hip flexion = ' + str(right_hip) + ' / Right hip extension = ' + str(ext_rh))
    print('    EMG feeedback: Left Upper Co-contraction = ' + str(l_upper_cc) + ' / Left Lower Co-contraction = ' + str(l_lower_cc) + ' / Left Spasticity (S+GM) = ' + str(left_spasticity))
    print('                   Right Upper Co-contraction = ' + str(r_upper_cc) + ' / Right Lower Co-contraction = ' + str(r_lower_cc) + ' / Right Spasticity (S+GM) = ' + str(right_spasticity))
    print('                   Left Semimembranosus = ' + str(l_lh) + ' / Left Gastrocnemius Medialis = ' + str(l_mg) + ' / Left Rectus Femoris = ' + str(l_rf) + ' / Left Tibialis Anterior = ' + str(l_ta))
    print('                   Right Semimembranosus = ' + str(r_lh) + ' / Right Gastrocnemius Medialis = ' + str(r_mg) + ' / Right Rectus Femoris = ' + str(r_rf) + ' / Right Tibialis Anterior = ' + str(r_ta))
    print('-----------------------------------------------------------------------------------------------------------------------------------------------------------------------')

    print('Please select what do you want to modify ')
    first_selection = input('1 -> Start / 2 -> Joint feedback / 3 -> EMG feedback / 4 -> End >> ')
    print('\n')
    if first_selection == 1:
        start = input('Select the value of Start >> ')
        if start == 1:
            end = 0
    if first_selection == 2:
        print('Select the the joint which feedback value would you change ')
        joint_selection = input('1 -> Left knee flexion / 2 -> Right knee flexion / 3 -> Left hip flexion / 4 -> Left hip extension / 5 -> Right hip flexion / 6 -> Right hip extension >> ')
        if joint_selection == 1:
            left_knee = input('Receive feedback for left knee flexion? (1 -> yes / 0 -> no) >> ')
            if left_knee == 1:
                right_knee = 0
                left_hip = 0
                ext_lh = 0
                right_hip = 0
                ext_rh = 0
        if joint_selection == 2:
            right_knee = input('Receive feedback for right knee flexion? (1 -> yes / 0 -> no) >> ')
            if right_knee == 1:
                left_knee = 0
                left_hip = 0
                ext_lh = 0
                right_hip = 0
                ext_rh = 0
        if joint_selection == 3:
            left_hip = input('Receive feedback for left hip flexion? (1 -> yes / 0 -> no) >> ')
            if left_hip == 1:
                left_knee = 0
                right_knee = 0
                ext_lh = 0
                right_hip = 0
                ext_rh = 0
        if joint_selection == 4:
            ext_lh = input('Receive feedback for left hip extension? (1 -> yes / 0 -> no) >> ')
            if ext_lh == 1:
                left_knee = 0
                right_knee = 0
                left_hip = 0
                right_hip = 0
                ext_rh = 0
        if joint_selection == 5:
            right_hip = input('Receive feedback for right hip flexion? (1 -> yes / 0 -> no) >> ')
            if right_hip == 1:
                left_knee = 0
                right_knee = 0
                left_hip = 0
                ext_lh = 0
                ext_rh = 0
        if joint_selection == 6:
            ext_rh = input('Receive feedback for right hip extension? (1 -> yes / 0 -> no) >> ')
            if ext_rh == 1:
                left_knee = 0
                right_knee = 0
                left_hip = 0
                ext_lh = 0
                right_hip = 0

    if first_selection == 3:
        leg = input('Left (0) or right (1) leg? >> ')
        print('\n')
        if leg == 0:
            feedback_emg = input('1 -> Upper co-contraction / 2 -> Lower co-contraction / 3 -> Spasticity / 4 -> Individual muscle >> ')
            print('\n')
            if feedback_emg == 1:
                l_upper_cc = input('Receive feedback for the Upper Co-contraction? (1 -> yes / 0 -> no) >> ')
            if feedback_emg == 2:
                l_lower_cc = input('Receive feedback for the Lower Co-contraction? (1 -> yes / 0 -> no) >> ')
            if feedback_emg == 3:
                left_spasticity = input('Receive feedback for the simultaneous activation of the Semimembranous and Gastrocnemius Medialis in the swing phase? (1 -> yes / 0 -> no) >> ')
            if feedback_emg == 4:
                print('Select the LEFT leg muscle which feedback value would you change ')
                emg_selection = input('1 -> Semimembranosus / 2 -> Gastrocnemius Medialis / 3 -> Rectus Femoris / 4 -> Tibialis Anterior >> ')
                print('\n')
                if emg_selection == 1:
                    l_lh = input('Receive feedback for Left Semimembranosus? (1 -> yes / 0 -> no) >> ')
                if emg_selection == 2:
                    l_mg = input('Receive feedback for Left Gastrocnemius Medialis? (1 -> yes / 0 -> no) >> ')
                if emg_selection == 3:
                    l_rf = input('Receive feedback for Left Rectus Femoris? (1 -> yes / 0 -> no) >> ')
                if emg_selection == 4:
                    l_ta = input('Receive feedback for Left Tibialis Anterior? (1 -> yes / 0 -> no) >> ')
        if leg == 1:
            feedback_emg = input('1 -> Upper co-contraction / 2 -> Lower co-contraction / 3 -> Spasticity / 4 -> Individual muscle >> ')
            print('\n')
            if feedback_emg == 1:
                r_upper_cc = input('Receive feedback for the Upper Co-contraction? (1 -> yes / 0 -> no) >> ')
            if feedback_emg == 2:
                r_lower_cc = input('Receive feedback for the Lower Co-contraction? (1 -> yes / 0 -> no) >> ')
            if feedback_emg == 3:
                right_spasticity = input('Receive feedback for the simultaneous activation of the Semimembranous and Gastrocnemius Medialis in the swing phase? (1 -> yes / 0 -> no) >> ')
            if feedback_emg == 4:
                print('Select the RIGHT leg muscle which feedback value would you change ')
                emg_selection = input('1 -> Semimembranosus / 2 -> Gastrocnemius Medialis / 3 -> Rectus Femoris / 4 -> Tibialis Anterior >> ')
                print('\n')
                if emg_selection == 1:
                    l_lh = input('Receive feedback for Right Semimembranosus? (1 -> yes / 0 -> no) >> ')
                if emg_selection == 2:
                    l_mg = input('Receive feedback for Right Gastrocnemius Medialis? (1 -> yes / 0 -> no) >> ')
                if emg_selection == 3:
                    l_rf = input('Receive feedback for Right Rectus Femoris? (1 -> yes / 0 -> no) >> ')
                if emg_selection == 4:
                    l_ta = input('Receive feedback for Right Tibialis Anterior? (1 -> yes / 0 -> no) >> ')

    if first_selection == 4:
        end = input('Select the value of End >> ')
        if end == 1:
            start = 0

    msg = [start, left_knee, right_knee, left_hip, ext_lh, right_hip, ext_rh, l_upper_cc, r_upper_cc, l_lower_cc, r_lower_cc, left_spasticity, right_spasticity, l_lh, l_mg, l_rf, l_ta, r_lh, r_mg, r_rf, r_ta, end]
    msg = {"data": msg}
    msg_json = json.dumps(msg)
    biofeedback_socket.send(msg_json.encode())

    if end == 1 and start == 0:
        biofeedback_socket.close()
        print('Closed')
        break
