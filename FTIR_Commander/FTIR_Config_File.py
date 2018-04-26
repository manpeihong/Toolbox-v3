
from struct import *

def Load_FTIR_Config( file_contents ):
	Beam_Splitters = ["", "KBr Mid IR", "CaF2", "Quartz", "Solid Substrate Far IR"]
	size_of_types = {'f':4,'B':1,'b':1}
	wanted_data = [
		("Beam Splitter Index", 0xEBF, 'b'),
		("Start Wavelength", 0xF1E, 'f'),
		("End Wavelength", 0xF22, 'f'),
		("Number of Scans", 0x63A, 'B'),
		("Velocity", 0xEC5, 'f'),
		("Aperture", 0xEC1, 'f'),
		#("Aperture", 0xEC1, 'f'),
		("Gain", 0xED7, 'f')]

	sorted_wanted_data = sorted( wanted_data, key=lambda x:x[1] )
	struct_format = "<" + str( sorted_wanted_data[0][1] ) + 'x' + sorted_wanted_data[0][2]
	for index, useful_bit in enumerate( sorted_wanted_data[1:] ):
		distance_to_previous = useful_bit[1] - sorted_wanted_data[index][1] - size_of_types[ sorted_wanted_data[index][2] ]
		struct_format += str(distance_to_previous) + 'x' + useful_bit[2]

	file_settings = {}

	sizeofthing = len( file_contents )
	#extracted_data2 = unpack_from('<3870xff', file_contents)
	extracted_data = unpack_from(struct_format, file_contents)

	file_settings = dict( zip([x[0] for x in sorted_wanted_data],
							extracted_data) )

	file_settings["Beam Splitter"] = Beam_Splitters[ file_settings["Beam Splitter Index"] ]

	return file_settings

if __name__ == "__main__":
	with open( "Default.exp", 'rb' ) as file:
		file_contents = file.read()

		settings = Load_FTIR_Config( file_contents )
	pass