-- Lua script for experiment To be run in mpv

-- keypresses.txt: the output file
-- It lists the actual time followed by the position
-- in the video for each keypress

-- positions.txt: list of positions (in order) to which to skip
-- You should make this file before starting the experiment
-- The end of the video should be one of the positions

-- Open the files
file = io.open(os.date('keypresses_%Y%m%d_%H%M%S.txt'), 'a')
positions = io.open('positions.txt', 'r')
starttime = 0

-- Read positions into array
pos = {}
i = 1
n = 0
while n ~= nil do
	n = positions:read('*n')
	pos[i] = n
	i = i + 1
end

-- Search for first position greater than n
function find_first_gre(n)
	local i = 1
	while pos[i] < n do
		i=i+1
	end
	return pos[i]
end

-- The handler for the keypress, outputs to keypresses.txt
function keypress_handler()
	local pos = mp.get_property_number('time-pos')
	file:write(mp.get_time() - starttime, ' ', pos, '\n')
	mp.set_property('time-pos', find_first_gre(pos))
end

-- Close files
function close_files()
	file:close()
	positions:close()
end

-- Get time when file is loaded
function get_start_time()
	starttime = mp.get_time()
end

-- Register events and add key bindings
-- You can see a list of special keys with `mpv --input-keylist'
mp.register_event('file-loaded', get_start_time)
mp.register_event('shutdown', close_files)
mp.add_key_binding('kp_enter', 'expkeypress', keypress_handler)
