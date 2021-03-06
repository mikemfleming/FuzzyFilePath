"""
	manages current state, which include: current filename of view, current project folder if any, project folder
	does not manage settings, but sends a message with the current project folder to settings
"""
ID = "CurrentState"


import sublime
import os
import re
import FuzzyFilePath.common.settings as settings
from FuzzyFilePath.project.FileCache import FileCache
import FuzzyFilePath.common.path as Path
import FuzzyFilePath.common.verbose as logger


is_enabled = False # set to true when plugin has initially updated settings
valid = False # if the current view is a valid project file
file_caches = {} # caches any file indices of each project folder
state = {} # saves current views state like filename, project_folder, cache and settings


def update():
	""" call me anytime a new view has gained focus. This includes activation of a new window, which should have an
		active view
	"""
	global valid, is_enabled

	if not is_enabled:
		return False

	temp = False
	window = sublime.active_window()
	if window is None:
		logger.log(ID, "Abort -- no active window")
		valid = False
		return valid
	view = window.active_view()
	if view is None:
		logger.log(ID, "Abort -- no active view")
		valid = False
		return valid
	file = Path.posix(view.file_name())
	if not file:
		logger.log(ID, "Abort -- view has not yet been saved to file")
		temp = True
		return valid
	if state.get("file") == file:
		logger.log(ID, "Abort -- view already updated")
		return valid

	folders = list(map(lambda f: Path.posix(f), window.folders()))
	project_folder = get_closest_folder(file, folders)

	if project_folder is False:
		logger.log(ID, "Abort -- file not part of a project (folder)")
		valid = False
		return valid

	# notify settings of new project folder
	if state.get("project_folder") != project_folder:
		settings.update_project_settings()
	settings.update_project_folder_settings(project_folder)

	valid = True

	# @TODO cache
	state["file"] = file
	state["directory"] = sanitize_directory(file, project_folder)
	state["folders"] = folders
	state["project_folder"] = project_folder
	state["cache"] = get_file_cache(project_folder)

	logger.start_block()
	logger.verbose(ID, "Updated", state)

	return valid


def sanitize_directory(file_name, project_folder):
	directory = re.sub(project_folder, "", file_name)
	directory = re.sub("^[\\\\/\.]*", "", directory)
	return os.path.dirname(directory)


def get_project_directory():
	return state.get("project_folder")


def get_directory():
	return state.get("directory")


def update_settings():
	if state.get("project_folder"):
		# we expect settings to be already updated and thus only update the project folder settings
		settings.update_project_folder_settings(state.get("project_folder"))


def is_valid():
	return valid


def enable():
	global is_enabled
	is_enabled = True


def get_file_cache(folder):
	if not folder in file_caches:
		valid_file_extensions = get_valid_extensions(settings.get("trigger"))
		logger.verbose(ID, "Build cache for " + folder + " (", valid_file_extensions , ") excluding", settings.get("exclude_folders"))
		file_caches[folder] = FileCache(valid_file_extensions, settings.get("exclude_folders"), folder)

	return file_caches.get(folder)


def rebuild_filecache(folder=None):
	if not folder:
		if state.get("cache"):
			logger.verbose(ID, "rebuild current filecache of folder " + state.get("project_folder"))
			state.get("cache").rebuild()
		return

	folder = Path.posix(folder)
	if not folder in file_caches:
		logger.log(ID, "Abort rebuild filecache -- folder " + folder + " not cached")
		return False

	logger.verbose(ID, "rebuild current filecache of folder " + folder)
	file_caches.get(folder).rebuild()


def search_completions(needle, project_folder, valid_extensions, base_path=False):
	return state.get("cache").search_completions(needle, project_folder, valid_extensions, base_path)


def find_file(file_name):
	return state.get("cache").find_file(file_name)


def get_valid_extensions(triggers):
	""" Returns a list of all file extensions found in scope triggers """
	extensionsToSuggest = []
	for scope in triggers:
	    ext = scope.get("extensions", [])
	    extensionsToSuggest += ext
	# return without duplicates
	return list(set(extensionsToSuggest))


def get_closest_folder(filepath, directories):
	"""
		Returns the (closest) project folder associated with the given file or False

		# the rational behind this is as follows:
		In nodejs we might work with linked node_modules. Each node_module is a separate project. Adding nested folders
		to the root document thus owns the file and defines the project scope. A separated folder should never reach
		out (via files) on its parents folders.
	"""
	folderpath = os.path.dirname(filepath)
	current_folder = folderpath
	closest_directory = False
	for folder in directories:
		distance = current_folder.replace(folder, "")
		if len(distance) < len(folderpath):
			folderpath = distance
			closest_directory = folder
	return closest_directory
