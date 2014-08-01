# Andrew Edwards -- almostimplemented.com
# =======================================
# A checkers agent implementaiton based
# on Arthur Samuel's historic program.
#
# Last updated: July 21, 2014

# Constants
BLACK, WHITE = 0, 1
VALID_SQUARES = 0x7FBFDFEFF

# Feature functions
def adv(board): # Advancement
    """
        The parameter is credited with 1 for each passive man in the
        fifth and sixth rows (counting in passive's direction) and
        debited with 1 for each passive man in the third and fourth
        rows.
    """
    passive = board.passive

    rows_3_and_4 =   0x1FE00
    rows_5_and_6 = 0x3FC0000
    if passive == WHITE:
        rows_3_and_4, rows_5_and_6 = rows_5_and_6, rows_3_and_4

    bits_3_and_4 = rows_3_and_4 & board.pieces[passive]
    bits_5_and_6 = rows_5_and_6 & board.pieces[passive]
    return bin(bits_5_and_6).count("1") - bin(bits_3_and_4).count("1")

def back(board): # Back Row Bridge
    """
        The parameter is credited with 1 if there are no active kings
        on the board and if the two bridge squares (1 and 3, or 30 and
        32) in the back row are occupied by passive pieces.
    """
    active = board.active
    passive = board.passive
    if active == BLACK:
        if board.backward[BLACK] != 0:
            return 0
        back_row_bridge = 0x480000000
    else:
        if board.forward[WHITE] != 0:
            return 0
        back_row_bridge = 0x5

    if bin(back_row_bridge & board.pieces[passive]).count('1') == 2:
        return 1
    return 0

def cent(board): # Center Control I
    """
        The parameter is credited with 1 for each of the following
        squares: 11, 12, 15, 16, 20, 21, 24, 25 which is occupied by
        a passive man.
    """
    passive = board.passive
    if passive == WHITE:
        center_pieces = 0xA619800
    else:
        center_pieces = 0xCC3280

    return bin(board.pieces[passive] & center_pieces).count("1")

def cntr(board): # Center Control II
    """
        The parameter is credited with 1 for each of the following
        squares: 11, 12, 15, 16, 20, 21, 24, 25 that is either
        currently occupied by an active piece or to which an active
        piece can move.
    """
    active = board.active
    if active == BLACK:
        center_pieces = 0xA619800
    else:
        center_pieces = 0xCC3280

    active_center_count = bin(board.pieces[active] & center_pieces).count("1")

    destinations = reduce(lambda x, y: x|y,
                          [(m ^ (m & board.pieces[active])) for m in board.get_moves()])

    active_near_center_count = bin(destinations & center_pieces).count("1")

    return active_center_count + active_near_center_count

def deny(board): # Denial of Occupancy
    """
        The parameter is credited 1 for each square defined in MOB if
        on the next move a piece occupying this square could be
        captured without exchange.
    """
    rf = board.right_forward()
    lf = board.left_forward()
    rb = board.right_backward()
    lb = board.left_backward()

    moves =  [0x11 << i for (i, bit) in enumerate(bin(rf)[::-1]) if bit == '1']
    moves += [0x21 << i for (i, bit) in enumerate(bin(lf)[::-1]) if bit == '1']
    moves += [0x11 << i - 4 for (i, bit) in enumerate(bin(rb)[::-1]) if bit == '1']
    moves += [0x21 << i - 5 for (i, bit) in enumerate(bin(lb)[::-1]) if bit == '1']

    destinations =  [0x10 << i for (i, bit) in enumerate(bin(rf)[::-1]) if bit == '1']
    destinations += [0x20 << i for (i, bit) in enumerate(bin(lf)[::-1]) if bit == '1']
    destinations += [0x10 << i - 4 for (i, bit) in enumerate(bin(rb)[::-1]) if bit == '1']
    destinations += [0x20 << i - 5 for (i, bit) in enumerate(bin(lb)[::-1]) if bit == '1']

    denials = 0

    for move, dest in zip(moves, destinations):
        B = board.peek_move(move)
        active = B.active
        ms_taking = []
        ds = []
        if (B.forward[active] & (dest >> 4)) != 0 and (B.empty & (dest << 4)) != 0:
            ms_taking.append((-1)*((dest >> 4) | (dest << 4)))
            ds.append(dest << 4)
        if (B.forward[active] & (dest >> 5)) != 0 and (B.empty & (dest << 5)) != 0:
            ms_taking.append(((-1)*(dest >> 5) | (dest << 5)))
            ds.append(dest << 5)
        if (B.backward[active] & (dest << 4)) != 0 and (B.empty & (dest >> 4)) != 0:
            ms_taking.append((-1)*((dest << 4) | (dest >> 4)))
            ds.append(dest >> 4)
        if (B.backward[active] & (dest << 5)) != 0 and (B.empty & (dest >> 4)) != 0:
            ms_taking.append((-1)*((dest << 5) | (dest >> 5)))
            ds.append(dest >> 5)

        if not ms_taking:
            continue
        else:
            for m, d in zip(ms_taking, ds):
                C = B.peek_move(m)
                if C.active == active:
                    denials += 1
                    continue
                if not C.takeable(d):
                    denials += 1

    return denials


def kcent(board): # King Center Control
    """
        The parameter is credited with 1 for each of the following
        squares: 11, 12, 15, 16, 20, 21, 24, and 25 which is occupied
        by a passive king.
    """
    passive = board.passive
    if passive == WHITE:
        center_pieces = 0xA619800
        passive_kings = board.forward[WHITE]
    else:
        center_pieces = 0xCC3280
        passive_kings = board.backward[BLACK]

    return bin(passive_kings & center_pieces).count("1")


def mob(board): # Total Mobility
    """
        The parameter is credited with 1 for each square to which the
        active side could move one or more pieces in the normal fashion
        disregarding the fact that jump moves may or may not be
        available.
    """
    rf = board.right_forward()
    lf = board.left_forward()
    rb = board.right_backward()
    lb = board.left_backward()

    destinations =  [0x10 << i for (i, bit) in enumerate(bin(rf)[::-1]) if bit == '1']
    destinations += [0x20 << i for (i, bit) in enumerate(bin(lf)[::-1]) if bit == '1']
    destinations += [0x10 << i - 4 for (i, bit) in enumerate(bin(rb)[::-1]) if bit == '1']
    destinations += [0x20 << i - 5 for (i, bit) in enumerate(bin(lb)[::-1]) if bit == '1']

    return bin(reduce(lambda x, y: x|y, destinations)).count("1")

def mobil(board): # Undenied Mobility
    """
        The parameter is credited with the difference between MOB and
        DENY.
    """
    return mob(board) - deny(board)

def move(board): # Move
    """
        The parameter is credited with 1 if pieces are even with a
        total piece count (2 for men, and 3 for kings) of less than 24,
        and if an odd number of pieces are in the move system, defined
        as those vertical files starting with squares 1, 2, 3, and 4.
    """

def thret(board): # Threat
    """
        The parameter is credited with 1 for each square to which an
        active piece may be moved and in doing so threaten to capture
        a passive piece on a subsequent move.
    """

if __name__ == '__main__':
    import checkers
    B = checkers.CheckerBoard()
    for _ in [1]*10:
        B.make_move(B.get_moves()[0])
    print deny(B)
