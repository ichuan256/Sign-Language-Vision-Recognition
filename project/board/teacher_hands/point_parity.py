"""Board-versus-PC normalized landmark parity with best two-hand assignment."""
import itertools
import json
import numpy as np

board=json.load(open('project/_tmp/teacher_board_20261027_v1/result_hello_v6/frames.json'))
pc=json.load(open('project/board/teacher_hands/pc_reference_hello_v2.json'))
all_errors=[]
for b,p in zip(board,pc):
    actual=[np.asarray(x).reshape(21,3) for x in b['points']]
    expected=[np.asarray(x).reshape(21,3) for x in p['hands']]
    candidates=[]
    for permutation in itertools.permutations(range(len(expected)),len(actual)):
        pairs=list(zip(actual,[expected[i] for i in permutation]))
        cost=sum(float(np.linalg.norm(x[0,:2]-y[0,:2])) for x,y in pairs)
        candidates.append((cost,pairs))
    pairs=min(candidates,key=lambda x:x[0])[1] if candidates else []
    errors=[]
    for x,y in pairs:
        delta=(x[:,:2]-y[:,:2])*[1280.,720.]
        errors.append(dict(xy_rmse_pixels=float(np.sqrt(np.mean(delta**2))),
            xy_max_pixels=float(np.max(np.abs(delta)))))
        all_errors.extend(delta.reshape(-1).tolist())
    print(json.dumps(dict(frame=b['frame_id'],hands=len(actual),errors=errors)))
if all_errors:
    values=np.asarray(all_errors)
    print(json.dumps(dict(all_xy_rmse_pixels=float(np.sqrt(np.mean(values**2))),
        all_xy_max_abs_pixels=float(np.max(np.abs(values))))))
