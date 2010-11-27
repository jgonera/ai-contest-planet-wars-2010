import logging

log = logging.getLogger(__name__)

store = {}
stats = {}

def memoize(func):
	def wrapper(*args, **kwargs):
		# don't depend on dict's order
		kwargs_sorted = [ i + ':' + repr(kwargs[i]) for i in sorted(kwargs.iterkeys()) ]
		key = ','.join([repr(func), repr(args), repr(kwargs_sorted)])
		#log.debug(key)
		
		if not stats.has_key(func.__name__):
			stats[func.__name__] = {'hits': 0, 'misses': 0}
		
		if store.has_key(key):
			#log.debug("cache hit")
			stats[func.__name__]['hits'] += 1
			return store[key]
		else:
			#log.debug("cache miss")
			stats[func.__name__]['misses'] += 1
			store[key] = func(*args, **kwargs)
			return store[key]
	return wrapper
