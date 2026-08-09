"""Test suite for the Robot Walk Recognizer -- TECH 315 Week 6 deliverable.

The system under test is the ``robot_walk`` package in the repository root,
imported unchanged: the tests never edit, patch, or re-implement any part of
it. Importing this package puts that root on the import path so that
``from robot_walk import dfa`` works from any test module.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir)
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
