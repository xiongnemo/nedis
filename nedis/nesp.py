class NESP:

    class NedisObject:
        def __init__(self, value):
            self.value = value

        def __repl__(self):
            return f"{self.__class__}={self.value}"
        
        def serialize(self) -> bytes:
            return f"{self.__nesp_serialization__()}".encode('utf-8')
        
        def __nesp_serialization__(self):
            return f"{self.__class__}={self.value}"
        
        def __nesp_deserialization__(self, value):
            self.value = value

        @staticmethod
        def from_serialized(data: str):
            pass

        @staticmethod
        def from_serialized_trailing(data: str):
            pass

        def __eq__(self, other):
            return self.value == other.value

    @staticmethod
    def construct_from_python_type(value) -> NedisObject:
        if type(value) == int:
            return NESP.Integer(value)
        if type(value) == str:
            return NESP.BulkString(value)
        if type(value) == list:
            return NESP.Array(value)
        if type(value) == bool:
            return NESP.Boolean(value)
        if type(value) == float:
            return NESP.Double(value)
        if type(value) == dict:
            return NESP.Map(value)
        if type(value) == set:
            return NESP.Set(value)
        if type(value) == tuple:
            return NESP.Push(value)
        if value == None:
            return NESP.Null()
        return NESP.SimpleString(value)

    @staticmethod
    def serialize(obj: NedisObject) -> bytes:
        return f"{obj.__nesp_serialization__()}".encode('utf-8')
    
    @staticmethod
    def determine_serialization_type(data: str) -> NedisObject:
        match data[0]:
            case '+':
                obj = NESP.SimpleString
            case '-':
                obj = NESP.SimpleError
            case ':':
                obj = NESP.Integer
            case '$':
                obj = NESP.BulkString
            case '*':
                obj = NESP.Array
            case '_':
                obj = NESP.Null
            case '#':
                obj = NESP.Boolean
            case ',':
                obj = NESP.Double
            case '(':
                obj = NESP.BigNumber
            case '!':
                obj = NESP.BulkError
            case '=':
                obj = NESP.VerbatimString
            case '%':
                obj = NESP.Map
            case '~':
                obj = NESP.Set
            case '>':
                obj = NESP.Push
            case _:
                raise ValueError(f'Unknown serialization type: {data[0]}')
        return obj

    @staticmethod
    def deserialize(data: bytes | str) -> NedisObject:
        if type(data) == bytes:
            data = data.decode('utf-8')
        obj: NESP.NedisObject = None
        obj = NESP.determine_serialization_type(data)
        return obj.from_serialized(data)
    
    @staticmethod
    def deserialize_trailing(data: bytes | str) -> tuple[NedisObject, str]:
        if type(data) == bytes:
            data = data.decode('utf-8')
        obj: NESP.NedisObject = None
        obj = NESP.determine_serialization_type(data)
        return obj.from_serialized_trailing(data)

    class SimpleString(NedisObject):
        def __init__(self, value):
            super().__init__(value)

        def __nesp_serialization__(self):
            return f'+{self.value}\r\n'
        
        @staticmethod
        def from_serialized(data: str):
            return NESP.SimpleString(data[1:-2])
        
        @staticmethod
        def from_serialized_trailing(data: str):
            end = data.find('\r\n') + 2
            return NESP.SimpleString.from_serialized(data[:end]), data[end:]
        
    class SimpleError(NedisObject):
        def __init__(self, value):
            super().__init__(value)

        def __nesp_serialization__(self):
            return f'-{self.value}\r\n'
        
        @staticmethod
        def from_serialized(data: str):
            return NESP.SimpleError(data[1:-2])
        
        @staticmethod
        def from_serialized_trailing(data: str):
            end = data.find('\r\n') + 2
            return NESP.SimpleError.from_serialized(data[:end]), data[end:]
        
    class Integer(NedisObject):
        def __init__(self, value):
            super().__init__(value)

        def __nesp_serialization__(self):
            return f':{self.value}\r\n'
        
        @staticmethod
        def from_serialized(data: str):
            return NESP.Integer(int(data[1:-2]))
        
        @staticmethod
        def from_serialized_trailing(data: str):
            end = data.find('\r\n') + 2
            return NESP.Integer.from_serialized(data[:end]), data[end:]
        
    class BulkString(NedisObject):
        def __init__(self, value):
            super().__init__(value)

        def __nesp_serialization__(self):
            if self.value == None:
                return f'$-1\r\n'
            return f'${len(self.value)}\r\n{self.value}\r\n'
        
        @staticmethod
        def from_serialized(data: str) -> str:
            if data == '$-1\r\n':
                return NESP.BulkString(None)
            prefix = data.split('\r\n')[0] + '\r\n'
            return NESP.BulkString(data[:-2].removeprefix(prefix))
        
        @staticmethod
        def from_serialized_trailing(data: str):
            if data.startswith('$-1\r\n'):
                return NESP.BulkString(None), data[len('$-1\r\n'):]
            string_length = int(data[1:data.find('\r\n')])
            prefix = f'${string_length}\r\n'
            end = len(prefix) + 2 + string_length
            return NESP.BulkString.from_serialized(data[:end]), data[end:]
        
    class Array(NedisObject):
        def __init__(self, value):
            super().__init__(value)

        def __nesp_serialization__(self):
            if self.value == None:
                return f'*-1\r\n'
            return f'*{len(self.value)}\r\n{"".join([x.serialize().decode('utf-8') for x in self.value])}'
        
        @staticmethod
        def from_serialized(data: str):
            if data == '*-1\r\n':
                return NESP.Array(None)
            array_len = int(data[:data.find('\r\n')][1:])
            prefix = f'*{array_len}\r\n'
            data = data.removeprefix(prefix)
            parts = []
            while data:
                obj, data = NESP.deserialize_trailing(data)
                parts.append(obj)
            
            return NESP.Array(parts)
        
        @staticmethod
        def from_serialized_trailing(data: str):
            if data.startswith('*-1\r\n'):
                return NESP.Array(None), data[len('*-1\r\n'):]
            array_len = int(data[:data.find('\r\n')][1:])
            prefix = f'*{array_len}\r\n'
            data = data.removeprefix(prefix)
            parts = []
            for _ in range(array_len):
                obj, data = NESP.deserialize_trailing(data)
                parts.append(obj)
            return NESP.Array(parts), data
        
    class Null(NedisObject):
        def __init__(self):
            super().__init__(None)

        def __nesp_serialization__(self):
            return f'_\r\n'
        
        @staticmethod
        def from_serialized(data: str):
            return NESP.Null()
        
        @staticmethod
        def from_serialized_trailing(data: str):
            return NESP.Null(), data[3:]
        
    class Boolean(NedisObject):
        def __init__(self, value):
            super().__init__(value)

        def __nesp_serialization__(self):
            return f'#{"t" if self.value else "f"}\r\n'
        
        @staticmethod
        def from_serialized(data: str):
            return NESP.Boolean(data[1:-2] == 't')
        
        @staticmethod
        def from_serialized_trailing(data: str):
            return NESP.Boolean.from_serialized(data[:4]), data[4:]
        
    class Double(NedisObject):
        def __init__(self, value):
            super().__init__(value)

        def __nesp_serialization__(self):
            return f',{self.value}\r\n'
        
        @staticmethod
        def from_serialized(data: str):
            return NESP.Double(float(data[1:-2]))
        
        @staticmethod
        def from_serialized_trailing(data: str):
            end = data.find('\r\n') + 2
            return NESP.Double.from_serialized(data[:end]), data[end:]