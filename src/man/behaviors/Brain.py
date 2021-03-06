import time
import sys

# Redirect standard error to standard out
_stderr = sys.stderr
sys.stderr = sys.stdout
## import cProfile
## import pstats

# Packages and modules from super-directories
import noggin_constants as Constants
from objects import RobotLocation

# Modules from this directory
from . import Leds
from . import robots
from . import GameController

# Packages and modules from sub-directories
from . import FallController
from .headTracker import HeadTracker
from .typeDefs import (Play, TeamMember)
from .navigator import Navigator
from .playbook import PBInterface
from .players import Switch
from .kickDecider import KickDecider

# Import message protocol buffers and interface
import interface
import LedCommand_proto
import GameState_proto
import WorldModel_proto
import RobotLocation_proto
import BallModel_proto
import PMotion_proto
import MotionStatus_proto
import SonarState_proto
import VisionRobot_proto
import VisionField_proto
import ButtonState_proto
import FallStatus_proto

class Brain(object):
    """
    Class brings all of our components together and runs the behaviors
    """

    def __init__(self, teamNum, playerNum):
        """
        Class constructor
        """

        # Parse arguments
        self.playerNumber = playerNum
        self.teamNumber = teamNum

        self.counter = 0
        self.time = time.time()

        # Initalize the leds and game controller
        self.leds = Leds.Leds(self)
        self.gameController = GameController.GameController(self)

        # Initialize fallController
        self.fallController = FallController.FallController(self)

        # Retrieve our robot identification and set per-robot parameters
        self.CoA = robots.get_certificate()

        # coa is Certificate of Authenticity (to keep things short)
        print '\033[32m'+str(self.CoA)                              +'\033[0m'
        print '\033[32m'+"GC:  I am on team "+str(self.teamNumber)  +'\033[0m'
        print '\033[32m'+"GC:  I am player  "+str(self.playerNumber)+'\033[0m'

        # Information about the environment
        self.ball = None
        self.initTeamMembers()
        self.motion = None
        self.game = None

        self.play = Play.Play()

        # FSAs
        self.player = Switch.selectedPlayer.SoccerPlayer(self)
        self.tracker = HeadTracker.HeadTracker(self)
        self.nav = Navigator.Navigator(self)
        self.playbook = PBInterface.PBInterface(self)
        self.kickDecider = KickDecider.KickDecider(self)

        # Message interface
        self.interface = interface.interface

    def initTeamMembers(self):
        self.teamMembers = []
        for i in xrange(Constants.NUM_PLAYERS_PER_TEAM):
            mate = TeamMember.TeamMember(self)
            mate.playerNumber = i + 1
            self.teamMembers.append(mate)

##
##--------------CONTROL METHODS---------------##
##
    def profile(self):
        if self.counter == 0:
            cProfile.runctx('self.run()',  self.__dict__, locals(),
                            'pythonStats')
            self.p = pstats.Stats('pythonStats')

        elif self.counter < 3000:
            self.p.add('pythonStats')
            cProfile.runctx('self.run()',  self.__dict__, locals(),
                            'pythonStats')

        elif self.counter == 3000:
            self.p.strip_dirs()
            self.p.sort_stats('cumulative')
            ## print 'PYTHON STATS:'
            ## self.p.print_stats()
            ## print 'OUTGOING CALLEES:'
            ## self.p.print_callees()
            ## print 'OUTGOING CALLEES:'
            ## self.p.print_callers()
            self.p.dump_stats('pythonStats')

        self.counter += 1

    def run(self):
        """
        Main control loop
        """
        # Update Environment
        self.time = time.time()

        # Update objects
        self.updateVisionObjects()
        self.updateMotion()
        self.updateLoc()
        self.getCommUpdate()
        self.updateLoc()

        # Behavior stuff
        # Order here is very important
        self.gameController.run()
        self.updatePlaybook()
        self.fallController.run()
        self.player.run()
        self.tracker.run()
        self.nav.run()

        #Set LED message
        self.leds.processLeds()

        # Flush the output
        sys.stdout.flush()

    def getCommUpdate(self):
        self.game = self.interface.gameState
        for i in range(len(self.teamMembers)):
            self.teamMembers[i].update(self.interface.worldModelList()[i])

    def updateMotion(self):
        self.motion = self.interface.motionStatus

    def updateVisionObjects(self):
        """
        Update estimates of robot and ball positions on the field
        """
        self.ball = self.interface.filteredBall
        self.yglp = self.interface.visionField.goal_post_l.visual_detection
        self.ygrp = self.interface.visionField.goal_post_r.visual_detection

    def updatePlaybook(self):
        """
        updates self.play to the new play
        """
        self.playbook.update(self.play)

    def activeTeamMates(self):
        activeMates = 0
        for i in xrange(Constants.NUM_PLAYERS_PER_TEAM):
            mate = self.teamMembers[i]
            if mate.active:
                activeMates += 1
        return activeMates

    def updateLoc(self):
        """
        Make Loc info a RobotLocation.
        """
        self.loc = RobotLocation(self.interface.loc.x,
                                 self.interface.loc.y,
                                 self.interface.loc.h)

    def resetLocTo(self, x, y, h):
        """
        Sends a reset request to loc to reset to given x, y, h
        """
        self.interface.resetLocRequest.x = x
        self.interface.resetLocRequest.y = y
        self.interface.resetLocRequest.h = h
        self.interface.resetLocRequest.timestamp = int(self.time * 1000)

    def resetInitialLocalization(self):
        """
        Reset loc according to team number and team color.
        Note: Loc uses truly global coordinates.
        """
        if self.gameController.teamColor == Constants.teamColor.TEAM_BLUE:
            if self.playerNumber == 1:
                self.resetLocTo(Constants.BLUE_GOALBOX_RIGHT_X,
                                    Constants.FIELD_WHITE_BOTTOM_SIDELINE_Y,
                                    Constants.HEADING_UP,
                                    _localization.LocNormalParams(15.0, 15.0, 1.0))
            elif self.playerNumber == 2:
                self.resetLocTo(Constants.BLUE_GOALBOX_RIGHT_X,
                                    Constants.FIELD_WHITE_TOP_SIDELINE_Y,
                                    Constants.HEADING_DOWN,
                                    _localization.LocNormalParams(15.0, 15.0, 1.0))
            elif self.playerNumber == 3:
                self.resetLocTo(Constants.LANDMARK_BLUE_GOAL_CROSS_X,
                                    Constants.FIELD_WHITE_TOP_SIDELINE_Y,
                                    Constants.HEADING_DOWN,
                                    _localization.LocNormalParams(15.0, 15.0, 1.0))
            elif self.playerNumber == 4:
                self.resetLocTo(Constants.LANDMARK_BLUE_GOAL_CROSS_X,
                                    Constants.FIELD_WHITE_BOTTOM_SIDELINE_Y,
                                    Constants.HEADING_UP,
                                    _localization.LocNormalParams(15.0, 15.0, 1.0))
        else:
            if self.playerNumber == 1:
                self.resetLocTo(Constants.YELLOW_GOALBOX_LEFT_X,
                                    Constants.FIELD_WHITE_TOP_SIDELINE_Y,
                                    Constants.HEADING_DOWN,
                                    _localization.LocNormalParams(15.0, 15.0, 1.0))
            elif self.playerNumber == 2:
                self.resetLocTo(Constants.YELLOW_GOALBOX_LEFT_X,
                                    Constants.FIELD_WHITE_BOTTOM_SIDELINE_Y,
                                    Constants.HEADING_UP,
                                    _localization.LocNormalParams(15.0, 15.0, 1.0))
            elif self.playerNumber == 3:
                self.resetLocTo(Constants.LANDMARK_YELLOW_GOAL_CROSS_X,
                                    Constants.FIELD_WHITE_BOTTOM_SIDELINE_Y,
                                    Constants.HEADING_UP,
                                    _localization.LocNormalParams(15.0, 15.0, 1.0))
            elif self.playerNumber == 4:
                self.resetLocTo(Constants.LANDMARK_YELLOW_GOAL_CROSS_X,
                                    Constants.FIELD_WHITE_TOP_SIDELINE_Y,
                                    Constants.HEADING_DOWN,
                                    _localization.LocNormalParams(15.0, 15.0, 1.0))

        # Loc knows the side of the field now. Reset accordingly.
        self.onOwnFieldSide = True

    #@todo: HACK HACK HACK Mexico 2012 to make sure we still re-converge properly even if
    #we get manually positioned
    #should make this nicer (or at least the locations)
    def resetSetLocalization(self):
        gameSetResetUncertainties = _localization.LocNormalParams(50, 200, 1.0)

        if self.gameController.teamColor == Constants.teamColor.TEAM_BLUE:
            if self.playerNumber == 1:
                self.resetLocTo(Constants.BLUE_GOALBOX_RIGHT_X,
                                Constants.FIELD_WHITE_BOTTOM_SIDELINE_Y,
                                Constants.HEADING_UP)
                if self.gameController.ownKickOff:
                    self.resetLocTo(Constants.LANDMARK_BLUE_GOAL_CROSS_X,
                                    Constants.CENTER_FIELD_Y,
                                    0,
                                    gameSetResetUncertainties)
                else:
                    self.resetLocTo(Constants.BLUE_GOALBOX_RIGHT_X,
                                    Constants.CENTER_FIELD_Y,
                                    0,
                                    gameSetResetUncertainties)
            # HACK: Figure out what this is supposed to do!
            #self.loc.resetLocToSide(True)
        else:
            if self.gameController.ownKickOff:
                self.resetLocTo(Constants.LANDMARK_YELLOW_GOAL_CROSS_X,
                                Constants.CENTER_FIELD_Y,
                                180,
                                gameSetResetUncertainties)
            else:
                self.resetLocTo(Constants.YELLOW_GOALBOX_LEFT_X,
                                Constants.CENTER_FIELD_Y,
                                180,
                                gameSetResetUncertainties)
            #self.loc.resetLocToSide(False)

    def resetLocalizationFromPenalty(self):
        """
        Resets localization to both possible locations, depending on team color.
        """
        return ## HACK -- these resetLocs are too complicated!
        if self.gameController.teamColor == Constants.teamColor.TEAM_BLUE:
            self.resetLocTo(Constants.LANDMARK_BLUE_GOAL_CROSS_X,
                                Constants.FIELD_WHITE_BOTTOM_SIDELINE_Y,
                                Constants.HEADING_UP,
                                Constants.LANDMARK_BLUE_GOAL_CROSS_X,
                                Constants.FIELD_WHITE_TOP_SIDELINE_Y,
                                Constants.HEADING_DOWN,
                                _localization.LocNormalParams(15.0, 15.0, 1.0),
                                _localization.LocNormalParams(15.0, 15.0, 1.0))
        else:
            self.resetLocTo(Constants.LANDMARK_YELLOW_GOAL_CROSS_X,
                                Constants.FIELD_WHITE_BOTTOM_SIDELINE_Y,
                                Constants.HEADING_UP,
                                Constants.LANDMARK_YELLOW_GOAL_CROSS_X,
                                Constants.FIELD_WHITE_TOP_SIDELINE_Y,
                                Constants.HEADING_DOWN,
                                _localization.LocNormalParams(15.0, 15.0, 1.0),
                                _localization.LocNormalParams(15.0, 15.0, 1.0))

        # Loc knows the side of the field now. Reset accordingly.
        self.onOwnFieldSide = True

    def resetGoalieLocalization(self):
        """
        Resets the goalie's localization to the manual position in the goalbox.
        """
        if self.gameController.teamColor == Constants.teamColor.TEAM_BLUE:
            self.resetLocTo(Constants.FIELD_WHITE_LEFT_SIDELINE_X,
                                Constants.MIDFIELD_Y,
                                Constants.HEADING_RIGHT,
                                _localization.LocNormalParams(15.0, 15.0, 1.0))
        else:
            self.resetLocTo(Constants.FIELD_WHITE_RIGHT_SIDELINE_X,
                                Constants.MIDFIELD_Y,
                                Constants.HEADING_LEFT,
                                _localization.LocNormalParams(15.0, 15.0, 1.0))

        # Loc knows the side of the field now. Reset accordingly.
        self.onOwnFieldSide = True

    #TODO: write this method!
    def resetPenaltyKickLocalization(self):
        pass
