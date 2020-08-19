import pygame
import os
import logging
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
            font = pygame.font.SysFont("Corbel", 40)
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
        self.logger = logging.getLogger("Discord_Bot_Logger")
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
        self.color_orange = pygame.Color("orange")
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
        self.tick_rate = 10
        # set witdh and height
        self.SW = self.screen.get_width()
        self.SH = self.screen.get_height()

        self.background_color = self.color_black
        self.image_path = "/run/media/space/SD CARD/Bilderrahmen/"
        self.margin = 10
        self.current_image_i = 0

        # load images
        self.images = os.listdir(self.image_path)

        # buttons
        self.quit_button_dimension = (150, 30)
        self.quit_button_location = (int(self.SW / 2 - self.quit_button_dimension[0] / 2),
                                     int(self.SH - self.quit_button_dimension[1] - self.margin))
        self.quit_button = Button(self.color_orange, self.quit_button_location[0], self.quit_button_location[1],
                                  self.quit_button_dimension[0], self.quit_button_dimension[1], "Quit")

        self.back_button_dimension = (150, 30)
        self.back_button_location = (int(self.SW / 2 - self.back_button_dimension[0] - self.quit_button_dimension[0] /
                                         2 - self.margin), int(self.SH - self.back_button_dimension[1] - self.margin))
        self.back_button = Button(self.color_white, self.back_button_location[0], self.back_button_location[1],
                                  self.back_button_dimension[0], self.back_button_dimension[1], "<<")

        self.forward_button_dimension = (150, 30)
        self.forward_button_location = (int(self.SW / 2 - self.forward_button_dimension[0] +
                                            self.quit_button_dimension[0] / 2 + self.quit_button_dimension[0] +
                                            self.margin), int(self.SH - self.forward_button_dimension[1] - self.margin))
        self.forward_button = Button(self.color_white, self.forward_button_location[0], self.forward_button_location[1],
                                     self.forward_button_dimension[0], self.forward_button_dimension[1], ">>")

        self.rotate_button_dimension = (50, 30)
        self.rotate_button_location = (int(self.forward_button_location[0] + self.forward_button_dimension[0] +
                                           self.margin), int(self.SH - self.rotate_button_dimension[1] - self.margin))
        self.rotate_button = Button(self.color_white, self.rotate_button_location[0], self.rotate_button_location[1],
                                    self.rotate_button_dimension[0], self.rotate_button_dimension[1], "90°")

        # run
        self.draw_update(self.images[self.current_image_i])
        try:
            self.main()
        except pygame.error as error:
            self.logger.warning(error)

    def draw_update(self, image, image_rotate=0):
        # fill screen
        self.screen.fill(self.background_color)
        # load image
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
            if picture_height > (self.SH - (self.margin * 3)):
                height_fac = (self.SH - (self.margin * 3)) / size[1]
                width_res = height_fac * size[0]
                height_res = height_fac * size[1]
                picture_width = int(width_res)
                picture_height = int(height_res)
            new_aspect_ratio = picture_width / picture_height
            if round(new_aspect_ratio, 2) != round(aspect_ratio, 2):
                self.logger.warning(f"aspect_ratio changed!!!\nold: {aspect_ratio}\nnew: {new_aspect_ratio}")

        else:
            self.logger.debug("pictures height is lager then width")
            height_fac = (self.SH - (self.margin * 3)) / size[1]
            width_res = height_fac * size[0]
            picture_width = int(width_res)
            picture_height = int(self.SH - (self.margin * 3))

        image_load = image_load.resize((picture_width, picture_height), Image.ANTIALIAS)
        # image_load = image_load.resize((width, height - (margin * 3)), Image.ANTIALIAS)
        mode = image_load.mode
        size = image_load.size
        data = image_load.tobytes()
        picture = pygame.image.fromstring(data, size, mode)
        # draw image
        image_rect = picture.get_rect()
        image_rect.center = (int(self.SW / 2), int(self.SH / 2 - self.margin * 4))
        self.screen.blit(picture, image_rect)
        # draw button
        self.back_button.draw(self.screen)
        self.forward_button.draw(self.screen)
        self.rotate_button.draw(self.screen)
        self.quit_button.draw(self.screen)
        # update
        pygame.display.update()

    def main(self):
        running = True

        while running:
            # get mouse position
            mouse = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # quit button
                    if (self.quit_button_location[0] <= mouse[0] <= self.quit_button_location[0] +
                            self.quit_button_dimension[0]
                            and
                            self.quit_button_location[1] <= mouse[1] <= self.quit_button_location[1] +
                            self.quit_button_dimension[1]):
                        pygame.quit()
                    # forward button
                    elif (self.forward_button_location[0] <= mouse[0] <= self.forward_button_location[0] +
                          self.forward_button_dimension[0]
                          and
                          self.forward_button_location[1] <= mouse[1] <= self.forward_button_location[1] +
                          self.forward_button_dimension[1]):
                        if self.current_image_i + 1 <= len(self.images) - 1:
                            self.draw_update(self.images[self.current_image_i + 1])
                            self.current_image_i += 1
                        else:
                            self.draw_update(self.images[0])
                            self.current_image_i = 0
                    # back button
                    elif (self.back_button_location[0] <= mouse[0] <= self.back_button_location[0] +
                          self.back_button_dimension[0]
                          and
                          self.back_button_location[1] <= mouse[1] <= self.back_button_location[1] +
                          self.back_button_dimension[1]):
                        if self.current_image_i - 1 >= 0:
                            self.draw_update(self.images[self.current_image_i - 1])
                            self.current_image_i -= 1
                        else:
                            self.draw_update(self.images[-1])
                            self.current_image_i = len(self.images) - 1
                    # rotate button
                    elif (self.rotate_button_location[0] <= mouse[0] <= self.rotate_button_location[0] +
                          self.rotate_button_dimension[
                              0]
                          and
                          self.rotate_button_location[1] <= mouse[1] <= self.rotate_button_location[1] +
                          self.rotate_button_dimension[
                              1]):
                        self.draw_update(self.images[self.current_image_i], image_rotate=90)
            self.screen_clock.tick(self.tick_rate)
            fps_counter = Button(self.color_yellow, self.SW - 60, 0, 60, 40,
                                 text=str(round(self.screen_clock.get_fps(), 2)))
            fps_counter.draw(self.screen)
            pygame.display.update()


image_show = ImageShow()
