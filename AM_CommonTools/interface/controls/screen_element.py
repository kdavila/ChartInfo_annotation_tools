
class ScreenElement:
    def __init__(self, name):
        self.name = name
        self.position = (0,0)
        self.width = 0
        self.height = 0
        self.parent = None
        self.visible = True
        self.is_container = False

        # for events
        self.click_callback = None
        self.double_click_callback = None
        self.key_up_callback = None
        self.mouse_motion_callback = None
        self.mouse_enter_callback = None
        self.mouse_leave_callback = None
        self.mouse_button_up_callback = None
        self.mouse_button_down_callback = None


    def get_left(self):
        return self.position[0]
    
    def get_top(self):
        return self.position[1]
    
    def get_bottom(self):
        return self.position[1] + self.height
    
    def get_right(self):
        return self.position[0] + self.width
    
    def get_center_x(self):
        return int(self.position[0] + (self.width / 2))
    
    def get_center_y(self):
        return int(self.position[1] + (self.height / 2))
        
    def on_mouse_motion(self, pos, rel, buttons):
        # by default, call a callback function (if assigned)
        if self.mouse_motion_callback is not None:
            self.mouse_motion_callback(self, pos, rel, buttons)
    
    def on_mouse_enter(self, pos, rel, buttons):
        # by default, call a callback function (if assigned)
        if self.mouse_enter_callback is not None:
            self.mouse_enter_callback(self, pos, rel, buttons)
    
    def on_mouse_leave(self, pos, rel, buttons):
        # by default, call a callback function (if assigned)
        if self.mouse_leave_callback is not None:
            self.mouse_leave_callback(self, pos, rel, buttons)
        
    def on_mouse_button_up(self, pos, button):
        # by default, call a callback function (if assigned)
        if self.mouse_button_up_callback is not None:
            self.mouse_button_up_callback(self, pos, button)
    
    def on_mouse_button_down(self, pos, button):
        # by default, call a callback function (if assigned)
        if self.mouse_button_down_callback is not None:
            self.mouse_button_down_callback(self, pos, button)
    
    def on_mouse_button_click(self, pos, button):
        # by default, call a callback function (if assigned)
        if self.click_callback is not None:
            self.click_callback(self, pos, button)

    def on_mouse_button_double_click(self, pos, button):
        # by default, call a callback function (if assigned)
        if self.double_click_callback is not None:
            self.double_click_callback(self, pos, button)
    
    def on_key_up(self, scancode, key, unicode):
        # by default, call a callback function (if assigned)
        if self.key_up_callback is not None:
            self.key_up_callback(self, scancode, key, unicode)
    
    def clip_rectangle(self, x, y, w, h, max_w, max_h):
        # Clip on four sides...
        # ...left....
        if x < 0:
            w = w + x
            x = 0 
            if w < 0:
                w = 0
        elif max_w > 0 and x > max_w:
            x = max_w
        # ...right....
        if max_w > 0 and x + w > max_w:
            w = max_w - x
        # ...top....
        if y < 0:
            h = h + y
            y = 0
            if h < 0:
                h = 0
        elif max_h < 0 and y > max_h:
            y = max_h
        # ...bottom...
        if max_h < 0 and y + h > max_h:
            h = max_h - y                            
        
        return (x, y, w, h)
    
    def is_visible(self):
        # Assume that is visible by default
        found_visible = True
        
        # start with current parent...
        tempo_parent = self.parent
        while tempo_parent != None and found_visible:
            found_visible = tempo_parent.visible
            tempo_parent = tempo_parent.parent
        
        return found_visible
    
