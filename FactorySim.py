import pygame
import pygame.gfxdraw
import random

"""
TODO: adapt robot grab coordinates
Goal of this Simulation:
Visualize a HMI for a 2-D factory including manufacturing machines, intralogistics, productivity stats.
[3-D factory by having floors, switch floor with arrows on display]
Either pre-setup or player-based input for layout
Grid-based system (rectangles are 25x25 pixels)   CHANGE?

Available machines: (add them step by step)
product-adder
storage unit

Available intralogistics elements:
conveyor belt
roller , accumulating roller
robot arm
drones?

Available products:
empty box
bottles

++V0.0 add grid and visualize
++V0.1 add first pre-setup machine, first belt
++V0.1.1 define interfaces and orientation check
++V0.2 add empty box
++V0.3 add animations to machines, movement to products
+V0.4 expand setup -> more machines, more conveyors, more boxes, more products, actual production
V0.5a switch to player based layout
V1.2 decorate HUD

"""

WIDTH = 1000	# make sure this matches a factor of block_size from function create_grid! (does right now)
HEIGHT = 400	# make sure this matches a factor of block_size from function create_grid! (does right now)
BACKGROUND = (255, 255, 255)
MACHINES = list()
LOGISTICS = list()
PRODUCTS = list()
IDS = dict()


class PlacementError(Exception):
	def __init__(self, machinetype, coordinates, entity):
		machine = str(machinetype)
		machine = machine.split('.')[1]
		machine = machine.split('\'')[0]
		if isinstance(entity, str) == False:
			entity = str(entity)
		print("Can't place " + machine + " at " + str(coordinates) + ", because of " + entity)

class Resources:
	"""
	doc
	"""
	
	def __init__(self, coordinates):
		self.check_coordinates(coordinates)
		self.coordinates = coordinates
		self.ID = generate_ID()
		IDS[self.ID] = type(self)
		self.input_rect = list()		# a list of 25x3 rect  
		self.output_rect = list()		# a list of 25x3 rect  

	def check_coordinates(self, coordinates):
		if coordinates[0] < 0 or coordinates[0] > WIDTH:
			raise PlacementError(type(self), coordinates, "horizontal coordinate bounds")
		elif coordinates[1] < 0 or coordinates[1] > HEIGHT:
			raise PlacementError(type(self), coordinates, "vertical coordinate bounds")
		for i, entity in enumerate(LOGISTICS+MACHINES):
			if coordinates == entity.coordinates:
				raise PlacementError(type(self), coordinates, entity)

	def get_interfaces(self):
		"""
		goes through all currently existing machines and logistic elements,
		if one of their output interfaces overlap with own rect -> interface found -> add to own input interfaces
		"""
		combinedlist = MACHINES + LOGISTICS
		for i,logistic in enumerate(combinedlist):
			if logistic.coordinates == self.coordinates:
				if self.ID != logistic.ID:
					print(self.ID)
					print(logistic.ID)
			else:
				outputlist_indexes = self.rect.collidelistall(logistic.output_rect)
				if len(outputlist_indexes) > 0:
					for j in range(0, len(outputlist_indexes)):
						if logistic.output_rect[outputlist_indexes[j]] not in self.input_rect:
							self.input_rect.append(logistic.output_rect[outputlist_indexes[j]])
				inputlist_indexes = self.rect.collidelistall(logistic.input_rect)
				if len(inputlist_indexes) > 0:
					for j in range(0, len(inputlist_indexes)):
						if logistic.input_rect[inputlist_indexes[j]] not in self.output_rect:
							self.output_rect.append(logistic.input_rect[inputlist_indexes[j]])
					

class Machine(Resources):
	"""
	doc
	"""
	def __init__(self, coordinates):
		super().__init__(coordinates)
		pass

class ProductAdder(Machine):
	"""
	doc
	"""
	def __init__(self, coordinates, orientation, product):
		super().__init__(coordinates)
		self.size = (25,25)
		self.rect = pygame.Rect(coordinates, self.size)
		self.product = product
		if product == "boxes":
			tempimage = pygame.image.load("res/factory/boxAdder.png").convert()
		elif product == "bottles":
			tempimage = pygame.image.load("res/factory/bottleAdder.png").convert()
		self.image = pygame.transform.smoothscale(tempimage, self.size)	
		self.orientation = orientation
		if orientation == "horizontal":
			output_right = pygame.Rect((coordinates[0]+24, coordinates[1]), (3,25))
			self.output_rect.append(output_right)
			output_left = pygame.Rect((coordinates[0]-3, coordinates[1]), (3,25))
			self.output_rect.append(output_left)
			
		elif orientation == "vertical":
			output_up = pygame.Rect((coordinates[0], coordinates[1]-3), (25,3))
			self.output_rect.append(output_up)
			output_down = pygame.Rect((coordinates[0], coordinates[1]+24), (25,3))
			self.output_rect.append(output_down)

	def update(self):
		counter = 0
		for i, logistic in enumerate(LOGISTICS):
			coordinates = (0,0)
			collision = False
			if self.orientation == "horizontal":
				if self.output_rect[0] in logistic.input_rect:	# right output
					coordinates = (self.output_rect[0][0], self.output_rect[0][1] )			
				elif self.output_rect[1] in logistic.input_rect:
					coordinates = (self.output_rect[1][0]-19, self.output_rect[1][1] )
			else:			#vertical
				if self.output_rect[0] in logistic.input_rect:	# top output
					coordinates = (self.output_rect[0][0], self.output_rect[0][1]-19 )			
				elif self.output_rect[1] in logistic.input_rect:
					coordinates = (self.output_rect[1][0], self.output_rect[1][1]-1 )
			if coordinates != (0,0):
				if self.product == "boxes":
					newProduct = Box(coordinates)
					collision_box = pygame.Rect(coordinates, newProduct.size)
				elif self.product == "bottles":
					newProduct = Bottles(coordinates)
					collision_box = pygame.Rect(coordinates, newProduct.size)
				collision = check_collision(self.rect, collision_box, True)
				if collision == False:
					PRODUCTS.append(newProduct)
					counter += 1
				else:
					string = str(type(self)) + " " + self.ID + " overflow!"
					print(string)
			if counter == 2:
				break
		

class StorageUnit(Machine):
	"""
	doc
	"""
	def __init__(self, coordinates):
		super().__init__(coordinates)
		self.size = (25,25)
		self.rect = pygame.Rect(coordinates, self.size)
		tempimage = pygame.image.load("res/factory/storage.png").convert()
		self.image = pygame.transform.smoothscale(tempimage, self.size)
		self.get_interfaces()
		print(self.input_rect)
	
	def update(self):
		for i, product in enumerate(PRODUCTS):
			index = product.rect.collidelist(self.input_rect)
			if index > -1:
				new_coordinates = (self.rect[0]+2, self.rect[1]+2)
				product.rect.update(new_coordinates, product.size)

class Logistics(Resources):
	"""
	doc
	"""
	def __init__(self, coordinates):
		super().__init__(coordinates)
		pass

class Conveyor(Logistics):
	"""
	doc
	"""
	def __init__(self, coordinates):
		super().__init__(coordinates)
		self.direction = None	# stores direction of transportation, "up", "down", "left", "right"
		#self.check_orientation()
	
	def update(self):
		pass	

	def check_orientation(self):
		if self.direction == None:
			left_interface = pygame.Rect(self.coordinates[0]-1, self.coordinates[1], 3, 25)
			right_interface = pygame.Rect(self.coordinates[0]+24, self.coordinates[1], 3, 25)
			up_interface = pygame.Rect(self.coordinates[0], self.coordinates[1]-1, 25, 3)
			down_interface = pygame.Rect(self.coordinates[0], self.coordinates[1]+24, 25, 3)
			possible_neighbours = [(self.coordinates[0]-25,self.coordinates[1]), (self.coordinates[0]+25,self.coordinates[1]), (self.coordinates[0],self.coordinates[1]+25), (self.coordinates[0],self.coordinates[1]-25)]
			hits = list()
			combinedlist = LOGISTICS+MACHINES
			for i, entity in enumerate(combinedlist):
				if entity.coordinates in possible_neighbours:
					hits.append(entity.coordinates)
			if len(hits) > 2 and isinstance(self, RollerConveyor) and isinstance(self, TIntersection) == False: #1D Roller Conveyor supposed to only have 2 neighbors
				raise PlacementError(type(self), self.coordinates, "too many neighbours")
			elif len(hits) <= 0:
				pass
			else:
				if len(self.input_rect) == 0:
					pass
				elif len(self.input_rect) == 1:
					input = self.input_rect[0]
					output_rect = False
					for k in range (0,len(hits)):
						if hits[k][0] < self.coordinates[0]: # neighbour on left flank
							if input.left < self.coordinates[0]: # input on left flank
								pass
							else: # input not on left flank -> has to be output
								output_rect = left_interface
								self.direction = "left"
								self.image = pygame.transform.rotate(self.image, 90)
								self.image1 = pygame.transform.rotate(self.image1, 90)
								break
						elif hits[k][0] > self.coordinates[0]: # neighbour on the right flank
							if input.left > self.coordinates[0]: # input on the right flank
								pass
							else:
								output_rect = right_interface
								self.direction = "right"
								self.image = pygame.transform.rotate(self.image, 270)
								self.image1 = pygame.transform.rotate(self.image1, 270)
								break
						elif hits[k][1] < self.coordinates[1]: # neighbour above
							if input.top < self.coordinates[1]: # input above
								pass
							else:
								output_rect = up_interface
								self.direction = "up"
								#image correct orientation from loading
								break
						elif hits[k][1] > self.coordinates[1]:
							if input.top > self.coordinates[1]:
								pass
							else:
								output_rect = down_interface
								self.direction = "down"
								self.image = pygame.transform.flip(self.image, False, True)
								self.image1 = pygame.transform.flip(self.image1, False, True)
								break
						else:
							print('error3')
					if not output_rect == False:
						if output_rect not in self.output_rect: 
							self.output_rect.append(output_rect)
				elif len(self.input_rect) == 2:
					pass
				elif len(self.input_rect) == 3:
					if isinstance(self, TIntersection):
						possible_interfaces = [left_interface, right_interface, up_interface, down_interface]
						for i in range(0,4):
							if not possible_interfaces[i] in self.input_rect:
								self.output_rect.append(possible_interfaces[i])
								if i == 0:
									self.direction = "left"
									self.image = pygame.transform.rotate(self.image, 90)
									self.image1 = pygame.transform.rotate(self.image1, 90)
								elif i == 1:
									self.direction = "right"
									self.image = pygame.transform.rotate(self.image, 270)
									self.image1 = pygame.transform.rotate(self.image1, 270)
								elif i == 2:
									self.direction = "up"
									#image correct orientation from loading
								else:
									self.direction = "down"
									self.image = pygame.transform.flip(self.image, False, True)
									self.image1 = pygame.transform.flip(self.image1, False, True)
								break
				else:
					print('error1')
					# TODO: create actual error
		if self.direction == None:
			if len(self.output_rect) == 1:
				output = self.output_rect[0]
				if output == left_interface:	# if only output found, turn conveyor towards output 
					self.direction ="left"
					self.image = pygame.transform.rotate(self.image, 90)
					self.image1 = pygame.transform.rotate(self.image1, 90)
				elif output == right_interface:
					self.direction = "right"
					self.image = pygame.transform.rotate(self.image, 270)
					self.image1 = pygame.transform.rotate(self.image1, 270)
				elif output == up_interface:
					self.direction = "up"
					#image correct orientation from loading
				elif output == down_interface:
					self.direction = "down"
					self.image = pygame.transform.flip(self.image, False, True)
					self.image1 = pygame.transform.flip(self.image1, False, True)
				input_rect = False
				for k in range (0,len(hits)):
					if hits[k][0] < self.coordinates[0]: # neighbour on left flank
						if output.left < self.coordinates[0]: # ouput on left flank
							pass
						else: # output not on left flank -> has to be input
							input_rect = left_interface
					elif hits[k][0] > self.coordinates[0]: # neighbour on the right flank
						if output.left > self.coordinates[0]: # output on the right flank
							pass
						else:
							input_rect = right_interface
					elif hits[k][1] < self.coordinates[1]: # neighbour above
						if output.top < self.coordinates[1]: # output above
							pass
						else:
							input_rect = up_interface
					elif hits[k][1] > self.coordinates[1]: # neighbour below
						if output.top > self.coordinates[1]: # output below
							pass
						else:
							input_rect = down_interface
					else:
						print('error3')
				if not input_rect == False:
					if input_rect not in self.input_rect: 
						self.input_rect.append(input_rect)
			else:
				pass
				#print("error4")

class BeltConveyor(Conveyor):
	"""
	doc
	"""
	def __init__(self,coordinates):
		pass
	
	def update(self):
		pass

class RollerConveyor(Conveyor):
	"""
	doc
	"""
	def __init__(self,coordinates):
		super().__init__(coordinates)
		self.size = (25,25)
		self.rect = pygame.Rect(coordinates, self.size)
		tempimage = pygame.image.load("res/factory/rollerConveyor.png").convert()
		self.image = pygame.transform.smoothscale(tempimage, self.size)	
		tempimage1 = pygame.image.load("res/factory/rollerConveyor1.png").convert()
		self.image1 = pygame.transform.smoothscale(tempimage1, self.size)	
		self.get_interfaces()
		self.check_orientation()	# can only be called here since in class __init__ the images are not yet set
			
	
	def update(self):
		pass

class TIntersection(RollerConveyor):
	"""
	2/3 inputs, 1 output, if 2 inputs direction needs to be specified (otherwise type None for automatic orientation)
	"""
	def __init__(self,coordinates, direction):
		super().__init__(coordinates)
		tempimage = pygame.image.load("res/factory/TIntersection.png").convert()
		self.image = pygame.transform.smoothscale(tempimage, self.size)	
		tempimage1 = pygame.image.load("res/factory/TIntersection1.png").convert()
		self.image1 = pygame.transform.smoothscale(tempimage1, self.size)	
		self.direction = direction
		if direction == "up":
			output_interface = pygame.Rect((coordinates[0], coordinates[1]-1), (25,3))
			#picture correct orientation
		elif direction == "down":
			output_interface = pygame.Rect((coordinates[0], coordinates[1]+24), (25,3))
			self.image = pygame.transform.flip(self.image, False, True)
			self.image1 = pygame.transform.flip(self.image1, False, True)
		elif direction == "left":
			output_interface = pygame.Rect((coordinates[0]-1, coordinates[1]), (3,25))
			self.image = pygame.transform.rotate(self.image, 270)
			self.image1 = pygame.transform.rotate(self.image1, 270)
		elif direction == "right":
			output_interface = pygame.Rect((coordinates[0]+24, coordinates[1]), (3,25))
			self.image = pygame.transform.rotate(self.image, 90)
			self.image1 = pygame.transform.rotate(self.image1, 90)
		if direction != None:
			self.output_rect.append(output_interface)
		self.get_interfaces()
		self.check_orientation()	# can only be called here since in class __init__ the images are not yet set
		
		
			
	
	def update(self):
		pass

class RobotArm(Logistics):
	"""
	doc
	"""
	def __init__(self,coordinates, direction):
		super().__init__(coordinates)
		self.grabbed = None
		self.size = (25,25)
		self.rect = pygame.Rect(coordinates, self.size)
		self.images = dict()
		for i in range(0,8):
			path = "res/factory/robotArm/robotArm" + str(i+1) + ".png"
			tempimage = pygame.image.load(path).convert()
			self.images[i+1] = pygame.transform.smoothscale(tempimage, self.size)		
		left_interface = pygame.Rect(self.coordinates[0]-1, self.coordinates[1], 3, 25)
		right_interface = pygame.Rect(self.coordinates[0]+24, self.coordinates[1], 3, 25)
		up_interface = pygame.Rect(self.coordinates[0], self.coordinates[1]-1, 25, 3)
		down_interface = pygame.Rect(self.coordinates[0], self.coordinates[1]+24, 25, 3)
		self.direction = direction
		if direction == "up":
			self.image_index = 1
			self.output_rect.append(up_interface)
			self.input_rect = [right_interface, down_interface, left_interface]
		elif direction == "right":
			self.image_index = 3
			self.output_rect.append(right_interface)
			self.input_rect = [up_interface, down_interface, left_interface]
		elif direction == "down":
			self.image_index = 5
			self.output_rect.append(down_interface)
			self.input_rect = [up_interface, right_interface, left_interface]
		elif direction == "left":
			self.image_index = 7
			self.output_rect.append(left_interface)
			self.input_rect = [up_interface, right_interface, down_interface]
		self.image = self.images[self.image_index]
	
	def update(self):
		if self.grabbed == None:
			for i, product in enumerate(PRODUCTS):
				if isinstance(product, Bottles):
					index = product.rect.collidelist(self.input_rect)
					if index > -1:
						left_interface = pygame.Rect(self.coordinates[0]-1, self.coordinates[1], 3, 25)
						right_interface = pygame.Rect(self.coordinates[0]+24, self.coordinates[1], 3, 25)
						up_interface = pygame.Rect(self.coordinates[0], self.coordinates[1]-1, 25, 3)
						down_interface = pygame.Rect(self.coordinates[0], self.coordinates[1]+24, 25, 3)
						if self.input_rect[index] == left_interface: # left input
							if self.image_index == 7:
								self.grabbed = product.ID
								product.busy = True
							elif self.image_index in [8,1,2,3]:
								newindex = self.image_index -1
								if newindex == 0:
									newindex = 8
								self.image_index = newindex
								self.image = self.images[newindex]
							elif self.image_index in [4,5,6]:
								newindex = self.image_index + 1
								self.image_index = newindex
								self.image = self.images[newindex]
						elif self.input_rect[index] == right_interface: # right input
							if self.image_index == 3:
								self.grabbed = product.ID
								product.busy = True
							elif self.image_index in [7,8,1,2]:
								newindex = self.image_index +1
								if newindex == 9:
									newindex = 1
								self.image_index = newindex
								self.image = self.images[newindex]
							elif self.image_index in [4,5,6]:
								newindex = self.image_index - 1
								self.image_index = newindex
								self.image = self.images[newindex]
						elif self.input_rect[index] == up_interface: # upper input
							if self.image_index == 1:
								self.grabbed = product.ID
								product.busy = True
							elif self.image_index in [5,6,7,8]:
								newindex = self.image_index + 1
								if newindex == 9:
									newindex = 1
								self.image_index = newindex
								self.image = self.images[newindex]
							elif self.image_index in [2,3,4]:
								newindex = self.image_index - 1
								self.image_index = newindex
								self.image = self.images[newindex]
						elif self.input_rect[index] == down_interface: # lower input
							if self.image_index == 5:
								self.grabbed = product.ID
								product.busy = True
							elif self.image_index in [6,7,8]:
								newindex = self.image_index - 1
								self.image_index = newindex
								self.image = self.images[newindex]
							elif self.image_index in [1,2,3,4]:
								newindex = self.image_index + 1
								self.image_index = newindex
								self.image = self.images[newindex]
						if not self.grabbed == None:
							if self.image_index == 1:
								new_coordinates = (self.rect[0]+5, self.rect[1]-10)
							elif self.image_index == 2:
								new_coordinates = (self.rect[0]+10, self.rect[1]-5)
							elif self.image_index == 3:
								new_coordinates = (self.rect[0]+18, self.rect[1]-1)
							elif self.image_index == 4:
								new_coordinates = (self.rect[0]+10, self.rect[1]+5)
							elif self.image_index == 5:
								new_coordinates = (self.rect[0]+5, self.rect[1]+10)
							elif self.image_index == 6:
								new_coordinates = (self.rect[0], self.rect[1]+5)
							elif self.image_index == 7:
								new_coordinates = (self.rect[0]-5, self.rect[1]-1)
							elif self.image_index == 8:
								new_coordinates = (self.rect[0]-10, self.rect[1]-5)
							product.rect.update(new_coordinates, product.size)
						break


class Product:
	"""
	doc
	"""
	def __init__(self, coordinates):
		"""
		doc
		"""
		self.ID = generate_ID()
		IDS[self.ID] = type(self)
		self.busy = False
	
	def update(self):
		"""
		doc
		"""
		if self.busy == False:
			upc = 0
			downc = 0
			leftc = 0
			rightc = 0
			xcenter = self.rect[0] + int(self.size[0]*0.5)
			ycenter = self.rect[1] + int(self.size[1]*0.5)
			xline = ((self.rect[0], ycenter ) , ( self.rect[0] + self.size[0],  ycenter))
			yline = ((xcenter, self.rect[1] ) , ( xcenter, self.rect[1]+self.size[1]))
			collision = False
			for i,logistic in enumerate(LOGISTICS):
				if logistic.direction == "up" or logistic.direction == "down":
					yclip = logistic.rect.clipline(yline) #yclip containts line part coordinates which is in logistic rect
					if yclip:	# evaluates if yclip has contents and there is inside the 
						if logistic.direction == "up":
							if upc == 0:
								collision_box = pygame.Rect(self.rect[0], self.rect[1]-1, self.size[0], self.size[1]+1)
								collision = check_collision(self.rect, collision_box, False)
								if collision == False:
									self.rect = self.rect.move(0,-1)
								upc += 1
						elif logistic.direction == "down":
							if downc == 0:
								collision_box = pygame.Rect(self.rect[0], self.rect[1], self.size[0], self.size[1]+1)
								collision = check_collision(self.rect, collision_box, False)
								if collision == False:
									self.rect = self.rect.move(0,1)
								downc += 1
				else:   # direction == left or right
					xclip = logistic.rect.clipline(xline) #yclip containts line part coordinates which is in logistic rect
					if xclip:	# evaluates if yclip has contents and there is inside the 
						if logistic.direction == "left":
							if leftc == 0:
								collision_box = pygame.Rect(self.rect[0]-1, self.rect[1], self.size[0]+1, self.size[1])
								collision = check_collision(self.rect, collision_box, False)
								if collision == False:
									self.rect = self.rect.move(-1,0)
								leftc += 1
						elif logistic.direction == "right":
							if rightc == 0:
								collision_box = pygame.Rect(self.rect[0], self.rect[1], self.size[0]+1, self.size[1])
								collision = check_collision(self.rect, collision_box, False, )
								if collision == False:
									self.rect = self.rect.move(1,0)
								rightc += 1
			machine_index = self.rect.collidelist(MACHINES)
			if machine_index >= 0:
				machine = MACHINES[machine_index]
				if isinstance(machine, StorageUnit):
					self.rect.update((machine.coordinates[0]+3, machine.coordinates[1]+3), self.size)
					self.busy = True

class Box(Product):
	"""
	doc
	"""
	size = (19,17)

	def __init__(self, coordinates):
		super().__init__(coordinates)
		
		self.rect = pygame.Rect((coordinates[0]+3, coordinates[1]+3), self.size)
		tempimage = pygame.image.load("res/factory/box.png").convert_alpha()
		self.image = pygame.transform.smoothscale(tempimage, self.size)	
		self.content = None

class Bottles(Product):
	"""
	doc
	"""
	size = (19,17)
	
	def __init__(self, coordinates):
		super().__init__(coordinates)
		self.rect = pygame.Rect((coordinates[0]+3, coordinates[1]+3), self.size)
		tempimage = pygame.image.load("res/factory/bottles.png").convert_alpha()
		self.image = pygame.transform.smoothscale(tempimage, self.size)
		tempimage = pygame.image.load("res/factory/boxedBottles.png").convert_alpha()
		self.image_boxed = pygame.transform.smoothscale(tempimage, self.size)
		

def check_collision(own_rect, collision_box, ignore_machines):
	"""
	method to check if a moved or spawned product would collide with another product or machine
	IN:
		collision_box: pygame.Rect box representing the area where a product wants to move to
		ignore_machines: flag if collisions with machines should be ignored
	DO:
		checks for rect overlap with all other products and machines
	OUT:
		returns True for a detected collision and False if not
	"""
	collision = False
	for i, product in enumerate(PRODUCTS):
		if product.rect.colliderect(collision_box) == True and not product.rect == own_rect:
			collision = True
			break
	if ignore_machines == False:
		for j, machine in enumerate(MACHINES):
			if machine.rect.colliderect(collision_box) == True:
				collision = True
				break
		for k, logistic in enumerate(LOGISTICS):
			if isinstance(logistic, RobotArm):
				if logistic.rect.colliderect(collision_box) == True:
					collision = True
					break
	return collision

def generate_ID():
		ID = str(random.randint(1,9999))
		while len(ID) < 4:
			ID = "0" + ID
		while ID in IDS.keys():
			ID = str(random.randint(1,9999))
			while len(ID) < 4:
				ID = "0" + ID
		return ID

def create_grid(screen):
	"""
	creates a grid of 25x25 pixel rectangles. There are the boxes which all further elements are aligned on
	creates the boxes by drawing horizontal and vertical lines
	color is greyish (20,20,20) with alpha value 60 for high-transparency
	"""
	block_size = 25 
	for z in range(0, int(HEIGHT/block_size)):
		pygame.gfxdraw.hline(screen, 0, WIDTH, z*block_size, (20,20,20, 60) ) 
	for x in range(0, int(WIDTH/block_size)):
		pygame.gfxdraw.vline(screen, x*block_size, 0, HEIGHT, (20,20,20, 60) )

def main():
	global MACHINES
	global LOGISTICS
	global PRODUCTS
	global IDS
	clock = pygame.time.Clock()
	pygame.init()
	screen = pygame.display.set_mode((WIDTH, HEIGHT))
	box_adder1 = ProductAdder((50,50), "horizontal", "boxes")
	MACHINES.append(box_adder1)
	box_adder2 = ProductAdder((175,50), "horizontal", "boxes")
	MACHINES.append(box_adder2)
	box_adder3 = ProductAdder((225,200), "horizontal", "boxes")
	MACHINES.append(box_adder3)
	bottle_adder1 = ProductAdder((100,0), "vertical", "bottles")
	MACHINES.append(bottle_adder1)
	bottle_adder2 = ProductAdder((350,100), "vertical", "bottles")
	MACHINES.append(bottle_adder2)
	storage1 = StorageUnit((75,150))
	MACHINES.append(storage1)


	roller_coordinates = [(75,50), (100,75), (100,100), (75,100), (75,125), (125,50), (100,25), (150,50)]
	roller_coordinates2 = [(350,75), (375,75), (400,75), (400,100), (400,125), (400,150), (375,150), (350,150), (325,150)]
	roller_coordinates3 = [(275,150), (250,150), (250,175), (250,200), (300,125)]
	merged_lists = roller_coordinates+roller_coordinates2+roller_coordinates3
	for i in range(0,len(merged_lists)):
		new_roller = RollerConveyor(merged_lists[i])
		LOGISTICS.append(new_roller)
	TIntersection1 = TIntersection((100,50), None)
	LOGISTICS.append(TIntersection1)
	robotArm1 = RobotArm((300,150), "up")
	LOGISTICS.append(robotArm1)

	SPAWNTIMER, t = pygame.USEREVENT+1, 5000
	pygame.time.set_timer(SPAWNTIMER, t)
	CHECKTIMER, t2 = pygame.USEREVENT+2, 800
	pygame.time.set_timer(CHECKTIMER, t2)
	caption = 'FactorySim'
	pygame.display.set_caption(caption)
	counter = 0
	print("/--- Automatic interface and orientation detection in progress, please wait")
	for j in range(0,len(LOGISTICS)+1):
		for i,entity in enumerate(LOGISTICS):
			if isinstance(entity, Conveyor):
				entity.get_interfaces()
				entity.check_orientation()	
	print("o/-- Automatic interface and orientation detection in progress, please wait")
	for j in range(0,len(LOGISTICS)+1):
		for i,entity in enumerate(LOGISTICS):
			if isinstance(entity, Conveyor):
				entity.get_interfaces()
				entity.check_orientation()	
	print("oo/- Automatic interface and orientation detection in progress, please wait")
	for i, machine in enumerate(MACHINES):
			machine.get_interfaces()
	print("ooo/ Automatic interface and orientation detection finished")
	while 1:
		screen.fill(BACKGROUND)
		create_grid(screen)
		#print(pygame.event.get())
		for event in pygame.event.get():
			if event.type == SPAWNTIMER:
				for j, machine in enumerate(MACHINES):
					machine.update()
				#print(IDS.keys())	
			elif event.type == CHECKTIMER:
				for i, logistic in enumerate(LOGISTICS):
					if isinstance(logistic, RobotArm):
						logistic.update()
		for i,machine in enumerate(MACHINES):
				screen.blit(machine.image, machine.rect)
		if counter == 0:
			for i,entity in enumerate(LOGISTICS):
				screen.blit(entity.image, entity.rect)	
			counter = 1
		else:
			for i,entity in enumerate(LOGISTICS):
				if isinstance(entity, Conveyor):
					screen.blit(entity.image1, entity.rect)	
				else:
					screen.blit(entity.image, entity.rect)
					entity.update()
			counter = 0		
		for i,product in enumerate(PRODUCTS):
				screen.blit(product.image, product.rect)
				product.update()

		pygame.display.flip()
		clock.tick(24)
		#slow-mo:
		#clock.tick(5)

if __name__ == "__main__":
	main()