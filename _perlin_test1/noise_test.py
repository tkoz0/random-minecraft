from mclib.jrand import JavaRandom
import sys
import math

# noise_test.py <seed> <file> <height> <width>

def randomNoise(rand,h,w):
    buffer = [0]*(h*w)
    rand.nextBytes(buffer)
    buffer = [256 + b if b < 0 else b for b in buffer] # signed to unsigned
    return bytes(buffer)

def randomUnitVector(rand):
    s = 0.0
    while s >= 1.0 or s == 0.0:
        x = 2.0 * rand.nextDouble() - 1.0
        y = 2.0 * rand.nextDouble() - 1.0
        s = x*x + y*y
    m = math.sqrt(s)
    return (x/m,y/m)

def interpolate(a0,a1,w):
    assert 0.0 <= w <= 1.0
    return (1.0-w)*a0 + w*a1

def interpolate(a0,a1,w):
    w = 3.0*w*w - 2.0*w*w*w
    return (1.0-w)*a0 + w*a1

# dot product of gradient vector at gx,gy with offset from grid point to x,y
def dotGridGradient(grid,gx,gy,x,y):
    dx,dy = x-gx, y-gy
    return dx*grid[gx][gy][0] + dy*grid[gx][gy][1]

def perlinValue(grid,x,y):
    x0,y0 = int(x), int(y)
    x1,y1 = x0+1, y0+1
    sx,sy = x-x0, y-y0
    n0 = dotGridGradient(grid,x0,y0,x,y)
    n1 = dotGridGradient(grid,x1,y0,x,y)
    ix0 = interpolate(n0,n1,sx)
    n0 = dotGridGradient(grid,x0,y1,x,y)
    n1 = dotGridGradient(grid,x1,y1,x,y)
    ix1 = interpolate(n0,n1,sx)
    return interpolate(ix0,ix1,sy)

# scale should be between 0 and 1
def perlinNoise(rand,h,w,freq):
    grid = [[None]*(w+1) for _ in range(h+1)]
    for hh in range(h+1): # random gradient vectors for each grid point
        for ww in range(w+1):
            grid[hh][ww] = randomUnitVector(rand)
    values = [0.0]*(h*w)
    for hh in range(h):
        for ww in range(w):
            x = hh*freq # hh+0.5
            y = ww*freq # ww+0.5
            value = perlinValue(grid,x,y)
            values[hh*w+ww] = value
    return values

def perlinFractalNoise(rand,h,w,freq=[1.0,0.5,0.25,0.125,0.0625,0.03125,0.015625,0.0078125],amp=[1.0,2.0,4.0,8.0,16.0,32.0,64.0,128.0]):
    values = [0.0]*(h*w)
    for fi,freq in enumerate(freq):
        perlin_values = perlinNoise(rand,h,w,freq)
        for i,v in enumerate(perlin_values):
            values[i] += amp[fi]*v
    lo,hi = min(values),max(values)
    print(lo,hi)
    values = [(v-lo)/(hi-lo+0.000001) for v in values] # scale to range [0,1)
    return bytes(int(256.0*v) for v in values)

rand = JavaRandom(int(sys.argv[1]))
h,w = sys.argv[3],sys.argv[4]
h = int(h)
w = int(w)
assert 0 < h <= 2048 # sane limits
assert 0 < w <= 2048
outf = open(sys.argv[2],'wb')
outf.write(('P5\n%d %d\n255\n'%(w,h)).encode())
freq = [0.015625,0.0078125,0.00390625,0.001953125]
amp = [1.0,2.0,4.0,8.0]
outf.write(perlinFractalNoise(rand,h,w,freq,amp))
outf.flush()
outf.close()
