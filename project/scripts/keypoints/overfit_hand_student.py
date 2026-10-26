"""Fit a frozen human training subset and verify it separately. This never measures generalization."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
os.environ.setdefault('TF_USE_LEGACY_KERAS','1');os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
for name,value in [('OPENBLAS_NUM_THREADS','1'),('OMP_NUM_THREADS','1'),('MKL_NUM_THREADS','1'),
        ('TF_NUM_INTRAOP_THREADS','4'),('TF_NUM_INTEROP_THREADS','2')]:os.environ.setdefault(name,value)
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import cv2
import numpy as np
from vision.keypoints.student_data import load_dataset,digest,augment,human_xy_training_subset,coordinate_metrics
from project.scripts.keypoints.build_hand_student import build


def metrics(prediction,targets,masks):
    return dict(all_points=coordinate_metrics(prediction,targets,masks),
        fingertips=coordinate_metrics(prediction,targets,masks,point_indices=(4,8,12,16,20)))


def draw_predictions(path,x,y,prediction,masks,ids):
    cards=[]
    for i in range(len(x)):
        card=np.zeros((296,256,3),np.uint8)
        card[:256]=cv2.resize(cv2.cvtColor(np.rint(x[i]*255).astype(np.uint8),cv2.COLOR_RGB2BGR),(256,256))
        for values,color in [(y[i],(0,220,0)),(prediction[i],(0,60,255))]:
            xy=values[:63].reshape(21,3)[:,:2]*255
            for j,point in enumerate(xy):
                if masks[i,j*3] and masks[i,j*3+1] and np.isfinite(point).all():
                    cv2.circle(card,tuple(np.clip(np.rint(point),-1000,1000).astype(int)),3,color,1)
        cv2.putText(card,ids[i],(3,272),cv2.FONT_HERSHEY_SIMPLEX,.34,(255,255,255),1)
        cv2.putText(card,'green=human red=prediction',(3,289),cv2.FONT_HERSHEY_SIMPLEX,.4,(255,255,255),1);cards.append(card)
    while len(cards)%3:cards.append(np.zeros_like(cards[0]))
    if not cv2.imwrite(str(path),np.vstack([np.hstack(cards[i:i+3]) for i in range(0,len(cards),3)])):
        raise OSError('Cannot write diagnostic visualization')


def new_output(path):
    path=path.resolve()
    if path.exists() or not path.is_relative_to(ROOT/'project/_tmp'):raise ValueError('New project/_tmp output required')
    path.mkdir(parents=True);return path


def fit(a):
    import tensorflow as tf
    import tf_keras as keras
    if a.size not in (96,128) or a.steps<1 or a.check_every<1 or a.stable_checks<1 or not 0<a.goal<=1 or a.learning_rate<=0:
        raise ValueError('Invalid diagnostic configuration')
    images,y,m,records,data_report=load_dataset(a.data,a.reviews,mask_outside_source=True)
    indices,targets,masks=human_xy_training_subset(y,m,records,a.count)
    selected=[records[i] for i in indices];ids=[r['sample_id'] for r in selected]
    x=np.stack([augment(images[i],y[i],m[i],a.size)[0] for i in indices])
    if not np.isfinite(x).all() or x.min()<0 or x.max()>1:raise ValueError('Invalid fixed RGB inputs')
    out=new_output(a.output)
    np.savez_compressed(out/'batch.npz',images=x,targets=targets,masks=masks,sample_ids=np.array(ids))
    spec_path=ROOT/'project/algo/keypoints/hand_student_v1.json';spec=json.loads(spec_path.read_text())
    keras.utils.set_random_seed(a.seed);model=build(spec,a.size)
    for layer in model.layers:
        if isinstance(layer,keras.layers.BatchNormalization):layer.momentum=.9
    head=model.get_layer('coordinate_presence_handedness_head');rng=np.random.default_rng(a.seed)
    kernel,bias=head.get_weights();kernel=rng.normal(0,.001,kernel.shape).astype(np.float32)
    mean=np.divide((targets*masks).sum(0),masks.sum(0),out=np.zeros(65,np.float32),where=masks.sum(0)>0)
    bias[:]=mean;head.set_weights([kernel,bias]);initial_head=[v.copy() for v in head.get_weights()]
    model.save(out/'initial_DIAGNOSTIC.keras')
    before=model(x,training=False).numpy();baseline=np.broadcast_to(mean,targets.shape)
    draw_predictions(out/'before.jpg',x,targets,before,masks,ids)
    optimizer=keras.optimizers.Adam(learning_rate=a.learning_rate,clipnorm=1.)
    tx=tf.constant(x);ty=tf.constant(targets);tm=tf.constant(masks)
    @tf.function
    def step():
        with tf.GradientTape() as tape:
            prediction=model(tx,training=True)
            delta=tf.abs(prediction-ty);huber=tf.where(delta<.03,.5*delta*delta,.03*(delta-.015))
            loss=tf.reduce_sum(huber*tm)/(.03*tf.maximum(1.,tf.reduce_sum(tm)))
        gradients=tape.gradient(loss,model.trainable_variables)
        if any(g is None for g in gradients):raise ValueError('Disconnected trainable gradient')
        norm=tf.linalg.global_norm(gradients)
        tf.debugging.assert_all_finite(loss,'Nonfinite loss');tf.debugging.assert_all_finite(norm,'Nonfinite gradient')
        optimizer.apply_gradients(zip(gradients,model.trainable_variables));return loss,norm
    history=[];best=(-1.,-float('inf'));best_weights=None;stable=0;start=time.perf_counter()
    for number in range(1,a.steps+1):
        loss,norm=step()
        if number==1 or number%a.check_every==0 or number==a.steps:
            predicted=model(x,training=False).numpy();result=metrics(predicted,targets,masks);all_points=result['all_points']
            rank=(all_points['PCK_at_005'],-all_points['mean_normalized_error'])
            if rank>best:best=rank;best_weights=model.get_weights();best_step=number
            stable=stable+1 if all_points['PCK_at_005']>=a.goal else 0
            history.append(dict(step=number,loss=float(loss),gradient_norm=float(norm),inference=result))
            print('OVERFIT',number,'loss',round(float(loss),6),'NME',round(all_points['mean_normalized_error'],6),
                'PCK',round(all_points['PCK_at_005'],4),'stable',stable,flush=True)
            if stable>=a.stable_checks:break
    model.set_weights(best_weights);prediction=model(x,training=False).numpy()
    # Probe batch-statistics output without leaving an extra BN moving-statistics update in the saved model.
    state=model.get_weights();train_prediction=model(x,training=True).numpy();model.set_weights(state)
    shuffled=[metrics(model(np.roll(x,shift,axis=0),training=False).numpy(),targets,masks)['all_points'] for shift in range(1,len(x))]
    constant=metrics(model(np.repeat(x[:1],len(x),axis=0),training=False).numpy(),targets,masks)
    excluded=np.flatnonzero(masks.sum(0)==0);final_head=head.get_weights()
    excluded_change=max(float(np.max(np.abs(final_head[0][:,excluded]-initial_head[0][:,excluded]))),
        float(np.max(np.abs(final_head[1][excluded]-initial_head[1][excluded]))))
    if excluded_change!=0:raise RuntimeError('XY-only diagnostic changed unsupervised head parameters')
    file='hand_student_'+str(a.size)+'_OVERFIT_DIAGNOSTIC.keras';model.save(out/file)
    final=metrics(prediction,targets,masks)
    np.savez_compressed(out/'predictions.npz',predictions=prediction,targets=targets,masks=masks,sample_ids=np.array(ids))
    draw_predictions(out/'after.jpg',x,targets,prediction,masks,ids)
    report=dict(scope='Training-subset memorization diagnostic only; no validation/test metrics or deployment acceptance',
        input_size=a.size,seed=a.seed,steps_run=number,best_step=best_step,elapsed_s=time.perf_counter()-start,
        learning_rate=a.learning_rate,bn_momentum=.9,loss='masked XY Huber delta .03; no z/presence/handedness',
        augmentation=False,full_batch=True,goal_PCK_at_005=a.goal,stable_checks_required=a.stable_checks,
        stable_goal_met=stable>=a.stable_checks,goal_met=final['all_points']['PCK_at_005']>=a.goal,
        before=metrics(before,targets,masks),mean_shape=metrics(baseline,targets,masks),after=final,
        training_mode_probe=metrics(train_prediction,targets,masks),
        cyclic_input_shuffle=shuffled,shuffle_mean_PCK=float(np.mean([s['PCK_at_005'] for s in shuffled])),constant_input=constant,
        unsupervised_head_parameter_max_change=excluded_change,
        per_ROI=[dict(sample_id=s,metrics=metrics(prediction[i:i+1],targets[i:i+1],masks[i:i+1])) for i,s in enumerate(ids)],
        selected=[{k:r[k] for k in ['sample_id','source_sha256','source_frame','split','split_group','pose_source']} for r in selected],
        unique_source_clips=len({r['source_sha256'] for r in selected}),history=history,
        dataset_sha256=digest(a.data/'dataset.json'),records_sha256=data_report['records_sha256'],reviews_sha256=digest(a.reviews),
        student_spec_sha256=digest(spec_path),batch_sha256=digest(out/'batch.npz'),model_file=file,model_sha256=digest(out/file),
        holdout_used_for_training=False,holdout_metrics_computed=False,quantized=False,board_deployed=False)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('OVERFIT_COMPLETE',json.dumps(dict(goal_met=report['goal_met'],after=final,shuffle_mean_PCK=report['shuffle_mean_PCK'])),flush=True)


def verify(a):
    import tf_keras as keras
    run=a.run.resolve();report=json.loads((run/'report.json').read_text());model_path=(run/report['model_file']).resolve()
    if not model_path.is_relative_to(run) or digest(model_path)!=report['model_sha256'] or digest(run/'batch.npz')!=report['batch_sha256']:
        raise ValueError('Diagnostic model/batch SHA mismatch')
    with np.load(run/'batch.npz',allow_pickle=False) as batch:
        x=batch['images'];y=batch['targets'];m=batch['masks'];ids=batch['sample_ids'].tolist()
    if ids!=[r['sample_id'] for r in report['selected']] or any(r['split']!='train' or r['pose_source']!='human' for r in report['selected']):
        raise ValueError('Diagnostic rows differ from human train subset')
    model=keras.models.load_model(model_path,compile=False);prediction=model(x,training=False).numpy();result=metrics(prediction,y,m)
    difference=abs(result['all_points']['mean_normalized_error']-report['after']['all_points']['mean_normalized_error'])
    if difference>1e-6 or result['all_points']['PCK_at_005']!=report['after']['all_points']['PCK_at_005']:
        raise RuntimeError('Saved-model metric parity failed')
    out=new_output(a.output)
    np.savez_compressed(out/'predictions.npz',predictions=prediction,sample_ids=np.array(ids))
    draw_predictions(out/'verified.jpg',x,y,prediction,m,ids)
    result.update(model_sha256=digest(model_path),batch_sha256=digest(run/'batch.npz'),NME_difference=difference,
        holdout_metrics_computed=False,diagnostic_only=True)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    train=sub.add_parser('fit');train.add_argument('--data',type=Path,required=True);train.add_argument('--reviews',type=Path,required=True)
    train.add_argument('--output',type=Path,required=True);train.add_argument('--size',type=int,default=96)
    train.add_argument('--count',type=int,default=6);train.add_argument('--steps',type=int,default=1500)
    train.add_argument('--check-every',type=int,default=25);train.add_argument('--stable-checks',type=int,default=3)
    train.add_argument('--goal',type=float,default=.95);train.add_argument('--learning-rate',type=float,default=1e-3)
    train.add_argument('--seed',type=int,default=20261026)
    check=sub.add_parser('verify');check.add_argument('--run',type=Path,required=True);check.add_argument('--output',type=Path,required=True)
    a=p.parse_args();fit(a) if a.mode=='fit' else verify(a)


if __name__=='__main__':main()
