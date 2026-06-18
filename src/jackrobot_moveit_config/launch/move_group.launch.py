from launch import LaunchDescription
from launch_ros.actions import SetParameter
from launch.actions import TimerAction  # 引入定時器模組
from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_move_group_launch


def generate_launch_description():
    moveit_config = (
        MoveItConfigsBuilder("arm_manipulator", package_name="jackrobot_moveit_config")
        .to_moveit_configs()
    )

    # 1. 取得 MoveIt 預設的啟動描述物件
    move_group_launch = generate_move_group_launch(moveit_config)

    # 2. 【核心優化】將 MoveIt 的所有內部節點，通通包進一個「延遲 5 秒」的定時器中
    # 這樣可以確保 Gazebo 已經完全把機器人印好、控制器完全啟動後，大腦才進場對接
    delayed_move_group_entities = TimerAction(
        period=5.0,
        actions=move_group_launch.entities
    )

    return LaunchDescription([
        # 強制讓這個 Launch 裡的所有子節點一律採用模擬器時間
        SetParameter(name="use_sim_time", value=True),
        
        # 啟動被延遲的大腦
        delayed_move_group_entities
    ])
