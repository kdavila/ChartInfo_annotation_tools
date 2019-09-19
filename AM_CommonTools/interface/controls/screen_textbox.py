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
        self.highlighted_car = None
        self.highlighted_nocar = None
        self.draw_caret = None

        # create an inner label
        self.updateText(text)

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
        if move_caret_to_end:
            self.caret_position = len(self.text)
        
        # calculate max inner width for text...
        # width - padding_right - padding_left
        max_inner_width = self.width - (self.padding[1] + self.padding[3])
        
        # now, create an inner label
        self.inner_label = ScreenLabel(self.name + "__LABEL__", self.text, self.text_size, max_inner_width, 0)
        self.inner_label.position = (self.padding[3], self.padding[0])
        self.inner_label.set_color( self.text_color )
        self.inner_label.set_background( self.back_color )
        
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

        no_caret_text = self.text[:self.caret_position] + " " + self.text[self.caret_position:]
        caret_text = self.text[:self.caret_position] + "|" + self.text[self.caret_position:]
        
        # now, create the highlighted view without caret...
        self.inner_label.set_text(no_caret_text)
        self.inner_label.set_color( self.back_color )
        self.inner_label.set_background( self.text_color )
        
        self.highlighted_nocar = pygame.Surface( (self.width, self.height ) )
        self.highlighted_nocar.fill( self.text_color )
        
        # render highlighted without caret...
        self.inner_label.render( self.highlighted_nocar )
        
        # finally, create the highlighted view with caret...
        # self.inner_label.set_text(self.text + '|' )
        self.inner_label.set_text(caret_text)
        caret_height = self.inner_label.height
        
        self.highlighted_car = pygame.Surface( (self.width, self.height ) )
        self.highlighted_car.fill( self.text_color )

        # render highlighted without caret...
        self.inner_label.render(self.highlighted_car)
        
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
            #normal view            
            background.blit( self.rendered, (self.position[0] + off_x, self.position[1] + off_y ) )
            
            pygame.draw.rect( background, self.text_color, rect, border_w)
        else:
            #highlighted view...
            
            current_time = time.time()
            decimal = current_time - int(current_time)

            if int((decimal * 100) / 25) % 2 == 0 or not self.draw_caret:
                # without caret
                background.blit( self.highlighted_nocar, (self.position[0] + off_x, self.position[1] + off_y ) )
            else:
                #with caret
                background.blit( self.highlighted_car, (self.position[0] + off_x, self.position[1] + off_y ) )

            pygame.draw.rect( background, self.back_color, rect, border_w)
    
    def on_mouse_button_click(self, pos, button):
        #get focus...
        if button == 1:
            self.set_focus()
            
            
    def set_focus(self):
        #request focus from parent...
        got_focus = self.parent.set_text_focus( self )
        #set focus....
        self.is_highlighted = got_focus
            
    def lost_focus(self):
        #the writing focus has been lost!
        self.is_highlighted = False

    def on_key_up(self, scancode, key, unicode):
        if self.is_highlighted:
            if len(unicode) > 0:
                if key == 27:
                    #print "ESCAPE!"
                    self.is_highlighted = False
                elif key == 13:
                    #print "ENTER!"
                    if self.capture_EOL:
                        new_text = self.text[:self.caret_position] + "\n" + self.text[self.caret_position:]
                        self.caret_position += 1
                        self.updateText(new_text, False)
                elif key == 8:
                    #print "BACKSPACE!"
                    if self.caret_position > 0:
                        new_text = self.text[:self.caret_position - 1] + self.text[self.caret_position:]
                        self.caret_position -= 1
                        self.updateText(new_text, False)
                elif key == 9:
                    pass
                    #print "TAB!"
                else:
                    new_text = self.text[:self.caret_position] + unicode + self.text[self.caret_position:]
                    self.caret_position += 1
                    self.updateText(new_text, False)
            else:
                #print "CONTROL KEY!"
                # print((scancode, key, unicode))
                if key == 263 or key == 278:
                    # home ...
                    self.caret_position = 0
                    self.updateText(self.text, False)

                elif key == 257 or key == 279:
                    # end ....
                    self.caret_position = len(self.text)
                    self.updateText(self.text, False)

                elif key == 127 or key == 266:
                    # Delete ....
                    new_text = self.text[:self.caret_position] + self.text[self.caret_position + 1:]
                    self.updateText(new_text, False)

                elif key == 276:
                    # LEFT cursor?
                    if self.caret_position > 0:
                        self.caret_position -= 1
                        self.updateText(self.text, False)

                elif key == 275:
                    # RIGHT cursor
                    if self.caret_position < len(self.text):
                        self.caret_position += 1
                        self.updateText(self.text, False)
