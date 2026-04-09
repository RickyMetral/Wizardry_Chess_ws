# chess_interfaces/msg/Waypoint.msg
# A single gantry target position with gripper state.

float64 x       # file direction (metres from a1 corner)
float64 y       # rank direction (metres from a1 corner)
float32 z       # height above board surface (metres)
bool    grip    # true = electromagnet / gripper ON
