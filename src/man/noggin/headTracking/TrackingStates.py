from man.motion import MotionConstants
from . import TrackingConstants as constants
from objects import RelLocation

DEBUG = False

def ballTracking(tracker):
    '''Super state which handles following/refinding the ball'''
    if tracker.target.vis.framesOff <= \
            constants.TRACKER_FRAMES_OFF_REFIND_THRESH:
        return tracker.goNow('tracking')
    else:
        return tracker.goNow('scanBall')

def tracking(tracker):
    """
    While the target is visible, track it via vision values.
    If the ball is lost, go to last diff state.
    """

    if tracker.firstFrame():
        tracker.activeLocOn = False

    if tracker.target.dist > constants.ACTIVE_TRACK_DIST:
        return tracker.goLater('activeTracking')

    tracker.helper.trackObject()

    if not tracker.target.vis.on:
        if DEBUG : tracker.printf("Missing object this frame",'cyan')
        if tracker.target.vis.framesOff > \
                constants.TRACKER_FRAMES_OFF_REFIND_THRESH:
            return tracker.goLater(tracker.lastDiffState)
        return tracker.stay()

    return tracker.stay()

def ballSpinTracking(tracker):
    '''Super state which handles following/refinding the ball'''
    if tracker.target.vis.framesOff <= \
            constants.TRACKER_FRAMES_OFF_REFIND_THRESH:
        return tracker.goNow('tracking')
    else:
        return tracker.goNow('spinScanBall')

def activeTracking(tracker):
    """
    If ball is visible and close, track it via vision values.
    If ball is not visible, execute naive pans.
    If state counter is low enough, track ball via vision values.
    If state counter is high enough, perform triangle pans
    and return to last head angles.
    """
    if tracker.firstFrame():
        tracker.shouldStareAtBall = 0
        tracker.activeLocOn = True

    tracker.helper.trackObject()

    # If we are close to the ball and have seen it consistently
    if tracker.target.dist < constants.STARE_TRACK_DIST:
        tracker.shouldStareAtBall += 1

        if tracker.shouldStareAtBall > constants.STARE_TRACK_THRESH:
            return tracker.goLater('tracking')
    else:
        tracker.shouldStareAtBall = 0

    if tracker.target.vis.framesOff > \
            constants.TRACKER_FRAMES_OFF_REFIND_THRESH and \
            tracker.counter > constants.TRACKER_FRAMES_OFF_REFIND_THRESH:
        return tracker.goLater('activeLocScan')

    elif tracker.counter >= constants.BALL_ON_ACTIVE_PAN_THRESH and \
            tracker.target.vis.on:
        return tracker.goLater('panToFieldObject')

    return tracker.stay()

def panToFieldObject(tracker):
    """
    Calculate which goalpost is easiest to look at and look to it.
    After we look at it for a bit, look back at target.
    """

    # Calculate closest field object
    if tracker.firstFrame():

        closest = tracker.helper.calculateClosestLandmark()

        # For some reason, we aren't going to look at anything, so go
        # back to tracking
        if closest is None:
            return tracker.goLater('activeTracking')

        target = RelLocation(tracker.brain.my, closest.x, closest.y, 0)
        target.height = 45

        tracker.lastMove = tracker.helper.lookToPoint(target)

    elif tracker.lastMove.isDone():
        return tracker.goLater('activeTracking')

    return tracker.stay()
