""" Main script

Created by: Mauro Tassinari """

from NAO_CPWalker import NAO_CPWalker
from NAO_controller import RobotController

NAO = RobotController()
NAO.getInfo()

""" The session with NAO and CPWalker can start """
print('The session with NAO and CPWalker can start')
NAO_CPWalker_feedback = NAO_CPWalker()

while True:
    NAO_CPWalker.update(NAO_CPWalker_feedback)
    if NAO_CPWalker_feedback.bye == 1:
        break
