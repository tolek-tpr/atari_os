import sys, os

IMPLIED = "IMP"             # DEX
ACCUMULATOR = "ACC"         # ASL A
IMMEDIATE = "IMM"           # LDA #$55
ABSOLUTE = "ABS"            # LDA $2000
INDIRECT = "IND"            # BEQ :label
STACK = "STK"               # PHA (PH* PL*)
ZERO_PAGE = "ZPG"           # LDA $81
ABSOLUTE_X = "ABX"          # LDA $2000,X
ABSOLUTE_Y = "ABY"          # LDA $2000,Y
ZERO_PAGE_X = "ZPX"         # LDA $55,X
ZERO_PAGE_Y = "ZPY"         # LDA $55,Y
ABSOLUTE_INDIRECT = "ABI"   # JMP ($1020)
INDIRECT_Y = "INY"          # LDA ($55),Y
INDIRECT_X = "INX"          # LDA ($55, X)

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
    "NOP": { IMPLIED: 0xea },
    "STA": { ZERO_PAGE: 0x85, ZERO_PAGE_X: 0x95, ABSOLUTE: 0x8d, ABSOLUTE_X: 0x9d, ABSOLUTE_Y: 0x99, INDIRECT_X: 0x81, INDIRECT_Y: 0x91 },
    "CMP": { IMMEDIATE: 0xc9, },
    "BNE": { INDIRECT: 0xd0, }
}

def isLabel(s):
    return type(s) == str and s.__contains__(':')

def isIndexed(s, register):
    return s.__contains__(',') and s.__contains__(register)

def isIndirect(s):
    return s.__contains__('(') and s.__contains__(')')

def isImmediate(s):
    return s.__contains__('#')

def isZeroPage(n):
    return n <= 255

def isStack(s):
    return ["TSX", "TXS", "PHA", "PLA", "PHP", "PLP"].__contains__(s)

def rawToOperand(s):
    s = s.strip('()#, XYA')
    if s.__contains__('$'):
        return int(s[1:], 16)
    else:
        return int(s)

def lsb(n):
    return n & 255

def msb(n):
    return n >> 8

def isWord(n):
    return n > 255

def numberToBytes(n):
    if isWord(n):
        return [ lsb(n), msb(n) ]
    else:
        return [ lsb(n) ]

def parse(line):
    items = line.strip().split(" ")
    if len(items) > 0 and isLabel(items[0]):
        label, items = items[0].strip(": ").upper(), items[1:]
    else:
        label = None

    if len(items) == 0:
        return label, []
    
    operator = items[0].strip().upper()

    if len(items) == 1:
        if isStack(operator):
            return label, [OPCODES[operator][STACK]]
        else:
            return label, [OPCODES[operator][IMPLIED]]

    raw = items[1].strip().upper()
    if isLabel(raw):
        return label, [OPCODES[operator][INDIRECT], raw.strip(': ').upper()]

    operand = rawToOperand(raw)
    if len(items) == 2:
        raw = items[1]
    else:
        raw = None

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
    elif isWord(operand):
        mode = ABSOLUTE
    else:
        mode = ZERO_PAGE
    
    bytes = [OPCODES[operator][mode]]
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
        label, op = parse(line)
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
            addr = labels.get(byte) - pc
            if addr < 0:
                addr = 256 + addr
            bytes[pc] = addr

    file_out = 'build/' + file_out
    print(file_out)
    output = open(file_out, "wb")
    output.write(bytearray(bytes))
    output.close()

#try:
if len(sys.argv) > 4:
    if sys.argv[1] == "--in" or sys.argv[1] == "-i":
        if sys.argv[3] == "--out" or sys.argv[3] == "-o":
            main(sys.argv[2], sys.argv[4])
            try:
                os.mkdir("build")
            except:
                print("Error while making drectory build")
    else:
        print("Please specify the in and out file")
else:
    print("Please specify the in and out file")

#except:
    #print("Please enter a in and out file name")