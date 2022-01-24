
import sys
import os
from os import path

current_dir = path.dirname(path.abspath(__file__))
while path.split(current_dir)[-1] != r'Heron':
    current_dir = path.dirname(current_dir)
sys.path.insert(0, path.dirname(current_dir))

import threading
import pygame
from Heron import general_utils as gu, constants as ct
from Heron.communication.socket_for_serialization import Socket

pg_thread_running = False
resources_path = path.join(current_dir, 'Operations', 'Sinks', 'Transfer_Learning', 'TL_Task2_Screens')
monitors: str
sprites: dict
rotation: bool
opacity: int
screen_colour: int
main_screen_x_size = 2561 + 1280
sprite_screens_x_size = 1980


def initialise(_worker_object):
    global monitors
    global rotation
    global opacity
    global pg_thread_running
    print('PYGAME')
    try:
        parameters = _worker_object.parameters
        monitors = parameters[0]
        rotation = parameters[1]
        opacity = parameters[2]
    except Exception as e:
        print(e)
        return False

    screen_x = main_screen_x_size
    screen_y = 0
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (screen_x, screen_y)
    pg_thread = threading.Thread(group=None, target=pygame_thread)
    pg_thread.start()

    return True


class Sprite(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, image_file, flipped=False, opacity=255):
        super().__init__()
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.opacity = opacity
        self.flipped = flipped
        self.base_image = pygame.image.load(path.join(resources_path, image_file))
        self.base_rect = self.base_image.get_rect()
        self.base_rect.center = [pos_x, pos_y]
        self.image = pygame.image.load(path.join(resources_path, image_file))
        if flipped:
            self.base_image = pygame.transform.flip(self.base_image, True, False)
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.rect.center = [pos_x, pos_y]

        self.image = self.image.convert_alpha()
        self.base_image = self.base_image.convert_alpha()
        self.image.set_alpha(opacity)
        self.base_image.set_alpha(opacity)

    def rotate(self, angle):
        if self.flipped:
            self.image = pygame.transform.rotate(self.base_image, -angle)
        else:
            self.image = pygame.transform.rotate(self.base_image, angle)
        self.rect = self.image.get_rect(center=[self.pos_x, self.pos_y])

    def translate_x(self, position):
        self.pos_x = position
        self.rect.center = [self.pos_x, self.pos_y]

    def draw(self, screen):
        screen.blit(self.image, self.rect)


def pygame_thread():
    global pg_thread_running
    global monitors
    global sprites
    global rotation
    global screen_colour
    global opacity

    #Init and background
    pygame.init()
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((2 * sprite_screens_x_size, 1080))

    #Sprites
    sprite_y_pos = 600
    sprite_x_pos = 600
    manipulandum_file_name = 'Manipulandum_S.png'
    if rotation:
        target_file_name = 'Target_S.png'
        trap_file_name = 'Trap_S.png'
    else:
        target_file_name = 'Target_Dot.png'
        trap_file_name = 'Trap_Dot.png'

    sprites = {'top manipulandum': Sprite(sprite_x_pos, sprite_y_pos, manipulandum_file_name, True),
               'left manipulandum': Sprite(sprite_screens_x_size + sprite_x_pos + 200, sprite_y_pos,
                                           manipulandum_file_name),
               'top target': Sprite(sprite_x_pos, sprite_y_pos, target_file_name, True, opacity),
               'left target': Sprite(sprite_screens_x_size + sprite_x_pos + 200, sprite_y_pos, target_file_name, False,
                                     opacity),
               'top trap': Sprite(sprite_x_pos, sprite_y_pos, trap_file_name, True, opacity),
               'left trap': Sprite(sprite_screens_x_size + sprite_x_pos + 200, sprite_y_pos, trap_file_name, False,
                                   opacity)
               }

    sprites_group = pygame.sprite.Group()
    if rotation:
        if monitors == 'Top':
            sprites_group.add(sprites['top target'])
            sprites_group.add(sprites['top trap'])
            sprites['top trap'].rotate(-90)
            sprites_group.add(sprites['top manipulandum'])
            sprites['top manipulandum'].rotate(-45)
        if monitors == 'Left':
            sprites_group.add(sprites['left target'])
            sprites_group.add(sprites['left trap'])
            sprites['left trap'].rotate(-90)
            sprites_group.add(sprites['left manipulandum'])
            sprites['left manipulandum'].rotate(-45)
        if monitors == 'Both':
            sprites_group.add(sprites['top target'])
            sprites_group.add(sprites['top trap'])
            sprites['top trap'].rotate(-90)
            sprites_group.add(sprites['left target'])
            sprites_group.add(sprites['left trap'])
            sprites['left trap'].rotate(-90)
            sprites_group.add(sprites['top manipulandum'])
            sprites['top manipulandum'].rotate(-45)
            sprites_group.add(sprites['left manipulandum'])
            sprites['left manipulandum'].rotate(-45)
    else:
        if monitors == 'Top':
            sprites_group.add(sprites['top target'])
            sprites_group.add(sprites['top trap'])
            sprites['top trap'].translate_x(sprite_screens_x_size + 50)
            sprites_group.add(sprites['top manipulandum'])
            sprites['top manipulandum'].translate_x(sprite_screens_x_size + 300)
        if monitors == 'Left':
            sprites_group.add(sprites['left target'])
            sprites_group.add(sprites['left trap'])
            sprites['left trap'].translate_x(50)
            sprites_group.add(sprites['left manipulandum'])
            sprites['left manipulandum'].translate_x(300)
        if monitors == 'Both':
            sprites_group.add(sprites['top target'])
            sprites_group.add(sprites['top trap'])
            sprites['top trap'].translate_x(sprite_screens_x_size + 50)
            sprites_group.add(sprites['left target'])
            sprites_group.add(sprites['left trap'])
            sprites['left trap'].translate_x(50)
            sprites_group.add(sprites['top manipulandum'])
            sprites['top manipulandum'].translate_x(sprite_screens_x_size + 300)
            sprites_group.add(sprites['left manipulandum'])
            sprites['left manipulandum'].translate_x(300)

    pg_thread_running = True

    while pg_thread_running:
        pygame.event.pump()  # I am not doing anything with events but a call to the event queue must be done
                             # otherwise pygame freezes

        try:
            screen.fill([screen_colour, 0, 0, 0.5])

            if show_sprites:
                sprites_group.draw(screen)
            else:
                pass
                #sprites_group.clear(screen, background)

            pygame.display.update()
            clock.tick(5)
        except:
            pass

    pygame.quit()


def update_output(data, parameters):
    global sprites
    global show_sprites
    global sprites_to_hide_in_ms
    global screen_colour

    topic = data[0].decode('utf-8')
    message = Socket.reconstruct_array_from_bytes_message(data[1:])

    if len(message) == 4:

        screen_colour = 255

        if rotation:
            angle_man, angle_target, angle_trap = int(message[1]), int(message[2]), int(message[3])
            try:
                for man_keys in sprites:
                    if 'manipulandum' in man_keys:
                        sprites[man_keys].rotate(angle_man)
                    if 'target' in man_keys:
                        sprites[man_keys].rotate(angle_target)
                    if 'trap' in man_keys:
                        sprites[man_keys].rotate(angle_trap)
            except NameError:
                pass
        else:
            try:
                for man_keys in sprites:
                    trans_man = int(-1200 / 90 * message[1]) + 50
                    trans_target = int(-1200 / 90 * message[2]) + 50
                    trans_trap = int(-1200 / 90 * message[3]) + 50
                    if 'top' in man_keys:
                        trans_man += sprite_screens_x_size
                        trans_target += sprite_screens_x_size
                        trans_trap += sprite_screens_x_size
                    if 'manipulandum' in man_keys:
                        sprites[man_keys].translate_x(trans_man)
                    if 'target' in man_keys:
                        sprites[man_keys].translate_x(trans_target)
                    if 'trap' in man_keys:
                        sprites[man_keys].translate_x(trans_trap)
            except NameError:
                pass
        show_sprites = True
    elif len(message) == 1:
        if message[0]:
            screen_colour = 255
        else:
            screen_colour = 0
        show_sprites = False


def on_end_of_life():
    global pg_thread_running

    pg_thread_running = False


if __name__ == "__main__":
    worker_object = gu.start_the_sink_worker_process(work_function=update_output,
                                                     end_of_life_function=on_end_of_life,
                                                     initialisation_function=initialise)
    worker_object.start_ioloop()
