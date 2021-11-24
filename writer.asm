start
    PLA
    LDX #0
print
    LDA 1553,X
    CMP #0
    BEQ end
    STA 40001,X
    INX
    BNE print
end
    RTS
_text
    DATA 65,66,67,0