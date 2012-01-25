import pygame

files =  ['menu.xm', 'egyptian-trance.xm']
niters = 25
next_track = 0

def play_music(path):
    pygame.mixer.music.load(path)
    pygame.mixer.music.play(-1)
    print "Playing", path

pygame.mixer.init(44100, -16, 2, 4096)

try:
    for i in range(niters):
        next_track = (next_track + 1) % 2
        play_music(files[next_track])
        pygame.time.delay(4000)
    pygame.time.delay(20000)
finally:
    pygame.mixer.quit()
    pygame.quit()

