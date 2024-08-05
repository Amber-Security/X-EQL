from ply.lex import lex
from ply.yacc import yacc


# --- Tokenizer

tokens = ['SYM', 'L', 'R', 'AL', 'AR', 'COLON', 'SEQUENCE', 'BY', 'COMMA']

t_ignore = ' \t'

t_L = r'\('
t_R = r'\)'
t_AL = r'\['
t_AR = r'\]'
t_COLON = r':'
t_SEQUENCE = r'sequence'
t_BY = r'by'
t_COMMA = r','

def t_SYM(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value == "sequence": t.type = "SEQUENCE"
    if t.value == "by": t.type = "BY"
    return t

def t_ignore_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')

def t_error(t):
    print(f'Illegal character {t.value[0]!r}')
    t.lexer.skip(1)

lexer = lex()

# --- Parser

def p_rule(p):
    '''
    rule    : head seq
    '''
    # print("rule", len(p))
    head, seq = p[1], p[2]
    p[0] = tuple(['rule', head, seq])

def p_head(p):
    '''
    head    : SYM COLON SEQUENCE
            | SYM COLON SEQUENCE commonkeys
    '''
    # print("head", len(p))
    if len(p) == 5:
        p[0] = tuple(['head', p[1], p[3], p[4]])
    else:
        p[0] = tuple(['head', p[1], p[3]])

def p_commonkeys(p):
    '''
    commonkeys  : BY farr
    '''
    # print("commonkeys", len(p))
    p[0] = ('by', p[2])

def p_farr(p):
    '''
    farr    : farr COMMA SYM
            | SYM
    '''
    # print("farr", len(p))
    if len(p) == 4:
        p[0] = p[1] + (p[3],)
    else:
        p[0] = (p[1],)

def p_seq(p):
    '''
    seq : seq event
        | event
        | seq AL denseblock AR
        | AL denseblock AR
    '''
    # print("seq", len(p))
    if len(p) == 3:
        p[0] = p[1] + (p[2],)
        return
    if len(p) == 2:
        p[0] = (p[1],)
        return
    if len(p) == 5:
        p[0] = p[1] + (p[3],)
        return
    if len(p) == 4:
        p[0] = (p[2],)
        return

def p_denseblock(p):
    '''
    denseblock  : denseblock event
                | event
    '''
    # print("denseblock", len(p))
    if len(p) == 3:
        p[0] = p[1] + (p[2],)
    else:
        p[0] = (p[1],)

def p_event(p):
    '''
    event   : AL SYM AR BY constraint
            | AL SYM AR
    '''
    # print("event", len(p))
    if len(p) == 4:
        p[0] = ('event', p[2])
    else:
        p[0] = ('event', p[2], p[5])

def p_constraint(p):
    '''
    constraint  : constraint COMMA L farr R COLON SYM
                | L farr R COLON SYM
    '''
    # print("constraint", len(p))
    if len(p) == 6:
        p[0] = ((p[5], p[2]),)  # gid, fields
    else:
        p[0] = p[1] + ((p[7], p[4]),)

def p_error(p):
    print(f'Syntax error at {p.value!r}')

# Build the parser
def gen_parser():
    parser = yacc()
    return parser


if __name__ == '__main__':
    pass
