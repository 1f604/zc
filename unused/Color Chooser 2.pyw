#Author: Ian Mallett (geometrian)
#Link: http://www.pygame.org/project/687/1217
import pygame
from pygame.locals import *
import sys, os
##if sys.platform == 'win32' or sys.platform == 'win64':
##    os.environ['SDL_VIDEO_CENTERED'] = '1'
pygame.init()

try:
    from pygame import scrap
    scrap.init()
except:
    pass

Screen = (500,400)

icon = pygame.Surface((1,1)); icon.set_alpha(0); pygame.display.set_icon(icon)
pygame.display.set_caption("Color Chooser - v.2.0.0 - Ian Mallett - 2008")
Surface = pygame.display.set_mode(Screen,RESIZABLE)

Font = pygame.font.SysFont(None,16)

def RGBToOpenGLColor(rgb_tuple):
    red = rgb_tuple[0]/255.0
    green = rgb_tuple[1]/255.0
    blue = rgb_tuple[2]/255.0
    return "("+str(red)+", "+str(green)+", "+str(blue)+")"
def RGBToHTMLColor(rgb_tuple):
    hexcolor = '#%02x%02x%02x' % rgb_tuple
    return hexcolor
class Slider(object):
    def __init__(self, value=0):
        self.pos = [0,0]
        self.bar = pygame.Surface((275,15))
        self.bar.fill((200,200,200))
        self.slider = pygame.Surface((20,15))
        self.slider.fill((230,230,230))
        pygame.draw.rect(self.bar, (0,0,0), (0,0,275,15), 1)
        pygame.draw.rect(self.slider, (0,0,0), (0,0,20,15), 1)
        self.clicked = False
        self.value = value
    def update(self):
        if (mpos[0] > (self.pos[0]+self.value)) and (mpos[0] < (self.pos[0]+self.value)+20):
            if mpos[1] > self.pos[1] and mpos[1] < self.pos[1]+15:
                if mpress[0]:
                    self.clicked = True
        if not mpress[0]:
            self.clicked = False
        if self.clicked:
            self.value += mrel[0]
        if self.value < 0: self.value = 0
        if self.value > 255: self.value = 255
    def render(self, surface, height, space, number):
        x = (Screen[0]/2)-(275/2)
        y = (3*space)+height+55+((number-1)*20)
        self.pos = (x,y)
        surface.blit(self.bar,(x,y))
        surface.blit(self.slider,(x+self.value,y))
def GetInput():
    global Screen, Surface
    global mpress, mpos, mrel, key
    key = pygame.key.get_pressed()
    mpress = pygame.mouse.get_pressed()
    mpos = pygame.mouse.get_pos()
    mrel = pygame.mouse.get_rel()
    for event in pygame.event.get():
        if event.type == QUIT or key[K_ESCAPE]:
            pygame.quit(); sys.exit()
        if event.type == VIDEORESIZE:
            Screen = (event.w,event.h)
            Surface = pygame.display.set_mode(Screen,RESIZABLE)
def Draw():
    Surface.fill((255,255,255))

    CenterX = Screen[0]/2
    CenterY = Screen[1]/2

    r,g,b=s1.value,s2.value,s3.value
    
    Width   = Screen[0]/2
    Height  = Screen[1]/3

    Space = (Screen[1]-Height-55-55)/4.0

    pygame.draw.rect(Surface,(0,0,0),(CenterX-(Width/2)-1,Space,Width+2,Height+2),1)
    pygame.draw.rect(Surface,(r,g,b),(CenterX-(Width/2),Space+1,Width,Height),0)
    
    ren1 = Font.render("RGB: (%s, %s, %s)" % (r,g,b),True,(0,0,0))
    pos1 = ((Screen[0]/2)-(ren1.get_width()/2), Height+(2*Space))
    Surface.blit(ren1, pos1)
    ren2 = Font.render("Hex: %s" % RGBToHTMLColor((r,g,b)),True,(0,0,0))
    pos2 = ((Screen[0]/2)-(ren2.get_width()/2), Height+(2*Space)+20)
    Surface.blit(ren2, pos2)
    ren3 = Font.render("OpenGL: %s" % RGBToOpenGLColor((r,g,b)),True,(0,0,0))
    pos3 = ((Screen[0]/2)-(ren3.get_width()/2), Height+(2*Space)+40)
    Surface.blit(ren3, pos3)

    if hasattr(pygame, "scrap"):
        rect1 = pygame.Rect(pos1[0], pos1[1], ren1.get_width(), ren1.get_height())
        rect2 = pygame.Rect(pos2[0], pos2[1], ren2.get_width(), ren2.get_height())
        rect3 = pygame.Rect(pos3[0], pos3[1], ren3.get_width(), ren3.get_height())
        Collision = False
        if rect1.collidepoint(mpos): Collision = True; pygame.draw.rect(Surface,(0,0,255),rect1,1); ColorText = (r,g,b)
        if rect2.collidepoint(mpos): Collision = True; pygame.draw.rect(Surface,(0,0,255),rect2,1); ColorText = RGBToHTMLColor((r,g,b))
        if rect3.collidepoint(mpos): Collision = True; pygame.draw.rect(Surface,(0,0,255),rect3,1); ColorText = RGBToOpenGLColor((r,g,b))
        if Collision:
            if ((key[K_LCTRL] or key[K_RCTRL]) and key[K_c]) or mpress[0]:
                pygame.scrap.put(SCRAP_TEXT, str(ColorText))

    s1.render(Surface,Height,Space,1)
    s2.render(Surface,Height,Space,2)
    s3.render(Surface,Height,Space,3)

    pygame.display.flip()
def main():
    global s1,s2,s3,r,g,b
    r = g = b = 155
    s1 = Slider()
    s2 = Slider()
    s3 = Slider()
    while True:
        GetInput()
        s1.update()
        s2.update()
        s3.update()
        Draw()
if __name__ == '__main__': main()
