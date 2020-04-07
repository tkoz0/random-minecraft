import json,gzip,sys,os
from nbt2json import nbt2json
from mca2json import mca2json

world = os.path.normpath(sys.argv[1])

def explore(path):
    if os.path.isfile(path):
        if path.endswith('.dat'): # assume nbt
            newf = open(path[:-3]+'json','w')
            obj = nbt2json(gzip.decompress(open(path,'rb').read()))
            newf.write(json.dumps(obj[''],indent=4))
            newf.close()
            print('converted',path)
        elif path.endswith('.mca'):
            chunks = mca2json(open(path,'rb').read())
            for chunk in chunks:
                path2 = path
                while len(path2) > 0 and path2[-1] != '/': path2 = path2[:-1]
                newf = open(path2+'c.%d.%d.json'%(chunk['Level']['xPos'],
                                                  chunk['Level']['zPos']),'w')
                newf.write(json.dumps(chunk,indent=4))
                newf.close()
            print('converted',path)
    elif os.path.isdir(path):
        for file in os.listdir(path):
            explore(path+'/'+file)

explore(world)
