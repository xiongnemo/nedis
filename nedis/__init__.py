import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s.%(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from .nesp import NESP

import traceback

from enum import IntEnum

class NedisLifecycleState(IntEnum):
    Starting = 0
    Running = 1
    ShuttingDown = 2
    Shutdown = 3

class Nedis:
    def __init__(self):
        self.state = NedisLifecycleState.Starting
        self.data = {}  # The in-memory database
        logger.info('Nedis is Starting...')
        # loads the last snapshot from disk
        self.load()
        self.state = NedisLifecycleState.Running

    def set(self, key, value):
        self.data[key] = value
        return 'OK'

    def get(self, key):
        return self.data.get(key, None)

    def delete(self, *keys):
        acc = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                acc += 1
        return acc

    def info(self):
        return f'Nedis version 0.1.0\nState: {self.state.name}\n'

    def keys(self):
        return self.data.keys()

    def flush(self):
        self.data = {}

    def exists(self, key):
        return key in self.data
    
    def process(self, command) -> NESP.NedisObject:
        try:
            command = command.decode('utf-8')
            if command[0] == '*':
                # command is from redis-cli
                parts = [value.value for value in NESP.Array.from_serialized(command).value]
                logger.info(f'Processing redis command: {parts}')
            else:
                parts = command.split()
                logger.info(f'Processing ascii command: {parts}')
            action = parts[0].lower()
            mutation_mapping = {
                'del': 'delete',
            }
            action = mutation_mapping.get(action, action)
            try:
                func = self.__getattribute__(action)
                return NESP.construct_from_python_type(func(*parts[1:]))
            except AttributeError:
                traceback.print_exc()
                return NESP.SimpleError(f'ERR unknown command \'{parts[0]}\'')
        except Exception as e:
            traceback.print_exc()
            return NESP.SimpleError(f'ERR {e.__str__()}')
        
    
    def dump(self):
        import pickle
        with open('nedis.pickle', 'wb') as f:
            pickle.dump(self.data, f)
        logger.info('DB saved on disk')

    def load(self):
        import pickle
        try:
            with open('nedis.pickle', 'rb') as f:
                self.data = pickle.load(f)
            logger.info('DB loaded from disk')
        except FileNotFoundError:
            logger.info('No DB snapshot found, starting with an empty DB')
    
    def shutdown(self):
        if self.state >= NedisLifecycleState.ShuttingDown:
            return
        self.state = NedisLifecycleState.ShuttingDown
        logger.info("User requested shutdown...")
        logger.info('Saving the final NDB snapshot before exiting.')
        self.dump()
        logger.info("Nedis is now ready to exit, bye bye...")
        self.state = NedisLifecycleState.Shutdown

