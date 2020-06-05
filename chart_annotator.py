
import os
import sys
import pygame
import traceback

from AM_CommonTools.configuration.configuration import Configuration

from ChartInfo.annotation.chart_main_annotator import ChartMainAnnotator

def main():
    if len(sys.argv) < 2:
        print("Usage: python chart_annotator.py config [small/large]")
        print("Where")
        print("\tconfig\t= Configuration File")
        print("\tsize\t= Window Size (normal by default)")
        print("\t\tsmall: for smaller window")
        print("\t\tlarge: for larger window")
        print("")
        return

    config_filename = sys.argv[1]

    if not os.path.exists(config_filename):
        print("Invalid config file / path")
        return

    if os.path.isdir(config_filename):
        # chose one ...
        user_filename = input("Please enter the name of configuration file to use: ")
        config_filename = config_filename + "/" + user_filename

    config = Configuration.from_file(config_filename)

    # input/output files path
    small_mode = (len(sys.argv) >= 3) and (sys.argv[2].lower() == "small")
    large_mode = (len(sys.argv) >= 3) and (sys.argv[2].lower() == "large")

    admin_mode = config.get_bool("ENABLE_ADMIN_MODE", False)

    if admin_mode:
        print("Admin mode enable!")

    charts_dir = config.get_str("CHART_DIRECTORY")
    annotations_dir = config.get_str("CHART_ANNOTATIONS")

    pygame.init()
    pygame.display.set_caption('Chart Annotation Tool')

    if small_mode:
        # 1250, 670
        screen_w, screen_h = 1250, 820
    else:
        if large_mode:
            screen_w, screen_h = 1850, 970
        else:
            # default res....
            screen_w, screen_h = 1500, 820

    window = pygame.display.set_mode((screen_w, screen_h))
    background = pygame.Surface(window.get_size())
    background = background.convert()

    # try:
    main_menu = ChartMainAnnotator(window.get_size(), charts_dir, annotations_dir, admin_mode)
    # except Exception as e:
    #    print(e)
    #    return

    current_screen = main_menu
    current_screen.prepare_screen()

    # print("Remove this! on loading!")
    # current_screen.update_selected_image(5)
    # current_screen.update_selected_image(8)
    # current_screen.btn_annotate_click(None)

    prev_screen = None

    while not current_screen is None:
        #detect when the screen changes...
        if current_screen != prev_screen:
            #remember last screen...
            prev_screen = current_screen

        #capture events...
        current_events = pygame.event.get()
        try:
            current_screen = current_screen.handle_events(current_events)
        except Exception as e:
            print("An exception ocurred")
            print(e)
            traceback.print_exc()

        if current_screen != prev_screen:
            if current_screen != None:
                #prepare the screen for new display ...
                current_screen.prepare_screen()

        #draw....
        background.fill((0, 0, 0))

        if not current_screen is None:
            current_screen.render(background)

        window.blit(background, (0, 0))
        pygame.display.flip()


if __name__ == '__main__':
    main()
