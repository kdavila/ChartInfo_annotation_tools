
import time
from .screen_element import *
from .screen_horizontal_scroll import *
from .screen_vertical_scroll import *

class ScreenContainer(ScreenElement):
    def __init__(self, name, size, back_color = (0,0,0)):
        ScreenElement.__init__(self, name)
        
        self.size = size
        self.width = size[0]
        self.height = size[1]
                
        self.right_padding = 20
        self.bottom_padding = 20
        self.inner_width = self.right_padding
        self.inner_height = self.bottom_padding
        
        # Scroll Bars
        # ....vertical....
        self.v_scroll = ScreenVerticalScroll( name + "_cont_vscroll", 0, 100, 0, 20)
        self.v_scroll.position = (self.position[0] + self.width - 16, self.position[1])
        self.v_scroll.height = self.height - 17
        self.v_scroll.scroll_callback = self.v_scroll_changed
        # ....horizontal....
        self.h_scroll = ScreenHorizontalScroll( name + "_cont_hscroll", 0, 100, 0, 20)
        self.h_scroll.position = (self.position[0], self.position[1] + self.height - 16)
        self.h_scroll.width = self.width - 17
        self.h_scroll.scroll_callback = self.h_scroll_changed
        
        # by default is visible
        self.visible = True
        # mark as control container
        self.is_container = True
        
        self.back_color = back_color
        
        # elements contained....
        self.elements = []
        
        # for event handling
        self.last_mouse_down_pos = { }
        self.last_mouse_focus = None
        self.last_mouse_click_time = {}
        
        self.v_offset = 0
        self.h_offset = 0
        self.v_scroll.active = False
        self.h_scroll.active = False        
        
        self.container_buffer = pygame.Surface( self.size )
        
        self.text_focus = None
        
    def set_text_focus(self, focus_reference):
        if self.parent is None:
            # the case of the root container...
            if self.text_focus is not None:
                self.text_focus.lost_focus()
            
            self.text_focus = focus_reference
            
            return True
        else:
            # intermediate container, past request to parent...
            return self.parent.set_text_focus( focus_reference )

        
    def v_scroll_changed(self, scroll):
        pass
    
    def h_scroll_changed(self, scroll):
        pass
        
    def append(self, new_element):
        # add to elements...
        self.elements.append(new_element)
        # tell element who is its new parent
        new_element.parent = self
        # now, recalculate the size...
        self.recalculate_size()
        
    def clear(self):
        # Will erase all elements in the container (make it like brand new...)
        # elements contained....
        del self.elements[:]
        
        # for event handling
        self.last_mouse_down_pos.clear()
        
        self.v_offset = 0
        self.h_offset = 0
        self.v_scroll.active = False
        self.h_scroll.active = False
        
        self.inner_width = self.right_padding
        self.inner_height = self.bottom_padding
                                
        
    def recalculate_size(self):
        max_x = max_y = 0
        for element in self.elements:
            # ...max...
            # ...X...
            if element.position[0] + element.width > max_x:
                max_x = element.position[0] + element.width
            # ...y...
            if element.position[1] + element.height > max_y:
                max_y = element.position[1] + element.height
        
        self.inner_width = max_x + self.right_padding
        self.inner_height = max_y + self.bottom_padding
        
        # adjusting scroll bars...
        self.v_scroll.active = max_y > self.height 
        self.v_scroll.value = 0
        self.h_scroll.active = max_x > self.width        
        self.h_scroll.value = 0
        
        # the limits...
        if self.v_scroll.active:
            self.v_scroll.max = self.inner_height - self.height
        if self.h_scroll.active:
            self.h_scroll.max = self.inner_width - self.width
            
    def handle_event(self, event):
        if not self.visible:
            # not visible equal not event handling...
            return
        
        # check scroll bars...
        # ....vertical.....
        if self.v_scroll.active:
            v_handled = self.list_handle_event( [ self.v_scroll ], event, 0, 0, False, False)
            off_y = self.v_scroll.value
        else:
            v_handled = False
            off_y = 0
        # ....horizontal...
        if self.h_scroll.active:
            h_handled = self.list_handle_event( [ self.h_scroll ], event, 0, 0, False, False)
            off_x = self.h_scroll.value
        else:
            h_handled = False
            off_x = 0 
            
        # the rest of elements...
        if not v_handled and not h_handled:
            self.list_handle_event(self.elements, event, off_x, off_y, True, True)
        
    def list_handle_event(self, element_list, event, off_x, off_y, scrolling, key_input):
        handled = False
                        
        if event.type == pygame.MOUSEMOTION:            
            # With scrolling, mouse position becomes relative...
            rel_x = event.pos[0] + off_x
            rel_y = event.pos[1] + off_y
            rel_pos = (rel_x, rel_y)                        
                
            # get states....
            # ... previous...
            prev_state = self.element_at_xy( element_list, rel_x - event.rel[0], rel_y - event.rel[1])
            curr_state = self.element_at_xy( element_list, rel_x, rel_y )
            
            # now, report events to elements...
            for i in range(len(element_list)):
                if not element_list[i].visible:
                    # skip this element since it is not visible
                    continue
                
                if element_list[i].is_container:
                    # process event recursively (subcontainer)
                    if curr_state[i] == 1 or prev_state[i] == 1:
                        # if mouse is or was inside this container, handle recursively
                        original_pos = event.pos
                        event.pos = (rel_x - element_list[i].position[0], rel_y - element_list[i].position[1])                        
                        element_list[i].handle_event(event)
                        event.pos = original_pos
                else:
                    # process event...
                    if prev_state[i] == 1:
                        if curr_state[i] == 1:
                            # still inside, mouse motion...
                            element_list[i].on_mouse_motion(rel_pos, event.rel, event.buttons)
                            handled = True
                        else:
                            # was inside, now it is not, it left!
                            element_list[i].on_mouse_leave(rel_pos, event.rel, event.buttons)
                            # check for focus...
                            if self.last_mouse_focus == element_list[i]:
                                self.last_mouse_focus = None                             
                            handled = True
                    else:
                        if curr_state[i] == 1:
                            # it just got inside...
                            element_list[i].on_mouse_enter(rel_pos, event.rel, event.buttons)
                            # check for focus...
                            if self.last_mouse_focus != None and \
                               self.last_mouse_focus != element_list[i]:
                                self.last_mouse_focus.on_mouse_leave(rel_pos, event.rel, event.buttons)
                            self.last_mouse_focus = element_list[i] 
                                
                            handled = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            # With scrolling, mouse position becomes relative...
            rel_x = event.pos[0] + off_x
            rel_y = event.pos[1] + off_y
            rel_pos = (rel_x, rel_y)
            # check affected elements...
            curr_state = self.element_at_xy( element_list, rel_x, rel_y )
            # now report...
            recursions = False
            
            for i in range(len(element_list)):
                if not element_list[i].visible:
                    # skip this element since it is not visible
                    continue
                                
                if curr_state[i] == 1:
                    if element_list[i].is_container:
                        # handle it recursively...
                        original_pos = event.pos
                        event.pos = (rel_x - element_list[i].position[0], rel_y - element_list[i].position[1])
                        element_list[i].handle_event(event)
                        event.pos = original_pos           
                        recursions = True
                                                             
                    else:
                        # handle event normally...
                        element_list[i].on_mouse_button_down( rel_pos, event.button )
                        handled = True
                    
            # handle vertical scroll bar with mouse scrolling
            if self.v_scroll.active and not recursions and scrolling:
                if event.button == 4:
                    # Scroll-UP
                    self.v_scroll.apply_step(-1)
                elif event.button == 5:
                    # Scroll-Down
                    self.v_scroll.apply_step(1)
            
            # store position....
            self.last_mouse_down_pos[ str(event.button) ] = rel_pos
            
        elif event.type == pygame.MOUSEBUTTONUP:
            # With scrolling, mouse position becomes relative...
            rel_x = event.pos[0] + off_x
            rel_y = event.pos[1] + off_y
            rel_pos = (rel_x, rel_y)
            # check affected elements...
            curr_state = self.element_at_xy( element_list, rel_x, rel_y )
            # check elements where current button was pushed...
            
            if str(event.button) in self.last_mouse_down_pos:
                last_pos = self.last_mouse_down_pos[ str(event.button) ]
            else:
                # special case when button was pressed on a different container and released over this one...
                last_pos = (-1, -1)
                
            prev_state = self.element_at_xy( element_list,  last_pos[0] , last_pos[1] )

            current_time = time.time()
            click_registered = False
            double_click_registered = False
            # now, for every element...
            for i in range(len(element_list)):
                if not element_list[i].visible:
                    # skip this element since it is not visible
                    continue
                
                if curr_state[i] == 1:
                    if element_list[i].is_container:
                        # handle it recursively...
                        original_pos = event.pos
                        event.pos = (rel_x - element_list[i].position[0], rel_y - element_list[i].position[1])
                        element_list[i].handle_event(event)
                        event.pos = original_pos
                    else:
                        # handle it normaly...
                        
                        # report mouse up....
                        element_list[i].on_mouse_button_up( rel_pos, event.button )
                        handled = True
                        
                        # check if full click... (only left, middle, right click and double-click )
                        if prev_state[i] == 1 and event.button <= 3:
                            element_list[i].on_mouse_button_click( rel_pos, event.button )
                            click_registered = True
                            handled = True


                            if event.button in self.last_mouse_click_time and self.last_mouse_click_time[event.button] is not None:
                                delta = current_time - self.last_mouse_click_time[event.button]
                                # double click delta ...
                                if delta < 0.35:
                                    double_click_registered = True
                                    element_list[i].on_mouse_button_double_click(rel_pos, event.button)

            if click_registered:
                if double_click_registered:
                    self.last_mouse_click_time[event.button] = None
                else:
                    self.last_mouse_click_time[event.button] = current_time



        elif event.type == pygame.KEYDOWN and key_input:

            if self.text_focus is not None and self.text_focus.visible:
                # call it on child which has the focus and is visible ...
                self.text_focus.on_key_up(event.scancode, event.key, event.unicode)
            elif self.key_up_callback is not None:
                # call it itself since a call back has been stablished
                self.key_up_callback(event.scancode, event.key, event.unicode)

        else:
            # print event
            pass
        
        return handled
                            
    def element_at_xy(self, element_list, x, y):
        states = []
        for element in element_list:
            if element.position[0] <= x and element.position[1] <= y and \
               x <= element.position[0] + element.width and y <= element.position[1] + element.height and \
               element.visible:
                states.append( 1 )
            else:
                states.append( 0 )
        
        return states
    
    def render(self, background, off_x = 0, off_y = 0):
        if not self.visible:
            # not visible equal not rendering
            return
                                
        # clean buffer...
        self.container_buffer.fill( self.back_color )
        
        # Draw all inner elements using local offset
        if self.h_scroll.active or self.v_scroll.active:
            # draw only elements on current area...
            
            for element in self.elements:
                if element.position[0] - self.h_scroll.value < self.width and \
                   element.position[1] - self.v_scroll.value < self.height and \
                   element.position[0] - self.h_scroll.value + element.width > 0 and \
                   element.position[1] - self.v_scroll.value + element.height > 0 and \
                   element.visible:
                    element.render(self.container_buffer, -self.h_scroll.value, -self.v_scroll.value)
        else:
            # simple case, no test for clipping performed...
            for element in self.elements:
                # Draw on local surface....
                if element.visible:            
                    element.render(self.container_buffer, 0, 0)
            
        # Draw the scroll bars on absolute position at local buffer
        if self.v_scroll.active:
            self.v_scroll.render(self.container_buffer, 0, 0)
        if self.h_scroll.active:
            self.h_scroll.render(self.container_buffer, 0, 0)
            
        # draw the container buffer on top of parent background at relative position
        background.blit( self.container_buffer, (self.position[0] + off_x, self.position[1] + off_y ) )
    