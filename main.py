import pygame as pg
from pygame.locals import *
import sys, random, os

level = None

WIDTH = 800
HEIGHT = 600

def get_res_path(name):
	return os.path.join(os.path.join(os.path.split(sys.argv[0])[0], "images"), name)

def load_animation(width, filename):
	anim = pg.image.load(filename).convert_alpha()
		
	images = []
	
	for i in xrange(0, width, 50):
		image = pg.Surface((50, 50), SRCALPHA, 32)
		image.blit(anim, (0, 0), (i, 0, i+50, 50))
		images.append(image)
	
	return images

class Sprite(pg.sprite.Sprite):
	def __init__(self):
		pg.sprite.Sprite.__init__(self)
	
	def handle_event(self, event): pass
	
	def update(self, fps): pass
	
	def onCollide(self, other): pass

class PhysicsSprite(Sprite):
	def __init__(self):
		Sprite.__init__(self)
		
		self.velX = 0
		self.velY = 0
		self.onGround = False
		self.inLiquid = False
		self.speed = 1.0
		self.gravity = 1.0
	
	def onDeath(self):
		global level
		level.sprites.collide.remove(self)
	
	def update(self, fps):
		global level
		
		#Fall if the sprite is not on the ground
		if not self.onGround:
			self.velY += 1.5 * self.gravity
			
			#Maximum falling speed
			if self.velY > 40: self.velY = 40
		
		#Move by the x axis
		self.velX *= self.speed
		self.rect.move_ip(self.velX, 0)
		self.velX/= self.speed
		
		#Check for collisions by the x axis
		for other in pg.sprite.spritecollide(self, level.sprites.get_all(), False):
			if other != self: self.onCollide(other, self.velX, 0)
		
		#Move by the y axis
		self.velY *= self.speed
		self.rect.move_ip(0, self.velY)
		self.velY /= self.speed
		
		self.onGround = False
		self.inLiquid = False
		
		self.speed = 1.0
		
		#Check for collisions by the y axis
		for other in pg.sprite.spritecollide(self, level.sprites.get_all(), False):
			if other != self: self.onCollide(other, 0, self.velY)
		
		#Stop if the sprite is on the ground
		if self.onGround and self.velY > 0:
			self.velY = 0
		
		#Check for collisions by boths axis's
		for other in pg.sprite.spritecollide(self, level.sprites.get_all(), False):
			if other != self: self.onCollide(other, self.velX, self.velY)
		
		#stop sprite from falling out of the level
		self.rect.left = max(0, self.rect.left)
		self.rect.right = min(level.lwidth, self.rect.right)
		
		if self.rect.bottom > level.lheight:
			#sprite fell out of the level
			self.onDeath()
	
	def onCollide(self, other, velX, velY):
		if velX < 0:
			self.rect.left = other.rect.right+0 #Stop sprite from sticking to walls
		elif velX > 0:
			self.rect.right = other.rect.left-0 #Stop sprite from sticking to walls
		if velY >= 0:
			self.onGround = True
		elif velY < 0:
			self.rect.top = other.rect.bottom
			self.velY += 1
			self.onGround = False
		if velY > 0:
			self.rect.bottom = other.rect.top

#Sprite representing a player
class Player(PhysicsSprite):
	def __init__(self, x, y):
		PhysicsSprite.__init__(self)
		
		self.up = pg.image.load(get_res_path("player_up.bmp"))
		self.down = pg.image.load(get_res_path("player_down.bmp"))
		self.left = pg.image.load(get_res_path("player_left.bmp"))
		self.right = pg.image.load(get_res_path("player_right.bmp"))
		self.idle = pg.image.load(get_res_path("player.bmp"))
		
		self.image = self.idle
		self.rect  = self.image.get_rect()
		
		self.rect.move_ip(x, y)
		self.air = 20.0
		self.score = 0
		
		self.speed = 1.0
	
	def update(self, fps):
		PhysicsSprite.update(self, fps)
		global level
		
		if self.air <= 0:
			level.onDeath()
		
		self.air = min(20.0, self.air+0.01)
		
		self.image = self.idle if self.velY == 0 else self.up
		self.velX = 0 #Reset the x velocity so the player does not go sliding
		if pg.key.get_pressed()[K_a]:
			self.velX = -5
			self.image = self.left
		if pg.key.get_pressed()[K_d]:
			self.velX = 5
			self.image = self.right
		if pg.key.get_pressed()[K_SPACE] and (self.velY == 0 or self.inLiquid):
			self.velY = -25
	
	def onDeath(self):
		global level
		level.onDeath()
	
	def onCollide(self, other, velX, velY):
		global level
		if isinstance(other, Coin):
			level.sprites.remove(other)
			self.score += 1
		elif isinstance(other, EnemyBall):
			if velY > 0:
				level.sprites.collide.remove(other)
				self.score += 10
			else:
				level.onDeath()
		elif isinstance(other, EnemySpike):
			level.onDeath()
		elif isinstance(other, EnemyCannon):
			#if other.spikes == 0:
			level.sprites.collide.remove(other)
			self.score += 30
		elif isinstance(other, Trampoline):
			if self.velY > 0:
				self.velY = -30
		elif isinstance(other, ExitBlock):
			level.onWin()
		elif isinstance(other, Teleporter):
			level.onTeleport()
		elif isinstance(other, Mud):
			if self.rect.top <= other.rect.top and self.rect.bottom+1 >= other.rect.bottom:
				self.speed = 0.2
				self.onGround = False
				self.inLiquid = True
				
				self.air -= 0.005
		elif isinstance(other, Water):
			if self.rect.top <= other.rect.top and self.rect.bottom+1 >= other.rect.bottom:
				self.speed = 0.5
				self.onGround = False
				self.inLiquid = True
				
				self.air -= 0.005
		else:
			PhysicsSprite.onCollide(self, other, velX, velY)

class Block(Sprite):
	path = ""
	alpha = False
	
	def __init__(self, x, y):
		Sprite.__init__(self)
		
		if self.alpha:
			self.image = pg.image.load(self.path).convert_alpha()
		else:
			self.image = pg.image.load(self.path).convert()
		self.rect  = self.image.get_rect()
		
		self.rect.move_ip(x, y)
	

#Sprite representing a block
class StoneBlock(Block):
	path = get_res_path("stone.bmp")

class CloudBlock(Sprite):
	def __init__(self, x, y):
		Sprite.__init__(self)
		
		self.image = pg.Surface((50, 50))
		self.image.fill((255, 255, 255))
		self.rect  = self.image.get_rect()
		
		self.rect.move_ip(x, y)

class Mud(Block):
	path = get_res_path("mud.bmp")

class Water(Block):
	alpha = True
	path = get_res_path("water.png")

#Sprite representing a grass block
class GrassBlock(Block):
	path = get_res_path("grass.bmp")

class DirtBlock(Block):	
	path = get_res_path("dirt.bmp")

class Coin(Block):
	alpha = True
	path = get_res_path("coin.png")

class ExitBlock(Block):
	alpha = True
	path = get_res_path("exit.png")

class Trampoline(Block):
	alpha = True
	path = get_res_path("trampoline.png")

class Teleporter(Sprite):
	def __init__(self, x, y):
		Sprite.__init__(self)
		
		self.image = pg.Surface((32, 32), SRCALPHA, 32)
		self.image.fill((0, 0, 0, 0))
		
		self.rect = self.image.get_rect()
		
		self.rect.move_ip(x, y)

class EnemyBall(PhysicsSprite):
	def __init__(self, x, y):
		PhysicsSprite.__init__(self)
		
		self.images = load_animation(400, get_res_path("ball_enemy.png"))
		
		self.image = self.images[0]
		
		self.frame = 0
		
		self.rect = self.image.get_rect()
		
		self.rect.move_ip(x, y)
	
	def update(self, fps):
		global level
		PhysicsSprite.update(self, fps)
		if abs(level.player.rect.x - self.rect.x) < 300 and abs(level.player.rect.y - self.rect.y) < 150:
			self.image = self.images[self.frame]
			
			self.frame += -1 if level.player.rect.x < self.rect.x else 1
			
			self.frame %= len(self.images)
			
			if abs(level.player.rect.x - self.rect.x) <= 5:
				self.rect.x = level.player.rect.x
			elif level.player.rect.x < self.rect.x:
				self.velX = -5
			else:
				self.velX = 5
	
	def onCollide(self, other, velX, velY):
		if not other.__class__ == Coin:
			PhysicsSprite.onCollide(self, other, velX, velY)

class EnemyCannon(Sprite):
	def __init__(self, x, y):
		Sprite.__init__(self)
		
		self.images = load_animation(400, "C:\\Users\\rugrats\\Documents\\Python\\images\\cannon.png")
		
		self.empty = pg.image.load("C:\\Users\\rugrats\\Documents\\Python\\images\\cannon_empty.png")
		
		self.image = self.images[0]
		self.rect = self.image.get_rect()
		
		self.rect.move_ip(x, y)
		self.frame = 0
		
		self.spikes = 5
		
		self.spike = None
	
	def update(self, fps):
		global level
		if self.spikes:
			self.image = self.images[self.frame]
		else:
			self.image = self.empty
		
		self.frame += 1
		self.frame %= 8
		
		if abs(level.player.rect.x - self.rect.x) < 400 and abs(level.player.rect.y - self.rect.y) < 400 and self.spikes and self.spike == None and random.randint(1, 30) == 1:
			self.spike = EnemySpike(self.rect.x, self.rect.y-50)
			level.sprites.add_collidable(self.spike)
			#self.spikes -= 1
		
		if self.spike != None:
			if self.spike.dying:
				self.spike = None

class EnemySpike(PhysicsSprite):
	def __init__(self, x, y):
		PhysicsSprite.__init__(self)
		
		self.images = load_animation(400, get_res_path("spike_enemy.png"))
		
		self.image = self.images[0]
		self.rect  = self.image.get_rect()
		
		self.death = load_animation(400, get_res_path("spike_death.png"))
		
		self.dying = False
		
		self.rect.move_ip(x, y)
		self.frame = 0
		self.gravity = 0.0
	
	def update(self, fps):
		global level
		PhysicsSprite.update(self, fps)
		if abs(level.player.rect.x - self.rect.x) < 400 and abs(level.player.rect.y - self.rect.y) < 400:
			if self.dying:
				self.speed = 0.0000001
				if self.frame == 8:
					level.player.score += 20
					level.sprites.collide.remove(self)
					return
				self.image = self.death[int(self.frame)]
			else:
				self.image = self.images[int(self.frame)]
			
			self.frame += 1
			if not self.dying:
				self.frame %= len(self.images)
				if abs(level.player.rect.x - self.rect.x) <= 4:
					self.rect.x = level.player.rect.x
			
				if level.player.rect.x < self.rect.x:
					self.velX = -3
				else:
					self.velX = 3
				if abs(level.player.rect.y - self.rect.y) <= 4:
					self.rect.y = level.player.rect.y 
				elif level.player.rect.y < self.rect.y:
					self.velY = -3
				else:
					self.velY = 3
	
	def onCollide(self, other, velX, velY):
		global level
		if not other.__class__ in [Water, Coin]:
			self.dying = True
			self.frame = 0
			PhysicsSprite.onCollide(self, other, velX,velY)

class SpriteGroup:
	def __init__(self):
		self.collide    = pg.sprite.Group()
		self.player     = None
	
	def set_player(self, player):
		self.player = player
	
	def add_collidable(self, sprite):
		self.collide.add(sprite)
	
	def remove(self, sprite):
		global level
		self.collide.remove(sprite)
	
	def update(self, fps):
		self.collide.update(fps)
		self.player.update(fps)
	
	def get_all(self):
		all = pg.sprite.Group(self.collide)
		
		all.add(self.player)
		
		return all
	
	def draw(self, surface):
		surface.blit(self.player.image, self.player.rect.topleft)
		
		self.collide.draw(surface)

class Level:
	levels = []
	levelidx = 0
	def __init__(self, idx):
		level = self.levels[idx]
		self.levelidx = idx
		
		#initilize pygame
		pg.init()
		#create the window
		self.screen = pg.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF)
		
		pg.event.set_allowed([QUIT, KEYDOWN, KEYUP])
		
		self.sprites = SpriteGroup()
		
		self.fps = 40
		
		self.lheight = len(level) * 50
		self.lwidth = len(level[0]) * 50
		
		y = 0
		x = 0
		#Build level
		for row in level:
			for col in row:
				if col == "S":
					self.sprites.add_collidable(StoneBlock(x, y))
				elif col == "G":
					self.sprites.add_collidable(GrassBlock(x, y))
				elif col == "O":
					self.sprites.add_collidable(Coin(x, y))
				elif col == "M":
					self.sprites.add_collidable(Mud(x, y))
				elif col == "W":
					self.sprites.add_collidable(Water(x, y))
				elif col == "D":
					self.sprites.add_collidable(DirtBlock(x, y))
				elif col == "@":
					self.sprites.add_collidable(CloudBlock(x, y))
				elif col == "B":
					self.sprites.add_collidable(EnemyBall(x, y))
				elif col == "*":
					self.sprites.add_collidable(EnemySpike(x, y))
				elif col == "E":
					self.sprites.add_collidable(ExitBlock(x, y))
				elif col == "U":
					self.sprites.add_collidable(EnemyCannon(x, y))
				elif col == "H":
					self.sprites.add_collidable(Trampoline(x, y))
				elif col == "T":
					self.sprites.add_collidable(Teleporter(x, y))
				elif col == "P":
					self.player = Player(x, y)
					self.sprites.set_player(self.player)
				x += 50
			y += 50
			x = 0
		
		self.background = pg.transform.scale(pg.image.load(get_res_path("background.bmp")), (self.lwidth, self.lheight))
		
		self.stop = False
	
	def displayText(self, text, pos, size, color, center=False):
		pg.font.init()
		font = pg.font.SysFont("None", size, True)
		message = font.render(text, True, color)
		pg.font.quit()
		message = message.convert_alpha()
		
		#draw text
		if center:
			self.screen.blit(message, (WIDTH/2-message.get_rect().w/2, HEIGHT/2-message.get_rect().h/2))
		else:
			self.screen.blit(message, pos)
	
	def onDeath(self):
		#draw everything
		self.draw()
		
		#draw message
		self.displayText("You died!", (0, 0), 70, (0, 0, 0), True)
		self.displayText("You died!", (0, 0), 65, (255, 255, 255), True)
		
		pg.display.flip()
		
		start = pg.time.get_ticks()
		
		while not self.stop:
			self.process_events()
	
	def onTeleport(self):
		self.__init__(self.levelidx+1)
		
		self.run()
	
	def onWin(self):
		#draw everything
		self.draw()
		
		#draw message
		self.displayText("You won!", (0, 0), 70, (0, 0, 0), True)
		self.displayText("You won!", (0, 0), 65, (255, 255, 255), True)
		
		pg.display.flip()
		
		start = pg.time.get_ticks()
		
		while not self.stop:
			self.process_events()
	
	def process_events(self):
		for event in pg.event.get():
			#send events to sprites
			for sprite in self.sprites.get_all():
				sprite.handle_event(event)
			
			if event.type == QUIT:
				self.stop = True
				break
	
	def draw(self, surf=None):
		if surf == None:
			surf = self.surf
		
		#clear the screen
		surf.blit(self.background, (0, 0))
		self.screen.fill((0, 255, 255))
		
		#Draw sprites
		self.sprites.draw(surf)
		
		camera_pos = [-self.player.rect.left + self.lwidth / 4 + 25, -self.player.rect.top + self.lheight / 4 + 25]
		camera_pos[0] = min(0, camera_pos[0])
		camera_pos[0] = max(-(self.lwidth-WIDTH), camera_pos[0])
		
		camera_pos[1] = max(-(self.lheight-HEIGHT), camera_pos[1])
		
		self.screen.blit(self.surf, (camera_pos[0], camera_pos[1]))
		
		pg.display.flip()
	
	def update_sprites(self):
		self.sprites.update(self.clock.get_fps())
	
	def run(self):
		#create the clock
		clock = pg.time.Clock()
		self.clock = clock
		
		self.surf = pg.Surface((self.lwidth, self.lheight))
		
		self.draw()
		
		#level game loop
		while not self.stop:
			#update the sprites
			self.update_sprites()
			
			if self.stop:
				return
			
			#process the events
			self.process_events()
			
			if self.stop:
				return
			
			#draw everything
			self.draw()
			
			#Display debugging information
			pg.display.set_caption("fps: %.2f velX: %.2f velY: %.2f air: %.1f score: %d" % (clock.get_fps(), self.player.velX, self.player.velY, self.player.air, self.player.score))
			
			#Keep at a constant frame rate
			clock.tick(self.fps)

map = [
" @@@ @  @  @@  @@@@ @@@ @@ @@@@ @@ @@@@",
"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
"                                       ",
"                                       ",
"                                       ",
"OOOBOOOO                               ",
"GGGGGGGG   OOO                         ",
"           GGG             G           ",
"OOOOOOOO     DO            DG          ",
"OOGWWWWGG    DGO           DDG        G",
"OGDDDDDDDG   DDG           DSDG      GD",
"             DDDO          DSSDG    GDD",
"POOOOOOO   B DDDGOOO  GGG HDSSSDG    DD",
"GGGGGGGGGGGGGDDDDGGGGGDDDGGDDDDDDGGG DD",
"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDS SS",
"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDS SS",
"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDS SS",
"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDS SS",
"SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS SS",
"S                                    SS",
"ST       BBBBB                       SS",
"SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS"]


map2 = [
"GGGGGGGGGGGGGDDDDGGGGGDDDGGDDDDDDGGG GG",
"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDS SS",
"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDS SS",
"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDS SS",
"DDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDS SS",
"SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS SS",
"S S                                    ",
"SPS                                    ",
"S SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
"S SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
"S                                     S",
"S                BBBBBBB              S",
"S                BBBBBBB             TS",
"SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS"]

map3 = [
"SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
"S                                     S",
"S                                     S",
"S                                    PS",
"SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS S",
"S                                      ",
"S             BBBBBBBB                 ",
"S             BBBBBBBB                 ",
"S SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
"S               S                     S",
"S      BBBB     S                     S",
"S      BBBB     S    S   S   S   S    S",
"S      BBBB         SSSUSSSUSSSUSSS   S",
"SSSSSSSSSSSSSSSSSSSSSSS SSSS SSS SSSSSSS",
"SSSSSSSSSSSSSSSSSSSSSSSTSSSTSSSTSSSSSSS"]

map4 = [
" @@@ @  @  @@  @@@@ @@@ @@ @@@@ @@ @@@@",
"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",
"                                       ",
"                                       ",
"                                       ",
"EOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO ",
"GGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG ",
"                                     OO",
"                                   OBSS",
"                                 OBSSSS",
"                               OBSSSSSS",
"                             OBSSSSSSSS",
"                           OBSSSSSSSSSS",
"                         OBSSSSSSSSSSSS",
"                       OBSSSSSSSSSSSSSS",
"                     OBSSSSSSSSSSSSSSSS",
"                   OBSSSSSSSSSSSSSSSSSS",
"                 OBSSSSSSSSSSSSSSSSSSSS",
"POOOOOOOOOOOOOOOBSSSSSSSSSSSSSSSSSSSSSS",
"SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
]

Level.levels = [map, map2, map3, map4]

level = Level(0)

level.run()

pg.quit()
