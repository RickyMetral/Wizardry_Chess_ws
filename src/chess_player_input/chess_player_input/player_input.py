"""Orchestrates how to return what move is side makes using Lichess API or stt model. Waits for planner to send a request and will wait until player responds with a move or the game ends"""
import rclpy
import time
import threading
from rclpy.node import Node
from chess_interfaces.srv import PlayerInput
import json
from chess_common_py.lichess_api import LichessApi


class PlayerInputSrvNode(Node):
    move_count = 0
    moves = []

    def __init__(self):
        super().__init__('chess_input_service_node')
        self.srv = self.create_service(PlayerInput, 'player_input', self.get_next_move_callback)
        self.get_logger().info('Chess service node ready!')
        self.lichess = LichessApi()
        self._event_thread_started = False
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)

    def start_event_parsing_thread(self):
        lichess_response = self.lichess.wait_for_board_event() #Will block input until a new move is received
        self.parse_moves_from_events(lichess_response)

    def get_next_move_callback(self, request, response):
        self.get_logger().info(f'Received request with color: {request.player_color}')
        self.lichess.set_game_id(request.game_id)
        self.update_move_count(request.move_count)
        self.get_logger().debug(f"Current list of moves:\n {self.moves}")

        if not self._event_thread_started:
            self._event_thread_started = True
            thread = threading.Thread(target=self.start_event_parsing_thread, daemon=True)
            thread.start()


        if request.player_color == "w":
            move = self.get_white_move()#Gets move from moves buffer
            response.move = move
            return response
        
        elif request.player_color == "b":
            move = self.get_black_move()#Gets move from moves buffer
            response.move = move
            return response

        #If we could not understand the player color send an error
        else:
            response.move = "error"  
            return response

    #Will append to the move buffers holding all the moves for each color
    def parse_moves_from_events(self, response):
        #Each line is a new event that has been appended to the NDJSON
        for line in response.iter_lines():
            #Some lines may be empty for keep alive
            if line:
                event = json.loads(line)
                
                #If there is an event error
                if event.get("error"):
                    self.get_logger().warn("Something went wrong parsing events")
                    break

                elif event["type"] == "gameFinish":
                    print("Game is over!")
                    self.moves.append("end")
                    break

                # First event, contains full game info and current moves
                elif event["type"] == "gameFull":
                    lichess_moves = event["state"]["moves"]
                    #If moves list is empty
                    if not lichess_moves:
                        continue
                    last_move = lichess_moves.rsplit(" ", 1)[-1]
                    self.append_to_move_buffer(last_move)

                elif event["type"] == "gameState":
                    lichess_moves = event["moves"]
                    #If moves list is empty
                    if not lichess_moves:
                        continue
                    last_move = lichess_moves.rsplit(" ", 1)[-1]
                    self.append_to_move_buffer(last_move)

                else:
                    continue

    #Gets the most recent white move in a list of moves
    def get_white_move(self) -> str:
        #Loop until enough moves have been input
        with self.condition:
                self.condition.wait_for(
                    lambda: len(self.moves) > (self.move_count)
                )
                if self.move_count % 2 == 0:
                    return self.moves[self.move_count]
                else:
                    self.get_logger().warn("Move count was not even")
                    return "error"

    #Gets the most recent black move in a list of moves
    def get_black_move(self) -> str:
        #Loop until enough moves have been input
        with self.condition:
                self.condition.wait_for(
                    lambda: len(self.moves) > self.move_count
                )
                if self.move_count % 2 == 1:
                    return self.moves[self.move_count]
                else:
                    self.get_logger().warn("Move count was not odd")
                    return "error"
    
    def update_move_count(self, move_count: int):
        self.move_count = move_count
    
    def append_to_move_buffer(self, move: str):
        with self.condition:
            self.moves.append(move)
            self.condition.notify_all()


def main(args=None):
    rclpy.init(args=args)
    node = PlayerInputSrvNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()