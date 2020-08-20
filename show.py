import pygame
import os
import logging
import time
import random
import pygame_menu
from PIL import Image


class PyScope:
    screen = None

    def __init__(self, logger):
        self.logger = logger
        "Ininitializes a new pygame screen using the framebuffer"
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        disp_no = os.getenv("DISPLAY")
        if disp_no:
            self.logger.info(
                "I'm running under X display = {0}".format(disp_no))

        # Check which frame buffer drivers are available
        # Start with fbcon since directfb hangs with composite output
        drivers = ['fbcon', 'directfb', 'svgalib']
        found = False
        for driver in drivers:
            # Make sure that SDL_VIDEODRIVER is set
            if not os.getenv('SDL_VIDEODRIVER'):
                os.putenv('SDL_VIDEODRIVER', driver)
            try:
                pygame.display.init()
            except pygame.error:
                self.logger.warning(
                    'Driver: {0} failed.'.format(driver))
                continue
            found = True
            break

        if not found:
            raise Exception('No suitable video driver found!')

        size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.logger.info(
            "Framebuffer size: %d x %d" % (size[0], size[1]))
        self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN)
        # Clear the screen to start
        self.screen.fill((0, 0, 0))
        # Initialise font support
        pygame.font.init()
        # Render the screen
        pygame.display.update()

    def __del__(self):
        # Destructor to make sure pygame shuts down, etc.
        pass


class Button:
    def __init__(self, color, x, y, width, height, text=''):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

    def draw(self, win, outline=None):
        # Call this method to draw the button on the screen
        if outline:
            pygame.draw.rect(win, outline, (self.x - 2, self.y - 2, self.width + 4, self.height + 4), 0)

        pygame.draw.rect(win, self.color, (self.x, self.y, self.width, self.height), 0)

        if self.text != '':
            font = pygame.font.SysFont("Corbel", 50)
            text = font.render(self.text, 1, (0, 0, 0))
            win.blit(text, (
                self.x + (int(self.width / 2 - text.get_width() / 2)),
                self.y + (int(self.height / 2 - text.get_height() / 2))))

    def is_over(self, pos):
        # Pos is the mouse position or a tuple of (x,y) coordinates
        if self.x < pos[0] < self.x + self.width:
            if self.y < pos[1] < self.y + self.height:
                return True

        return False


class ImageShow:
    def __init__(self):
        self.logger = logging.getLogger("Show_logger")
        self.logger.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s: :%(levelname)s: %(message)s",
                                      "%Y-%m-%d %H:%M:%S")

        ch.setFormatter(formatter)

        self.logger.addHandler(ch)
        # init
        pygame.init()
        # Font
        self.Font = pygame.font.SysFont("Corbel", 35)

        # Color
        self.color_red = pygame.Color("red")
        self.color_white = pygame.Color("white")
        self.color_black = pygame.Color("black")
        self.color_grey = pygame.Color("grey")
        self.color_green = pygame.Color("green")
        self.color_yellow = pygame.Color("yellow")

        try:
            # Create an instance of the PyScope class
            scope = PyScope(self.logger)
            self.screen = scope.screen
        except Exception as error:
            self.logger.warning(f'error trying to run in frame buffer: {error}')
            self.screen = pygame.display.set_mode([1920, 1080], pygame.FULLSCREEN)
        # Clock
        self.screen_clock = pygame.time.Clock()
        self.tick_rate = 10  # fps
        self.show_fps_counter = False
        self.last_time = time.time()
        self.change_interval = 15  # change image after 15 secs

        # set witdh and height
        self.SW = self.screen.get_width()
        self.SH = self.screen.get_height()

        self.background_color = self.color_black
        self.image_path = "/run/media/space/SD CARD/Bilderrahmen/"
        self.margin = 10
        self.current_image_i = 0
        self.current_image_name = ""
        self.current_image = None

        # load images
        self.shuffel = []
        self.images = []
        self.load_images()
        self.shuffel_images()

        # buttons
        self.show_buttons = False
        self.show_buttons_ = False

        self.menu_button_dimension = (150, 50)
        self.menu_button_location = (int(self.SW / 2 - self.menu_button_dimension[0] / 2),
                                     int(self.SH - self.menu_button_dimension[1] - self.margin))
        self.menu_button = Button(self.color_green, self.menu_button_location[0], self.menu_button_location[1],
                                  self.menu_button_dimension[0], self.menu_button_dimension[1], "Menu")

        self.back_button_dimension = (150, 50)
        self.back_button_location = (int(self.SW / 2 - self.back_button_dimension[0] - self.menu_button_dimension[0] /
                                         2 - self.margin), int(self.SH - self.back_button_dimension[1] - self.margin))
        self.back_button = Button(self.color_white, self.back_button_location[0], self.back_button_location[1],
                                  self.back_button_dimension[0], self.back_button_dimension[1], "<<")

        self.forward_button_dimension = (150, 50)
        self.forward_button_location = (int(self.SW / 2 - self.forward_button_dimension[0] +
                                            self.menu_button_dimension[0] / 2 + self.menu_button_dimension[0] +
                                            self.margin), int(self.SH - self.forward_button_dimension[1] - self.margin))
        self.forward_button = Button(self.color_white, self.forward_button_location[0], self.forward_button_location[1],
                                     self.forward_button_dimension[0], self.forward_button_dimension[1], ">>")

        self.rotate_button_dimension = (60, 50)
        self.rotate_button_location = (int(self.forward_button_location[0] + self.forward_button_dimension[0] +
                                           self.margin), int(self.SH - self.rotate_button_dimension[1] - self.margin))
        self.rotate_button = Button(self.color_white, self.rotate_button_location[0], self.rotate_button_location[1],
                                    self.rotate_button_dimension[0], self.rotate_button_dimension[1], "90°")

        self.hide_button_dimension = (80, 50)
        self.hide_button_location = (int(self.back_button_location[0] - self.hide_button_dimension[0] - self.margin),
                                     int(self.SH - self.hide_button_dimension[1] - self.margin))
        self.hide_button = Button(self.color_yellow, self.hide_button_location[0], self.hide_button_location[1],
                                  self.hide_button_dimension[0], self.hide_button_dimension[1], "Hide")

        # Menu
        self.menu_background_dimension = (500, 600)
        self.menu_background_location = (int(self.SW / 2 - self.menu_background_dimension[0] / 2),
                                         int(self.SH / 2 - self.menu_background_dimension[1] / 2))
        self.menu_background = pygame.Surface(self.menu_background_dimension, pygame.SRCALPHA, 32)
        self.menu_background.fill((0, 0, 0, 200))

        self.menu = pygame_menu.Menu(width=self.menu_background_dimension[0], height=self.menu_background_dimension[1],
                                     title="Menu")
        self.menu.add_selector("Interval: ", [("5", 1), ("10", 2), ("15", 3), ("20", 4), ("25", 5), ("30", 6)],
                               default=2, onchange=None)
        self.menu.add_button('Shuffel', self.shuffel_images)
        self.menu.add_button('Close', self.disable_menu)
        self.menu.disable()

        # run
        self.draw_update(self.images[self.shuffel[self.current_image_i]])
        try:
            self.main()
        except pygame.error as error:
            self.logger.warning(error)

    def disable_menu(self):
        self.menu.disable()
        self.last_time = time.time()
        self.draw_update(self.images[self.shuffel[self.current_image_i]])

    def load_images(self):
        if self.images != os.listdir(self.image_path):
            self.logger.info("updated images from storage")
            self.images = os.listdir(self.image_path)

    def shuffel_images(self):
        numbers = []
        for i in self.images:
            numbers.append(random.randrange(0, len(self.images)))
        numbers = list(dict.fromkeys(numbers))
        range_list = range(0, len(self.images))
        for e in range_list:
            if e not in numbers:
                numbers.append(int(e))
        self.shuffel = numbers

    def draw_update(self, image, image_rotate=0, refresh_all=False):
        # fill screen
        self.screen.fill(self.background_color)
        # load image
        if self.current_image_name != image or image_rotate != 0 or refresh_all:
            image_load = Image.open(os.path.join(self.image_path, image))
            if image_rotate == 90:
                image_load = image_load.transpose(Image.ROTATE_270)
            # resize image
            size = image_load.size
            aspect_ratio = size[0] / size[1]

            if size[0] > size[1]:
                self.logger.debug("pictures width is lager then height")
                with_fac = self.SW / size[0]
                height_res = with_fac * size[1]
                picture_width = int(self.SW)
                picture_height = int(height_res)
                if picture_height > (self.SH - (self.margin * 3)) if self.show_buttons_ else picture_height > self.SH:
                    height_fac = (self.SH - (self.margin * 3)) / size[1] if self.show_buttons_ else self.SH / size[1]
                    width_res = height_fac * size[0]
                    height_res = height_fac * size[1]
                    picture_width = int(width_res)
                    picture_height = int(height_res)
                new_aspect_ratio = picture_width / picture_height
                if round(new_aspect_ratio, 2) != round(aspect_ratio, 2):
                    self.logger.warning(f"aspect_ratio changed!!!\nold: {aspect_ratio}\nnew: {new_aspect_ratio}")

            else:
                self.logger.debug("pictures height is lager then width")
                height_fac = (self.SH - (self.margin * 3)) / size[1] if self.show_buttons_ else self.SH / size[1]
                width_res = height_fac * size[0]
                picture_width = int(width_res)
                picture_height = int(self.SH - (self.margin * 3)) if self.show_buttons_ else int(self.SH)

            image_load = image_load.resize((picture_width, picture_height), Image.ANTIALIAS)
            # image_load = image_load.resize((width, height - (margin * 3)), Image.ANTIALIAS)
            mode = image_load.mode
            size = image_load.size
            data = image_load.tobytes()
            picture = pygame.image.fromstring(data, size, mode)
        else:
            picture = self.current_image
        # draw image
        image_rect = picture.get_rect()
        image_rect.center = (int(self.SW / 2), int(self.SH / 2 - self.margin * 4)) \
            if self.show_buttons_ else (int(self.SW / 2), int(self.SH / 2))
        self.screen.blit(picture, image_rect)
        self.current_image_name = image
        self.current_image = picture
        # draw button
        if self.show_buttons:
            self.back_button.draw(self.screen)
            self.forward_button.draw(self.screen)
            self.rotate_button.draw(self.screen)
            self.menu_button.draw(self.screen)
            self.hide_button.draw(self.screen)
        pygame.display.update()

    def forward(self):
        self.last_time = time.time()
        if self.current_image_i + 1 <= len(self.images) - 1:
            self.draw_update(self.images[self.shuffel[self.current_image_i + 1]])
            self.current_image_i += 1
        else:
            self.load_images()
            # TODO chnage to change evrey day
            self.shuffel_images()
            self.draw_update(self.images[self.shuffel[0]])
            self.current_image_i = 0

    def back(self):
        self.last_time = time.time()
        if self.current_image_i - 1 >= 0:
            self.draw_update(self.images[self.shuffel[self.current_image_i - 1]])
            self.current_image_i -= 1
        else:
            self.draw_update(self.images[self.shuffel[-1]])
            self.current_image_i = len(self.images) - 1

    def rotate(self):
        self.last_time = time.time()
        self.draw_update(self.images[self.shuffel[self.current_image_i]], image_rotate=90)

    def hide_buttons(self):
        self.show_buttons = not self.show_buttons
        self.draw_update(self.images[self.shuffel[self.current_image_i]], refresh_all=True)
        self.last_time = time.time()

    def main(self):
        running = True

        while running:
            # get mouse position
            mouse = pygame.mouse.get_pos()

            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    pygame.quit()
                if event.type == pygame.KEYDOWN:
                    if not self.menu.is_enabled():
                        if event.key == pygame.K_RIGHT:
                            self.forward()
                        elif event.key == pygame.K_LEFT:
                            self.back()
                        elif event.key == pygame.K_r:
                            self.rotate()
                        elif event.key == pygame.K_b:
                            self.hide_buttons()
                        elif event.key == pygame.K_f:
                            self.show_fps_counter = not self.show_fps_counter
                            self.draw_update(self.images[self.shuffel[self.current_image_i]], refresh_all=True)
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                    elif event.key == pygame.K_m:
                        if not self.menu.is_enabled():
                            self.menu.enable()
                            self.show_buttons = False
                        else:
                            self.disable_menu()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.show_buttons and not self.menu.is_enabled():
                        # Menu button
                        if (self.menu_button_location[0] <= mouse[0] <= self.menu_button_location[0] +
                                self.menu_button_dimension[0]
                                and
                                self.menu_button_location[1] <= mouse[1] <= self.menu_button_location[1] +
                                self.menu_button_dimension[1]):
                            self.menu.enable()
                            self.show_buttons = False

                        # forward button
                        elif (self.forward_button_location[0] <= mouse[0] <= self.forward_button_location[0] +
                              self.forward_button_dimension[0]
                              and
                              self.forward_button_location[1] <= mouse[1] <= self.forward_button_location[1] +
                              self.forward_button_dimension[1]):
                            self.forward()
                        # back button
                        elif (self.back_button_location[0] <= mouse[0] <= self.back_button_location[0] +
                              self.back_button_dimension[0]
                              and
                              self.back_button_location[1] <= mouse[1] <= self.back_button_location[1] +
                              self.back_button_dimension[1]):
                            self.back()
                        # rotate button
                        elif (self.rotate_button_location[0] <= mouse[0] <= self.rotate_button_location[0] +
                              self.rotate_button_dimension[
                                  0]
                              and
                              self.rotate_button_location[1] <= mouse[1] <= self.rotate_button_location[1] +
                              self.rotate_button_dimension[
                                  1]):
                            self.rotate()
                        # hide button
                        elif (self.hide_button_location[0] <= mouse[0] <= self.hide_button_location[0] +
                              self.hide_button_dimension[
                                  0]
                              and
                              self.hide_button_location[1] <= mouse[1] <= self.hide_button_location[1] +
                              self.hide_button_dimension[
                                  1]):
                            self.hide_buttons()
                        else:
                            self.hide_buttons()
                    else:
                        if not self.menu.is_enabled():
                            self.hide_buttons()
                        elif not (self.menu_background_location[0] <= mouse[0] <= self.menu_background_location[0] +
                                  self.menu_background_dimension[0]
                                  and
                                  self.menu_background_location[1] <= mouse[1] <= self.menu_background_location[1] +
                                  self.menu_background_dimension[1]):
                            self.menu.disable()
                            self.draw_update(self.images[self.shuffel[self.current_image_i]])

            # draw menu
            if self.menu.is_enabled():
                # self.screen.blit(self.menu_background, self.menu_background_location)
                self.menu.update(events)
                if self.menu.is_enabled():
                    self.menu.draw(self.screen)
                pygame.display.update()

            # tick
            self.screen_clock.tick(self.tick_rate)
            # fps counter
            if self.show_fps_counter:
                fps_counter = Button(self.color_yellow, self.SW - 100, 0, 100, 40,
                                     text=str(round(self.screen_clock.get_fps(), 2)))
                fps_counter.draw(self.screen)
                pygame.display.update()
            # loop
            if time.time() - self.last_time >= self.change_interval and not self.menu.is_enabled():
                self.last_time = time.time()
                self.forward()


image_show = ImageShow()
