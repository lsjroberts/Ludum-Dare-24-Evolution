# -------- Player.py --------
# Handles all logic relating to the Player
# ---------------------------

# Imports
import pygame, Config
import Vector2D
from Event import EventManager, EventListener
from Sprite import StaticSprite, MovingSprite

# Load sounds
pygame.mixer.init( )
sound_shoot = pygame.mixer.Sound( "sounds/player-shoot.wav" )
sound_player_die = pygame.mixer.Sound( "sounds/player-die.wav" )
sound_shoot.set_volume( 0.5 )

# -------- Player --------
class Player( MovingSprite ):
	control_FIRE_PRIMARY = 1 # Mouse left
	control_FIRE_SECONDARY = 3 # Mouse right
	control_MOVE_UP = pygame.K_w
	control_MOVE_RIGHT = pygame.K_d
	control_MOVE_DOWN = pygame.K_s
	control_MOVE_LEFT = pygame.K_a

	max_speed 	= [600.0, 400.0] # Pixels per second
	cur_speed 	= [0.0, 0.0]
	accl 		= [10.0, 20.0] # Change per second
	dccl		= [5.0, 10.0]
	is_accl 	= [0, 0]

	move_vector = [0, 0]

	energy_flip = 0
	energy_rate = 8 # per second
	is_firing_energy = False
	has_fired_energy = False
	direction = 1

	has_captured = False
	captured_plant = None

	lives = 3
	
	# Init
	def __init__( self ):
		# Set groups & layer
		self.groups = Config.app.sprite_groups['player'], Config.app.sprites_all
		self._layer = Config.sprite_layer_player

		# Create as animated sprite
		MovingSprite.__init__(
			self,
			"player/player-b.png",
			[Config.screen_move_x, Config.screen_h / 2]
		)

		self.AddAnimationState( "moving-right", 0, 7, 6 )
		self.AddAnimationState( "moving-left", 8, 15, 6 )
		self.SetAnimationState( "moving-right" )

		# Register listeners
		Config.app.em.RegisterListener( PlayerMouseListener() )
		Config.app.em.RegisterListener( PlayerKeyboardListener() )

		self.collide_with = [
			{
				'group': Config.app.sprite_groups['friendly-trees'],
				'module': 'Friendly',
				'event': 'FriendlyTreePlayerCollisionEvent'
			},
			{
				'group': Config.app.sprite_groups['enemy-flying'],
				'module': 'Enemy',
				'event': 'CollisionEvent'
			}
		]

		for i in range( self.lives ):
			PlayerLife( i+1 )

		Config.player = self


	# Fire Energy
	def FireEnergy( self ):
		if self.has_captured == False:

			# Flip which gun fires the particle
			self.energy_flip = 1 - self.energy_flip
			if (self.energy_flip):
				vector = Vector2D.AddVectors( self.vector, [self.direction * 20, 9] )
			else:
				vector = Vector2D.AddVectors( self.vector, [self.direction * 20, 19] )

			# Create energy particle
			EnergyParticle( vector, self.direction )


	# Fire Pulse
	def FirePulse( self ):
		pass


	# Launch Captured
	def LaunchCaptured( self ):
		self.has_captured = False
		self.captured_plant.captured = False
		self.captured_plant = None

	
	# On Collision
	def OnCollision( self, c ):
		if c.__class__.__name__ == "EnemyFlying":
			self.lives -= 1
			sound_player_die.play( )

			for l in Config.app.sprite_groups['player-lives']:
				if l.life == self.lives + 1:
					l.kill( )
					break


			if self.lives >= 0:
				self.vector = [Config.screen_move_x, Config.screen_h / 2]
				Config.world_offset = 0
			else:
				Config.app.UnloadGame( )

	# Update
	def Update( self, frame_time, ticks ):
		m = frame_time / 1000.0

		if self.is_firing_energy:
			if self.has_fired_energy <= 0:
				self.FireEnergy( )
				self.has_fired_energy = 1000 / self.energy_rate

		if self.has_fired_energy > 0:
			self.has_fired_energy -= frame_time


		if self.cur_speed[0] < 0:
			if self.GetDrawPos(0) < Config.screen_move_x and self.vector[0] >= Config.screen_move_x:
				Config.world_offset -= (self.cur_speed[0] * m)

		elif self.cur_speed[0] > 0:
			if self.GetDrawPos(0) > Config.screen_w - Config.screen_move_x and self.vector[0] <= (Config.screen_w * Config.world_size) - Config.screen_move_x:
				Config.world_offset -= (self.cur_speed[0] * m)

		MovingSprite.Update( self, frame_time, ticks )


	# Control Mouse Down
	def ControlMouseDown( self, event ):
		if event.button == self.control_FIRE_PRIMARY:
			self.is_firing_energy = True

		elif event.button == self.control_FIRE_SECONDARY:
			if self.has_captured == True:
				self.LaunchCaptured( )
			else:
				self.FirePulse( )


	# Control Mouse Up
	def ControlMouseUp( self, event ):
		if event.button == self.control_FIRE_PRIMARY:
			self.is_firing_energy = False


	# Control Mouse Motion
	def ControlMouseMotion( self, event ):
		pass


	# Control Keyboard Down
	def ControlKeyDown( self, event ):
		if event.key == self.control_MOVE_UP:
			self.is_accl[1] = -1
		elif event.key == self.control_MOVE_RIGHT:
			self.is_accl[0] = 1
			self.direction = 1
			self.SetAnimationState( "moving-right" )
		elif event.key == self.control_MOVE_DOWN:
			self.is_accl[1] = 1
		elif event.key == self.control_MOVE_LEFT:
			self.is_accl[0] = -1
			self.direction = -1
			self.SetAnimationState( "moving-left" )


	# Control Keyboard Up
	def ControlKeyUp( self, event ):
		if event.key == self.control_MOVE_UP:
			if self.is_accl[1] == -1:
				self.is_accl[1] = 0
		elif event.key == self.control_MOVE_RIGHT:
			if self.is_accl[0] == 1:
				self.is_accl[0] = 0
		elif event.key == self.control_MOVE_DOWN:
			if self.is_accl[1] == 1:
				self.is_accl[1] = 0
		elif event.key == self.control_MOVE_LEFT:
			if self.is_accl[0] == -1:
				self.is_accl[0] = 0


# -------- PlayerLife --------
class PlayerLife( StaticSprite ):
	# Init
	def __init__( self, life ):
		self.groups = Config.app.sprite_groups['player-lives'], Config.app.sprites_all
		self._layer = Config.sprite_layer_player

		StaticSprite.__init__( self, "player/player-life.png", [life * 40, 20] )

		self.life = life

	# Get Draw Pos
	# without offset
	def GetDrawPos( self, i=None ):
		if i == None:
			self.vector
		elif i == 0:
			return self.vector[i]
		elif i == 1:
			return self.vector[i]


# -------- EnergyParticle --------
class EnergyParticle( StaticSprite ):
	max_speed = [1000.0, 0.0]
	

	# Init
	def __init__( self, vector, direction ):
		# Set groups & layer
		self.groups = Config.app.sprite_groups['energy-particles'], Config.app.sprites_all
		self._layer = Config.sprite_layer_player

		StaticSprite.__init__( self, "player/energy-particle.png", vector )

		self.direction = direction

		sound_shoot.play( )

		self.collide_with = [
			{
				'group': Config.app.sprite_groups['friendly-plants'],
				'module': 'Friendly',
				'event': 'FriendlyPlantEnergyCollisionEvent'
			},
			{
				'group': Config.app.sprite_groups['enemy-flying'],
				'module': 'Enemy',
				'event': 'EnemyFlyingEnergyCollisionEvent'
			}
		]


	# Update
	def Update( self, frame_time, ticks ):
		m = (frame_time / 1000.0) * self.direction

		self.move_vector = Vector2D.MultiplyVectors( self.max_speed, [m, 0] )
		self.vector = Vector2D.AddVectors( self.vector, self.move_vector )

		StaticSprite.Update( self, frame_time, ticks )

		if self.vector[0] > Config.screen_w * Config.world_size or self.vector[0] < 0:
			self.kill( )


	# On Collision
	def OnCollision( self, c ):
		if c.__class__.__name__ == "EnemyFlying":
			c.health -= 1
			if c.health <= 0:
				c.DieOverlyDramatically( )

		self.kill( )


# -------- Player Keyboard Listener --------
class PlayerKeyboardListener( EventListener ):
	# Notify
	def Notify( self, event ):
		if event.name == "Pygame Event":
			if event.data.type == pygame.KEYDOWN:
				Config.player.ControlKeyDown( event.data )

			elif event.data.type == pygame.KEYUP:
				Config.player.ControlKeyUp( event.data )


# -------- Player Mouse Listener ---------
class PlayerMouseListener( EventListener ):
	# Notify
	def Notify( self, event ):
		if event.name == "Pygame Event":
			if event.data.type == pygame.MOUSEBUTTONDOWN:
				Config.player.ControlMouseDown( event.data )

			elif event.data.type == pygame.MOUSEBUTTONUP:
				Config.player.ControlMouseUp( event.data )

			elif event.data.type == pygame.MOUSEMOTION:
				Config.player.ControlMouseMotion( event.data )