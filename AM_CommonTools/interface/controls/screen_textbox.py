import pygame
import time
from .screen_element import *
from .screen_label import *

class ScreenTextbox(ScreenElement):
    
    def __init__(self, name, text, text_size, width, height = 0, text_color = None, back_color = None ):
        ScreenElement.__init__(self, name)
        
        self.max_length = max(100, len(text))
        
        self.padding = (10, 15, 10, 15)
        self.text_size = text_size
        self.width = width
        self.height = height
        self.original_height = height
        self.text = None
        self.capture_EOL = False

        self.caret_position = len(text)
        self.caret_visual_x = 0
        self.caret_visual_y = 0
        self.caret_visual_h = 0

        # check colors....
        # ...text...
        if text_color is None:
            self.text_color = (0,0,0)
        else:
            self.text_color = text_color

        # ... background...
        if back_color is None:
            self.back_color = (255, 255, 255)
        else:
            self.back_color = back_color
        
        self.is_highlighted = False

        self.rendered = None
        self.inner_label = None
        self.highlighted = None
        self.draw_caret = None

        # create an inner label
        self.updateText(text)

        self.text_typed_callback = None

    def setPadding(self, top, right, bottom, left):
        self.padding = (top, right, bottom, left)
        
        self.updateText(self.text)
        
    def set_colors(self, text_color, back_color ):
        self.text_color = text_color
        self.back_color = back_color
            
        self.updateText( self.text )

    def updateText(self, new_text, move_caret_to_end=True):
        # check text length ...
        if len(new_text) > self.max_length:
            new_text = new_text[:self.max_length]
            
        self.text = new_text

        # calculate max inner width for text...
        # width - padding_right - padding_left
        max_inner_width = self.width - (self.padding[1] + self.padding[3])
        
        # now, create an inner label
        self.inner_label = ScreenLabel(self.name + "__LABEL__", self.text, self.text_size, max_inner_width, 0)
        self.inner_label.position = (self.padding[3], self.padding[0])
        self.inner_label.set_color( self.text_color )
        self.inner_label.set_background( self.back_color )

        if move_caret_to_end:
            # self.caret_position = len(self.text)
            self.__update_caret_position(len(self.text))

        base_height = self.inner_label.height
        
        self.height = self.original_height
        min_height = self.padding[0] + self.padding[2] + self.inner_label.height
        if min_height > self.height:
            self.height = min_height
        
        # now, the label should be rendered on the background...
        self.rendered = pygame.Surface((self.width, self.height))
        self.rendered.fill(self.back_color)
        
        # create the normal view...
        self.inner_label.render(self.rendered)

        # now, create the highlighted view ...
        self.inner_label.set_color(self.back_color)
        self.inner_label.set_background(self.text_color)
        
        self.highlighted = pygame.Surface((self.width, self.height))
        self.highlighted.fill(self.text_color)
        
        # render highlighted ...
        self.inner_label.render(self.highlighted)
        
        caret_height = self.inner_label.height
        self.draw_caret = (base_height == caret_height)
        
        
    def render(self, background, off_x = 0, off_y = 0):
        #for border...
        border_w = 2
        rect_x = self.position[0] + off_x
        rect_y = self.position[1] + off_y
        rect_w = self.width
        rect_h = self.height
        rect = ( rect_x, rect_y, rect_w, rect_h ) 
        
        #draw text on the background texture...
        if not self.is_highlighted:            
            # normal view
            background.blit(self.rendered, (self.position[0] + off_x, self.position[1] + off_y))
            
            pygame.draw.rect(background, self.text_color, rect, border_w)
        else:
            #highlighted view...
            current_time = time.time()
            decimal = current_time - int(current_time)

            # draw text ...
            background.blit(self.highlighted, (self.position[0] + off_x, self.position[1] + off_y))

            if int((decimal * 100) / 25) % 2 == 0 and self.draw_caret:
                # with caret
                draw_caret_x = self.position[0] + off_x + self.inner_label.position[0] + self.caret_visual_x
                draw_caret_y = self.position[1] + off_y + self.inner_label.position[1] + self.caret_visual_y
                caret_rect = (draw_caret_x, draw_caret_y, 3, self.caret_visual_h)
                pygame.draw.rect(background, self.back_color, caret_rect, 0)

            pygame.draw.rect( background, self.back_color, rect, border_w)
    
    def on_mouse_button_click(self, pos, button):
        #get focus...
        if button == 1:
            self.set_focus()

            click_x = pos[0] - self.position[0] - self.inner_label.position[0]
            click_y = pos[1] - self.position[1] - self.inner_label.position[1]

            # first, determine the line clicked ...
            # if len(self.)
            offset = self.inner_label.get_visual_position_closest_character(click_x, click_y)

            self.__update_caret_position(offset)

    def set_focus(self):
        # request focus from parent...
        got_focus = self.parent.set_text_focus( self )
        # set focus....
        self.is_highlighted = got_focus
            
    def lost_focus(self):
        #the writing focus has been lost!
        self.is_highlighted = False

    def on_key_up(self, scancode, key, unicode):
        text_changed = False
        current_lines = self.total_lines()
        if self.is_highlighted:
            if len(unicode) > 0:
                if key == 27:
                    # "ESCAPE!"
                    self.is_highlighted = False
                elif key == 13:
                    # "ENTER!"
                    if self.capture_EOL:
                        new_text = self.text[:self.caret_position] + "\n" + self.text[self.caret_position:]
                        self.updateText(new_text, False)
                        self.__update_caret_position(self.caret_position + 1)
                        text_changed = True
                elif key == 8:
                    # "BACKSPACE!"
                    if self.caret_position > 0:
                        new_text = self.text[:self.caret_position - 1] + self.text[self.caret_position:]
                        self.updateText(new_text, False)
                        self.__update_caret_position(self.caret_position - 1)
                        text_changed = True
                elif key == 9:
                    # "TAB!"
                    pass
                else:
                    # any other non-control key?
                    new_text = self.text[:self.caret_position] + unicode + self.text[self.caret_position:]
                    self.updateText(new_text, False)
                    self.__update_caret_position(self.caret_position + 1)
                    text_changed = True
            else:
                # "CONTROL KEY!"
                # print((scancode, key, unicode))
                if key == 263 or key == 278:
                    # home ...
                    self.__update_caret_position(0)
                elif key == 257 or key == 279:
                    # end ....
                    self.__update_caret_position(len(self.text))
                elif key == 127 or key == 266:
                    # Delete ....
                    new_text = self.text[:self.caret_position] + self.text[self.caret_position + 1:]
                    self.updateText(new_text, False)
                    text_changed = True
                elif key == 276:
                    # LEFT cursor?
                    self.__update_caret_position(self.caret_position - 1)
                elif key == 275:
                    # RIGHT cursor
                    self.__update_caret_position(self.caret_position + 1)
                elif key == 273:
                    # UP cursor
                    car_line, car_column = self.inner_label.get_character_line_column(self.caret_position)
                    if car_line > 0:
                        # move a line up ..
                        new_caret_pos = self.inner_label.line_column_to_offset(car_line - 1, car_column)
                        self.__update_caret_position(new_caret_pos)
                elif key == 274:
                    # DOWN cursor
                    car_line, car_column = self.inner_label.get_character_line_column(self.caret_position)
                    if car_line + 1 < self.inner_label.total_lines():
                        # move a line down ..
                        new_caret_pos = self.inner_label.line_column_to_offset(car_line + 1, car_column)
                        self.__update_caret_position(new_caret_pos)

        # if the input key changed the contents ...
        if text_changed:
            # and there is a listener ...
            if self.text_typed_callback is not None:
                # notify!
                new_lines = self.total_lines()
                self.text_typed_callback(self, current_lines != new_lines)

    def __update_caret_position(self, new_caret_position):
        if new_caret_position < 0 or new_caret_position > len(self.text):
            # invalid new caret position ... ignore
            return

        self.caret_position = new_caret_position

        # identify the location of the caret on the text label ...
        visual_pos = self.inner_label.get_character_visual_position(self.caret_position)
        self.caret_visual_x, self.caret_visual_y, self.caret_visual_h = visual_pos

    def total_lines(self):
        return self.inner_label.total_lines()