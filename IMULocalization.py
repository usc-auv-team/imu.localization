import numpy as np
from quaternion import Quaternion
from madgwickahrs import MadgwickAHRS

# quat = Quaternion(1,0,0,0)
# madgwick = MadgwickAHRS(1/400, quat, 1)
#
# def getQuaternion(gyroscope, accelerometer, magnetometer = None, madgwick = madgwick):
#     madgwick.update_imu(gyroscope, accelerometer)
#     return madgwick.quaternion

result = getQuaternion([0,0,0], [0,0,.3])
qw = result[0]
qx = result[1]
qy = result[2]
qz = result[3]
rotationMatrix = np.matrix([[1-2*qy**2-2*qz**2,2*qx*qy-2*qz*qw,2*qx*qz+2*qy*qw],
                            [2*qx*qy+2*qz*qw,1-2*qx**2-2*qz**2,2*qy*qz-2*qx*qw],
                            [2*qx*qz-2*qy*qw,2*qy*qz+2*qx*qw,1-2*qx**2-2*qy**2]])
trueAcceleration = np.matmul(np.linalg.inv(rotationMatrix), np.matrix([[0],[0],[.3]]))
print(trueAcceleration)
