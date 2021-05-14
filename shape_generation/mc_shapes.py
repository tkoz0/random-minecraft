'''
For even diameter circles, center at block corner. For odd diameter circles,
center at block center. Use block centers to calculate distance for determining
if it is included as inside the circle.
'''

def circle(d):
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

if __name__ == '__main__':
    import sys
    import png
    C = circle(int(sys.argv[1]))
    if len(sys.argv) > 2:
        arr = [[0 if b else 255 for b in row] for row in C]
        img = png.from_array(arr,'L;8')
        img.save(sys.argv[2])
    else:
        for row in C:
            print(''.join('X' if b else ' ' for b in row))
