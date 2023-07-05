import dis


class ClientVerifier(type):
    def __init__(self, classname, bases, clsdict):
        methods = []
        for func in clsdict:
            try:
                opcodes_tuple = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for item in opcodes_tuple:
                    if item.opname == 'LOAD_GLOBAL':
                        if item.argval not in methods:
                            methods.append(item.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода')
            
        if 'get_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(classname, bases, clsdict)


class ServerVerifier(type):
    def __init__(self, classname, bases, clsdict):
        methods = []
        # attrs = []
        for func in clsdict:
            try:
                opcodes_tuple = dis.get_instructions(clsdict[func])
            except TypeError:
                pass
            else:
                for item in opcodes_tuple:
                    print(item)
                    if item.opname == 'LOAD_GLOBAL':
                        if item.argval not in methods:
                            methods.append(item.argval)
                    # if item.opname == 'LOAD_ATTR':
                    #     if item.argval not in attrs:
                    #         attrs.append(item.argval)
        print(methods)
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        if not ('SOCK_STREAM' in methods and 'AF_INET' in methods):
            raise TypeError('Некорректная инициализация сокета.')
        super().__init__(classname, bases, clsdict)





