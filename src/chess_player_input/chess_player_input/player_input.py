"""Orchestrates how to return what move is side makes using Lichess API or stt model. Waits for planner to send a request and will wait until player responds with a move or the game ends"""
import rclpy
from rclpy.node import Node
from chess_interfaces.srv import PlayerInput
from chess_common_py.lichess_api import LichessApi


class PlayerInputSrvNode(Node):
    def __init__(self):
        super().__init__('chess_input_service_node')
        self.srv = self.create_service(PlayerInput, 'player_input', self.get_next_move_callback)
        self.get_logger().info('Chess service node ready!')
        self.lichess = LichessApi()

    def get_white_move(self):
        while True:
            lichess_response = self.lichess.wait_for_board_event() #Will block input until a new move is received
            move_list = self.lichess.parse_moves_from_events(lichess_response)

            #If game is over return 'finished'
            if move_list == None:
                return "finished"
        
            #If no new move has been made wait again
            elif not move_list:
                continue
        
            #Return most recent white move from list of moves
            else:
                return self.lichess.get_white_move(move_list)

    def get_black_move(self):
        while True:
            lichess_response = self.lichess.wait_for_board_event()#Will block input until a new move is received)
            move_list = self.lichess.parse_moves_from_events(lichess_response)

            #If game is over return 'finished'
            if move_list == None:
                return "finished"
        
            #If no new move has been made wait again
            elif not move_list:
                continue
        
            #Retrive most recent black move from list of moves
            else:
                return self.lichess.get_black_move(move_list)

    def get_next_move_callback(self, request, response):
        self.get_logger().info(f'Received request with player color: {request.player_color}')
        self.lichess.set_game_id(request.game_id)
        self.lichess.update_move_count(request.move_count)

        if request.player_color == "w":
            move = self.get_white_move()
            response.move = move
            return response
        
        elif request.player_color == "b":
            move = self.get_black_move()
            response.move = move
            return response

        #If we could not understand the player color send an error
        else:
            response.move = "error"  
            return response
        

def main(args=None):
    rclpy.init(args=args)
    node = PlayerInputSrvNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()