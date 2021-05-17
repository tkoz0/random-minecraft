'''
For even diameter circles, center at block corner. For odd diameter circles,
center at block center. Use block centers to calculate distance for determining
if it is included as inside the circle.
'''

def filled_circle(d):
    assert type(d) == int and d > 0
    if d % 2 == 0: # even, centered at block corner
        R = d//2
        # 1 quarter, r*r grid to be duplicated 4x
        # block r,c center is offset r+0.5,c+0.5 from circle center
        # (r+0.5)**2 + (c+0.5)**2 < R**2
        # r**2 + r + c**2 + c + 0.5 < R**2
        # 0.5 can be eliminated r,c,R are integers
        Q = [[r*r + r + c*c + c < R*R for c in range(R)] for r in range(R)]
        H = [row[::-1] + row for row in Q] # mirror horizontally
        return [row[:] for row in H[::-1]] + H
    else: # odd, centered at block center
        R = (d+1)//2
        # 1 quarter, including the vertical and horizontal diameters
        # the vertical and horizontal diameters are not duplicated
        # radius is R-0.5
        # block r,c center is offset r,c from circle center
        # r**2 + c**2 < (R-0.5)**2 = R**2 - R + 0.25
        # 0.25 should be changed to 1 since r,c,R are integers
        # or equivalently use <= R**2 - R
        Q = [[r*r + c*c <= R*R - R for c in range(R)] for r in range(R)]
        H = [row[1:][::-1] + row for row in Q] # mirror horizontally
        return [row[:] for row in H[1:][::-1]] + H

def open_circle(d):
    # similar to filled circle, but marks the edges by calculating
    # the largest value satisfying the equation
    assert type(d) == int and d > 0
    if d % 2 == 0:
        R = d//2
        Q = [[False for c in range(R)] for r in range(R)] # empty
        for i in range(R):
            # by symmetry, let r=i, then find maximum c
            # i**2 + i + c**2 + c < R**2
            # this can be rearranged to c**2 + c < R**2 - i**2 - i
            rhs = R*R - i*i - i
            c = 0
            while c**2 + c < rhs: c += 1
            c -= 1
            Q[i][c] = True
            Q[c][i] = True
        # same as above
        H = [row[::-1] + row for row in Q] # mirror horizontally
        return [row[:] for row in H[::-1]] + H
    else:
        R = (d+1)//2
        Q = [[False for c in range(R)] for r in range(R)] # empty
        for i in range(R):
            # by symmetry, let r=i, then find maximum c
            # r**2 + c**2 <= R**2 - R
            rhs = R*R - R - i*i
            c = 0
            while c*c <= rhs: c += 1
            c -= 1
            Q[i][c] = True
            Q[c][i] = True
        # same as above
        H = [row[1:][::-1] + row for row in Q] # mirror horizontally
        return [row[:] for row in H[1:][::-1]] + H

if __name__ == '__main__':
    import sys
    import png
    if sys.argv[2] == 'open':
        C = open_circle(int(sys.argv[1]))
    elif sys.argv[2] == 'filled':
        C = filled_circle(int(sys.argv[1]))
    else:
        assert 0
    if len(sys.argv) > 3:
        arr = [[0 if b else 255 for b in row] for row in C]
        img = png.from_array(arr,'L;8')
        img.save(sys.argv[3])
    else:
        for row in C:
            print(''.join('X' if b else ' ' for b in row))
