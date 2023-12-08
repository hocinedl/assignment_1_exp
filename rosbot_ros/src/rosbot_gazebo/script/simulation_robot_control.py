#!/usr/bin/env python

import sys
import rospy
from std_msgs.msg import Float64, Int32
from sensor_msgs.msg import  Image
from geometry_msgs.msg import Twist, Point

# Constants
pixel_limit = 170
camera_width = 320
allignment_thr = 70
distance_thr = 2

class RobotController:

    def __init__(self):
        rospy.init_node('image_feature', anonymous=True)

        #publisher to publish the cmd vel commands
        self.vel_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)

        #subscribing to the /camera/color/image_raw topic so that each time something is published in this topic the callback will run
        self.subscriber = rospy.Subscriber("/camera/color/image_raw", Image, self.control_loop_callback, queue_size=1)

        #subscription to the topics to extract the id, seze and center of the marker.
        self.id_subscriber = rospy.Subscriber("/marker_id", Int32, self.id_callback, queue_size=1)
        self.marker_center_sub = rospy.Subscriber("/marker_center", Point, self.marker_center_callback, queue_size=1)
        self.marker_size_sub = rospy.Subscriber("/marker_size", Float64, self.marker_size_callback, queue_size=1)

        #initializations
        self.marker_list = [11, 12, 13, 15]
        self.marker_id = 0
        self.marker_size = 0.0
        self.robot_state = "searching"

    #control loop for the robot to perform the task.
    def control_loop_callback(self, _):
        if not self.marker_list:
            rospy.signal_shutdown("All markers reached")
            return

        if self.marker_id == self.marker_list[0]:
            self.error = abs(self.marker_center_x - camera_width)

            if self.marker_size > pixel_limit and self.robot_state == "searching":
                self.stop_robot()
                self.transition_to_next_marker()

            elif self.error < allignment_thr and self.robot_state == "searching":
                self.align_robot_with_marker()

                if self.error < distance_thr:
                    self.stop_robot()
                    self.transition_to_next_marker()
                else:
                    self.move_forward()

            else:
                self.print_debug_info()

        else:
            self.search_for_marker()

    #callbacks to extract data from topics.    
    def id_callback(self, data):
        self.marker_id = data.data

    def marker_center_callback(self, data):
        self.marker_center_x, self.marker_center_y = data.x, data.y

    def marker_size_callback(self, data):
        self.marker_size = data.data
    
    #functions for robot movements
    def stop_robot(self):
        print("MARKER REACHED:", self.marker_id)
        cmd_vel = Twist()
        cmd_vel.linear.x, cmd_vel.angular.z = 0.0, 0.0
        self.vel_pub.publish(cmd_vel)

    def transition_to_next_marker(self):
        if len(self.marker_list) > 1:
            self.marker_list.pop(0)
            self.robot_state = "searching"
            print("Transitioning to searching state")
        else:
            rospy.signal_shutdown("All markers reached")
            print("All markers reached. Shutting down.")

    def align_robot_with_marker(self):
        print("ROBOT AND MARKER ALIGNED!")
        cmd_vel = Twist()
        cmd_vel.linear.x, cmd_vel.angular.z = 0.0, 0.0
        self.vel_pub.publish(cmd_vel)

    def move_forward(self):
        print("Continuing to move forward.")
        cmd_vel = Twist()
        cmd_vel.linear.x, cmd_vel.angular.z = 0.2, 0.0
        self.vel_pub.publish(cmd_vel)

    def search_for_marker(self):
        print("ROBOT SEARCHING FOR MARKER...")
        cmd_vel = Twist()
        cmd_vel.linear.x, cmd_vel.angular.z = 0.0, 0.5
        self.vel_pub.publish(cmd_vel)

    def print_debug_info(self):
        print("Marker ID:", self.marker_id)
        print("Error:", self.error)
        print("Robot State:", self.robot_state)


def main(args):
    ic = RobotController()
    try:
        rospy.spin()
    except KeyboardInterrupt:
        print("Shutting down ROS Image feature detector module")

if __name__ == '__main__':
    main(sys.argv)


