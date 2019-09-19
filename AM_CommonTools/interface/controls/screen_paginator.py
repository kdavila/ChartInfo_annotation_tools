import math
from .screen_element import *
from .screen_container import *
from .screen_button import *

class ScreenPaginator(ScreenElement):
    def __init__(self, name, text_size, p_size, e_count, max_width, height = 0, text_color = None, back_color = None ):
        ScreenElement.__init__(self, name)
                
        #copy propierties...
        self.text_size = text_size
        self.max_width = max_width        
        self.height = height
        self.text_color = text_color
        self.back_color = back_color
        
        #mark as control container
        self.is_container = True                    
        
        self.width = max_width        
        
        self.page_w = 35
        self.page_p = 3
        
        self.page_selected_callback = None
        
        self.current_page = -1
        self.first_page = None
        self.page_size = None
        self.element_count = None
        self.total_pages = None
        self.add_arrows = None

        self.left_arrow = None
        self.right_arrow = None
        self.container = None
        self.buttons = None

        # ... create pages...
        self.paginate(p_size, e_count)
        
    def paginate(self, p_size, e_count):    
        self.page_size = p_size
        self.element_count = e_count
        self.first_page = 0
        self.current_page = 0
        
        if self.page_size <= 0:
            self.page_size = 1
        if self.element_count < 0:
            self.element_count = 0
        
        # number of pages...
        self.total_pages = int(math.ceil( self.element_count / float(self.page_size) ))
        
        # create the buttons...
        
        # ...Arrow buttons...
        self.left_arrow = ScreenButton(self.name + "_L_btn", "<|", self.text_size, self.page_w, self.height, self.text_color, self.back_color)
        self.left_arrow.setPadding(10, 5, 10, 5)
        self.left_arrow.click_callback = self.left_arrow_click
        self.left_arrow.visible = False
        
        self.right_arrow = ScreenButton(self.name + "_R_btn", "|>", self.text_size, self.page_w, self.height, self.text_color, self.back_color)
        self.right_arrow.setPadding(10, 5, 10, 5)
        self.right_arrow.click_callback = self.right_arrow_click
        self.right_arrow.visible = False
        
        # now the container...
        # create inner container...
        self.container = ScreenContainer(self.name + "_container", (self.max_width, self.left_arrow.height + 1), back_color = (0,0,0))
        self.container.parent = self
        
        # ...add the arrows...
        self.container.append( self.left_arrow )        
        self.container.append( self.right_arrow )
        
        # page buttons
        self.buttons = []
                
        for i in range(self.total_pages):             
            btn_name = self.name + "_pg_btn_" + str(i)
            new_button = ScreenButton(btn_name, str(i + 1), self.text_size, self.page_w, self.height, self.text_color, self.back_color)
            new_button.index = i
            new_button.setPadding(10, 5, 10, 5)
            new_button.click_callback = self.page_click
            new_button.visible = False
            
            # reference in button array and control container...
            self.buttons.append( new_button )                 
            self.container.append( new_button )       
            
        self.add_arrows = (self.page_w + 3) * self.total_pages > self.max_width                    
        self.height = self.container.height
        
        self.show_pages()
    
    def show_pages(self):
                
        if self.add_arrows:
            # the left arrow
            self.left_arrow.visible = (self.first_page > 0) 
            
            # the right arrow...
            max_pages_w = self.max_width - (self.page_p * 2 + self.page_w) #assuming left arrow is shown
            curr_pages_w = (self.total_pages - self.first_page) * (self.page_w + self.page_p)
            self.right_arrow.visible = curr_pages_w > max_pages_w                                              
        else:
            # none is visible...
            self.left_arrow.visible = False
            self.right_arrow.visible = False             
            
        # if visible, set left arrow...
        if self.left_arrow.visible:
            self.left_arrow.position = (self.page_p, 0)
            current_x = self.page_w + self.page_p * 2
        else:
            self.left_arrow.position = (0, 0)
            current_x = 3
        
        # if visible, set right arrow...
        if self.right_arrow.visible:
            self.right_arrow.position = (self.max_width - self.page_w - self.page_p, 0)
            max_x = self.right_arrow.position[0] - self.page_p 
        else:
            self.right_arrow.position = (0, 0)
            max_x = self.max_width - self.page_p
        
        # now, display pages...
        curr_page = self.first_page
        while current_x + self.page_w < max_x and curr_page < self.total_pages:
            self.buttons[curr_page].visible = True
            self.buttons[curr_page].position = (current_x, 0)
            
            curr_page += 1
            current_x += self.page_w + self.page_p
        
        # the remaining must be hidden...
        for i in range(self.total_pages):
            if i < self.first_page or i >= curr_page:
                self.buttons[i].visible = False
                self.buttons[i].position = (0, 0)
    
    def left_arrow_click(self, button):
        self.first_page -= 1
        self.show_pages()
    
    def right_arrow_click(self, button):
        self.first_page += 1
        self.show_pages()
        
    def set_first_page(self, page_idx):
        if page_idx >= 0 and page_idx < self.total_pages:
            self.first_page = page_idx
            self.show_pages()
            
    def set_current_page(self, page_idx):
        if page_idx < 0:
            self.current_page = 0
        elif page_idx >= self.total_pages:
            self.current_page = self.total_pages - 1
        else:
            self.current_page = page_idx
    
    def page_click(self, button):
        if self.page_selected_callback != None:
            self.current_page = button.index
            self.page_selected_callback(self, button.index)
        
    def render(self, background, off_x = 0, off_y = 0):
        self.container.render( background, off_x + self.position[0], off_y + self.position[1] )    
    
    def handle_event(self, event):
        if not self.visible:
            #not visible equal not event handling...
            return
        
        #print event
        
        #from recursive event handling..., just pass event info to child container
        self.container.handle_event(event)
         