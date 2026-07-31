cmake_minimum_required(VERSION 3.0.2)
project(wuji_retargeting)

find_package(catkin REQUIRED)

catkin_python_setup()

catkin_package()

# The python module resolves URDFs relative to its own files
# (wuji_retargeting/opt/base.py: _PACKAGE_ROOT / "wuji_hand_description/urdf/<side>.urdf"),
# so the urdf directory must be installed alongside the python package. setup.py package_data
# is unreliable under catkin_python_setup, hence the explicit CMake install.
install(
  DIRECTORY wuji_retargeting/wuji_hand_description/urdf
  DESTINATION ${CATKIN_GLOBAL_PYTHON_DESTINATION}/wuji_retargeting/wuji_hand_description
)

install(
  DIRECTORY config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
