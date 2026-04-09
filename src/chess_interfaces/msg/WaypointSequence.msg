# chess_interfaces/msg/WaypointSequence.msg
# Ordered list of waypoints for a complete chess move.

string   move_uci          # UCI string that triggered this sequence, e.g. "e2e4"
Waypoint[] waypoints       # execute in order
