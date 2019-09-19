
import sys
import pygame

from .screen_element import *

class ScreenLabel(ScreenElement):
    def __init__(self, name, text, size, max_width = 0, centered = 1):
        ScreenElement.__init__(self, name)
        
        #set label properties
        self.text_size = size
        self.max_width = max_width
        self.centered = centered
        
        #default color...
        self.color = (255,255,255)
        self.background = (0, 0, 0)
        
        #set the text....
        self.set_text(text)

    def set_text(self, new_text):
        self.text = new_text
        
        #first, create a font to render the message
        font_label = pygame.font.Font(None, self.text_size)
        
        if self.max_width == 0:
            #no limit in text length to render...
            self.rendered = font_label.render(self.text, 1, self.color, self.background)
            
            text_rect = self.rendered.get_rect()
            self.width = text_rect.width
            self.height = text_rect.height
        else:
            #width limited...
            #do some line splitting (if possible)....
            text_parts = []
            parts_heights = []
            parts_widths = []
            remaining = self.text
            while len(remaining) > 0:
                #calculate best splitting...
                #find next space...
                current_space = 0
                current_words = 0
                best_split = None
                
                split_found = False 
                while not split_found:
                    #check for next space...
                    while current_space < len(remaining) and remaining[current_space] != ' ' and remaining[current_space] != '\n':
                        current_space += 1

                    stopped_at_EOL = current_space < len(remaining) and remaining[current_space] == '\n'

                    #check length until current position...
                    current_size = font_label.size(remaining[0:current_space])
                    
                    if current_size[0] < self.max_width:
                        current_words += 1
                        best_split = current_space
                        best_width = current_size[0]
                        best_height = current_size[1]
                        
                        current_space += 1

                    if current_size[0] >= self.max_width or current_space >= len(remaining) or stopped_at_EOL:
                        #limit reached, check ...
                        if current_words > 0:
                            #normal split...
                            text_parts.append(remaining[0:best_split])
                            parts_widths.append( best_width )
                            parts_heights.append( best_height )
                        else:
                            #no complete words??, find the best position without spaces...
                            #use bin search...                            
                            min_pos = 0                            
                            max_pos = current_space
                            
                            while max_pos > min_pos:
                                mid = int((min_pos + max_pos ) / 2 )
                                                             
                                current_size = font_label.size(remaining[0:mid])
                                
                                if current_size[0] <= self.max_width:
                                    min_pos = mid + 1
                                else:
                                    max_pos = mid
                                    
                            if max_pos > 1:
                                current_size = font_label.size(remaining[0:(max_pos - 1)])
                                
                                text_parts.append(remaining[0:(max_pos - 1)])
                                                            
                                best_split = max_pos - 2
                            else:
                                #special case with only 1 char!
                                current_size = font_label.size(remaining[0])
                                text_parts.append(remaining[0])
                                best_split = 0
                                
                            parts_widths.append( current_size[0] )
                            parts_heights.append( current_size[1] )

                        split_found = True
                        
                remaining = remaining[(best_split + 1):] 
            
            #now, render all parts and assemble them into a single surface...
            #...first, get total height....
            total_height = sum( parts_heights )
            self.rendered = pygame.Surface( ( self.max_width, total_height) )
            self.rendered = self.rendered.convert()
            self.rendered.fill( self.background )
            
            #... render all parts...
            y_offset = 0
            for index, part in enumerate(text_parts):
                #... render current part...
                tempo_rendered = font_label.render( part, 1, self.color, self.background)
                
                #... combine it with final surface...
                #...... check text alignment....
                if self.centered == 1:
                    x_offset = int((self.max_width - parts_widths[index]) / 2)  
                else:
                    x_offset = 0
                #...... combine ....
                self.rendered.blit( tempo_rendered, (x_offset, y_offset ) )
                
                #... prepare for next line ...
                y_offset += parts_heights[index]
                
            self.width = self.max_width
            self.height = total_height
                
        
    def set_color(self, new_color ):
        self.color = new_color
        
        self.set_text( self.text)
        
    def set_background(self, new_background):
        self.background = new_background
        
        self.set_text( self.text )
        
    def render(self, background, off_x = 0, off_y = 0):
        #test with text...
        background.blit( self.rendered, (self.position[0] + off_x, self.position[1] + off_y ) )