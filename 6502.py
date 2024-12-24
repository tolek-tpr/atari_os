import sys

IMPLIED = "implied"          # DEX
ACCUMULATOR = "accumulator"  # ASL A
IMMEDIATE = "#immediate"     # LDA #$55
ABSOLUTE = "absolute"        # LDA $2000
INDIRECT = "indirect"        # BEQ label
STACK = "stack"              # PHA (PH* PL*)
ZERO_PAGE = "zero page"      # LDA $81
ABSOLUTE_X = "absolute, X"   # LDA $2000,X
ABSOLUTE_Y = "absolute, Y"   # LDA $2000,Y
ZERO_PAGE_X = "zero page, X" # LDA $55,X
ZERO_PAGE_Y = "zero page, Y" # LDA $55,Y
ABSOLUTE_INDIRECT = "(absolute indirect)" # JMP ($1020)
INDIRECT_Y = "(indirect), Y"              # LDA ($55),Y
INDIRECT_X = "(indirect, X)"              # LDA ($55, X)

OPCODES = {
    "TXS": { STACK: 0x9a },
    "TSX": { STACK: 0xba },
    "PHA": { STACK: 0x48 },
    "PLA": { STACK: 0x68 },
    "PHP": { STACK: 0x08 },
    "PLP": { STACK: 0x28 },
    "JMP": { ABSOLUTE: 0x4c, INDIRECT: 0x6c },
    "JSR": { ABSOLUTE: 0x20 },
    "RTS": { IMPLIED: 0x60 },
    "LDA": { IMMEDIATE: 0xa9, ZERO_PAGE: 0xa5, ZERO_PAGE_X: 0xb5, ABSOLUTE: 0xad, ABSOLUTE_X: 0xbd, ABSOLUTE_Y: 0xb9, INDIRECT_X: 0xa1, INDIRECT_Y: 0xb1 },
    "LDX": { IMMEDIATE: 0xa2, ZERO_PAGE: 0xa6, ABSOLUTE: 0xae, ZERO_PAGE_Y: 0xb6, ABSOLUTE_Y: 0xbe, INDIRECT: 0xad },
    "NOP": { IMPLIED: 0xea },
    "STA": { ZERO_PAGE: 0x85, ZERO_PAGE_X: 0x95, ABSOLUTE: 0x8d, ABSOLUTE_X: 0x9d, ABSOLUTE_Y: 0x99, INDIRECT_X: 0x81, INDIRECT_Y: 0x91 },
    "CMP": { IMMEDIATE: 0xc9, },
    "INX": { IMPLIED: 0xe8 },
    "INY": { IMPLIED: 0xc8 },
    "BNE": { INDIRECT: 0xd0, },
    "BEQ": { INDIRECT: 0xf0, },
}

def isLabel(s):
    return s not in OPCODES and not str(s).replace('$', '').isnumeric()

def isIndexed(s, register):
    if type(s) == str and s.__contains__(',') and s.__contains__(register):
        return True
    else:
        return False

def isIndirect(s):
    return s.__contains__('(') and s.__contains__(')')

def isImmediate(s):
    return type(s) == str and s.__contains__('#')

def isZeroPage(n):
    return n <= 255 if str(n).isnumeric() else False

def isStack(s):
    return ["TSX", "TXS", "PHA", "PLA", "PHP", "PLP"].__contains__(s)

def rawToOperand(s):
    if type(s) != str:
        return None
    s = s.strip('()#, XYA')
    if s.__contains__('$'):
        return int(s[1:], 16)
    elif s.isnumeric():
        return int(s)
    else:
        return s

def lsb(n):
    return n & 255 if type(n) == int else n

def msb(n):
    return n >> 8

def isWord(n):
    if type(n) != int:
        return False
    return n > 255 

def numberToBytes(n):
    if type(n) == str:
        return n
    elif isWord(n):
        return [ lsb(n), msb(n) ]
    else:
        return [ lsb(n) ]

def error(msg, n, line):
    return Exception('Error at line {}: "{}"\n- {}'.format(n, line.strip(), msg))

def parse(n, line):
    items = line.strip().upper().split(" ")
    if len(items) > 0 and isLabel(items[0]):
        label, items = items[0], items[1:]
    else:
        label = None
    if len(items) == 0:
        return label, []

    operator = items[0]
    raw = None if len(items) != 2 else items[1]
    if label == "DATA":
        return label, list(map(rawToOperand, items[0].split(',')))
    if len(items) == 1:
        if isStack(operator):
            return label, [OPCODES[operator][STACK]]
        else:
            return label, [OPCODES[operator][IMPLIED]]

    
    operand = rawToOperand(raw)

    if isImmediate(raw):
        mode = IMMEDIATE
    elif isIndexed(raw, 'X'):
        if isZeroPage(operator):
            if isIndirect(raw):
                mode = INDIRECT_X
            else:
                mode = ZERO_PAGE_X
        else:
            mode = ABSOLUTE_X
    elif isIndexed(raw, 'Y'):
        if isZeroPage(operator):
            if isIndirect(raw):
                mode = INDIRECT_Y
            else:
                mode = ZERO_PAGE_Y
        else:
            mode = ABSOLUTE_Y
    elif isLabel(raw) and ["BEQ", "BNE"].__contains__(operator):
        mode = INDIRECT      
    elif isWord(operand):
        mode = ABSOLUTE
    else:
        mode = ZERO_PAGE

    if mode not in OPCODES[operator]:
        raise error('Operand "{}" was understood as "{}" but {} does not support {} addressing mode'.format(raw, operand, operator, mode), n, line)

    bytes = [OPCODES[operator][mode]]
    if type(operand) == str:
        bytes.append(operand)
    else:
        bytes.extend(numberToBytes(operand))
    return label, bytes

def main(file_in, file_out):
    pc = 0 # program counter, current position in memory
    bytes = [] # compiled program
    labels = {} # dict of labels and their position in memory
    
    input = open(file_in, 'r+')

    print('Line no | PC   | Label  | Program line | Machine code')
    print('--------|------|--------|--------------|------------------')
    for i, line in enumerate(input.readlines()):
        label, op = parse(i, line)
        if (label != None):
            labelStr, labels[label] = str(label), pc
        else:
            labelStr = ''
        print('{:7} | {:04} | {:6} | {:12} | {}'.format(i, pc, labelStr, line.strip().upper(), op))
        bytes.extend(op)
        pc += len(op)

    input.close()

    for pc, byte in enumerate(bytes):
        if (type(byte) == str):
            if byte not in labels:
                raise Exception('Label "{}" is used but not declared'.format(byte))
            addr = labels.get(byte) - pc
            if addr < 0:
                addr = 256 + addr
            bytes[pc] = addr

    print(bytes)
    output = open(file_out, "wb")
    output.write(bytearray(bytes))
    output.close()

if len(sys.argv) > 4:
    if sys.argv[1] == "--in" or sys.argv[1] == "-i":
        if sys.argv[3] == "--out" or sys.argv[3] == "-o":
            main(sys.argv[2], sys.argv[4])
    else:
        print("Please specify the in and out file")
else:
    print("Please specify the in and out file")