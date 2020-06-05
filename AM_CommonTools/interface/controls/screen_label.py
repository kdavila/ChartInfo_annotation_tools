
import sys
import pygame

from .screen_element import *

class ScreenLabel(ScreenElement):
    def __init__(self, name, text, size, max_width = 0, centered = 1):
        ScreenElement.__init__(self, name)
        
        # set label properties
        self.text_size = size
        self.max_width = max_width
        self.centered = centered
        
        # default color...
        self.color = (255,255,255)
        self.background = (0, 0, 0)

        # render info ...
        self.rendered = None
        self.render_starts = None
        self.render_offsets_x = None
        self.render_offsets_y = None
        self.render_widths = None

        # set the text....
        self.set_text(text)

    def set_text(self, new_text):
        self.text = new_text
        
        # first, create a font to render the message
        font_label = pygame.font.Font(None, self.text_size)
        
        if self.max_width == 0:
            # no limit in text length to render...
            self.rendered = font_label.render(self.text, 1, self.color, self.background)
            
            text_rect = self.rendered.get_rect()
            self.width = text_rect.width
            self.height = text_rect.height

            self.render_starts = [0]
            self.render_offsets_x = [0]
            self.render_offsets_y = [0]
            self.render_widths = [text_rect.width]
        else:
            # width limited...
            # do some line splitting (if possible)....
            text_parts = []
            parts_heights = []
            parts_widths = []
            remaining = self.text
            self.render_starts = []
            self.render_offsets_x = []
            self.render_offsets_y = []
            self.render_widths = []
            while len(remaining) > 0:
                # calculate best splitting...
                # find next space...
                current_space = 0
                current_words = 0
                best_split = None
                
                split_found = False 
                while not split_found:
                    # check for next space...
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
                        # limit reached, check ...
                        if current_words > 0:
                            # normal split...
                            text_parts.append(remaining[0:best_split])
                            parts_widths.append(best_width)
                            parts_heights.append(best_height)
                        else:
                            # no complete words??, find the best position without spaces...
                            # use bin search...
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

                self.render_starts.append(len(self.text) - len(remaining))
                remaining = remaining[(best_split + 1):] 
            
            # now, render all parts and assemble them into a single surface...
            # ...first, get total height....
            total_height = sum(parts_heights)
            self.rendered = pygame.Surface( ( self.max_width, total_height) )
            self.rendered = self.rendered.convert()
            self.rendered.fill( self.background )
            
            # ... render all parts...
            y_offset = 0
            for index, part in enumerate(text_parts):
                # ... render current part...
                tempo_rendered = font_label.render(part, 1, self.color, self.background)
                
                # ... combine it with final surface...
                # ...... check text alignment....
                if self.centered == 1:
                    x_offset = int((self.max_width - parts_widths[index]) / 2)  
                else:
                    x_offset = 0
                # ...... combine ....
                self.rendered.blit(tempo_rendered, (x_offset, y_offset))

                self.render_offsets_x.append(x_offset)
                self.render_offsets_y.append(y_offset)
                self.render_widths.append(parts_widths[index])

                # ... prepare for next line ...
                y_offset += parts_heights[index]
                
            self.width = self.max_width
            self.height = total_height

        # print(self.render_starts)
        # print(self.render_offsets_x)
        # print(self.render_offsets_y)
        # print(self.render_widths)

    def get_character_line_column(self, offset):
        if offset < 0:
            offset = 0
        if offset > len(self.text):
            offset = len(self.text)

        if len(self.render_starts) == 0:
            return 0, 0

        # start checking from the first line
        character_line = 0
        # if we are not on the last line and
        #    the requested position is larger than or equal to the start of the next line
        while character_line + 1 < len(self.render_starts) and offset >= self.render_starts[character_line + 1]:
            # move to the next line ...
            character_line += 1

        column = offset - self.render_starts[character_line]

        return character_line, column

    def line_column_to_offset(self, line, column):
        if len(self.render_starts) == 0 or line < 0:
            return 0

        if line >= len(self.render_starts):
            return len(self.text)

        # if it makes it here ... the line is valid ...
        base_offset = self.render_starts[line]

        # check line length ...
        if line + 1 < len(self.render_starts):
            line_length = self.render_starts[line + 1] - self.render_starts[line]
        else:
            line_length = len(self.text) - self.render_starts[line]

        # and validate column ...
        if column >= line_length:
            column = line_length - 1

        if column <= 0:
            return base_offset
        else:
            return base_offset + column

    def get_character_visual_position(self, offset):
        font_label = pygame.font.Font(None, self.text_size)

        if len(self.text) == 0:
            # special case, empty text ...
            y_offset = 0
            # ...... check text alignment....
            if self.centered == 1:
                x_offset = int(self.max_width / 2)
            else:
                x_offset = 0

            _, line_h = font_label.size("|")
        else:
            character_line, column = self.get_character_line_column(offset)

            # now ... identify length of substring ...
            substring = self.text[self.render_starts[character_line]:offset]

            line_w, line_h = font_label.size(substring)

            x_offset = self.render_offsets_x[character_line] + line_w
            y_offset = self.render_offsets_y[character_line]

            # if not the last line ...
            if character_line + 1 < len(self.render_starts):
                # use the height of the entire line
                # (not sure if this will be different than current substring height)
                line_h = self.render_offsets_y[character_line + 1] - self.render_offsets_y[character_line]

            # print((character_line, substring, x_offset, y_offset))

        return x_offset, y_offset, line_h

    def get_visual_position_closest_character(self, x_offset, y_offset):
        if len(self.render_starts) == 0 or y_offset < 0:
            return 0

        font_label = pygame.font.Font(None, self.text_size)

        # first, determine the line ...
        # start checking from the first line
        char_line = 0
        # if we are not on the last line and
        #    the requested y position is larger than or equal to the start of the next line
        while char_line + 1 < len(self.render_offsets_y) and y_offset >= self.render_offsets_y[char_line + 1]:
            # move to the next line ...
            char_line += 1

        if char_line + 1 < len(self.render_starts):
            max_col = self.render_starts[char_line + 1] - self.render_starts[char_line]
        else:
            max_col = len(self.text) - self.render_starts[char_line]

        if x_offset <= self.render_offsets_x[char_line]:
            # before the beginning
            # print("case 1")
            char_col = 0
        elif x_offset >= self.render_offsets_x[char_line] + self.render_widths[char_line]:
            # before the ending
            # print("case 2")
            char_col = max_col
        else:
            # in the middle ... test using bin search
            # print("case 3 ")

            # start_col will have the answer when end_col is equal or lower
            start_col = 0
            end_col = max_col
            while end_col - 1 > start_col:
                mid_col = int((start_col + end_col) / 2)

                # .... check length ...
                substring = self.text[self.render_starts[char_line]:self.render_starts[char_line] + mid_col]

                sub_w, sub_h = font_label.size(substring)

                if x_offset < self.render_offsets_x[char_line] + sub_w:
                    # reduce higher boundary ....
                    end_col = mid_col
                else:
                    # reduce lower boundary ....
                    start_col = mid_col

            char_col = start_col

        offset = self.render_starts[char_line] + char_col
        # print((x_offset, y_offset, char_line, char_col, offset))

        return offset

    def total_lines(self):
        return len(self.render_starts)

    def set_color(self, new_color ):
        self.color = new_color
        
        self.set_text( self.text)
        
    def set_background(self, new_background):
        self.background = new_background
        
        self.set_text( self.text )
        
    def render(self, background, off_x = 0, off_y = 0):
        # test with text...
        background.blit( self.rendered, (self.position[0] + off_x, self.position[1] + off_y ) )