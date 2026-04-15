from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import TimerAction

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='chess_board_state',
            executable='chess_board_state_node',
            output='screen',
            arguments=['--ros-args', '--log-level', 'info'] 
        ),
        Node(
            package='chess_player_input',
            executable='lichess_player_input_node',
            output='screen',
            arguments=['--ros-args', '--log-level', 'info'] 
        ),
        TimerAction(
            period=3.0,
            actions=[
                Node(
                    package='chess_planner',
                    executable='lichess_planner_node',
                    output='screen',
                    arguments=['--ros-args', '--log-level', 'info'] 
                ),
            ]
        ),
    ])