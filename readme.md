# 🤖 JackRobot ROS 2 機械手臂虛實整合工作空間 (ROS Camp & Lab Project)（至第assignments.pdf 8章節截止）

本專案為 **ROS Camp 培訓與自動化實驗室** 之核心開發成果。主要實現了一套基於 **ROS 2 Jazzy** 環境的 4-DOF 機械手臂（`jackrobot`）虛實整合模擬系統。本專案成功克服了 ROS 2 與新版 Gazebo Sim 在時間軸同步、時序控制（Race Condition）上的經典衝突，採用先進的 **Python Launch 定時器機制** 達成高穩定度的一鍵自動化雙視窗啟動。

---

## 📌 核心基礎概念

在深入操作前，請務必理解以下本工作空間運作的核心技術架構：

### 1. ROS 2 工作空間與環境疊加 (Workspace Overlaying)
ROS 2 採用隔離的工作空間設計。編譯完成後的二進位檔與設定檔皆存放在 `install` 資料夾中。每次開啟新終端機時，必須透過 `source install/setup.bash` 將此工作空間的路徑「疊加」到系統環境變數中，否則系統將無法識別自訂的機器人節點與 Launch 檔案。

### 2. MoveIt 2 運動規劃核心
負責處理高難度的機械手臂逆運動學（IK）求解與三維空間避障規劃。本專案捨棄了容易因未指定工藝型態而報錯的工業級 Pilz 規劃器，全數全面對接相容性最高、適應隨機空間障礙物的 **OMPL（RRTConnect 算法）**。

### 3. ros2_control 與 控制器橋樑
為 ROS 2 官方標準的硬體控制框架。在本專案中扮演「神經網路」的角色：
* **`joint_state_broadcaster`**：實時收集 Gazebo 物理世界中各關節的真實角度，並以 100Hz 頻率廣播給全域（包括 RViz2），若其暴斃，RViz2 將會顯示 `No transform` 錯誤。
* **`arm_controller` & `gripper_controller`**：基於 `joint_trajectory_controller` 插件，負責接收 MoveIt 計算出來的流暢時間最優化軌跡軌道（Splines），並轉化為位置控制命令驅動虛擬馬達。

### 4. 模擬時間同步 (Simulation Time Synchronization)
在虛實整合開發中，模擬器（Gazebo）往往因電腦效能限制，其內部物理時鐘（Simulation Time）會慢於牆上的真實世界時間（Wall Time）。因此，全域節點（MoveIt、RViz2、控制器）必須強行鎖定 **`use_sim_time:=True`**，強制所有人聆聽 Gazebo 發布的 `/clock` 議題。若時間軸脫節，大腦會判定指令「過期」而拋出 `CONTROL_FAILED` 阻擋執行。

---

## 🛠/📋 本專案常用指令速查表 (Cheat Sheet)

### 1. 編編譯與環境建置
| 指令 | 功能描述 | 適用時機 |
| :--- | :--- | :--- |
| `colcon build --symlink-install` | 編譯整個工作空間。使用軟連結避免微調 Python/YAML 時需反覆重編。 | 修改了程式碼、Launch 檔或控制器 YAML 後。 |
| `rm -rf build/ install/ log/` | 徹底掃除所有編譯快取與舊檔案。 | 遇到不明常駐錯誤、快取死鎖、或大改設定檔結構時。 |
| `source install/setup.bash` | 將目前編譯成果刷入該終端機視窗。 | **每一次開啟全新終端機分頁時的必備動作。** |

### 2. 後台進程大清空（終極除錯特效藥）
當多次異常中斷（Ctrl+C）或遇到控制崩潰後，Gazebo 與 MoveIt 的物理渲染引擎往往會變成「背景殭屍進程」死死霸佔 Port，導致後續模擬器閃退、開不起來或控制器載入失敗（Failed to configure）。請直接執行以下**強效清道夫組合拳**：
```bash
pkill -f gz && pkill -f ruby && pkill -f move_group && pkill -f rviz2 && pkill -f ros2_control
```
# 3. 實時除錯與狀態監測


查看目前系統中活著的所有 ROS 2 議題清單
ros2 topic list

# 🏃‍♂️操作與使用教學

本專案已將「生產機器人」、「加載控制器」、「開啟視覺化 RViz2」與「載入 MoveIt 大腦」四大繁瑣步驟，透過內建 4 秒及 7 秒定時延遲技術，完美收斂至雙視窗一鍵全開機制。
# 步驟 1：啟動虛擬物理世界後台 (視窗 1)

打開第一個終端機分頁，輸入指令來建立空白的虛擬模擬世界：
Bash

cd ~/ros2_ws
source install/setup.bash
ros2 launch jackrobot_gazebo start_simulator.launch.xml

    ⚠️ 關鍵檢查點：

        請等待灰色網格的 Gazebo Sim 視窗完全跳出。

        極重要： 請將視線移至 Gazebo 視窗的正下方或左下角，確保物理模擬處於「Play（三角形播放鍵）」狀態。若處於暫停，全系統時鐘將凍結在 0.00 秒。

# 步驟 2：身體與大腦一鍵完全體啟動 (視窗 2)

打開第二個全新的終端機分頁，執行流暢時序自動化腳本：
Bash

cd ~/ros2_ws
source install/setup.bash
ros2 launch jackrobot_gazebo spawn_robot.launch.py

    📊 自動時序流程說明：
    敲下指令後，請靜靜觀察終端機與模擬器畫面：

        T = 0 秒：紅白相間的 jackrobot 機械手臂實體立刻「刷」地出現在 Gazebo 模擬器正中央。

        T = 4 秒：定時器觸發，後台優雅印出 Configured and activated arm_controller、gripper_controller、joint_state_broadcaster。三大控制器毫無衝突、完美激活！

        T = 7 秒：定時器再度觸發，RViz2 圖形控制介面自動彈出，此時因為 MoveIt 參數大禮包已完美注入，全關節 TF 座標變換完美呈現綠色 OK 狀態，絕無死白或斷線紅字。

🎮 如何在 RViz2 介面中操控機械手臂？

    喚醒規劃插件：
    若 RViz2 打開後沒看見面板，請點擊左下角 Add 按鈕 -> 在彈出選單中雙擊 MotionPlanning 插件。

    切換核心大腦為 OMPL：
    看向中央的 MotionPlanning 控制面板，點擊進入 Context（上下文） 頁籤。找到 Planning Pipeline 下拉選單，將預設的 pilz 工業規劃器切換改選為 ompl。

    拖曳目標影子：
    切換回 Planning 頁籤，點擊下方的 Query -> Update。此時手臂前端夾爪會蹦出可以滑鼠互動的發光控制球與箭頭。用滑鼠按住它並任意拖曳到你想抵達的空間新座標（此時會出現一隻橘色的虛擬影子手臂）。

    見證虛實聯動同步跳舞：
    確認目標姿勢後，大膽點擊左下角面板的 Plan & Execute 按鈕。
    此時 MoveIt 大腦會瞬間解算逆運動學並優化時間軌跡，將驅動命令精準注入。你會親眼見證 左邊 Gazebo 世界裡的實體紅白手臂，跟著右邊 RViz2 的軌跡極其平滑、流暢、無延遲地同步擺動至指定座標！

# 💡 常見故障排除 (Troubleshooting)
Q1：RViz2 一直卡在 Status: Error 且旋轉關節全部顯示 No transform from...？

    原因：ROS 2 時間軸凍結在 0.00 秒，導致動態關節角度發布器沒有工作。

    解法：去第一個視窗看 Gazebo 模擬器，它此時一定處於 Pause（暫停）狀態，用滑鼠點擊 Play（播放按鈕），讓時間開始走，紅字就會在 0.5 秒內全部轉綠現形。

Q2：MotionPlanning 面板跳出刺眼的紅字 NO PLANNING LIBRARY LOADED 且下拉選單空空如也？

    原因：RViz2 啟動時沒有得到 MoveIt 的參數字典，處於裸奔狀態。

    解法：請確保你的 spawn_robot.launch.py 中，rviz2_node 區塊內已經確實加上了 parameters=[moveit_config.to_dict()] 這行全功能大禮包注入參數，並重新 colcon build 即可解決。

Q3：不小心猛烈中斷程式後，下次再開連第一個視窗 Gazebo 都開不起來或控制器狂噴死掉（process has died）？

    原因：背景殘留的「殭屍進程」鎖死系統通訊埠。

    解法：直接複製並執行本手冊提供的 [後台進程大清空] 指令，清乾淨後重新按照標準順序開啟視窗，即可滿血復活。
