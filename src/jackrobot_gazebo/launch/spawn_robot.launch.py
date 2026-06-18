import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node, SetParameter
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    # ================= 1. 初始化 MoveIt 大腦參數 =================
    moveit_config = (
        MoveItConfigsBuilder("arm_manipulator", package_name="jackrobot_moveit_config")
        .to_moveit_configs()
    )

    # ================= 2. 身體組件（立即啟動） =================
    # 讀取機器人 URDF 模型並發布
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[moveit_config.robot_description],
        remappings=[("robot_description", "/robot_description")]
    )

    # 在 Gazebo 模擬器中生產實體機器人
    gazebo_spawner_node = Node(
        package="ros_gz_sim",
        executable="create",
        name="robot_spawner",
        output="screen",
        arguments=["-topic", "/robot_description", "-name", "arm_manipulator", "-x", "0", "-y", "0", "-z", "0"]
    )

    # ================= 3. 控制器組件（延遲 4 秒啟動） =================
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        name="joint_state_broadcaster_spawner",
        arguments=["joint_state_broadcaster", "-c", "/controller_manager"],
        output="screen"
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        name="arm_controller_spawner",
        arguments=["arm_controller", "-c", "/controller_manager"],
        output="screen"
    )

    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        name="gripper_controller_spawner",
        arguments=["gripper_controller", "-c", "/controller_manager"],
        output="screen"
    )

    delay_controllers = TimerAction(
        period=4.0,
        actions=[
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
            gripper_controller_spawner
        ]
    )

    # ================= 4. 大腦與視覺組件（延遲 7 秒啟動） =================
    # 運動規劃核心
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
    )

    # 視覺介面視覺化
    rviz_config_file = os.path.join(
        get_package_share_directory("jackrobot"), "config", "config.rviz"
    )
    
    # 【核心修正】在 rviz2_node 中同樣注入 moveit_config.to_dict() 參數
    # 這樣 RViz 才能順利加載 OMPL 規劃函式庫、逆運動學求解器，並長出互動式發光球
    rviz2_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
        parameters=[moveit_config.to_dict()]
    )

    delay_moveit_and_rviz = TimerAction(
        period=7.0,
        actions=[
            move_group_node,
            rviz2_node
        ]
    )

    # ================= 5. 建立啟動描述並強制同步時間 =================
    return LaunchDescription([
        # 強制讓這份檔案裡誕生的所有節點百分之百同步聽從 Gazebo 的模擬時間
        SetParameter(name="use_sim_time", value=True),

        robot_state_publisher_node,
        gazebo_spawner_node,
        delay_controllers,
        delay_moveit_and_rviz
    ])