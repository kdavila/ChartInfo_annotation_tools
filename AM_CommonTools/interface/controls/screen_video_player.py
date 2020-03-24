
import pygame
import numpy as np
import cv2
import math


from .screen_element import ScreenElement

# TODO: these classes MUST be re-located from AccessMath to AM_CommonTools if possible
from AccessMath.util.opencv_video_player import OpenCVVideoPlayer
from AccessMath.util.image_list_video_player import ImageListVideoPlayer
from AccessMath.util.ST3D_video_player import ST3D_VideoPlayer

class ScreenVideoPlayer(ScreenElement):
    MinSpeedFactor = -3
    MaxSpeedFactor = 4
    VideoPlayerOpenCV = 0
    VideoPlayerImageList = 1
    VideoPlayerST3D = 2

    def __init__(self, name, width, height):
        ScreenElement.__init__(self, name)

        self.width = width
        self.height = height
        self.video_player = None
        self.video_files = None

        self.frame_surface = None
        self.corrected_frame = None
        self.render_width = None
        self.render_height = None
        self.render_location = None

        self.current_frame_idx = 0

        self.speed_factor = 0

        self.blank_frame = None

        #for events...
        self.click_callback = None
        self.frame_changed_callback = None

    def increase_speed(self):
        self.speed_factor += 1
        if self.speed_factor > ScreenVideoPlayer.MaxSpeedFactor:
            self.speed_factor = ScreenVideoPlayer.MaxSpeedFactor

        self.video_player.play_speed = math.pow(2, self.speed_factor)

    def decrease_speed(self):
        self.speed_factor -= 1
        if self.speed_factor < ScreenVideoPlayer.MinSpeedFactor:
            self.speed_factor = ScreenVideoPlayer.MinSpeedFactor

        self.video_player.play_speed = math.pow(2, self.speed_factor)

    def open_video_files(self, video_files, forced_resolution, video_player=0,file_format=None):
        self.video_files = video_files
        if video_player == ScreenVideoPlayer.VideoPlayerOpenCV:
            self.video_player = OpenCVVideoPlayer(self.video_files, forced_resolution)
        elif video_player == ScreenVideoPlayer.VideoPlayerImageList:
            # note that only the first file is used ...
            self.video_player = ImageListVideoPlayer(self.video_files[0], forced_resolution,file_extension=file_format)
        elif video_player == ScreenVideoPlayer.VideoPlayerST3D:
            # special case, instead of video paths, it expects a CCStabilityEstimator and a SpaceTimeStruct
            self.video_player = ST3D_VideoPlayer(self.video_files[0], self.video_files[1])
        else:
            raise Exception("Unknown video player type")

        self.video_player.frame_changed_callback = self.on_video_frame_change

        # check resizing of player (keep original aspect ratio)
        player_ratio = float(self.width) / float(self.height)
        video_ratio = float(self.video_player.width) / float(self.video_player.height)

        if player_ratio >= video_ratio:
            # "horizontal bars"
            render_height = int(self.height)
            render_width = int(render_height * video_ratio)
        else:
            # vertical bars
            render_width = int(self.width)
            render_height = int(render_width * (float(self.video_player.height) / float(self.video_player.width)))

        self.render_width = render_width
        self.render_height = render_height
        self.render_location = (self.position[0] + (self.width - render_width) / 2,
                                self.position[1] + (self.height - render_height) / 2)

    def play(self):
        self.video_player.play()

    def pause(self):
        self.video_player.pause()

    def set_player_frame(self, frame, notify_listeners):
        self.video_player.set_position_frame(frame, notify_listeners)


    def render(self, background, off_x = 0, off_y = 0):
        current_frame, self.current_frame_idx = self.video_player.get_frame()
        if current_frame is not None:
            current_frame = cv2.resize(current_frame, (self.render_width, self.render_height))
        else:
            if self.blank_frame is None:
                self.blank_frame = np.zeros((self.render_height, self.render_width, 3), dtype=np.uint8)
            current_frame = self.blank_frame

        current_frame = np.transpose(current_frame, (1,0,2))
        # correct frame to pygame format
        if self.corrected_frame is None:
            self.corrected_frame = np.zeros(current_frame.shape, current_frame.dtype)

        self.corrected_frame[:,:, 0] = current_frame[:,:, 2]
        self.corrected_frame[:,:, 1] = current_frame[:,:, 1]
        self.corrected_frame[:,:, 2] = current_frame[:,:, 0]

        # can't blit directly because of different dimensions, use temporal surface
        if self.frame_surface is None:
            self.frame_surface = pygame.surfarray.make_surface(self.corrected_frame)
        else:
            pygame.surfarray.blit_array(self.frame_surface, self.corrected_frame)


        background.blit(self.frame_surface, (self.render_location[0] + off_x, self.render_location[1] + off_y))

    def on_mouse_motion(self, pos, rel, buttons):
        # by default, call a callback function (if assigned)
        if self.mouse_motion_callback is not None:
            new_pos = (pos[0] - self.render_location[0], pos[1] - self.render_location[1])
            self.mouse_motion_callback(self, new_pos, rel, buttons)

    def on_mouse_enter(self, pos, rel, buttons):
        # by default, call a callback function (if assigned)
        if self.mouse_enter_callback is not None:
            new_pos = (pos[0] - self.render_location[0], pos[1] - self.render_location[1])
            self.mouse_enter_callback(self, new_pos, rel, buttons)

    def on_mouse_leave(self, pos, rel, buttons):
        # by default, call a callback function (if assigned)
        if self.mouse_leave_callback is not None:
            new_pos = (pos[0] - self.render_location[0], pos[1] - self.render_location[1])
            self.mouse_leave_callback(self, new_pos, rel, buttons)

    def on_mouse_button_click(self, pos, button):
        #by default, do nothing
        if button == 1 and self.click_callback != None:
            self.click_callback(self)

    def on_video_frame_change(self, next_frame, next_abs_time):
        if self.frame_changed_callback is not None:
            self.frame_changed_callback(next_frame, next_abs_time)