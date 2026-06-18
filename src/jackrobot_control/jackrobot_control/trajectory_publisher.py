import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import math

class TrajectoryPublisher(Node):

    def __init__(self):
        super().__init__('trajectory_publisher')
        
        # 建立 JointState 的發布者 (與 robot_state_publisher 對接)
        self.publisher_ = self.create_publisher(JointState, '/joint_states', 10)
        
        # 設定定時器：每 50 毫秒 (0.05 秒) 執行一次控制迴圈 (20 Hz)
        self.timer_period = 0.05
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        
        # 定義 5 個關節空間的目標點 (對應手臂的 5 個可動關節)
        # 關節依序為: [arm_0_joint, arm_1_joint, arm_2_joint, gripper_1_joint, gripper_2_joint]
        self.waypoints = [
            [0.0,   0.0,   0.0,   0.0,   0.0],    # 點 1: 初始姿態
            [1.0,   0.5,   0.5,  -0.03, -0.03],   # 點 2: 舉起並閉合夾爪
            [2.0,  -0.5,   1.0,   0.0,   0.0],    # 點 3: 擺動至另一側並張開
            [-1.0,  0.8,  -0.5,  -0.02, -0.02],   # 點 4: 換角度低頭
            [0.0,   0.3,   0.2,   0.0,   0.0]     # 點 5: 準備返回初始點
        ]
        
        self.current_waypoint_idx = 0
        self.next_waypoint_idx = 1
        self.interpolation_steps = 40  # 兩點之間插補 40 步 (40 * 0.05秒 = 2秒移動時間)
        self.step_counter = 0

    def timer_callback(self):
        msg = JointState()
        # 填充時間戳記與關節名稱 (必須與 URDF 內定義的名稱完全一致)
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [
            'arm_0_joint', 
            'arm_1_joint', 
            'arm_2_joint', 
            'gripper_1_joint', 
            'gripper_2_joint'
        ]
        
        # 計算線性插補權重 t (從 0.0 線性增加到 1.0)
        t = self.step_counter / self.interpolation_steps
        
        # 平滑化權重 t (使用平滑階梯函數 Smoothstep: 3t^2 - 2t^3 讓速度連續)
        t_smooth = 3 * (t ** 2) - 2 * (t ** 3)
        
        # 取得當前點與下一個目標點
        start_p = self.waypoints[self.current_waypoint_idx]
        end_p = self.waypoints[self.next_waypoint_idx]
        
        # 計算當前步的插補關節角度
        msg.position = []
        for i in range(len(start_p)):
            pos = start_p[i] + (end_p[i] - start_p[i]) * t_smooth
            msg.position.append(pos)
            
        # 發布訊息
        self.publisher_.publish(msg)
        
        # 推進步數計數器
        self.step_counter += 1
        if self.step_counter > self.interpolation_steps:
            # 到達目標點，切換至下一段軌跡
            self.step_counter = 0
            self.current_waypoint_idx = self.next_waypoint_idx
            self.next_waypoint_idx = (self.next_waypoint_idx + 1) % len(self.waypoints)

def main(args=None):
    rclpy.init(args=args)
    node = TrajectoryPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
