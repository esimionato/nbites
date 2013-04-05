from math import fabs, hypot
from . import NavConstants as constants
import NavStates as states
from ..util import MyMath
import noggin_constants as NogginConstants
from ..players import ChaseBallTransitions
from . import NavHelper as helper

DEBUG = True

def atDestination(nav):
    """
    Returns true if we're close enough to nav's current destination;
    Takes into account loc uncertainty to check if we're at least close to
    the destination according to our belief
    """
    relDest = helper.getRelativeDestination(nav.brain.my, states.goToPosition.dest)
    my = nav.brain.my
    (x, y, h) = states.goToPosition.precision

    if (not helper.isDestinationRelative(states.goToPosition.dest)):
        return relDest.within((x + my.uncertX, y + my.uncertY, h + my.uncertH))
    else:
        return relDest.within((x, y, h))

def shouldDodgeLeft(nav):
    if not states.goToPosition.avoidObstacles:
        return False

    # check sonars
    sonarState = nav.brain.interface.sonarState
    sonars = (sonarState.us_right != -1 and
              sonarState.us_right < constants.AVOID_OBSTACLE_SIDE_DIST)

    #check vision
    vision = nav.brain.vision.obstacles.onRight

    #check feet
    footBumperState = nav.brain.interface.footBumperState
    feet = (footBumperState.r_foot_bumper_left or
            footBumperState.r_foot_bumper_right)

    if (feet and vision):
        return True
    elif (vision and sonars):
        return True
    elif (sonars and feet):
        return True

    else:
        return False

def shouldDodgeRight(nav):
    if not states.goToPosition.avoidObstacles:
        return False

    # check sonars
    sonarState = nav.brain.interface.sonarState
    sonars = (sonarState.us_left != -1 and
              sonarState.us_left < constants.AVOID_OBSTACLE_SIDE_DIST)
    #check vision
    vision = nav.brain.vision.obstacles.onLeft

    #check feet
    footBumperState = nav.brain.interface.footBumperState
    feet = (footBumperState.l_foot_bumper_left or
            footBumperState.l_foot_bumper_right)

    if (feet and vision):
        return True
    elif (vision and sonars):
        return True
    elif (sonars and feet):
        return True

    else:
        return False

def doneDodging(nav):
    return nav.brain.interface.motionStatus.standing

def notAtLocPosition(nav):
    return not atDestination(nav)

def walkedEnough(nav):
    deltaDest = states.walkingTo.deltaDest
    dest = states.walkingTo.dest
    precision = states.walkingTo.precision

    #check if we've "passed" the point we were supposed to go to
    #with odometry
    if (dest.relX * deltaDest.relX < 0 and
        dest.relY * deltaDest.relY < 0 and
        dest.relH * deltaDest.relH < 0):
        return True

    return deltaDest.within(precision)

######### BALL IN BOX ###############

#keeping this code around for posterity; do we actually need it?
#not safe to call as of 4/4/2013

def shouldChaseAroundBox(my, ball):

    # 3 common, simple cases where we don't need to worry about the box.
    if my.x > NogginConstants.MY_GOALBOX_RIGHT_X:
        if ball.loc.x > NogginConstants.MY_GOALBOX_RIGHT_X:
            return False

    if my.y < NogginConstants.MY_GOALBOX_BOTTOM_Y:
        if ball.loc.y < NogginConstants.MY_GOALBOX_BOTTOM_Y:
            return False

    if my.y > NogginConstants.MY_GOALBOX_TOP_Y:
        if ball.loc.y > NogginConstants.MY_GOALBOX_TOP_Y:
            return False

    # handle more complex cases where correct behavior isn't obvious
    intersect = MyMath.linesIntersect

    return ( intersect( my.x, my.y, ball.loc.x, ball.loc.y, # BOTTOM_GOALBOX_LINE
                        NogginConstants.MY_GOALBOX_LEFT_X,
                        NogginConstants.MY_GOALBOX_BOTTOM_Y,
                        NogginConstants.MY_GOALBOX_RIGHT_X,
                        NogginConstants.MY_GOALBOX_BOTTOM_Y) or
             intersect( my.x, my.y, ball.loc.x, ball.loc.y, # LEFT_GOALBOX_LINE
                        NogginConstants.MY_GOALBOX_RIGHT_X,
                        NogginConstants.MY_GOALBOX_TOP_Y,
                        NogginConstants.MY_GOALBOX_RIGHT_X,
                        NogginConstants.MY_GOALBOX_BOTTOM_Y) or
             intersect( my.x, my.y, ball.loc.x, ball.loc.y, # BOTTOM_GOALBOX_LINE
                        NogginConstants.MY_GOALBOX_LEFT_X,
                        NogginConstants.MY_GOALBOX_TOP_Y,
                        NogginConstants.MY_GOALBOX_RIGHT_X,
                        NogginConstants.MY_GOALBOX_TOP_Y) )

