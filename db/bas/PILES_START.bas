DEFINT A-Z
DECLARE SUB BigTextEnd (SndT, PlyT)
DECLARE SUB BigText (Factor%, S$, Y%, X%, C%)
DECLARE SUB Plot (Num, Y, X)
STACK 512
DIM Grid(20, 20) AS STRING * 1
DIM Colors(3) AS INTEGER
DIM Gcol(20, 20) AS INTEGER
DIM SHARED Text AS INTEGER
DIM SHARED Brick(65, 3)
DIM Pic&(8192)
DIM Temp(5000), TempVar(5000)
DIM SHARED SndT, PlyT

DIM A$(186)
L$ = CHR$(0) + CHR$(75)
R$ = CHR$(0) + CHR$(77)
U$ = CHR$(0) + CHR$(72)
D$ = CHR$(0) + CHR$(80)
F1$ = CHR$(0) + CHR$(59)
F2$ = CHR$(0) + CHR$(60)
F3$ = CHR$(0) + CHR$(61)
F4$ = CHR$(0) + CHR$(62)

PLAY "o0MBL8 "
DATA A16,MN, A2,o1,ML,E4.,D-32,C32,D2
DATA C16,ML,O0,B16,o0,D-16,MN,o1,C,C,o0,B2,A4.,ML,C16,G16
DATA F2,o1,C4.,o0,ML,B16,G16,A-4
DATA A4,B.,o1,MS,C16,MN,D.
DATA o0,ML,G16,B16,MN,o1,E,E,ML,E4,D8,ML,C16,E16,MN,E2
DATA T240
DATA o0,F2,ML,B2,B4,MN,E4,ML,A2
DATA A,MN,D,ML,G2,G4,MN,C4,F2
DATA T120
DATA o0,MS,E4,o1,ML,C2,C8
DATA MN,F8,ML,G16,F16,E16,D16
DATA C2,C8,MN,F8,ML,G16,F16,E16,D16

DATA o1,Co0,G,ML,A16,G16,F16,D16,MN,G,B-,o1,ML,C16,o0,B16,A16,G16,MN,o1,C2.
DATA ML,o0,G,B,o1,D,MN,D,D4,P8,G,G
DATA F+,F,F,E,P8,E-,ML,E,D,D,E,E,D,D,C,MN,C4,ML,o0,B.,A16,B16,MN,A4,P8,A
DATA o0,ML,D,B4.,A,G4,P8,D,B4,A,G4,P8,D,o1,E2.,MS,D,C,o0,B,A,G4,P4,P8,ML,E16

PRINT "Please Wait..."
FOR J = 1 TO 184
    READ A$(J)
NEXT J
LOCATE 1, 1: PRINT "             "

SndT = 1
PlyT = 1
Com$ = UCASE$(COMMAND$)

IF INSTR(Com$, "NOGR") THEN NoGr = 1
IF INSTR(Com$, "TEXT") THEN
    Text = 1
    GOTO Txt
END IF
IF Text <> 1 THEN
    ON ERROR GOTO Text
    IF INSTR(Com$, "MCGA") THEN
        SCREEN 13
        MCGA = 1
    ELSE
        SCREEN 9
    END IF
    ON ERROR GOTO 0
    FOR J = 1 TO 3
        LINE (1, 1)-(7, 7), J, BF
        LINE (1, 1)-(1, 7), 3 + J
        LINE (1, 1)-(7, 1), 3 + J
        LINE (7, 1)-(7, 7), 8 + J
        LINE (7, 7)-(2, 7), 8 + J
        GET (1, 1)-(7, 7), Brick(0, J)
    NEXT J
    IF MCGA <> 1 THEN
        PALETTE 4, 8
        PALETTE 5, 16
        PALETTE 6, 24
    ELSE
        PALETTE 4, 1376256
        PALETTE 5, 5376&
        PALETTE 6, 1381632
    END IF
    CLS
    IF MCGA <> 1 THEN
        WINDOW (0, 0)-(319, 199)
        WIDTH 40
    END IF
    IF MCGA <> 1 AND NoGr <> 1 THEN
        LINE (118, 100)-(208, 112), 15, B
        LOCATE 14, 16: PRINT "Please Wait"
        GET (119, 101)-(207, 111), Temp
        PUT (119, 101), Temp
        PAINT (122, 102), 7, 15
        PUT (119, 101), Temp, OR
        LINE (118, 100)-(208, 112), 8, B
        LINE (208, 101)-(208, 112), 15
        LINE (119, 112)-(208, 112), 15

        ON ERROR GOTO Ferror
        OPEN "Piles.NAS" FOR INPUT AS #1
        FOR J% = 0 TO 8192
            INPUT #1, Pic&(J%)
        NEXT J%
        CLOSE
    END IF
END IF

GOTO Start

Ferror:
RESUME Start:

Text:
RESUME Txt

Txt:
Text = 1
SCREEN 0
WIDTH 40
CLS

Start:

Score& = 0

ON ERROR GOTO 0

IF Text <> 1 THEN
    CLS
    IF MCGA <> 1 AND NoGr <> 1 THEN
        PUT (0, 0), Pic&(0)
        COLOR 9
        LINE (160, 0)-(160, 160), 9
        LINE (0, 160)-(160, 160), 9
    END IF
    LINE (0, 0)-(159, 159), 0, BF
ELSE
    FOR J = 1 TO 24
        LOCATE 25, 1
        PRINT SPACE$(34);
    NEXT J
END IF

RANDOMIZE TIMER

FOR X = 1 TO 20
    FOR Y = 1 TO 20
        Grid(X, Y) = " "
        Gcol(X, Y) = 0
    NEXT Y
NEXT X

FOR J = 1 TO 20
    LOCATE J, 1
    PRINT SPACE$(20)
NEXT J

COLOR 9
LOCATE 1, 25
PRINT "ÚÄÄÄÄÄÄÄÄÄÄÄÄÄ¿"
LOCATE 2, 25
PRINT "³  S C O R E  ³"
LOCATE 3, 25
PRINT "ÃÄÄÄÄÄÄÄÄÄÄÄÄÄ´"
LOCATE 4, 25
PRINT USING "³ ###,###,### ³"; Score
LOCATE 5, 25
PRINT "ÀÄÄÄÄÄÄÄÄÄÄÄÄÄÙ"
IF Text <> 1 THEN
    LINE (197, 6)-(197, 19), 1
    LINE (197, 5)-(306, 5), 1
    LINE (197, 22)-(197, 35), 1
    LINE (197, 21)-(306, 21), 1
    LINE (197, 37)-(308, 37), 1
    LINE (309, 37)-(309, 5), 1
    COLOR 1
    LOCATE 2, 26
    GET (198, 8)-(305, 15), TempVar
    PRINT "  S C O R E  "
    GET (198, 8)-(305, 15), Temp
    PUT (199, 9), Temp, OR
    PUT (198, 8), TempVar, OR
END IF
LOCATE 6, 