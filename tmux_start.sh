#!/bin/bash
#
#  Start tmux.
#
#

tmux start-server

# TODO: Get a main-horizontal split with the big window on the left.

# New session should default to name "dev".
tmux new -s dev
