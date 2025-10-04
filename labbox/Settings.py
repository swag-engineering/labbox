import json
import os

class MetaSettings(type):
	"""
	Initialize module settings from json
	"""

	class Wrapper(object):
		def __init__(self, args_dict):
			for key, value in args_dict.items():
				if isinstance(value, dict):
					self.__dict__[key] = self.__class__(value)
				else:
					self.__dict__[key] = value

	_instance = None
	root_path = os.path.dirname(__file__)
	icons_folder = os.path.join(root_path, "icons")
	gifs_folder = os.path.join(root_path, "gifs")
	settings_path = os.path.join(root_path,
		os.path.join("settings", "settings.json"))
	with open(settings_path, "rb") as data_file:              # should the path be automatically generated?
		_data = json.load(data_file)
	if not _instance:
		_instance = Wrapper(_data)

	def __getattr__(cls, name):
		return getattr(MetaSettings._instance, name)

	@staticmethod
	def byObject(obj):
		return getattr(MetaSettings._instance, type(obj).__name__)

	@staticmethod
	def _update(dump, obj):
		for key, value in dump.items():
			if isinstance(value, dict):
				dump[key] = MetaSettings._update(value, getattr(obj, key))
				continue
			dump[key] = getattr(obj, key)
		return dump

	@staticmethod
	def saveSettings():
		MetaSettings._data = MetaSettings._update(
			MetaSettings._data, MetaSettings._instance
		)
		with open("settings/settings.json", "w") as out_data_file:
			json.dump(MetaSettings._data, out_data_file, indent=4, sort_keys=True)  # enable pretty printing


class Settings(metaclass=MetaSettings):
	pass
