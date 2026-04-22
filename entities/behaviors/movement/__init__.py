"""
Movement Strategies Module

Contains all movement behavior algorithms.
Each strategy implements a different way of moving through the savanna.
"""

from .random_walk import RandomWalkStrategy
from .herd_follow import HerdFollowStrategy
from .seek_target import SeekTargetStrategy
from .flee import FleeStrategy